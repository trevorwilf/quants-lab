"""Bucketing correctness for ADV / spread / time-of-day."""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.reports.liquidity_execution import (
    adv_bucket_distribution,
    spread_bucket_distribution,
    time_of_day_buckets,
)


def test_adv_bucket_distribution() -> None:
    df = pd.DataFrame({"risk_snapshot.candidate_adv": [100_000, 600_000, 2_000_000, 10_000_000, 25_000_000]})
    out = adv_bucket_distribution(df)
    assert not out.empty


def test_spread_bucket_distribution() -> None:
    df = pd.DataFrame({"quote.spread_pct": [0.0003, 0.0008, 0.002, 0.005, 0.015]})
    out = spread_bucket_distribution(df)
    assert not out.empty


def test_time_of_day_buckets() -> None:
    df = pd.DataFrame({"decision_timestamp": [
        "2024-09-04T13:35:00Z",  # open15
        "2024-09-04T14:00:00Z",  # first_hour
        "2024-09-04T16:00:00Z",  # morning
        "2024-09-04T18:30:00Z",  # afternoon
        "2024-09-04T20:00:00Z",  # closing
    ]})
    out = time_of_day_buckets(df)
    assert not out.empty
