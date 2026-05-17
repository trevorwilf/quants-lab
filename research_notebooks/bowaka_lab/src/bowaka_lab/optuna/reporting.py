"""Study-level reporting: trial ranking, top-k clustering, sensitivity plots."""

from __future__ import annotations

from typing import Any

import optuna
import pandas as pd


def trials_dataframe(study: optuna.study.Study) -> pd.DataFrame:
    if not study.trials:
        return pd.DataFrame()
    rows = []
    for t in study.trials:
        if t.state.name != "COMPLETE":
            continue
        row = {"trial_id": t.number, "score": t.value}
        for k, v in t.params.items():
            row[k] = v
        rows.append(row)
    return pd.DataFrame(rows)


def ranked_trials(study: optuna.study.Study, *, top_k: int = 10) -> pd.DataFrame:
    df = trials_dataframe(study)
    if df.empty:
        return df
    return df.sort_values("score", ascending=False).head(top_k).reset_index(drop=True)


def walkforward_heatmap_data(fold_scores: pd.DataFrame) -> pd.DataFrame:
    """Pivot fold×trial scores for a heatmap-ready table."""
    if fold_scores.empty:
        return fold_scores
    if {"fold", "trial_id", "test_score"} - set(fold_scores.columns):
        return pd.DataFrame()
    return fold_scores.pivot(index="trial_id", columns="fold", values="test_score")
