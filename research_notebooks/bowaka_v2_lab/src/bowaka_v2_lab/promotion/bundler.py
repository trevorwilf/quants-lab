"""Assemble the review package per [Report §9 review-package list].

Writes to ``artifacts/promotion/<run_id>/``:
- run_manifest.json
- config_snapshot.json
- dataset_manifest.json
- data_quality_report.json
- candidate_events.parquet
- entry_decisions.parquet
- trades.parquet
- daily_equity.parquet
- summary.json
- report.md
- optuna_report.md (if present in source run_dir)
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable


REQUIRED_BUNDLE_FILES = (
    "run_manifest.json",
    "config_snapshot.json",
    "dataset_manifest.json",
    "data_quality_report.json",
    "candidate_events.parquet",
    "entry_decisions.parquet",
    "trades.parquet",
    "daily_equity.parquet",
    "summary.json",
    "report.md",
)

OPTIONAL_BUNDLE_FILES = ("optuna_report.md",)


def bundle_review_package(
    *,
    source_run_dir: Path,
    promotion_root: Path,
    run_id: str | None = None,
) -> Path:
    """Copy required + optional bundle files into ``promotion_root/<run_id>/``.

    Raises ``FileNotFoundError`` if any required file is missing from source.
    """
    src = Path(source_run_dir)
    if not src.is_dir():
        raise FileNotFoundError(f"source run_dir does not exist: {src}")
    rid = run_id or src.name
    out = Path(promotion_root) / rid
    out.mkdir(parents=True, exist_ok=True)
    missing = []
    for fname in REQUIRED_BUNDLE_FILES:
        s = src / fname
        if not s.is_file():
            missing.append(fname)
            continue
        shutil.copy2(s, out / fname)
    if missing:
        raise FileNotFoundError(f"required bundle files missing from {src}: {missing}")
    for fname in OPTIONAL_BUNDLE_FILES:
        s = src / fname
        if s.is_file():
            shutil.copy2(s, out / fname)
    return out
