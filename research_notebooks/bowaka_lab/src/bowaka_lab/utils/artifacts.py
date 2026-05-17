"""Shared artifact contract for bowaka_lab research notebooks.

Notebooks under ``research_notebooks/bowaka_lab/notebooks/`` produce and
consume artifacts under
``research_notebooks/bowaka_lab/artifacts/{run_id}/``.

This module is the single source of truth for the artifact layout. Notebook
authors NEVER hardcode artifact paths or filenames — they go through
:class:`ArtifactPaths` instead. Adding a new artifact is a one-line property
addition here plus an entry in the table in
``bowaka_lab_finish_notebooks_claude_code_prompt.md``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from bowaka_lab.utils.io import to_parquet_safe


@dataclass(frozen=True)
class ArtifactPaths:
    """Computed paths for one ``run_id`` under one ``artifacts_root``.

    Example::

        paths = ArtifactPaths.for_run(
            "bt_iex_default",
            Path("research_notebooks/bowaka_lab/artifacts"),
        )
        paths.candidates
        # -> .../artifacts/bt_iex_default/candidates.parquet
    """

    run_id: str
    root: Path

    @classmethod
    def for_run(cls, run_id: str, artifacts_root: Path | str) -> "ArtifactPaths":
        return cls(run_id=run_id, root=Path(artifacts_root) / run_id)

    def ensure_dir(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    # File paths — one property per artifact name. Order mirrors the
    # artifact-contract table in the phase prompt.
    @property
    def config(self) -> Path:
        return self.root / "config.json"

    @property
    def funnel(self) -> Path:
        return self.root / "funnel.json"

    @property
    def candidates(self) -> Path:
        return self.root / "candidates.parquet"

    @property
    def trades(self) -> Path:
        return self.root / "trades.parquet"

    @property
    def summary(self) -> Path:
        return self.root / "summary.json"

    @property
    def cf_entry(self) -> Path:
        return self.root / "cf_entry.parquet"

    @property
    def cf_exit(self) -> Path:
        return self.root / "cf_exit.parquet"

    @property
    def signal_fade(self) -> Path:
        return self.root / "signal_fade.parquet"

    @property
    def liquidity(self) -> Path:
        return self.root / "liquidity_buckets.parquet"

    @property
    def reconciliation(self) -> Path:
        return self.root / "reconciliation.parquet"

    @property
    def optuna_trials(self) -> Path:
        return self.root / "optuna_trials.parquet"

    @property
    def optuna_best(self) -> Path:
        return self.root / "optuna_best.json"

    @property
    def weekly_report_md(self) -> Path:
        return self.root / "weekly_report.md"

    @property
    def weekly_report_json(self) -> Path:
        return self.root / "weekly_report.json"


# ---------------------------------------------------------------------------
# Generic read/write helpers
# ---------------------------------------------------------------------------


def save_json(path: Path, data: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_parquet(path: Path, df: pd.DataFrame) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    to_parquet_safe(df, path)


def load_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def artifact_exists(paths: ArtifactPaths, name: str) -> bool:
    """Check if a named artifact exists. ``name`` matches the property name
    on :class:`ArtifactPaths` (e.g. ``"candidates"``, ``"trades"``).

    Returns ``False`` for unknown names and for paths that don't exist on disk.
    """
    attr = getattr(paths, name, None)
    if attr is None:
        return False
    return Path(attr).exists()
