"""§5.1 — backfill official open/close auctions into the lake (``auctions/`` partition).

Multithreaded raw-REST downloader for Alpaca ``GET /v2/stocks/auctions`` (the SDK
lacks the request class). Reads the universe from the existing daily-bar partition,
extracts the official open/close per session (bowaka_common.marketdata.auctions),
and writes per-symbol/month parquet via ``layout.auctions_path``. Resume-aware
(skip symbols already covering the window's last month) and prints progress.

Run (in-container)::

  MARKET_DATA_ROOT=/opt/market_data_cache \
  PYTHONPATH=src:../bowaka_common/src /opt/conda/envs/quants-lab/bin/python \
    scripts/backfill_auctions.py --feed sip --start 2025-08-01 --end 2026-06-30 \
      --workers 8 --batch 100

Creds: ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY from env or /quants-lab/.env
(auto-``.strip()``-ed — the .env has CRLF line endings).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout as _layout
from bowaka_common.marketdata.auctions import parse_auctions_response
from bowaka_common.marketdata.store import resolve_market_data_root

_BASE = "https://data.alpaca.markets/v2/stocks/auctions"


def _clean_cred(v) -> str:
    # .env values are QUOTED ("PK...") and CRLF-terminated -> strip quotes + ws.
    return (v or "").strip().strip('"').strip("'").strip()


def _creds() -> tuple[str, str]:
    key = _clean_cred(os.environ.get("ALPACA_API_KEY_ID"))
    sec = _clean_cred(os.environ.get("ALPACA_API_SECRET_KEY"))
    if not key or not sec:
        env = Path("/quants-lab/.env")
        if env.is_file():
            for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("ALPACA_API_KEY_ID=") and not key:
                    key = _clean_cred(line.split("=", 1)[1])
                elif line.startswith("ALPACA_API_SECRET_KEY=") and not sec:
                    sec = _clean_cred(line.split("=", 1)[1])
    if not key or not sec:
        raise SystemExit("ALPACA creds missing (ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY)")
    return key, sec


class _RateLimiter:
    """Token bucket: <= ``per_min`` acquisitions per rolling 60s (thread-safe)."""

    def __init__(self, per_min: int) -> None:
        self._per_min = max(1, int(per_min))
        self._lock = threading.Lock()
        self._times: list[float] = []

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                self._times = [t for t in self._times if now - t < 60.0]
                if len(self._times) < self._per_min:
                    self._times.append(now)
                    return
                wait = 60.0 - (now - self._times[0])
            time.sleep(max(0.05, wait))


def _universe_symbols(root: Path, feed: str) -> list[str]:
    base = _layout.bars_timeframe_root(root, "1d", feed=feed, adjustment="split_adjusted")
    return sorted(
        p.name.split("=", 1)[1] for p in base.glob("symbol=*") if p.is_dir()
    )


def _already_done(root: Path, sym: str, feed: str, last_year: int, last_month: int) -> bool:
    return _layout.auctions_path(root, sym, last_year, last_month, feed=feed).is_file()


def _fetch_batch(symbols, *, feed, start, end, key, sec, limiter) -> dict:
    out: dict[str, list[dict]] = {s: [] for s in symbols}
    page_token = None
    while True:
        params = {"symbols": ",".join(symbols), "start": start, "end": end,
                  "feed": feed, "limit": 10000}
        if page_token:
            params["page_token"] = page_token
        url = _BASE + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            "APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec, "accept": "application/json"})
        data = None
        for attempt in range(5):
            limiter.acquire()
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    data = json.loads(resp.read())
                break
            except Exception:  # noqa: BLE001 — transient HTTP / 429; backoff + retry
                if attempt == 4:
                    raise
                time.sleep(1.5 * (attempt + 1))
        for sym in symbols:
            out[sym].extend(parse_auctions_response(data or {}, sym))
        page_token = (data or {}).get("next_page_token")
        if not page_token:
            break
    return out


def _write_symbol(root: Path, sym: str, rows: list[dict], feed: str) -> int:
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])
    if df.empty:
        return 0
    df["_y"] = df["timestamp"].dt.year
    df["_m"] = df["timestamp"].dt.month
    written = 0
    for (y, m), g in df.groupby(["_y", "_m"]):
        path = _layout.auctions_path(root, sym, int(y), int(m), feed=feed)
        g = g.drop(columns=["_y", "_m"])
        if path.is_file():
            try:
                g = pd.concat([pd.read_parquet(path), g], ignore_index=True)
            except Exception:  # noqa: BLE001
                pass
        g = (g.drop_duplicates(subset=["session_date"], keep="last")
             .sort_values("timestamp").reset_index(drop=True))
        path.parent.mkdir(parents=True, exist_ok=True)
        g.to_parquet(path, index=False)
        written += 1
    return written


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="§5.1 official-auction backfill (multithreaded REST).")
    ap.add_argument("--feed", default="sip")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--batch", type=int, default=100, help="symbols per REST call")
    ap.add_argument("--per-min", type=int, default=180, help="max REST requests/minute (shared)")
    ap.add_argument("--symbols", default=None, help="comma list (default: full daily-bar universe)")
    ap.add_argument("--force", action="store_true", help="re-fetch symbols already present")
    ns = ap.parse_args(argv)

    key, sec = _creds()
    root = resolve_market_data_root(None, create=False)
    limiter = _RateLimiter(ns.per_min)

    if ns.symbols:
        symbols = [s.strip().upper() for s in ns.symbols.split(",") if s.strip()]
    else:
        symbols = _universe_symbols(root, ns.feed)
    last = pd.Timestamp(ns.end)
    if not ns.force:
        symbols = [s for s in symbols if not _already_done(root, s, ns.feed, last.year, last.month)]
    print(f"auctions backfill: {len(symbols)} symbols, {ns.start}..{ns.end}, feed={ns.feed}, "
          f"workers={ns.workers}, batch={ns.batch}", flush=True)
    if not symbols:
        print("nothing to do (all symbols already present; use --force to refetch)", flush=True)
        return 0

    batches = [symbols[i:i + ns.batch] for i in range(0, len(symbols), ns.batch)]
    done = {"sym": 0, "rows": 0, "files": 0, "batches": 0, "errors": 0}
    lock = threading.Lock()

    def _do(batch):
        res = _fetch_batch(batch, feed=ns.feed, start=ns.start, end=ns.end,
                           key=key, sec=sec, limiter=limiter)
        files = rows = 0
        for sym, srows in res.items():
            rows += len(srows)
            files += _write_symbol(root, sym, srows, ns.feed)
        return len(batch), rows, files

    with ThreadPoolExecutor(max_workers=ns.workers) as ex:
        futs = {ex.submit(_do, b): b for b in batches}
        for fut in as_completed(futs):
            try:
                n_sym, rows, files = fut.result()
            except Exception as e:  # noqa: BLE001
                with lock:
                    done["errors"] += 1
                print(f"  batch ERROR ({futs[fut][:3]}...): {repr(e)[:120]}", flush=True)
                continue
            with lock:
                done["sym"] += n_sym; done["rows"] += rows
                done["files"] += files; done["batches"] += 1
                print(f"  [{done['batches']}/{len(batches)}] symbols={done['sym']}/{len(symbols)} "
                      f"rows={done['rows']} files={done['files']} errors={done['errors']}", flush=True)

    print(f"DONE auctions: symbols={done['sym']} rows={done['rows']} files={done['files']} "
          f"errors={done['errors']}", flush=True)
    return 0 if done["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
