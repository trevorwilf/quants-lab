"""scripts/migrate_market_data.py — legacy layout -> canonical lake, no row loss."""
from __future__ import annotations

import importlib.util
import sys

import pandas as pd


def _load_migrate_module(repo_root):
    src = repo_root / "research_notebooks" / "bowaka_common" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    spec = importlib.util.spec_from_file_location(
        "migrate_market_data", repo_root / "scripts" / "migrate_market_data.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
            "volume": [100] * n,
        }
    )


def _build_legacy_tree(source):
    # daily: one per-symbol file
    daily = source / "bars/vendor=alpaca/feed=iex/timeframe=1d/adjustment=raw/symbol=AAA"
    daily.mkdir(parents=True, exist_ok=True)
    _bars("AAA", pd.to_datetime(["2026-05-01", "2026-05-02"], utc=True) + pd.Timedelta(hours=20)).to_parquet(
        daily / "part.parquet", index=False
    )
    # minute: two per-session files, same calendar month
    for day in ("2026-05-01", "2026-05-02"):
        mdir = source / f"bars/vendor=alpaca/feed=iex/timeframe=1m/adjustment=raw/session_date={day}"
        mdir.mkdir(parents=True, exist_ok=True)
        _bars("AAA", pd.to_datetime([f"{day} 14:00", f"{day} 14:01"], utc=True)).to_parquet(
            mdir / "symbol=AAA.parquet", index=False
        )
    # assets snapshot
    adir = source / "assets/vendor=alpaca/snapshot_id=snap1"
    adir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"snapshot_id": ["snap1"], "symbol": ["AAA"]}).to_parquet(adir / "assets.parquet", index=False)


def test_migration_transcodes_and_loses_no_rows(repo_root, tmp_path):
    mod = _load_migrate_module(repo_root)
    from bowaka_common.marketdata import layout

    source, dest = tmp_path / "old", tmp_path / "lake"
    _build_legacy_tree(source)

    report = mod.migrate_market_data(source, dest)
    assert report["ok"], report["mismatches"]

    assert layout.daily_bars_path(dest, "AAA").is_file()
    # two per-session files transcoded into one May month-file with 4 rows
    may = layout.minute_bars_path(dest, "AAA", 2026, 5)
    assert may.is_file()
    assert len(pd.read_parquet(may)) == 4
    assert layout.assets_path(dest, "snap1").is_file()

    assert report["minute"]["rows_in"] == report["minute"]["rows_out"] == 4
    assert report["daily"]["rows_in"] == report["daily"]["rows_out"] == 2
    assert (layout.ingestion_dir(dest) / "migration_report.json").is_file()


def test_migration_is_idempotent(repo_root, tmp_path):
    mod = _load_migrate_module(repo_root)
    from bowaka_common.marketdata import layout

    source, dest = tmp_path / "old", tmp_path / "lake"
    _build_legacy_tree(source)
    first = mod.migrate_market_data(source, dest)
    second = mod.migrate_market_data(source, dest)
    assert first["minute"]["rows_out"] == second["minute"]["rows_out"] == 4
    assert len(pd.read_parquet(layout.minute_bars_path(dest, "AAA", 2026, 5))) == 4


def test_dry_run_writes_nothing(repo_root, tmp_path):
    mod = _load_migrate_module(repo_root)
    from bowaka_common.marketdata import layout

    source, dest = tmp_path / "old", tmp_path / "lake"
    _build_legacy_tree(source)
    report = mod.migrate_market_data(source, dest, dry_run=True)
    assert report["dry_run"] is True
    assert not layout.daily_bars_path(dest, "AAA").is_file()
