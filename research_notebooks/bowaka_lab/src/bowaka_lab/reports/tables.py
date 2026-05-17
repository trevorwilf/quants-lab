"""Summary table builders for the weekly report.

Each function takes a tidy DataFrame and returns a tidy summary DataFrame that
is safe to serialize to both CSV and Parquet.
"""

from __future__ import annotations

import pandas as pd


def candidate_funnel(metadata: dict) -> pd.DataFrame:
    """Render the prefilter funnel as a 5-row DataFrame.

    Accepts either key style for back-compat:

    - Aggregated funnel from
      ``bowaka_lab.features.prefilter.aggregate_prefilter_funnel`` —
      ``universe_with_features``, ``passed_universe_gates``, ``candidates``,
      ``rejected_by_signal_gates``, ``excluded_by_instrument_class``.
    - Single-session ``CandidateSet.metadata`` style with ``n_`` prefixes.
    """
    m = metadata or {}

    def _get(stage: str) -> int:
        return int(m.get(stage, m.get(f"n_{stage}", 0)) or 0)

    return pd.DataFrame(
        [
            {"stage": "universe_with_features", "count": _get("universe_with_features")},
            {"stage": "passed_universe_gates", "count": _get("passed_universe_gates")},
            {"stage": "candidates", "count": _get("candidates")},
            {"stage": "rejected_by_signal_gates", "count": _get("rejected_by_signal_gates")},
            {"stage": "excluded_by_instrument_class", "count": _get("excluded_by_instrument_class")},
        ]
    )


def trade_summary(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame([{"trade_count": 0, "win_rate": 0.0, "mean_pnl_pct": 0.0, "total_pnl": 0.0}])
    wins = (trades.get("pnl", trades.get("pnl_pct", pd.Series(dtype=float))) > 0).sum()
    return pd.DataFrame(
        [
            {
                "trade_count": int(trades.shape[0]),
                "win_rate": float(wins / max(1, trades.shape[0])),
                "mean_pnl_pct": float(trades["pnl_pct"].mean()) if "pnl_pct" in trades else 0.0,
                "total_pnl": float(trades["pnl"].sum()) if "pnl" in trades else 0.0,
            }
        ]
    )


def exit_reasons(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty or "exit_reason" not in trades.columns:
        return pd.DataFrame(columns=["exit_reason", "count", "pct"])
    counts = trades["exit_reason"].value_counts().reset_index()
    counts.columns = ["exit_reason", "count"]
    counts["pct"] = counts["count"] / counts["count"].sum()
    return counts


def mfe_mae_buckets(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty or "mfe_pct" not in trades.columns:
        return pd.DataFrame(columns=["bucket", "count", "median_pnl_pct"])
    bins = [-1.0, 0.0, 0.05, 0.10, 0.20, 100.0]
    labels = ["loss", "0-5%", "5-10%", "10-20%", ">=20%"]
    df = trades.copy()
    df["mfe_bucket"] = pd.cut(df["mfe_pct"], bins=bins, labels=labels, include_lowest=True)
    grouped = df.groupby("mfe_bucket", observed=False).agg(count=("mfe_pct", "size"), median_pnl_pct=("pnl_pct", "median")).reset_index()
    grouped = grouped.rename(columns={"mfe_bucket": "bucket"})
    return grouped


def entry_counterfactual_grid(outcomes: pd.DataFrame) -> pd.DataFrame:
    from bowaka_lab.metrics.bucket_analysis import summarize_by_entry_rule

    return summarize_by_entry_rule(outcomes)


def exit_counterfactual_grid(outcomes: pd.DataFrame) -> pd.DataFrame:
    from bowaka_lab.metrics.bucket_analysis import summarize_by_exit_geometry

    return summarize_by_exit_geometry(outcomes)


def signal_fade_thresholds(outcomes: pd.DataFrame) -> pd.DataFrame:
    from bowaka_lab.metrics.bucket_analysis import summarize_by_signal_fade_threshold

    return summarize_by_signal_fade_threshold(outcomes)


def liquidity_buckets(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty or "notional" not in trades.columns:
        return pd.DataFrame(columns=["bucket", "count"])
    bins = [0, 1000, 5000, 10000, 50000, 1_000_000]
    labels = ["<1k", "1k-5k", "5k-10k", "10k-50k", ">=50k"]
    df = trades.copy()
    df["notional_bucket"] = pd.cut(df["notional"], bins=bins, labels=labels, include_lowest=True)
    return df.groupby("notional_bucket", observed=False).agg(count=("notional", "size")).reset_index().rename(columns={"notional_bucket": "bucket"})


def paper_vs_backtest_summary(reconciliation: pd.DataFrame) -> pd.DataFrame:
    if reconciliation.empty:
        return pd.DataFrame(columns=["classification", "count", "pct"])
    counts = reconciliation["classification"].value_counts().reset_index()
    counts.columns = ["classification", "count"]
    counts["pct"] = counts["count"] / counts["count"].sum()
    return counts
