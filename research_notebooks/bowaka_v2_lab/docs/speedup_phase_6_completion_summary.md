# Speedup Phase 6 — completion summary

Implements the archived prompt `docs/old_cc_prompts/bowaka_v2_lab_speedup_phase_6_claude_code_prompt.md` (PRs 0–5 +
the Phase 2.5 worker-count benchmark). All seven phases landed on `dev`,
each on its own branch, merged with `--no-ff` after `make test-all` passed.

A local copy of this note is also written to
`artifacts/speedup_phase_6_completion_summary.md` (gitignored); this `docs/`
copy is the committed reference.

## Per-phase status

| Phase | Status | Merge commit (dev) | Notes |
|---|---|---|---|
| 0 — stop_pct contract reconciliation (0.08 → 0.025) | PASSED | `65ef03e` | Contract, configs, overlays, search-space comment reconciled; SIP configs kept on `--feed-thresholds actual` (prompt's `sip_tightened` flag conflicted with the byte-stability test). |
| 1 — scanner subphase timers + gate-dump cleanup | PASSED | `7558765` | 8 subphase timers + 9 skip/candidate counters on `ProfileCounters`; failing-gate `dump_row` deferred under `collect_gate_dump=False`. |
| 2 — scan-matrix safety hardening | PASSED | `6f12c85` | Real content-derived `dataset_hash` in the manifest; `verify_scan_matrix` rewritten with seeded sampling + cell rules + drift detection; `MatrixVerifyError`. |
| 2.5 — worker-count benchmark + adoption | PASSED (code) / SKIPPED (live sweep) | `8e18310` | Benchmark + parity-check + selector scripts + 13 tests shipped. Live sweep is operator-driven (needs PG + full lake + hours); `n_jobs` stays at the documented baseline of 8. See `docs/phase-2-5-worker-benchmark-handoff.md`. |
| 3 — Phase 6 compatibility runtime | PASSED | `0009865` | `evaluate_one_scan_compat` parity bridge (bit-identical to legacy); backtester + FoldRuntimeContext wiring; `parity_proof.json` (verifier_version=1). |
| 4 — Phase 6 vectorized runtime | PASSED | `a9a3035` | `evaluate_one_scan_vectorized` (NumPy gate masks) + `compute_signal_strength_vectorized`; three-way parity (legacy == compat == vectorized); opt-in needs `parity_proof.json` verifier_version≥2. |
| 5 — expanded finalist validation report (Stage B) | PASSED | `9f68828` | `stop_ship_checklist.py` gate + fold-local stress matrix, top-K clustering, sensitivity, recent-window, DQ summary, trade diagnostics, final-holdout audit. |

## Phase 2.5 worker-count winner

Not determined here — the live benchmark is operator-driven. The workstation
config was since set to `optuna.n_jobs: 10` / `optuna.parallel.max_workers: 10`
(operator decision 2026-05-28; the fast_realism study config uses 16). The
operator runbook + acceptance criteria are in
`docs/phase-2-5-worker-benchmark-handoff.md`. The winner artifact, once the
sweep runs, lands at `artifacts/benchmarks/worker_count_winner.txt`.

## Phase 3 parity_proof.json

The compatibility runtime is proven by the
`tests/parity/test_scan_matrix_*` matrix. The `parity_proof.json` marker
(written by `bowaka-v2-lab scan-matrix verify`) records
`verifier_version: 1` for the compatibility opt-in; `--vectorized-check`
bumps it to `2` for the vectorized opt-in. No proof file is committed (it is
written per built matrix under the operator's `store_root`).

## Phase 4 three-way parity test counts

All passing (legacy == compatibility == vectorized):
- `test_scan_matrix_vectorized_one_scan_parity.py` — 1
- `test_scan_matrix_vectorized_full_session_parity.py` — 1
- `test_scan_matrix_vectorized_tie_order.py` — 1
- `test_scan_matrix_vectorized_full_fold_parity.py` (slow) — 1
- `test_scan_matrix_vectorized_objective_parity.py` (slow) — 1
- `test_compute_signal_strength_vectorized_parity.py` — 2
- `test_scan_matrix_vectorized_missing_value_semantics.py` — parametrised _ge/_le/_between matrix
- `test_scan_matrix_vectorized_stable_sort.py` — 2

## Unresolved items / status notes

- Phase 2.5 live benchmark — operator-owned (not a failure). See
  `docs/phase-2-5-worker-benchmark-handoff.md` (also mirrored to the
  gitignored `artifacts/phase_2_5_test_status.md`).

## Test posture

`make test-all` (unit + parity + integration + reconcile, non-slow,
non-live) is green at every phase merge: ~1231 unit+parity passed, ~392
integration+reconcile passed, 2 skipped (Hummingbot PostgreSQL). The slow
three-way / full-fold / end-to-end parity tests pass when run with `-m slow`.

## Promotion

`dev` is NOT auto-merged into `main`. Promotion is operator-owned and
requires Notebook 10 validation on the live lake (the prompt's
performance claims are not validated by running Notebook 10 here).
