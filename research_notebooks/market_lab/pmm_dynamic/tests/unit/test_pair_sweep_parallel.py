"""Concurrency tests for the pair-level `sweep_pairs` primitive.

These tests use a mock `pipeline_fn` — no real pipeline, no Optuna, no
Mongo — so they run fast (<2s each) and isolate the parallelism invariants
from pipeline correctness (which is covered elsewhere).
"""

from __future__ import annotations

import multiprocessing as mp
import threading
import time
from concurrent.futures import ProcessPoolExecutor

import pytest

from pmm_lab.sweep.pair_worker import (
    PairSweepInput, run_pair, sweep_pairs,
)


def _pair_key(r):
    sr = r.sweep_result
    return (sr["connector"], sr["pair"], sr["interval"])


# ────────────────────────────────────────────────────────────────────────────
# Serial vs parallel parity
# ────────────────────────────────────────────────────────────────────────────

def test_pair_parallel_matches_serial_two_pairs():
    """Dispatch two pairs serially then via 2-thread pool. Same result set."""
    inputs = [
        PairSweepInput(connector="mexc", pair="A-USDT", interval="5m"),
        PairSweepInput(connector="nonkyc", pair="B-USDT", interval="5m"),
    ]

    def pipeline(i):
        return {"connector": i.connector, "pair": i.pair, "interval": i.interval,
                "status": "validated_pass",
                "robust_score": hash((i.connector, i.pair)) % 1000 / 1000.0}

    serial = sweep_pairs(inputs, pipeline, max_workers=1)
    parallel = sweep_pairs(inputs, pipeline, max_workers=2)

    assert len(serial) == len(parallel) == 2
    # Parallel results may arrive out of order; sort by key
    serial_by_key = {_pair_key(r): r for r in serial}
    parallel_by_key = {_pair_key(r): r for r in parallel}
    assert set(serial_by_key.keys()) == set(parallel_by_key.keys())
    for k in serial_by_key:
        assert serial_by_key[k].sweep_result == parallel_by_key[k].sweep_result


def test_pair_parallel_isolates_errors():
    """One pair errors, others succeed. Pool must not abort; error surfaces as status='error'."""
    inputs = [
        PairSweepInput(connector="mexc", pair="OK-USDT", interval="5m"),
        PairSweepInput(connector="mexc", pair="BAD-USDT", interval="5m"),
        PairSweepInput(connector="nonkyc", pair="OK-USDT", interval="5m"),
    ]

    def pipeline(i):
        if i.pair == "BAD-USDT":
            raise RuntimeError("simulated failure for BAD-USDT")
        return {"connector": i.connector, "pair": i.pair, "interval": i.interval,
                "status": "validated_pass", "robust_score": 0.5}

    results = sweep_pairs(inputs, pipeline, max_workers=3)
    by_key = {_pair_key(r): r for r in results}
    assert len(results) == 3
    assert by_key[("mexc", "BAD-USDT", "5m")].status == "error"
    assert "simulated failure" in by_key[("mexc", "BAD-USDT", "5m")].error
    assert by_key[("mexc", "OK-USDT", "5m")].status == "validated_pass"
    assert by_key[("nonkyc", "OK-USDT", "5m")].status == "validated_pass"


def test_pair_parallel_on_complete_callback_fires_per_result():
    """The on_complete callback is invoked once per finished pair, in the main
    thread — safe for updating tqdm bars."""
    inputs = [
        PairSweepInput(connector="mexc", pair=f"P{i}-USDT", interval="5m")
        for i in range(5)
    ]

    def pipeline(i):
        return {"connector": i.connector, "pair": i.pair, "interval": i.interval,
                "status": "validated_pass", "robust_score": 0.1}

    seen = []

    def on_complete(r):
        seen.append(_pair_key(r))

    results = sweep_pairs(inputs, pipeline, max_workers=3, on_complete=on_complete)
    assert len(results) == 5
    assert len(seen) == 5
    assert set(seen) == {_pair_key(r) for r in results}


# ────────────────────────────────────────────────────────────────────────────
# Daemon-process guard — the critical architectural invariant
# ────────────────────────────────────────────────────────────────────────────

def _spawn_subprocess_worker():
    """Top-level so it's picklable. Just returns its own daemon flag."""
    return mp.current_process().daemon


def _pipeline_that_spawns_subprocess(inp):
    """Pipeline that tries to create a ProcessPoolExecutor (simulating the
    inner Optuna subprocess pool). If the outer pool used processes (daemonic),
    this would raise `AssertionError: daemonic processes are not allowed to
    have children`. With threads, it succeeds."""
    with ProcessPoolExecutor(max_workers=1) as inner:
        fut = inner.submit(_spawn_subprocess_worker)
        daemon = fut.result()
    return {"connector": inp.connector, "pair": inp.pair, "interval": inp.interval,
            "status": "validated_pass", "inner_daemon": daemon}


def test_pair_parallel_allows_inner_subprocess_pool_via_threads():
    """CRITICAL INVARIANT: sweep_pairs with max_workers>1 uses threads, so
    the pipeline_fn can safely spin up a `ProcessPoolExecutor` (simulating
    the Optuna Phase 1 inner pool). With a ProcessPoolExecutor outer, this
    would fail with the daemonic-processes error."""
    inputs = [PairSweepInput(connector="mexc", pair="X-USDT", interval="5m")]
    results = sweep_pairs(inputs, _pipeline_that_spawns_subprocess, max_workers=2)
    assert len(results) == 1
    assert results[0].status == "validated_pass"
    # The inner subprocess should NOT be a daemon (main Python process spawned it)
    assert results[0].sweep_result["inner_daemon"] is False


def test_pair_parallel_dispatch_is_thread_based():
    """Smoke check that the outer pool is using threads, not processes.

    A process-based outer would manifest as each pipeline_fn seeing a distinct
    `os.getpid()`. Threads share PID."""
    import os
    inputs = [
        PairSweepInput(connector="mexc", pair=f"P{i}-USDT", interval="5m")
        for i in range(4)
    ]
    main_pid = os.getpid()

    def pipeline(i):
        return {"connector": i.connector, "pair": i.pair, "interval": i.interval,
                "status": "ok", "seen_pid": os.getpid()}

    results = sweep_pairs(inputs, pipeline, max_workers=4)
    pids_seen = {r.sweep_result["seen_pid"] for r in results}
    assert pids_seen == {main_pid}, (
        f"Expected all pipelines to run in the main process (thread pool); "
        f"saw PIDs {pids_seen} vs main {main_pid}"
    )
