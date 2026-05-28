"""Matrix-backed scanner runtime evaluator.

Speedup report v2 §4 P6, §6.1, §11.2 Phase 6 — research-only by design.
Adds two evaluator paths:

* :class:`MatrixRuntimeCompatibilityMode` — produces per-scan candidate
  events field-by-field equal to the legacy
  :func:`scanner.scan_loop.evaluate_one_scan`. The parity bridge for the
  compatibility runtime_mode.
* :func:`evaluate_one_scan_vectorized` — gate evaluation as numpy
  vector ops over the matrix partition. Requires the parity manifest
  (``optuna.acceleration.scan_matrix.require_parity_manifest``).

Both are **scaffolding** in this build: the parity bridge requires
multi-day work to reconstruct per-symbol dicts identically to the
legacy scanner's gate ordering / score tie-stability / event-id
determinism, so the opt-in is refused at the backtester boundary until
the parity matrix (tests/parity/test_scan_matrix_*) proves bit-equal
results. The Phase 6 contract is:

1. ``runtime_mode`` defaults to ``"disabled"`` in every committed
   config — no production behaviour change.
2. ``runtime_mode="compatibility"`` is admissible AS A RESEARCH OPT-IN
   only when the parity manifest is present AND the parity tests pass;
   today the runtime still refuses at the backtester opt-in boundary.
3. ``runtime_mode="vectorized"`` requires the parity manifest plus the
   parity proof; refused for the same reason.
"""
from __future__ import annotations

import os
from typing import Any, Optional

import numpy as np
import pandas as pd

from .scan_matrix import (
    HoldoutMatrixReadError,
    ScanMatrixSession,
    ScanMatrixStore,
)


class MatrixRuntimeNotImplementedError(RuntimeError):
    """Raised when the runtime opt-in is set but the parity proof is missing."""


class MatrixRuntimeParityError(RuntimeError):
    """Raised when the BOWAKA_MATRIX_RUNTIME_ASSERT debug check finds drift.

    Speedup report v2 §6.1 / Phase 3 task 2. When the
    ``BOWAKA_MATRIX_RUNTIME_ASSERT`` env var is truthy, the compatibility
    runtime re-runs the legacy aggregator on the same bars and compares the
    matrix reconstruction dict-for-dict. A mismatch raises this — used in
    CI parity tests, off by default in production.
    """


class MatrixParityManifestMissingError(MatrixRuntimeNotImplementedError):
    """Raised when ``runtime_mode="vectorized"`` is set without a parity manifest.

    Speedup report v2 §6.1 / Phase 6 task 3. The vectorized path produces
    candidate events from numpy vector ops; without the parity manifest
    (built by ``bowaka-v2-lab scan-matrix build``) there is no proof the
    vectorized path matches the legacy scanner. The runtime refuses to
    enable the vectorized path under those conditions.
    """


def resolve_runtime_mode(cfg: Any) -> str:
    """Read ``optuna.acceleration.scan_matrix.runtime_mode`` with the default.

    Speedup report v2 §4 P6 / Phase 6 task 3. Valid values are
    ``"disabled"`` (the default — legacy ``evaluate_one_scan`` path),
    ``"compatibility"`` (matrix-backed evaluator returning identical
    candidate events to the legacy path), and ``"vectorized"`` (numpy
    vector-op gate evaluation; requires the parity manifest).
    """
    mode = (
        ((cfg or {}).get("optuna") or {}).get("acceleration", {})
        .get("scan_matrix", {}).get("runtime_mode", "disabled")
    )
    mode = str(mode).lower().strip() or "disabled"
    if mode not in ("disabled", "compatibility", "vectorized"):
        raise ValueError(
            f"optuna.acceleration.scan_matrix.runtime_mode must be one of "
            f"'disabled' / 'compatibility' / 'vectorized'; got {mode!r}"
        )
    return mode


