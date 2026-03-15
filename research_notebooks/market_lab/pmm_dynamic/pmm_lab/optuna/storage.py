"""
Optuna storage resolver.

Reads OPTUNA_STORAGE env var for Postgres URI.
Falls back to SQLite if not set.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_storage_url(fallback_path: str = "optuna_studies.db") -> str:
    """Return the Optuna storage URL.

    Priority:
    1. OPTUNA_STORAGE env var (expected: Postgres URI from Docker stack)
    2. SQLite file at fallback_path (relative to CWD)
    """
    env_url = os.environ.get("OPTUNA_STORAGE")
    if env_url:
        return env_url
    logger.warning(
        "OPTUNA_STORAGE not set — falling back to SQLite (%s). "
        "This is NOT suitable for multi-worker optimization.",
        fallback_path,
    )
    return f"sqlite:///{fallback_path}"


def get_storage_type() -> str:
    """Return 'postgres' if OPTUNA_STORAGE is set, otherwise 'sqlite'."""
    return "postgres" if os.environ.get("OPTUNA_STORAGE") else "sqlite"


def require_postgres(storage_url: Optional[str] = None) -> str:
    """Return the storage URL, raising if it's not PostgreSQL.

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
