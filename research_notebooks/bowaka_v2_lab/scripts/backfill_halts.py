"""P7 §5.2 — ingest Nasdaq Trader trade halts into the lake (``statuses/`` partition).

Produces the ``statuses/`` partition the DQ halt gate (``halt_data_unavailable_when_
required``) + ``halt_feed.read_halt_events`` consume, so ``intended_realism`` stops
failing closed at the DQ preflight.

DATA GATE: the build sandbox cannot resolve ``nasdaqtrader.com`` (only the Alpaca data
host is reachable), so RUN THIS WHERE NASDAQ RESOLVES (operator host / container). The
live RSS feed is CURRENT halts only; historical halts for past folds must come from a
local Nasdaq archive (``--dir`` of saved RSS/CSV files). See docs/p7_halt_gate_gap.md.

Run::

  # live (current) halts:
  PYTHONPATH=src:../bowaka_common/src python scripts/backfill_halts.py --url
  # historical archive (operator-provided Nasdaq RSS files):
  MARKET_DATA_ROOT=/opt/market_data_cache PYTHONPATH=src:../bowaka_common/src \
    python scripts/backfill_halts.py --dir /path/to/nasdaq_halt_rss_archive
"""
from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

from bowaka_common.marketdata.store import resolve_market_data_root
from bowaka_v2_lab.data.halt_ingest import parse_nasdaq_halt_rss, write_halt_statuses

_LIVE_RSS = "http://www.nasdaqtrader.com/rss.aspx?feed=tradehalts"


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", "replace")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="P7 §5.2 Nasdaq trade-halt ingester.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", action="store_true", help="fetch the live Nasdaq trade-halt RSS")
    src.add_argument("--file", help="parse one local Nasdaq RSS file")
    src.add_argument("--dir", help="parse every *.xml/*.rss in a local Nasdaq archive dir")
    ap.add_argument("--vendor", default="alpaca", help="lake vendor partition (default alpaca)")
    ns = ap.parse_args(argv)

    root = resolve_market_data_root(None, create=False)
    texts: list[str] = []
    if ns.url:
        texts.append(_fetch(_LIVE_RSS))
    elif ns.file:
        texts.append(Path(ns.file).read_text(encoding="utf-8", errors="replace"))
    else:
        files = sorted(p for ext in ("*.xml", "*.rss") for p in Path(ns.dir).glob(ext))
        if not files:
            print(f"no *.xml/*.rss files under {ns.dir}", flush=True)
            return 1
        texts = [p.read_text(encoding="utf-8", errors="replace") for p in files]

    rows = []
    for t in texts:
        rows.extend(parse_nasdaq_halt_rss(t))
    files_written = write_halt_statuses(root, rows, vendor=ns.vendor)
    print(f"DONE halts: parsed={len(rows)} halt events -> {files_written} statuses/ files "
          f"under {root}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
