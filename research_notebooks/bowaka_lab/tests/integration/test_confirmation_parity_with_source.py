"""Phase fidelity-3: lab ``confirm_entry`` matches source ``_confirm_entry``.

Feeds matched fixtures into both implementations and asserts the same
``(passed, fail_reason)`` for every case.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from bowaka_lab.sim.intraday_confirmation import confirm_entry
from tests.fixtures.source_confirm_entry import Entry, _confirm_entry as source_confirm


_NOW = datetime(2026, 5, 17, 14, 45, 0, tzinfo=timezone.utc)
_FRESH = (_NOW - timedelta(seconds=5)).isoformat()
_STALE = (_NOW - timedelta(seconds=30)).isoformat()


def _quote(**kw):
    base = {"bid": 9.95, "ask": 10.05, "timestamp": _FRESH}
    base.update(kw)
    return base


CASES = [
    # (label, close, cfg_ic, quote, expected_passed, expected_reason)
    (
        "valid_quote",
        10.0,
        {"max_spread_pct": 0.02, "max_quote_age_seconds": 15,
         "price_band": {"max_pct_above_close": 0.15, "min_pct_below_close": -0.02}},
        _quote(),
        True, None,
    ),
    (
        "wide_spread",
        10.0,
        {"max_spread_pct": 0.005, "max_quote_age_seconds": 15,
         "price_band": {"max_pct_above_close": 0.15, "min_pct_below_close": -0.02}},
        _quote(bid=9.5, ask=10.5),
        False, "spread>0.0050",
    ),
    (
        "stale_quote",
        10.0,
        {"max_spread_pct": 0.02, "max_quote_age_seconds": 15,
         "price_band": {"max_pct_above_close": 0.15, "min_pct_below_close": -0.02}},
        _quote(timestamp=_STALE),
        False, "quote_age>15s",
    ),
    (
        "inverted_bid_ask",
        10.0,
        {"max_spread_pct": 0.02, "max_quote_age_seconds": 15,
         "price_band": {"max_pct_above_close": 0.15, "min_pct_below_close": -0.02}},
        _quote(bid=10.10, ask=10.00),
        False, "no_quote",
    ),
    (
        "zero_bid",
        10.0,
        {"max_spread_pct": 0.02, "max_quote_age_seconds": 15,
         "price_band": {"max_pct_above_close": 0.15, "min_pct_below_close": -0.02}},
        _quote(bid=0.0),
        False, "no_quote",
    ),
    (
        "above_band_mid_chase",
        10.0,
        {"max_spread_pct": 0.50, "max_quote_age_seconds": 15,
         "price_band": {"max_pct_above_close": 0.15, "min_pct_below_close": -0.02}},
        _quote(bid=11.99, ask=12.01),  # mid=12 > 10*1.15=11.5
        False, "chase>0.15",
    ),
    (
        "below_band_mid_failure",
        10.0,
        {"max_spread_pct": 0.50, "max_quote_age_seconds": 15,
         "price_band": {"max_pct_above_close": 0.15, "min_pct_below_close": -0.02}},
        _quote(bid=9.49, ask=9.51),  # mid=9.5 < 10*0.98=9.8
        False, "failure<-0.02",
    ),
    (
        "exact_at_spread_threshold_passes",
        10.0,
        {"max_spread_pct": 0.02, "max_quote_age_seconds": 0,
         "price_band": {"max_pct_above_close": 0.50, "min_pct_below_close": -0.50}},
        # spread/mid = 0.10/10.0 = 0.01, NOT > 0.02 → passes
        _quote(bid=9.95, ask=10.05, timestamp=None),
        True, None,
    ),
]


@pytest.mark.parametrize(
    "label,close,cfg_ic,quote,expected_passed,expected_reason",
    [pytest.param(*c, id=c[0]) for c in CASES],
)
def test_lab_confirm_entry_matches_source(label, close, cfg_ic, quote, expected_passed, expected_reason):
    # Source reference.
    src_passed, src_reason = source_confirm(
        Entry(close_price=close), cfg_ic, quote, now_utc=_NOW
    )
    assert (src_passed, src_reason) == (expected_passed, expected_reason), (
        f"source result drifted from expectation for {label!r}: got ({src_passed}, {src_reason})"
    )

    # Lab port. The lab uses keyword args + a slightly richer return type.
    lab = confirm_entry(
        candidate_close=close,
        quote_row=quote,
        now_utc=pd.Timestamp(_NOW),
        max_spread_pct=cfg_ic["max_spread_pct"],
        max_quote_age_seconds=cfg_ic["max_quote_age_seconds"],
        price_band_max_above=cfg_ic["price_band"]["max_pct_above_close"],
        price_band_min_below=cfg_ic["price_band"]["min_pct_below_close"],
    )
    assert (lab.passed, lab.fail_reason) == (src_passed, src_reason), (
        f"lab vs source mismatch for {label!r}: lab=({lab.passed}, {lab.fail_reason}) "
        f"src=({src_passed}, {src_reason})"
    )
