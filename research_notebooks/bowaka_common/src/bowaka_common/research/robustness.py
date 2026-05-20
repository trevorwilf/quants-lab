"""Robustness checks: top-k convergence and parameter sensitivity scoring."""

from __future__ import annotations

import math

import pandas as pd


def topk_convergence(trial_scores: pd.DataFrame, *, k: int = 10) -> dict:
    """Measure how much top-k trial parameters agree.

    ``trial_scores`` must have ``trial_id``, ``score``, and parameter columns.
    """
    if trial_scores.empty:
        return {"k": k, "converged": False, "spread_ratio": 0.0}
    top = trial_scores.sort_values("score", ascending=False).head(k)
    if "score" not in top.columns or top["score"].iloc[0] == 0:
        return {"k": k, "converged": False, "spread_ratio": 0.0}
    spread = (top["score"].max() - top["score"].min()) / max(abs(top["score"].iloc[0]), 1e-9)
    converged = spread < 0.10  # within 10% of the best score
    return {"k": k, "converged": bool(converged), "spread_ratio": float(spread)}


def parameter_sensitivity(trial_scores: pd.DataFrame, *, param_columns: list[str]) -> pd.DataFrame:
    if trial_scores.empty:
        return pd.DataFrame(columns=["param", "std_score_top_quartile", "median_score_top_quartile"])
    df = trial_scores.copy()
    threshold = df["score"].quantile(0.75)
    top = df[df["score"] >= threshold]
    rows = []
    for col in param_columns:
        if col not in top.columns:
            continue
        rows.append(
            {
                "param": col,
                "std_score_top_quartile": float(top[col].astype(float).std(ddof=0)) if pd.api.types.is_numeric_dtype(top[col]) else float("nan"),
                "median_score_top_quartile": float(top[col].astype(float).median()) if pd.api.types.is_numeric_dtype(top[col]) else float("nan"),
            }
        )
    return pd.DataFrame(rows)
