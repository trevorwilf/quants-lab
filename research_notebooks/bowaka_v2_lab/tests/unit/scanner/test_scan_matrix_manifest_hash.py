"""`compute_matrix_input_hash` is stable under irrelevant cfg changes.

Matrix doc §8.1 / Phase 8. The hash must:

* change when ANY matrix-input (feed, scanner cadence, universe filter,
  historical_features, intraday_window_policy) changes;
* remain stable when ONLY a trial-tuned key (signals/sizing/risk/
  execution/exits) changes — the matrix is reusable across trials in
  one study.
"""
from __future__ import annotations

import datetime as dt

import pytest

from bowaka_v2_lab.scanner.scan_matrix import compute_matrix_input_hash


def _base_cfg() -> dict:
    return {
        "market_data": {"feed": "iex", "shared_root": "/tmp/lake",
                         "adjustment": "raw"},
        "backtest": {"start_date": "2024-01-01", "end_date": "2024-05-01"},
        "session": {"scanner_start": "09:45", "scanner_end": "16:00",
                     "scan_interval_seconds": 60},
        "simulation": {"intraday_window_policy": "scanner_start_to_scan"},
        "universe": {"min_price": 1.0, "max_price": 20.0,
                      "min_adv_dollars": 250_000.0},
        "historical_features": {"volume_curve": {"bucket_edges": [250_000]}},
        "optuna": {"walkforward": {"train_months": 21, "val_months": 1,
                                     "final_holdout_months": 5}},
    }


_PLAN = type("FakePlan", (), {"splits": []})()
_SESSIONS = {"validation": [dt.date(2024, 1, 2)]}


def test_hash_stable_under_signals_change():
    cfg_a = _base_cfg()
    cfg_b = _base_cfg()
    cfg_b["signals"] = {"gap_pct_max": 0.05}
    h1 = compute_matrix_input_hash(cfg_a, _PLAN, _SESSIONS, dataset_hash="ds")
    h2 = compute_matrix_input_hash(cfg_b, _PLAN, _SESSIONS, dataset_hash="ds")
    assert h1 == h2, "signals.* must not change the matrix hash"


def test_hash_stable_under_sizing_change():
    cfg_a = _base_cfg()
    cfg_b = _base_cfg()
    cfg_b["sizing"] = {"dollars_per_position": 999}
    h1 = compute_matrix_input_hash(cfg_a, _PLAN, _SESSIONS, dataset_hash="ds")
    h2 = compute_matrix_input_hash(cfg_b, _PLAN, _SESSIONS, dataset_hash="ds")
    assert h1 == h2


def test_hash_changes_when_feed_changes():
    cfg_a = _base_cfg()
    cfg_b = _base_cfg()
    cfg_b["market_data"]["feed"] = "sip"
    h1 = compute_matrix_input_hash(cfg_a, _PLAN, _SESSIONS, dataset_hash="ds")
    h2 = compute_matrix_input_hash(cfg_b, _PLAN, _SESSIONS, dataset_hash="ds")
    assert h1 != h2


def test_hash_changes_when_intraday_window_policy_changes():
    cfg_a = _base_cfg()
    cfg_b = _base_cfg()
    cfg_b["simulation"]["intraday_window_policy"] = "regular_open_to_scan"
    h1 = compute_matrix_input_hash(cfg_a, _PLAN, _SESSIONS, dataset_hash="ds")
    h2 = compute_matrix_input_hash(cfg_b, _PLAN, _SESSIONS, dataset_hash="ds")
    assert h1 != h2


def test_hash_changes_when_universe_filter_changes():
    cfg_a = _base_cfg()
    cfg_b = _base_cfg()
    cfg_b["universe"]["min_price"] = 5.0
    h1 = compute_matrix_input_hash(cfg_a, _PLAN, _SESSIONS, dataset_hash="ds")
    h2 = compute_matrix_input_hash(cfg_b, _PLAN, _SESSIONS, dataset_hash="ds")
    assert h1 != h2


def test_hash_changes_when_historical_features_change():
    cfg_a = _base_cfg()
    cfg_b = _base_cfg()
    cfg_b["historical_features"]["volume_curve"]["bucket_edges"] = [999]
    h1 = compute_matrix_input_hash(cfg_a, _PLAN, _SESSIONS, dataset_hash="ds")
    h2 = compute_matrix_input_hash(cfg_b, _PLAN, _SESSIONS, dataset_hash="ds")
    assert h1 != h2


def test_hash_changes_with_dataset_hash():
    cfg = _base_cfg()
    h1 = compute_matrix_input_hash(cfg, _PLAN, _SESSIONS, dataset_hash="a")
    h2 = compute_matrix_input_hash(cfg, _PLAN, _SESSIONS, dataset_hash="b")
    assert h1 != h2