def _matrix_runtime_assert_enabled() -> bool:
    """True when ``BOWAKA_MATRIX_RUNTIME_ASSERT`` is a truthy env value."""
    return str(os.environ.get("BOWAKA_MATRIX_RUNTIME_ASSERT", "")).strip().lower() in (
        "1", "true", "yes", "on",
    )


def _nan_to_none(v: Any) -> Optional[float]:
    """Matrix cell -> ``None`` when NaN, else ``float(v)`` (inverse of builder)."""
    fv = float(v)
    if np.isnan(fv):
        return None
    return fv


#: session_bar float columns reconstructed from the matrix dynamic_float64
#: arrays. ``last_bar_timestamp`` is reconstructed separately from
#: ``last_bar_ts_ns`` + ``has_valid_timestamp``.
_SESSION_BAR_F64_COLUMNS = (
    "session_open", "session_high", "session_low",
    "last_price", "session_volume", "session_range",
)

#: forming-feature columns reconstructed from the matrix dynamic_float64
#: arrays. Mirrors the keys ``compute_forming_session_features`` returns.
_FORMING_FEATURE_COLUMNS = (
    "rvol_so_far", "projected_full_day_rvol", "range_expansion_so_far",
    "close_location_so_far", "ema_distance", "current_return_pct",
    "gap_pct", "expected_volume_until_scan",
)


def _reconstruct_session_bar(
    matrix_session: ScanMatrixSession, scan_idx: int, s_idx: int,
) -> dict[str, Any]:
    """Rebuild the legacy ``aggregate_forming_session_bar`` dict from matrix cells."""
    out: dict[str, Any] = {}
    for col in _SESSION_BAR_F64_COLUMNS:
        out[col] = _nan_to_none(matrix_session.dynamic_float64[col][scan_idx, s_idx])
    # last_bar_timestamp: legacy stores the bar's tz-aware ISO string. The
    # matrix stores the ns value (UTC) + a validity flag. Reconstruct the
    # UTC ISO string only when the matrix recorded a valid timestamp.
    has_valid_ts = int(
        matrix_session.dynamic_uint8["has_valid_timestamp"][scan_idx, s_idx]
    )
    if has_valid_ts == 1:
        ns = int(matrix_session.dynamic_int64["last_bar_ts_ns"][scan_idx, s_idx])
        out["last_bar_timestamp"] = pd.Timestamp(ns, tz="UTC").isoformat()
    else:
        out["last_bar_timestamp"] = None
    return out


def _reconstruct_forming_feats(
    matrix_session: ScanMatrixSession, scan_idx: int, s_idx: int,
) -> dict[str, Any]:
    """Rebuild the legacy ``compute_forming_session_features`` dict from cells."""
    return {
        col: _nan_to_none(matrix_session.dynamic_float64[col][scan_idx, s_idx])
        for col in _FORMING_FEATURE_COLUMNS
    }


def _resolve_scan_idx(matrix_session: ScanMatrixSession, scan_ts_obj: pd.Timestamp) -> int:
    """Exact ns-aligned scan index, or raise if the scan_ts is not in the matrix."""
    target = int(scan_ts_obj.value)
    idx = int(np.searchsorted(matrix_session.scan_timestamps_ns, target))
    n = int(matrix_session.scan_timestamps_ns.shape[0])
    if idx >= n or int(matrix_session.scan_timestamps_ns[idx]) != target:
        raise MatrixRuntimeNotImplementedError(
            f"scan_ts {scan_ts_obj.isoformat()} (ns={target}) is not a matrix "
            f"scan index for session — the matrix scan cadence must match the "
            f"backtest scan cadence exactly (no fuzzy match)."
        )
    return idx


