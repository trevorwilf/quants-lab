"""Canonical Hive partition layout for the shared market-data lake.

This module is the **single source of truth** for where every dataset lives
under the lake root. All path construction goes through here so the layout can
never drift between the backfill (writer) and the store (reader).

Layout (under ``<root>/``)::

    bars/vendor=<v>/feed=<f>/timeframe=1d/adjustment=<a>/symbol=<s>/part.parquet
    bars/vendor=<v>/feed=<f>/timeframe=1m/adjustment=<a>/symbol=<s>/year=<Y>/month=<M>/part.parquet
    quotes/vendor=<v>/feed=<f>/symbol=<s>/year=<Y>/month=<M>/part.parquet
    assets/vendor=<v>/snapshot_id=<id>/assets.parquet
    corporate_actions/vendor=<v>/symbol=<s>/part.parquet
    _ingestion/manifest.json
    _ingestion/runs/<run_id>.json
    _ingestion/audits/<audit_run_id>.parquet

Daily bars are one file per symbol. Minute bars (and quotes) are grouped per
symbol/month — far fewer files than a per-session layout, and fast range scans.
"""
from __future__ import annotations

from pathlib import Path

from ..storage.parquet_store import ParquetStore, PathParts

DEFAULT_VENDOR = "alpaca"
DEFAULT_FEED = "iex"
DEFAULT_ADJUSTMENT = "raw"

DS_BARS = "bars"
DS_QUOTES = "quotes"
DS_ASSETS = "assets"
DS_CORPORATE_ACTIONS = "corporate_actions"
INGESTION_DIRNAME = "_ingestion"

_PART_FILENAME = "part.parquet"


def _yyyy(year: int | str) -> str:
    return f"{int(year):04d}"


def _mm(month: int | str) -> str:
    return f"{int(month):02d}"


# --------------------------------------------------------------------------
# Bars
# --------------------------------------------------------------------------
def bars_timeframe_root(
    root: Path | str,
    timeframe: str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
    adjustment: str = DEFAULT_ADJUSTMENT,
) -> Path:
    """Directory holding every symbol's bars for one (vendor, feed, timeframe)."""
    return (
        Path(root)
        / DS_BARS
        / f"vendor={vendor}"
        / f"feed={feed}"
        / f"timeframe={timeframe}"
        / f"adjustment={adjustment}"
    )


def daily_bars_symbol_dir(
    root: Path | str,
    symbol: str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
    adjustment: str = DEFAULT_ADJUSTMENT,
) -> Path:
    return bars_timeframe_root(root, "1d", vendor=vendor, feed=feed, adjustment=adjustment) / f"symbol={symbol}"


def daily_bars_path(
    root: Path | str,
    symbol: str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
    adjustment: str = DEFAULT_ADJUSTMENT,
) -> Path:
    """Canonical path to one symbol's daily-bar file."""
    parts = PathParts(
        {
            "vendor": vendor,
            "feed": feed,
            "timeframe": "1d",
            "adjustment": adjustment,
            "symbol": str(symbol),
        }
    )
    return ParquetStore(root).path_for(DS_BARS, parts, _PART_FILENAME)


def minute_bars_symbol_dir(
    root: Path | str,
    symbol: str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
    adjustment: str = DEFAULT_ADJUSTMENT,
) -> Path:
    return bars_timeframe_root(root, "1m", vendor=vendor, feed=feed, adjustment=adjustment) / f"symbol={symbol}"


def minute_bars_path(
    root: Path | str,
    symbol: str,
    year: int | str,
    month: int | str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
    adjustment: str = DEFAULT_ADJUSTMENT,
) -> Path:
    """Canonical path to one symbol/month minute-bar file."""
    parts = PathParts(
        {
            "vendor": vendor,
            "feed": feed,
            "timeframe": "1m",
            "adjustment": adjustment,
            "symbol": str(symbol),
            "year": _yyyy(year),
            "month": _mm(month),
        }
    )
    return ParquetStore(root).path_for(DS_BARS, parts, _PART_FILENAME)


# --------------------------------------------------------------------------
# Quotes
# --------------------------------------------------------------------------
def quotes_symbol_dir(
    root: Path | str,
    symbol: str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
) -> Path:
    return Path(root) / DS_QUOTES / f"vendor={vendor}" / f"feed={feed}" / f"symbol={symbol}"


def quotes_path(
    root: Path | str,
    symbol: str,
    year: int | str,
    month: int | str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
) -> Path:
    """Canonical path to one symbol/month quote file."""
    parts = PathParts(
        {
            "vendor": vendor,
            "feed": feed,
            "symbol": str(symbol),
            "year": _yyyy(year),
            "month": _mm(month),
        }
    )
    return ParquetStore(root).path_for(DS_QUOTES, parts, _PART_FILENAME)


# --------------------------------------------------------------------------
# Assets
# --------------------------------------------------------------------------
def assets_root(root: Path | str, *, vendor: str = DEFAULT_VENDOR) -> Path:
    return Path(root) / DS_ASSETS / f"vendor={vendor}"


def assets_path(root: Path | str, snapshot_id: str, *, vendor: str = DEFAULT_VENDOR) -> Path:
    """Canonical path to one asset snapshot."""
    return assets_root(root, vendor=vendor) / f"snapshot_id={snapshot_id}" / "assets.parquet"


# --------------------------------------------------------------------------
# Corporate actions
# --------------------------------------------------------------------------
def corporate_actions_path(
    root: Path | str, symbol: str, *, vendor: str = DEFAULT_VENDOR
) -> Path:
    """Canonical path to one symbol's corporate-actions file."""
    parts = PathParts({"vendor": vendor, "symbol": str(symbol)})
    return ParquetStore(root).path_for(DS_CORPORATE_ACTIONS, parts, _PART_FILENAME)


# --------------------------------------------------------------------------
# Ingestion metadata
# --------------------------------------------------------------------------
def ingestion_dir(root: Path | str) -> Path:
    return Path(root) / INGESTION_DIRNAME


def ingestion_manifest_path(root: Path | str) -> Path:
    return ingestion_dir(root) / "manifest.json"


def ingestion_run_path(root: Path | str, run_id: str) -> Path:
    return ingestion_dir(root) / "runs" / f"{run_id}.json"


def ingestion_audit_path(root: Path | str, audit_run_id: str) -> Path:
    return ingestion_dir(root) / "audits" / f"{audit_run_id}.parquet"
