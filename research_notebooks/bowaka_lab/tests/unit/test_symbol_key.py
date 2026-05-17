"""Phase 2: symbol normalization."""

from __future__ import annotations

import pytest

from bowaka_lab.data.assets import classify_instrument, normalize_symbol_key


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("riley", "RILEY"),
        ("brk.b", "BRK-B"),
        ("BRK.A", "BRK-A"),
        ("  qs  ", "QS"),
        ("MMM", "MMM"),
    ],
)
def test_normalize_symbol_key(raw, expected):
    assert normalize_symbol_key(raw) == expected


def test_normalize_handles_empty():
    assert normalize_symbol_key("") == ""


def test_normalize_handles_none():
    assert normalize_symbol_key(None) == ""


@pytest.mark.parametrize(
    ("name", "expected_class"),
    [
        ("ProShares UltraPro QQQ", "leveraged_etp"),
        ("Direxion Daily Semiconductor Bull 3X Shares", "leveraged_etp"),
        ("Direxion Daily Small Cap Bear 3X", "inverse_etp"),
        ("ProShares Short S&P 500", "inverse_etp"),
        ("iPath Series B S&P 500 ETN", "etn"),
        ("Vanguard S&P 500 ETF", "etf"),
        ("Acme Acquisition Corp", "spac"),
        ("B. Riley Financial Inc", "operating_equity"),
        ("Apple Inc", "operating_equity"),
    ],
)
def test_classify_instrument(name, expected_class):
    cls, _ = classify_instrument(name)
    assert cls == expected_class


def test_classify_empty_name_defaults_operating():
    cls, reason = classify_instrument("")
    assert cls == "operating_equity"
    assert "default" in reason
