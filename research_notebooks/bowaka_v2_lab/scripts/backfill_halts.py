"""P7 §5.2 — ingest Nasdaq Trader trade halts into the lake (``statuses/`` partition).

Produces the ``statuses/`` partition the DQ halt gate (``halt_data_unavailable_when_
required``) + ``halt_feed.read_halt_events`` consume, so ``intended_realism`` stops
failing closed at the DQ preflight.

``nasdaqtrader.com`` is reachable again (the earlier sandbox DNS block is gone), so the
historical source is the TradingHaltSearch JSON-RPC (Jayrock at ``RPCHandler.axd``),
wired here via :class:`~bowaka_v2_lab.data.halt_ingest.NasdaqHaltRpcClient`:

* ``--start/--end`` — per-day historical backfill (``GetHaltsByDate`` ``YYYYMMDD``,
  reaches back years). This is the IR halt gate's real source for past folds.
* ``--recent`` — the trailing ~1 year (~13k halts) in one ``SearchTradeHaltsNEW`` call.
* ``--url`` — the live RSS, a snapshot of CURRENTLY-OPEN halts only (not historical).
* ``--file`` / ``--dir`` — parse local saved RSS files (offline archive).

Run::

  # historical per-day backfill (the IR halt gate source) over a date range:
  MARKET_DATA_ROOT=/opt/market_data_cache PYTHONPATH=src:../bowaka_common/src \
    python scripts/backfill_halts.py --start 2024-01-01 --end 2024-12-31
  # trailing ~1 year in a single call:
  python scripts/backfill_halts.py --recent
  # live CURRENT-halt RSS snapshot:
  python scripts/backfill_halts.py --url
"""
from __future__ import annotations

import argparse
import datetime as dt
import urllib.request
from pathlib import Path

from bowaka_common.marketdata.store import resolve_market_data_root
from bowaka_v2_lab.data.halt_ingest import (
    NasdaqHaltRpcClient,
    parse_nasdaq_halt_rss,
    parse_nasdaq_halt_table,
    write_halt_statuses,
)

_LIVE_RSS = "http://www.nasdaqtrader.com/rss.aspx?feed=tradehalts"


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", "replace")


def _dedup(rows: list[dict]) -> list[dict]:
    """A halt can surface under both its halt-day and its resumption-day query; key on
    ``(symbol, ts_start, reason)`` so the union across days has no duplicates."""
    seen: set = set()
    out: list[dict] = []
    for r in rows:
        key = (r["symbol"], r["ts_start"], r["reason"])
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def _backfill_range(start: dt.date, end: dt.date) -> list[dict]:
    client = NasdaqHaltRpcClient()
    rows: list[dict] = []
    day = start
    while day <= end:
        if day.weekday() < 5:  # weekdays only — markets are closed weekends
            day_rows = parse_nasdaq_halt_table(client.halts_for_day(day))
            rows.extend(day_rows)
            print(f"  {day.isoformat()}: {len(day_rows)} halts", flush=True)
        day += dt.timedelta(days=1)
    return _dedup(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="P7 §5.2 Nasdaq trade-halt ingester.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--start", help="YYYY-MM-DD: per-day JSON-RPC historical backfill start")
    src.add_argument("--recent", action="store_true",
                     help="trailing ~1yr of halts via JSON-RPC (one SearchTradeHaltsNEW call)")
    src.add_argument("--url", action="store_true",
                     help="fetch the live Nasdaq CURRENT-halt RSS snapshot")
    src.add_argument("--file", help="parse one local Nasdaq RSS file")
    src.add_argument("--dir", help="parse every *.xml/*.rss in a local Nasdaq archive dir")
    ap.add_argument("--end", help="YYYY-MM-DD: per-day backfill end (default: --start)")
    ap.add_argument("--vendor", default="alpaca", help="lake vendor partition (default alpaca)")
    ns = ap.parse_args(argv)

    root = resolve_market_data_root(None, create=False)
    rows: list[dict] = []
    if ns.start:
        start = dt.date.fromisoformat(ns.start)
        end = dt.date.fromisoformat(ns.end) if ns.end else start
        print(f"backfill halts {start} .. {end} via JSON-RPC GetHaltsByDate", flush=True)
        rows = _backfill_range(start, end)
    elif ns.recent:
        print("fetch trailing ~1yr halts via SearchTradeHaltsNEW", flush=True)
        rows = _dedup(parse_nasdaq_halt_table(NasdaqHaltRpcClient().recent_halts()))
    elif ns.url:
        rows = parse_nasdaq_halt_rss(_fetch(_LIVE_RSS))
    elif ns.file:
        rows = parse_nasdaq_halt_rss(Path(ns.file).read_text(encoding="utf-8", errors="replace"))
    else:
        files = sorted(p for ext in ("*.xml", "*.rss") for p in Path(ns.dir).glob(ext))
        if not files:
            print(f"no *.xml/*.rss files under {ns.dir}", flush=True)
            return 1
        for p in files:
            rows.extend(parse_nasdaq_halt_rss(p.read_text(encoding="utf-8", errors="replace")))

    files_written = write_halt_statuses(root, rows, vendor=ns.vendor)
    print(f"DONE halts: parsed={len(rows)} halt events -> {files_written} statuses/ files "
          f"under {root}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
