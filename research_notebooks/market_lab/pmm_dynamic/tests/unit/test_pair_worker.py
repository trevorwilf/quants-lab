"""Unit tests for the pair-level parallelism primitive.

Covers:
- `run_pair` captures exceptions, never re-raises.
- Two sequential calls produce identical results (no state leakage).
- Notebook-constant `PAIR_JOBS` defaults to 1 in each committed notebook.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pmm_lab.sweep.pair_worker import (
    PairSweepInput, PairSweepResult, run_pair, sweep_pairs,
)


_ROOT = Path(__file__).resolve().parents[2]
_NOTEBOOKS = [
    _ROOT / "notebooks" / "direction-custom" / name
    for name in (
        "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "mean_reversion_bb_rsi_retest_sweep.ipynb",
        "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "ema_regime_hold_retest_sweep.ipynb",
    )
]


# ────────────────────────────────────────────────────────────────────────────
# run_pair behavior
# ────────────────────────────────────────────────────────────────────────────

def test_run_pair_returns_result_from_pipeline_fn():
    inp = PairSweepInput(connector="mexc", pair="XMR-USDT", interval="5m")

    def pipeline(i):
        return {"connector": i.connector, "pair": i.pair, "interval": i.interval,
                "status": "validated_pass", "robust_score": 0.42}

    res = run_pair(inp, pipeline)
    assert res.status == "validated_pass"
    assert res.sweep_result["robust_score"] == 0.42
    assert res.connector == "mexc"
    assert res.error is None


def test_run_pair_captures_exception_as_error_status():
    """A pipeline that raises must return status='error', not re-raise."""
    inp = PairSweepInput(connector="mexc", pair="BAD-USDT", interval="5m")

    def bad_pipeline(i):
        raise RuntimeError("simulated failure")

    res = run_pair(inp, bad_pipeline)
    assert res.status == "error"
    assert res.error is not None
    assert "simulated failure" in res.error
    assert res.error_traceback is not None
    assert "simulated failure" in res.error_traceback
    # The sweep_result dict still carries the pair identity and the error
    assert res.sweep_result["status"] == "error"
    assert res.sweep_result["pair"] == "BAD-USDT"


def test_run_pair_two_sequential_calls_produce_consistent_results():
    """Two calls on the same inputs → identical sweep_result dicts."""
    inp = PairSweepInput(connector="nonkyc", pair="BTC-USDT", interval="5m")
    call_count = {"n": 0}

    def pipeline(i):
        call_count["n"] += 1
        # Make the output deterministic but reference a captured variable
        return {"connector": i.connector, "pair": i.pair, "interval": i.interval,
                "status": "validated_pass", "robust_score": 0.1 * 5}  # deterministic

    r1 = run_pair(inp, pipeline)
    r2 = run_pair(inp, pipeline)
    assert r1.sweep_result == r2.sweep_result
    assert call_count["n"] == 2


def test_run_pair_pipeline_returns_none_is_handled():
    """A pipeline that returns None must yield an error-shaped result."""
    inp = PairSweepInput(connector="mexc", pair="X-USDT", interval="5m")

    def pipeline(i):
        return None

    res = run_pair(inp, pipeline)
    assert res.status == "error"
    assert "None" in res.sweep_result.get("error", "")


# ────────────────────────────────────────────────────────────────────────────
# PAIR_JOBS constant wired into every committed notebook
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("nb_path", _NOTEBOOKS)
def test_notebook_has_pair_jobs_constant(nb_path):
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    src_all = []
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        s = cell["source"]
        if isinstance(s, list):
            s = "".join(s)
        src_all.append(s)
    joined = "\n".join(src_all)
    assert "PAIR_JOBS" in joined, (
        f"{nb_path.name}: missing PAIR_JOBS constant in any code cell"
    )
    # Default value should be 1 (serial) — opt-in parallelism only
    assert "PAIR_JOBS = 1" in joined, (
        f"{nb_path.name}: default PAIR_JOBS must be 1 (serial, bit-identical to pre-change)"
    )
