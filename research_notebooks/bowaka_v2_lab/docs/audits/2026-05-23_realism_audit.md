# Bowaka v2 lab — Realism Audit (2026-05-23)

> Verbatim landing of the audit driving `docs/old_cc_prompts/bowaka_v2_lab_realism_remediation_3_claude_code_prompt.md` (archived, gitignored).
>
> Two prior remediations exist (`docs/old_cc_prompts/bowaka_v2_lab_realism_remediation_claude_code_prompt.md`, `…_remediation_2_claude_code_prompt.md`). The 2026-05-23 audit re-tested after those merges and found the defects below still live in code (verified against the repo before the remediation-3 prompt was written).

## Critical context — defects verified before remediation 3

| ID | Severity | File / Location | Defect |
|---|---|---|---|
| P0-001 | P0 | `src/bowaka_v2_lab/optuna/walkforward_runner.py` | The broad `except Exception` in the per-trial objective + the per-fold handler swallow structural rejections (HoldoutGuard, preflight) as `_FAILED_TRIAL_SCORE = -1.0e9`. The study writer emits `status: "ok"` with non-empty `best_params` even when every trial failed structurally. |
| P0-002 | P0 | `src/bowaka_v2_lab/optuna/holdout_guard.py:30-39` / `optuna/walkforward.py` | `assert_can_read` uses closed-interval logic (`end < start` + `start > end`) so `end == final_holdout_start` is rejected as an overlap. `walkforward.build_walkforward_splits` admits a fold whose `val_end == final_holdout_start` (half-open semantics). Valid folds are rejected and the resulting `HoldoutGuardError` is swallowed by the objective. |
| P0-003 | P0 | `src/bowaka_v2_lab/optuna/preflight.py` | `_check_data_quality`, `_check_quote_coverage`, `_probe_fold`, and the calendar / DQ / quote probes return `status="skipped"` for missing or failed probes under `intended_realism`. Fail-open instead of fail-closed. |
| P0-004 / P0-005 | P0 | Data lake | Required parquet partitions (bars, quotes, statuses, corporate actions, asset snapshots) may be absent. There is no operator-runnable CLI that fails closed on what is missing. Remediation 3 only adds the verifier, not the ingestion. |
| P1-001 | P1 | `universe/builder.py` | Historical asset-snapshot coverage is not yet available; preflight telemetry must report PIT-union coverage so the gap is visible. |
| P1-002 | P1 | `src/bowaka_v2_lab/reference/__init__.py:115` | The frozen contract hashes only `bowaka_v2_config.yaml`. The strategy/scanner/features/schemas/backtest Python files are not in the contract. |
| P1-003 | P1 | `configs/bowaka_v2_actual_iex_intended_realism_optuna.yml` etc. | Generated optuna configs expose only a subset of the live `scanner:` block (`max_candidates_per_scan`, `max_entries_per_scan`, `min_signal_strength`); the other live scanner keys (`scan_interval_seconds`, `signal_expiry_seconds`, `same_symbol_entries_per_day`, `symbol_cooldown_minutes`, `require_prior_daily_baseline`, `require_fresh_intraday_bar`) are buried in code defaults. `StrategyConsumer` reads `same_symbol_entries_per_day` from `risk_cfg` (default 1) instead of the live `scanner` block. |
| P1-004 | P1 | `src/bowaka_v2_lab/optuna/search_space.py` | Risk-control parameters are in the Optuna search space. User-selected remediation: leave the search space; add a hard promotion-gate refusal when the winning trial's risk-control parameters materially differ from the incumbent. |
| P1-005 | P1 | Fill calibration | Out of scope — requires paper logs. Tracked for next prompt. |
| P1-006 | P1/P2 | `configs/*.yml` | `OPTUNA_STORAGE:-sqlite:///research_notebooks/bowaka_v2_lab/artifacts/optuna/local.db` is a CWD-sensitive relative path that breaks when launched from the lab directory. |
| P1-008 | P1 | IEX caveats | Already in code; revalidated in remediation 3. |
| P1-009 | P1 | Paper reconciliation | Out of scope — requires paper logs. Tracked for next prompt. |
| P2-001 | P2 | `src/bowaka_v2_lab/config/models.py:180-189` | Stale defaults (`max_price=1000.0`, `min_adv_dollars=1_000_000`, `max_candidates_per_scan=10`, `min_signal_strength=0.5`) that no longer match the live contract. |
| P2-002 | P2 | `pyproject.toml` markers | Missing `optuna_smoke` / `paper_reconcile` markers for the slow Optuna integration tests. |
| §6.6 | P0 | `src/bowaka_v2_lab/optuna/walkforward_runner.py::_resolve_symbols` | The preflight caps at 100 symbols. Under `intended_realism` the preflight must run against the full per-fold PIT eligible-universe union, not a capped sample. |

## Reproductions

### §1.3 — all-sentinel study completing as "ok"

```bash
cd research_notebooks/bowaka_v2_lab
export PYTHONPATH=src:../bowaka_common/src
python - <<'PY'
import datetime as dt, tempfile
from pathlib import Path
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study

lab_root = Path.cwd()
tmp = Path(tempfile.mkdtemp())
lake = tmp / "lake"
build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
cfg = write_walkforward_test_config(
    lab_root / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
    tmp / "wf.yml", lake=lake, symbols=["AAA"],
    start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=2,
)
r = run_walkforward_study(cfg, allow_smoke=True)
print({"status": r["status"], "best_value": r["best_value"], "best_params": r["best_params"]})
PY
```

**Pre-remediation observed:** `{"status": "ok", "best_value": -1000000000.0, "best_params": {...}}` — the all-sentinel study reports success.

**Post-remediation expected (after Phase 0 P0-002 fix):** either `status: "ok"` with a real `best_value` (the tiny lake now produces non-sentinel folds because the fold boundary is no longer rejected), OR `OptunaStudyInvalidError` (if the trivial lake still cannot produce non-degenerate folds). The forbidden outcome is the old one — `status=ok` with `best_value=-1e9`.

### §6.6 — capped preflight under intended_realism

`walkforward_runner._resolve_symbols(cfg, md, cap=100)` is invoked for every preflight under every simulation mode. Under `intended_realism` this means the preflight may probe only 100 of, e.g., the 3000+ symbols the per-fold PIT universe would actually trade. Coverage telemetry is not exposed.

## Out-of-scope (deferred to next prompt)

- Audit Phase 1 data-lake ingestion proper (adjusted/split-adjusted bars, historical quotes, halt/status partitions, corporate actions, historical asset snapshots).
- Audit Phases 4 & 5 — fill calibration and OCO/protection paper reconciliation (P1-005, P1-009).
- Audit Phase 7 — paper trading validation.
- Audit Phase 8 — SIP migration.

Remediation 3 Phase 1 adds a `verify-lake` CLI and full-PIT preflight gates so that when the data work is done, the lab will fail closed precisely on what is still missing, and pass cleanly once it is all present.

## Promotion checklist (audit §12)

Promotion to `paper_candidate` / `live_candidate` requires:

1. All P0/P1 findings closed (this prompt closes the code-addressable ones).
2. SIP-feed lake + historical quotes + halt/status + corporate-actions partitions.
3. Paper-vs-sim reconciliation against real paper logs (P1-009).
4. Fill-model calibration against real paper fills (P1-005).
5. Operator review of the full `promotion_evidence.json`.

Remediation 3 is **not** the gate for `main`; the gate stays at audit §12.
