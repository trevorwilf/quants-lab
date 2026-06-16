"""c9 liveness: the worker-result drain must not deadlock on a silently-dead worker.

Speedup investigation 2026-06-16. The legacy drain blocked on one ``q.get()`` per
process; a worker that died WITHOUT putting a result (OOM/crash over a multi-day
run) hung the whole study forever. ``_drain_worker_results`` polls with a timeout
and stops once all processes have exited, synthesizing a failure for any worker
that never reported. Pure control-flow — no real subprocesses or market data.
"""
from __future__ import annotations

import queue

from bowaka_v2_lab.optuna.parallel import WorkerResult, _drain_worker_results


class _FakeProc:
    def __init__(self, alive: bool) -> None:
        self._alive = alive

    def is_alive(self) -> bool:
        return self._alive


def _ok(worker_id: int) -> WorkerResult:
    return WorkerResult(worker_id=worker_id, n_completed=5, error=None)


def test_drain_happy_path_returns_all_results():
    q: "queue.Queue" = queue.Queue()
    q.put(_ok(0))
    q.put(_ok(1))
    procs = [_FakeProc(True), _FakeProc(True)]
    out = _drain_worker_results(procs, q, poll_timeout=0.05)
    assert len(out) == 2
    assert all(r.error is None for r in out)


def test_drain_does_not_deadlock_when_worker_dies_silently():
    # One worker reported; the other crashed without putting a result, and both
    # processes are now dead. The drain must return PROMPTLY (no hang) with a
    # synthesized failure for the missing worker.
    q: "queue.Queue" = queue.Queue()
    q.put(_ok(0))
    procs = [_FakeProc(False), _FakeProc(False)]
    out = _drain_worker_results(procs, q, poll_timeout=0.05)
    assert len(out) == 2
    errs = [r for r in out if r.error]
    assert len(errs) == 1
    assert "without reporting" in errs[0].error


def test_drain_does_not_lose_results_buffered_before_exit():
    # Both results are present but the procs already report dead — they must still
    # be drained (not discarded as "missing").
    q: "queue.Queue" = queue.Queue()
    q.put(_ok(0))
    q.put(_ok(1))
    procs = [_FakeProc(False), _FakeProc(False)]
    out = _drain_worker_results(procs, q, poll_timeout=0.05)
    assert len(out) == 2
    assert all(r.error is None for r in out)
