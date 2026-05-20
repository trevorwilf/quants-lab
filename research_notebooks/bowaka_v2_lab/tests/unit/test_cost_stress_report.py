"""base/conservative/severe rows present."""
from __future__ import annotations

from bowaka_v2_lab.reports.cost_stress import cost_stress_compare


def test_three_rows_emitted() -> None:
    df = cost_stress_compare({
        "base": {"n_trades": 5, "win_rate": 0.6, "total_pnl": 200, "net_return_pct": 0.02, "max_drawdown_pct": 0.01},
        "conservative": {"n_trades": 5, "win_rate": 0.5, "total_pnl": 100, "net_return_pct": 0.01, "max_drawdown_pct": 0.02},
        "severe": {"n_trades": 5, "win_rate": 0.4, "total_pnl": 0, "net_return_pct": 0.0, "max_drawdown_pct": 0.03},
    })
    assert set(df["cost_stress"]) == {"base", "conservative", "severe"}
    assert len(df) == 3
