"""Phase 4: quote-based fill model."""

from __future__ import annotations

import pandas as pd
import pytest

from bowaka_lab.sim.fill_model import BowakaFillModel


def _quote(*, bid=10.0, ask=10.05):
    return {"timestamp": pd.Timestamp("2026-05-12 13:45Z"), "bid_price": bid, "ask_price": ask}


def test_buy_uses_ask_plus_buffer():
    fm = BowakaFillModel(slippage_bps=25)
    fill = fm.buy_from_quote(_quote(bid=10.0, ask=10.05))
    assert fill.fill_price == pytest.approx(10.05 * 1.0025)
    assert fill.model == "ask_plus_slippage"


def test_sell_uses_bid_minus_buffer():
    fm = BowakaFillModel(slippage_bps=25)
    fill = fm.sell_from_quote(_quote(bid=10.0, ask=10.05))
    assert fill.fill_price == pytest.approx(10.0 * 0.9975)
    assert fill.model == "bid_minus_slippage"
