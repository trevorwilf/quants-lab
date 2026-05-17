"""Phase 6: soft fade with execute_threshold=8 must NOT trigger an exit."""

from __future__ import annotations

from bowaka_lab.features.signal_fade_features import IntradayContext
from bowaka_lab.sim.signal_fade import compute_signal_fade_score


def _ctx(**overrides) -> IntradayContext:
    base = dict(
        current_price=9.95,
        prior_close=10.0,
        session_open=10.0,
        vwap_now=10.0,
        opening_range_high=10.05,
        opening_range_low=9.99,
        running_high=10.1,
        running_low=9.9,
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


def test_soft_fade_below_execute_threshold():
    # Construct a soft fade: below prior close and VWAP, but above entry, above
    # opening range low, and not in bottom 40% of intraday range. Score 4 → soft.
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
            running_high=10.02,
            running_low=9.98,
            made_higher_high_since_entry=True,
        ),
    )
    assert res.score < 8
    assert res.bucket in ("none", "soft")
