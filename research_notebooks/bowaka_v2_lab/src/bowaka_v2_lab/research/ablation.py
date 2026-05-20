"""Ablation harness: run the backtest with subsets of gates disabled."""
from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping

import pandas as pd


def run_ablation_grid(
    *,
    base_cfg: Mapping[str, Any],
    gate_ablations: Iterable[str],
    backtest_runner: Callable[[dict], dict],
) -> pd.DataFrame:
    """For each gate in ``gate_ablations``, disable that gate (set its threshold to None)
    and run the backtest. Returns a comparison DataFrame.

    ``backtest_runner(cfg) -> summary_dict`` is the injection point.
    """
    rows = [{"ablation": "baseline", **backtest_runner(dict(base_cfg))}]
    for gate in gate_ablations:
        cfg = dict(base_cfg)
        signals = dict(cfg.get("signals") or {})
        # Disable the gate by removing or nulling thresholds; convention: "<gate>_min" / "<gate>_max".
        for k in list(signals.keys()):
            if k.startswith(gate):
                signals.pop(k, None)
        cfg["signals"] = signals
        summary = backtest_runner(cfg)
        rows.append({"ablation": gate, **summary})
    return pd.DataFrame(rows)
