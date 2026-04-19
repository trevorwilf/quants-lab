"""Pair-level sweep worker — orchestrates one pair's pipeline end-to-end.

Design: closure-based. The notebook provides a `pipeline_fn(inp)` that does the
actual work (data load, Phase 1 Optuna, Phase 2 stress, validation, export).
`run_pair` wraps the call in a try/except so a single pair's failure cannot
kill the whole sweep.

Concurrency:
- Inner Phase 1 Optuna uses PostgreSQL-backed `ProcessPoolExecutor` (N_JOBS
  subprocesses) inside each pair.
- When the notebook dispatches many `run_pair` calls via a
  `ThreadPoolExecutor` (the outer pair layer), each pair's pipeline runs in
  a thread but its subprocess pool is spawned by the main Python process
  (threads share the parent process). No nested daemon problem.
- Using `ProcessPoolExecutor` for the outer pair layer would cause
  `AssertionError: daemonic processes are not allowed to have children`.
  See Appendix A of the pair-parallelism prompt.

BLAS pinning: each subprocess (Optuna worker, Phase 2 signal worker) pins
BLAS threads to 1 at process entry to avoid oversubscription when the outer
thread pool drives N_JOBS_INNER × PAIR_JOBS subprocesses simultaneously.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass(frozen=True)
class PairSweepInput:
    """All inputs needed to run one pair's pipeline end-to-end.

    For the notebook closure-based design, most of the pair's configuration
    lives in the closure's captured globals (N_TRIALS, TOP_N, etc.). This
    struct carries the minimum per-pair identity the notebook needs for
    ThreadPoolExecutor dispatch.

    Notebooks may stash additional per-pair state in `extra` (e.g.
    pair_info, connector metadata) that the pipeline closure reads back out.
    """

    connector: str
    pair: str
    interval: str
    # Whether Phase 1 Optuna should render a per-trial tqdm bar. Notebooks
    # set this to False when PAIR_JOBS > 1 to keep output readable.
    show_trial_progress: bool = True
    # Arbitrary per-pair state (e.g., pair_info dict).
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PairSweepResult:
    """Everything a completed pair produces.

    `sweep_result` is the dict the notebook appends to its `sweep_results`
    list — its schema is driven by the notebook, not by this module.
    """

    connector: str
    pair: str
    interval: str
    status: str                     # "validated_pass" / "validated_fail" / "error" / ...
    sweep_result: Dict[str, Any]    # schema matches pre-parallel behavior
    yaml_path: Optional[str] = None
    error: Optional[str] = None
    error_traceback: Optional[str] = None


def run_pair(
    inp: PairSweepInput,
    pipeline_fn: Callable[[PairSweepInput], Dict[str, Any]],
) -> PairSweepResult:
    """Run one pair end-to-end via the supplied pipeline closure.

    `pipeline_fn(inp)` must return the `sweep_result` dict the notebook
    normally appends to `sweep_results`. Any exception is caught and surfaced
    as `status="error"` on the returned `PairSweepResult` — it is never
    re-raised. This ensures one bad pair does not kill the whole sweep.

    The pipeline closure is free to read per-pair fields from
    `inp.extra` (e.g. `pair_info`) and to read sweep-wide notebook globals
    from its closure capture.
    """
    try:
        sweep_result = pipeline_fn(inp)
    except Exception as e:
        return PairSweepResult(
            connector=inp.connector,
            pair=inp.pair,
            interval=inp.interval,
            status="error",
            sweep_result={
                "connector": inp.connector,
                "pair": inp.pair,
                "interval": inp.interval,
                "status": "error",
                "robust_score": None,
                "error": str(e),
            },
            error=str(e),
            error_traceback=traceback.format_exc(),
        )

    # pipeline_fn may return None for early-exit statuses (e.g. "no trials"),
    # but for our invariant the notebook pipeline should always return a dict.
    if sweep_result is None:
        sweep_result = {
            "connector": inp.connector, "pair": inp.pair, "interval": inp.interval,
            "status": "error", "robust_score": None,
            "error": "pipeline_fn returned None",
        }

    status = str(sweep_result.get("status", "unknown"))
    yaml_path = sweep_result.get("yaml_path")
    if yaml_path is not None and not isinstance(yaml_path, str):
        yaml_path = str(yaml_path)

    return PairSweepResult(
        connector=inp.connector,
        pair=inp.pair,
        interval=inp.interval,
        status=status,
        sweep_result=sweep_result,
        yaml_path=yaml_path,
    )


def sweep_pairs(
    pair_inputs,
    pipeline_fn: Callable[[PairSweepInput], Dict[str, Any]],
    *,
    max_workers: int = 1,
    on_complete: Optional[Callable[[PairSweepResult], None]] = None,
):
    """Drive a list of pairs through `run_pair`, either serially or in a
    `ThreadPoolExecutor`.

    Parameters
    ----------
    pair_inputs : Sequence[PairSweepInput]
        Pairs to run.
    pipeline_fn : callable
        The per-pair pipeline closure; accepts PairSweepInput, returns the
        sweep_result dict. Exceptions are caught by `run_pair` — never
        re-raised.
    max_workers : int
        1 (default) = serial, preserves original behavior bit-identically.
        >1 = ThreadPoolExecutor with that many outer pair threads. Inner
        subprocess pools (Optuna Phase 1, Phase 2 precompute) are unaffected.
    on_complete : callable, optional
        Called in the main thread once per completed pair, with the
        `PairSweepResult`. Typical use: update a tqdm pair bar and print a
        per-pair summary. Called in arrival order, not submission order,
        when `max_workers > 1`.

    Returns
    -------
    list[PairSweepResult]
        One result per input, in arrival order when parallel.

    Safety notes
    ------------
    - The outer pool MUST be threads, not processes. A
      `ProcessPoolExecutor` outer pool would spawn daemon workers, which
      are forbidden from creating their own children — the inner Optuna
      subprocess pool would crash with
      `AssertionError: daemonic processes are not allowed to have children`.
    - Per-pair exceptions are captured by `run_pair` as `status="error"`
      results; the pool is never torn down by a single pair's failure.
    """
    results: list[PairSweepResult] = []

    if max_workers <= 1:
        for inp in pair_inputs:
            res = run_pair(inp, pipeline_fn)
            results.append(res)
            if on_complete is not None:
                on_complete(res)
        return results

    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=int(max_workers)) as pool:
        futs = {pool.submit(run_pair, inp, pipeline_fn): inp for inp in pair_inputs}
        for fut in as_completed(futs):
            res = fut.result()  # run_pair never raises
            results.append(res)
            if on_complete is not None:
                on_complete(res)
    return results
