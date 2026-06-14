"""P7 §5.2 — Nasdaq Trader trade-halt ingester (statuses/ producer).

Parses the Nasdaq Trader trade-halt feed into the ``statuses/`` schema that
:func:`bowaka_v2_lab.data.halt_feed.read_halt_events` + the DQ halt gate
(``halt_data_unavailable_when_required``) consume, so ``intended_realism`` stops
failing closed at the DQ preflight once a ``statuses/`` partition exists.

DATA GATE (§5.2): Alpaca serves NO historical halt/LULD data, and the build sandbox
cannot resolve ``nasdaqtrader.com`` (DNS blocked — only the Alpaca data host is
reachable). So this is the PARSER + writer the operator runs WHERE Nasdaq resolves
(``scripts/backfill_halts.py``). The parser is built to the DOCUMENTED Nasdaq RSS
shape (``rss.aspx?feed=tradehalts`` — the ``ndaq:`` item fields) and MUST be
validated against a real pull before production use. Onset + LULD bands come from
this feed; halt RESUME can additionally be inferred from reopening auctions (P6),
which is a documented follow-up (see docs/p7_halt_gate_gap.md).

statuses/ schema (per ``halt_feed.HaltEvent``): ``symbol, ts_start, ts_end, reason``
(``ts_end`` = resumption trade time, or ``None`` while still halted).
"""
from __future__ import annotations

import datetime as _dt
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
        for tf in ("%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"):
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


__all__ = ["parse_nasdaq_halt_rss", "write_halt_statuses", "LULD_REASON_CODES"]
