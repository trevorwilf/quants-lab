"""Phase 3 — delisting / survivorship.

A symbol whose asset-master ``status`` is not ``active`` as of the session date
is excluded with rejection reason ``delisted``. This keeps a delisted ticker out
of the point-in-time universe even when its (stale) prior bars would otherwise
pass the price + ADV gates.
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


def test_delisted_symbol_excluded() -> None:
    # GONE is delisted (status != active); ALIVE is active. Both have ample,
    # in-band prior bars, so only the delisting filter can drop GONE.
    am = asset_master_frame(
        [
            {"symbol": "GONE", "status": "delisted"},
            {"symbol": "ALIVE", "status": "active"},
        ]
    )
    daily = {
        "GONE": daily_bars_frame("GONE", end_before=_SESSION),
        "ALIVE": daily_bars_frame("ALIVE", end_before=_SESSION),
    }
    records = build_pit_universe(_SESSION, realism_cfg(), FakeLakeStore(am, daily))

    assert "delisted" in records["GONE"].rejection_reasons
    assert not records["GONE"].eligible_for_bowaka_equity_bucket

    assert "delisted" not in records["ALIVE"].rejection_reasons
    assert records["ALIVE"].eligible_for_bowaka_equity_bucket


def test_inactive_status_variants_are_delisted() -> None:
    # Any non-active status counts as delisted for the gate.
    am = asset_master_frame(
        [
            {"symbol": "INACT", "status": "inactive"},
            {"symbol": "SUSP", "status": "suspended"},
        ]
    )
    daily = {
        "INACT": daily_bars_frame("INACT", end_before=_SESSION),
        "SUSP": daily_bars_frame("SUSP", end_before=_SESSION),
    }
    records = build_pit_universe(_SESSION, realism_cfg(), FakeLakeStore(am, daily))
    assert "delisted" in records["INACT"].rejection_reasons
    assert "delisted" in records["SUSP"].rejection_reasons
