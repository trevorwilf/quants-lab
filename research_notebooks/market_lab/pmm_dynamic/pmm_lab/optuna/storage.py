"""
Optuna storage resolver.

Reads OPTUNA_STORAGE env var for Postgres URI.
Falls back to SQLite if not set.
"""

import os
from typing import Optional


def get_storage_url(fallback_path: str = "optuna_studies.db") -> str:
    """Return the Optuna storage URL.

    Priority:
    1. OPTUNA_STORAGE env var (expected: Postgres URI from Docker stack)
    2. SQLite file at fallback_path (relative to CWD)
    """
    env_url = os.environ.get("OPTUNA_STORAGE")
    if env_url:
        return env_url
    return f"sqlite:///{fallback_path}"


def get_storage_type() -> str:
    """Return 'postgres' if OPTUNA_STORAGE is set, otherwise 'sqlite'."""
    return "postgres" if os.environ.get("OPTUNA_STORAGE") else "sqlite"
