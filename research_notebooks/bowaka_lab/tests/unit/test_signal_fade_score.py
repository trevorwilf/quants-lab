"""Phase 6: signal-fade score per §13.2 — hand-crafted scenarios."""

from __future__ import annotations

import pytest

from bowaka_lab.features.signal_fade_features import IntradayContext
from bowaka_lab.sim.signal_fade import compute_signal_fade_score


def _ctx(**overrides) -> IntradayContext:
    base = dict(
        current_price=10.0,
        prior_close=10.0,
        session_open=10.0,
        vwap_now=10.0,
        opening_range_high=10.2,
        opening_range_low=9.95,
        running_high=10.3,
        running_low=9.95,
        short_ema_distance=0.0,
        spread_pct=0.001,
        quote_age_seconds=0.0,
        minutes_since_entry=60,
        rvol_now=1.5,
        morning_continuation_volume=1_000_000,
        last_30m_volume=900_000,
        made_higher_high_since_entry=True,
    )
    base.update(overrides)
    return IntradayContext(**base)


def test_clean_strong_position_scores_zero():
    res = compute_signal_fade_score(
        entry_price=10.0,
        mfe_pct=0.04,
        current_return_pct=0.04,
        minutes_since_entry=60,
        intraday=_ctx(current_price=10.4),
    )
    assert res.bucket == "none"
    assert res.score <= 2


def test_below_vwap_alone_is_soft_fade():
    """Report §13.2: 'below VWAP alone -> soft fade'.

    The position is *above* entry, *above* prior close, *above* session open,
    *above* opening-range low, no MFE giveback, healthy RVOL, no spread/quote
    issues, and the position has made a higher high. The ONLY thing wrong is
    being below VWAP. Per spec, that alone is enough to enter the soft bucket.
    """
    # parity-note: running_high/running_low widened from the original (10.02/9.98)
    # so current_price=9.99 sits at the top-60% boundary of the intraday range
    # rather than the bottom 40% -- otherwise price_in_bottom_40pct_intraday_range
    # would also trigger and contaminate the "vwap alone" scenario.
    res = compute_signal_fade_score(
        entry_price=9.95,
        mfe_pct=0.0,
        current_return_pct=(9.99 / 9.95) - 1.0,  # ~+0.4%, tiny green
        minutes_since_entry=60,
        intraday=_ctx(
            current_price=9.99,
            vwap_now=10.00,            # the only "below" trigger
            prior_close=9.50,          # above
            session_open=9.50,         # above
            opening_range_low=9.00,    # above
            running_high=10.05,
            running_low=9.95,
            short_ema_distance=0.0,    # not below
            spread_pct=0.001,          # tiny, no spread triggers
            quote_age_seconds=0.0,
            rvol_now=1.5,              # above hold threshold
            made_higher_high_since_entry=True,
        ),
    )
    triggered = {c.name for c in res.components}
    # The ONLY triggered component should be price_below_vwap.
    assert triggered == {"price_below_vwap"}, (
        f"expected only price_below_vwap triggered, got {triggered}"
    )
    assert res.score == 3, f"expected score=3, got {res.score}"
    assert res.bucket == "soft", f"expected bucket='soft', got {res.bucket!r}"


def test_below_vwap_and_prior_close_above_entry_is_soft_fade():
    # Entry at 9.95, now 9.99 -> above entry; below vwap (10.0) and prior_close (10.0).
    # No higher high made yet, but ema dist 0, no spread issues, MFE 0.
    # parity-note: running_high/running_low widened from the original (10.02/9.98)
    # so current_price=9.99 is no longer in the bottom 40% of the intraday range.
    # Without this, price_in_bottom_40pct_intraday_range adds +1 and the score
    # tips into the hard bucket once price_below_vwap moved from +2 to +3.
    res = compute_signal_fade_score(
        entry_price=9.95,
        mfe_pct=0.0,
        current_return_pct=(9.99 / 9.95) - 1.0,
        minutes_since_entry=60,
        intraday=_ctx(
            current_price=9.99,
            vwap_now=10.0,
            prior_close=10.0,
            session_open=9.99,
            opening_range_low=9.5,
            running_high=10.05,
            running_low=9.95,
            made_higher_high_since_entry=True,
        ),
    )
    # Below prior close (+2) + below VWAP (+3) = 5 -> soft (3-5)
    assert res.bucket == "soft"


def test_mfe_giveback_triggers_high_score():
    # MFE 0.12, current return 0.02 → giveback ~83%
    res = compute_signal_fade_score(
        entry_price=10.0,
        mfe_pct=0.12,
        current_return_pct=0.02,
        minutes_since_entry=120,
        intraday=_ctx(current_price=10.2, vwap_now=10.3, running_high=11.2, running_low=9.9),
    )
    # Should add 3 from mfe_giveback_12pct
    components = {c.name for c in res.components}
    assert "mfe_giveback_12pct_70pct" in components


def test_below_vwap_and_below_prior_close_plus_giveback_is_hard():
    res = compute_signal_fade_score(
        entry_price=10.0,
        mfe_pct=0.08,
        current_return_pct=0.01,
        minutes_since_entry=120,
        intraday=_ctx(
            current_price=9.8,
            vwap_now=10.0,
            prior_close=10.0,
            session_open=10.0,
            running_high=10.85,
            running_low=9.8,
            opening_range_low=10.0,
            made_higher_high_since_entry=False,
        ),
    )
    assert res.bucket in ("hard", "critical")


def test_liquidity_severe_spread_adds_score():
    res = compute_signal_fade_score(
        entry_price=10.0,
        mfe_pct=0.0,
        current_return_pct=0.0,
        minutes_since_entry=60,
        intraday=_ctx(spread_pct=0.05, quote_age_seconds=20.0),
    )
    component_names = {c.name for c in res.components}
    assert "spread_severe" in component_names
    assert "quote_age_severe" in component_names


def test_critical_fade_above_9():
    res = compute_signal_fade_score(
        entry_price=10.0,
        mfe_pct=0.12,
        current_return_pct=-0.05,
        minutes_since_entry=240,
        intraday=_ctx(
            current_price=9.5,
            vwap_now=10.0,
            prior_close=10.0,
            session_open=10.0,
            opening_range_low=10.0,
            running_high=11.2,
            running_low=9.5,
            short_ema_distance=-0.02,
            spread_pct=0.05,
            quote_age_seconds=20.0,
            rvol_now=0.5,
            morning_continuation_volume=1_000_000,
            last_30m_volume=100_000,
            made_higher_high_since_entry=False,
        ),
    )
    assert res.score >= 9
    assert res.bucket == "critical"
