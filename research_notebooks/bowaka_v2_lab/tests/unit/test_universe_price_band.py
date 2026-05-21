"""Phase 3 — price-band filter on the prior close.

The contract price band is ``[1.0, 20.0]``. The PIT builder gates on the
*prior* session close: a symbol whose prior close is $0.50 is rejected with
``price_below_min``; a symbol whose prior close is $25 is rejected with
``price_above_max``.
"""
from __future__ import annotations

import datetime as _dt

from bowaka_v2_lab.universe.builder import build_pit_universe
from tests.fixtures.universe_fixture import (
    FakeLakeStore,
    asset_master_frame,
    daily_bars_frame,
    realism_cfg,
)

_SESSION = _dt.date(2024, 9, 4)


def test_price_band_rejects_below_min_and_above_max() -> None:
    # PENNY prior close $0.50 (below $1); EXPENSIVE prior close $25 (above $20);
    # MIDCAP prior close $10 (inside the band). All carry ample ADV.
    am = asset_master_frame(
        [{"symbol": s} for s in ("PENNY", "EXPENSIVE", "MIDCAP")]
    )
    daily = {
        # 500k shares so even at $0.50 the ADV ($250k) is not the limiting gate
        # for PENNY — the test isolates the price filter.
        "PENNY": daily_bars_frame("PENNY", end_before=_SESSION, close=0.50, volume=2_000_000),
        "EXPENSIVE": daily_bars_frame("EXPENSIVE", end_before=_SESSION, close=25.0),
        "MIDCAP": daily_bars_frame("MIDCAP", end_before=_SESSION, close=10.0),
    }
    records = build_pit_universe(_SESSION, realism_cfg(), FakeLakeStore(am, daily))

    assert "price_below_min" in records["PENNY"].rejection_reasons
    assert not records["PENNY"].eligible_for_bowaka_equity_bucket
    assert records["PENNY"].prior_close == 0.50

    assert "price_above_max" in records["EXPENSIVE"].rejection_reasons
    assert not records["EXPENSIVE"].eligible_for_bowaka_equity_bucket
    assert records["EXPENSIVE"].prior_close == 25.0

    # The in-band symbol passes the price filter (and every other filter).
    assert records["MIDCAP"].eligible_for_bowaka_equity_bucket
    assert "price_below_min" not in records["MIDCAP"].rejection_reasons
    assert "price_above_max" not in records["MIDCAP"].rejection_reasons


def test_price_at_band_edges_is_inclusive() -> None:
    # Exactly $1.00 and exactly $20.00 are inside the band (>= / <=).
    am = asset_master_frame([{"symbol": s} for s in ("ATMIN", "ATMAX")])
    daily = {
        "ATMIN": daily_bars_frame("ATMIN", end_before=_SESSION, close=1.0, volume=1_000_000),
        "ATMAX": daily_bars_frame("ATMAX", end_before=_SESSION, close=20.0),
    }
    records = build_pit_universe(_SESSION, realism_cfg(), FakeLakeStore(am, daily))
    assert records["ATMIN"].eligible_for_bowaka_equity_bucket
    assert records["ATMAX"].eligible_for_bowaka_equity_bucket
