"""Realism Phase 4 — full intraday replay catches a signal a single scan misses.

The core motivation for Phase 4 (audit P0-003): the pre-Phase-4 backtester ran
exactly one scan per session at 14:00 UTC (= 10:00 ET). A candidate that only
becomes gateable later in the session was therefore *invisible* to the backtest.

This test builds a symbol whose forming-session ``last_price`` only enters the
configured price band (``price_min``) at ~10:31 ET. The full-replay backtest
finds the candidate; a single 14:00-UTC scan does not.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.sim.schedule import scan_times_for_session

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

_ET = ZoneInfo("America/New_York")
_UTC = ZoneInfo("UTC")
_SESSION = _dt.date(2024, 9, 4)
_SYMBOL = "LATE"


def _late_signal_bars() -> pd.DataFrame:
    """390 one-minute bars (09:30-15:59 ET) where ``last_price`` clears 105 only
    at ~10:31 ET (minute 61) and then holds inside the [105, 200] band.

    The price is flat at 100 for the first hour, steps to 105 at minute 61, and
    drifts gently afterwards — so a scan at 10:00 ET sees price 100 (below
    ``price_min``) and a scan at 10:31 ET sees price >= 105 (in band).
    """
    open_ts_et = _dt.datetime.combine(_SESSION, _dt.time(9, 30, tzinfo=_ET))
    rows = []
    for i in range(390):
        if i < 61:
            price = 100.0  # flat first hour — below price_min
        else:
            price = 105.0 + (i - 61) * 0.01  # crosses the band at minute 61
        ts = (open_ts_et + _dt.timedelta(minutes=i)).astimezone(_UTC)
        rows.append({
            "symbol": _SYMBOL, "timestamp": pd.Timestamp(ts),
            "open": price, "high": price + 0.3, "low": price - 0.3,
            "close": price, "volume": 25_000.0,
        })
    return pd.DataFrame(rows)


def _cfg(*, interval_s: int) -> dict:
    return {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "session": {
            "calendar": "XNYS", "timezone": "America/New_York",
            "scanner_start": "09:45", "scanner_end": "15:30",
            "scan_interval_seconds": interval_s,
        },
        # price_min=105 is the gate the late signal must clear; all other gates
        # left unset (disabled) so the price band alone decides.
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 600,
                    "same_symbol_entries_per_day": 1, "symbol_cooldown_minutes": 390},
        "signals": {"price_min": 105.0, "price_max": 200.0},
        "execution": {"max_spread_bps": 500, "max_quote_age_seconds": 120,
                      "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                 "max_gross_exposure_pct": 0.90, "daily_loss_pct": 0.90,
                 "max_stopouts_per_day": 9, "stop_trading_after_consecutive_stopouts": 9},
        "exits": {"stop_loss_pct": 0.10, "take_profit_pct": 0.10, "max_hold_days": 1},
        "backtest": {"start_date": _SESSION.isoformat(),
                     "end_date": _SESSION.isoformat(), "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {"lab_root": "research_notebooks/bowaka_v2_lab",
                  "data_root": "research_notebooks/bowaka_v2_lab/data",
                  "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts"},
    }


def _universe() -> dict:
    return {"universe_hash": "sha256:t",
            "symbols": [{"symbol": _SYMBOL, "exchange": "NASDAQ",
                         "venue_code": "XNAS",
                         "instrument_class": "operating_equity",
                         "eligible_for_bowaka_equity_bucket": True}]}


def _daily_cache() -> pd.DataFrame:
    return pd.DataFrame([{"symbol": _SYMBOL, "prior_close": 100.0,
                          "avg_dollar_volume_20d": 5_000_000,
                          "prior_atr_pct": 0.02, "ema_slope_prior": 0.01}])


def _bars_supplier(bars: pd.DataFrame):
    def supplier(symbol: str, cutoff) -> pd.DataFrame:
        # Forming-session window: 09:30 ET -> cutoff.
        ts = pd.Timestamp(cutoff).tz_convert("UTC")
        return bars[bars["timestamp"] <= ts].copy()
    return supplier


def test_single_1400utc_scan_misses_the_late_signal() -> None:
    # 14:00 UTC == 10:00 ET — the late signal has not yet cleared price_min.
    bars = _late_signal_bars()
    cfg = _cfg(interval_s=60)
    state = {"entered_symbols_today": [], "in_play_pool": {},
             "symbol_last_emit_ts": {}, "entries_per_symbol_today": {}}
    result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=_universe(), daily_cache=_daily_cache(),
        volume_curve=None, state=state,
        scan_ts=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        bars_supplier=_bars_supplier(bars),
    )
    assert result.emitted == [], "the late signal must not be gateable at 10:00 ET"


def test_scan_at_1031_et_finds_the_late_signal() -> None:
    # 10:31 ET == 14:31 UTC — price has just cleared price_min.
    bars = _late_signal_bars()
    cfg = _cfg(interval_s=60)
    state = {"entered_symbols_today": [], "in_play_pool": {},
             "symbol_last_emit_ts": {}, "entries_per_symbol_today": {}}
    result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=_universe(), daily_cache=_daily_cache(),
        volume_curve=None, state=state,
        scan_ts=pd.Timestamp("2024-09-04 14:31:00", tz="UTC"),
        bars_supplier=_bars_supplier(bars),
    )
    assert len(result.emitted) == 1
    assert result.emitted[0]["symbol"] == _SYMBOL


def test_full_replay_finds_late_signal_missed_by_single_scan(tmp_path: Path) -> None:
    bars = _late_signal_bars()
    # Coarse 15-minute cadence keeps the test fast; 09:45 + 15m steps still
    # land a scan inside the gateable window (10:45 ET clears price_min).
    cfg = _cfg(interval_s=900)
    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )

    # Full replay: the calendar-aware scheduler ticks the whole session.
    full = run_backtest(
        cfg=cfg, sessions=[_SESSION],
        scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        universe_snapshot_by_session={_SESSION: _universe()},
        daily_cache_by_session={_SESSION: _daily_cache()},
        minute_bars_supplier=_bars_supplier(bars),
        daily_bars_supplier=lambda sym, d: pd.DataFrame(
            [{"symbol": sym, "session_date": d, "open": 105.0, "high": 112.0,
              "low": 104.0, "close": 111.0, "volume": 1_000_000}]
        ),
        initial_bankroll=10_000.0, paths=paths,
        run_dir=tmp_path / "full",
    )
    # The single legacy 14:00-UTC scan: same backtester, one scan.
    single = run_backtest(
        cfg=cfg, sessions=[_SESSION],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session={_SESSION: _universe()},
        daily_cache_by_session={_SESSION: _daily_cache()},
        minute_bars_supplier=_bars_supplier(bars),
        daily_bars_supplier=lambda sym, d: pd.DataFrame(
            [{"symbol": sym, "session_date": d, "open": 105.0, "high": 112.0,
              "low": 104.0, "close": 111.0, "volume": 1_000_000}]
        ),
        initial_bankroll=10_000.0, paths=paths,
        run_dir=tmp_path / "single",
    )

    # Full replay finds the late signal; the single 14:00-UTC scan does not.
    assert len(full.candidate_events) >= 1
    assert any(ev["symbol"] == _SYMBOL for ev in full.candidate_events)
    assert single.candidate_events == []
