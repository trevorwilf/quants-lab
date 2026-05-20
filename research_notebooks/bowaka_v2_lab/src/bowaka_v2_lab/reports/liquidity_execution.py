"""ADV-bucket / spread-bucket / time-of-day buckets; slippage distribution."""
from __future__ import annotations

import pandas as pd


def adv_bucket_distribution(decisions: pd.DataFrame, *, key: str = "risk_snapshot.candidate_adv") -> pd.DataFrame:
    if key not in decisions.columns:
        return pd.DataFrame({"adv_bucket": [], "count": []})
    buckets = pd.cut(
        decisions[key].fillna(0),
        bins=[0, 250_000, 500_000, 1_000_000, 5_000_000, 20_000_000, float("inf")],
        labels=["<250k", "250k_500k", "500k_1M", "1M_5M", "5M_20M", "20M+"],
    )
    return buckets.value_counts().sort_index().reset_index().rename(
        columns={"index": "adv_bucket", key: "adv_bucket", 0: "count", "count": "count"}
    )


def spread_bucket_distribution(decisions: pd.DataFrame, *, key: str = "quote.spread_pct") -> pd.DataFrame:
    if key not in decisions.columns:
        return pd.DataFrame({"spread_bucket": [], "count": []})
    pcts = decisions[key].fillna(0) * 10_000.0  # bps
    buckets = pd.cut(pcts, bins=[0, 5, 10, 25, 50, 100, float("inf")],
                       labels=["0-5bp", "5-10bp", "10-25bp", "25-50bp", "50-100bp", "100bp+"])
    return buckets.value_counts().sort_index().reset_index().rename(
        columns={"index": "spread_bucket", key: "spread_bucket", 0: "count", "count": "count"}
    )


def time_of_day_buckets(decisions: pd.DataFrame, *, key: str = "decision_timestamp") -> pd.DataFrame:
    if key not in decisions.columns:
        return pd.DataFrame({"tod_bucket": [], "count": []})
    ts = pd.to_datetime(decisions[key], utc=True, errors="coerce")
    et = ts.dt.tz_convert("America/New_York")
    minute_of_day = (et.dt.hour - 9) * 60 + (et.dt.minute - 30)
    buckets = pd.cut(minute_of_day, bins=[0, 15, 60, 180, 330, 390],
                       labels=["open15", "first_hour", "morning", "afternoon", "closing"])
    return buckets.value_counts().sort_index().reset_index().rename(
        columns={"index": "tod_bucket", 0: "count", "count": "count"}
    )
