"""Phase 5: full counterfactual grid on the Phase 4 minute fixture."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from bowaka_lab.config.models import CounterfactualConfig
from bowaka_lab.sim.counterfactuals import run_grid_for_candidates
from bowaka_lab.sim.fill_model import BowakaFillModel


def test_counterfactual_grid_on_fixture(fixtures_dir: Path):
    minute_bars = pd.read_parquet(fixtures_dir / "minute_bars_small.parquet")
    candidates = pd.DataFrame(
        [
            {"symbol": "AAA", "rank": 1, "passed_prefilter": True},
            {"symbol": "BBB", "rank": 2, "passed_prefilter": True},
            {"symbol": "CCC", "rank": 3, "passed_prefilter": False},
        ]
    )
    trade_date = date(2026, 5, 11)
    bars_by_symbol = {sym: minute_bars[(minute_bars["symbol"] == sym) & (minute_bars["session_date"] == trade_date)] for sym in candidates["symbol"]}

    cfg = CounterfactualConfig(
        include_rejected_candidates=True,
        entry_rules=["fixed_time_0935", "fixed_time_0945"],
        stop_pct=[0.05, 0.08],
        target_pct=[0.10, 0.15],
        max_hold_days=[3],
        signal_fade_thresholds=[None, 8],
        stop_manager_models=["none", "breakeven_after_5pct"],
    )
    out = run_grid_for_candidates(
        candidates=candidates,
        minute_bars_by_symbol=bars_by_symbol,
        cfg=cfg,
        fill_model=BowakaFillModel(slippage_bps=0),
        signal_date=date(2026, 5, 8),
        trade_date=trade_date,
    )
    # 3 candidates × 2 entry × 2 stop × 2 target × 1 hold × 2 fade × 2 stop_mgr = 96 rows
    assert out.shape[0] == 96
    aaa_target_15 = out[(out["symbol"] == "AAA") & out["variant"].apply(lambda v: v["target_pct"] == 0.15 and v["entry_rule"] == "fixed_time_0935")]
    assert (aaa_target_15["exit_reason"].isin(["target_hit", "ambiguous_bar_target"])).any()


def test_counterfactual_grid_deterministic(fixtures_dir: Path):
    minute_bars = pd.read_parquet(fixtures_dir / "minute_bars_small.parquet")
    candidates = pd.DataFrame([{"symbol": "AAA", "rank": 1, "passed_prefilter": True}])
    trade_date = date(2026, 5, 11)
    bars_by_symbol = {"AAA": minute_bars[(minute_bars["symbol"] == "AAA") & (minute_bars["session_date"] == trade_date)]}
    cfg = CounterfactualConfig(
        entry_rules=["fixed_time_0945"],
        stop_pct=[0.08],
        target_pct=[0.15],
        max_hold_days=[3],
        signal_fade_thresholds=[None],
        stop_manager_models=["none"],
    )
    fm = BowakaFillModel(slippage_bps=0)
    a = run_grid_for_candidates(
        candidates=candidates,
        minute_bars_by_symbol=bars_by_symbol,
        cfg=cfg,
        fill_model=fm,
        signal_date=date(2026, 5, 8),
        trade_date=trade_date,
    )
    b = run_grid_for_candidates(
        candidates=candidates,
        minute_bars_by_symbol=bars_by_symbol,
        cfg=cfg,
        fill_model=fm,
        signal_date=date(2026, 5, 8),
        trade_date=trade_date,
    )
    pd.testing.assert_frame_equal(a, b)
