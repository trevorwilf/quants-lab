"""Optuna storage resolver.

Reads ``OPTUNA_STORAGE`` env var for the Postgres URI shared with
``market_lab`` and the ``quantslab_desktop_compose.yaml`` Docker stack.
Falls back to SQLite if unset. Provides :func:`require_postgres` for
multi-worker entry points that must refuse SQLite.

Back-compat:

- ``BOWAKA_OPTUNA_STORAGE`` is read with a :class:`DeprecationWarning` when
  ``OPTUNA_STORAGE`` is unset. The fallback shim will be dropped in a
  future cleanup phase — operators should rename their env var.
- :class:`StorageSpec` + :func:`resolve_storage` are preserved so existing
  callers (``safe_n_jobs``, ``optimize``, etc.) keep working without change.
"""

from __future__ import annotations

import logging
import os
import warnings
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StorageSpec:
    """Back-compat shim retained for callers that already import this."""

    url: str
    requires_n_jobs_1: bool


def _read_env(fallback_path: str) -> str:
    """Internal helper: resolve OPTUNA_STORAGE with deprecation fallback."""
    env_url = os.environ.get("OPTUNA_STORAGE")
    if env_url:
        return env_url
    legacy = os.environ.get("BOWAKA_OPTUNA_STORAGE")
    if legacy:
        warnings.warn(
            "BOWAKA_OPTUNA_STORAGE is deprecated; rename it to OPTUNA_STORAGE "
            "to match the docker stack and market_lab. The back-compat shim "
            "will be removed in a future release.",
            DeprecationWarning,
            stacklevel=3,
        )
        return legacy
    logger.warning(
        "OPTUNA_STORAGE not set - falling back to SQLite (%s). "
        "This is NOT suitable for multi-worker optimization.",
        fallback_path,
    )
    return f"sqlite:///{fallback_path}"


def get_storage_url(fallback_path: str = "bowaka_optuna_studies.db") -> str:
    """Return the Optuna storage URL.

    Priority:

    1. ``OPTUNA_STORAGE`` env var (expected: Postgres URI from Docker stack).
    2. ``BOWAKA_OPTUNA_STORAGE`` env var (deprecated, emits a warning).
    3. SQLite file at ``fallback_path`` (relative to CWD).
    """
    return _read_env(fallback_path)


def get_storage_type() -> str:
    """Return ``"postgres"`` if either env var is set to a Postgres URI,
    otherwise ``"sqlite"``."""
    url = os.environ.get("OPTUNA_STORAGE") or os.environ.get("BOWAKA_OPTUNA_STORAGE")
    if not url:
        return "sqlite"
    return "postgres" if "postgresql" in url.lower() else "sqlite"


def require_postgres(storage_url: Optional[str] = None) -> str:
    """Return the storage URL, raising :class:`ValueError` if not PostgreSQL.

    Use this for multi-worker optimization where SQLite is unsafe.
    """
    url = storage_url or get_storage_url()
    if "postgresql" not in url.lower():
        raise ValueError(
            f"Multi-worker optimization requires PostgreSQL storage. "
            f"Got: {url!r}. Set the OPTUNA_STORAGE environment variable "
            f"to a PostgreSQL connection string."
        )
    return url


def resolve_storage(url: Optional[str] = None) -> StorageSpec:
    """Back-compat: return a :class:`StorageSpec` for an explicit URL or the
    env-resolved one. SQLite forces ``n_jobs=1``.
    """
    final = url if url is not None else get_storage_url()
    requires_n_jobs_1 = "postgresql" not in final.lower()
    return StorageSpec(url=final, requires_n_jobs_1=requires_n_jobs_1)
