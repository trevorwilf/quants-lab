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


def build_candidate_v2(
    *,
    strategy: str,
    generated_at: str,
    signal_date: date | str,
    provider: str,
    data_feed: str,
    bar_timeframe: str,
    config_hash: str,
    config_hash_short: str,
    universe_hash: str,
    latest_bar_timestamp: str,
    counts: dict[str, int],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a v2 candidate document matching the legacy strategy schema."""
    return candidate_v2_doc(
        payload={
            "strategy": strategy,
            "generated_at": generated_at,
            "as_of_date": str(signal_date),
            "provider": provider,
            "data_feed": data_feed,
            "bar_timeframe": bar_timeframe,
            "config_hash": config_hash,
            "config_hash_short": config_hash_short,
            "universe_hash": universe_hash,
            "latest_bar_timestamp": latest_bar_timestamp,
            "n_universe_with_features": counts.get("n_universe_with_features", 0),
            "n_passed_universe_gates": counts.get("n_passed_universe_gates", 0),
            "n_in_play": counts.get("n_candidates", 0),
            "n_excluded_by_instrument_class": counts.get("n_excluded_by_instrument_class", 0),
            "candidates": candidates,
        }
    )


def build_candidate_v3(
    *,
    strategy: str,
    generated_at: str,
    signal_date: date | str,
    trade_date: date | str,
    provider: str,
    data_feed: str,
    bar_timeframe: str,
    adjustment: str,
    config_hash: str,
    dataset_hash: str,
    universe_hash: str,
    candidates: list[dict[str, Any]],
    all_decisions_path: str,
) -> dict[str, Any]:
    """Build a v3 candidate document for research."""
    return candidate_v3_doc(
        payload={
            "strategy": strategy,
            "generated_at": generated_at,
            "signal_date": str(signal_date),
            "trade_date": str(trade_date),
            "provider": provider,
            "data_feed": data_feed,
            "bar_timeframe": bar_timeframe,
            "adjustment": adjustment,
            "config_hash": config_hash,
            "dataset_hash": dataset_hash,
            "universe_hash": universe_hash,
            "candidates": candidates,
            "all_decisions_path": all_decisions_path,
        }
    )
