"""Vectorized scan-matrix gate evaluation (speedup report v2 §6.1 / §10.6).

Phase 4 — replaces the per-symbol Python gate loop with NumPy mask ops
across all symbols at a scan. Every gate is modelled with EXPLICIT masks
over the matrix validity flags (``has_bar`` / ``has_baseline`` /
``has_valid_timestamp`` / ``bar_timestamp_was_naive``) — never NaN
comparisons — so the missing-value semantics of the legacy scalar helpers
(``_ge`` / ``_le`` / ``_between`` / ``instrument_gate``) are reproduced
bit-for-bit. The score is computed by :func:`compute_signal_strength_vectorized`,
the stable descending sort by ``np.argsort(-scores, kind="stable")``, and the
emitted candidate events are built ROW-WISE by the existing
``build_candidate_event`` (the event builder is NOT vectorized in this phase).

Validated three-way (legacy == compatibility == vectorized) by
``tests/parity/test_scan_matrix_vectorized_*``.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------
# Vectorized gate helpers — explicit-mask twins of the scalar _ge / _le /
# _between in features/forming_bar.py. ``val`` is a float64 array (NaN ==
# "missing", i.e. the legacy ``None``); ``threshold`` is a scalar or None.
# --------------------------------------------------------------------------


def _ge_vec(val: np.ndarray, threshold: Optional[float]) -> np.ndarray:
    """``_ge``: threshold None passes all; val NaN fails when threshold set."""
    if threshold is None:
        return np.ones(val.shape, dtype=bool)
    out = ~np.isnan(val)
    out &= val >= float(threshold)
    return out


def _le_vec(val: np.ndarray, threshold: Optional[float]) -> np.ndarray:
    """``_le``: threshold None passes all; val NaN ALSO passes when threshold set."""
    if threshold is None:
        return np.ones(val.shape, dtype=bool)
    nan_mask = np.isnan(val)
    out = nan_mask.copy()
    out[~nan_mask] = val[~nan_mask] <= float(threshold)
    return out


def _between_vec(
    val: np.ndarray, lo: Optional[float], hi: Optional[float],
) -> np.ndarray:
    """``_between``: no bounds -> all pass; with bounds, val NaN fails."""
    if lo is None and hi is None:
        return np.ones(val.shape, dtype=bool)
    out = ~np.isnan(val)
    if lo is not None:
        out &= val >= float(lo)
    if hi is not None:
        out &= val <= float(hi)
    return out


def _to_float_opt(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def compute_signal_strength_vectorized(
    *,
    rvol_so_far: np.ndarray,
    range_expansion_so_far: np.ndarray,
    close_location_so_far: np.ndarray,
    ema_distance: np.ndarray,
    ema_slope_prior: np.ndarray,
    gap_pct: np.ndarray,
    score_cfg: Mapping[str, Any],
) -> np.ndarray:
    """Vectorized twin of ``features.compute_signal_strength``.

    Each input is a ``(n_symbols,)`` float64 array; NaN is treated as the
    legacy ``None`` -> ``0.0`` (the scalar does ``_to_float(x) or 0.0``).
    Returns a ``(n_symbols,)`` float64 score array bit-equal to calling the
    scalar function row-wise.
    """
    cfg = score_cfg or {}
    bounded = bool(cfg.get("bounded", True))
    cl_weight = float(cfg.get("close_location_weight", 0.75))
    gap_above = float(cfg.get("gap_penalty_above", 0.25))

    rvol = np.nan_to_num(np.asarray(rvol_so_far, dtype=np.float64), nan=0.0)
    rng = np.nan_to_num(np.asarray(range_expansion_so_far, dtype=np.float64), nan=0.0)
    cl = np.nan_to_num(np.asarray(close_location_so_far, dtype=np.float64), nan=0.0)
    ed = np.nan_to_num(np.asarray(ema_distance, dtype=np.float64), nan=0.0)
    es = np.nan_to_num(np.asarray(ema_slope_prior, dtype=np.float64), nan=0.0)
    gap = np.nan_to_num(np.asarray(gap_pct, dtype=np.float64), nan=0.0)

    if bounded:
        rvol_cap = float(cfg.get("rvol_score_cap", 5.0))
        rng_cap = float(cfg.get("range_score_cap", 2.5))
        ed_cap = float(cfg.get("ema_distance_score_cap", 0.40))
        es_cap = float(cfg.get("ema_slope_score_cap", 0.25))
        rvol_term = np.clip(rvol, 0.0, rvol_cap)
        rng_term = np.clip(rng, 0.0, rng_cap)
        ed_term = np.clip(ed, 0.0, ed_cap)
        es_term = np.clip(es, 0.0, es_cap)
        score = (
            1.00 * rvol_term
            + 1.00 * rng_term
            + cl_weight * cl
            + 10.0 * ed_term
            + 10.0 * es_term
            - 1.00 * np.maximum(gap - gap_above, 0.0)
        )
    else:
        score = (
            1.00 * rvol
            + 1.00 * rng
            + cl_weight * cl
            + 10.0 * ed
            + 10.0 * es
            - 1.00 * np.maximum(gap - gap_above, 0.0)
        )
    return score.astype(np.float64)


#: Gate dict insertion order matches ``apply_v2_gates`` exactly.
_GATE_ORDER = (
    "price_gate", "avg_dollar_volume_gate", "rvol_gate", "projected_rvol_gate",
    "prior_atr_pct_gate", "range_expansion_gate", "close_location_gate",
    "ema_distance_gate", "ema_slope_gate", "max_gap_gate", "max_rvol_gate",
    "max_range_expansion_gate", "instrument_gate",
)


def _f64_column(
    matrix_session: Any, name: str, scan_idx: int, order_idxs: np.ndarray,
) -> np.ndarray:
    """A dynamic_float64 column row at scan_idx, reindexed to legacy order.

    ``order_idxs[i]`` is the matrix column index for the i-th legacy symbol,
    or -1 when the symbol is absent (value -> NaN)."""
    arr = matrix_session.dynamic_float64[name][scan_idx, :]
    out = np.full(order_idxs.shape, np.nan, dtype=np.float64)
    present = order_idxs >= 0
    out[present] = arr[order_idxs[present]]
    return out


def evaluate_one_scan_vectorized(
    *,
    cfg: Any,
    matrix_session: Any,
    scan_ts: Any,
    state: dict,
    scan_context: Any,
    universe_snapshot: Any,
    volume_curve: Any = None,
    collect_gate_dump: bool = True,
):
    """Vectorized matrix-backed scan evaluator (returns a ``ScanResult``).

    Produces output bit-identical to ``evaluate_one_scan`` /
    ``evaluate_one_scan_compat``: same emitted events, state, rejection
    counts, and gate_dump. The gate evaluation is a set of NumPy masks over
    the scan's full symbol row; the per-symbol bookkeeping (skip ordering,
    stable cap, state mutation) follows the legacy order.
    """
    from ..features import (
        adv_bucket,
        compute_volume_curve_fraction,
        instrument_gate,
    )
    from .event_builder import build_candidate_event
    from .scan_loop import ScanResult, ScanSkipReason
    from .scan_matrix_runtime import (
        _reconstruct_forming_feats,
        _reconstruct_session_bar,
        _resolve_scan_idx,
    )

    scanner_cfg = cfg.get("scanner") or {}
    signals_cfg = cfg.get("signals") or {}
    score_cfg = cfg.get("score") or {}
    market_data_cfg = cfg.get("market_data") or cfg.get("data") or {}
    hf_cfg = cfg.get("historical_features") or {}
    bucket_edges = list(
        (hf_cfg.get("volume_curve") or {}).get(
            "bucket_edges", [250_000, 500_000, 1_000_000, 5_000_000, 20_000_000],
        )
    )
    fallback_share = float(
        (hf_cfg.get("volume_curve") or {}).get("fallback_opening_15m_share", 0.08)
    )
    max_candidates = int(scanner_cfg.get("max_candidates_per_scan", 25))
    max_entries = int(scanner_cfg.get("max_entries_per_scan", max_candidates))
    effective_cap = max(0, min(max_candidates, max_entries))
    max_bar_age_seconds = int(market_data_cfg.get("max_bar_age_seconds", 90))
    same_symbol_day_cap = int(scanner_cfg.get("same_symbol_entries_per_day", 1))
    symbol_cooldown_minutes = float(scanner_cfg.get("symbol_cooldown_minutes", 390))
    symbol_cooldown = pd.Timedelta(minutes=symbol_cooldown_minutes)
    allow_unknown = bool(
        signals_cfg.get("allow_unknown_instrument_class_for_research", False)
    )

    entered = set(state.get("entered_symbols_today") or [])
    symbol_last_emit_ts: dict[str, str] = state.setdefault("symbol_last_emit_ts", {})
    if "signal_emits_per_symbol_today" not in state:
        legacy = state.get("entries_per_symbol_today")
        state["signal_emits_per_symbol_today"] = (
            dict(legacy) if isinstance(legacy, dict) and legacy else {}
        )
    signal_emits_per_symbol: dict[str, int] = state["signal_emits_per_symbol_today"]

    universe_meta_by_sym = scan_context.universe_meta_by_sym
    cache_by_sym = scan_context.cache_by_sym
    config_hash_v = scan_context.config_hash_v
    vcf_map = scan_context.volume_curve_fraction_by_scan_bucket
    universe_hash = universe_snapshot.get("universe_hash", "sha256:unknown")

    scan_ts_obj = pd.Timestamp(scan_ts)
    if scan_ts_obj.tzinfo is None:
        raise ValueError("evaluate_one_scan_vectorized: scan_ts must be tz-aware")
    scan_iso = scan_ts_obj.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
    scan_idx = _resolve_scan_idx(matrix_session, scan_ts_obj)

    symbols = list(universe_meta_by_sym.keys())
    n = len(symbols)
    sym_to_idx = {
        str(s): i for i, s in enumerate(matrix_session.universe_meta["symbol"].tolist())
    }
    order_idxs = np.array([sym_to_idx.get(s, -1) for s in symbols], dtype=np.int64)

    # ---- vectorized feature + gate-input columns (legacy symbol order) ----
    last_price = _f64_column(matrix_session, "last_price", scan_idx, order_idxs)
    rvol = _f64_column(matrix_session, "rvol_so_far", scan_idx, order_idxs)
    proj_rvol = _f64_column(matrix_session, "projected_full_day_rvol", scan_idx, order_idxs)
    range_exp = _f64_column(matrix_session, "range_expansion_so_far", scan_idx, order_idxs)
    close_loc = _f64_column(matrix_session, "close_location_so_far", scan_idx, order_idxs)
    ema_dist = _f64_column(matrix_session, "ema_distance", scan_idx, order_idxs)
    gap_pct = _f64_column(matrix_session, "gap_pct", scan_idx, order_idxs)

    # baseline-sourced arrays (from cache_by_sym, NaN where absent)
    # Opt A (§10h) — these arrays depend only on cache_by_sym + universe_meta_by_sym
    # (session-constant) and allow_unknown (trial-constant), but were rebuilt EVERY
    # scan (~346x/session). Memoize on the per-session scan_context keyed by
    # allow_unknown so the loop runs ONCE per session. Byte-identical (the same
    # arrays, computed once); they are read-only downstream (the gates build new
    # mask arrays), so reuse is safe. The getattr fallback + shape guard keep a
    # scan_context without the cache field (or a stale length) correct by recompute.
    _bl_cache = getattr(scan_context, "_matrix_baseline_cache", None)
    _bl = _bl_cache.get(allow_unknown) if _bl_cache is not None else None
    if _bl is not None and _bl[0].shape[0] == n:
        adv, prior_atr_pct, ema_slope, has_baseline, instrument_pass = _bl
    else:
        adv = np.full(n, np.nan, dtype=np.float64)
        prior_atr_pct = np.full(n, np.nan, dtype=np.float64)
        ema_slope = np.full(n, np.nan, dtype=np.float64)
        has_baseline = np.zeros(n, dtype=bool)
        instrument_pass = np.zeros(n, dtype=bool)
        for i, sym in enumerate(symbols):
            b = cache_by_sym.get(sym)
            if b:
                has_baseline[i] = True
                v = _to_float_opt(b.get("avg_dollar_volume_20d"))
                if v is not None:
                    adv[i] = v
                v = _to_float_opt(b.get("prior_atr_pct"))
                if v is not None:
                    prior_atr_pct[i] = v
                v = _to_float_opt(b.get("ema_slope_prior"))
                if v is not None:
                    ema_slope[i] = v
            instrument_pass[i] = instrument_gate(
                universe_meta_by_sym[sym].get("instrument_class"),
                allow_unknown_for_research=allow_unknown,
            )
        if _bl_cache is not None:
            _bl_cache[allow_unknown] = (
                adv, prior_atr_pct, ema_slope, has_baseline, instrument_pass
            )

    # ---- vectorized gates (order matches apply_v2_gates) ----
    s = signals_cfg
    gate_masks: dict[str, np.ndarray] = {
        "price_gate": _between_vec(
            last_price, _to_float_opt(s.get("price_min")), _to_float_opt(s.get("price_max"))),
        "avg_dollar_volume_gate": _between_vec(
            adv, _to_float_opt(s.get("avg_dollar_volume_min")), _to_float_opt(s.get("avg_dollar_volume_max"))),
        "rvol_gate": _ge_vec(rvol, _to_float_opt(s.get("rvol_so_far_min"))),
        "projected_rvol_gate": _ge_vec(proj_rvol, _to_float_opt(s.get("projected_full_day_rvol_min"))),
        "prior_atr_pct_gate": _ge_vec(prior_atr_pct, _to_float_opt(s.get("prior_atr_pct_min"))),
        "range_expansion_gate": _ge_vec(range_exp, _to_float_opt(s.get("range_expansion_so_far_min"))),
        "close_location_gate": _ge_vec(close_loc, _to_float_opt(s.get("close_location_so_far_min"))),
        "ema_distance_gate": _ge_vec(ema_dist, _to_float_opt(s.get("ema_distance_min"))),
        "ema_slope_gate": _ge_vec(ema_slope, _to_float_opt(s.get("ema_slope_min"))),
        "max_gap_gate": _le_vec(gap_pct, _to_float_opt(s.get("gap_pct_max"))),
        "max_rvol_gate": _le_vec(rvol, _to_float_opt(s.get("rvol_so_far_max"))),
        "max_range_expansion_gate": _le_vec(range_exp, _to_float_opt(s.get("range_expansion_so_far_max"))),
        "instrument_gate": instrument_pass,
    }
    gate_pass_all = np.ones(n, dtype=bool)
    for name in _GATE_ORDER:
        gate_pass_all &= gate_masks[name]

    score_vec = compute_signal_strength_vectorized(
        rvol_so_far=rvol, range_expansion_so_far=range_exp,
        close_location_so_far=close_loc, ema_distance=ema_dist,
        ema_slope_prior=ema_slope, gap_pct=gap_pct, score_cfg=score_cfg,
    )

    # ---- matrix validity flags (matrix column order) ----
    has_bar_row = matrix_session.dynamic_uint8["has_bar"][scan_idx, :]
    has_valid_row = matrix_session.dynamic_uint8["has_valid_timestamp"][scan_idx, :]
    naive_row = matrix_session.dynamic_uint8["bar_timestamp_was_naive"][scan_idx, :]
    bar_age_row = matrix_session.dynamic_float64["bar_age_seconds"][scan_idx, :]

    # Opt C (§10h per-trial scan floor) — gather the validity-flag / bar-age rows
    # into SYMBOL order ONCE (vectorized) instead of a per-symbol ``_flag()`` call
    # in the loop below (22M calls/fold). Byte-identical to the prior
    # ``_flag(row, i)`` == ``int(row[order_idxs[i]]) if order_idxs[i] >= 0 else 0``;
    # symbols absent from the matrix universe (order_idxs < 0) take the legacy
    # default (0; NaN for age, which is unreached for those rows since the
    # order_idxs<0 / has_bar==0 guard ``continue``s first).
    _oi_ok = order_idxs >= 0
    _oi_clip = np.where(_oi_ok, order_idxs, 0)
    has_bar_sym = np.where(_oi_ok, has_bar_row[_oi_clip], 0)
    has_valid_sym = np.where(_oi_ok, has_valid_row[_oi_clip], 0)
    naive_sym = np.where(_oi_ok, naive_row[_oi_clip], 0)
    bar_age_sym = np.where(_oi_ok, bar_age_row[_oi_clip], np.nan)

    # ---- per-symbol loop (legacy skip ordering + emit/cap + state) ----
    result = ScanResult(universe_size=n)

    def _row(symbol: str, **extra: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "scan_ts": scan_iso, "scan_timestamp": scan_iso, "symbol": symbol,
            "candidate_emitted": False, "rejection_reason": None,
            "score": None, "rank": None,
        }
        base.update(extra)
        return base

    # Opt B (§10h) — bind the rejection-reason ``.value`` strings as locals so the
    # hot per-symbol loop avoids re-resolving the Enum ``value`` descriptor per
    # symbol (32M enum lookups/fold). Byte-identical (same interned strings).
    gate_failed_v = ScanSkipReason.GATE_FAILED.value
    max_cap_v = ScanSkipReason.MAX_ENTRIES_CAP.value

    def _record_skip(symbol: str, reason, **extra: Any) -> None:
        rv = reason.value
        if collect_gate_dump:
            result.gate_dump.append(_row(
                symbol, skipped=rv, rejection_reason=rv, **extra,
            ))
        else:
            result.rejection_counts[rv] = (
                int(result.rejection_counts.get(rv, 0)) + 1
            )

    passing: list[tuple[float, dict[str, Any]]] = []
    passing_rows: dict[str, dict[str, Any]] = {}
    for i, symbol in enumerate(symbols):
        meta = universe_meta_by_sym[symbol]
        if symbol in entered:
            _record_skip(symbol, ScanSkipReason.ALREADY_ENTERED_TODAY)
            continue
        if signal_emits_per_symbol.get(symbol, 0) >= same_symbol_day_cap > 0:
            _record_skip(
                symbol, ScanSkipReason.SAME_SYMBOL_DAY_CAP,
                signal_emits_today=int(signal_emits_per_symbol.get(symbol, 0)),
                entries_today=int(signal_emits_per_symbol.get(symbol, 0)),
                same_symbol_entries_per_day=same_symbol_day_cap,
            )
            continue
        last_emit = symbol_last_emit_ts.get(symbol)
        if last_emit is not None and symbol_cooldown > pd.Timedelta(0):
            cooldown_age = scan_ts_obj - pd.Timestamp(last_emit)
            if cooldown_age < symbol_cooldown:
                _record_skip(
                    symbol, ScanSkipReason.SYMBOL_COOLDOWN,
                    cooldown_age_seconds=float(cooldown_age.total_seconds()),
                    symbol_cooldown_minutes=symbol_cooldown_minutes,
                )
                continue
        if not has_baseline[i]:
            _record_skip(symbol, ScanSkipReason.NO_BASELINES)
            continue
        if order_idxs[i] < 0 or has_bar_sym[i] == 0:
            _record_skip(symbol, ScanSkipReason.NO_BARS)
            continue
        if has_valid_sym[i] == 1:
            if naive_sym[i] == 1:
                _record_skip(symbol, ScanSkipReason.STALE_BAR, reason="naive_timestamp")
                continue
            age = float(bar_age_sym[i])
            if not np.isnan(age) and age > max_bar_age_seconds:
                _record_skip(
                    symbol, ScanSkipReason.STALE_BAR,
                    bar_age_seconds=float(age),
                    max_bar_age_seconds=max_bar_age_seconds,
                )
                continue

        s_idx = int(order_idxs[i])
        ok = bool(gate_pass_all[i])

        # Speedup (per-trial scan floor): the per-cell session_bar / forming-
        # feats reconstruction (+ the per-gate dict, vcf, baseline scalars) is
        # consumed ONLY by a gate_dump row or by a PASSING candidate's event. In
        # objective mode (collect_gate_dump=False) a gate-FAILING symbol — the
        # vast majority each scan — discards all of it, so the reconstruction
        # below was pure dead work. Count the rejection and skip it. Emitted
        # events / scores / state / rejection counts are byte-identical (this is
        # dead-work elimination, NOT a semantic change); the existing three-way
        # parity tests run collect_gate_dump=False and guard it end-to-end.
        if not ok and not collect_gate_dump:
            result.rejection_counts[gate_failed_v] = (
                int(result.rejection_counts.get(gate_failed_v, 0)) + 1
            )
            continue

        adv_i = None if np.isnan(adv[i]) else float(adv[i])
        patr_i = None if np.isnan(prior_atr_pct[i]) else float(prior_atr_pct[i])
        eslope_i = None if np.isnan(ema_slope[i]) else float(ema_slope[i])
        bucket = adv_bucket(adv_i, bucket_edges)
        vcf = vcf_map.get((scan_ts_obj, bucket))
        if vcf is None:
            vcf = compute_volume_curve_fraction(
                volume_curve, scan_ts_obj, bucket,
                fallback_opening_15m_share=fallback_share,
            )
        gates = {name: bool(gate_masks[name][i]) for name in _GATE_ORDER}
        score = float(score_vec[i]) if ok else None
        sess = _reconstruct_session_bar(matrix_session, scan_idx, s_idx)
        feats = _reconstruct_forming_feats(matrix_session, scan_idx, s_idx)
        baselines = cache_by_sym.get(symbol)

        if not ok:
            # collect_gate_dump is True here (the False case continued above).
            dump_row = _row(
                symbol, ok=False,
                failing_gates=sorted(k for k, v in gates.items() if not v),
                gate_results=gates, features=feats,
                baselines={
                    "prior_close": baselines.get("prior_close"),
                    "prior_atr_pct": patr_i,
                    "ema_slope_prior": eslope_i,
                    "avg_dollar_volume_20d": adv_i,
                },
                session_bar=sess, volume_curve_fraction=vcf,
                instrument_class=meta.get("instrument_class"), score=score,
            )
            dump_row["rejection_reason"] = gate_failed_v
            dump_row["skipped"] = gate_failed_v
            result.gate_dump.append(dump_row)
            continue

        dump_row = _row(
            symbol, ok=True,
            failing_gates=sorted(k for k, v in gates.items() if not v),
            gate_results=gates, features=feats,
            baselines={
                "prior_close": baselines.get("prior_close"),
                "prior_atr_pct": patr_i,
                "ema_slope_prior": eslope_i,
                "avg_dollar_volume_20d": adv_i,
            },
            session_bar=sess, volume_curve_fraction=vcf,
            instrument_class=meta.get("instrument_class"), score=score,
        )
        ev = build_candidate_event(
            symbol=symbol, universe_meta=meta, cfg=cfg,
            universe_hash=universe_hash, config_hash_v=config_hash_v,
            session_bar=sess, prior_baselines=baselines, forming_feats=feats,
            volume_curve_fraction=vcf, gate_results=gates, candidate_rank=0,
            scan_ts=scan_ts_obj, signal_strength=score,
        )
        passing.append((score, ev))
        passing_rows[symbol] = dump_row

    # Stable descending sort by score (np.argsort kind="stable" matches the
    # legacy Python ``sort(key=lambda x: -x[0])`` tie behaviour).
    if passing:
        scores_arr = np.array([p[0] for p in passing], dtype=np.float64)
        order = np.argsort(-scores_arr, kind="stable")
    else:
        order = np.array([], dtype=np.int64)
    for rank, oi in enumerate(order.tolist(), start=1):
        score, ev = passing[oi]
        ev["candidate_rank"] = rank
        row = passing_rows[ev["symbol"]]
        row["rank"] = rank
        if rank <= effective_cap:
            result.emitted.append(ev)
            row["candidate_emitted"] = True
            state.setdefault("in_play_pool", {})[ev["symbol"]] = {
                "last_signal_ts": ev["scan_timestamp"],
                "signal_expiry_ts": ev["signal_expiry_timestamp"],
                "last_signal_strength": ev["features"]["signal_strength"],
            }
            symbol_last_emit_ts[ev["symbol"]] = scan_iso
            signal_emits_per_symbol[ev["symbol"]] = signal_emits_per_symbol.get(ev["symbol"], 0) + 1
        else:
            row["rejection_reason"] = max_cap_v
            row["skipped"] = max_cap_v
            row["effective_cap"] = effective_cap
            if not collect_gate_dump:
                result.rejection_counts[max_cap_v] = (
                    int(result.rejection_counts.get(max_cap_v, 0)) + 1
                )
        if collect_gate_dump:
            result.gate_dump.append(row)
    state["scanner_last_run_ts"] = scan_iso
    return result


__all__ = [
    "compute_signal_strength_vectorized",
    "evaluate_one_scan_vectorized",
]
