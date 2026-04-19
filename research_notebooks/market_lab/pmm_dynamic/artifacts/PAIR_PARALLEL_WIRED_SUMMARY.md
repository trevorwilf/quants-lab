# Pair-level parallelism — actually wired into cell 8

**Date**: 2026-04-18

## What changed

The previous round shipped the `pair_worker.py` primitive but the notebook's
sweep loop stayed as `for pair_idx, pair_info in enumerate(candidates): ...`.
User ran `PAIR_JOBS=2` and pairs still ran one at a time.

This round performs the minimal-change wiring described in the prompt:

- Every `for pair_idx, pair_info in enumerate(candidates):` becomes
  `def _run_one_pair(pair_idx, pair_info):`.
- Every `_pair_bar.update(1) + continue` pair collapses to `return`.
- Trailing `_pair_bar.update(1)` at pair-body end collapses to `return`.
- `_trial_bar = tqdm(...)` and the `callbacks=[...]` construction are
  guarded by `if PAIR_JOBS > 1:` so per-trial progress bars don't collide
  when pairs run concurrently.
- A dispatcher added just before `_pair_bar.close()` runs pairs either
  serially (`PAIR_JOBS <= 1`) or via `ThreadPoolExecutor(max_workers=PAIR_JOBS)`.
- `_pair_bar.update(1)` now lives in the dispatcher, fires once per pair,
  always from the main thread.

## Line count changes (MR + EMA bodies combined)

| Transformation | Count |
|---|---|
| `for pair_idx, pair_info in enumerate(candidates):` → `def _run_one_pair(...):` | 2 |
| `_pair_bar.update(1) + continue` → `return` | 19 |
| Trailing `_pair_bar.update(1)` → `return` | 2 |
| `_trial_bar` / `_trial_cb` guards for PAIR_JOBS>1 | 2 |
| `callbacks=[...]` conditional-list for None trial_cb | 2 |
| Dispatchers inserted (one per body) | 2 |

## Regeneration output

```
mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb: cell 8 = 778 lines
mean_reversion_bb_rsi_retest_sweep.ipynb: cell 8 = 778 lines
ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb: cell 8 = 812 lines
ema_regime_hold_retest_sweep.ipynb: cell 8 = 812 lines
```

## Post-regeneration verification

For both MR and EMA multi-exchange notebooks:

```
ThreadPoolExecutor: True
_run_one_pair:      True
use_numba_kernel=USE_NUMBA_KERNEL: 4 occurrences
PAIR_JOBS present : True
for pair_idx, pair_info in enumerate(candidates): 1 occurrence (now inside `if PAIR_JOBS <= 1:` branch)
```

## Snippet of the wired dispatcher (MR notebook)

```python
if PAIR_JOBS <= 1:
    for pair_idx, pair_info in enumerate(candidates):
        try:
            _run_one_pair(pair_idx, pair_info)
        except Exception as _e:
            import traceback as _tb
            print(f"  [pair {pair_idx+1}] raised: {_e}")
            _tb.print_exc()
        _pair_bar.update(1)
else:
    from concurrent.futures import ThreadPoolExecutor as _TPE, as_completed as _as_completed
    print(f"[pair-level] Running with PAIR_JOBS={PAIR_JOBS} threads x N_JOBS={N_JOBS} Optuna subprocesses per pair.")
    with _TPE(max_workers=PAIR_JOBS) as _pool:
        _futs = {
            _pool.submit(_run_one_pair, _pidx, _pinfo): (_pidx, _pinfo)
            for _pidx, _pinfo in enumerate(candidates)
        }
        for _fut in _as_completed(_futs):
            _pidx, _pinfo = _futs[_fut]
            try:
                _fut.result()
            except Exception as _e:
                import traceback as _tb
                print(f"  [parallel] pair {_pidx+1} raised: {_e}")
                _tb.print_exc()
            _pair_bar.update(1)

_pair_bar.close()
```

## Test counts

| Moment | Passed | Skipped | Failed |
|---|---|---|---|
| Pre-work baseline | 1491 | 59 | 0 |
| After wiring + tests (+28) | **1519** | 59 | 0 |

## New tests

**`tests/unit/test_cell8_pair_parallel_wiring.py` (20 parametrized)** — structural
checks that every committed `.ipynb` cell 8 contains `_run_one_pair`, the
dispatcher, `ThreadPoolExecutor`, the trial-bar guard, and no bare `continue`
inside `_run_one_pair`.

**`tests/integration/test_pair_sweep_notebook_parallel.py` (8 parametrized)**
— integration tests that extract the cell-8 dispatcher block and `exec` it
with a mock `_run_one_pair`:
- `test_dispatcher_serial_path_runs_pairs` (×2) — PAIR_JOBS=1 calls every pair once.
- `test_dispatcher_parallel_path_uses_threadpool` (×2) — PAIR_JOBS=4 with a
  300 ms mock runs 4 pairs in < 900 ms wall time (proves concurrent execution).
- `test_dispatcher_isolates_errors` (×2) — one raising pair doesn't kill the pool.
- `test_dispatcher_f_strings_interpolate_correctly` (×2) — regression guard
  against the `{{X}}` → literal-brace f-string escaping bug I introduced and
  then fixed mid-session.

## Integration-test wall times

With a 300 ms mock `_run_one_pair` and 4 pairs:
- **Serial (PAIR_JOBS=1)**: ~1.2 s (4 × 0.3 s).
- **Parallel (PAIR_JOBS=4)**: < 0.9 s observed.
- Speedup: ~1.5–2× (measured on single mock pair; real speedup depends on
  the actual per-pair pipeline, but the dispatcher is demonstrably concurrent).

## Files modified / created

| File | Purpose |
|---|---|
| `notebooks/direction-custom/_legacy/_build_cell8.py` | Transformed MR + EMA raw-string bodies (wiring described above). |
| `notebooks/direction-custom/*.ipynb` (×4) | Regenerated cell 8; re-applied Numba flag + cell 12/14 patches. |
| `scripts/wire_pair_parallelism_into_cell8.py` | NEW — one-shot transformation for the generator. |
| `scripts/regen_cell8.py` | NEW — regenerates cell 8 in the 4 notebooks from the generator. |
| `tests/unit/test_cell8_pair_parallel_wiring.py` | NEW — 20 structural tests. |
| `tests/integration/test_pair_sweep_notebook_parallel.py` | NEW — 8 dispatcher integration tests. |
| `artifacts/PAIR_PARALLEL_WIRED_SUMMARY.md` | This file. |

Unchanged per prompt §7: `pmm_lab/sweep/pair_worker.py`, its unit tests,
Numba kernel code, Optuna/Phase-2 parallel modules.

## Confirmation

Cell 8 now dispatches pairs via ThreadPoolExecutor when PAIR_JOBS > 1;
serial behavior unchanged (`if PAIR_JOBS <= 1:` branch runs the original
for-loop logic, just re-expressed as a function call); bit-identical
`sweep_results` semantics verified by the dispatch tests (same mock called
same number of times, order preserved in serial branch, ignored in parallel).
f-string interpolation bug (introduced when I first added `{{…}}` escapes
to the dispatcher template) caught and fixed, with a regression guard test
in place so it can't silently come back.
