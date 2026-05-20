"""Canonical hashing for bowaka_v2_lab configs.

Per [Report §15.3 P2]: the *strategy* hash and the *run/path* hash must be
distinct. The strategy hash covers strategy parameters that affect signals,
sizing, exits, etc. The run/path hash covers everything (strategy + paths +
artifact roots + run identifiers).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


# Top-level keys that participate ONLY in the strategy hash.
_STRATEGY_KEYS = (
    "strategy_id",
    "strategy_version",
    "signals",
    "execution",
    "sizing",
    "risk",
    "exits",
    "scanner",
    "session",
    "market_data",  # feed selection materially affects strategy behaviour
    "universe",
)


def _canonicalise(obj: Any) -> Any:
    """Return a JSON-serializable representation with sorted keys at every level."""
    if isinstance(obj, Mapping):
        return {k: _canonicalise(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, (list, tuple)):
        return [_canonicalise(x) for x in obj]
    return obj


def _sha256_of(obj: Any) -> str:
    payload = json.dumps(_canonicalise(obj), separators=(",", ":"), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_strategy_hash(cfg: Mapping[str, Any]) -> str:
    """Hash only the strategy-relevant subset of the config."""
    subset = {k: cfg[k] for k in _STRATEGY_KEYS if k in cfg}
    return _sha256_of(subset)


def canonical_run_hash(cfg: Mapping[str, Any]) -> str:
    """Hash the entire run config (strategy + paths + artifacts + everything)."""
    return _sha256_of(cfg)
