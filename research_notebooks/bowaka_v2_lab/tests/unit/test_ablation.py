"""Ablation works on a synthetic fixture."""
from __future__ import annotations

from bowaka_v2_lab.research.ablation import run_ablation_grid


def test_ablation_grid_runs() -> None:
    df = run_ablation_grid(
        base_cfg={"signals": {"rvol_so_far_min": 1.0, "ema_distance_min": 0.0}},
        gate_ablations=["rvol_so_far", "ema_distance"],
        backtest_runner=lambda cfg: {"n_trades": len(cfg["signals"]), "win_rate": 0.5},
    )
    assert {"baseline", "rvol_so_far", "ema_distance"}.issubset(set(df["ablation"]))
    # Baseline has 2 signals; ablating rvol_so_far leaves 1.
    baseline_row = df[df["ablation"] == "baseline"].iloc[0]
    rvol_row = df[df["ablation"] == "rvol_so_far"].iloc[0]
    assert baseline_row["n_trades"] == 2
    assert rvol_row["n_trades"] == 1
