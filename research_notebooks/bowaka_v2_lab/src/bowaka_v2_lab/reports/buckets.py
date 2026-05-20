"""Port of bowaka_v2_bucket_analysis.py — generic bucket helpers."""
from __future__ import annotations

from typing import Sequence

import pandas as pd


def bucket_by_quantile(values: pd.Series, *, n_buckets: int = 5) -> pd.Series:
    return pd.qcut(values, q=n_buckets, duplicates="drop", labels=False)


def bucket_summary(df: pd.DataFrame, value_col: str, bucket_col: str) -> pd.DataFrame:
    if df.empty or bucket_col not in df.columns:
        return pd.DataFrame()
    return df.groupby(bucket_col)[value_col].agg(["count", "mean", "std", "min", "max"]).reset_index()
