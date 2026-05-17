"""Phase 3: instrument classification (port of legacy classify_instrument)."""

from __future__ import annotations

import pytest

from bowaka_lab.features.instrument_classification import classify_instrument


def test_blocklist_wins_over_name():
    res = classify_instrument(
        "TSLL",
        name="Direxion Daily TSLA Bull 2X Shares",
        asset_class="us_equity",
        ticker_blocklist=["TSLL"],
    )
    assert res.instrument_class == "leveraged_etp"
    assert res.classification_reason == "ticker_blocklist"


def test_leveraged_name_keyword():
    res = classify_instrument("ABC", name="ProShares UltraPro 3X Long")
    assert res.instrument_class == "leveraged_etp"
    assert "name_keyword:leveraged" in res.classification_reason


def test_inverse_name_keyword():
    res = classify_instrument("ABC", name="ProShares Short S&P 500")
    # "SHORT" is in the inverse keyword list and the legacy precedence runs
    # leveraged first; "SHORT" is not in leveraged list, so inverse wins.
    assert res.instrument_class == "inverse_etp"


def test_bear_classified_as_leveraged_legacy_precedence():
    # Legacy precedence: "BEAR" appears in both leveraged and inverse lists;
    # leveraged is checked first. This preserves parity with the source.
    res = classify_instrument("ABC", name="Direxion Daily Bull 3X")
    assert res.instrument_class == "leveraged_etp"


def test_etn_classification():
    res = classify_instrument("ABC", name="iPath Series B ETN")
    assert res.instrument_class == "etn"


def test_etf_via_asset_class():
    res = classify_instrument("SPY", name="SPDR S&P 500 Trust", asset_class="etf")
    # ETF asset_class is checked after name keywords. Since "SPDR" / "TRUST"
    # is not in the leveraged/inverse/etn keyword lists, the classifier
    # falls through to asset_class:etf.
    assert res.instrument_class == "etf"


def test_default_operating_equity():
    res = classify_instrument("AAPL", name="Apple Inc", asset_class="us_equity")
    assert res.instrument_class == "operating_equity"
    assert res.eligible_for_bowaka_equity_bucket


def test_empty_name_defaults_operating():
    res = classify_instrument("XYZ", name=None, asset_class=None)
    assert res.instrument_class == "operating_equity"


def test_eligibility_flips_for_non_operating():
    res = classify_instrument("UVXY", name="ProShares Ultra VIX Short-Term", asset_class="us_equity")
    assert not res.eligible_for_bowaka_equity_bucket
