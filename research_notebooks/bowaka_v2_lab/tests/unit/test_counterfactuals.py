"""Counterfactual grid runs."""
from __future__ import annotations

from bowaka_v2_lab.research.counterfactuals import run_counterfactual_grid


def test_counterfactual_grid_runs() -> None:
    df = run_counterfactual_grid(
        base_cfg={"exits": {"stop_loss_pct": 0.02, "take_profit_pct": 0.05, "max_hold_days": 3}},
        exit_variants=[{"max_hold_days": 1}, {"take_profit_pct": 0.10}],
        backtest_runner=lambda cfg: {
            "n_trades": cfg["exits"]["max_hold_days"], "win_rate": 0.5,
        },
    )
    assert len(df) == 2
    assert "variant_idx" in df.columns
