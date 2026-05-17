"""MFE/MAE computation for a position's intraday path."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

_EPS = 1e-9


@dataclass(frozen=True)
class MFEMAEResult:
    mfe_pct: float
    mae_pct: float
    mfe_dollars: float
    mae_dollars: float
    time_to_mfe_minutes: int
    time_to_mae_minutes: int
    mfe_giveback_pct: float


def compute_mfe_mae(
    *,
    bars: pd.DataFrame,
    entry_time: pd.Timestamp,
    entry_price: float,
    qty: int,
    current_price: float | None = None,
) -> MFEMAEResult:
    """Compute MFE/MAE over a path of bars from entry to current_price (or last bar).

    ``bars`` must include columns ``timestamp``, ``high``, ``low`` and be sorted
    by timestamp. ``current_price`` defaults to the last bar's close.
    """
    if bars.empty:
        return MFEMAEResult(
            mfe_pct=0.0,
            mae_pct=0.0,
            mfe_dollars=0.0,
            mae_dollars=0.0,
            time_to_mfe_minutes=0,
            time_to_mae_minutes=0,
            mfe_giveback_pct=0.0,
        )

    df = bars.sort_values("timestamp")
    df = df[df["timestamp"] >= entry_time]
    if df.empty:
        return MFEMAEResult(0.0, 0.0, 0.0, 0.0, 0, 0, 0.0)

    minutes = ((df["timestamp"] - entry_time).dt.total_seconds() / 60.0).astype(int).reset_index(drop=True)
    highs = df["high"].reset_index(drop=True)
    lows = df["low"].reset_index(drop=True)

    high_cummax = highs.cummax()
    low_cummin = lows.cummin()

    mfe_idx = int(high_cummax.idxmax())
    mae_idx = int(low_cummin.idxmin())

    mfe_pct = float(high_cummax.iloc[mfe_idx]) / entry_price - 1.0
    mae_pct = float(low_cummin.iloc[mae_idx]) / entry_price - 1.0

    time_to_mfe = int(minutes.iloc[mfe_idx])
    time_to_mae = int(minutes.iloc[mae_idx])

    if current_price is None:
        current_price = float(df["close"].iloc[-1] if "close" in df.columns else df["high"].iloc[-1])
    current_return = current_price / entry_price - 1.0

    if mfe_pct <= 0:
        mfe_giveback = 0.0
    else:
        mfe_giveback = (mfe_pct - current_return) / max(mfe_pct, _EPS)

    return MFEMAEResult(
        mfe_pct=mfe_pct,
        mae_pct=mae_pct,
        mfe_dollars=mfe_pct * entry_price * qty,
        mae_dollars=mae_pct * entry_price * qty,
        time_to_mfe_minutes=time_to_mfe,
        time_to_mae_minutes=time_to_mae,
        mfe_giveback_pct=mfe_giveback,
    )
