"""Optuna storage URL resolver."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class StorageSpec:
    url: str
    requires_n_jobs_1: bool


def resolve_storage(url: str | None = None) -> StorageSpec:
    """Pick a storage URL. SQLite forces n_jobs=1 (per [Report §19] and CLAUDE.md)."""
    if url is None:
        url = os.environ.get("BOWAKA_OPTUNA_STORAGE", "sqlite:///bowaka_optuna.db")
    requires_n_jobs_1 = url.startswith("sqlite:")
    return StorageSpec(url=url, requires_n_jobs_1=requires_n_jobs_1)
