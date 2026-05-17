"""Phase 5: persistence round-trip for counterfactual outcomes."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from mongomock import MongoClient

from bowaka_lab.data.mongo_store import MongoStore
from bowaka_lab.sim.counterfactuals import persist_outcomes


def _outcome_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "counterfactual_id": "cf_AAA_2026-05-12_xyz",
                "symbol": "AAA",
                "signal_date": "2026-05-11",
                "trade_date": "2026-05-12",
                "prefilter_rank": 1,
                "passed_actual_prefilter": True,
                "variant": {"entry_rule": "fixed_time_0945", "stop_pct": 0.08, "target_pct": 0.15, "max_hold_days": 3, "signal_fade_threshold": None, "stop_manager_model": "none"},
                "would_enter": True,
                "entry_price": 5.0,
                "exit_price": 5.75,
                "exit_reason": "target_hit",
                "pnl_pct": 0.15,
                "mfe_pct": 0.16,
                "mae_pct": -0.02,
                "first_touch": "target",
                "diagnostics": {},
            }
        ]
    )


def test_parquet_round_trip(tmp_path):
    df = _outcome_rows()
    target = tmp_path / "cf.parquet"
    persist_outcomes(df, parquet_path=target)
    assert target.exists()
    read = pd.read_parquet(target)
    assert read.shape[0] == 1
    assert read.iloc[0]["symbol"] == "AAA"


def test_mongo_insert(tmp_path):
    df = _outcome_rows()
    client = MongoClient()
    store = MongoStore(database="bowaka_lab_test", client=client)
    persist_outcomes(df, mongo_store=store, run_id="bt_test")
    found = list(store.collection("bowaka_counterfactuals").find({}))
    assert len(found) == 1
    assert found[0]["symbol"] == "AAA"
    assert found[0]["backtest_run_id"] == "bt_test"
