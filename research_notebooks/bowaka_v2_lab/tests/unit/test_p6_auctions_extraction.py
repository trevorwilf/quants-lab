"""P6 §5.1 — official open/close auction extraction (pure parser).

Pure-logic tests of bowaka_common.marketdata.auctions over the real Alpaca
``/v2/stocks/auctions`` response shape (captured live for AAPL 2025-08-20). The
real-data fidelity assertion (the partition has official prints; official close
~= daily close for liquid names) runs on the lane against the actual lake.
"""
from __future__ import annotations

from bowaka_common.marketdata.auctions import extract_official_auction, parse_auctions_response

# Real response shape (AAPL 2025-08-20, captured from the live API).
_DAY = {
    "d": "2025-08-20",
    "o": [
        {"c": "Q", "p": 229.88, "s": 5, "t": "2025-08-20T13:30:00.1Z", "x": "P"},
        {"c": "O", "p": 230.0, "s": 457314, "t": "2025-08-20T13:30:00.9Z", "x": "Q"},
        {"c": "Q", "p": 230.0, "s": 457314, "t": "2025-08-20T13:30:00.9Z", "x": "Q"},
    ],
    "c": [
        {"c": "6", "p": 226.01, "s": 4543179, "t": "2025-08-20T20:00:00.2Z", "x": "Q"},
        {"c": "M", "p": 226.01, "s": 4543179, "t": "2025-08-20T20:00:00.2Z", "x": "Q"},
    ],
}


def test_extract_official_open_close() -> None:
    row = extract_official_auction(_DAY, symbol="AAPL")
    assert row["session_date"] == "2025-08-20"
    assert row["official_open"] == 230.0       # condition "O" (CTS opening), not the Q quote
    assert row["official_close"] == 226.01     # condition "M" (CTS official close)
    assert row["open_condition"] == "O"
    assert row["close_condition"] == "M"
    assert row["timestamp"] == "2025-08-20T20:00:00.2Z"  # anchors on the close auction


def test_open_only_and_close_only_days() -> None:
    open_only = extract_official_auction({"d": "2025-08-21", "o": _DAY["o"], "c": []}, symbol="AAPL")
    assert open_only["official_open"] == 230.0 and open_only["official_close"] is None
    close_only = extract_official_auction({"d": "2025-08-21", "o": [], "c": _DAY["c"]}, symbol="AAPL")
    assert close_only["official_close"] == 226.01 and close_only["official_open"] is None


def test_empty_day_is_none() -> None:
    assert extract_official_auction({"d": "2025-08-21", "o": [], "c": []}, symbol="AAPL") is None


def test_fallback_to_largest_when_no_priority_condition() -> None:
    # No O/Q/M/6 -> pick the largest-size print as the auction proxy.
    day = {"d": "2025-08-22",
           "o": [{"c": "X", "p": 10.0, "s": 100}, {"c": "X", "p": 10.5, "s": 9000}],
           "c": [{"c": "Y", "p": 11.0, "s": 5000}]}
    row = extract_official_auction(day, symbol="ZZZ")
    assert row["official_open"] == 10.5
    assert row["official_close"] == 11.0


def test_parse_response_filters_unusable_days() -> None:
    data = {"auctions": {"AAA": [_DAY, {"d": "2025-08-21", "o": [], "c": []}]}}
    rows = parse_auctions_response(data, "AAA")
    assert len(rows) == 1 and rows[0]["session_date"] == "2025-08-20"
    assert parse_auctions_response({"auctions": {}}, "AAA") == []