def evaluate_one_scan_compat(
    *,
    cfg: Any,
    matrix_session: ScanMatrixSession,
    scan_ts: Any,
    state: dict,
    scan_context: Any,
    universe_snapshot: Any,
    volume_curve: Any = None,
    collect_gate_dump: bool = True,
    debug_bars_supplier: Any = None,
):
    """Matrix-backed twin of :func:`scanner.scan_loop.evaluate_one_scan`.

    Speedup report v2 §10.5 "Algorithm". Reconstructs the per-symbol
    ``session_bar`` + ``forming_feats`` from the matrix partition (instead
    of re-fetching/aggregating bars) and calls the EXISTING
    ``apply_v2_gates`` / ``compute_signal_strength`` / ``build_candidate_event``
    so candidate events are field-by-field equal to the legacy path.

    Iterates ``scan_context.universe_meta_by_sym`` in its native order (the
    legacy loop's order) and looks matrix cells up by symbol name, so the
    stable sort's tie-order is preserved against the legacy scanner.

    Returns a :class:`scanner.scan_loop.ScanResult`.
    """
    # Local imports keep the module import-light + avoid an import cycle
    # (scan_loop imports features; this module imports scan_loop).
    from ..features import (
        adv_bucket,
        aggregate_forming_session_bar,
        apply_v2_gates,
        compute_forming_session_features,
        compute_signal_strength,
        compute_volume_curve_fraction,
    )
    from .event_builder import build_candidate_event
    from .scan_loop import ScanResult, ScanSkipReason

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

    entered = set(state.get("entered_symbols_today") or [])
    symbol_last_emit_ts: dict[str, str] = state.setdefault("symbol_last_emit_ts", {})
    if "signal_emits_per_symbol_today" not in state:
        legacy = state.get("entries_per_symbol_today")
        if isinstance(legacy, dict) and legacy:
            state["signal_emits_per_symbol_today"] = dict(legacy)
        else:
            state["signal_emits_per_symbol_today"] = {}
    signal_emits_per_symbol: dict[str, int] = state["signal_emits_per_symbol_today"]

    universe_meta_by_sym = scan_context.universe_meta_by_sym
    cache_by_sym = scan_context.cache_by_sym
    config_hash_v = scan_context.config_hash_v
    vcf_map = scan_context.volume_curve_fraction_by_scan_bucket
    universe_hash = universe_snapshot.get("universe_hash", "sha256:unknown")

    scan_ts_obj = pd.Timestamp(scan_ts)
    if scan_ts_obj.tzinfo is None:
        raise ValueError("evaluate_one_scan_compat: scan_ts must be tz-aware")
    scan_iso = scan_ts_obj.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")

    scan_idx = _resolve_scan_idx(matrix_session, scan_ts_obj)
    sym_to_idx = {
        str(s): i for i, s in enumerate(matrix_session.universe_meta["symbol"].tolist())
    }
    _assert_on = _matrix_runtime_assert_enabled()

    result = ScanResult(universe_size=len(universe_meta_by_sym))

    def _row(symbol: str, **extra: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "scan_ts": scan_iso,
            "scan_timestamp": scan_iso,
            "symbol": symbol,
            "candidate_emitted": False,
            "rejection_reason": None,
            "score": None,
            "rank": None,
        }
        base.update(extra)
        return base

    def _record_skip(symbol: str, reason, **extra: Any) -> None:
        if collect_gate_dump:
            result.gate_dump.append(_row(
                symbol, skipped=reason.value, rejection_reason=reason.value, **extra,
            ))
        else:
            result.rejection_counts[reason.value] = (
                int(result.rejection_counts.get(reason.value, 0)) + 1
            )

    passing: list[tuple[float, dict[str, Any]]] = []
    passing_rows: dict[str, dict[str, Any]] = {}
    for symbol, meta in universe_meta_by_sym.items():
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
            last_emit_ts = pd.Timestamp(last_emit)
            cooldown_age = scan_ts_obj - last_emit_ts
            if cooldown_age < symbol_cooldown:
                _record_skip(
                    symbol, ScanSkipReason.SYMBOL_COOLDOWN,
                    cooldown_age_seconds=float(cooldown_age.total_seconds()),
                    symbol_cooldown_minutes=symbol_cooldown_minutes,
                )
                continue

        baselines = cache_by_sym.get(symbol)
        if not baselines:
            _record_skip(symbol, ScanSkipReason.NO_BASELINES)
            continue

        adv = baselines.get("avg_dollar_volume_20d")
        prior_atr_pct = baselines.get("prior_atr_pct")
        ema_slope = baselines.get("ema_slope_prior")
        bucket = adv_bucket(adv, bucket_edges)
        vcf = vcf_map.get((scan_ts_obj, bucket))
        if vcf is None:
            vcf = compute_volume_curve_fraction(
                volume_curve, scan_ts_obj, bucket,
                fallback_opening_15m_share=fallback_share,
            )

        s_idx = sym_to_idx.get(symbol)
        if s_idx is None:
            # Symbol not present in this session's matrix partition — the
            # legacy path would have fetched zero bars. Treat as NO_BARS.
            _record_skip(symbol, ScanSkipReason.NO_BARS)
            continue

        has_bar = int(matrix_session.dynamic_uint8["has_bar"][scan_idx, s_idx])
        if has_bar == 0:
            _record_skip(symbol, ScanSkipReason.NO_BARS)
            continue

        # Stale-bar check — naive flag first (legacy skips naive before
        # computing age), then the age threshold.
        has_valid_ts = int(
            matrix_session.dynamic_uint8["has_valid_timestamp"][scan_idx, s_idx]
        )
        if has_valid_ts == 1:
            naive = int(
                matrix_session.dynamic_uint8["bar_timestamp_was_naive"][scan_idx, s_idx]
            )
            if naive == 1:
                _record_skip(
                    symbol, ScanSkipReason.STALE_BAR, reason="naive_timestamp",
                )
                continue
            age_seconds = float(
                matrix_session.dynamic_float64["bar_age_seconds"][scan_idx, s_idx]
            )
            if not np.isnan(age_seconds) and age_seconds > max_bar_age_seconds:
                _record_skip(
                    symbol, ScanSkipReason.STALE_BAR,
                    bar_age_seconds=float(age_seconds),
                    max_bar_age_seconds=max_bar_age_seconds,
                )
                continue

        sess = _reconstruct_session_bar(matrix_session, scan_idx, s_idx)
        feats = _reconstruct_forming_feats(matrix_session, scan_idx, s_idx)

        # Debug-only parity assertion (off by default). Re-runs the legacy
        # aggregator on the same bars and compares dict-for-dict to the matrix
        # reconstruction. Enabled via BOWAKA_MATRIX_RUNTIME_ASSERT for CI /
        # forensic runs; never fires the bar fetch in production.
        if _assert_on and debug_bars_supplier is not None:
            legacy_bars = debug_bars_supplier(symbol, scan_ts_obj)
            legacy_sess = aggregate_forming_session_bar(legacy_bars)
            legacy_feats = compute_forming_session_features(legacy_sess, baselines, vcf)
            for key, mv in sess.items():
                lv = legacy_sess.get(key)
                if mv != lv and not (mv is None and lv is None):
                    if isinstance(mv, float) and isinstance(lv, float):
                        if abs(mv - lv) <= 1e-9:
                            continue
                    raise MatrixRuntimeParityError(
                        f"session_bar[{key!r}] matrix={mv!r} legacy={lv!r} "
                        f"for {symbol} at {scan_iso}"
                    )
            for key, mv in feats.items():
                lv = legacy_feats.get(key)
                if mv != lv and not (mv is None and lv is None):
                    if isinstance(mv, float) and isinstance(lv, float):
                        if abs(mv - lv) <= 1e-9:
                            continue
                    raise MatrixRuntimeParityError(
                        f"forming_feats[{key!r}] matrix={mv!r} legacy={lv!r} "
                        f"for {symbol} at {scan_iso}"
                    )

        ok, gates = apply_v2_gates(
            feats, signals_cfg,
            price=sess.get("last_price"),
            avg_dollar_volume_20d=adv,
            prior_atr_pct=prior_atr_pct,
            ema_slope_prior=ema_slope,
            instrument_class=meta.get("instrument_class"),
        )
        score = (
            compute_signal_strength(feats, score_cfg, ema_slope_prior=ema_slope)
            if ok else None
        )
        if not ok:
            if collect_gate_dump:
                dump_row = _row(
                    symbol,
                    ok=False,
                    failing_gates=sorted(k for k, v in (gates or {}).items() if not v),
                    gate_results=gates,
                    features=feats,
                    baselines={
                        "prior_close": baselines.get("prior_close"),
                        "prior_atr_pct": prior_atr_pct,
                        "ema_slope_prior": ema_slope,
                        "avg_dollar_volume_20d": adv,
                    },
                    session_bar=sess,
                    volume_curve_fraction=vcf,
                    instrument_class=meta.get("instrument_class"),
                    score=score,
                )
                dump_row["rejection_reason"] = ScanSkipReason.GATE_FAILED.value
                dump_row["skipped"] = ScanSkipReason.GATE_FAILED.value
                result.gate_dump.append(dump_row)
            else:
                result.rejection_counts[ScanSkipReason.GATE_FAILED.value] = (
                    int(result.rejection_counts.get(ScanSkipReason.GATE_FAILED.value, 0)) + 1
                )
            continue

        dump_row = _row(
            symbol,
            ok=True,
            failing_gates=sorted(k for k, v in (gates or {}).items() if not v),
            gate_results=gates,
            features=feats,
            baselines={
                "prior_close": baselines.get("prior_close"),
                "prior_atr_pct": prior_atr_pct,
                "ema_slope_prior": ema_slope,
                "avg_dollar_volume_20d": adv,
            },
            session_bar=sess,
            volume_curve_fraction=vcf,
            instrument_class=meta.get("instrument_class"),
            score=score,
        )
        ev = build_candidate_event(
            symbol=symbol,
            universe_meta=meta,
            cfg=cfg,
            universe_hash=universe_hash,
            config_hash_v=config_hash_v,
            session_bar=sess,
            prior_baselines=baselines,
            forming_feats=feats,
            volume_curve_fraction=vcf,
            gate_results=gates,
            candidate_rank=0,
            scan_ts=scan_ts_obj,
            signal_strength=score,
        )
        passing.append((score, ev))
        passing_rows[symbol] = dump_row

    passing.sort(key=lambda x: -x[0])
    for rank, (score, ev) in enumerate(passing, start=1):
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
            row["rejection_reason"] = ScanSkipReason.MAX_ENTRIES_CAP.value
            row["skipped"] = ScanSkipReason.MAX_ENTRIES_CAP.value
            row["effective_cap"] = effective_cap
            if not collect_gate_dump:
                result.rejection_counts[ScanSkipReason.MAX_ENTRIES_CAP.value] = (
                    int(result.rejection_counts.get(ScanSkipReason.MAX_ENTRIES_CAP.value, 0)) + 1
                )
        if collect_gate_dump:
            result.gate_dump.append(row)
    state["scanner_last_run_ts"] = scan_iso
    return result


