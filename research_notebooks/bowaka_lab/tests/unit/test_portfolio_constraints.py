"""Phase 4: portfolio constraints + shadow risk recording."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from bowaka_lab.config.models import BowakaBacktestConfig, DataConfig, PortfolioConfig
from bowaka_lab.sim.portfolio_engine import BowakaPortfolioBacktester


def _make_cfg(**overrides):
    base = BowakaBacktestConfig.model_validate(
        {
            "data": {"vendor": "alpaca", "feed": "iex", "start_date": "2026-05-11", "end_date": "2026-05-15"},
            "portfolio": {"per_trade_notional": 5000.0, "max_concurrent_positions": 2, "max_total_entries_per_day": 2},
        }
    )
    for k, v in overrides.items():
        setattr(base.portfolio, k, v)
    return base


def _candidates(symbols: list[str], signal_date: date) -> pd.DataFrame:
    rows = []
    for i, sym in enumerate(symbols, start=1):
        rows.append(
            {
                "symbol": sym,
                "signal_date": signal_date,
                "rank": i,
                "close": 5.0,
                "passed_prefilter": True,
                "avg_dollar_volume": 1e8,
            }
        )
    return pd.DataFrame(rows)


def _flat_minute_bars(symbol: str, trade_date: date) -> pd.DataFrame:
    minutes = pd.date_range(
        start=pd.Timestamp(trade_date).tz_localize("America/New_York") + pd.Timedelta(hours=9, minutes=30),
        periods=390,
        freq="1min",
        tz="America/New_York",
    ).tz_convert("UTC")
    rows = []
    price = 5.0
    for ts in minutes:
        rows.append({"symbol": symbol, "timestamp": ts, "open": price, "high": price + 0.01, "low": price - 0.01, "close": price, "volume": 100})
    df = pd.DataFrame(rows)
    df["session_date"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
    return df


def test_max_concurrent_positions_cap():
    cfg = _make_cfg(max_concurrent_positions=1)
    signal_date = date(2026, 5, 8)
    trade_date = date(2026, 5, 11)

    def candidate_source(sd):
        return _candidates(["AAA", "BBB"], sd)

    def minute_bars_for(td, symbols):
        return pd.concat([_flat_minute_bars(s, td) for s in symbols], ignore_index=True)

    runner = BowakaPortfolioBacktester(cfg, candidate_source=candidate_source, minute_bars_for=minute_bars_for)
    res = runner.run()
    # Day 1 should enter only 1 position because cap is 1.
    day_one = res.daily_summary.iloc[0]
    assert day_one["entries"] <= 1


def test_max_entries_per_day_cap():
    cfg = _make_cfg(max_concurrent_positions=10, max_total_entries_per_day=2)

    def candidate_source(sd):
        return _candidates(["AAA", "BBB", "CCC", "DDD"], sd)

    def minute_bars_for(td, symbols):
        return pd.concat([_flat_minute_bars(s, td) for s in symbols], ignore_index=True)

    runner = BowakaPortfolioBacktester(cfg, candidate_source=candidate_source, minute_bars_for=minute_bars_for)
    res = runner.run()
    assert res.daily_summary.iloc[0]["entries"] <= 2


def test_shadow_risk_records_entries_breach():
    cfg = _make_cfg(max_concurrent_positions=20, max_total_entries_per_day=25)
    cfg.shadow_risk.max_entries_thresholds = [2]

    def candidate_source(sd):
        return _candidates(["AAA", "BBB", "CCC", "DDD"], sd)

    def minute_bars_for(td, symbols):
        return pd.concat([_flat_minute_bars(s, td) for s in symbols], ignore_index=True)

    runner = BowakaPortfolioBacktester(cfg, candidate_source=candidate_source, minute_bars_for=minute_bars_for)
    res = runner.run()
    assert any(b["rule"] == "max_entries" for b in res.shadow_blocks)
