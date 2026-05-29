"""Phase 3 (audit 2026-05-29 §9 Phase 5) — regime segmentation buckets."""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.reports.regime_analysis import segment_trades


def _et(hhmm: str) -> str:
    return pd.Timestamp(f"2024-08-01 {hhmm}", tz="America/New_York").tz_convert("UTC").isoformat()


def test_liquidity_and_tod_buckets() -> None:
    trades = [
        {"entry_timestamp": _et("10:00"), "adv_dollar": 5.0e5, "pnl": 10.0},   # micro, 0945-1030
        {"entry_timestamp": _et("10:05"), "adv_dollar": 5.0e5, "pnl": -5.0},   # micro, 0945-1030
        {"entry_timestamp": _et("11:00"), "adv_dollar": 1.0e8, "pnl": 20.0},   # large, 1030-1200
    ]
    rep = segment_trades(trades)
    assert rep["n_trades"] == 3
    assert rep["by_liquidity"]["micro"]["n_trades"] == 2
    assert rep["by_liquidity"]["large"]["n_trades"] == 1
    assert rep["by_time_of_day"]["0945-1030"]["n_trades"] == 2
    assert rep["by_time_of_day"]["1030-1200"]["n_trades"] == 1
    # win_rate of the micro bucket: 1 win / 2 trades
    assert abs(rep["by_liquidity"]["micro"]["win_rate"] - 0.5) < 1e-9
