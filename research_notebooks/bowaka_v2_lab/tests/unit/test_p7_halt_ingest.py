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

from bowaka_v2_lab.data.halt_ingest import (
    parse_nasdaq_halt_rss,
    parse_nasdaq_halt_table,
    write_halt_statuses,
)

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


# --- TradingHaltSearch JSON-RPC result-table parser ----------------------------------
# REAL Nasdaq records pulled via BL_TradeHalt.GetHaltsByDate (2024-06-03) +
# SearchTradeHaltsNEW, in the real GenTable shape: <th class="gtcolN"> headers, plain
# whitespace-padded <td> data cells. GME's M (market-wide LULD) pause on 2024-06-03 is
# the Roaring-Kitty-era halt; SWAV (deficiency) + AMOD (T1, still halted, ms time) cover
# the non-LULD / open-halt / fractional-seconds paths.
_TABLE = """<div class="genTable"><table>
<colgroup><col class="gtcol1"></col></colgroup>
<tr>
  <th class="gtcol1">Halt Date</th><th class="gtcol2">Halt Time</th>
  <th class="gtcol3">Issue Symbol</th><th class="gtcol4">Issue Name</th>
  <th class="gtcol5">Market</th><th class="gtcol6">Reason Code</th>
  <th class="gtcol7">Pause Threshold Price</th><th class="gtcol8">Resumption Date</th>
  <th class="gtcol9">Resumption Quote Time</th><th class="gtcol10">Resumption Trade Time</th>
</tr>
<tr>
  <td>06/03/2024                    </td><td>09:31:17</td><td>GME</td>
  <td>GameStop Corporation Common Stock</td><td>NYSE</td><td>M</td><td></td>
  <td>06/03/2024                    </td><td>09:36:21                      </td><td>09:36:21                      </td>
</tr>
<tr>
  <td>05/30/2024</td><td>19:50:00</td><td>SWAV</td><td>Shockwave Medical Cmn</td>
  <td>NASDAQ</td><td>D</td><td></td><td>06/03/2024</td><td>00:00:01</td><td>00:00:01</td>
</tr>
<tr>
  <td>06/12/2026</td><td>19:50:00.000</td><td>AMOD</td><td>Alpha Modus Hldgs A</td>
  <td>NASDAQ</td><td>T1</td><td></td><td></td><td></td><td></td>
</tr>
</table></div>"""


def test_parse_table_gme_luld_and_swav_deficiency() -> None:
    rows = {r["symbol"]: r for r in parse_nasdaq_halt_table(_TABLE)}
    assert set(rows) == {"GME", "SWAV", "AMOD"}
    g = rows["GME"]
    assert g["reason"] == "M" and g["is_luld"] is True and g["market"] == "NYSE"
    # 09:31:17 ET (EDT = UTC-4 in June) -> 13:31:17 UTC; resume 09:36:21 -> 13:36:21 UTC.
    # (whitespace-padded date/time cells must be trimmed.)
    assert g["ts_start"] == pd.Timestamp("2024-06-03 13:31:17", tz="UTC")
    assert g["ts_end"] == pd.Timestamp("2024-06-03 13:36:21", tz="UTC")
    s = rows["SWAV"]
    assert s["reason"] == "D" and s["is_luld"] is False
    assert s["ts_start"] == pd.Timestamp("2024-05-30 23:50:00", tz="UTC")  # 19:50 EDT


def test_parse_table_millisecond_time_and_still_halted() -> None:
    a = {r["symbol"]: r for r in parse_nasdaq_halt_table(_TABLE)}["AMOD"]
    assert a["reason"] == "T1" and a["is_luld"] is False
    # 19:50:00.000 parses despite the millisecond suffix; 19:50 EDT -> 23:50 UTC.
    assert a["ts_start"] == pd.Timestamp("2026-06-12 23:50:00", tz="UTC")
    assert a["ts_end"] is None  # empty resumption cells -> still halted


def test_parse_table_no_data_and_non_table() -> None:
    assert parse_nasdaq_halt_table("No Data Found") == []
    assert parse_nasdaq_halt_table("") == []
    assert parse_nasdaq_halt_table("<html><body>nope</body></html>") == []


def test_table_writer_roundtrips_through_halt_feed(tmp_path) -> None:
    """The JSON-RPC table parser feeds the same statuses/ <-> read_halt_events contract
    as the RSS parser (one (symbol, halt-date) file each)."""
    from bowaka_v2_lab.data.halt_feed import read_halt_events

    lake = tmp_path / "lake"
    n_files = write_halt_statuses(lake, parse_nasdaq_halt_table(_TABLE), vendor="alpaca")
    assert n_files == 3  # GME 06/03, SWAV 05/30, AMOD 06/12

    ev = read_halt_events(lake, "GME", dt.date(2024, 6, 3), dt.date(2024, 6, 4), vendor="alpaca")
    assert len(ev) == 1 and ev[0].reason == "M"
    assert ev[0].ts_start == pd.Timestamp("2024-06-03 13:31:17", tz="UTC")
    assert ev[0].ts_end == pd.Timestamp("2024-06-03 13:36:21", tz="UTC")
