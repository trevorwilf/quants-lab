"""P7 §5.2 — Nasdaq Trader trade-halt ingester (statuses/ producer).

Parses the Nasdaq Trader trade-halt feed into the ``statuses/`` schema that
:func:`bowaka_v2_lab.data.halt_feed.read_halt_events` + the DQ halt gate
(``halt_data_unavailable_when_required``) consume, so ``intended_realism`` stops
failing closed at the DQ preflight once a ``statuses/`` partition exists.

DATA GATE (§5.2): Alpaca serves NO historical halt/LULD data. ``nasdaqtrader.com``
is now reachable (the earlier DNS block is gone), so this module ships BOTH ingest
paths, validated against real Nasdaq pulls:

* :func:`parse_nasdaq_halt_rss` — the live RSS feed (``rss.aspx?feed=tradehalts``),
  which is a snapshot of CURRENTLY-OPEN halts only (not a historical log).
* :func:`parse_nasdaq_halt_table` + :class:`NasdaqHaltRpcClient` — the
  TradingHaltSearch JSON-RPC (Jayrock at ``RPCHandler.axd``). ``GetHaltsByDate``
  (``YYYYMMDD``) returns one historical day and reaches back years (verified on
  2024-06-03 — e.g. the GME market-wide LULD pause); ``SearchTradeHaltsNEW``
  returns the trailing ~1 year (~13k halts) in one call. This is the historical
  source the operator runs (``scripts/backfill_halts.py``) to populate ``statuses/``.

Onset + LULD bands come from these feeds; halt RESUME can additionally be inferred
from reopening auctions (P6), a documented follow-up (see docs/p7_halt_gate_gap.md).

statuses/ schema (per ``halt_feed.HaltEvent``): ``symbol, ts_start, ts_end, reason``
(``ts_end`` = resumption trade time, or ``None`` while still halted).
"""
from __future__ import annotations

import datetime as _dt
import html as _html
import json as _json
import re as _re
import urllib.request as _urlreq
import xml.etree.ElementTree as _ET
from typing import Any, Optional

import pandas as pd

#: Nasdaq Trader RSS namespace for the trade-halt feed item fields.
_NDAQ_NS = "http://www.nasdaqtrader.com/"
#: Reason codes that are LULD volatility pauses (vs news/regulatory halts).
LULD_REASON_CODES: frozenset[str] = frozenset({"LUDP", "LUDS", "M"})


def _text(item: _ET.Element, tag: str) -> Optional[str]:
    """First non-empty text for ``ndaq:<tag>`` (namespaced or bare)."""
    for path in (f"{{{_NDAQ_NS}}}{tag}", tag):
        el = item.find(path)
        if el is not None and el.text and el.text.strip():
            return el.text.strip()
    return None


def _et_to_utc(date_str: Optional[str], time_str: Optional[str]) -> Optional[pd.Timestamp]:
    """Combine Nasdaq ``MM/DD/YYYY`` + ``HH:MM:SS`` (US/Eastern) into a UTC Timestamp."""
    if not date_str:
        return None
    fmt_date = "%m/%d/%Y"
    try:
        d = _dt.datetime.strptime(date_str.strip(), fmt_date).date()
    except ValueError:
        try:
            d = _dt.date.fromisoformat(date_str.strip()[:10])
        except ValueError:
            return None
    t = _dt.time(0, 0, 0)
    if time_str and time_str.strip():
        for tf in ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"):
            try:
                t = _dt.datetime.strptime(time_str.strip(), tf).time()
                break
            except ValueError:
                continue
    try:
        ts = pd.Timestamp(_dt.datetime.combine(d, t), tz="America/New_York")
        return ts.tz_convert("UTC")
    except Exception:  # noqa: BLE001 — DST-invalid / unparseable -> drop the time
        return None


