"""IEX-vs-SIP feature divergence is exactly 0 on identical mock partitions.

Realism remediation 2 Phase 10 (audit §11 Phase 9 / §P1-010). The IEX-vs-SIP
feature divergence framework ships before either feed is reconciled. The
correctness contract is: when the IEX and SIP partitions for the same
(symbol, date) carry the same OHLCV (different only in the ``feed`` label),
the divergence must be exactly 0 across every supported feature.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bowaka_common.marketdata import MarketDataStore
from bowaka_common.marketdata.layout import (
    FEED_IEX,
    FEED_SIP,
    minute_bars_path,
    sip_minute_bars_path,
)
from bowaka_v2_lab.research.feature_divergence import (
    DEFAULT_DIVERGENCE_THRESHOLD,
    compute_feature_divergence,
    render_divergence_markdown,
    write_divergence_report,
)


def _synthetic_minute_frame(symbol: str, *, n_bars: int = 60) -> pd.DataFrame:
    """Build a synthetic minute frame for a single session, deterministic per symbol."""
    start = pd.Timestamp("2024-09-03 13:30:00", tz="UTC")  # 09:30 ET
    rng = np.random.default_rng(seed=hash(symbol) & 0xFFFF)
    base_price = 10.0 + rng.uniform(-1.0, 1.0)
    timestamps = pd.date_range(start, periods=n_bars, freq="1min", tz="UTC")
    closes = base_price + np.cumsum(rng.normal(0.0, 0.01, size=n_bars))
    opens = np.r_[closes[0], closes[:-1]]
    highs = np.maximum(opens, closes) + rng.uniform(0.01, 0.05, size=n_bars)
    lows = np.minimum(opens, closes) - rng.uniform(0.01, 0.05, size=n_bars)
    volumes = rng.integers(100, 10_000, size=n_bars)
    return pd.DataFrame({
        "symbol": symbol,
        "timestamp": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    })


def _write_iex_minute_partition(lake_root: Path, frame: pd.DataFrame) -> Path:
    """Write the frame to the IEX minute-partition path with feed='iex' column."""
    symbol = str(frame["symbol"].iloc[0])
    ts = pd.Timestamp(frame["timestamp"].iloc[0])
    target = minute_bars_path(lake_root, symbol, ts.year, ts.month, feed=FEED_IEX)
    target.parent.mkdir(parents=True, exist_ok=True)
    labelled = frame.copy()
    labelled["feed"] = FEED_IEX
    labelled.to_parquet(target, index=False)
    return target


def _write_sip_minute_partition(lake_root: Path, frame: pd.DataFrame) -> Path:
    """Write the SAME frame to the SIP minute-partition path with feed='sip' column."""
    symbol = str(frame["symbol"].iloc[0])
    ts = pd.Timestamp(frame["timestamp"].iloc[0])
    target = sip_minute_bars_path(lake_root, symbol, ts.year, ts.month)
    target.parent.mkdir(parents=True, exist_ok=True)
    labelled = frame.copy()
    labelled["feed"] = FEED_SIP
    labelled.to_parquet(target, index=False)
    return target


def test_identical_mock_partitions_yield_zero_divergence(tmp_path: Path) -> None:
    """Identical IEX and SIP partitions (differ only on feed label) -> divergence = 0."""
    lake = tmp_path / "lake"
    lake.mkdir()
    symbols = ["AAA", "BBB"]
    for sym in symbols:
        frame = _synthetic_minute_frame(sym)
        _write_iex_minute_partition(lake, frame)
        _write_sip_minute_partition(lake, frame)
    iex_store = MarketDataStore(lake)
    sip_store = MarketDataStore(lake)
    report = compute_feature_divergence(
        iex_store=iex_store, sip_store=sip_store,
        symbols=symbols,
        start=dt.date(2024, 9, 3), end=dt.date(2024, 9, 4),
        timeframe="1m",
    )
    assert report.per_symbol_rows, "divergence report must emit rows for present symbols"
    # Every per-(symbol, feature) divergence row reports exactly 0 across every
    # statistic. Use math.isclose-equivalent tolerance for floating-point safety.
    for row in report.per_symbol_rows:
        assert row.n_bars > 0, f"row {row.symbol}/{row.feature} probed 0 bars"
        assert row.max_abs_delta == pytest.approx(0.0, abs=1e-12), (
            f"max_abs_delta != 0 for {row.symbol}/{row.feature}: {row.max_abs_delta}"
        )
        assert row.mean_abs_delta == pytest.approx(0.0, abs=1e-12), (
            f"mean_abs_delta != 0 for {row.symbol}/{row.feature}: {row.mean_abs_delta}"
        )
        assert row.p95_abs_delta == pytest.approx(0.0, abs=1e-12)
        assert row.fraction_above_threshold == pytest.approx(0.0, abs=1e-12)
    # The aggregate maxima is also 0.
    assert report.max_divergence() == pytest.approx(0.0, abs=1e-12)
    # No symbols were skipped.
    assert not report.skipped, f"unexpected skipped rows: {report.skipped}"


def test_divergence_report_writes_markdown_and_json(tmp_path: Path) -> None:
    """The renderer writes a valid markdown + JSON pair the test can re-read."""
    lake = tmp_path / "lake"
    lake.mkdir()
    frame = _synthetic_minute_frame("XYZ")
    _write_iex_minute_partition(lake, frame)
    _write_sip_minute_partition(lake, frame)
    iex_store = MarketDataStore(lake)
    sip_store = MarketDataStore(lake)
    report = compute_feature_divergence(
        iex_store=iex_store, sip_store=sip_store,
        symbols=["XYZ"],
        start=dt.date(2024, 9, 3), end=dt.date(2024, 9, 4),
        timeframe="1m",
    )
    out_dir = tmp_path / "out"
    md_path, json_path = write_divergence_report(report, out_dir)
    assert md_path.is_file() and json_path.is_file()
    body = md_path.read_text(encoding="utf-8")
    assert "# IEX-vs-SIP feature divergence report" in body
    # The markdown rendering surfaces every feature's row.
    for feat in ("rvol_so_far", "range_expansion", "adv"):
        assert feat in body, f"divergence markdown missing row for {feat!r}"
    import json
    doc = json.loads(json_path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == 1
    assert doc["features"] == ["rvol_so_far", "range_expansion", "adv"]


def test_iex_frame_with_sip_label_raises_value_error(tmp_path: Path) -> None:
    """A frame whose feed-label contradicts its slot raises ValueError (skipped)."""
    lake = tmp_path / "lake"
    lake.mkdir()
    frame = _synthetic_minute_frame("BAD")
    # IEX slot, but labelled feed='sip' -> validation fails (recorded as skipped).
    bad_iex = frame.copy()
    bad_iex["feed"] = "sip"
    target_iex = minute_bars_path(lake, "BAD", 2024, 9, feed=FEED_IEX)
    target_iex.parent.mkdir(parents=True, exist_ok=True)
    bad_iex.to_parquet(target_iex, index=False)
    # Healthy SIP partition.
    _write_sip_minute_partition(lake, frame)
    iex_store = MarketDataStore(lake)
    sip_store = MarketDataStore(lake)
    report = compute_feature_divergence(
        iex_store=iex_store, sip_store=sip_store,
        symbols=["BAD"],
        start=dt.date(2024, 9, 3), end=dt.date(2024, 9, 4),
        timeframe="1m",
    )
    # The mismatched-label symbol is skipped, not crashed.
    assert any(s["symbol"] == "BAD" for s in report.skipped)
    assert not report.per_symbol_rows


def test_empty_universe_yields_empty_report(tmp_path: Path) -> None:
    """No symbols → empty report (no rows, no skipped entries, no exceptions)."""
    lake = tmp_path / "lake"
    lake.mkdir()
    iex_store = MarketDataStore(lake)
    sip_store = MarketDataStore(lake)
    report = compute_feature_divergence(
        iex_store=iex_store, sip_store=sip_store,
        symbols=[],
        start=dt.date(2024, 9, 3), end=dt.date(2024, 9, 4),
    )
    assert not report.per_symbol_rows
    assert not report.skipped
    assert report.max_divergence() == 0.0
