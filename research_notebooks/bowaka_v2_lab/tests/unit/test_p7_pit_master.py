"""P7 §3.4/§5.3 — PIT/survivorship master (pure logic).

Pins listing/delisting/rename survivorship + min-history eligibility, and the
fail-CLOSED treatment of unknown symbols (the inverse of the ``_status_active("")``
blank-is-active bug this replaces).
"""
from __future__ import annotations

import datetime as dt

from bowaka_v2_lab.universe.pit_master import (
    CA_PIT_HAZARD,
    build_pit_master,
    PitMaster,
)


def _ca(ca_type, symbol, effective_date, *, new_symbol=None,
        is_delisting=False, is_symbol_change=False, is_split=False):
    return {"ca_type": ca_type, "symbol": symbol, "new_symbol": new_symbol,
            "effective_date": effective_date, "is_delisting": is_delisting,
            "is_symbol_change": is_symbol_change, "is_split": is_split}


_LISTING = {"LIVE": dt.date(2024, 1, 1), "DEAD": dt.date(2024, 1, 1),
            "OLD": dt.date(2024, 1, 1), "SPLT": dt.date(2024, 1, 1)}
_CA_ROWS = [
    _ca("worthless_removals", "DEAD", "2024-06-13", is_delisting=True),
    _ca("name_changes", "OLD", "2024-06-11", new_symbol="NEW", is_symbol_change=True),
    _ca("forward_splits", "SPLT", "2024-06-12", is_split=True),
]


def _master() -> PitMaster:
    return build_pit_master(_CA_ROWS, listing_dates=_LISTING, warn_hazard=False)


def test_live_symbol_active_between_listing_and_forever() -> None:
    m = _master()
    assert m.status_as_of("LIVE", dt.date(2023, 12, 31)) == "not_yet_listed"
    assert m.status_as_of("LIVE", dt.date(2024, 1, 1)) == "active"
    assert m.is_active_as_of("LIVE", dt.date(2024, 6, 30))


def test_delisting_from_worthless_removal_on_effective_date() -> None:
    m = _master()
    assert m.is_active_as_of("DEAD", dt.date(2024, 6, 12))         # day before effective
    assert m.status_as_of("DEAD", dt.date(2024, 6, 13)) == "delisted"  # effective day
    assert m.status_as_of("DEAD", dt.date(2024, 7, 1)) == "delisted"
    rec = m.get("DEAD")
    assert rec.delisting_date == dt.date(2024, 6, 13)
    assert rec.delisting_reason == "worthless_removals"


def test_name_change_retires_old_and_lists_successor() -> None:
    m = _master()
    assert m.is_active_as_of("OLD", dt.date(2024, 6, 10))
    assert m.status_as_of("OLD", dt.date(2024, 6, 11)) == "renamed_away"
    old = m.get("OLD")
    assert old.renamed_to == "NEW" and old.rename_date == dt.date(2024, 6, 11)
    new = m.get("NEW")
    assert new is not None and new.renamed_from == "OLD"
    # The successor lists no later than the rename effective date.
    assert new.listing_date is not None and new.listing_date <= dt.date(2024, 6, 11)
    assert new.is_active_as_of(dt.date(2024, 6, 30))


def test_split_does_not_affect_survivorship() -> None:
    m = _master()
    assert m.is_active_as_of("SPLT", dt.date(2024, 6, 30))
    assert m.get("SPLT").delisting_date is None


def test_min_history_eligibility_gate() -> None:
    m = _master()
    on = dt.date(2024, 6, 15)
    assert m.eligible_as_of("LIVE", on, trading_days_available=10,
                            min_history_trading_days=45) == (False, "insufficient_history")
    assert m.eligible_as_of("LIVE", on, trading_days_available=50,
                            min_history_trading_days=45) == (True, None)
    # No count supplied -> history gate skipped (legacy-safe).
    assert m.eligible_as_of("LIVE", on, min_history_trading_days=45) == (True, None)


def test_delisted_and_unknown_are_not_eligible() -> None:
    m = _master()
    assert m.eligible_as_of("DEAD", dt.date(2024, 7, 1),
                            min_history_trading_days=0) == (False, "delisted")
    # Unknown symbol fails CLOSED (the inverse of _status_active("") blank-is-active).
    assert m.status_as_of("GHOST", dt.date(2024, 6, 15)) == "unknown"
    assert m.eligible_as_of("GHOST", dt.date(2024, 6, 15)) == (False, "unknown")


def test_earliest_delisting_effective_date_wins() -> None:
    rows = [
        _ca("redemptions", "X", "2024-09-01", is_delisting=True),
        _ca("cash_mergers", "X", "2024-06-04", is_delisting=True),
    ]
    m = build_pit_master(rows, listing_dates={"X": dt.date(2024, 1, 1)}, warn_hazard=False)
    assert m.get("X").delisting_date == dt.date(2024, 6, 4)


def test_hazard_banner_logged_once(caplog) -> None:
    import logging
    with caplog.at_level(logging.WARNING):
        build_pit_master(_CA_ROWS, listing_dates=_LISTING, warn_hazard=True)
    assert any(CA_PIT_HAZARD in r.message for r in caplog.records)
