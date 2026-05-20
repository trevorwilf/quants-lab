"""size > liquidity → partial fill; cost recorded."""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.fills import simulate_fill
from bowaka_v2_lab.sim.quote_model import synthesize_quote


def test_partial_fill_when_size_exceeds_liquidity() -> None:
    q = synthesize_quote(last_price=100.0, at=pd.Timestamp("2024-09-04 13:30:00", tz="UTC"))
    r = simulate_fill(side="buy", requested_qty=1000, quote=q, available_liquidity=300,
                       stress_level="base", adv_participation_frac=0.01)
    assert r.is_partial is True
    assert r.filled_qty == 300


def test_full_fill_when_liquidity_sufficient() -> None:
    q = synthesize_quote(last_price=100.0, at=pd.Timestamp("2024-09-04 13:30:00", tz="UTC"))
    r = simulate_fill(side="buy", requested_qty=100, quote=q, available_liquidity=1000,
                       stress_level="base", adv_participation_frac=0.01)
    assert r.is_partial is False
    assert r.filled_qty == 100


def test_no_fill_when_no_liquidity() -> None:
    q = synthesize_quote(last_price=100.0, at=pd.Timestamp("2024-09-04 13:30:00", tz="UTC"))
    r = simulate_fill(side="buy", requested_qty=100, quote=q, available_liquidity=0,
                       stress_level="base", adv_participation_frac=0.01)
    assert r.filled_qty == 0
    assert r.is_partial is True


def test_fill_price_higher_for_buy_with_higher_stress() -> None:
    q = synthesize_quote(last_price=100.0, at=pd.Timestamp("2024-09-04 13:30:00", tz="UTC"))
    r_base = simulate_fill(side="buy", requested_qty=100, quote=q,
                              stress_level="base", adv_participation_frac=0.01)
    r_severe = simulate_fill(side="buy", requested_qty=100, quote=q,
                                stress_level="severe", adv_participation_frac=0.01)
    assert r_severe.avg_fill_price > r_base.avg_fill_price
