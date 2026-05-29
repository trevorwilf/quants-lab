"""Phase 5 (audit 2026-05-29 §9 Phase 7) — IEX-vs-SIP feed divergence status.

- No SIP partition -> status SIP_DATA_UNAVAILABLE, 0 rows.
- A synthetic SIP partition that DIFFERS from IEX -> status ok with divergence.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from bowaka_common.marketdata import MarketDataStore
from bowaka_common.marketdata.layout import FEED_IEX, minute_bars_path, sip_minute_bars_path
from bowaka_v2_lab.reports.feed_divergence import feed_divergence_report


def _frame(symbol: str, volume_scale: float = 1.0) -> pd.DataFrame:
    start = pd.Timestamp("2024-09-03 13:30:00", tz="UTC")
    n = 60
    ts = pd.date_range(start, periods=n, freq="1min", tz="UTC")
    rng = np.random.default_rng(7)
    closes = 10.0 + np.cumsum(rng.normal(0.0, 0.01, size=n))
    opens = np.r_[closes[0], closes[:-1]]
    return pd.DataFrame({
        "symbol": symbol, "timestamp": ts, "open": opens,
        "high": np.maximum(opens, closes) + 0.02,
        "low": np.minimum(opens, closes) - 0.02,
        "close": closes,
        "volume": (rng.integers(1_000, 5_000, size=n) * volume_scale).astype(float),
    })


def test_sip_unavailable_status(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    lake.mkdir()
    frame = _frame("AAA")
    p = minute_bars_path(lake, "AAA", 2024, 9, feed=FEED_IEX)
    p.parent.mkdir(parents=True, exist_ok=True)
    f = frame.copy(); f["feed"] = FEED_IEX
    f.to_parquet(p, index=False)
    store = MarketDataStore(lake)
    rep = feed_divergence_report(
        iex_store=store, sip_store=store, symbols=["AAA"],
        start=dt.date(2024, 9, 3), end=dt.date(2024, 9, 4),
    )
    assert rep["status"] == "SIP_DATA_UNAVAILABLE"
    assert rep["n_rows"] == 0


def test_synthetic_sip_yields_divergence(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    lake.mkdir()
    iex = _frame("AAA", volume_scale=1.0)
    sip = _frame("AAA", volume_scale=0.6)   # SIP volume differs -> RVOL/ADV diverge
    pi = minute_bars_path(lake, "AAA", 2024, 9, feed=FEED_IEX)
    pi.parent.mkdir(parents=True, exist_ok=True)
    fi = iex.copy(); fi["feed"] = FEED_IEX
    fi.to_parquet(pi, index=False)
    ps = sip_minute_bars_path(lake, "AAA", 2024, 9)
    ps.parent.mkdir(parents=True, exist_ok=True)
    fs = sip.copy(); fs["feed"] = "sip"
    fs.to_parquet(ps, index=False)
    store = MarketDataStore(lake)
    rep = feed_divergence_report(
        iex_store=store, sip_store=store, symbols=["AAA"],
        start=dt.date(2024, 9, 3), end=dt.date(2024, 9, 4),
    )
    assert rep["status"] == "ok"
    assert rep["n_rows"] >= 1
    assert rep["max_divergence"] > 0.0