class MatrixRuntimeCompatibilityMode:
    """Parity-bridge evaluator for ``runtime_mode='compatibility'``.

    Speedup report v2 §4 P6 / §6.1 / §10.5 — produces a
    :class:`scanner.scan_loop.ScanResult` field-by-field equal to
    :func:`scanner.scan_loop.evaluate_one_scan` for the same inputs, by
    reconstructing the per-symbol ``session_bar`` / ``forming_feats`` dicts
    from the matrix partition and calling the EXISTING ``apply_v2_gates`` /
    ``compute_signal_strength`` / ``build_candidate_event`` (no gate
    re-implementation).

    Construction holds the per-session matrix partition + the cfg;
    :meth:`evaluate_one_scan_compat` runs one scan against it.
    """

    def __init__(
        self,
        *,
        matrix_partition: Any,
        cfg: Optional[Any] = None,
    ) -> None:
        self.matrix_partition = matrix_partition
        self.cfg = cfg

    def evaluate_one_scan_compat(
        self,
        scan_ts: Any,
        eligible_symbols: Any = None,
        *,
        state: dict,
        scan_context: Any,
        universe_snapshot: Any,
        volume_curve: Any = None,
        collect_gate_dump: bool = True,
    ):
        """Return the :class:`ScanResult` ``evaluate_one_scan`` would produce.

        ``eligible_symbols`` is accepted for signature-compatibility with the
        Phase 6 spec but the iteration order is taken from
        ``scan_context.universe_meta_by_sym`` (the legacy order) so the stable
        sort's tie-order matches the legacy scanner exactly.
        """
        if self.matrix_partition is None:
            raise MatrixRuntimeNotImplementedError(
                "MatrixRuntimeCompatibilityMode.evaluate_one_scan_compat: no "
                "matrix partition attached — open one via "
                "ScanMatrixStore.open_session(session_date, purpose='objective')."
            )
        return evaluate_one_scan_compat(
            cfg=self.cfg,
            matrix_session=self.matrix_partition,
            scan_ts=scan_ts,
            state=state,
            scan_context=scan_context,
            universe_snapshot=universe_snapshot,
            volume_curve=volume_curve,
            collect_gate_dump=collect_gate_dump,
        )


