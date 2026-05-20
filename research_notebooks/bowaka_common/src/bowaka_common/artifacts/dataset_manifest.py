"""Dataset-manifest builder.

Per [Report §7.2]. Required fields:
- schema_version (int)
- provider (str)
- feed (str)
- symbols (list[str], sorted)
- start_date (ISO date str)
- end_date (ISO date str)
- dataset_hash (str)
- bar_count (int)

Optional:
- adjustments, exchange_calendar, source_uri, notes
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional


DATASET_MANIFEST_SCHEMA_VERSION = 1
_REQUIRED = frozenset({"schema_version", "provider", "feed", "symbols", "start_date", "end_date", "dataset_hash", "bar_count"})


def build_dataset_manifest(
    *,
    provider: str,
    feed: str,
    symbols: Iterable[str],
    start_date: str,
    end_date: str,
    dataset_hash: str,
    bar_count: int,
    adjustments: Optional[str] = None,
    exchange_calendar: str = "XNYS",
    source_uri: Optional[str] = None,
    notes: Optional[str] = None,
    extras: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    if not provider:
        raise ValueError("provider is required")
    if not feed:
        raise ValueError("feed is required")
    syms = sorted({s for s in symbols if s})
    if not syms:
        raise ValueError("symbols must be non-empty")
    if bar_count < 0:
        raise ValueError("bar_count must be non-negative")
    manifest: dict[str, Any] = {
        "schema_version": DATASET_MANIFEST_SCHEMA_VERSION,
        "provider": provider,
        "feed": feed,
        "symbols": syms,
        "start_date": start_date,
        "end_date": end_date,
        "dataset_hash": dataset_hash,
        "bar_count": int(bar_count),
        "exchange_calendar": exchange_calendar,
    }
    if adjustments is not None:
        manifest["adjustments"] = adjustments
    if source_uri is not None:
        manifest["source_uri"] = source_uri
    if notes is not None:
        manifest["notes"] = notes
    if extras is not None:
        for k, v in extras.items():
            if k not in _REQUIRED:
                manifest[k] = v
    return manifest


def validate_dataset_manifest(manifest: Mapping[str, Any]) -> None:
    missing = _REQUIRED - set(manifest.keys())
    if missing:
        raise ValueError(f"dataset_manifest missing required fields: {sorted(missing)}")
