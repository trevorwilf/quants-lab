"""Phase 4: bar-based fill model."""

from __future__ import annotations

import pandas as pd
import pytest

from bowaka_lab.sim.fill_model import BowakaFillModel


def _bar():
    return {"timestamp": pd.Timestamp("2026-05-12 13:45Z"), "open": 10.0, "high": 10.2, "low": 9.9, "close": 10.1, "volume": 1000}


def test_buy_slippage_applied():
    fm = BowakaFillModel(slippage_bps=25)
    fill = fm.buy_from_bar(_bar())
    assert fill.fill_price == pytest.approx(10.0 * 1.0025)
    assert fill.model == "next_minute_open_plus_slippage"


def test_sell_slippage_applied():
    fm = BowakaFillModel(slippage_bps=25)
    fill = fm.sell_from_bar(_bar())
    assert fill.fill_price == pytest.approx(10.0 * 0.9975)


def test_zero_slippage_returns_open():
    fm = BowakaFillModel(slippage_bps=0)
    fill = fm.buy_from_bar(_bar())
    assert fill.fill_price == 10.0


def test_negative_slippage_rejected():
    with pytest.raises(ValueError):
        BowakaFillModel(slippage_bps=-1)
