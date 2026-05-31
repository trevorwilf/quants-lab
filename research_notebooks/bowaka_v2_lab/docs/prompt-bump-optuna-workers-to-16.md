# Prompt: bump Optuna parallel workers from 8 → 16 (workstation profile)

Paste everything in the fenced block below into a fresh Claude Code session
(run from the repo root, `E:\tradingsoftware\quants-lab`). It is self-contained;
it does not rely on any prior conversation.

---

```
Goal: raise the Bowaka v2 walk-forward Optuna optimization from 8 concurrent
workers to 16 on the workstation profile.

Background you need (verify it before acting — line numbers may have drifted):

- The effective worker count is `min(n_jobs, max_workers)`, enforced in
  research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/optuna/dispatcher.py
  (look for `effective_n_jobs = min(int(n_jobs), int(budget.max_optuna_workers))`).
  - `optuna.n_jobs` is the REQUESTED worker count
    (read at walkforward_runner.py: `jobs = ... optuna_cfg.get("n_jobs", 1)`).
  - `optuna.parallel.max_workers` is the CEILING; it feeds
    `MemoryBudget(max_optuna_workers=...)` at walkforward_runner.py
    (`max_optuna_workers=int(parallel_cfg.get("max_workers", 8))`).
  - Both are 8 today, so raising only one leaves the other as the binding
    limit. BOTH must become 16.

The change — edit
research_notebooks/bowaka_v2_lab/configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml:
  1. `optuna.n_jobs: 8`            -> `optuna.n_jobs: 16`   (around line 116)
  2. `optuna.parallel.max_workers: 8` -> `... : 16`         (around line 122)
Leave `optuna.parallel.memory_reserve_gib: 62` and `strict_parallel: true`
as they are. A pre-built reference overlay with exactly these two values is at
configs/bowaka_v2_actual_iex_current_code_optuna.workstation_16w.yml — diff
against it to confirm you changed the right keys and nothing else.

Validate the memory budget BEFORE finishing (MemoryBudget in
src/bowaka_v2_lab/utils/memory_guard.py). With strict_parallel=true the run
HARD-FAILS (no serial fallback) if the budget can't fit the workers, so this
must pass:
  effective_budget = total_ram - reserve_system(62) - emergency_headroom(16) - postgres(8)
  projected        = n_workers * worker_private_gib_estimate(6.0)
  require: projected <= effective_budget
  On a 192 GiB box: 16*6 = 96 GiB <= 192-62-16-8 = 106 GiB  -> passes (10 GiB spare).
  FIRST confirm this machine's actual total RAM (psutil.virtual_memory().total).
  If it is NOT ~192 GiB, recompute; if 96 GiB does not fit, do NOT flip to 16 —
  report the numbers back to me instead.

Postgres needs NO change: the optuna-postgres container in
quantslab_desktop_compose.yaml runs stock postgres:16 at the default
max_connections=100, which already covers 16 workers (each worker is one
process opening ~1-2 connections at n_jobs=1). Do not lower max_connections.

After editing, run the config-load / overlay-validation tests to prove the
edited config still parses and validates:
  cd research_notebooks/bowaka_v2_lab
  python -m pytest tests/unit/optuna/test_workstation_overlays_load_and_validate.py tests/unit/optuna/test_parallel_worker_caps_at_8.py tests/unit/test_config_loader.py -v
Then show me the final diff. Do NOT commit unless I say so.

IMPORTANT governance caveat — read before flipping:
The workstation.yml header and docs/phase-2-5-worker-benchmark-handoff.md
say production stays at n_jobs=8 until the worker-count benchmark proves 16
wins with zero fixed-parameter parity drift vs the 8-worker baseline. The
proper sequence is:
  python scripts/benchmark_worker_count_matrix.py --config <workstation.yml> --n-trials 24 --workers 1,4,8,10,12,16 --output artifacts/benchmarks/
  python scripts/check_worker_count_parity.py  --input "artifacts/benchmarks/worker_count_matrix_*.json" --output artifacts/benchmarks/worker_count_parity_report.json
  python scripts/select_worker_count_winner.py --input artifacts/benchmarks/worker_count_parity_report.json --output artifacts/benchmarks/worker_count_winner.txt
That sweep needs the Optuna Postgres container up + the full IEX lake + several
hours of wall time. Ask me whether I want you to (a) just flip the config to 16
now, or (b) run the benchmark first and only flip if 16 is the proven winner.
```