def parse_nasdaq_halt_rss(xml_text: str) -> list[dict[str, Any]]:
    """Parse a Nasdaq Trader trade-halt RSS document into ``statuses/`` rows.

    Each ``<item>`` carries ``ndaq:IssueSymbol``, ``ndaq:HaltDate`` / ``HaltTime``,
    ``ndaq:ReasonCode``, ``ndaq:ResumptionDate`` / ``ResumptionTradeTime`` (+
    ``ResumptionQuoteTime``, ``PauseThresholdPrice``). Returns one row per item with
    ``symbol, ts_start, ts_end, reason`` (+ ``market``, ``is_luld``,
    ``pause_threshold_price``). Items without a symbol or halt date are dropped.
    """
    out: list[dict[str, Any]] = []
    if not xml_text or not xml_text.strip():
        return out
    try:
        root = _ET.fromstring(xml_text)
    except _ET.ParseError:
        return out
    for item in root.iter("item"):
        symbol = _text(item, "IssueSymbol")
        ts_start = _et_to_utc(_text(item, "HaltDate"), _text(item, "HaltTime"))
        if not symbol or ts_start is None:
            continue
        ts_end = _et_to_utc(
            _text(item, "ResumptionDate"),
            _text(item, "ResumptionTradeTime") or _text(item, "ResumptionQuoteTime"),
        )
        reason = (_text(item, "ReasonCode") or "UNKNOWN").upper()
        thr = _text(item, "PauseThresholdPrice")
        out.append({
            "symbol": str(symbol).upper(),
            "ts_start": ts_start,
            "ts_end": ts_end,  # None = still halted at feed time
            "reason": reason,
            "market": _text(item, "Market"),
            "is_luld": reason in LULD_REASON_CODES,
            "pause_threshold_price": (float(thr) if thr and thr.replace(".", "", 1).isdigit() else None),
        })
    return out


#: TradingHaltSearch result-table header label -> internal field name. The data
#: ``<td>`` cells are positional (no class); we map by the ``<th>`` header order so
#: column reordering can't silently mis-map.
_TABLE_COL_FIELDS: dict[str, str] = {
    "Halt Date": "halt_date",
    "Halt Time": "halt_time",
    "Issue Symbol": "symbol",
    "Issue Name": "issue_name",
    "Market": "market",
    "Reason Code": "reason",
    "Pause Threshold Price": "pause_threshold_price",
    "Resumption Date": "resume_date",
    "Resumption Quote Time": "resume_quote_time",
    "Resumption Trade Time": "resume_trade_time",
}
_TR_RE = _re.compile(r"<tr[^>]*>(.*?)</tr>", _re.S | _re.I)
_TD_RE = _re.compile(r"<td[^>]*>(.*?)</td>", _re.S | _re.I)
_TH_RE = _re.compile(r"<th[^>]*>(.*?)</th>", _re.S | _re.I)
_TAG_RE = _re.compile(r"<[^>]+>")


def _cell_text(raw: str) -> str:
    """Strip tags, unescape entities, collapse the Nasdaq cell whitespace padding."""
    return _re.sub(r"\s+", " ", _html.unescape(_TAG_RE.sub(" ", raw))).strip()


def parse_nasdaq_halt_table(html_text: str) -> list[dict[str, Any]]:
    """Parse a TradingHaltSearch result table (``GetHaltsByDate`` /
    ``SearchTradeHaltsNEW`` HTML) into the same ``statuses/`` rows as
    :func:`parse_nasdaq_halt_rss`.

    Columns (``Halt Date, Halt Time, Issue Symbol, Issue Name, Market, Reason Code,
    Pause Threshold Price, Resumption Date, Resumption Quote Time, Resumption Trade
    Time``) are mapped by the ``<th>`` header order. Returns one row per data row with
    ``symbol, ts_start, ts_end, reason, market, is_luld, pause_threshold_price``; rows
    without a symbol or halt timestamp are dropped, and ``'No Data Found'`` / non-table
    input yields ``[]``.
    """
    out: list[dict[str, Any]] = []
    if not html_text or "<t" not in html_text.lower():
        return out
    rows = _TR_RE.findall(html_text)
    headers: Optional[list[str]] = None
    for row in rows:
        ths = _TH_RE.findall(row)
        if ths:
            headers = [_cell_text(h) for h in ths]
            break
    if not headers:
        return out
    fields = [_TABLE_COL_FIELDS.get(h) for h in headers]
    for row in rows:
        if _TH_RE.search(row):
            continue
        tds = _TD_RE.findall(row)
        if len(tds) < len(headers):
            continue
        rec: dict[str, str] = {}
        for field, td in zip(fields, tds):
            if field:
                rec[field] = _cell_text(td)
        symbol = rec.get("symbol")
        ts_start = _et_to_utc(rec.get("halt_date"), rec.get("halt_time"))
        if not symbol or ts_start is None:
            continue
        ts_end = _et_to_utc(
            rec.get("resume_date"),
            rec.get("resume_trade_time") or rec.get("resume_quote_time"),
        )
        reason = (rec.get("reason") or "UNKNOWN").upper()
        thr = rec.get("pause_threshold_price")
        out.append({
            "symbol": str(symbol).upper(),
            "ts_start": ts_start,
            "ts_end": ts_end,  # None = still halted at pull time
            "reason": reason,
            "market": rec.get("market") or None,
            "is_luld": reason in LULD_REASON_CODES,
            "pause_threshold_price": (float(thr) if thr and thr.replace(".", "", 1).isdigit() else None),
        })
    return out


