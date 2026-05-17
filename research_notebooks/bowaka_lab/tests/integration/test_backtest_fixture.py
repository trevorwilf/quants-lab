"""Phase 4: end-to-end backtest on synthetic minute fixture."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from bowaka_lab.config.models import BowakaBacktestConfig
from bowaka_lab.sim.portfolio_engine import BowakaPortfolioBacktester


def test_backtest_fixture_smoke(fixtures_dir: Path):
    minute_bars = pd.read_parquet(fixtures_dir / "minute_bars_small.parquet")
    sessions = [date(2026, 5, 11), date(2026, 5, 12), date(2026, 5, 13), date(2026, 5, 14), date(2026, 5, 15)]

    # Candidates: AAA, BBB, CCC selected on the signal day before the first session.
    # Use Friday 2026-05-08 as signal_date → 2026-05-11 trade_date.
    cands_signal_dates = {
        date(2026, 5, 8): pd.DataFrame(
            [
                {"symbol": "AAA", "signal_date": date(2026, 5, 8), "rank": 1, "close": 5.0, "passed_prefilter": True, "avg_dollar_volume": 1e8},
                {"symbol": "BBB", "signal_date": date(2026, 5, 8), "rank": 2, "close": 10.0, "passed_prefilter": True, "avg_dollar_volume": 1e8},
                {"symbol": "CCC", "signal_date": date(2026, 5, 8), "rank": 3, "close": 4.0, "passed_prefilter": True, "avg_dollar_volume": 1e8},
            ]
        )
    }

    cfg = BowakaBacktestConfig.model_validate(
        {
            "data": {"vendor": "alpaca", "feed": "iex", "start_date": "2026-05-08", "end_date": "2026-05-15"},
            "portfolio": {"per_trade_notional": 5000.0, "max_concurrent_positions": 5},
            "exits": {"stop_pct": 0.08, "target_pct": 0.15, "max_hold_days": 3},
            "entry": {"default_rule": "fixed_time_0945", "slippage_bps": 0},
        }
    )

    def candidate_source(sd: date):
        return cands_signal_dates.get(sd, pd.DataFrame())

    def minute_bars_for(td: date, symbols):
        df = minute_bars[(minute_bars["session_date"] == td) & (minute_bars["symbol"].isin(symbols))]
        return df.copy()

    runner = BowakaPortfolioBacktester(cfg, candidate_source=candidate_source, minute_bars_for=minute_bars_for)
    res = runner.run()
    trades = res.trades_df()

    assert trades.shape[0] >= 3
    symbols = set(trades["symbol"].tolist())
    assert {"AAA", "BBB", "CCC"} <= symbols

    aaa = trades[trades["symbol"] == "AAA"].iloc[0]
    assert aaa["exit_reason"] in ("target_hit", "ambiguous_bar_target")
    assert aaa["pnl"] > 0

    bbb = trades[trades["symbol"] == "BBB"].iloc[0]
    assert bbb["exit_reason"] in ("stop_hit", "stop_gap", "ambiguous_bar_stop")
    assert bbb["pnl"] < 0

    ccc = trades[trades["symbol"] == "CCC"].iloc[0]
    # CCC ramps slightly up (0.5%) — should time-stop after max_hold_days.
    assert ccc["exit_reason"] == "time_stop"
