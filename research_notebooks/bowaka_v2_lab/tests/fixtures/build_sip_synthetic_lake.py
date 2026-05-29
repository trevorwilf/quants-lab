"""Build the synthetic-SIP fixture lake (audit 2026-05-29 §9 Phase 7 smoke).

Materialises a small SIP-shaped lake under ``tests/fixtures/sip_synthetic_lake/``
so the SIP cutover path (preflight + NBBO quote gate + halt-feed reader +
feed-divergence) can be exercised end-to-end against real-shaped data BEFORE the
operator has SIP feed access. Deterministic (seeded) so regenerating produces a
small, stable diff; the tests read the committed parquet directly.

SIP partition layout (per ``bowaka_common.marketdata.layout``)::

    bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted/symbol=<S>/part.parquet
    bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw/symbol=<S>/year=Y/month=M/part.parquet
    quotes/vendor=alpaca/feed=sip/symbol=<S>/year=Y/month=M/part.parquet
    statuses/vendor=alpaca/symbol=<S>/date=YYYY-MM-DD/part.parquet
    assets/vendor=alpaca/snapshot_id=<id>/assets.parquet
    _ingestion/manifest.json   (feed=sip, adjustment=split_adjusted)

The synthetic SIP data differs from the IEX fixture in audit-realistic ways:
wider true spread and higher RVOL (volume ramps over the window) on the same
symbols, so the IEX-vs-SIP divergence report shows non-zero divergence.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from bowaka_common.marketdata import layout

from tests.fixtures.universe_fixture import write_lake_asset_master

SYMBOLS = ("AAAA", "BBBB", "CCCC", "DDDD", "EEEE")
DAILY_START = _dt.date(2025, 6, 2)
DAILY_END = _dt.date(2025, 8, 29)
# Minute + quote coverage is the validation window only (Aug 2025) — the tests
# and the smoke config's fold land there; one month keeps the committed fixture
# small while still exercising every cutover gate.
MINUTE_MONTHS = ((2025, 8),)
QUOTE_MONTHS = ((2025, 8),)
#: One LULD halt, seeded for the halt-feed reader test.
HALT_SYMBOL = "AAAA"
HALT_DATE = _dt.date(2025, 8, 26)
DEFAULT_ROOT = Path(__file__).resolve().parent / "sip_synthetic_lake"


def _write(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _seed(symbol: str) -> int:
    return abs(hash(symbol)) % (2**31)


def write_daily(root: Path, symbol: str, *, feed: str = "sip", vol_scale: float = 1.0) -> None:
    days = [d.date() for d in pd.bdate_range(DAILY_START, DAILY_END)]
    rng = np.random.default_rng(_seed(symbol))
    base = 20.0 + rng.uniform(-3.0, 3.0)
    closes = base + np.cumsum(rng.normal(0.0, 0.15, size=len(days)))
    opens = np.r_[closes[0], closes[:-1]]
    # Volume ramps up over the window -> elevated RVOL near the validation tail.
    # SIP carries more volume than IEX (vol_scale<1 for IEX) -> RVOL divergence.
    vol = (vol_scale * 1_500_000 * (1.0 + 0.9 * np.linspace(0.0, 1.0, len(days)))).astype(float)
    _write(
        layout.daily_bars_path(root, symbol, feed=feed, adjustment="split_adjusted"),
        pd.DataFrame({
            "symbol": symbol,
            "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
            "open": np.round(opens, 4),
            "high": np.round(np.maximum(opens, closes) * 1.02, 4),
            "low": np.round(np.minimum(opens, closes) * 0.98, 4),
            "close": np.round(closes, 4),
            "volume": vol,
            "vwap": np.round((opens + closes) / 2.0, 4),
            "trades": (vol / 100).astype(int),
            "session_date": days,
        }),
    )


def write_minute_month(root: Path, symbol: str, year: int, month: int,
                       *, feed: str = "sip", vol_scale: float = 1.0) -> None:
    first = _dt.date(year, month, 1)
    days = [d.date() for d in pd.bdate_range(first, first + _dt.timedelta(days=31))
            if d.month == month]
    rng = np.random.default_rng(_seed(symbol) + year * 100 + month)
    rows = []
    for d in days:
        base = 20.0 + rng.uniform(-3.0, 3.0)
        for i in range(390):
            px = base + rng.normal(0.0, 0.03)
            ts = pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=13, minutes=30 + i)
            rows.append({
                "symbol": symbol, "timestamp": ts,
                "open": round(px, 4), "high": round(px * 1.004, 4),
                "low": round(px * 0.996, 4), "close": round(px, 4),
                "volume": float(rng.integers(2_000, 9_000)) * vol_scale,
            })
    # minute bars are RAW by lake convention (even for SIP).
    _write(
        layout.minute_bars_path(root, symbol, year, month, feed=feed, adjustment="raw"),
        pd.DataFrame(rows),
    )


def write_quotes_month(root: Path, symbol: str, year: int, month: int) -> None:
    first = _dt.date(year, month, 1)
    days = [d.date() for d in pd.bdate_range(first, first + _dt.timedelta(days=31))
            if d.month == month]
    rng = np.random.default_rng(_seed(symbol) + 7 * year + month)
    rows = []
    for d in days:
        mid0 = 20.0 + rng.uniform(-3.0, 3.0)
        # An NBBO snapshot EVERY minute so a quote exists within the
        # quote-coverage probe's 60s max-age at any scan timestamp.
        for i in range(390):
            mid = mid0 + rng.normal(0.0, 0.03)
            # Wider true SIP spread than the IEX synthetic fixture (~12 bps).
            half = mid * 0.0006
            ts = pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=13, minutes=30 + i)
            rows.append({
                "symbol": symbol, "timestamp": ts,
                "bid": round(mid - half, 4), "ask": round(mid + half, 4),
                "bid_size": float(rng.integers(200, 2_000)),
                "ask_size": float(rng.integers(200, 2_000)),
                "conditions": "R",
            })
    _write(
        layout.quotes_path(root, symbol, year, month, feed="sip"),
        pd.DataFrame(rows),
    )


def write_halt_status(root: Path) -> None:
    ts_start = pd.Timestamp(HALT_DATE, tz="UTC") + pd.Timedelta(hours=14, minutes=33)
    _write(
        layout.statuses_path(root, HALT_SYMBOL, HALT_DATE),
        pd.DataFrame({
            "symbol": [HALT_SYMBOL],
            "ts_start": [ts_start],
            "ts_end": [ts_start + pd.Timedelta(minutes=5)],
            "reason": ["LULD"],
        }),
    )


def write_manifest(root: Path) -> None:
    mpath = layout.ingestion_manifest_path(root)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps({
        "feed": "sip", "adjustment": "split_adjusted",
        "lake_root": str(root),
        "assets": len(SYMBOLS),
        "daily": {"symbols_written": len(SYMBOLS)},
        "symbols_failed": 0,
        "dataset_hashes": {"lake": "sha256:synthetic_sip"},
    }), encoding="utf-8")
    run = layout.ingestion_run_path(root, "ingest_synthetic_sip")
    run.parent.mkdir(parents=True, exist_ok=True)
    run.write_text(json.dumps({
        "run_id": "ingest_synthetic_sip", "feed": "sip",
        "adjustment": "split_adjusted", "symbols": list(SYMBOLS),
        "status": "complete",
    }), encoding="utf-8")


def build(root: Path | str = DEFAULT_ROOT, symbols: Sequence[str] = SYMBOLS) -> Path:
    root = Path(root)
    for symbol in symbols:
        write_daily(root, symbol, feed="sip", vol_scale=1.0)
        # An IEX counterpart at lower volume so the IEX-vs-SIP divergence report
        # has non-zero RVOL divergence to surface.
        write_daily(root, symbol, feed="iex", vol_scale=0.6)
        for (year, month) in MINUTE_MONTHS:
            write_minute_month(root, symbol, year, month, feed="sip", vol_scale=1.0)
            write_minute_month(root, symbol, year, month, feed="iex", vol_scale=0.6)
        for (year, month) in QUOTE_MONTHS:
            write_quotes_month(root, symbol, year, month)
    write_halt_status(root)
    write_lake_asset_master(root, list(symbols), snapshot_id="synthetic_sip_2025")
    write_manifest(root)
    return root


if __name__ == "__main__":
    out = build()
    print(f"synthetic SIP lake -> {out}")
