"""Run-ID generation for bowaka_v2_lab.

Format (deterministic given inputs): ``{YYYYMMDD}_bowaka_v2_{kind}_{cfg_hash8}_{ds_hash8}``.
"""
from __future__ import annotations

import datetime as _dt
from typing import Optional


_KIND_ALLOWED = {"backtest", "replay", "smoke", "optuna", "reconcile", "scanner", "universe"}


def generate_run_id(
    *,
    kind: str,
    cfg_hash: str,
    dataset_hash: str,
    on_date: Optional[_dt.date] = None,
) -> str:
    if kind not in _KIND_ALLOWED:
        raise ValueError(f"unknown run kind {kind!r}; allowed: {sorted(_KIND_ALLOWED)}")
    if not cfg_hash or len(cfg_hash) < 8:
        raise ValueError("cfg_hash must be at least 8 hex chars")
    if not dataset_hash or len(dataset_hash) < 8:
        raise ValueError("dataset_hash must be at least 8 hex chars")
    d = on_date if on_date is not None else _dt.date.today()
    return f"{d:%Y%m%d}_bowaka_v2_{kind}_{cfg_hash[:8]}_{dataset_hash[:8]}"
