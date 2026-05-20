"""Per-trade sim_fill vs paper_fill residual; histogram by ADV/spread bucket."""
from __future__ import annotations

from typing import Iterable

import pandas as pd


def compute_slippage_residuals(
    paper_fills: list[dict],
    sim_fills: list[dict],
) -> pd.DataFrame:
    """Join paper fills to sim fills by (symbol, parent_order_id) and compute residuals.

    residual = paper_fill_price - sim_fill_price  (positive = paper worse for buy)
    """
    if not paper_fills or not sim_fills:
        return pd.DataFrame(columns=["symbol", "paper_fill", "sim_fill", "residual"])
    df_p = pd.DataFrame(paper_fills).rename(columns={"avg_fill_price": "paper_fill"})
    df_s = pd.DataFrame(sim_fills).rename(columns={"avg_fill_price": "sim_fill"})
    join_keys: list[str] = []
    if "parent_order_id" in df_p.columns and "parent_order_id" in df_s.columns:
        join_keys.append("parent_order_id")
    if "symbol" in df_p.columns and "symbol" in df_s.columns:
        join_keys.append("symbol")
    if not join_keys:
        return pd.DataFrame(columns=["symbol", "paper_fill", "sim_fill", "residual"])
    merged = df_p.merge(df_s[join_keys + ["sim_fill"]], on=join_keys, how="inner")
    merged["residual"] = merged["paper_fill"] - merged["sim_fill"]
    cols = [c for c in ("symbol", "parent_order_id", "paper_fill", "sim_fill", "residual") if c in merged.columns]
    return merged[cols]
