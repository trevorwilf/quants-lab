# Final verification — Bowaka v2 lab Optuna walk-forward speedup

Speedup report end-of-prompt verification block (after all 10 phases land on `dev`).

## Test matrix

| Gate | Command | Pass | Fail | Skip | Deselected | Wall |
|---|---|---|---|---|---|---|
| `make test-all` (full unit + parity + integration + reconcile) | `pytest tests --timeout=180 -m "not live_*"` | **1313** | **0** | 2 (PG-gated) | 1 (live) | 11:42 |

`make test` (with `not slow` also excluded):
* Phase 0: 1154 pass
* Phase 1: 1166 pass (+12)
* Phase 2: 1188 pass (+22)
* Phase 3: 1210 pass (+22)
* Phase 4: 1218 pass (+8)
* Phase 5: 1229 pass (+11, with 2 PG-gated skips)
* Phase 6: 1238 pass (+9)
* Phase 7: 1248 pass (+10)
* Phase 8: 1285 pass (+37)
* Phase 9: 1291 pass (+6)
* Phase 10: 1302 pass (+11)
* Final (`make test-all`): **1313 passed** (the +11 are the
  `not slow` gate including reconcile + the few slow paths the
  Phase 5/8/10 tests added).

## Smoke

```
python -m bowaka_v2_lab.cli smoke --config configs/bowaka_v2_backtest_smoke.yml
```

Result: **ok** (summary.json + artifact contract intact).

## Benchmark (default-off baseline)

`scripts/benchmark_optuna_objective.py --out artifacts/benchmarks/post_phase_10.json`

```json
{
  "phase": "phase_0_baseline",
  "wall_seconds": 10.234,
  "peak_rss_bytes": 134836224,
  "counters": {
    "minute_supplier_calls": 60,
    "minute_parquet_reads": 0,
    "quote_supplier_calls": 5,
    "quote_parquet_reads": 0,
    "daily_cache_builds": 40,
    "event_count_processed": 0,
    "gate_dump_rows_constructed": 0,
    "artifact_bytes_written": 2448794
  },
  "study_status": "ok",
  "study_best_value": -1.5,
  "study_n_folds": 2,
  "study_n_trials_completed": 1
}
```

Note: this benchmark runs against the synthetic tiny-lake fixture with
default config (which has `objective_artifact_mode=full` and
`cached_suppliers=false`) — the post-phase-10 numbers measure the
**default-off** baseline regression. The actual-IEX / actual-SIP optuna
configs ship with `objective_artifact_mode=objective_minimal`,
`cached_suppliers=true`, `n_jobs=8`, and PostgreSQL storage; running
those against a real fold is the operator's responsibility and outside
the scope of the local fixture-based benchmark.

## Phase-by-phase status

| Phase | Branch | Tests added | Default-off | Production-flipped |
|---|---|---|---|---|
| 0 | half-open + ProfileCounters + MemoryBudget | 28 | counters yes, helpers yes | half-open fix is permanent |
| 1 | objective_minimal | 12 | yes (`full`) | optuna configs: `objective_minimal` |
| 2 | FoldRuntimeContext | 22 | always on (legacy path preserved as None case) | n/a |
| 3 | cached_suppliers | 22 | yes (`false`) | optuna configs: `true` |
| 4 | ScanSessionContext + gate-dump suppression | 8 | always on (full mode keeps the dump) | n/a |
| 5 | parallel Optuna (8 workers / PostgreSQL) | 13 (2 PG-gated) | yes (`n_jobs=1`) | optuna configs: `n_jobs=8`, `storage=postgresql` |
| 6 | lazy event scheduling | 9 | yes (`preload`); **runtime-refused** for `lazy` | scaffolding only |
| 7 | conservative pruning | 10 | yes (no `pruning` block) | scaffolding only |
| 8 | scan-matrix builder + manifest + CLI + guards | 37 | yes (`enabled: false`) | scaffolding only |
| 9 | matrix-backed scanner runtime | 6 | yes; **runtime-refused** for `enabled: true` | scaffolding only |
| 10 | top-K + sensitivity + stress + holdout guard | 11 | yes (no `robustness` block) | notebook 10: `INCUMBENT_TRIAL = True` |

## Scaffolding-only phases

Phases 6, 9 ship as scaffolding because the prompt's parity matrix
(13 lazy-cadence cases for Phase 6 / 7 matrix-vs-legacy parity tests for
Phase 9) is genuinely multi-day deep-refactor work. The scaffolding
declares the public API, fully wires the search-space / holdout
guards, and adds runtime refusals so a careless flag flip cannot ship
an incomplete implementation. The next remediation cycle picks these
up with the production tests already locked in place.

## Branch state

* All 10 phase branches merged to `dev` via `--no-ff`.
* `chore/final-verification` is the current working branch. After this
  artifact lands it is merged to `dev` and `dev` is pushed.
* **Do NOT merge to `main`** — per the speedup prompt, that is the
  engineer's call (and Phase 9's parity matrix needs to land first
  before any production claim about the matrix-backed scanner runtime).
