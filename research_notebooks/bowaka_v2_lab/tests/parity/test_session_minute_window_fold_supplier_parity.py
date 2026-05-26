"""Fold context with session-window cache produces identical supplier output.

Speedup report v2 §4 P3 / §5.7 / Phase 4 task 6. With
``optuna.acceleration.session_minute_window_cache.enabled=True`` AND
``cached_suppliers=True`` the fold context's ``suppliers.minute`` callable
returns the same per-(symbol, scan_ts) frames as the legacy
``make_lake_suppliers`` minute supplier.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake
from bowaka_v2_lab.optuna.fold_context import build_fold_contexts
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits


def _make_cfg(lake: Path, symbols: list[str], *, enable: bool) -> dict:
    return {
        "simulation": {"mode": "smoke_fixture"},
        "market_data": {
            "feed": "iex", "shared_root": str(lake), "minute_bar_source": "fixture",
        },
        "universe": {"symbols": symbols, "min_adv_dollars": 0,
                     "min_price": 1.0, "max_price": 1_000.0},
        "backtest": {"start_date": "2024-01-01", "end_date": "2024-04-01",
                     "cost_stress": "conservative"},
        "optuna": {
            "n_trials": 1, "n_jobs": 1,
            "cached_suppliers": True,  # Phase 4 wraps the minute supplier on top.
            "walkforward": {"train_months": 1, "val_months": 1,
                            "final_holdout_months": 1},
            "acceleration": {
                "session_minute_window_cache": {"enabled": bool(enable)},
            },
        },
    }


def test_fold_context_minute_supplier_parity_with_session_window_cache(
    tmp_path: Path,
) -> None:
    lake = tmp_path / "lake"
    symbols = ["AAA"]
    build_tiny_lake(lake, symbols, start=dt.date(2024, 1, 1), end=dt.date(2024, 4, 1))
    plan = build_walkforward_splits(
        full_start=dt.date(2024, 1, 1), full_end=dt.date(2024, 4, 1),
        train_months=1, val_months=1, final_holdout_months=1,
    )
    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)

    ctxs_off = build_fold_contexts(
        _make_cfg(lake, symbols, enable=False), plan, lake_root=lake,
        feed="iex", symbols=symbols, paths=paths, holdout_guard=holdout_guard,
    )
    ctxs_on = build_fold_contexts(
        _make_cfg(lake, symbols, enable=True), plan, lake_root=lake,
        feed="iex", symbols=symbols, paths=paths, holdout_guard=holdout_guard,
    )

    for off, on in zip(ctxs_off, ctxs_on):
        if off is None and on is None:
            continue
        # Probe each session at a mid-session timestamp.
        for s in off.sessions:
            cutoff = pd.Timestamp(
                dt.datetime.combine(s, dt.time(hour=10, minute=30)),
                tz="America/New_York",
            ).tz_convert("UTC")
            a = off.suppliers.minute("AAA", cutoff).reset_index(drop=True)
            b = on.suppliers.minute("AAA", cutoff).reset_index(drop=True)
            assert list(a.columns) == list(b.columns), s
            assert len(a) == len(b), (
                f"row count differs at {s}: off={len(a)} on={len(b)}"
            )
            for col in a.columns:
                for va, vb in zip(a[col].tolist(), b[col].tolist()):
                    assert va == vb, f"{s} {col}: off={va!r} on={vb!r}"
