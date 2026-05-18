"""Deterministic config / artifact hashing.

The hash is canonicalized by sorting keys and dropping platform-dependent
representations (numpy scalars, Decimal, Timestamp, etc.). Two semantically
equal config dicts must yield the same hash regardless of key insertion order.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from decimal import Decimal
from typing import Any

try:
    import numpy as np
except ImportError:  # pragma: no cover - numpy is a hard dep of bowaka_lab
    np = None  # type: ignore[assignment]

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore[assignment]


def _default(obj: Any) -> Any:
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if np is not None and isinstance(obj, np.generic):
        return obj.item()
    if pd is not None and isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="python")
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def stable_hash(obj: Any, *, prefix: str = "sha256:") -> str:
    """Return a deterministic SHA-256 hash for any JSON-serializable object."""
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_default).encode("utf-8")
    return prefix + hashlib.sha256(blob).hexdigest()


def compute_config_hash(cfg: Any, *, prefix: str = "sha256:") -> str:
    """Return a stable hash for a ``BowakaBacktestConfig`` (or any pydantic model
    exposing ``canonical_dict()`` or ``model_dump()``)."""
    if hasattr(cfg, "canonical_dict"):
        payload = cfg.canonical_dict()
    elif hasattr(cfg, "model_dump"):
        payload = cfg.model_dump(mode="json")
    else:
        payload = cfg
    return stable_hash(payload, prefix=prefix)


def short(hash_str: str, length: int = 12) -> str:
    """Truncated form for log lines."""
    if ":" in hash_str:
        hash_str = hash_str.split(":", 1)[1]
    return hash_str[:length]
