"""Realism remediation 2 Phase 6 — OCO / protected-position lifecycle tests.

Audit finding **P0-007** documents that the lab's pre-Phase-6 strategy consumer
stamped lots ``bracket_attached=True`` immediately after the synchronous fill
simulation, masking the unprotected interval the live strategy actually spends
between PARENT_FILL and OCO_ATTACH. Phase 6 wires the explicit lifecycle:

  candidate_emitted
    -> order_planned
    -> parent_submitted
    -> parent_acknowledged / parent_rejected
    -> parent_partially_filled / parent_filled / parent_canceled
    -> oco_attach_pending
    -> oco_attached / oco_attach_failed
    -> protected / unprotected_violation
    -> fallback_stop_submitted / flatten_submitted / entries_blocked
    -> child_exit_filled / manual_exit_filled

The audit's acceptance criteria translate to seven integration tests:

* ``test_parent_fill_then_oco_attach_success`` — happy path: a normal fill +
  attach lifecycle ends with the lot in PROTECTED.
* ``test_oco_attach_retry_then_success`` — under
  ``protection_stress=oco_attach_fail_once`` the first attach fails; the
  second succeeds. Final state PROTECTED; ``oco_attach_failure_count == 1``.
* ``test_oco_attach_two_failures_triggers_fallback_stop`` — under
  ``oco_attach_fail_always`` both attempts fail; the lot lands in
  FALLBACK_STOP_SUBMITTED (or FLATTEN_SUBMITTED) and the
  ``fallback_stop_count`` metric is incremented.
* ``test_unprotected_violation_blocks_new_entries`` — while a lot is in
  violation, the next SCAN's candidate is rejected with
  ``entries_blocked_by_protection``.
* ``test_unprotected_violation_flatten_if_configured`` — under
  ``flatten_if_unprotected: true`` the violating lot is closed at the next
  PROTECTION_CHECK tick with exit_reason ``manual_flatten``.
* ``test_protection_metrics_in_run_report`` — the run summary carries every
  metric required by the audit, and the rendered report references them.
* ``test_halt_during_unprotected_triggers_flatten_or_logged_breach`` — the
  ``halt_during_unprotected`` stress drives the violation flow exactly like
  ``delayed_attach``; the flatten still fires and the breach is logged.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import run_backtest


# ---- helpers (mirror the Phase-4 acceptance suite) -----------------------


def _paths(tmp_path: Path) -> BowakaV2Paths:
    return BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )


def _cfg(
    *,
    mode: str = "current_code_parity",
    protection_stress: str = "none",
    max_unprotected_seconds: float = 10.0,
    oco_attach_attempts: int = 2,
    fallback_stop_enabled: bool = True,
    flatten_if_unprotected: bool = True,
    block_entries_on_violation: bool = True,
    oco_attach_latency_seconds: float = 0.5,
    stop_pct: float = 0.08,
    target_pct: float = 0.20,
    daily_loss_pct: float = 0.99,
    max_concurrent_positions: int = 5,
    extra_sim: Optional[dict] = None,
) -> dict:
    sim_block: dict[str, Any] = {
        "mode": mode,
        "allow_research_relaxed": True,
        "same_minute_resolution": "conservative",
        "protection_poll_interval_seconds": 1,
        "fill_poll_interval_seconds": 1,
        "protection_stress": protection_stress,
    }
    if extra_sim:
        sim_block.update(extra_sim)
    return {
        "strategy_id": "bowaka_v2",
        "strategy_version": "0.1.0",
        "simulation": sim_block,
        "market_data": {"feed": "iex", "max_bar_age_seconds": 6000},
        "session": {
            "loop_interval_seconds": 1,
            "scan_interval_seconds": 60,
        },
        "scanner": {
            "max_candidates_per_scan": 10,
            "max_entries_per_scan": 10,
            "min_signal_strength": 0.0,
            "signal_expiry_seconds": 6000,
            "symbol_cooldown_minutes": 0,
            "same_symbol_entries_per_day": 5,
        },
        "signals": {},
        "execution": {
            "max_spread_bps": 800,
            "max_quote_age_seconds": 600,
            "order_type": "market",
            "oco_attach_latency_seconds": oco_attach_latency_seconds,
        },
        "sizing": {
            "dollars_per_position": 1000,
            "max_position_dollars": 5000,
            "max_concurrent_positions": max_concurrent_positions,
            "min_order_notional": 100,
        },
        "risk": {
            "max_concurrent_positions": max_concurrent_positions,
            "max_total_entries_per_day": 50,
            "max_gross_exposure_pct": 0.99,
            "daily_loss_pct": daily_loss_pct,
            "max_stopouts_per_day": 99,
            "stop_trading_after_consecutive_stopouts": 99,
            "same_symbol_entries_per_day": 5,
            "max_lots_per_symbol": 5,
        },
        "exits": {
            "stop_pct": stop_pct,
            "target_pct": target_pct,
            "max_hold_days": 3,
        },
        "protected_position": {
            "enabled": True,
            "max_unprotected_seconds": max_unprotected_seconds,
            "oco_attach_attempts": oco_attach_attempts,
            "fallback_stop_enabled": fallback_stop_enabled,
            "flatten_if_unprotected": flatten_if_unprotected,
            "block_entries_on_violation": block_entries_on_violation,
        },
        "backtest": {
            "start_date": "2024-09-04",
            "end_date": "2024-09-04",
            "cost_stress": "base",
        },
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {
            "lab_root": "research_notebooks/bowaka_v2_lab",
            "data_root": "research_notebooks/bowaka_v2_lab/data",
            "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
        },
    }


def _universe(session_date: _dt.date, symbols: list[str]) -> dict:
    return {
        session_date: {
            "universe_hash": "sha256:t",
            "symbols": [{
                "symbol": s,
                "exchange": "NASDAQ",
                "venue_code": "XNAS",
                "instrument_class": "operating_equity",
                "eligible_for_bowaka_equity_bucket": True,
            } for s in symbols],
        }
    }


def _daily_cache(session_date: _dt.date, symbols: list[str]) -> dict:
    return {
        session_date: pd.DataFrame([{
            "symbol": s,
            "prior_close": 100.0,
            "avg_dollar_volume_20d": 500_000_000,
            "prior_atr_pct": 0.02,
            "ema_slope_prior": 0.01,
        } for s in symbols])
    }


def _daily_bars(session_date: _dt.date, symbol: str, close: float = 100.0) -> pd.DataFrame:
    return pd.DataFrame([{
        "symbol": symbol,
        "session_date": session_date,
        "open": 100.0,
        "high": 130.0,
        "low": 90.0,
        "close": close,
        "volume": 1_000_000.0,
    }])


def _build_minute_path(
    symbol: str,
    session_date: _dt.date,
    *,
    base_price: float = 100.0,
    until_et: str = "16:00",
) -> pd.DataFrame:
    """A non-breaching minute path — neither stop nor target hit."""
    start = pd.Timestamp(f"{session_date} 09:30", tz="America/New_York")
    end = pd.Timestamp(f"{session_date} {until_et}", tz="America/New_York")
    rows = []
    ts = start
    while ts <= end:
        rows.append({
            "symbol": symbol,
            "timestamp": ts.tz_convert("UTC"),
            "open": base_price, "high": base_price + 0.3,
            "low": base_price - 0.3, "close": base_price,
            "volume": 50_000.0,
        })
        ts = ts + pd.Timedelta(minutes=1)
    return pd.DataFrame(rows)


def _run(
    *,
    tmp_path: Path,
    cfg: dict,
    session_date: _dt.date,
    symbols: list[str],
    minute_by_symbol: dict[str, pd.DataFrame],
    scan_times: list[pd.Timestamp],
) -> Any:
    def minute_supplier(sym, ts):
        full = minute_by_symbol[sym]
        tsv = pd.to_datetime(full["timestamp"], utc=True)
        return full[tsv <= pd.Timestamp(ts)]

    def session_minute_supplier(sym, sd):
        return minute_by_symbol.get(sym)

    def daily_supplier(sym, sd):
        return _daily_bars(sd, sym)

    return run_backtest(
        cfg=cfg, sessions=[session_date],
        scan_times_per_session=lambda d: scan_times,
        universe_snapshot_by_session=_universe(session_date, symbols),
        daily_cache_by_session=_daily_cache(session_date, symbols),
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=daily_supplier,
        session_minute_supplier=session_minute_supplier,
        initial_bankroll=100_000.0, paths=_paths(tmp_path),
        run_dir=tmp_path / "run",
    )


# ---- Phase 6 acceptance tests --------------------------------------------


def test_parent_fill_then_oco_attach_success(tmp_path: Path) -> None:
    """Normal lifecycle — a PARENT_FILL → OCO_ATTACH_ATTEMPT → PROTECTED.

    Final state PROTECTED for the lot; no fallback or flatten counters fire;
    ``max_unprotected_seconds_observed`` reflects the attach latency.
    """
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA"]
    cfg = _cfg(protection_stress="none", oco_attach_latency_seconds=0.5)
    minute_by_symbol = {"AAA": _build_minute_path("AAA", sd)}
    scan_times = [pd.Timestamp(f"{sd}T13:45:00", tz="UTC")]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    pm = result.portfolio.protection_metrics
    # One attempt, no failures.
    assert pm.oco_attach_attempts_count == 1, (
        f"expected 1 attach attempt; got {pm.oco_attach_attempts_count}"
    )
    assert pm.oco_attach_failure_count == 0
    assert pm.fallback_stop_count == 0
    assert pm.flatten_unprotected_count == 0
    assert pm.unprotected_violation_count == 0
    # The attach latency is 0.5s, so the observed unprotected interval is ~0.5s.
    assert pm.max_unprotected_seconds_observed >= 0.5 - 1e-3
    assert pm.max_unprotected_seconds_observed < 2.0
    # The lot reaches PROTECTED.
    from bowaka_v2_lab.sim.portfolio import ProtectionState
    assert len(result.portfolio.open_positions) == 1
    pos = next(iter(result.portfolio.open_positions.values()))
    assert pos.protection_state == ProtectionState.PROTECTED, pos.protection_state
    # Summary surfaces the metrics.
    summary = json.loads((result.run_dir / "summary.json").read_text())
    assert summary["protection"]["oco_attach_attempts_count"] == 1
    assert summary["protection"]["unprotected_violation_count"] == 0


def test_oco_attach_retry_then_success(tmp_path: Path) -> None:
    """``oco_attach_fail_once`` — attempt 0 fails, attempt 1 succeeds.

    The lot lands in PROTECTED; ``oco_attach_failure_count == 1`` and
    ``oco_attach_attempts_count == 2``; no fallback / flatten fired.
    """
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA"]
    cfg = _cfg(
        protection_stress="oco_attach_fail_once",
        oco_attach_latency_seconds=1.0,
        oco_attach_attempts=2,
    )
    minute_by_symbol = {"AAA": _build_minute_path("AAA", sd)}
    scan_times = [pd.Timestamp(f"{sd}T13:45:00", tz="UTC")]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    pm = result.portfolio.protection_metrics
    assert pm.oco_attach_attempts_count == 2, (
        f"expected 2 attach attempts (fail-once + succeed); got "
        f"{pm.oco_attach_attempts_count}"
    )
    assert pm.oco_attach_failure_count == 1
    # No remediation fired — the retry succeeded before the violation window.
    assert pm.fallback_stop_count == 0
    assert pm.flatten_unprotected_count == 0
    assert pm.unprotected_violation_count == 0
    from bowaka_v2_lab.sim.portfolio import ProtectionState
    pos = next(iter(result.portfolio.open_positions.values()))
    assert pos.protection_state == ProtectionState.PROTECTED, pos.protection_state


def test_oco_attach_two_failures_triggers_fallback_stop(tmp_path: Path) -> None:
    """``oco_attach_fail_always`` — both attempts fail.

    After two attempts the state machine triggers the violation flow:
    ``fallback_stop_count == 1`` (fallback is enabled) and the lot is in a
    violation state (FALLBACK_STOP_SUBMITTED / FLATTEN_SUBMITTED) rather than
    PROTECTED.
    """
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA"]
    cfg = _cfg(
        protection_stress="oco_attach_fail_always",
        oco_attach_latency_seconds=1.0,
        oco_attach_attempts=2,
        fallback_stop_enabled=True,
        flatten_if_unprotected=False,  # isolate the fallback path
    )
    minute_by_symbol = {"AAA": _build_minute_path("AAA", sd)}
    scan_times = [pd.Timestamp(f"{sd}T13:45:00", tz="UTC")]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    pm = result.portfolio.protection_metrics
    assert pm.oco_attach_attempts_count == 2
    assert pm.oco_attach_failure_count == 2
    assert pm.fallback_stop_count == 1, (
        f"expected 1 fallback_stop_submitted; got {pm.fallback_stop_count}"
    )
    assert pm.flatten_unprotected_count == 0
    assert pm.unprotected_violation_count == 1
    # The lot is still open (flatten disabled), in a violation state.
    from bowaka_v2_lab.sim.portfolio import ProtectionState
    assert len(result.portfolio.open_positions) == 1
    pos = next(iter(result.portfolio.open_positions.values()))
    assert pos.protection_state in (
        ProtectionState.FALLBACK_STOP_SUBMITTED,
        ProtectionState.UNPROTECTED_VIOLATION,
    ), pos.protection_state
    assert pos.fallback_stop_ts is not None


def test_unprotected_violation_blocks_new_entries(tmp_path: Path) -> None:
    """While a lot is in violation, the next SCAN must reject candidates.

    With ``block_entries_on_violation=True``, ``Portfolio.state.entries_blocked``
    is set; the risk gate rejects the next SCAN's candidate with reason
    ``entries_blocked_by_protection``.
    """
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA", "BBB"]
    cfg = _cfg(
        protection_stress="oco_attach_fail_always",
        oco_attach_latency_seconds=1.0,
        oco_attach_attempts=2,
        fallback_stop_enabled=True,
        flatten_if_unprotected=False,  # keep the violator open
        block_entries_on_violation=True,
    )
    minute_by_symbol = {
        "AAA": _build_minute_path("AAA", sd),
        "BBB": _build_minute_path("BBB", sd),
    }
    # Two scans: 13:45 (AAA enters → both attaches fail → violation), 14:00
    # (BBB candidate must be blocked because the AAA violation persists).
    scan_times = [
        pd.Timestamp(f"{sd}T13:45:00", tz="UTC"),
        pd.Timestamp(f"{sd}T14:00:00", tz="UTC"),
    ]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    pm = result.portfolio.protection_metrics
    assert pm.unprotected_violation_count >= 1
    assert pm.entries_blocked_by_protection_count >= 1, (
        f"expected at least 1 entries-blocked rejection; got "
        f"{pm.entries_blocked_by_protection_count}"
    )
    # The decisions parquet records the rejection reason.
    decisions = pd.read_parquet(result.run_dir / "entry_decisions.parquet")
    blocked = decisions[
        (decisions["decision"] == "rejected")
        & (decisions["reason"] == "entries_blocked_by_protection")
    ]
    assert len(blocked) >= 1, (
        f"expected at least 1 entries_blocked_by_protection rejection; got: "
        f"{decisions['reason'].tolist() if 'reason' in decisions.columns else 'no reason col'}"
    )


def test_unprotected_violation_flatten_if_configured(tmp_path: Path) -> None:
    """``flatten_if_unprotected: true`` flattens the violator at the next tick.

    Under ``oco_attach_fail_always`` + ``flatten_if_unprotected: true`` the
    state machine moves the lot to FLATTEN_SUBMITTED; the next PROTECTION_CHECK
    closes the lot with exit_reason ``manual_flatten`` and the
    ``flatten_unprotected_count`` is incremented.
    """
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA"]
    cfg = _cfg(
        protection_stress="oco_attach_fail_always",
        oco_attach_latency_seconds=1.0,
        oco_attach_attempts=2,
        fallback_stop_enabled=True,
        flatten_if_unprotected=True,
        block_entries_on_violation=True,
    )
    minute_by_symbol = {"AAA": _build_minute_path("AAA", sd)}
    scan_times = [pd.Timestamp(f"{sd}T13:45:00", tz="UTC")]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    pm = result.portfolio.protection_metrics
    assert pm.unprotected_violation_count >= 1
    assert pm.flatten_unprotected_count >= 1, (
        f"expected at least 1 manual flatten; got {pm.flatten_unprotected_count}"
    )
    # The lot is closed via manual_flatten in trades.parquet.
    trades = pd.read_parquet(result.run_dir / "trades.parquet")
    flatten_trades = trades[trades["exit_reason"] == "manual_flatten"]
    assert len(flatten_trades) >= 1, (
        f"expected at least one manual_flatten trade; got: "
        f"{trades['exit_reason'].tolist() if 'exit_reason' in trades.columns else trades}"
    )
    # The portfolio is flat — the violator was closed.
    assert len(result.portfolio.open_positions) == 0


def test_protection_metrics_in_run_report(tmp_path: Path) -> None:
    """summary.json and report.md surface every required protection metric.

    Audit P0-007's acceptance criteria require the run report to expose
    ``max_unprotected_seconds_observed``, ``oco_attach_attempts``,
    ``fallback_stop_count``, ``flatten_unprotected_count``, and
    ``entries_blocked_by_protection_count``. Phase 6 task 4 also adds
    ``oco_attach_failure_count``, ``total_unprotected_seconds_across_lots``
    and ``unprotected_violation_count``.
    """
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA"]
    # Use the fail-always stress so the metrics are non-zero (the assertion
    # below verifies field presence; whether they're zero or positive is the
    # test's job not the runtime's).
    cfg = _cfg(
        protection_stress="oco_attach_fail_always",
        oco_attach_latency_seconds=1.0,
        flatten_if_unprotected=True,
    )
    minute_by_symbol = {"AAA": _build_minute_path("AAA", sd)}
    scan_times = [pd.Timestamp(f"{sd}T13:45:00", tz="UTC")]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    # summary.json holds the dict.
    summary = json.loads((result.run_dir / "summary.json").read_text())
    assert "protection" in summary, (
        f"summary.json missing 'protection' block; keys: {sorted(summary.keys())}"
    )
    prot = summary["protection"]
    required_keys = {
        "max_unprotected_seconds_observed",
        "oco_attach_attempts_count",
        "oco_attach_failure_count",
        "fallback_stop_count",
        "flatten_unprotected_count",
        "entries_blocked_by_protection_count",
        "total_unprotected_seconds_across_lots",
        "unprotected_violation_count",
    }
    assert required_keys.issubset(set(prot.keys())), (
        f"summary['protection'] missing keys; have {sorted(prot.keys())}; "
        f"need {sorted(required_keys)}"
    )
    # report.md mentions the section header + metrics.
    report_md = (result.run_dir / "report.md").read_text(encoding="utf-8")
    assert "Protection Lifecycle" in report_md, (
        "report.md missing 'Protection Lifecycle' section"
    )
    for key in required_keys:
        assert key in report_md, (
            f"report.md missing protection metric: {key}"
        )


def test_halt_during_unprotected_triggers_flatten_or_logged_breach(tmp_path: Path) -> None:
    """``halt_during_unprotected`` exercises the protected-position violation.

    The stress models a halt that delays the OCO attach until the
    ``max_unprotected_seconds`` clock expires. The state machine triggers the
    violation flow exactly as ``delayed_attach`` does; with
    ``flatten_if_unprotected: true`` the lot flattens and the breach lands in
    the run summary.
    """
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA"]
    cfg = _cfg(
        protection_stress="halt_during_unprotected",
        max_unprotected_seconds=2.0,  # narrow window so the delay overshoots
        oco_attach_latency_seconds=1.0,
        oco_attach_attempts=2,
        fallback_stop_enabled=True,
        flatten_if_unprotected=True,
        block_entries_on_violation=True,
    )
    # The ``delayed_attach`` / ``halt_during_unprotected`` stresses inject an
    # extra ``delayed_attach_extra_seconds`` (default 5s) into the first
    # OCO_ATTACH_ATTEMPT scheduling, so the unprotected window grows from
    # ~1s to ~6s — comfortably past the 2s max above.
    minute_by_symbol = {"AAA": _build_minute_path("AAA", sd)}
    scan_times = [pd.Timestamp(f"{sd}T13:45:00", tz="UTC")]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    pm = result.portfolio.protection_metrics
    # The violation flow fired (either via PROTECTION_CHECK timeout or via
    # the attempt failure path).
    assert pm.unprotected_violation_count >= 1, (
        f"expected at least 1 unprotected_violation; got {pm.unprotected_violation_count}"
    )
    # The breach lands in the run summary.
    summary = json.loads((result.run_dir / "summary.json").read_text())
    assert summary["protection"]["max_unprotected_seconds_observed"] >= 2.0
    # Flatten OR fallback fired (depending on whether the violation came from
    # PROTECTION_CHECK or the final attach failure).
    assert (pm.flatten_unprotected_count + pm.fallback_stop_count) >= 1, (
        f"expected at least one remediation; got flatten="
        f"{pm.flatten_unprotected_count} fallback={pm.fallback_stop_count}"
    )
