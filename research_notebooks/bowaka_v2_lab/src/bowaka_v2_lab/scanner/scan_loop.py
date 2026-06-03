"""Pure-function scan loop (port of ``evaluate_one_scan`` from
``bowaka_intraday_scanner.py`` lines 330-546).

§15 remediations applied:

- **Stale-bar enforcement happens BEFORE feature compute** per [Report §15.1 P0]:
  the original archive computed features then sometimes skipped — exposing the
  scanner to lookahead in edge cases.
- **max_entries_per_scan** policy per [Report §15.2 P1]: the emitted candidate
  count is capped at ``min(max_candidates_per_scan, max_entries_per_scan)``
  when both are set.
- Per-symbol gate dumps are returned as a list rather than written via a
  global file handle, so callers (scanner.replay, sim.event_loop) can route
  them anywhere.

Realism Phase 4 (audit P0-003 / P0-006):

- Every ``(scan_ts, symbol)`` tuple produces exactly one gate-dump row, carrying
  ``scan_ts``, the gate result booleans, the gate input values, ``score``,
  ``rank``, ``candidate_emitted`` and ``rejection_reason`` — so the dump is a
  complete per-scan funnel.
- ``signal_expiry_seconds``, ``same_symbol_entries_per_day`` and
  ``symbol_cooldown_minutes`` (the live scanner dedup keys) are honoured across
  scans via the threaded ``state`` dict: a symbol emitted in a recent scan is
  not re-emitted until its cooldown elapses, and once its per-day entry quota is
  hit it is skipped for the rest of the session.
"""
from __future__ import annotations

import enum
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping, Sequence

import pandas as pd

from ..features import (
    aggregate_forming_session_bar,
    apply_v2_gates,
    compute_forming_session_features,
    compute_signal_strength,
    compute_volume_curve_fraction,
    adv_bucket,
)
from ..utils.profile_counters import counters_enabled as _profile_counters_enabled
from ..utils.profile_counters import current_profile_counters as _profile_counters_current
from .event_builder import build_candidate_event


SCAN_SKIP_REASONS: tuple[str, ...] = (
    "already_entered_today",
    "symbol_cooldown",
    "same_symbol_day_cap",
    "no_baselines",
    "bars_fetch_failed",
    "no_bars",
    "stale_bar",
    "gate_failed",
    "max_entries_cap",
)
SCAN_SKIP_REASONS_SET: frozenset[str] = frozenset(SCAN_SKIP_REASONS)


class ScanSkipReason(str, enum.Enum):
    ALREADY_ENTERED_TODAY = "already_entered_today"
    SYMBOL_COOLDOWN = "symbol_cooldown"
    SAME_SYMBOL_DAY_CAP = "same_symbol_day_cap"
    NO_BASELINES = "no_baselines"
    BARS_FETCH_FAILED = "bars_fetch_failed"
    NO_BARS = "no_bars"
    STALE_BAR = "stale_bar"
    GATE_FAILED = "gate_failed"
    MAX_ENTRIES_CAP = "max_entries_cap"


# Speedup report v2 §9.4 / Phase 1 — skip-reason -> ProfileCounters field name.
# Only the per-skip causes have dedicated counters; GATE_FAILED bumps
# ``scanner_gate_failures`` from the gate-evaluation branch (not _record_skip),
# and MAX_ENTRIES_CAP bumps ``scanner_candidates_capped`` from the post-sort
# cap branch. ``BARS_FETCH_FAILED`` falls back to the unmapped path.
_SCAN_SKIP_COUNTER_FIELD: dict[str, str] = {
    ScanSkipReason.ALREADY_ENTERED_TODAY.value: "scanner_skip_already_entered",
    ScanSkipReason.SYMBOL_COOLDOWN.value: "scanner_skip_cooldown",
    ScanSkipReason.SAME_SYMBOL_DAY_CAP.value: "scanner_skip_same_symbol_cap",
    ScanSkipReason.NO_BASELINES.value: "scanner_skip_no_baseline",
    ScanSkipReason.NO_BARS.value: "scanner_skip_no_bars",
    ScanSkipReason.STALE_BAR.value: "scanner_skip_stale_bar",
}