def evaluate_one_scan_from_matrix(
    *,
    cfg: Any,
    matrix_session: ScanMatrixSession,
    state: dict,
    scan_idx: int,
    consumer: Any,
    quote_supplier: Optional[Any] = None,
    forward_minute_supplier: Optional[Any] = None,
    status_supplier: Optional[Any] = None,
    collect_gate_dump: bool = False,
) -> tuple[Any, list]:
    """**Phase 9 scaffolding: NOT yet wired.**

    The compatibility-mode evaluator (Step 9A) MUST:

    1. Read dynamic+static rows from
       ``matrix_session.dynamic_float64[col][scan_idx, :]`` etc.
    2. Reconstruct per-symbol ``session_bar`` + ``forming_feats`` dicts
       identical in keys to the legacy path output.
    3. Call existing ``apply_v2_gates`` / ``compute_signal_strength``
       on those dicts — do not re-implement gate logic.
    4. Build candidate events via
       ``scanner.event_builder.build_candidate_event(...)``. Event IDs
       / hashes / schema MUST match the legacy path exactly.
    5. Apply scanner-state updates
       (``signal_emits_per_symbol_today``, ``symbol_last_emit_ts``)
       identically to ``evaluate_one_scan``.

    Until the parity matrix
    (``tests/parity/test_scan_matrix_one_scan_parity.py`` and
    ``test_scan_matrix_full_session_parity.py`` and
    ``test_scan_matrix_full_fold_backtest_parity.py``) is wired and
    proves identical emitted-candidate sequences + scanner state +
    fills + trades + daily equity + FoldResults, the runtime opt-in
    is refused.
    """
    raise MatrixRuntimeNotImplementedError(
        "evaluate_one_scan_from_matrix is reserved for the Phase 9 "
        "matrix-backed scanner runtime; the per-symbol dict "
        "reconstruction + gate ordering + score tie-stability + "
        "event_id determinism parity proof against evaluate_one_scan "
        "(legacy) is not yet shipped. Set "
        "optuna.acceleration.scan_matrix.enabled=false until the "
        "parity matrix proves bit-identical results "
        "(speedup report §6.4 / matrix doc §17.2)."
    )


