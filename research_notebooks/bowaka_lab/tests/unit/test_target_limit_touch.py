"""Phase 4: §F.1 stop and target in separate bars."""

from __future__ import annotations

from datetime import date

import pandas as pd

from bowaka_lab.config.models import ExitConfig
from bowaka_lab.sim.exits import evaluate_bar_exit
from bowaka_lab.sim.fill_model import BowakaFillModel
from bowaka_lab.sim.positions import SimulatedPosition


def _position():
    return SimulatedPosition(
        trade_id="t",
        symbol="X",
        signal_date=date(2026, 5, 11),
        trade_date=date(2026, 5, 12),
        entry_time=pd.Timestamp("2026-05-12 13:45Z"),
        entry_price=10.0,
        qty=100,
        stop_price=9.20,
        target_price=11.50,
        max_hold_exit_date=date(2026, 5, 14),
    )


def test_bar_one_no_exit_bar_two_target():
    pos = _position()
    fm = BowakaFillModel(slippage_bps=0)
    cfg = ExitConfig(stop_pct=0.08, target_pct=0.15, max_hold_days=3, target_fill_policy="limit_touch")

    bar1 = {"timestamp": pd.Timestamp("2026-05-12 14:00Z"), "open": 10.0, "high": 10.50, "low": 9.80, "close": 10.30, "volume": 100}
    ev1 = evaluate_bar_exit(position=pos, bar=bar1, cfg=cfg, fill_model=fm)
    assert ev1 is None

    bar2 = {"timestamp": pd.Timestamp("2026-05-12 14:01Z"), "open": 10.3, "high": 11.60, "low": 10.90, "close": 11.50, "volume": 100}
    ev2 = evaluate_bar_exit(position=pos, bar=bar2, cfg=cfg, fill_model=fm)
    assert ev2 is not None
    assert ev2.exit_reason == "target_hit"
    assert ev2.fill_price == 11.50  # limit_touch
