"""bowaka_common.marketdata — the shared Alpaca market-data lake layer.

A partitioned-Parquet store plus its ingestion pipeline, consumed by both
``bowaka_lab`` and ``bowaka_v2_lab``. The on-disk layout is defined once in
:mod:`bowaka_common.marketdata.layout`; readers go through
:class:`MarketDataStore`; the backfill writes via the same layout.
"""
from __future__ import annotations

from . import layout
from .backfill import BackfillConfig, run_backfill
from .catalog import available_symbols, dataset_hash, date_coverage
from .runner import load_backfill_config, resolve_end_date, run_configured_backfill
from .store import (
    MarketDataStore,
    QuoteRow,
    default_market_data_root,
    resolve_market_data_root,
)

__all__ = [
    "MarketDataStore",
    "QuoteRow",
    "resolve_market_data_root",
    "default_market_data_root",
    "available_symbols",
    "date_coverage",
    "dataset_hash",
    "layout",
    "BackfillConfig",
    "run_backfill",
    "load_backfill_config",
    "run_configured_backfill",
    "resolve_end_date",
]
