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
    statuses/vendor=<v>/symbol=<s>/date=<YYYY-MM-DD>/part.parquet
    _ingestion/manifest.json
    _ingestion/runs/<run_id>.json
    _ingestion/audits/<audit_run_id>.parquet

Daily bars are one file per symbol. Minute bars (and quotes) are grouped per
symbol/month — far fewer files than a per-session layout, and fast range scans.

The same layout supports any ``feed`` value — IEX today, SIP when the SIP
ingestion stage exists. The SIP-feed path helpers (see :data:`FEED_SIP` and
:func:`sip_daily_bars_path` / ``sip_minute_bars_path`` / ``sip_quotes_path``)
are thin wrappers over the generic builders that pin ``feed="sip"``; they
exist so SIP-aware callers — preflight, DQ, MarketDataStore SIP probes — can
spell the lookup explicitly without hard-coding the partition string. SIP daily
bars are split-adjusted by convention (``adjustment="split_adjusted"``); SIP
minute bars are raw (``adjustment="raw"``) just like IEX. Realism
remediation 2 Phase 10 (audit §11 Phase 9): the SIP layout helpers ship before
the SIP data does, so labs can write SIP-aware code with no payload in the lake.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

from ..storage.parquet_store import ParquetStore, PathParts

DEFAULT_VENDOR = "alpaca"
DEFAULT_FEED = "iex"
DEFAULT_ADJUSTMENT = "raw"

#: Canonical feed string for the SIP (consolidated tape) partitions. The lake
#: layout supports any feed value — this constant is the lab-side anchor for the
#: SIP-specific path helpers added in realism remediation 2 Phase 10.
FEED_SIP = "sip"

#: Canonical feed string for IEX (partial tape).
FEED_IEX = "iex"

#: Default adjustment policy for SIP daily bars. SIP ingestion produces
#: split-adjusted daily bars; minute bars remain raw (the same as IEX).
SIP_DAILY_ADJUSTMENT = "split_adjusted"

DS_BARS = "bars"
DS_QUOTES = "quotes"
DS_QUOTES_FINE = "quotes_fine"
DS_TRADES = "trades"
DS_ASSETS = "assets"
DS_CORPORATE_ACTIONS = "corporate_actions"
DS_STATUSES = "statuses"
DS_AUCTIONS = "auctions"
INGESTION_DIRNAME = "_ingestion"

_PART_FILENAME = "part.parquet"


def _date_part(d: _dt.date | str) -> str:
    """Return ``YYYY-MM-DD`` for a ``date`` or ISO string."""
    if isinstance(d, _dt.date):
        return d.isoformat()
    return str(d)


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
# Fine NBBO (sub-minute / exchange-coded) — PA.3
# --------------------------------------------------------------------------
def quotes_fine_symbol_dir(
    root: Path | str,
    symbol: str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
) -> Path:
    return Path(root) / DS_QUOTES_FINE / f"vendor={vendor}" / f"feed={feed}" / f"symbol={symbol}"


def quotes_fine_path(
    root: Path | str,
    symbol: str,
    year: int | str,
    month: int | str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
) -> Path:
    """Canonical path to one symbol/month FINE quote file (sub-minute NBBO +
    bid/ask exchange + tape).

    A SIBLING of ``quotes/`` (never under it), so the canonical 1/min
    ``quote_partitions_hash`` is unaffected by a fine-quote backfill
    (dataset-lineage Guardrail 2).
    """
    parts = PathParts(
        {
            "vendor": vendor,
            "feed": feed,
            "symbol": str(symbol),
            "year": _yyyy(year),
            "month": _mm(month),
        }
    )
    return ParquetStore(root).path_for(DS_QUOTES_FINE, parts, _PART_FILENAME)


# --------------------------------------------------------------------------
# Trades (raw tape) — PA.2
# --------------------------------------------------------------------------
def trades_symbol_dir(
    root: Path | str,
    symbol: str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
) -> Path:
    return Path(root) / DS_TRADES / f"vendor={vendor}" / f"feed={feed}" / f"symbol={symbol}"


def trades_path(
    root: Path | str,
    symbol: str,
    year: int | str,
    month: int | str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
) -> Path:
    """Canonical path to one symbol/month RAW trade-tape file.

    A SIBLING of ``quotes/`` (never under it), so the canonical 1/min
    ``quote_partitions_hash`` is unaffected by a trades backfill (dataset-lineage
    Guardrail 2). Stored raw — no per-minute sampling.
    """
    parts = PathParts(
        {
            "vendor": vendor,
            "feed": feed,
            "symbol": str(symbol),
            "year": _yyyy(year),
            "month": _mm(month),
        }
    )
    return ParquetStore(root).path_for(DS_TRADES, parts, _PART_FILENAME)


# --------------------------------------------------------------------------
# Auctions (§5.1) — official open/close auction prints, one symbol/month file.
# A SIBLING of trades/ + quotes/ (never under them), so an auctions backfill never
# perturbs the canonical quote/trade partition hashes (dataset-lineage Guardrail 2).
# --------------------------------------------------------------------------
def auctions_symbol_dir(
    root: Path | str,
    symbol: str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
) -> Path:
    return Path(root) / DS_AUCTIONS / f"vendor={vendor}" / f"feed={feed}" / f"symbol={symbol}"


def auctions_path(
    root: Path | str,
    symbol: str,
    year: int | str,
    month: int | str,
    *,
    vendor: str = DEFAULT_VENDOR,
    feed: str = DEFAULT_FEED,
) -> Path:
    """Canonical path to one symbol/month official-auction file (§5.1).

    Rows are the official opening / closing auction prints from Alpaca
    ``GET /v2/stocks/auctions`` — one file per symbol/month.
    """
    parts = PathParts(
        {
            "vendor": vendor,
            "feed": feed,
            "symbol": str(symbol),
            "year": _yyyy(year),
            "month": _mm(month),
        }
    )
    return ParquetStore(root).path_for(DS_AUCTIONS, parts, _PART_FILENAME)


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


