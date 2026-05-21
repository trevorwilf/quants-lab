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
    args = ap.parse_args(argv)

    config = load_backfill_config(args.config)
    if args.feed:
        config["feed"] = args.feed
    if args.start:
        config["start_date"] = args.start
    if args.end:
        config["end_date"] = args.end

    result = run_configured_backfill(config, lake_root=args.lake_root)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
