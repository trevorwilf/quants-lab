"""§3.5 — backfill all-adjusted (split+dividend) DAILY bars (adjustment=all).

Reuses ``make_alpaca_bars_fetcher`` (SDK) to fetch daily bars with
``adjustment=all`` for the universe and writes
``bars/.../timeframe=1d/adjustment=all/symbol=*/part.parquet`` — the partition the
§3.5 dividend-adjustment cutover (``require_adjusted_daily_bars -> "all"``) reads.
Multithreaded over symbol batches; small (~250 MB, daily cadence). Reuses the
creds / universe / rate-limiter helpers from backfill_auctions.

Run (in-container)::

  MARKET_DATA_ROOT=/opt/market_data_cache PYTHONPATH=src:../bowaka_common/src \
    /opt/conda/envs/quants-lab/bin/python scripts/backfill_daily_all.py \
      --feed sip --start 2025-07-01 --end 2026-06-30 --workers 6 --batch 100
"""
from __future__ import annotations

import argparse
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout as _layout
from bowaka_common.marketdata.backfill import BackfillConfig, make_alpaca_bars_fetcher
from bowaka_common.marketdata.store import resolve_market_data_root

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backfill_auctions import _RateLimiter, _creds, _universe_symbols  # noqa: E402


def _write_daily(root: Path, sym: str, rows: list[dict], feed: str) -> int:
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    if "timestamp" not in df.columns or df.empty:
        return 0
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])
    if df.empty:
        return 0
    path = _layout.daily_bars_path(root, sym, feed=feed, adjustment="all")
    if path.is_file():
        try:
            df = pd.concat([pd.read_parquet(path), df], ignore_index=True)
        except Exception:  # noqa: BLE001
            pass
    df = (df.drop_duplicates(subset=["timestamp"], keep="last")
          .sort_values("timestamp").reset_index(drop=True))
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="§3.5 all-adjusted daily-bar backfill (multithreaded).")
    ap.add_argument("--feed", default="sip")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--batch", type=int, default=100)
    ap.add_argument("--per-min", type=int, default=180)
    ap.add_argument("--symbols", default=None)
    ap.add_argument("--force", action="store_true")
    ns = ap.parse_args(argv)

    key, sec = _creds()
    root = resolve_market_data_root(None, create=False)
    log = logging.getLogger("daily_all")
    logging.basicConfig(level=logging.ERROR)
    limiter = _RateLimiter(ns.per_min)
    cfg = BackfillConfig(
        api_key=key, api_secret=sec, paper=True, feed=ns.feed,
        start_date=pd.Timestamp(ns.start).date(), end_date=pd.Timestamp(ns.end).date(),
        lake_root=root, adjustment="all", rate_limit_rpm=ns.per_min,
    )
    fetcher = make_alpaca_bars_fetcher(cfg, limiter, log)
    start_dt = datetime.combine(cfg.start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(cfg.end_date, datetime.min.time(), tzinfo=timezone.utc)

    if ns.symbols:
        symbols = [s.strip().upper() for s in ns.symbols.split(",") if s.strip()]
    else:
        symbols = _universe_symbols(root, ns.feed)
    if not ns.force:
        symbols = [s for s in symbols
                   if not _layout.daily_bars_path(root, s, feed=ns.feed, adjustment="all").is_file()]
    print(f"daily-all backfill: {len(symbols)} symbols, {ns.start}..{ns.end}, feed={ns.feed}, "
          f"workers={ns.workers}, batch={ns.batch}", flush=True)
    if not symbols:
        print("nothing to do (all present; --force to refetch)", flush=True)
        return 0

    batches = [symbols[i:i + ns.batch] for i in range(0, len(symbols), ns.batch)]
    done = {"sym": 0, "files": 0, "batches": 0, "errors": 0}
    lock = threading.Lock()

    def _do(batch):
        res = fetcher(batch, "1d", start_dt, end_dt)
        files = sum(_write_daily(root, sym, rows, ns.feed) for sym, rows in res.items())
        return len(batch), files

    with ThreadPoolExecutor(max_workers=ns.workers) as ex:
        futs = {ex.submit(_do, b): b for b in batches}
        for fut in as_completed(futs):
            try:
                n, files = fut.result()
            except Exception as e:  # noqa: BLE001
                with lock:
                    done["errors"] += 1
                print(f"  batch ERROR ({futs[fut][:3]}...): {repr(e)[:120]}", flush=True)
                continue
            with lock:
                done["sym"] += n; done["files"] += files; done["batches"] += 1
                print(f"  [{done['batches']}/{len(batches)}] symbols={done['sym']}/{len(symbols)} "
                      f"files={done['files']} errors={done['errors']}", flush=True)

    print(f"DONE daily-all: symbols={done['sym']} files={done['files']} errors={done['errors']}", flush=True)
    return 0 if done["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
