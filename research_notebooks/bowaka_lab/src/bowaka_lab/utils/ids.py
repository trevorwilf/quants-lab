"""Deterministic ID generators.

All IDs derive from inputs only, never from clocks or randomness, so the same
inputs always yield the same ID. This keeps backtests reproducible and gives
counterfactual results stable join keys.
"""

from __future__ import annotations

from datetime import date, datetime

from bowaka_lab.config.hashing import short, stable_hash


def run_id(
    *,
    strategy: str,
    config_hash: str,
    started_at: datetime,
    feed: str = "iex",
    label: str | None = None,
) -> str:
    timestamp = started_at.strftime("%Y-%m-%dT%H%M%SZ")
    bits = [f"bt_{timestamp}_cfg_{short(config_hash, 8)}_{feed}"]
    if label:
        bits.append(label)
    return "_".join(bits)


def prefilter_run_id(
    *,
    signal_date: date,
    feed: str,
    config_hash: str,
) -> str:
    return f"prefilter_{signal_date.isoformat()}_{feed}_cfg_{short(config_hash, 6)}"


def trade_id(
    *,
    symbol: str,
    trade_date: date,
    entry_rule: str,
    config_hash: str,
) -> str:
    return f"bt_{symbol}_{trade_date.isoformat()}_{entry_rule}_cfg_{short(config_hash, 6)}"


def counterfactual_id(
    *,
    symbol: str,
    trade_date: date,
    variant: dict,
) -> str:
    return f"cf_{symbol}_{trade_date.isoformat()}_{short(stable_hash(variant), 10)}"


def ingestion_run_id(
    *,
    feed: str,
    timeframe: str,
    adjustment: str,
    started_at: datetime,
) -> str:
    timestamp = started_at.strftime("%Y-%m-%dT%H%M%SZ")
    return f"ingest_{timestamp}_{feed}_{timeframe}_{adjustment}"


def asset_snapshot_id(*, vendor: str, captured_at: datetime) -> str:
    timestamp = captured_at.strftime("%Y-%m-%dT%H%M%SZ")
    return f"{timestamp}_{vendor}_assets"
