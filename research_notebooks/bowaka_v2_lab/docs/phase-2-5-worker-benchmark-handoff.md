# Phase 2.5 — operator hand-off (worker-count benchmark)

**Status (updated 2026-06-16).** Code and tests landed (parity check + selector +
smoke + 13 unit tests); the live benchmark sweep is **operator-driven**. Worker
counts have since been adopted: the workstation config is `n_jobs: 10` (operator
decision 2026-05-28) and the fast_realism study config runs `n_jobs: 16`, so this
benchmark hand-off is now largely historical. The "stays at `n_jobs: 8`" baseline
below predates those decisions.

(A local copy of this note is also written to
`artifacts/phase_2_5_test_status.md`, which is gitignored — this `docs/`
copy is the committed reference.)

## What landed

- `scripts/benchmark_worker_count_matrix.py` — sweeps a configurable
  grid of worker counts (default `1,4,8,10,12`), records per-trial
  throughput, memory headroom, profile counters, and a fixed-parameter
  replay snapshot for each.
- `scripts/check_worker_count_parity.py` — scores each row in the matrix
  for fixed-parameter parity against the lowest-`n_workers` reference.
  Uses the speedup-report tolerances (`1e-12` prices, `1e-9` objective).
- `scripts/select_worker_count_winner.py` — applies the documented
  selection rules (highest `trials_per_hour` among parity-clean,
  non-error rows; tie-break on `p50_trial_seconds` then `peak_rss_gib`;
  fallback to `n_workers=8`).
- `tests/unit/scripts/test_worker_count_parity_check.py` and
  `tests/unit/scripts/test_worker_count_winner_selection.py` — 11 unit
  tests covering the parity-tolerance, error-rejection, parity-
  violation, fallback, and tiebreaker paths.
- `tests/integration/test_worker_count_benchmark_smoke.py` — import +
  CLI-help smoke (slow-marked).

## What did NOT happen

- The live benchmark sweep across `[1, 4, 8, 10, 12]` worker counts
  with `--n-trials 24` against the live PostgreSQL backend + actual
  IEX lake. Requirements:
    - PostgreSQL Optuna container up (`docker compose -f
      quantslab_desktop_compose.yaml up -d optuna-postgres`).
    - The full IEX lake (~30k bar partitions; the in-CI tiny lake is
      not large enough for the throughput signal to surface).
    - Several hours of clean wall-time.
    - Available system RAM headroom above the configured 62 GiB
      reserve at every worker count tested.

## Operator runbook

```powershell
# 0. Bring PostgreSQL up if it is not already running.
docker compose -f quantslab_desktop_compose.yaml up -d optuna-postgres

# 1. Run the sweep against the production workstation config.
cd research_notebooks/bowaka_v2_lab
python scripts/benchmark_worker_count_matrix.py `
    --config configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml `
    --n-trials 24 `
    --workers 1,4,8,10,12 `
    --output artifacts/benchmarks/

# 2. Verify per-worker-count fixed-parameter parity.
python scripts/check_worker_count_parity.py `
    --input "artifacts/benchmarks/worker_count_matrix_*.json" `
    --output artifacts/benchmarks/worker_count_parity_report.json

# 3. Select the winner.
python scripts/select_worker_count_winner.py `
    --input artifacts/benchmarks/worker_count_parity_report.json `
    --output artifacts/benchmarks/worker_count_winner.txt

# 4. If winner != 8, hand-edit the workstation overlay's optuna.n_jobs
#    and optuna.parallel.max_workers, then re-run make test-all.
```

## PostgreSQL thread cap audit

The compose's `optuna-postgres` is currently sized for ~8 concurrent
client connections. If the benchmark adopts `N > 8`, sustained
PostgreSQL CPU > 85% means PG is the bottleneck; that is a separate
operator-owned change (raise `max_connections` / `shared_buffers`).
The selector script records this in its rationale when relevant.

## Acceptance for closing this phase

This phase merges to `dev` with the benchmark scripts + tests in place
but `n_jobs=8` unchanged. The next live benchmark run by the operator
either:
1. Confirms `n_jobs=8` is the winner -> nothing further to do; or
2. Adopts a higher count and updates the workstation overlay's
   `optuna.n_jobs` / `optuna.parallel.max_workers` + the comment block.

Either branch is considered "Phase 2.5 complete."
