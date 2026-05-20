"""Canonical hashing: key-order invariance + strategy-vs-run hash separation."""
from __future__ import annotations

from bowaka_v2_lab.config.hashing import canonical_run_hash, canonical_strategy_hash


_BASE_CFG = {
    "strategy_id": "bowaka_v2",
    "strategy_version": "0.1.0",
    "market_data": {"feed": "iex"},
    "signals": {"min_signal_strength": 0.5},
    "execution": {"limit_offset_bps": 5},
    "sizing": {"dollars_per_position": 1000},
    "risk": {"max_concurrent_positions": 5},
    "exits": {"stop_loss_pct": 0.02},
    "scanner": {"max_entries_per_scan": 3},
    "session": {"calendar": "XNYS"},
    "universe": {"min_price": 1.0},
    "paths": {
        "lab_root": "research_notebooks/bowaka_v2_lab",
        "data_root": "research_notebooks/bowaka_v2_lab/data",
        "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
    },
    "run": {"kind": "backtest", "seed": 1337},
}


def test_strategy_hash_stable_across_key_order() -> None:
    a = canonical_strategy_hash(_BASE_CFG)
    cfg2 = {k: _BASE_CFG[k] for k in reversed(list(_BASE_CFG.keys()))}
    b = canonical_strategy_hash(cfg2)
    assert a == b


def test_run_hash_changes_when_paths_change() -> None:
    cfg2 = {**_BASE_CFG, "paths": {**_BASE_CFG["paths"], "data_root": "research_notebooks/bowaka_v2_lab/data_alt"}}
    assert canonical_run_hash(_BASE_CFG) != canonical_run_hash(cfg2)


def test_strategy_hash_unchanged_when_paths_change() -> None:
    cfg2 = {**_BASE_CFG, "paths": {**_BASE_CFG["paths"], "data_root": "research_notebooks/bowaka_v2_lab/data_alt"}}
    assert canonical_strategy_hash(_BASE_CFG) == canonical_strategy_hash(cfg2)


def test_strategy_hash_changes_when_signals_change() -> None:
    cfg2 = {**_BASE_CFG, "signals": {"min_signal_strength": 0.9}}
    assert canonical_strategy_hash(_BASE_CFG) != canonical_strategy_hash(cfg2)


def test_strategy_hash_unchanged_when_run_seed_changes() -> None:
    cfg2 = {**_BASE_CFG, "run": {"kind": "backtest", "seed": 9999}}
    assert canonical_strategy_hash(_BASE_CFG) == canonical_strategy_hash(cfg2)