# --------------------------------------------------------------------------
# Statuses (halt / LULD / status partitions; realism remediation 2 Phase 10)
#
# Status partitions are per-symbol/date — a session-local artifact. They are
# read by the halt gate and by the DQ stack's quote/status level when the run
# is intended_realism on a feed whose halt gate is enabled. The lake's writer
# is not in scope for Phase 10; the layout helper ships so DQ + preflight can
# probe for the existence of the partition.
# --------------------------------------------------------------------------
def statuses_symbol_dir(
    root: Path | str,
    symbol: str,
    *,
    vendor: str = DEFAULT_VENDOR,
) -> Path:
    """Directory holding every date partition for ``symbol`` statuses."""
    return Path(root) / DS_STATUSES / f"vendor={vendor}" / f"symbol={symbol}"


def statuses_path(
    root: Path | str,
    symbol: str,
    date: _dt.date | str,
    *,
    vendor: str = DEFAULT_VENDOR,
) -> Path:
    """Canonical path to one symbol/date status partition."""
    return statuses_symbol_dir(root, symbol, vendor=vendor) / f"date={_date_part(date)}" / _PART_FILENAME


# --------------------------------------------------------------------------
# SIP-specific helpers (realism remediation 2 Phase 10, audit §11 Phase 9)
#
# Thin wrappers over the generic builders that pin ``feed="sip"``. They exist
# so SIP-aware callers can spell the lookup explicitly — and so a SIP-only
# preflight failure (no SIP data on the lake) carries an unambiguous pointer
# to the canonical path. SIP daily bars are split-adjusted by convention;
# minute bars are raw (same as IEX). The lake's SIP-payload writer is not in
# scope for Phase 10; these helpers ship before the data does.
#
# SIP partition layout (under ``<root>/``)::
#
#     bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted/symbol=<SYM>/part.parquet
#     bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw/symbol=<SYM>/year=<Y>/month=<M>/part.parquet
#     quotes/vendor=alpaca/feed=sip/symbol=<SYM>/year=<Y>/month=<M>/part.parquet
#     statuses/vendor=alpaca/symbol=<SYM>/date=<YYYY-MM-DD>/part.parquet
#     corporate_actions/vendor=alpaca/symbol=<SYM>/part.parquet
# --------------------------------------------------------------------------
def sip_daily_bars_path(
    root: Path | str,
    symbol: str,
    *,
    vendor: str = DEFAULT_VENDOR,
    adjustment: str = SIP_DAILY_ADJUSTMENT,
) -> Path:
    """Canonical path to one symbol's SIP daily-bar file (default split-adjusted)."""
    return daily_bars_path(root, symbol, vendor=vendor, feed=FEED_SIP, adjustment=adjustment)


def sip_minute_bars_path(
    root: Path | str,
    symbol: str,
    year: int | str,
    month: int | str,
    *,
    vendor: str = DEFAULT_VENDOR,
    adjustment: str = "raw",
) -> Path:
    """Canonical path to one symbol/month SIP minute-bar file (default raw)."""
    return minute_bars_path(
        root, symbol, year, month, vendor=vendor, feed=FEED_SIP, adjustment=adjustment,
    )


def sip_quotes_path(
    root: Path | str,
    symbol: str,
    year: int | str,
    month: int | str,
    *,
    vendor: str = DEFAULT_VENDOR,
) -> Path:
    """Canonical path to one symbol/month SIP quote file."""
    return quotes_path(root, symbol, year, month, vendor=vendor, feed=FEED_SIP)


def sip_bars_root(
    root: Path | str,
    timeframe: str,
    *,
    vendor: str = DEFAULT_VENDOR,
    adjustment: str | None = None,
) -> Path:
    """SIP-feed bars-timeframe-adjustment root for one (timeframe, adjustment).

    Defaults to ``adjustment=split_adjusted`` for ``timeframe='1d'`` and
    ``adjustment=raw`` for ``timeframe='1m'``.
    """
    if adjustment is None:
        adjustment = SIP_DAILY_ADJUSTMENT if str(timeframe) == "1d" else "raw"
    return bars_timeframe_root(root, timeframe, vendor=vendor, feed=FEED_SIP, adjustment=adjustment)


def sip_quotes_root(root: Path | str, *, vendor: str = DEFAULT_VENDOR) -> Path:
    """SIP-feed quotes root (``quotes/vendor=<v>/feed=sip/``)."""
    return Path(root) / DS_QUOTES / f"vendor={vendor}" / f"feed={FEED_SIP}"


def sip_partitions_available(root: Path | str, *, vendor: str = DEFAULT_VENDOR) -> bool:
    """Return ``True`` when the lake has *any* SIP partition (bars or quotes).

    A cheap existence probe used by SIP preflight + DQ. Realism remediation 2
    Phase 10 (audit §11 Phase 9): the lake has no SIP data today, so this
    returns ``False`` on a normal lake; a SIP-feed config that runs against
    such a lake must fail closed with a clear pointer to
    ``docs/data_lake_layout.md``.
    """
    rt = Path(root)
    if not rt.is_dir():
        return False
    bars_1d = sip_bars_root(rt, "1d")
    bars_1m = sip_bars_root(rt, "1m")
    quotes = sip_quotes_root(rt)
    for candidate in (bars_1d, bars_1m, quotes):
        if candidate.is_dir() and any(candidate.rglob("*.parquet")):
            return True
    return False
