"""Phase 4: §F.3 gap-through-stop policy."""

from __future__ import annotations

import pandas as pd

from bowaka_lab.config.models import ExitConfig
from bowaka_lab.sim.exits import evaluate_bar_exit
from bowaka_lab.sim.fill_model import BowakaFillModel
from bowaka_lab.sim.positions import SimulatedPosition


def _position(*, entry: float = 10.0, stop: float = 9.20, target: float = 11.50) -> SimulatedPosition:
    from datetime import date

    return SimulatedPosition(
        trade_id="t",
        symbol="X",
        signal_date=date(2026, 5, 11),
        trade_date=date(2026, 5, 12),
        entry_time=pd.Timestamp("2026-05-12 13:45Z"),
        entry_price=entry,
        qty=100,
        stop_price=stop,
        target_price=target,
        max_hold_exit_date=date(2026, 5, 14),
    )


def test_gap_through_stop_fills_at_open_under_next_available_open():
    pos = _position()
    bar = {"timestamp": pd.Timestamp("2026-05-12 14:30Z"), "open": 8.75, "high": 8.80, "low": 8.50, "close": 8.60, "volume": 100}
    fm = BowakaFillModel(slippage_bps=0)
    cfg = ExitConfig(stop_pct=0.08, target_pct=0.15, max_hold_days=3, stop_gap_policy="next_available_open")
    ev = evaluate_bar_exit(position=pos, bar=bar, cfg=cfg, fill_model=fm)
    assert ev is not None
    assert ev.exit_reason == "stop_gap"
    assert ev.fill_price == 8.75


def test_gap_through_stop_fills_at_stop_price_under_stop_price_policy():
    pos = _position()
    bar = {"timestamp": pd.Timestamp("2026-05-12 14:30Z"), "open": 8.75, "high": 8.80, "low": 8.50, "close": 8.60, "volume": 100}
    fm = BowakaFillModel(slippage_bps=0)
    cfg = ExitConfig(stop_pct=0.08, target_pct=0.15, max_hold_days=3, stop_gap_policy="stop_price")
    ev = evaluate_bar_exit(position=pos, bar=bar, cfg=cfg, fill_model=fm)
    assert ev is not None
    assert ev.exit_reason == "stop_gap"
    assert ev.fill_price == 9.20
