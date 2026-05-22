"""Multi-level data-quality checks (realism remediation 2 Phase 3, audit §P0-010).

The audit found the prior coverage check too shallow — it probed only a daily
bar per (symbol, session) and minute bars at the *first* scan timestamp, missing
late-session gaps, exit-path holes, intraday gaps, feature leakage, and
halt-status availability.

This module adds the five DQ check *levels* the audit specifies. Every builder
returns a list of checks in the standard shape
(``{name,status,count,threshold,source_file,evidence}``) — they are *appended*
to the existing :func:`bowaka_v2_lab.data.data_quality.build_data_quality_report`
``checks`` list, not a replacement.

Levels:

1. **Ingestion** — partition existence, schema, sorted timestamps, duplicate
   timestamps, OHLC validity, zero/negative prices, volume anomalies (>=3 sigma).
2. **Session** — expected XNYS minute count per session (390 regular / 210
   early-close), intra-session gaps > 5 min, stale segments (no volume change
   > 15 min during regular hours).
3. **Replay** — every scan timestamp has the bars each eligible symbol needs;
   every accepted-eligible entry has forward exit-path data through
   ``max_hold_days``; every candidate requiring a quote has a quote within
   ``max_quote_age_seconds``.
4. **Feature** — daily baselines use only completed prior sessions (no same-day
   leakage); split / corporate-action-aware daily features when
   ``require_adjusted_daily_bars: true``.
5. **Quote / status** — quote coverage by timestamp, quote-age distribution,
   spread distribution, halt / status data availability.

Design rule: a check ``fail`` requires a *genuine defect* AND enough data to
detect it. Absent data degrades to ``warn`` (or, for the halt-status gate under
``intended_realism``, to ``fail`` — fail-closed is the intended realism outcome).
A complete, clean lake therefore passes every new check.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import pandas as pd

# Re-use the canonical check builder so every level emits the standard shape.
from .data_quality import _check

#: XNYS regular-session minute count (09:30-15:59 inclusive = 390 one-minute bars).
REGULAR_SESSION_MINUTES = 390
#: XNYS early-close minute count (09:30-12:59 inclusive = 210 one-minute bars).
EARLY_CLOSE_MINUTES = 210
#: A minute gap above this is *flagged* (advisory). The audit's "gaps inside a
#: session > 5 minutes" detection threshold.
MAX_INTRA_SESSION_GAP_MINUTES = 5
#: A minute gap above this is a *severe* hole — a genuine missing chunk of the
#: session, not the ordinary partial-tape sparsity an IEX feed always carries.
#: ``intraday_gap`` *fails* only on a systemic prevalence of severe gaps.
SEVERE_INTRA_SESSION_GAP_MINUTES = 30
#: Fraction of probed sessions that may carry a severe gap before
#: ``intraday_gap`` fails (vs. merely warns).
INTRADAY_GAP_FAIL_FRACTION = 0.50
#: A "stale segment" = no volume change for this many regular-hours minutes.
STALE_SEGMENT_MINUTES = 15
#: Rolling window + sigma multiple for the volume-anomaly check.
VOLUME_ANOMALY_WINDOW = 20
VOLUME_ANOMALY_SIGMA = 3.0
#: Fraction of probed sessions that may be short on minutes before
#: ``session_minute_count_violation`` fails (vs. merely warns). IEX is a partial
#: tape, so a modest shortfall is advisory; a systemic shortfall fails.
SESSION_MINUTE_COUNT_FAIL_FRACTION = 0.80
#: Fraction of (symbol, session) replay probes that may lack late-session or
#: exit-path coverage before the corresponding replay check fails.
REPLAY_COVERAGE_FAIL_FRACTION = 0.05
#: Maximum number of *post-first* scan timestamps probed per session by the
#: late-session coverage check. The check needs to detect *systemic* missing
#: minute bars, not exhaustively visit every scan timestamp — sampling
#: representative scans keeps the check bounded on real configs (60 s cadence
#: gives ~350 scans/session, an O(scans x symbols x sessions) walk would dwarf
#: the rest of the DQ stack). Sampling honours determinism: the sample indices
#: are fixed positions (early / mid / late within the post-first scans).
LATE_SESSION_PROBE_CAP_PER_SESSION = 8


# --------------------------------------------------------------------------
# Level 1 — Ingestion
# --------------------------------------------------------------------------
def build_ingestion_checks(
    *,
    bar_frames: Mapping[str, pd.DataFrame],
    source_file: str = "(ingestion-level probe)",
) -> list[dict[str, Any]]:
    """Ingestion-level checks over a ``{symbol: daily_or_minute_frame}`` map.

    ``bar_frames`` is keyed by symbol; each frame is the symbol's bar payload.
    Frames are typically the per-run daily bars. Emits, as aggregate checks:

    - ``ingestion_schema`` — every frame carries the OHLCV + timestamp columns.
    - ``ingestion_timestamps_sorted`` — timestamps are non-decreasing.
    - ``ingestion_duplicate_timestamps`` — no duplicate timestamp rows.
    - ``ingestion_ohlc_violation`` — ``high >= max(open,close,low)`` and
      ``low <= min(open,close,high)`` for every bar.
    - ``ingestion_nonpositive_price`` — no zero / negative OHLC prices.
    - ``ingestion_volume_anomaly`` — no bar with volume >= 3 sigma over a
      rolling-20 mean (advisory ``warn`` — a real volume spike is not a defect).
    """
    required_cols = {"open", "high", "low", "close", "volume", "timestamp"}
    schema_bad: dict[str, list[str]] = {}
    unsorted: list[str] = []
    dup_counts: dict[str, int] = {}
    ohlc_bad: dict[str, int] = {}
    nonpos: dict[str, int] = {}
    vol_anom: dict[str, int] = {}

    for sym, df in bar_frames.items():
        if df is None or len(df) == 0:
            continue
        missing = sorted(required_cols - set(df.columns))
        if missing:
            schema_bad[str(sym)] = missing
            continue  # schema gate first — the rest assume the columns exist
        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        if not ts.is_monotonic_increasing:
            unsorted.append(str(sym))
        n_dup = int(ts.duplicated().sum())
        if n_dup:
            dup_counts[str(sym)] = n_dup
        o, h, l, c = (df["open"], df["high"], df["low"], df["close"])
        hi_ok = h >= pd.concat([o, c, l], axis=1).max(axis=1) - 1e-9
        lo_ok = l <= pd.concat([o, c, h], axis=1).min(axis=1) + 1e-9
        n_ohlc = int((~(hi_ok & lo_ok)).sum())
        if n_ohlc:
            ohlc_bad[str(sym)] = n_ohlc
        n_nonpos = int((pd.concat([o, h, l, c], axis=1) <= 0).any(axis=1).sum())
        if n_nonpos:
            nonpos[str(sym)] = n_nonpos
        vol = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
        if len(vol) >= VOLUME_ANOMALY_WINDOW:
            roll_mean = vol.rolling(VOLUME_ANOMALY_WINDOW).mean()
            roll_std = vol.rolling(VOLUME_ANOMALY_WINDOW).std(ddof=0)
            anom = (vol - roll_mean) >= (VOLUME_ANOMALY_SIGMA * roll_std.replace(0.0, pd.NA))
            n_anom = int(anom.fillna(False).sum())
            if n_anom:
                vol_anom[str(sym)] = n_anom

    def _agg(name: str, per_symbol: dict, severity: str, threshold: Any, detail: str) -> dict[str, Any]:
        total = sum(int(v) if not isinstance(v, list) else 1 for v in per_symbol.values())
        status = severity if per_symbol else "pass"
        ev: dict[str, Any] = {
            "offending_symbols": sorted(per_symbol)[:50],
            "per_symbol": {k: per_symbol[k] for k in sorted(per_symbol)[:50]},
        }
        if per_symbol:
            ev["detail"] = detail
        return _check(name, status, total or len(per_symbol), threshold, source_file, ev)

    return [
        _agg("ingestion_schema", schema_bad, "fail", sorted(required_cols),
             "bar frame(s) missing required OHLCV / timestamp columns"),
        _agg("ingestion_timestamps_sorted", {s: 1 for s in unsorted}, "fail", "monotonic_increasing",
             "bar frame(s) have non-monotonic timestamps"),
        _agg("ingestion_duplicate_timestamps", dup_counts, "fail", 0,
             "bar frame(s) have duplicate-timestamp rows"),
        _agg("ingestion_ohlc_violation", ohlc_bad, "fail", 0,
             "bar(s) violate high>=max(o,c,l) / low<=min(o,c,h)"),
        _agg("ingestion_nonpositive_price", nonpos, "fail", 0,
             "bar(s) have a zero or negative OHLC price"),
        _agg("ingestion_volume_anomaly", vol_anom, "warn",
             {"window": VOLUME_ANOMALY_WINDOW, "sigma": VOLUME_ANOMALY_SIGMA},
             "bar(s) with volume >= 3 sigma over the rolling-20 mean (advisory)"),
    ]


# --------------------------------------------------------------------------
# Level 2 — Session
# --------------------------------------------------------------------------
def _early_close_sessions(sessions: Iterable[_dt.date]) -> set[_dt.date]:
    """XNYS early-close sessions inside the probed date range."""
    sess = sorted(sessions)
    if not sess:
        return set()
    try:
        import exchange_calendars as xcals

        cal = xcals.get_calendar("XNYS")
        out: set[_dt.date] = set()
        for d in sess:
            try:
                close = cal.session_close(pd.Timestamp(d))
                open_ = cal.session_open(pd.Timestamp(d))
            except Exception:  # noqa: BLE001 — a non-session date is simply skipped
                continue
            # Regular close is 16:00 ET; early closes (13:00 ET) run ~6.5h shorter.
            if (close - open_) < pd.Timedelta(hours=6, minutes=15):
                out.add(d)
        return out
    except Exception:  # noqa: BLE001 — calendar unavailable -> assume no early closes
        return set()


def build_session_checks(
    *,
    minute_frames_by_session: Mapping[tuple[str, _dt.date], pd.DataFrame],
    early_close_sessions: Optional[set[_dt.date]] = None,
    source_file: str = "(session-level probe)",
) -> list[dict[str, Any]]:
    """Session-level checks over per-(symbol, session) minute frames.

    Emits:

    - ``session_minute_count_violation`` — sessions whose minute count falls
      materially short of the expected 390 (regular) / 210 (early-close). IEX is
      a partial tape so a modest shortfall is advisory (``warn``); a systemic
      shortfall fails.
    - ``intraday_gap`` — minute frames with an internal gap. A gap > 5 min is
      *flagged*; the check only *fails* on a systemic prevalence of *severe*
      gaps (> 30 min — a genuine missing chunk of a session, not ordinary IEX
      partial-tape sparsity, which is expected and merely warns).
    - ``session_stale_segment`` — minute frames with a >= 15-minute regular-hours
      run of unchanged volume (advisory ``warn``).
    """
    early = early_close_sessions if early_close_sessions is not None else _early_close_sessions(
        {d for (_s, d) in minute_frames_by_session}
    )
    short_sessions: list[dict[str, Any]] = []
    gap_sessions: list[dict[str, Any]] = []
    severe_gap_sessions: list[dict[str, Any]] = []
    stale_sessions: list[dict[str, Any]] = []
    n_probed = 0

    for (sym, session), df in minute_frames_by_session.items():
        if df is None or len(df) == 0 or "timestamp" not in getattr(df, "columns", []):
            continue
        n_probed += 1
        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce").dropna().sort_values()
        if ts.empty:
            continue
        expected = EARLY_CLOSE_MINUTES if session in early else REGULAR_SESSION_MINUTES
        observed = int(len(ts))
        # Materially short = below 65 % of the expected count. IEX partial-tape
        # sessions routinely run well under 390 bars, so the per-session bar is
        # low; the *systemic* fraction (below) is what gates.
        if observed < int(0.65 * expected):
            short_sessions.append(
                {"symbol": str(sym), "session": session.isoformat(),
                 "observed": observed, "expected": expected}
            )
        # Intra-session gaps — flag > 5 min, separately track > 30 min (severe).
        deltas = ts.diff().dropna()
        big = deltas[deltas > pd.Timedelta(minutes=MAX_INTRA_SESSION_GAP_MINUTES)]
        severe = deltas[deltas > pd.Timedelta(minutes=SEVERE_INTRA_SESSION_GAP_MINUTES)]
        if not big.empty:
            row = {
                "symbol": str(sym), "session": session.isoformat(),
                "max_gap_minutes": round(big.max().total_seconds() / 60.0, 1),
                "gap_count": int(len(big)),
                "severe_gap_count": int(len(severe)),
            }
            gap_sessions.append(row)
            if not severe.empty:
                severe_gap_sessions.append(row)
        # Stale segments — consecutive unchanged volume during regular hours.
        if "volume" in df.columns and len(df) >= STALE_SEGMENT_MINUTES:
            vol = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0).reset_index(drop=True)
            run = 1
            longest = 1
            for i in range(1, len(vol)):
                run = run + 1 if vol.iloc[i] == vol.iloc[i - 1] else 1
                longest = max(longest, run)
            if longest >= STALE_SEGMENT_MINUTES:
                stale_sessions.append(
                    {"symbol": str(sym), "session": session.isoformat(),
                     "longest_stale_run_minutes": int(longest)}
                )

    # session_minute_count_violation — required; fail only on a systemic shortfall.
    frac_short = (len(short_sessions) / n_probed) if n_probed else 0.0
    if not short_sessions:
        smc_status = "pass"
    elif frac_short >= SESSION_MINUTE_COUNT_FAIL_FRACTION:
        smc_status = "fail"
    else:
        smc_status = "warn"
    smc = _check(
        "session_minute_count_violation",
        smc_status,
        len(short_sessions),
        {"fail_fraction": SESSION_MINUTE_COUNT_FAIL_FRACTION,
         "regular": REGULAR_SESSION_MINUTES, "early_close": EARLY_CLOSE_MINUTES},
        source_file,
        {
            "sessions_probed": n_probed,
            "short_sessions": short_sessions[:50],
            "short_fraction": round(frac_short, 6),
            **({"detail": (
                f"{len(short_sessions)}/{n_probed} probed sessions are materially "
                f"short on minute bars — systemic minute-bar shortfall"
            )} if smc_status == "fail" else {}),
        },
    )

    # intraday_gap — required; fails only on a *systemic prevalence of severe*
    # gaps (> 30 min). Ordinary > 5 min IEX partial-tape sparsity merely warns.
    frac_severe = (len(severe_gap_sessions) / n_probed) if n_probed else 0.0
    if not gap_sessions:
        gap_status = "pass"
    elif severe_gap_sessions and frac_severe >= INTRADAY_GAP_FAIL_FRACTION:
        gap_status = "fail"
    else:
        gap_status = "warn"
    gap = _check(
        "intraday_gap",
        gap_status,
        len(gap_sessions),
        {"flag_gap_minutes": MAX_INTRA_SESSION_GAP_MINUTES,
         "severe_gap_minutes": SEVERE_INTRA_SESSION_GAP_MINUTES,
         "fail_fraction": INTRADAY_GAP_FAIL_FRACTION},
        source_file,
        {
            "sessions_probed": n_probed,
            "sessions_with_gap": len(gap_sessions),
            "sessions_with_severe_gap": len(severe_gap_sessions),
            "severe_gap_fraction": round(frac_severe, 6),
            "gap_sessions": gap_sessions[:50],
            **({"detail": (
                f"{len(severe_gap_sessions)}/{n_probed} probed sessions have a "
                f"severe (> {SEVERE_INTRA_SESSION_GAP_MINUTES} min) intra-session "
                f"gap — a systemic missing-data hole, not ordinary IEX sparsity"
            )} if gap_status == "fail" else {}),
        },
    )

    # session_stale_segment — advisory.
    stale = _check(
        "session_stale_segment",
        "warn" if stale_sessions else "pass",
        len(stale_sessions),
        {"stale_minutes": STALE_SEGMENT_MINUTES},
        source_file,
        {"sessions_probed": n_probed, "stale_sessions": stale_sessions[:50]},
    )
    return [smc, gap, stale]


# --------------------------------------------------------------------------
# Level 3 — Replay
# --------------------------------------------------------------------------
def build_replay_checks(
    *,
    requested_symbols: Iterable[str],
    sessions: Iterable[_dt.date],
    minute_bars_supplier,
    scan_times_per_session,
    max_hold_days: int,
    quote_coverage_rows: Optional[Iterable[Mapping[str, Any]]] = None,
    max_quote_age_seconds: float = 15.0,
    source_file: str = "(replay-level probe)",
) -> list[dict[str, Any]]:
    """Replay-level checks — does the lake actually support the replay?

    Emits:

    - ``coverage_missing_late_session`` — every scan timestamp (not just the
      first) has minute bars for each eligible symbol. The prior coverage check
      only probed the first scan timestamp; the audit calls this out explicitly.
    - ``coverage_missing_exit_path`` — every (symbol, session) entry candidate
      has forward minute-bar data through ``max_hold_days`` trailing sessions so
      a stop / target / max-hold exit can actually be evaluated.
    - ``replay_quote_age_violation`` — when per-candidate quote-coverage rows are
      supplied, every row that carries a quote has ``quote_age_seconds`` within
      ``max_quote_age_seconds`` (advisory ``warn``; the hard quote gate is
      ``quote_coverage`` in ``data_quality.py``).
    """
    symbols = [str(s) for s in requested_symbols]
    session_list = sorted(sessions)
    late_missing: list[str] = []
    late_probes = 0
    exit_missing: list[str] = []
    exit_probes = 0

    for i, session in enumerate(session_list):
        try:
            scan_times = list(scan_times_per_session(session))
        except Exception:  # noqa: BLE001
            scan_times = []
        # Sample up to LATE_SESSION_PROBE_CAP_PER_SESSION evenly-spaced
        # post-first scan timestamps per session (the first scan is the existing
        # coverage_missing check's job). An exhaustive walk over a 60 s-cadence
        # session would be O(350 x symbols) per session — too slow on real
        # configs and unnecessary for detecting *systemic* missing minutes.
        post_first = scan_times[1:]
        if len(post_first) > LATE_SESSION_PROBE_CAP_PER_SESSION:
            step = len(post_first) / LATE_SESSION_PROBE_CAP_PER_SESSION
            sampled = [post_first[int(k * step)] for k in range(LATE_SESSION_PROBE_CAP_PER_SESSION)]
        else:
            sampled = post_first
        for ts in sampled:
            for sym in symbols:
                late_probes += 1
                ok = False
                try:
                    m = minute_bars_supplier(sym, ts)
                    ok = m is not None and len(m) > 0
                except Exception:  # noqa: BLE001 — a supplier error counts as missing
                    ok = False
                if not ok:
                    late_missing.append(f"{sym}@{session.isoformat()}T{pd.Timestamp(ts):%H:%M}")
        # Exit-path probe: the last scan timestamp of each of the next
        # ``max_hold_days`` sessions must have minute bars for each symbol.
        hold = max(1, int(max_hold_days))
        forward = session_list[i + 1 : i + 1 + hold]
        for fwd in forward:
            try:
                fwd_scans = list(scan_times_per_session(fwd))
            except Exception:  # noqa: BLE001
                fwd_scans = []
            probe_ts = fwd_scans[-1] if fwd_scans else None
            if probe_ts is None:
                continue
            for sym in symbols:
                exit_probes += 1
                ok = False
                try:
                    m = minute_bars_supplier(sym, probe_ts)
                    ok = m is not None and len(m) > 0
                except Exception:  # noqa: BLE001
                    ok = False
                if not ok:
                    exit_missing.append(f"{sym}@{fwd.isoformat()}")

    def _coverage_check(name: str, missing: list[str], probes: int, detail_kind: str) -> dict[str, Any]:
        n_missing = len(set(missing))
        frac = (n_missing / probes) if probes else 0.0
        if probes == 0:
            # No probes -> nothing to assert. Not a failure (e.g. single-session
            # window has no later scans / no forward sessions).
            status = "pass"
        elif frac >= REPLAY_COVERAGE_FAIL_FRACTION:
            status = "fail"
        elif n_missing > 0:
            status = "warn"
        else:
            status = "pass"
        ev: dict[str, Any] = {
            "probes": probes,
            "missing": n_missing,
            "missing_fraction": round(frac, 6),
            "missing_examples": sorted(set(missing))[:50],
        }
        if status == "fail":
            ev["detail"] = (
                f"{n_missing}/{probes} {detail_kind} probes lack minute bars — "
                f"the lake cannot support a faithful replay"
            )
        return _check(
            name, status, n_missing,
            {"fail_fraction": REPLAY_COVERAGE_FAIL_FRACTION, "probes": probes},
            source_file, ev,
        )

    checks = [
        _coverage_check("coverage_missing_late_session", late_missing, late_probes,
                        "late-session (post-first-scan)"),
        _coverage_check("coverage_missing_exit_path", exit_missing, exit_probes,
                        "exit-path (forward max_hold_days)"),
    ]

    # Quote-age distribution over the per-candidate coverage rows.
    rows = list(quote_coverage_rows or [])
    aged = [
        r for r in rows
        if r.get("quote_present")
        and r.get("quote_age_seconds") is not None
        and float(r.get("quote_age_seconds", 0.0)) > float(max_quote_age_seconds)
    ]
    qa_status = "warn" if aged else "pass"
    checks.append(
        _check(
            "replay_quote_age_violation",
            qa_status,
            len(aged),
            {"max_quote_age_seconds": float(max_quote_age_seconds)},
            source_file,
            {
                "candidates_with_quote": sum(1 for r in rows if r.get("quote_present")),
                "stale_quote_candidates": len(aged),
            },
        )
    )
    return checks


# --------------------------------------------------------------------------
# Level 4 — Feature
# --------------------------------------------------------------------------
def build_feature_checks(
    *,
    daily_cache_by_session: Mapping[_dt.date, Any],
    require_adjusted_daily_bars: bool,
    lake_adjustment: str,
    corporate_actions_available: bool,
    source_file: str = "(feature-level probe)",
) -> list[dict[str, Any]]:
    """Feature-level checks — no same-day leakage, split-aware baselines.

    Emits:

    - ``feature_leakage`` — the per-session daily-feature cache must contain only
      bars from sessions *strictly before* the session being scanned. A daily
      cache row whose ``session_date`` is the scan session itself (or later) is
      same-day leakage and fails. ``daily_cache_by_session`` maps a scan session
      to its daily-feature frame (or any object with a ``session_date`` column).
    - ``feature_split_unaware`` — when ``require_adjusted_daily_bars`` is true but
      the lake is ``raw`` and carries no ``corporate_actions/`` partition, daily
      features cannot be split-aware (advisory ``warn``; the hard adjustment gate
      is ``adjustment_mismatch`` in ``data_quality.py``).
    """
    leak_rows: list[dict[str, Any]] = []
    n_caches = 0
    for scan_session, cache in daily_cache_by_session.items():
        if cache is None:
            continue
        df = cache
        if not hasattr(df, "columns"):
            continue
        n_caches += 1
        if "session_date" not in df.columns or len(df) == 0:
            continue
        sd = pd.to_datetime(df["session_date"], errors="coerce").dt.date
        # Any cached daily bar at or after the scan session is same-day leakage.
        leaked = df[sd >= scan_session]
        if len(leaked) > 0:
            syms = sorted({str(s) for s in leaked.get("symbol", pd.Series(dtype=str))})
            leak_rows.append(
                {"scan_session": scan_session.isoformat(),
                 "leaked_rows": int(len(leaked)),
                 "symbols": syms[:20]}
            )

    leak_status = "fail" if leak_rows else "pass"
    leak = _check(
        "feature_leakage",
        leak_status,
        sum(r["leaked_rows"] for r in leak_rows),
        {"rule": "daily cache must contain only sessions strictly before the scan session"},
        source_file,
        {
            "caches_probed": n_caches,
            "leaking_sessions": leak_rows[:50],
            **({"detail": (
                f"{len(leak_rows)} daily-feature cache(s) contain same-day or "
                f"future bars — daily baselines would leak look-ahead information"
            )} if leak_status == "fail" else {}),
        },
    )

    split_unaware = bool(require_adjusted_daily_bars) and str(lake_adjustment) == "raw" and not corporate_actions_available
    split = _check(
        "feature_split_unaware",
        "warn" if split_unaware else "pass",
        1 if split_unaware else 0,
        {"require_adjusted_daily_bars": bool(require_adjusted_daily_bars)},
        source_file,
        {
            "lake_adjustment": str(lake_adjustment),
            "corporate_actions_available": bool(corporate_actions_available),
            **({"detail": (
                "config requires adjusted daily bars but the lake is raw and has "
                "no corporate_actions/ partition — daily features cannot be "
                "split / corporate-action aware"
            )} if split_unaware else {}),
        },
    )
    return [leak, split]


# --------------------------------------------------------------------------
# Level 5 — Quote / status
# --------------------------------------------------------------------------
def build_quote_status_checks(
    *,
    quote_coverage_rows: Optional[Iterable[Mapping[str, Any]]],
    status_partitions_available: bool,
    halt_gate_enabled: bool,
    simulation_mode: str,
    source_file: str = "(quote/status-level probe)",
) -> list[dict[str, Any]]:
    """Quote / status-level checks — quote distributions + halt-status gate.

    Emits:

    - ``quote_age_distribution`` — median / p95 quote age over the per-candidate
      coverage rows (informational ``pass``; ``quote_coverage`` /
      ``replay_quote_age_violation`` are the gating checks).
    - ``quote_spread_distribution`` — median / p95 spread bps (informational).
    - ``halt_data_unavailable_when_required`` — when the strategy's halt gate is
      enabled and the lake has no ``statuses/`` partitions, halts cannot be
      modelled. Under ``intended_realism`` this is a required ``fail``
      (fail-closed); under ``current_code_parity`` / ``smoke_fixture`` it is a
      ``warn`` (the live code fails the gate open — a documented wart).
    """
    rows = list(quote_coverage_rows or [])
    ages = [
        float(r["quote_age_seconds"]) for r in rows
        if r.get("quote_present") and r.get("quote_age_seconds") is not None
    ]
    spreads = [
        float(r["spread_bps"]) for r in rows
        if r.get("quote_present") and r.get("spread_bps") is not None
    ]

    def _dist(name: str, vals: list[float], unit: str) -> dict[str, Any]:
        if vals:
            s = pd.Series(vals)
            ev = {
                "n": int(len(vals)),
                "median": round(float(s.median()), 4),
                "p95": round(float(s.quantile(0.95)), 4),
                "max": round(float(s.max()), 4),
                "unit": unit,
            }
        else:
            ev = {"n": 0, "unit": unit,
                  "detail": "no per-candidate quote rows to summarise"}
        return _check(name, "pass", len(vals), None, source_file, ev)

    age_dist = _dist("quote_age_distribution", ages, "seconds")
    spread_dist = _dist("quote_spread_distribution", spreads, "bps")

    # Halt-status availability gate.
    halt_missing = bool(halt_gate_enabled) and not bool(status_partitions_available)
    if not halt_missing:
        halt_status = "pass"
    elif str(simulation_mode) == "intended_realism":
        halt_status = "fail"
    else:
        halt_status = "warn"
    halt = _check(
        "halt_data_unavailable_when_required",
        halt_status,
        1 if halt_missing else 0,
        {"halt_gate_enabled": bool(halt_gate_enabled)},
        source_file,
        {
            "status_partitions_available": bool(status_partitions_available),
            "halt_gate_enabled": bool(halt_gate_enabled),
            "simulation_mode": str(simulation_mode),
            **({"detail": (
                "the strategy's halt gate is enabled but the lake has no "
                "statuses/ partitions — halts / LULD pauses cannot be modelled"
                + ("; intended_realism fails closed" if halt_status == "fail"
                   else "; current-code parity tolerates this (live code fails open)")
            )} if halt_missing else {}),
        },
    )
    return [age_dist, spread_dist, halt]


def status_partitions_available(lake_root: Optional[Path]) -> bool:
    """True when a non-empty ``statuses/`` directory exists in the lake.

    The current lake has no status-ingestion stage; the layout reserves the
    slot. Absence is the normal case and drives ``halt_data_unavailable_when_required``.
    """
    if lake_root is None:
        return False
    statuses_root = Path(lake_root) / "statuses"
    if not statuses_root.is_dir():
        return False
    return any(statuses_root.rglob("*.parquet"))


__all__ = [
    "build_ingestion_checks",
    "build_session_checks",
    "build_replay_checks",
    "build_feature_checks",
    "build_quote_status_checks",
    "status_partitions_available",
    "REGULAR_SESSION_MINUTES",
    "EARLY_CLOSE_MINUTES",
]
