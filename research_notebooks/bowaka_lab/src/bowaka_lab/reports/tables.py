"""Summary table builders for the weekly report.

Each function takes a tidy DataFrame and returns a tidy summary DataFrame that
is safe to serialize to both CSV and Parquet.
"""

from __future__ import annotations

import pandas as pd


def candidate_rank_distribution(candidates: pd.DataFrame) -> pd.DataFrame:
    """Summarize candidates.parquet for Section 6.

    Returns a tidy frame with one row per rank bucket (1-50, 51-100, etc.)
    showing the count of candidates and the median signal_strength in that
    bucket. Buckets above the observed max are dropped so the table stays
    informative on small runs.
    """
    if candidates is None or candidates.empty or "rank" not in candidates.columns:
        return pd.DataFrame(columns=["rank_bucket", "candidates", "median_signal_strength"])
    bins = [0, 50, 100, 200, 500, 1000, float("inf")]
    labels = ["1-50", "51-100", "101-200", "201-500", "501-1000", "1000+"]
    df = candidates.copy()
    df["rank_bucket"] = pd.cut(df["rank"], bins=bins, labels=labels, include_lowest=True)
    agg = (
        df.groupby("rank_bucket", observed=False)
        .agg(
            candidates=("rank", "size"),
            median_signal_strength=("signal_strength", "median")
            if "signal_strength" in df.columns
            else ("rank", "size"),
        )
        .reset_index()
    )
    # Trim empty trailing buckets so the table is compact.
    agg = agg[agg["candidates"] > 0].reset_index(drop=True)
    agg["rank_bucket"] = agg["rank_bucket"].astype(str)
    return agg


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


def signal_fade_bucket_distribution(evaluations: pd.DataFrame) -> pd.DataFrame:
    """Summarize notebook 07's per-trade signal-fade evaluations.

    Expects the schema written by notebook 07:
    ``[trade_id, symbol, trade_date, eval_label, eval_time, score, bucket,
       current_price, current_return_pct, mfe_pct, triggered_components]``.

    Returns a tidy bucket-x-eval_label grid so the weekly report can show
    how the fade scoreboard looks at RTH eval vs after-close eval.
    """
    if evaluations is None or evaluations.empty or "bucket" not in evaluations.columns:
        return pd.DataFrame(columns=["bucket", "eval_label", "trades", "mean_score"])
    group_cols = ["bucket"]
    if "eval_label" in evaluations.columns:
        group_cols.append("eval_label")
    out = (
        evaluations.groupby(group_cols, dropna=False)
        .agg(
            trades=("trade_id", "size") if "trade_id" in evaluations.columns else ("bucket", "size"),
            mean_score=("score", "mean") if "score" in evaluations.columns else ("bucket", "size"),
        )
        .reset_index()
    )
    bucket_order = ["none", "soft", "hard", "critical"]
    out["bucket"] = pd.Categorical(out["bucket"], categories=bucket_order, ordered=True)
    sort_cols = ["bucket"] + (["eval_label"] if "eval_label" in out.columns else [])
    out = out.sort_values(sort_cols).reset_index(drop=True)
    out["bucket"] = out["bucket"].astype(str)
    return out


def liquidity_buckets(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty or "notional" not in trades.columns:
        return pd.DataFrame(columns=["bucket", "count"])
    bins = [0, 1000, 5000, 10000, 50000, 1_000_000]
    labels = ["<1k", "1k-5k", "5k-10k", "10k-50k", ">=50k"]
    df = trades.copy()
    df["notional_bucket"] = pd.cut(df["notional"], bins=bins, labels=labels, include_lowest=True)
    return df.groupby("notional_bucket", observed=False).agg(count=("notional", "size")).reset_index().rename(columns={"notional_bucket": "bucket"})


def optuna_top_trials(trials: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return the top-N completed Optuna trials sorted by objective value.

    Notebook 10 writes ``optuna_trials.parquet`` with columns
    ``trial_number``, ``objective_value``, ``state``, plus a ``param_<name>``
    column for each search-space dimension. We keep ``trial_number`` and
    ``objective_value`` up front and append each parameter column so the
    weekly report shows what tuning the best trials used.
    """
    if trials is None or trials.empty or "objective_value" not in trials.columns:
        return pd.DataFrame(columns=["trial_number", "objective_value"])
    completed = trials
    if "state" in trials.columns:
        completed = trials[trials["state"].astype(str).str.upper().str.contains("COMPLETE")]
        if completed.empty:
            completed = trials
    out = completed.dropna(subset=["objective_value"])
    if out.empty:
        return pd.DataFrame(columns=["trial_number", "objective_value"])
    out = out.sort_values("objective_value", ascending=False).head(n)
    cols = ["trial_number", "objective_value"]
    cols += [c for c in out.columns if c.startswith("param_")]
    return out[cols].reset_index(drop=True)


def paper_vs_backtest_summary(reconciliation: pd.DataFrame) -> pd.DataFrame:
    if reconciliation.empty:
        return pd.DataFrame(columns=["classification", "count", "pct"])
    counts = reconciliation["classification"].value_counts().reset_index()
    counts.columns = ["classification", "count"]
    counts["pct"] = counts["count"] / counts["count"].sum()
    return counts