@dataclass
class ScanResult:
    emitted: list[dict[str, Any]] = field(default_factory=list)
    gate_dump: list[dict[str, Any]] = field(default_factory=list)
    universe_size: int = 0
    #: Realism Phase 6 — per-(symbol, scan_ts) quote-coverage rows for each
    #: emitted candidate. Populated by ``sim.event_loop.run_one_scan`` (the
    #: scanner itself leaves it empty); drives ``historical_quote_coverage_pct``.
    quote_coverage: list[dict[str, Any]] = field(default_factory=list)
    #: Speedup report §5.4 / §11.2 Phase 4 — bounded per-reason rejection
    #: counters populated when ``collect_gate_dump=False`` (objective-minimal
    #: mode). Each key is a :class:`ScanSkipReason` value plus
    #: ``"max_entries_cap"`` for the rank-capping fallback; values are
    #: integer counts. Funnel reporting can still compute the
    #: accepted / rejected / per-reason totals from this map.
    rejection_counts: dict[str, int] = field(default_factory=dict)


def _config_hash(cfg: Mapping[str, Any]) -> str:
    payload = json.dumps(cfg, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()[:16]


def _iso_utc(ts: Any) -> str:
    pts = pd.Timestamp(ts)
    if pts.tzinfo is None:
        raise ValueError("scan_loop: tz-naive timestamp rejected")
    return pts.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def evaluate_one_scan(
    *,
    cfg: Mapping[str, Any],
    universe_snapshot: Mapping[str, Any],
    daily_cache: pd.DataFrame | None,
    volume_curve: pd.DataFrame | None,
    state: dict[str, Any],
    scan_ts: Any,
    bars_supplier: Callable[[str, Any], pd.DataFrame | None],
    # Speedup report §5.4 / §11.2 Phase 4 — precomputed per-session context
    # (universe_meta_by_sym, cache_by_sym, config_hash_v, volume_curve
    # fractions). When ``None`` the legacy inline build path is used (no
    # behaviour change). When supplied AND ``collect_gate_dump=False`` the
    # per-symbol nested dump rows are replaced with bounded rejection
    # counters on ``ScanResult.rejection_counts``.
    scan_context: Any = None,
    collect_gate_dump: bool = True,
) -> ScanResult:
    """Pure scan evaluation. ``bars_supplier`` is the only data-side injection.

    ``state`` carries cross-scan dedup memory: ``entered_symbols_today``
    (symbols with an open position — never re-emitted), ``symbol_last_emit_ts``
    (UTC ISO of each symbol's last emitted candidate, for the cooldown gate) and
    ``signal_emits_per_symbol_today`` (per-symbol emitted-candidate counter, for
    the ``same_symbol_entries_per_day`` scanner-dedup cap). The caller threads
    one ``state`` dict through every scan of a session and resets it per session.

    Realism remediation 2 Phase 7 (audit P1-003) renamed the emit counter from
    ``entries_per_symbol_today`` → ``signal_emits_per_symbol_today``. The legacy
    ``entries_per_symbol_today`` key is now driven by the ``Portfolio`` on
    ``PARENT_FILL`` (lots opened today, per symbol) — risk gates that care about
    actual entries should read it from the portfolio state, not from the scanner
    dedup memory. For one-release back-compat the scanner accepts an existing
    ``entries_per_symbol_today`` dict in ``state`` and migrates it.
    """
    scanner_cfg = cfg.get("scanner") or {}
    signals_cfg = cfg.get("signals") or {}
    score_cfg = cfg.get("score") or {}
    market_data_cfg = cfg.get("market_data") or cfg.get("data") or {}
    hf_cfg = (cfg.get("historical_features") or {})
    bucket_edges = list(
        (hf_cfg.get("volume_curve") or {}).get(
            "bucket_edges", [250_000, 500_000, 1_000_000, 5_000_000, 20_000_000],
        )
    )
    fallback_share = float(
        (hf_cfg.get("volume_curve") or {}).get("fallback_opening_15m_share", 0.08)
    )
    # Walk-forward numba speedup Phase 1 — route the per-symbol forming-feature
    # math through the shared compiled kernel when enabled (the SAME kernel the
    # scan-matrix build uses, so build-path and scan-path stay parity-equal).
    # Default OFF; compute_forming_session_features falls back to pure Python
    # when numba is not installed.
    _numba_feats = bool(
        (((cfg.get("optuna") or {}).get("acceleration") or {}).get("numba") or {})
        .get("enabled", False)
    )
    # Per [Report §15.2 P1]: emitted count capped by min(max_candidates_per_scan, max_entries_per_scan).
    max_candidates = int(scanner_cfg.get("max_candidates_per_scan", 25))
    max_entries = int(scanner_cfg.get("max_entries_per_scan", max_candidates))
    effective_cap = max(0, min(max_candidates, max_entries))

    # Per [Report §15.1 P0]: stale-bar enforcement BEFORE feature compute.
    max_bar_age_seconds = int(market_data_cfg.get("max_bar_age_seconds", 90))

    # Realism Phase 4 — live scanner dedup keys (frozen-contract defaults).
    same_symbol_day_cap = int(scanner_cfg.get("same_symbol_entries_per_day", 1))
    symbol_cooldown_minutes = float(scanner_cfg.get("symbol_cooldown_minutes", 390))
    symbol_cooldown = pd.Timedelta(minutes=symbol_cooldown_minutes)

    entered = set(state.get("entered_symbols_today") or [])
    symbol_last_emit_ts: dict[str, str] = state.setdefault("symbol_last_emit_ts", {})
    # Realism remediation 2 Phase 7 (audit P1-003): the scanner-dedup counter
    # is ``signal_emits_per_symbol_today`` (incremented on emission). The legacy
    # ``entries_per_symbol_today`` key is now reserved for portfolio entries
    # (PARENT_FILL) and tracked by the Portfolio. For one-release back-compat
    # the scanner migrates any pre-Phase-7 ``entries_per_symbol_today`` value.
    if "signal_emits_per_symbol_today" not in state:
        legacy = state.get("entries_per_symbol_today")
        if isinstance(legacy, dict) and legacy:
            state["signal_emits_per_symbol_today"] = dict(legacy)
        else:
            state["signal_emits_per_symbol_today"] = {}
    signal_emits_per_symbol: dict[str, int] = state["signal_emits_per_symbol_today"]
    if scan_context is not None:
        universe_meta_by_sym = scan_context.universe_meta_by_sym
        cache_by_sym = scan_context.cache_by_sym
        config_hash_v = scan_context.config_hash_v
    else:
        universe_meta_by_sym = {
            s["symbol"]: s for s in universe_snapshot.get("symbols", [])
        }
        cache_by_sym = {}
        if daily_cache is not None and not daily_cache.empty:
            for _, row in daily_cache.iterrows():
                cache_by_sym[row["symbol"]] = row.to_dict()
        config_hash_v = _config_hash(cfg)

    universe_hash = universe_snapshot.get("universe_hash", "sha256:unknown")

    scan_ts_obj = pd.Timestamp(scan_ts)
    if scan_ts_obj.tzinfo is None:
        raise ValueError("evaluate_one_scan: scan_ts must be tz-aware")
    scan_iso = _iso_utc(scan_ts)

    def _row(symbol: str, **extra: Any) -> dict[str, Any]:
        """Base gate-dump row — every (scan_ts, symbol) tuple gets exactly one.

        ``scan_ts`` / ``candidate_emitted`` / ``rejection_reason`` are always
        present (Phase 4 contract). ``rejection_reason`` is ``None`` for a
        symbol that emitted a candidate.
        """
        base: dict[str, Any] = {
            "scan_ts": scan_iso,
            "scan_timestamp": scan_iso,  # back-compat column name
            "symbol": symbol,
            "candidate_emitted": False,
            "rejection_reason": None,
            "score": None,
            "rank": None,
        }
        base.update(extra)
        return base

    def _skip(symbol: str, reason: ScanSkipReason, **extra: Any) -> dict[str, Any]:
        """Gate-dump row for a skipped symbol (records ``skipped`` + ``rejection_reason``)."""
        return _row(
            symbol,
            skipped=reason.value,
            rejection_reason=reason.value,
            **extra,
        )

    result = ScanResult(universe_size=len(universe_meta_by_sym))

    def _record_skip(symbol: str, reason: ScanSkipReason, **extra: Any) -> None:
        """Append the per-symbol gate-dump row OR bump a rejection counter
        depending on ``collect_gate_dump`` (speedup report §5.4 / Phase 4).

        Speedup report v2 §9.4 / Phase 1 — additionally bump the per-reason
        ``scanner_skip_*`` ProfileCounters field when counters are enabled.
        """
        if collect_gate_dump:
            result.gate_dump.append(_skip(symbol, reason, **extra))
        else:
            result.rejection_counts[reason.value] = (
                int(result.rejection_counts.get(reason.value, 0)) + 1
            )
        # Phase 1 skip-reason counter (no-op when counters are disabled).
        if _profile_counters_enabled():
            field_name = _SCAN_SKIP_COUNTER_FIELD.get(reason.value)
            if field_name is not None:
                try:
                    _profile_counters_current().inc(**{field_name: 1})
                except LookupError:
                    pass
    passing: list[tuple[float, dict[str, Any]]] = []
    # Gate-dump rows for symbols that passed gates — finalised after ranking so
    # rank / candidate_emitted reflect the per-scan cap.
    passing_rows: dict[str, dict[str, Any]] = {}
    # Speedup report v2 §9.4 / Phase 1 — cache the enabled flag once per scan
    # so the per-symbol fast path is a single boolean check.
    _counters_on = _profile_counters_enabled()

    def _bump(**kwargs: Any) -> None:
        """No-op when counters are disabled; otherwise inc the current bag."""
        if _counters_on:
            try:
                _profile_counters_current().inc(**kwargs)
            except LookupError:
                pass

    for symbol, meta in universe_meta_by_sym.items():
        _bump(scanner_symbols_seen=1)
        if symbol in entered:
            _record_skip(symbol, ScanSkipReason.ALREADY_ENTERED_TODAY)
            continue

        # Realism Phase 4 + remediation 2 Phase 7 — same_symbol_entries_per_day
        # cap is keyed on the EMIT counter (scanner-dedup), per audit P1-003.
        # The accepted/filled entry count lives on Portfolio.state.
        if signal_emits_per_symbol.get(symbol, 0) >= same_symbol_day_cap > 0:
            _record_skip(
                symbol, ScanSkipReason.SAME_SYMBOL_DAY_CAP,
                signal_emits_today=int(signal_emits_per_symbol.get(symbol, 0)),
                # Back-compat alias of the prior dump-row key:
                entries_today=int(signal_emits_per_symbol.get(symbol, 0)),
                same_symbol_entries_per_day=same_symbol_day_cap,
            )
            continue

        # Realism Phase 4 — symbol cooldown: skip if emitted within cooldown.
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
        if scan_context is not None:
            vcf_map = scan_context.volume_curve_fraction_by_scan_bucket
            vcf = vcf_map.get((scan_ts_obj, bucket))
            if vcf is None:
                # The session context did not precompute this (scan_ts, bucket)
                # pair (e.g. a symbol whose bucket was not present at build
                # time). Fall back to the per-call computation.
                vcf = compute_volume_curve_fraction(
                    volume_curve, scan_ts_obj, bucket,
                    fallback_opening_15m_share=fallback_share,
                )
        else:
            vcf = compute_volume_curve_fraction(
                volume_curve, scan_ts_obj, bucket,
                fallback_opening_15m_share=fallback_share,
            )

        # Fetch minute bars.
        _t0 = time.perf_counter() if _counters_on else 0.0
        try:
            bars = bars_supplier(symbol, scan_ts_obj)
        except Exception as e:
            if _counters_on:
                _bump(scanner_time_bars_supplier_seconds=time.perf_counter() - _t0)
            _record_skip(symbol, ScanSkipReason.BARS_FETCH_FAILED, error=str(e)[:200])
            continue
        if _counters_on:
            _bump(scanner_time_bars_supplier_seconds=time.perf_counter() - _t0)
        if bars is None or len(bars) == 0:
            _record_skip(symbol, ScanSkipReason.NO_BARS)
            continue

        # STALE BAR CHECK — per [Report §15.1 P0], BEFORE feature compute.
        _t_stale = time.perf_counter() if _counters_on else 0.0
        ts_col = None
        for c in bars.columns:
            if c.lower() in ("timestamp", "ts"):
                ts_col = c
                break
        stale_skipped = False
        if ts_col is not None:
            last_bar_ts = pd.Timestamp(bars[ts_col].iloc[-1])
            if last_bar_ts.tzinfo is None:
                # Reject naive — same policy as features module.
                if _counters_on:
                    _bump(scanner_time_stale_check_seconds=time.perf_counter() - _t_stale)
                _record_skip(
                    symbol, ScanSkipReason.STALE_BAR, reason="naive_timestamp",
                )
                stale_skipped = True
            else:
                age_seconds = (scan_ts_obj - last_bar_ts).total_seconds()
                if age_seconds > max_bar_age_seconds:
                    if _counters_on:
                        _bump(scanner_time_stale_check_seconds=time.perf_counter() - _t_stale)
                    _record_skip(
                        symbol, ScanSkipReason.STALE_BAR,
                        bar_age_seconds=float(age_seconds),
                        max_bar_age_seconds=max_bar_age_seconds,
                    )
                    stale_skipped = True
        if stale_skipped:
            continue
        if _counters_on and ts_col is not None:
            _bump(scanner_time_stale_check_seconds=time.perf_counter() - _t_stale)

        _t_agg = time.perf_counter() if _counters_on else 0.0
        sess = aggregate_forming_session_bar(bars)
        if _counters_on:
            _bump(scanner_time_aggregate_seconds=time.perf_counter() - _t_agg)
        _t_feat = time.perf_counter() if _counters_on else 0.0
        feats = compute_forming_session_features(sess, baselines, vcf, use_numba=_numba_feats)
        if _counters_on:
            _bump(scanner_time_features_seconds=time.perf_counter() - _t_feat)
        _t_gate = time.perf_counter() if _counters_on else 0.0
        ok, gates = apply_v2_gates(
            feats, signals_cfg,
            price=sess.get("last_price"),
            avg_dollar_volume_20d=adv,
            prior_atr_pct=prior_atr_pct,
            ema_slope_prior=ema_slope,
            instrument_class=meta.get("instrument_class"),
        )
        if _counters_on:
            _bump(scanner_time_gates_seconds=time.perf_counter() - _t_gate)
        if ok:
            _t_score = time.perf_counter() if _counters_on else 0.0
            score = compute_signal_strength(feats, score_cfg, ema_slope_prior=ema_slope)
            if _counters_on:
                _bump(scanner_time_score_seconds=time.perf_counter() - _t_score)
        else:
            score = None
        if not ok:
            # Speedup report v2 §9.5 / Phase 1 — defer the dump_row allocation
            # in the objective-minimal path (the dominant code path). When
            # collect_gate_dump=True, build the full row as before; when
            # False, only bump the rejection counter and skip the dict build.
            _bump(scanner_gate_failures=1)
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

        # Passing branch: the row is needed by the post-sort emit/cap pass for
        # passing_rows[symbol] mutations (rank, candidate_emitted, etc.) — so
        # we keep building it even when ``collect_gate_dump=False``. (Per the
        # speedup report v2 §9.5 conservative recommendation.)
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

        _t_event = time.perf_counter() if _counters_on else 0.0
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
        if _counters_on:
            _bump(scanner_time_event_builder_seconds=time.perf_counter() - _t_event)
        passing.append((score, ev))
        passing_rows[symbol] = dump_row

    _t_sort = time.perf_counter() if _counters_on else 0.0
    passing.sort(key=lambda x: -x[0])
    if _counters_on:
        _bump(scanner_time_sort_rank_seconds=time.perf_counter() - _t_sort)
    for rank, (score, ev) in enumerate(passing, start=1):
        ev["candidate_rank"] = rank
        row = passing_rows[ev["symbol"]]
        row["rank"] = rank
        if rank <= effective_cap:
            result.emitted.append(ev)
            _bump(scanner_candidates_built=1)
            row["candidate_emitted"] = True
            state.setdefault("in_play_pool", {})[ev["symbol"]] = {
                "last_signal_ts": ev["scan_timestamp"],
                "signal_expiry_ts": ev["signal_expiry_timestamp"],
                "last_signal_strength": ev["features"]["signal_strength"],
            }
            # Realism Phase 4 + remediation 2 Phase 7 — record emit for cooldown
            # + per-day emit cap. The portfolio entry counter (PARENT_FILL) is
            # NOT touched here; it is maintained on Portfolio.state via
            # add_position. Per audit P1-003 the scanner-dedup view (emits) and
            # the risk-gate view (filled entries) must be distinct.
            symbol_last_emit_ts[ev["symbol"]] = scan_iso
            signal_emits_per_symbol[ev["symbol"]] = signal_emits_per_symbol.get(ev["symbol"], 0) + 1
        else:
            # Passed gates but capped by max_entries_per_scan.
            _bump(scanner_candidates_capped=1)
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
    if _profile_counters_enabled() and result.gate_dump:
        try:
            _profile_counters_current().inc(
                gate_dump_rows_constructed=len(result.gate_dump),
            )
        except LookupError:
            pass
    return result
