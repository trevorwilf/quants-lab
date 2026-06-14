"""P7 §3.4/§5.3 — backfill corporate actions into the lake (``corporate_actions/`` partition).

Multithreaded raw-REST downloader for Alpaca ``GET /v1beta1/corporate-actions``. The
``symbols`` param is OPTIONAL, so we fetch the WHOLE CA stream by date window (REQUIRED
for survivorship: a renamed / merged / removed symbol is no longer in the current
universe, so a per-universe-symbol fetch would miss exactly the events that prove a
delisting/rename happened). Date windows are fetched in parallel (each paginated), all
events are normalised (bowaka_common.marketdata.corporate_actions), then grouped by the
affected symbol and written one file per symbol via ``layout.corporate_actions_path``.

Run (in-container)::

  MARKET_DATA_ROOT=/opt/market_data_cache \
  PYTHONPATH=src:../bowaka_common/src /opt/conda/envs/quants-lab/bin/python \
    scripts/backfill_corporate_actions.py --start 2020-01-01 --end 2026-06-30 --workers 6

Creds: ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY from env or /quants-lab/.env
(auto-``.strip()``-ed — the .env has CRLF line endings).
"""
from __future__ import annotations

import argparse
import json
import os
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout as _layout
from bowaka_common.marketdata.corporate_actions import parse_corporate_actions_response
from bowaka_common.marketdata.store import resolve_market_data_root

_BASE = "https://data.alpaca.markets/v1beta1/corporate-actions"
#: All CA types relevant to survivorship + adjustment (explicit so a server default
#: never silently narrows the set).
_TYPES = (
    "forward_split,reverse_split,unit_split,cash_dividend,stock_dividend,spin_off,"
    "cash_merger,stock_merger,stock_and_cash_merger,redemption,name_change,"
    "worthless_removal,rights_distribution"
)


def _clean_cred(v) -> str:
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


def _year_chunks(start: str, end: str) -> list[tuple[str, str]]:
    """Split ``[start, end]`` into per-calendar-year [s, e] windows (parallel units)."""
    s, e = pd.Timestamp(start).date(), pd.Timestamp(end).date()
    out: list[tuple[str, str]] = []
    y = s.year
    while y <= e.year:
        ws = max(s, pd.Timestamp(f"{y}-01-01").date())
        we = min(e, pd.Timestamp(f"{y}-12-31").date())
        out.append((ws.isoformat(), we.isoformat()))
        y += 1
    return out


def _fetch_window(start: str, end: str, *, key: str, sec: str, limiter: _RateLimiter) -> list[dict]:
    rows: list[dict] = []
    page_token = None
    while True:
        params = {"types": _TYPES, "start": start, "end": end, "limit": 1000}
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
        rows.extend(parse_corporate_actions_response(data or {}))
        page_token = (data or {}).get("next_page_token")
        if not page_token:
            break
    return rows


def _write_symbol(root: Path, sym: str, rows: list[dict]) -> int:
    """Write/merge one symbol's normalised CA rows (dedupe on the Alpaca event ``id``)."""
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    path = _layout.corporate_actions_path(root, sym, vendor="alpaca")
    if path.is_file():
        try:
            df = pd.concat([pd.read_parquet(path), df], ignore_index=True)
        except Exception:  # noqa: BLE001 — corrupt prior partition -> overwrite
            pass
    subset = ["id"] if "id" in df.columns and df["id"].notna().any() else None
    if subset:
        df = df.drop_duplicates(subset=subset, keep="last")
    sort_col = "effective_date" if "effective_date" in df.columns else None
    if sort_col:
        df = df.sort_values(sort_col, kind="stable")
    df = df.reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="P7 corporate-actions backfill (multithreaded REST, global stream).")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--per-min", type=int, default=180, help="max REST requests/minute (shared)")
    ns = ap.parse_args(argv)

    key, sec = _creds()
    root = resolve_market_data_root(None, create=False)
    limiter = _RateLimiter(ns.per_min)
    chunks = _year_chunks(ns.start, ns.end)
    print(f"corporate-actions backfill: {ns.start}..{ns.end} in {len(chunks)} year-window(s), "
          f"workers={ns.workers}", flush=True)

    all_rows: list[dict] = []
    errors = 0
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=ns.workers) as ex:
        futs = {ex.submit(_fetch_window, s, e, key=key, sec=sec, limiter=limiter): (s, e)
                for (s, e) in chunks}
        for fut in as_completed(futs):
            win = futs[fut]
            try:
                rows = fut.result()
            except Exception as exc:  # noqa: BLE001
                errors += 1
                print(f"  window ERROR {win}: {repr(exc)[:120]}", flush=True)
                continue
            with lock:
                all_rows.extend(rows)
                print(f"  window {win} -> {len(rows)} events (total {len(all_rows)})", flush=True)

    # Group the global stream by the affected symbol; write one file per symbol.
    by_symbol: dict[str, list[dict]] = {}
    for r in all_rows:
        sym = r.get("symbol")
        if sym:
            by_symbol.setdefault(str(sym), []).append(r)
    files = 0
    for sym, srows in by_symbol.items():
        files += _write_symbol(root, sym, srows)
    print(f"DONE corporate-actions: events={len(all_rows)} symbols={len(by_symbol)} "
          f"files={files} errors={errors}", flush=True)
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
