"""P7 §5.2 — Nasdaq halt-RSS parser + statuses/ writer (pure logic + round-trip).

The parser is built to the DOCUMENTED Nasdaq Trader trade-halt RSS shape (the sandbox
cannot reach nasdaqtrader.com — see docs/p7_halt_gate_gap.md); these pins the
field mapping, ET->UTC, LULD classification, and that the writer round-trips through
``halt_feed.read_halt_events`` (the producer<->reader contract that unblocks the IR
halt gate).
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_v2_lab.data.halt_ingest import parse_nasdaq_halt_rss, write_halt_statuses

# Documented Nasdaq trade-halt RSS shape (ndaq: item fields; unqualified <item>).
_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:ndaq="http://www.nasdaqtrader.com/" version="2.0"><channel>
  <item>
    <ndaq:IssueSymbol>ABCD</ndaq:IssueSymbol>
    <ndaq:IssueName>Test Corp</ndaq:IssueName>
    <ndaq:Market>NASDAQ</ndaq:Market>
    <ndaq:ReasonCode>LUDP</ndaq:ReasonCode>
    <ndaq:HaltDate>06/13/2024</ndaq:HaltDate>
    <ndaq:HaltTime>10:30:00</ndaq:HaltTime>
    <ndaq:ResumptionDate>06/13/2024</ndaq:ResumptionDate>
    <ndaq:ResumptionQuoteTime>10:34:30</ndaq:ResumptionQuoteTime>
    <ndaq:ResumptionTradeTime>10:35:00</ndaq:ResumptionTradeTime>
    <ndaq:PauseThresholdPrice>12.34</ndaq:PauseThresholdPrice>
  </item>
  <item>
    <ndaq:IssueSymbol>NEWS</ndaq:IssueSymbol>
    <ndaq:ReasonCode>T1</ndaq:ReasonCode>
    <ndaq:HaltDate>06/13/2024</ndaq:HaltDate>
    <ndaq:HaltTime>09:45:00</ndaq:HaltTime>
  </item>
</channel></rss>"""


def test_parse_luld_halt_with_resumption() -> None:
    rows = {r["symbol"]: r for r in parse_nasdaq_halt_rss(_RSS)}
    assert set(rows) == {"ABCD", "NEWS"}
    a = rows["ABCD"]
    assert a["reason"] == "LUDP" and a["is_luld"] is True
    assert a["market"] == "NASDAQ" and a["pause_threshold_price"] == 12.34
    # 10:30 ET (EDT = UTC-4 in June) -> 14:30 UTC; resumption 10:35 ET -> 14:35 UTC.
    assert a["ts_start"] == pd.Timestamp("2024-06-13 14:30", tz="UTC")
    assert a["ts_end"] == pd.Timestamp("2024-06-13 14:35", tz="UTC")


def test_parse_news_halt_still_halted_not_luld() -> None:
    n = {r["symbol"]: r for r in parse_nasdaq_halt_rss(_RSS)}["NEWS"]
    assert n["reason"] == "T1" and n["is_luld"] is False
    assert n["ts_start"] == pd.Timestamp("2024-06-13 13:45", tz="UTC")  # 09:45 EDT
    assert n["ts_end"] is None  # no resumption -> still halted


def test_empty_and_garbage_inputs() -> None:
    assert parse_nasdaq_halt_rss("") == []
    assert parse_nasdaq_halt_rss("<rss></rss>") == []
    assert parse_nasdaq_halt_rss("not xml at all <") == []


def test_writer_roundtrips_through_halt_feed(tmp_path) -> None:
    """write_halt_statuses -> read_halt_events: the producer<->reader contract that
    makes the lake's statuses/ partition consumable by the IR halt gate."""
    from bowaka_v2_lab.data.halt_feed import read_halt_events

    lake = tmp_path / "lake"
    rows = parse_nasdaq_halt_rss(_RSS)
    n_files = write_halt_statuses(lake, rows, vendor="alpaca")
    assert n_files == 2  # one (symbol, date) file each

    # read_halt_events takes [start, end] timestamps; a bare end-DATE is midnight, so
    # span the session day to include the intraday (14:30 UTC) halt.
    events = read_halt_events(lake, "ABCD", dt.date(2024, 6, 13), dt.date(2024, 6, 14),
                              vendor="alpaca")
    assert len(events) == 1
    ev = events[0]
    assert ev.symbol == "ABCD" and ev.reason == "LUDP"
    assert ev.ts_start == pd.Timestamp("2024-06-13 14:30", tz="UTC")
    assert ev.ts_end == pd.Timestamp("2024-06-13 14:35", tz="UTC")
    # The still-halted news halt reads back with ts_end = None.
    news = read_halt_events(lake, "NEWS", dt.date(2024, 6, 13), dt.date(2024, 6, 14),
                            vendor="alpaca")
    assert len(news) == 1 and news[0].ts_end is None
