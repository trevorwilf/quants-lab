"""Group counterfactual outcomes by variant fields and summarize PnL distributions."""

from __future__ import annotations

import pandas as pd


def _variant_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "variant" not in df.columns:
        return df
    if df["variant"].dtype == object and isinstance(df["variant"].iloc[0], dict):
        v = pd.json_normalize(df["variant"])
        v.index = df.index
        return pd.concat([df.drop(columns=["variant"]), v], axis=1)
    return df


def summarize_by_entry_rule(outcomes: pd.DataFrame) -> pd.DataFrame:
    df = _variant_columns(outcomes)
    if df.empty:
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
    if df.empty:
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
