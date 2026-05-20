"""Counterfactual harness: swap out exits / holds while keeping entries fixed."""
from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping

import pandas as pd


def run_counterfactual_grid(
    *,
    base_cfg: Mapping[str, Any],
    exit_variants: Iterable[Mapping[str, Any]],
    backtest_runner: Callable[[dict], dict],
) -> pd.DataFrame:
    """For each variant in ``exit_variants``, run a backtest with the same entries but
    different exit parameters. Returns a comparison DataFrame.
    """
    rows = []
    for i, variant in enumerate(exit_variants):
        cfg = dict(base_cfg)
        exits = dict(cfg.get("exits") or {})
        exits.update(variant)
        cfg["exits"] = exits
        summary = backtest_runner(cfg)
        rows.append({"variant_idx": i, **dict(variant), **summary})
    return pd.DataFrame(rows)
