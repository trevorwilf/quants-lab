# Archived Claude Code prompts

This folder holds the **input prompts** that drove the bowaka (v1 / common / v2) work.
They are historical artifacts: each corresponds to work already shipped on `dev`. The
implementations live in code + git history + the committed `docs/` summaries and audits.

**These files are gitignored** (root `.gitignore` rule `*_claude_code_prompt.md`) — they
live only in the local working tree, not in version control. They were moved here from
the repo root for tidiness. This `README.md` *is* tracked.

## Specs extracted into committed docs

Two prompts held forward-looking content that other (committed) docs depend on. That
content was extracted into tracked docs so it survives independently of these gitignored
files:

| Extracted to (committed, tracked) | Source prompt |
|---|---|
| `research_notebooks/bowaka_v2_lab/docs/phase-6-acceptance-criteria.md` | `bowaka_v2_lab_optuna_speedup_v2_claude_code_prompt.md` — Phase 6 acceptance criteria (the scan-matrix runtime is **still deferred / scaffolding-only**) |
| `research_notebooks/bowaka_common/marketdata_operator_runbook.md` | `bowaka_shared_marketdata_lake_claude_code_prompt.md` — operator runbook (migrate the real dataset, smoke-test, delete the legacy tree) |

## Inventory (chronological)

| Date | Prompt | Shipped work |
|---|---|---|
| 2026-05-20 | `bowaka_v2_lab_quantslab_integration_…` | 10-phase v2 lab integration into quants-lab |
| 2026-05-20 | `bowaka_shared_marketdata_lake_…` | shared Alpaca market-data lake (`bowaka_common.marketdata`) |
| 2026-05-21 | `bowaka_v2_lab_realism_remediation_…` | realism-audit remediation (round 1) |
| 2026-05-22 | `bowaka_v2_lab_realism_remediation_2_…` | realism remediation (round 2) |
| 2026-05-23 | `bowaka_v2_lab_realism_remediation_3_…` | realism remediation (round 3); audit landed in `docs/audits/` |
| 2026-05-24 | `bowaka_v2_lab_optuna_walkforward_speedup_…` | Optuna walk-forward speedup (10 phases) |
| 2026-05-26 | `bowaka_v2_lab_optuna_speedup_v2_…` | Optuna speedup v2 (6 phases; Phase 6 scan-matrix = scaffolding) |
| 2026-05-27 | `bowaka_v2_lab_speedup_phase_6_…` | scan-matrix scaffolding (PRs 0–5) |
| 2026-05-28 | `bowaka_v2_lab_bayesian_optimization_fix_…` | constant -1.5 objective fix (Phases 0–3) |
| 2026-05-29 | `bowaka_v2_lab_phases_4_7_…` | stress matrix, methodology, paper-recon, SIP-readiness |
| 2026-05-29 | `bowaka_v2_lab_lake_root_fix_and_sip_smoke_…` | lake-root resolution fix + synthetic-SIP smoke |
| 2026-05-29 | `bowaka_v2_lab_parity_notebook_…` | lab-vs-production parity notebook |
| 2026-05-29 | `bowaka_v2_lab_production_backtester_and_parity_…` | production backtester + parity |
| 2026-05-30 | `bowaka_v2_lab_lake_root_hotfix_…` | lake-root hotfix |
| 2026-05-30 | `bowaka_v2_lab_session_minute_window_supplier_parity_fix_…` | session-minute-window supplier parity fix |
