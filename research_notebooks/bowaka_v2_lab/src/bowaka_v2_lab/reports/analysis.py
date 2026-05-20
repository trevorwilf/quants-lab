"""Port of bowaka_v2_analysis.py — run-id scoped analysis helpers."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def load_run_artifacts(run_dir: Path) -> dict:
    """Read the standard artifacts written by ``sim.backtester.run_backtest``."""
    run_dir = Path(run_dir)
    out: dict = {}
    for fname in ("run_manifest.json", "summary.json", "dataset_manifest.json", "code_manifest.json"):
        p = run_dir / fname
        if p.is_file():
            out[fname.replace(".json", "")] = json.loads(p.read_text(encoding="utf-8"))
    for fname in ("trades", "entry_decisions", "candidate_events", "daily_equity"):
        p = run_dir / f"{fname}.parquet"
        if p.is_file():
            try:
                out[fname] = pd.read_parquet(p)
            except Exception:
                out[fname] = pd.DataFrame()
    return out
