"""Entry-delay grid produces rows for 1/5/15/30m."""
from __future__ import annotations

from bowaka_v2_lab.reports.delay_sensitivity import delay_sensitivity_grid, standard_delays


def test_grid_emits_one_row_per_delay() -> None:
    summaries = {d: {"n_trades": d, "win_rate": 0.5, "total_pnl": 10*d, "net_return_pct": 0.001*d}
                   for d in standard_delays()}
    df = delay_sensitivity_grid(summaries)
    assert list(df["entry_delay_minutes"]) == list(standard_delays())
    assert len(df) == 4
