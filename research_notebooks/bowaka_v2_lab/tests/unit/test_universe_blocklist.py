"""Phase 3 — ticker-blocklist exclusion.

The live contract blocks ``TSLL`` / ``CONL`` / ``SMCX``. The PIT universe
builder must exclude any blocklisted symbol with rejection reason ``blocklist``,
even when every other filter would have passed it.
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


def test_blocklisted_symbols_excluded() -> None:
    # Three blocklisted + one clean operating equity, all otherwise eligible.
    syms = ("TSLL", "CONL", "SMCX", "GOODCO")
    am = asset_master_frame([{"symbol": s} for s in syms])
    daily = {s: daily_bars_frame(s, end_before=_SESSION) for s in syms}
    records = build_pit_universe(_SESSION, realism_cfg(), FakeLakeStore(am, daily))

    for blocked in ("TSLL", "CONL", "SMCX"):
        assert "blocklist" in records[blocked].rejection_reasons, blocked
        assert not records[blocked].eligible_for_bowaka_equity_bucket, blocked
    # The non-blocklisted operating equity passes every filter.
    assert records["GOODCO"].eligible_for_bowaka_equity_bucket
    assert records["GOODCO"].rejection_reasons == []


def test_config_blocklist_additions_are_honored() -> None:
    # EXTRA1 is added via the config blocklist (additive to the contract default).
    cfg = realism_cfg(ticker_blocklist=["TSLL", "EXTRA1"])
    syms = ("EXTRA1", "CLEAN")
    am = asset_master_frame([{"symbol": s, "exchange": "NYSE"} for s in syms])
    daily = {s: daily_bars_frame(s, end_before=_SESSION) for s in syms}
    records = build_pit_universe(_SESSION, cfg, FakeLakeStore(am, daily))

    assert "blocklist" in records["EXTRA1"].rejection_reasons
    assert records["CLEAN"].eligible_for_bowaka_equity_bucket
