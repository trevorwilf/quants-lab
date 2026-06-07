#!/usr/bin/env python
"""Configurable, incremental backfill of the shared market-data lake.

Reads ``config/marketdata_backfill.yml``, fetches only what is missing from the
canonical lake, and is safe to run nightly from cron — re-runs are incremental
and ``end_date: auto`` advances the window automatically. Switching ``feed``
(``iex`` <-> ``sip``) writes a separate partition with no special handling.

    python scripts/backfill_market_data.py
    python scripts/backfill_market_data.py --feed sip
    python scripts/backfill_market_data.py --start 2020-01-01 --end 2026-05-01
    python scripts/backfill_market_data.py --config config/marketdata_backfill.yml

Requires ``ALPACA_API_KEY_ID`` / ``ALPACA_API_SECRET_KEY`` in the environment.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _bootstrap_bowaka_common() -> None:
    """Put ``bowaka_common`` on ``sys.path`` regardless of how this is launched."""
    here = Path(__file__).resolve()
    for cand in [here.parent, *here.parents]:
        src = cand / "research_notebooks" / "bowaka_common" / "src"
        if (src / "bowaka_common" / "__init__.py").is_file():
            if str(src) not in sys.path:
                sys.path.insert(0, str(src))
            return
    raise RuntimeError("could not locate research_notebooks/bowaka_common/src")


_bootstrap_bowaka_common()

from bowaka_common.marketdata.runner import (  # noqa: E402
    load_backfill_config,
    run_configured_backfill,
)

_DEFAULT_CONFIG = "config/marketdata_backfill.yml"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Incremental backfill of the shared market-data lake."
    )
    ap.add_argument("--config", default=_DEFAULT_CONFIG, help="backfill YAML config")
    ap.add_argument("--feed", choices=["iex", "sip"], help="override the config feed")
    ap.add_argument("--start", help="override start_date (YYYY-MM-DD)")
    ap.add_argument("--end", help="override end_date (YYYY-MM-DD or 'auto')")
    ap.add_argument("--lake-root", help="override the lake root")
    ap.add_argument(
        "--quotes", action="store_true",
        help="enable the SIP NBBO quote stage (overrides config quotes.enabled). "
             "Required for full intended_realism; use with --feed sip. Heavy on a "
             "first run (the NBBO tick stream is fetched then sampled to one "
             "prevailing quote per minute) — scope --start/--end; it is incremental.",
    )
    ap.add_argument(
        "--quotes-only", action="store_true",
        help="fetch ONLY quotes (implies --quotes): skip the daily + minute bar "
             "fetch and the shared audit/manifest/ingestion-run writes. Daily + "
             "minute bars must already be in the lake. Lets many processes backfill "
             "quotes for disjoint --start/--end month ranges in parallel without "
             "racing on per-symbol daily files or the single manifest.json. Run a "
             "normal (non --quotes-only) backfill once afterward to refresh the "
             "manifest/ingestion record.",
    )
    ap.add_argument(
        "--rpm", type=int,
        help="override rate_limit_rpm = your Alpaca data-API per-minute request "
             "limit (read it from any data response's X-RateLimit-Limit header; "
             "10000 on the SIP / Algo-Trader-Plus tier). The config's 180 is "
             "conservative — raise it for the heavy quote backfill. If this key is "
             "shared with live trading, leave headroom or run off-hours.",
    )
    args = ap.parse_args(argv)

    config = load_backfill_config(args.config)
    if args.feed:
        config["feed"] = args.feed
    if args.start:
        config["start_date"] = args.start
    if args.end:
        config["end_date"] = args.end
    if args.quotes or args.quotes_only:
        config.setdefault("quotes", {})["enabled"] = True
    if args.quotes_only:
        config["quotes_only"] = True
    if args.rpm:
        config["rate_limit_rpm"] = args.rpm

    result = run_configured_backfill(config, lake_root=args.lake_root)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
