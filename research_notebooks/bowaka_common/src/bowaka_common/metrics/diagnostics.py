"""Exit-reason distribution and first-touch counts."""

from __future__ import annotations

import pandas as pd


def exit_reason_distribution(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty or "exit_reason" not in trades.columns:
        return pd.DataFrame(columns=["exit_reason", "count", "pct"])
    counts = trades["exit_reason"].value_counts().reset_index()
    counts.columns = ["exit_reason", "count"]
    counts["pct"] = counts["count"] / counts["count"].sum()
    return counts


def first_touch_summary(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["first_touch", "count"])
    if "first_touch" in trades.columns:
        return trades["first_touch"].value_counts().reset_index().rename(columns={"index": "first_touch", "first_touch": "count"})
    # Derive from exit_reason if first_touch column not populated.
    mapping = {"target_hit": "target", "stop_hit": "stop", "stop_gap": "stop", "ambiguous_bar_stop": "stop", "ambiguous_bar_target": "target"}
    derived = trades["exit_reason"].map(mapping).fillna("none")
    counts = derived.value_counts().reset_index()
    counts.columns = ["first_touch", "count"]
    return counts
