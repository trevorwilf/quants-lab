"""Group counterfactual outcomes by variant fields and summarize PnL distributions."""

from __future__ import annotations

import json

import pandas as pd


def flatten_variant_column(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten a ``variant`` column into top-level columns.

    Accepts either dict variants (in-memory frames from notebook 05/06) or
    JSON-string variants (frames read back from parquet, where
    ``utils.io.to_parquet_safe`` serialized dict columns to strings so Arrow
    could write them). The two cases produce the same flattened result.

    Public so notebooks can pre-flatten frames before passing them to the
    renderer, eliminating the dependency on a freshly-loaded
    ``bucket_analysis`` module inside long-lived Jupyter kernels.
    """
    if df is None or "variant" not in df.columns or df["variant"].empty:
        return df
    if df["variant"].dtype != object:
        return df
    sample = df["variant"].iloc[0]
    if isinstance(sample, dict):
        records = df["variant"].tolist()
    elif isinstance(sample, str):
        records = [
            json.loads(s) if isinstance(s, str) and s else {} for s in df["variant"]
        ]
    else:
        return df
    v = pd.json_normalize(records)
    v.index = df.index
    return pd.concat([df.drop(columns=["variant"]), v], axis=1)


# Backwards-compat: internal callers still use _variant_columns.
_variant_columns = flatten_variant_column


def summarize_by_entry_rule(outcomes: pd.DataFrame) -> pd.DataFrame:
    df = _variant_columns(outcomes)
    if df.empty or "entry_rule" not in df.columns:
        return pd.DataFrame(columns=["entry_rule", "n", "win_rate", "mean_pnl_pct", "median_pnl_pct", "stop_first_rate", "target_first_rate"])
    entered = df[df["would_enter"]] if "would_enter" in df.columns else df
    out = (
        entered.groupby("entry_rule")
        .agg(
            n=("pnl_pct", "size"),
            win_rate=("pnl_pct", lambda s: float((s > 0).mean())),
            mean_pnl_pct=("pnl_pct", "mean"),
            median_pnl_pct=("pnl_pct", "median"),
        )
        .reset_index()
    )
    if "first_touch" in entered.columns:
        first_touch = entered.groupby(["entry_rule", "first_touch"]).size().unstack(fill_value=0)
        for col in ("target", "stop"):
            if col not in first_touch.columns:
                first_touch[col] = 0
        total = first_touch.sum(axis=1).replace(0, 1)
        first_touch["target_first_rate"] = first_touch["target"] / total
        first_touch["stop_first_rate"] = first_touch["stop"] / total
        out = out.merge(
            first_touch[["target_first_rate", "stop_first_rate"]].reset_index(),
            on="entry_rule",
            how="left",
        )
    return out


def summarize_by_exit_geometry(outcomes: pd.DataFrame) -> pd.DataFrame:
    df = _variant_columns(outcomes)
    if df.empty or "stop_pct" not in df.columns or "target_pct" not in df.columns:
        return pd.DataFrame()
    entered = df[df["would_enter"]] if "would_enter" in df.columns else df
    return (
        entered.groupby(["stop_pct", "target_pct"])
        .agg(
            n=("pnl_pct", "size"),
            mean_pnl_pct=("pnl_pct", "mean"),
            median_pnl_pct=("pnl_pct", "median"),
            win_rate=("pnl_pct", lambda s: float((s > 0).mean())),
        )
        .reset_index()
    )


def summarize_by_signal_fade_threshold(outcomes: pd.DataFrame) -> pd.DataFrame:
    df = _variant_columns(outcomes)
    if df.empty or "signal_fade_threshold" not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby("signal_fade_threshold", dropna=False)
        .agg(
            n=("pnl_pct", "size"),
            mean_pnl_pct=("pnl_pct", "mean"),
            median_pnl_pct=("pnl_pct", "median"),
        )
        .reset_index()
    )
