"""Mongo collection schema constructors.

These are *not* enforced schemas; they are factory functions that build the
canonical document for each collection given the relevant inputs. Tests assert
that the produced dicts match the layout in ``[Report §8.5]`` and ``[Report §11.3]``.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Any, Iterable


def asset_snapshot_doc(*, snapshot_id: str, vendor: str, asset_count: int, asset_hash: str, allowed_exchanges: list[str] | None) -> dict[str, Any]:
    return {
        "snapshot_id": snapshot_id,
        "vendor": vendor,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "allowed_exchanges": allowed_exchanges,
        "asset_count": asset_count,
        "asset_hash": asset_hash,
        "source": "alpaca_trading_assets",
        "notes": "Current asset universe. Survivorship-biased for historical backtests.",
    }


def asset_row_doc(*, snapshot_id: str, row: Any) -> dict[str, Any]:
    base = asdict(row) if hasattr(row, "__dataclass_fields__") else dict(row)
    base["snapshot_id"] = snapshot_id
    return base


def ingestion_run_doc(
    *,
    ingestion_run_id: str,
    vendor: str,
    feed: str,
    timeframe: str,
    adjustment: str,
    start: date,
    end: date,
    symbol_count_requested: int,
    symbol_count_success: int,
    symbol_count_failed: int,
    api_call_count: int,
    rate_limit_policy: str,
    dataset_hash: str,
    parquet_root: str,
) -> dict[str, Any]:
    return {
        "ingestion_run_id": ingestion_run_id,
        "vendor": vendor,
        "feed": feed,
        "timeframe": timeframe,
        "adjustment": adjustment,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "symbol_count_requested": symbol_count_requested,
        "symbol_count_success": symbol_count_success,
        "symbol_count_failed": symbol_count_failed,
        "api_call_count": api_call_count,
        "rate_limit_policy": rate_limit_policy,
        "dataset_hash": dataset_hash,
        "parquet_root": parquet_root,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def candidate_v2_doc(*, schema_version: int = 2, payload: dict[str, Any]) -> dict[str, Any]:
    out = {"schema_version": schema_version, **payload}
    required = (
        "schema_version",
        "strategy",
        "generated_at",
        "as_of_date",
        "provider",
        "data_feed",
        "bar_timeframe",
        "config_hash",
        "universe_hash",
        "candidates",
    )
    missing = [k for k in required if k not in out]
    if missing:
        raise ValueError(f"candidate v2 missing required fields: {missing}")
    return out


def candidate_v3_doc(*, payload: dict[str, Any]) -> dict[str, Any]:
    out = {"schema_version": 3, **payload}
    required = (
        "strategy",
        "generated_at",
        "signal_date",
        "trade_date",
        "provider",
        "data_feed",
        "bar_timeframe",
        "adjustment",
        "config_hash",
        "dataset_hash",
        "universe_hash",
        "candidates",
        "all_decisions_path",
    )
    missing = [k for k in required if k not in out]
    if missing:
        raise ValueError(f"candidate v3 missing required fields: {missing}")
    return out
