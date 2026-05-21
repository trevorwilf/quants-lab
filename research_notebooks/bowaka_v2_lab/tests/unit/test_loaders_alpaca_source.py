"""loaders.py source="alpaca" reads the shared market-data lake."""
from __future__ import annotations

import inspect

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.data import loaders
from bowaka_v2_lab.data.loaders import (
    corporate_actions_for,
    daily_bars_for,
    minute_bars_for,
    quotes_for,
)


def _write(path, df):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _bars(symbol, timestamps):
    n = len(timestamps)
    return pd.DataFrame(
        {
            "symbol": [symbol] * n,
            "timestamp": timestamps,
            "open": [1.0] * n,
            "high": [2.0] * n,
            "low": [0.5] * n,
            "close": [1.5] * n,
            "volume": [1000] * n,
        }
    )


def test_daily_bars_for_alpaca_source(tmp_path):
    lake = tmp_path / "lake"
    ts = pd.to_datetime(["2026-05-01", "2026-05-02", "2026-05-03"], utc=True) + pd.Timedelta(hours=20)
    _write(layout.daily_bars_path(lake, "AAA"), _bars("AAA", ts))
    out = daily_bars_for(
        "AAA", "2026-05-01", "2026-05-02",
        paths=BowakaV2Paths.default(tmp_path), source="alpaca", shared_root=lake,
    )
    assert len(out) == 2


def test_minute_bars_for_alpaca_source(tmp_path):
    lake = tmp_path / "lake"
    ts = pd.to_datetime(["2026-05-04 14:00", "2026-05-04 14:01", "2026-05-04 14:02"], utc=True)
    _write(layout.minute_bars_path(lake, "AAA", 2026, 5), _bars("AAA", ts))
    out = minute_bars_for(
        "AAA", pd.Timestamp("2026-05-04 14:01", tz="UTC"),
        paths=BowakaV2Paths.default(tmp_path), source="alpaca", shared_root=lake,
    )
    # bars at-or-before the cutoff only
    assert len(out) == 2
    assert str(out["timestamp"].dt.tz) == "UTC"


def test_shared_alias_resolves_to_the_lake(tmp_path):
    lake = tmp_path / "lake"
    ts = pd.to_datetime(["2026-05-01"], utc=True) + pd.Timedelta(hours=20)
    _write(layout.daily_bars_path(lake, "AAA"), _bars("AAA", ts))
    out = daily_bars_for(
        "AAA", "2026-05-01", "2026-05-01",
        paths=BowakaV2Paths.default(tmp_path), source="shared", shared_root=lake,
    )
    assert len(out) == 1


def test_quotes_for_alpaca_returns_none_when_lake_has_no_quotes(tmp_path):
    q = quotes_for(
        "AAA", pd.Timestamp("2026-05-04 14:00", tz="UTC"),
        paths=BowakaV2Paths.default(tmp_path), source="alpaca", shared_root=tmp_path / "lake",
    )
    assert q is None


def test_corporate_actions_for_alpaca_empty_when_absent(tmp_path):
    df = corporate_actions_for(
        "AAA", "2026-01-01", "2026-12-31",
        paths=BowakaV2Paths.default(tmp_path), source="alpaca", shared_root=tmp_path / "lake",
    )
    assert df.empty


def test_loaders_no_notimplementederror_remains():
    src = inspect.getsource(loaders)
    assert "NotImplementedError" not in src, "loaders.py must no longer stub its sources"
