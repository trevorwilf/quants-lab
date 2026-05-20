"""Generic run-manifest builder.

Per [Report §18.2]. Required fields:
- schema_version (int)
- strategy_id (str)
- run_id (str)
- created_at (ISO-8601 string)
- config_hash (str)
- dataset_hash (str)
- code_manifest_hash (str)

Optional fields:
- strategy_version, run_kind, feed, host, environment, notes, parameters
"""
from __future__ import annotations

import datetime as _dt
import socket
from typing import Any, Mapping, Optional


RUN_MANIFEST_SCHEMA_VERSION = 1
_REQUIRED = frozenset({"schema_version", "strategy_id", "run_id", "created_at", "config_hash", "dataset_hash", "code_manifest_hash"})


def build_run_manifest(
    *,
    strategy_id: str,
    run_id: str,
    config_hash: str,
    dataset_hash: str,
    code_manifest_hash: str,
    strategy_version: str = "0.0.0",
    run_kind: str = "backtest",
    feed: Optional[str] = None,
    parameters: Optional[Mapping[str, Any]] = None,
    extras: Optional[Mapping[str, Any]] = None,
    created_at: Optional[_dt.datetime] = None,
) -> dict[str, Any]:
    if not strategy_id:
        raise ValueError("strategy_id is required")
    if not run_id:
        raise ValueError("run_id is required")
    if not config_hash:
        raise ValueError("config_hash is required")
    if not dataset_hash:
        raise ValueError("dataset_hash is required")
    if not code_manifest_hash:
        raise ValueError("code_manifest_hash is required")
    if created_at is None:
        created_at = _dt.datetime.now(tz=_dt.timezone.utc)
    elif created_at.tzinfo is None:
        raise ValueError("created_at must be timezone-aware")
    manifest: dict[str, Any] = {
        "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "run_id": run_id,
        "run_kind": run_kind,
        "created_at": created_at.isoformat(),
        "config_hash": config_hash,
        "dataset_hash": dataset_hash,
        "code_manifest_hash": code_manifest_hash,
        "host": socket.gethostname(),
    }
    if feed is not None:
        manifest["feed"] = feed
    if parameters is not None:
        manifest["parameters"] = dict(parameters)
    if extras is not None:
        for k, v in extras.items():
            if k in _REQUIRED:
                continue
            manifest[k] = v
    return manifest


def validate_run_manifest(manifest: Mapping[str, Any]) -> None:
    missing = _REQUIRED - set(manifest.keys())
    if missing:
        raise ValueError(f"run_manifest missing required fields: {sorted(missing)}")
