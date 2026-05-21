# Phase 0 summary — Mode contract, strategy contract freeze, Optuna quarantine

**Branch:** `phase-0-realism-contract-and-modes` (off `dev`)
**Audit refs:** §11 Phase 0; P0-001.
**Status:** complete, merged to `dev`.

## What shipped

- **`SimulationConfig`** (`config/models.py`) — `mode` ∈ {`current_code_parity`,
  `intended_realism`, `smoke_fixture`} (default `smoke_fixture`) plus
  `allow_research_relaxed` and four policy fields that default to `None` and are
  resolved from `mode` by a post-validator: `intraday_window_policy`,
  `accepted_event_sequencing`, `unknown_instrument_class_policy`,
  `quote_fallback_policy`. Wired into `BowakaV2Config`; `simulation` added to the
  loader allow-list.
- **`reference/` package** — loads/regenerates the frozen contract; resolves the
  read-only live source via `$BOWAKA_V2_SOURCE_ROOT` or the git-ignored mirror
  (`reference/source_strategy/scripts`); `python -m bowaka_v2_lab.reference`
  regenerates the contract.
- **`reference/actual_bowaka_v2_contract.yaml`** — frozen machine-readable
  snapshot of the live config; pins `session`, `universe`, `historical_features`,
  `scanner`, `signals`, `score`, `execution`, `sizing`, `risk` (incl.
  `adv_tier_caps` + `shadow`), `exits`; carries `source_sha256`.
- **Optuna config quarantined** — `bowaka_v2_walkforward_optuna.yml` →
  `.quarantined` (its `n_startup_trials` key is not in the `OptunaConfig` schema;
  Phase 1 restores it).
- **Shipping configs** — smoke + IEX research → `mode: smoke_fixture`; SIP
  research → `mode: intended_realism`.
- **Smoke-run refusal** — `run-backtest` and walk-forward Optuna refuse a
  `smoke_fixture` config unless `--allow-smoke-optimization`; the `smoke`
  subcommand stays exempt.
- **Run lineage** — the backtester writes the `simulation` block + a `lineage`
  block (`simulation_mode`, `feed`, `strategy_config_hash_actual`,
  `lab_config_hash`, `dataset_hash`, `code_hash`/git HEAD) into
  `run_manifest.json`, and a `## Run Header` section into `report.md`.
- **`docs/current_code_vs_intended_realism.md`** — documents the four
  live-vs-intended behaviors and the lab flag controlling each.
- **`mirror_bowaka_v2_source.ps1`** (repo root) — operator script: mirrors the
  read-only live source + regenerates the contract.

## Note on naming

The prompt's `manifest.json` is the run manifest, written as `run_manifest.json`
(the 16-file artifact contract names it that). The `simulation`/`lineage`
metadata is written there; no new file was added, so the artifact-contract test
is unaffected.

## Files changed

Code: `config/models.py`, `config/loader.py`, `config/__init__.py`,
`reference/__init__.py` (new), `reference/__main__.py` (new),
`sim/backtester.py`, `optuna/walkforward_runner.py`, `cli.py`, `cli_runners.py`.
Configs: 3 shipping configs (+`simulation:`), optuna config → `.quarantined`.
New: `reference/actual_bowaka_v2_contract.yaml`,
`docs/current_code_vs_intended_realism.md`, `mirror_bowaka_v2_source.ps1`.
Notebooks: `_build_10_optuna_walkforward.py` (+`ALLOW_SMOKE`), regenerated
`10_optuna_walkforward.ipynb`. `.gitignore` (mirror ignore).

## Tests

Added: `tests/parity/test_actual_contract_loaded.py`,
`tests/unit/test_simulation_mode_required.py`,
`tests/unit/test_simulation_mode_defaults_coupled.py`,
`tests/unit/test_smoke_optuna_refused.py`,
`tests/unit/test_manifest_mode_present.py`,
`tests/integration/test_quarantined_excluded.py` (+ `tests/parity/__init__.py`).
Updated (incidental): `test_cli_commands.py`, `test_walkforward_runner.py`,
`test_notebook_10_runs.py` (quarantine path + `--allow-smoke-optimization`).

**Result:** 314 passed, 1 skipped, 12 deselected (slow/live), 0 failed.
env-check passes on all 3 shipping configs.

## Acceptance criteria

| Criterion | Status |
|---|---|
| env-check passes on every non-quarantined config | PASS (3/3) |
| Reference contract YAML exists and is parsed by reference loader | PASS |
| `run_manifest.json` + report header list mode and lineage hashes | PASS |
| Quarantined file not picked up by config-validation tests | PASS |