class NasdaqHaltRpcClient:
    """Network client for the Nasdaq TradingHaltSearch JSON-RPC (Jayrock, version 1.1,
    at ``RPCHandler.axd``). OPERATOR USE — run where ``nasdaqtrader.com`` resolves.

    The handler is Referer-guarded, so the constructor first GETs the search page to
    establish the session cookies + a valid Referer. Two accessors:

    * :meth:`halts_for_day` — ``BL_TradeHalt.GetHaltsByDate('YYYYMMDD')``; one
      historical day, reaches back years (the per-day backfill primitive).
    * :meth:`recent_halts` — ``BL_TradeHalt.SearchTradeHaltsNEW``; the trailing ~1
      year (~13k halts) in a single call.

    Both return the raw result HTML for :func:`parse_nasdaq_halt_table`.
    """

    _PAGE = "https://nasdaqtrader.com/Trader.aspx?id=TradingHaltSearch"
    _RPC = "https://nasdaqtrader.com/RPCHandler.axd"

    def __init__(self, *, timeout: int = 60) -> None:
        import http.cookiejar

        self._timeout = timeout
        self._opener = _urlreq.build_opener(
            _urlreq.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self._opener.addheaders = [("User-Agent", "Mozilla/5.0")]
        self._opener.open(self._PAGE, timeout=timeout).read()  # cookies + Referer setup

    def _call(self, method: str, args: list[Any]) -> Any:
        body = _json.dumps(
            {"id": 1, "method": method, "params": _json.dumps(list(args)), "version": "1.1"}
        ).encode()
        req = _urlreq.Request(
            self._RPC,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Referer": self._PAGE,
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0",
            },
        )
        raw = self._opener.open(req, timeout=self._timeout).read().decode("utf-8-sig", "replace")
        return _json.loads(raw).get("result")

    def halts_for_day(self, day: Any) -> str:
        """``day``: a ``datetime.date`` or ``'YYYYMMDD'`` string. Returns result HTML."""
        if hasattr(day, "strftime"):
            day = day.strftime("%Y%m%d")
        return self._call("BL_TradeHalt.GetHaltsByDate", [str(day)]) or ""

    def recent_halts(self) -> str:
        """Trailing ~1 year of halts in one call. Returns the result HTML."""
        return self._call("BL_TradeHalt.SearchTradeHaltsNEW", [""] * 7) or ""


def write_halt_statuses(lake_root: Any, rows: list[dict[str, Any]], *, vendor: str = "alpaca") -> int:
    """Write parsed halt rows to the per-symbol/date ``statuses/`` partition.

    Groups by ``(symbol, halt date)`` and writes
    ``statuses/vendor=<vendor>/symbol=<S>/date=<YYYY-MM-DD>/part.parquet`` (the tree
    :func:`halt_feed.read_halt_events` reads). Returns the number of files written.
    """
    from bowaka_common.marketdata import layout

    if not rows:
        return 0
    df = pd.DataFrame(rows)
    df["ts_start"] = pd.to_datetime(df["ts_start"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts_start", "symbol"])
    if df.empty:
        return 0
    df["_date"] = df["ts_start"].dt.date
    written = 0
    for (sym, day), g in df.groupby(["symbol", "_date"]):
        path = layout.statuses_path(lake_root, str(sym), day, vendor=vendor)
        g = g.drop(columns=["_date"]).sort_values("ts_start").reset_index(drop=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        g.to_parquet(path, index=False)
        written += 1
    return written


__all__ = [
    "parse_nasdaq_halt_rss",
    "parse_nasdaq_halt_table",
    "NasdaqHaltRpcClient",
    "write_halt_statuses",
    "LULD_REASON_CODES",
]