def evaluate_one_scan_from_matrix_vectorized(
    *,
    cfg: Any,
    matrix_session: ScanMatrixSession,
    state: dict,
    scan_idx: int,
    consumer: Any,
    quote_supplier: Optional[Any] = None,
    forward_minute_supplier: Optional[Any] = None,
    status_supplier: Optional[Any] = None,
    collect_gate_dump: bool = False,
) -> tuple[Any, list]:
    """Vectorized (Step 9B) — also Phase 9 scaffolding.

    Will use ``np.argsort(-scores, kind="stable")`` (matrix doc §17.3) on
    the full ``dyn_f64`` / ``flags`` slices for ``scan_idx``, then call
    ``build_candidate_event`` row-wise for passing rows. Missing-value
    semantics from matrix doc §6 must be implemented explicitly (no
    NaN-compares — every gate masks on the corresponding uint8 flag).
    """
    raise MatrixRuntimeNotImplementedError(
        "evaluate_one_scan_from_matrix_vectorized is reserved for "
        "Phase 9 Step 9B and is not yet shipped."
    )


def assert_backtester_matrix_opt_in_is_supported(
    *,
    enabled: bool,
    runtime_mode: str = "disabled",
    parity_manifest_present: bool = False,
    parity_proof_version: Optional[int] = None,
) -> None:
    """Resolve the matrix-backed scanner opt-in.

    Speedup report v2 §4 P6 / §6.1 / Phase 3-4 task 3. Three-mode resolution:

    * ``runtime_mode == "disabled"`` (the default) → no-op; legacy scanner.
    * ``runtime_mode == "compatibility"`` → ACCEPTED (Phase 3). The
      compatibility evaluator (:func:`evaluate_one_scan_compat`) produces
      bit-identical candidate events to ``evaluate_one_scan``; the
      ``tests/parity/test_scan_matrix_*`` matrix is the proof.
    * ``runtime_mode == "vectorized"`` → ACCEPTED (Phase 4) IFF the parity
      manifest is present AND ``<store_root>/parity_proof.json`` records a
      ``verifier_version >= 2`` (the verifier ran the vectorized-vs-legacy
      spot check). Otherwise refused.
    """
    if not enabled or runtime_mode == "disabled":
        return
    if runtime_mode == "compatibility":
        # Phase 3 — accepted. The parity tests are the proof; the fold-context
        # builder additionally verifies the manifest config_input_hash /
        # dataset_hash so a stale matrix cannot be silently consumed.
        return
    if runtime_mode == "vectorized":
        if not parity_manifest_present:
            raise MatrixParityManifestMissingError(
                "scan-matrix runtime_mode='vectorized' requires the parity "
                "manifest. Build it via `bowaka-v2-lab scan-matrix build` "
                "(speedup report v2 §6.1 / matrix doc §17.2)."
            )
        if parity_proof_version is None or int(parity_proof_version) < 2:
            raise MatrixRuntimeNotImplementedError(
                "scan-matrix runtime_mode='vectorized' requires a parity-proof "
                "marker with verifier_version >= 2 (the vectorized-vs-legacy "
                "spot check). Run `bowaka-v2-lab scan-matrix verify` against a "
                "freshly built matrix to write "
                "<store_root>/parity_proof.json (speedup report v2 §10.6 / "
                "matrix doc §17.3)."
            )
        return
    raise MatrixRuntimeNotImplementedError(
        f"scan-matrix runtime_mode={runtime_mode!r} is not a supported mode; "
        "use 'disabled' / 'compatibility' / 'vectorized'."
    )


__all__ = [
    "MatrixParityManifestMissingError",
    "MatrixRuntimeCompatibilityMode",
    "MatrixRuntimeNotImplementedError",
    "MatrixRuntimeParityError",
    "assert_backtester_matrix_opt_in_is_supported",
    "evaluate_one_scan_compat",
    "evaluate_one_scan_from_matrix",
    "evaluate_one_scan_from_matrix_vectorized",
    "resolve_runtime_mode",
]
