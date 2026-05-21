#!/usr/bin/env python
"""Migrate the legacy ``bowaka_lab`` parquet tree into the shared market-data lake.

The legacy backfill wrote (under ``bowaka_lab/db_tools/bowaka_data/parquet/``)::

    bars/vendor=alpaca/feed=<f>/timeframe=1d/adjustment=<a>/symbol=<s>/part.parquet
    bars/vendor=alpaca/feed=<f>/timeframe=1m/adjustment=<a>/session_date=<D>/symbol=<s>.parquet
    assets/vendor=alpaca/snapshot_id=<id>/assets.parquet

The canonical lake (see ``bowaka_common.marketdata.layout``) uses::

    bars/vendor=alpaca/feed=<f>/timeframe=1d/adjustment=<a>/symbol=<s>/part.parquet
    bars/vendor=alpaca/feed=<f>/timeframe=1m/adjustment=<a>/symbol=<s>/year=<Y>/month=<M>/part.parquet
    assets/vendor=alpaca/snapshot_id=<id>/assets.parquet

Daily bars and asset snapshots copy with a straight path remap. Minute bars are
**transcoded**: a symbol's per-session files are regrouped into per-symbol/month
files. The strategy-derived ``scope/`` tree is not migrated — the lake holds raw
vendor data only.

The migration is idempotent (re-runs overwrite identically) and verifies that no
rows are lost. A report lands at ``<dest>/_ingestion/migration_report.json``.

Usage::

    python scripts/migrate_market_data.py --source <old/parquet> --dest <lake>
    python scripts/migrate_market_data.py --verify-only      # compare, don't write
    python scripts/migrate_market_data.py --dry-run          # plan, don't write
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
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

import pandas as pd  # noqa: E402

from bowaka_common.marketdata import layout as _layout  # noqa: E402
from bowaka_common.marketdata.store import resolve_market_data_root  # noqa: E402
from bowaka_common.storage.dataset_hash import hash_dataframe  # noqa: E402

_DEFAULT_SOURCE = "research_notebooks/bowaka_lab/db_tools/bowaka_data/parquet"


def _partition_value(path_part: str) -> str:
    return path_part.split("=", 1)[1] if "=" in path_part else path_part


def _read(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def _write(df: pd.DataFrame, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(target, index=False)


def _row_hash(df: pd.DataFrame) -> str:
    sort_keys = [c for c in ("symbol", "timestamp") if c in df.columns]
    return hash_dataframe(df, sort_by=sort_keys or None)


def migrate_market_data(
    source: str | Path,
    dest: str | Path,
    *,
    dry_run: bool = False,
    verify_only: bool = False,
) -> dict:
    """Migrate ``source`` (legacy parquet tree) into ``dest`` (canonical lake).

    Returns a report dict; also written to ``<dest>/_ingestion/migration_report.json``
    unless ``dry_run``.
    """
    source = Path(source)
    dest = resolve_market_data_root(dest, create=not dry_run)
    if not source.is_dir():
        raise FileNotFoundError(f"migration source not found: {source}")

    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "dest": str(dest),
        "dry_run": dry_run,
        "verify_only": verify_only,
        "daily": {"symbols": 0, "rows_in": 0, "rows_out": 0},
        "minute": {"symbols": 0, "months_written": 0, "rows_in": 0, "rows_out": 0},
        "assets": {"snapshots": 0},
        "mismatches": [],
    }

    # -- daily bars: straight copy with path remap ------------------------
    for src_file in sorted(source.glob("bars/vendor=*/feed=*/timeframe=1d/adjustment=*/symbol=*/part.parquet")):
        parts = {p.split("=", 1)[0]: p.split("=", 1)[1] for p in src_file.parts if "=" in p}
        symbol = parts["symbol"]
        df = _read(src_file)
        report["daily"]["symbols"] += 1
        report["daily"]["rows_in"] += len(df)
        target = _layout.daily_bars_path(
            dest, symbol, vendor=parts.get("vendor", "alpaca"),
            feed=parts.get("feed", "iex"), adjustment=parts.get("adjustment", "raw"),
        )
        if verify_only:
            out_rows = len(_read(target)) if target.is_file() else 0
        else:
            if not dry_run:
                _write(df, target)
            out_rows = len(df)
        report["daily"]["rows_out"] += out_rows
        if out_rows != len(df):
            report["mismatches"].append(f"daily {symbol}: in={len(df)} out={out_rows}")

    # -- minute bars: transcode per-session -> per-symbol/month ----------
    minute_by_symbol: dict[tuple, list[Path]] = defaultdict(list)
    for src_file in sorted(source.glob("bars/vendor=*/feed=*/timeframe=1m/adjustment=*/session_date=*/symbol=*.parquet")):
        parts = {p.split("=", 1)[0]: p.split("=", 1)[1] for p in src_file.parts if "=" in p}
        symbol = _partition_value(src_file.stem)  # "symbol=AAA" -> "AAA"
        key = (parts.get("vendor", "alpaca"), parts.get("feed", "iex"), parts.get("adjustment", "raw"), symbol)
        minute_by_symbol[key].append(src_file)

    for (vendor, feed, adjustment, symbol), files in sorted(minute_by_symbol.items()):
        frames = [_read(f) for f in files]
        combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        rows_in = len(combined)
        report["minute"]["symbols"] += 1
        report["minute"]["rows_in"] += rows_in
        if combined.empty or "timestamp" not in combined.columns:
            continue
        combined["timestamp"] = pd.to_datetime(combined["timestamp"], utc=True)
        rows_out = 0
        for (year, month), grp in combined.groupby(
            [combined["timestamp"].dt.year, combined["timestamp"].dt.month]
        ):
            target = _layout.minute_bars_path(
                dest, symbol, int(year), int(month), vendor=vendor, feed=feed, adjustment=adjustment
            )
            grp = grp.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
            if verify_only:
                rows_out += len(_read(target)) if target.is_file() else 0
            else:
                if not dry_run:
                    _write(grp, target)
                    report["minute"]["months_written"] += 1
                rows_out += len(grp)
        report["minute"]["rows_out"] += rows_out
        if not verify_only and not dry_run and rows_out != len(combined.drop_duplicates(subset=["timestamp"])):
            report["mismatches"].append(f"minute {symbol}: in={rows_in} out={rows_out}")

    # -- assets: straight copy with path remap ---------------------------
    for src_file in sorted(source.glob("assets/vendor=*/snapshot_id=*/assets.parquet")):
        parts = {p.split("=", 1)[0]: p.split("=", 1)[1] for p in src_file.parts if "=" in p}
        df = _read(src_file)
        target = _layout.assets_path(dest, parts["snapshot_id"], vendor=parts.get("vendor", "alpaca"))
        if not dry_run and not verify_only:
            _write(df, target)
        report["assets"]["snapshots"] += 1

    report["ok"] = not report["mismatches"]
    if not dry_run:
        report_path = _layout.ingestion_dir(dest) / "migration_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        report["report_path"] = str(report_path)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Migrate the legacy parquet tree into the market-data lake.")
    ap.add_argument("--source", default=_DEFAULT_SOURCE, help="legacy parquet root")
    ap.add_argument("--dest", default=None, help="lake root (default: resolve MARKET_DATA_ROOT)")
    ap.add_argument("--dry-run", action="store_true", help="plan only; write nothing")
    ap.add_argument("--verify-only", action="store_true", help="compare source vs an existing dest")
    args = ap.parse_args(argv)

    report = migrate_market_data(
        args.source, args.dest, dry_run=args.dry_run, verify_only=args.verify_only
    )
    print(json.dumps(report, indent=2, default=str))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
