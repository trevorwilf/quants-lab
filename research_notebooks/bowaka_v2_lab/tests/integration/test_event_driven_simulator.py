"""Phase 4 — event-driven simulator: the seven acceptance tests.

These tests prove the audit's P0-002 (exits processed only after all scans) and
P1-009 (cadence mismatch) findings are fixed:

* ``test_intraday_stop_before_later_scan_blocks_daily_loss_entries`` — the
  parity-flipping test. Under the pre-Phase-4 backtester this FAILS because
  the 10:05 stop is realized only at end of session, so the 10:06 scan sees
  ``daily_realized_pnl == 0`` and lets a same-day re-entry through. Under the
  event-driven loop the stop fires before the 10:06 scan and the
  ``daily_loss_pct`` kill switch blocks every subsequent entry.

* ``test_intraday_target_before_later_scan_releases_concurrent_slot`` — a
  target hit BEFORE noon releases the ``max_concurrent_positions`` slot so a
  noon scan can fill it.

* ``test_two_stopouts_before_noon_blocks_third_entry_same_day`` — two stops
  before noon trip the ``max_stopouts_per_day`` cap; the noon-scan candidate
  is rejected for that reason.

* ``test_time_stop_at_1545_closes_before_eod_snapshot`` — a lot held to the
  15:45 ET time stop closes BEFORE the 16:00 EOD equity snapshot, so the
  snapshot shows the realized PnL.

* ``test_consecutive_stopouts_kill_switch`` — two consecutive stopouts trip
  the consecutive-stopout kill switch; subsequent scans cannot enter.

* ``test_event_log_chronological_and_complete`` — ``events/events.parquet``
  rows are monotonic in timestamp and the SCAN-count matches the run report.

* ``test_cadences_decoupled`` — with ``scan_interval_seconds=60`` and
  ``protection_poll_interval_seconds=5`` the per-scan window holds 12
  PROTECTION_CHECK events.

The smoke fixture path retains the legacy daily-bar exit driver so the broad
smoke suite stays fast; that lock-in is asserted by
``test_smoke_path_keeps_daily_driver``.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import run_backtest


# ---- helpers --------------------------------------------------------------


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
    stop_pct: float = 0.05,
    target_pct: float = 0.10,
    max_hold_days: int = 3,
    daily_loss_pct: float = 0.50,
    max_stopouts_per_day: int = 4,
    stop_trading_after_consecutive_stopouts: int = 3,
    max_concurrent_positions: int = 5,
    same_symbol_entries_per_day: int = 5,
    max_total_entries_per_day: int = 50,
    max_gross_exposure_pct: float = 0.99,
    time_stop_enabled: bool = False,
    time_stop_at: str = "15:45",
    extra_sim: Optional[dict] = None,
) -> dict:
    sim_block: dict[str, Any] = {
        "mode": mode,
        "allow_research_relaxed": True,
        "same_minute_resolution": "conservative",
    }
    if extra_sim:
        sim_block.update(extra_sim)
    return {
        "strategy_id": "bowaka_v2",
        "strategy_version": "0.1.0",
        "simulation": sim_block,
        "market_data": {"feed": "iex", "max_bar_age_seconds": 6000},
        "scanner": {
            "max_candidates_per_scan": 10,
            "max_entries_per_scan": 10,
            "min_signal_strength": 0.0,
            "signal_expiry_seconds": 6000,
            "symbol_cooldown_minutes": 0,
            # The scanner has its OWN same-symbol cap (in addition to the
            # risk-gate one) that defaults to 1. Phase 4 tests need the
            # scanner to re-emit a symbol after its prior lot exits so we
            # raise both to ``same_symbol_entries_per_day``.
            "same_symbol_entries_per_day": same_symbol_entries_per_day,
        },
        "signals": {},
        "execution": {
            "max_spread_bps": 800,
            "max_quote_age_seconds": 600,
            "order_type": "market",
        },
        "sizing": {
            "dollars_per_position": 1000,
            "max_position_dollars": 5000,
            "max_concurrent_positions": max_concurrent_positions,
            "min_order_notional": 100,
        },
        "risk": {
            "max_concurrent_positions": max_concurrent_positions,
            "max_total_entries_per_day": max_total_entries_per_day,
            "max_gross_exposure_pct": max_gross_exposure_pct,
            "daily_loss_pct": daily_loss_pct,
            "max_stopouts_per_day": max_stopouts_per_day,
            "stop_trading_after_consecutive_stopouts": stop_trading_after_consecutive_stopouts,
            "same_symbol_entries_per_day": same_symbol_entries_per_day,
            "max_lots_per_symbol": 5,
        },
        "exits": {
            "stop_pct": stop_pct,
            "target_pct": target_pct,
            "max_hold_days": max_hold_days,
            "time_stop": {
                "enabled": time_stop_enabled,
                "exit_time": time_stop_at,
            },
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
    """A single daily-bar row used for the EOD mark-to-market."""
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
    stop_at_et: Optional[str] = None,
    target_at_et: Optional[str] = None,
    stop_pct: float = 0.05,
    target_pct: float = 0.10,
    base_price: float = 100.0,
    until_et: str = "16:00",
) -> pd.DataFrame:
    """Build a full-session minute path 09:30..``until_et`` ET.

    The bar at ``stop_at_et`` (if set) has a low that breaches the stop
    bracket; the bar at ``target_at_et`` (if set) has a high that breaches the
    target bracket. Every other bar straddles the entry price with a small
    range so brackets aren't hit elsewhere.
    """
    start = pd.Timestamp(f"{session_date} 09:30", tz="America/New_York")
    end = pd.Timestamp(f"{session_date} {until_et}", tz="America/New_York")
    stop_price = base_price * (1.0 - stop_pct)
    target_price = base_price * (1.0 + target_pct)
    rows = []
    ts = start
    while ts <= end:
        ts_et_str = ts.strftime("%H:%M")
        o = base_price
        h = base_price + 0.3
        l = base_price - 0.3
        c = base_price
        if stop_at_et is not None and ts_et_str == stop_at_et:
            # Drive a low through the stop; close at the breach.
            l = stop_price - 0.5
            c = stop_price - 0.2
        elif target_at_et is not None and ts_et_str == target_at_et:
            # Drive a high through the target.
            h = target_price + 0.5
            c = target_price + 0.2
        rows.append({
            "symbol": symbol,
            "timestamp": ts.tz_convert("UTC"),
            "open": o, "high": h, "low": l, "close": c,
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
    """Wire a deterministic ``run_backtest`` call from the per-test fixtures."""
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


# ---- Phase 4 acceptance tests --------------------------------------------


def test_intraday_stop_before_later_scan_blocks_daily_loss_entries(tmp_path: Path) -> None:
    """The parity-flipping test (audit P0-002).

    The 09:45 scan accepts AAA (and BBB to be safe); at 10:05 the AAA path hits
    its 8% stop, realizing a loss large enough to breach the
    ``daily_loss_pct: 0.005`` cap. Under the pre-Phase-4 backtester the 11:00
    scan still sees ``daily_realized_pnl == 0`` and accepts a third entry;
    under the event-driven loop the kill switch fires and the 11:00 candidate
    is rejected with ``reason=kill_switch``.
    """
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA", "BBB", "CCC"]
    cfg = _cfg(
        # Aggressive daily_loss_pct so a single 8% stop on a $1000 position
        # trips the kill switch (8% of $1000 = $80 vs bankroll $100k →
        # daily_loss_pct must be tighter than 0.0008).
        daily_loss_pct=0.0005,
        stop_pct=0.08, target_pct=0.20,
    )
    minute_by_symbol = {
        # AAA stops out at 10:05; price flat otherwise.
        "AAA": _build_minute_path("AAA", sd, stop_at_et="10:05", stop_pct=0.08, target_pct=0.20),
        # BBB / CCC: stable so they would happily fill if the gates allowed it.
        "BBB": _build_minute_path("BBB", sd, stop_pct=0.08, target_pct=0.20),
        "CCC": _build_minute_path("CCC", sd, stop_pct=0.08, target_pct=0.20),
    }
    # Three scans: 09:45 (before stop), 10:05 (during stop), 11:00 (after stop).
    scan_times = [
        pd.Timestamp(f"{sd}T13:45:00", tz="UTC"),  # 09:45 ET
        pd.Timestamp(f"{sd}T14:10:00", tz="UTC"),  # 10:10 ET — after the 10:05 stop
        pd.Timestamp(f"{sd}T15:00:00", tz="UTC"),  # 11:00 ET — well after
    ]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    trades = pd.read_parquet(result.run_dir / "trades.parquet")
    # The 10:05 stop closed at least one lot.
    aaa_stops = trades[(trades.get("symbol") == "AAA") & (trades.get("exit_reason").isin(["stop", "gap_stop"]))]
    assert len(aaa_stops) >= 1, f"expected AAA to stop intraday; trades: {trades.to_dict('records')}"
    # After the stop, the kill switch must have fired; later scans must NOT
    # have accepted ADDITIONAL entries beyond the pre-stop intake.
    decisions = pd.read_parquet(result.run_dir / "entry_decisions.parquet")
    later_accepts = decisions[
        (decisions["decision"] == "accepted")
        & (decisions["scan_timestamp"] > "2024-09-04T14:05:00Z")
    ] if "scan_timestamp" in decisions.columns else pd.DataFrame()
    # Every rejection after the stop should be reason=kill_switch (or the
    # equivalent safety reason — the gate may use a different label).
    later_rejects = decisions[
        (decisions["decision"] == "rejected")
        & (decisions["scan_timestamp"] > "2024-09-04T14:05:00Z")
    ] if "scan_timestamp" in decisions.columns else pd.DataFrame()
    assert len(later_accepts) == 0, (
        f"event-driven loop should block post-stop entries; got accepts: "
        f"{later_accepts.to_dict('records')}"
    )
    assert (later_rejects["reason"] == "kill_switch").any(), (
        f"expected kill_switch rejection after stop; got: "
        f"{later_rejects['reason'].tolist() if len(later_rejects) else 'no rejections'}"
    )


def test_intraday_target_before_later_scan_releases_concurrent_slot(tmp_path: Path) -> None:
    """A target hit before noon must release the max_concurrent slot."""
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA", "BBB"]
    cfg = _cfg(
        max_concurrent_positions=1,  # only one lot at a time
        same_symbol_entries_per_day=5,
        stop_pct=0.08, target_pct=0.10,
    )
    minute_by_symbol = {
        # AAA hits its 10% target at 10:10; BBB is steady so it can be picked
        # up the moment AAA closes.
        "AAA": _build_minute_path("AAA", sd, target_at_et="10:10", stop_pct=0.08, target_pct=0.10),
        "BBB": _build_minute_path("BBB", sd, stop_pct=0.08, target_pct=0.10),
    }
    scan_times = [
        pd.Timestamp(f"{sd}T13:45:00", tz="UTC"),  # 09:45 ET — first AAA fill
        pd.Timestamp(f"{sd}T14:15:00", tz="UTC"),  # 10:15 ET — AAA already exited
    ]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    trades = pd.read_parquet(result.run_dir / "trades.parquet")
    # AAA hit its target.
    assert (trades["exit_reason"].isin(["target", "gap_target"])).any(), trades
    # The second scan opened a NEW position (since AAA exited and freed the slot).
    decisions = pd.read_parquet(result.run_dir / "entry_decisions.parquet")
    accepts = decisions[decisions["decision"] == "accepted"]
    assert len(accepts) >= 2, (
        f"target exit should release the max_concurrent slot for a second "
        f"entry; got accepts: {accepts.to_dict('records')}"
    )


def test_two_stopouts_before_noon_blocks_third_entry_same_day(tmp_path: Path) -> None:
    """Two intraday stops trip max_stopouts_per_day; the noon scan is rejected.

    With ``max_stopouts_per_day: 2`` and ``stop_trading_after_consecutive_
    stopouts: 99`` the consecutive-stopout kill switch will not fire — the
    behavior under test is strictly the per-day stop-count cap.
    """
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA", "BBB", "CCC"]
    cfg = _cfg(
        max_stopouts_per_day=2,
        stop_trading_after_consecutive_stopouts=99,
        # Loose daily-loss so the cap isn't tripped by the loss path first.
        daily_loss_pct=0.99,
        stop_pct=0.08, target_pct=0.20,
    )
    minute_by_symbol = {
        "AAA": _build_minute_path("AAA", sd, stop_at_et="10:00", stop_pct=0.08, target_pct=0.20),
        "BBB": _build_minute_path("BBB", sd, stop_at_et="11:00", stop_pct=0.08, target_pct=0.20),
        "CCC": _build_minute_path("CCC", sd, stop_pct=0.08, target_pct=0.20),
    }
    scan_times = [
        pd.Timestamp(f"{sd}T13:45:00", tz="UTC"),  # 09:45 ET → AAA + BBB + CCC
        pd.Timestamp(f"{sd}T16:00:00", tz="UTC"),  # 12:00 ET — after both stops
    ]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    trades = pd.read_parquet(result.run_dir / "trades.parquet")
    stop_trades = trades[trades["exit_reason"].isin(["stop", "gap_stop"])]
    assert len(stop_trades) >= 2, f"expected two intraday stops; got: {trades}"
    decisions = pd.read_parquet(result.run_dir / "entry_decisions.parquet")
    later_rejects = decisions[
        (decisions["decision"] == "rejected")
        & (decisions["scan_timestamp"] > "2024-09-04T15:00:00Z")
    ] if "scan_timestamp" in decisions.columns else pd.DataFrame()
    # The noon-scan candidate must be rejected with kill_switch (which is the
    # canonical reason name the gate emits when max_stopouts_per_day trips —
    # see ``sim/risk_gates.py``).
    assert len(later_rejects) >= 1, (
        f"expected a noon-scan rejection after two stops; got decisions: "
        f"{decisions.to_dict('records')}"
    )
    assert (later_rejects["reason"] == "kill_switch").any(), (
        f"expected kill_switch reason; got: {later_rejects['reason'].tolist()}"
    )


def test_time_stop_suppressed_for_parity_contract_l14(tmp_path: Path) -> None:
    """L14: live (run_time_stop_pass_v2) has NO intraday time-stop, so under
    current_code_parity the sim does NOT fire the 15:45 time-stop even with
    ``time_stop.enabled: true`` in config — the lot holds to bracket/max_hold,
    matching live. The engine's time-stop mechanism is still covered by the
    direct-walk unit test ``test_exit_time_stop`` (which passes no contract, so the
    mode gate leaves the time-stop enabled).

    L14 changelog: was ``test_time_stop_at_1545_closes_before_eod_snapshot`` which
    asserted the 15:45 time-stop FIRED; that 15:30/15:45 force-close was the
    first-order sim<->live divergence this phase removes for the parity contracts.
    """
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA"]
    cfg = _cfg(
        time_stop_enabled=True, time_stop_at="15:45",
        stop_pct=0.20, target_pct=0.30,  # neither will hit
    )
    minute_by_symbol = {
        "AAA": _build_minute_path("AAA", sd, stop_pct=0.20, target_pct=0.30),
    }
    scan_times = [
        pd.Timestamp(f"{sd}T13:45:00", tz="UTC"),  # 09:45 ET → AAA fills
    ]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    trades = pd.read_parquet(result.run_dir / "trades.parquet")
    # L14: the intraday time-stop is suppressed for current_code_parity → the lot
    # holds (single session, brackets not hit, no time-stop) → no close this session.
    if len(trades) and "exit_reason" in trades.columns:
        assert not (trades["exit_reason"] == "time_stop").any(), (
            f"L14: time_stop must NOT fire under current_code_parity; got "
            f"{trades['exit_reason'].tolist()}"
        )
    assert len(trades) == 0, (
        f"L14: lot should hold with no intraday time-stop; got {len(trades)} closed trades"
    )
    # The entry still occurred and a daily-equity row was written.
    daily = pd.read_parquet(result.run_dir / "daily_equity.parquet")
    row = daily.iloc[0].to_dict()
    assert int(row["entries_today"]) >= 1
    assert "daily_realized_pnl" in row, row


def test_consecutive_stopouts_kill_switch(tmp_path: Path) -> None:
    """Two consecutive stopouts trip the consecutive-stopout kill switch."""
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA", "BBB", "CCC"]
    cfg = _cfg(
        max_stopouts_per_day=99,  # don't trip the cap
        stop_trading_after_consecutive_stopouts=2,
        daily_loss_pct=0.99,
        stop_pct=0.08, target_pct=0.20,
    )
    minute_by_symbol = {
        "AAA": _build_minute_path("AAA", sd, stop_at_et="10:00", stop_pct=0.08, target_pct=0.20),
        "BBB": _build_minute_path("BBB", sd, stop_at_et="11:00", stop_pct=0.08, target_pct=0.20),
        "CCC": _build_minute_path("CCC", sd, stop_pct=0.08, target_pct=0.20),
    }
    scan_times = [
        pd.Timestamp(f"{sd}T13:45:00", tz="UTC"),  # 09:45 ET
        pd.Timestamp(f"{sd}T16:30:00", tz="UTC"),  # 12:30 ET
    ]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    decisions = pd.read_parquet(result.run_dir / "entry_decisions.parquet")
    later_rejects = decisions[
        (decisions["decision"] == "rejected")
        & (decisions["scan_timestamp"] > "2024-09-04T15:30:00Z")
    ] if "scan_timestamp" in decisions.columns else pd.DataFrame()
    assert (later_rejects["reason"] == "kill_switch").any(), later_rejects


def test_event_log_chronological_and_complete(tmp_path: Path) -> None:
    """``events/events.parquet`` rows monotonic in timestamp + SCAN count matches."""
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA"]
    cfg = _cfg()
    minute_by_symbol = {
        "AAA": _build_minute_path("AAA", sd),
    }
    scan_times = [
        pd.Timestamp(f"{sd}T13:45:00", tz="UTC"),
        pd.Timestamp(f"{sd}T14:00:00", tz="UTC"),
        pd.Timestamp(f"{sd}T14:30:00", tz="UTC"),
    ]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    events_path = result.run_dir / "events" / "events.parquet"
    assert events_path.is_file(), "events/events.parquet missing"
    events = pd.read_parquet(events_path)
    assert len(events) > 0, "event log empty for an event-driven run"
    # Monotonic in timestamp (parsed as UTC).
    ts = pd.to_datetime(events["timestamp"], utc=True)
    assert ts.is_monotonic_increasing, "event log not chronological"
    # The SCAN events count matches the scan_times list.
    scan_count = int((events["event_type"] == "SCAN").sum())
    assert scan_count == len(scan_times), (
        f"event log SCAN count {scan_count} != scheduled {len(scan_times)}"
    )
    # EOD_MARK fires exactly once per session in the log.
    eod_count = int((events["event_type"] == "EOD_MARK").sum())
    assert eod_count == 1, f"expected 1 EOD_MARK; got {eod_count}"


def test_cadences_decoupled(tmp_path: Path) -> None:
    """``protection_poll_interval_seconds=5``, ``scan_interval_seconds=60``
    → 12 PROTECTION_CHECK events per 60s scan window."""
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA"]
    cfg = _cfg(
        extra_sim={
            "protection_poll_interval_seconds": 5,
            "fill_poll_interval_seconds": 5,
            "time_stop_check_interval_seconds": 60,
        },
    )
    # Pin loop_interval_seconds via session config so the live default holds.
    cfg["session"] = {"loop_interval_seconds": 5, "scan_interval_seconds": 60}
    minute_by_symbol = {
        "AAA": _build_minute_path("AAA", sd),
    }
    # Two scans 60s apart: 09:45 and 09:46 ET.
    scan_times = [
        pd.Timestamp(f"{sd}T13:45:00", tz="UTC"),
        pd.Timestamp(f"{sd}T13:46:00", tz="UTC"),
    ]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    events = pd.read_parquet(result.run_dir / "events" / "events.parquet")
    # PROTECTION_CHECK events between scan 1 and scan 2: ticks at 13:45:00,
    # 13:45:05, ..., 13:45:55 = 12 ticks in [13:45:00, 13:46:00). Phase-4
    # preloads PROTECTION_CHECK at every 5-second boundary in the session
    # window, so this asserts the decoupled cadence holds.
    ts = pd.to_datetime(events["timestamp"], utc=True)
    in_window = (
        (events["event_type"] == "PROTECTION_CHECK")
        & (ts >= pd.Timestamp("2024-09-04T13:45:00Z"))
        & (ts < pd.Timestamp("2024-09-04T13:46:00Z"))
    )
    n_prot = int(in_window.sum())
    assert n_prot == 12, (
        f"expected 12 PROTECTION_CHECK events between 13:45 and 13:46; got "
        f"{n_prot}"
    )


def test_smoke_path_keeps_daily_driver(tmp_path: Path) -> None:
    """``simulation.mode == smoke_fixture`` keeps the daily-bar exit driver.

    Phase 4 Task 6: the smoke path must NOT route through the event-driven
    minute walker (the smoke suite would otherwise pay the per-minute cost).
    The signal that the daily driver ran is that the canonical
    ``events/events.parquet`` exists but holds zero event rows for a smoke
    run (the event loop is the realism / parity path only).
    """
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA"]
    cfg = _cfg(mode="smoke_fixture")
    minute_by_symbol = {
        "AAA": _build_minute_path("AAA", sd),
    }
    scan_times = [
        pd.Timestamp(f"{sd}T13:45:00", tz="UTC"),
        pd.Timestamp(f"{sd}T14:00:00", tz="UTC"),
    ]
    result = _run(
        tmp_path=tmp_path, cfg=cfg, session_date=sd, symbols=symbols,
        minute_by_symbol=minute_by_symbol, scan_times=scan_times,
    )
    events_path = result.run_dir / "events" / "events.parquet"
    assert events_path.is_file(), "events/events.parquet required even in smoke mode"
    events = pd.read_parquet(events_path)
    # Smoke runs do NOT drive the event loop; the canonical roll-up is empty.
    assert len(events) == 0, (
        f"smoke_fixture should keep the daily driver; got {len(events)} "
        f"event-log rows."
    )
