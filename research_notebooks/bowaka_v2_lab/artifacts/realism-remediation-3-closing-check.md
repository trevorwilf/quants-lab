# Realism remediation 3 — Closing check

## §1.3 reproduction (audit's all-sentinel-success scenario)

### Pre-remediation observed output (audit, 2026-05-23)

The tiny-lake walk-forward study ran two trials, each of whose folds rejected the boundary-equal `val_end == final_holdout_start` fold via `HoldoutGuardError`. The broad `except Exception` in the per-trial objective swallowed the guard error as `_FAILED_TRIAL_SCORE = -1.0e9`. The study writer then emitted:

```json
{
  "status": "ok",
  "best_value": -1000000000.0,
  "best_params": {"signals.gap_pct_max": ..., "exits.stop_pct": ..., ...},
  "n_trials_completed": 2,
  "n_folds": 2
}
```

— a successful-looking study whose `best_params` was the optimizer's random sample of a sentinel-only trial.

### Post-remediation observed output (2026-05-24, after Phases 0-3)

```bash
$ python scripts/closing_check_realism_3.py
2026-05-24 00:07:50,219 INFO preflight passed: 4 checks
[I 2026-05-24 00:07:50,294] A new study created in memory ...
[I 2026-05-24 00:07:56,376] Trial 0 finished with value: -1.5 and parameters: {...}
[I 2026-05-24 00:08:02,580] Trial 1 finished with value: -1.5 and parameters: {...}
2026-05-24 00:08:31,968 INFO walk-forward study done: 2/2 trials completed, best=-1.5
{
  "status": "ok",
  "best_value": -1.5,
  "n_folds": 2,
  "n_trials_completed": 2,
  "best_params_keys": [...]
}
```

`best_value=-1.5` is a real composite objective score from two real fold backtests on the tiny lake — NOT the sentinel score. The Phase 0 half-open-guard fix (audit §P0-002) admits the boundary-equal fold; the Phase 0 structural-exception change (audit §P0-001) ensures any future structural failure aborts the study with `OptunaStudyInvalidError` rather than completing with a sentinel result.

The forbidden outcome — `status: "ok"` with `best_value: -1e9` — is reproducibly impossible: the post-`study.optimize` validation in `run_walkforward_study` raises `OptunaStudyInvalidError` when every completed trial is sentinel-scored, and `_write_failed_study_artifact` writes `status: "failed"` to disk before the exception propagates.

## Per-finding remediation status

| Finding | Severity | Phase | Remediation status | Verification |
|---|---|---|---|---|
| P0-001 all-sentinel success | P0 | 0 | done | `tests/integration/test_walkforward_runner_invalid_study.py` (3 tests) + closing-check reproduction above |
| P0-002 interval semantics | P0 | 0 | done | `tests/unit/optuna/test_holdout_guard_boundaries.py` (8 tests) |
| P0-003 DQ/quote fail-open | P0 | 0 | done | `tests/unit/optuna/test_preflight_fail_closed.py` (22 tests) |
| §6.6 capped preflight | P0 | 1 | done | `tests/unit/optuna/test_full_pit_preflight_fail_closed.py` (5 tests) + telemetry in `study.universe.preflight_coverage_fraction` |
| P0-004 / P0-005 lake completeness verification | P0 | 1 | verification-only | `bowaka-v2-lab verify-lake` CLI + `tests/integration/test_verify_lake_cli.py` (6 tests). Ingestion itself is operator-owned and intentionally out of scope. |
| P1-001 PIT universe (telemetry only) | P1 | 1 | telemetry added; historical snapshots still pending ingestion | `tests/unit/optuna/test_pit_universe_union.py` (6 tests) + `study.universe.pit_union_symbol_count` |
| P1-002 source manifest | P1 | 2 | done | `tests/parity/test_source_manifest_unchanged.py` (3 tests). Contract bumped to v3; `source_manifest` + `source_manifest_hash` carried. |
| P1-003 scanner keys + same_symbol_entries_per_day | P1 | 2 | done | `tests/parity/test_scanner_keys_in_generated_configs.py` (7 tests) + `tests/parity/test_same_symbol_entries_per_day_propagation.py` (4 tests). Generator iterates the contract scanner mapping; `StrategyConsumer` reads from `scanner_cfg`; loader raises `ConfigParityError` on both-blocks-set. |
| P1-004 risk-control promotion gate | P1 | 3 | done (gate, not freeze) | `tests/unit/optuna/test_risk_control_promotion_gate.py` (14 tests). Search space preserved; risk drift past epsilon caps the tier at `research_only` and flips `risk_policy_experiment` in promotion_evidence. |
| P1-006 storage path | P1/P2 | 3 | done | `tests/integration/test_optuna_storage_path.py` (7 tests). Relative SQLite URIs resolve against the lab root; PostgreSQL passthrough; legacy `research_notebooks/bowaka_v2_lab/...` prefix dedup. |
| P1-008 IEX caveat | P1 | already in code; revalidated | parity tests | `tests/parity/test_iex_optuna_study_user_attrs_contain_partial_tape_flag.py` + promotion gate's IEX cap. |
| P2-001 stale defaults | P2 | 3 | done | `tests/unit/test_actual_mode_config_required_fields.py` (9 tests). `UniverseConfig.max_price` 1000.0 → 20.0; `min_adv_dollars` 1_000_000 → 250_000.0. `config/defaults.py` deleted. |
| P2-002 test mark segmentation | P2 | 3 | done | `pyproject.toml` markers registered: `optuna_smoke`, `paper_reconcile`. |
| P1-005 fill calibration | P1 | — | out of scope (requires paper logs) | tracked for next prompt |
| P1-009 paper reconciliation | P1 | — | out of scope (requires paper logs) | tracked for next prompt |

## Phase test results summary

| Phase | Branch | Unit + parity | Integration + reconcile | bowaka_common |
|---|---|---|---|---|
| 0 | phase-0-realism-3-p0-stopship | 749 / 0 | 316 / 0 (1s, 12d) | 97 / 0 |
| 1 | phase-1-realism-3-full-pit-preflight | 760 / 0 | 322 / 0 (1s, 12d) | 97 / 0 |
| 2 | phase-2-realism-3-source-manifest-and-scanner-keys | 774 / 0 | 322 / 0 (12d) | 97 / 0 |
| 3 | phase-3-realism-3-storage-defaults-promotion-gate | 796 / 0 | 330 / 0 (12d) | 97 / 0 |

All four phases merged to `dev` via `--no-ff` with phase-summary artifacts under `artifacts/phase-N-realism-3-summary.md`.

## What stays out of scope

- Audit Phase 1 data-lake ingestion proper (adjusted/split-adjusted bars, historical quotes, halt/status partitions, corporate actions, historical asset snapshots).
- Audit Phases 4 & 5 — fill calibration and OCO/protection paper reconciliation (P1-005, P1-009).
- Audit Phase 7 — paper trading validation.
- Audit Phase 8 — SIP migration.

The Phase 1 `verify-lake` CLI and full-PIT preflight gates fail closed precisely on the inputs the deferred ingestion work needs to produce, so the lab will pass cleanly once those land. Remediation 3 is **not** the gate for `main` — the audit §12 promotion checklist is, and it still requires the deferred data + paper-log work.
