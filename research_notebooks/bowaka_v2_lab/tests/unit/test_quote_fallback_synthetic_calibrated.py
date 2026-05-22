"""Phase 6 — smoke mode → calibrated synthetic quote (positive spread, non-zero age).

The ``synthetic_calibrated`` fallback policy (resolved from ``smoke_fixture``
mode) derives a spread from a per-symbol/day model calibrated to ADV / price /
volatility, and gives the quote a random age in ``[1, max_quote_age_seconds]``.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.quote_model import (
    SOURCE_SYNTHETIC_CALIBRATED,
    calibrated_half_spread_bps,
    resolve_quote,
    synthesize_calibrated_quote,
)


def test_calibrated_fallback_has_positive_spread_and_nonzero_age():
    res = resolve_quote(
        symbol="AAA", at=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        signal_price=10.0,
        historical_quote=None,
        quote_fallback_policy="synthetic_calibrated",
        adv_dollars=2_000_000.0,
        volatility_pct=0.03,
        max_quote_age_seconds=5,
    )
    assert res.missing_quote is False
    q = res.quote
    assert q is not None
    assert q.source == SOURCE_SYNTHETIC_CALIBRATED
    assert q.spread_pct > 0.0
    assert q.ask > q.bid
    assert q.mid == 10.0  # mid == signal_price
    # quote_age random in [1, max_quote_age_seconds].
    assert 1.0 <= q.quote_age_seconds <= 5.0


def test_calibrated_spread_widens_for_thin_adv():
    """The calibrated spread is wider for thinner ADV (a structural driver)."""
    thick = calibrated_half_spread_bps(
        price=10.0, adv_dollars=50_000_000.0, volatility_pct=0.02
    )
    thin = calibrated_half_spread_bps(
        price=10.0, adv_dollars=200_000.0, volatility_pct=0.02
    )
    assert thin > thick


def test_calibrated_spread_widens_for_cheaper_price():
    """A cheaper stock pays more bps to cross the spread."""
    cheap = calibrated_half_spread_bps(
        price=1.0, adv_dollars=5_000_000.0, volatility_pct=0.02
    )
    expensive = calibrated_half_spread_bps(
        price=50.0, adv_dollars=5_000_000.0, volatility_pct=0.02
    )
    assert cheap > expensive


def test_calibrated_quote_age_within_bounds():
    q = synthesize_calibrated_quote(
        signal_price=20.0, at=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        max_quote_age_seconds=10,
    )
    assert 1.0 <= q.quote_age_seconds <= 10.0
    assert q.spread_pct > 0.0
