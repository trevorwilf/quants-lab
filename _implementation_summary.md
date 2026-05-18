# Strategy fidelity remediation — implementation summary

## Phase fidelity-1 — Contract freeze + config wiring (2026-05-17)

**Branch:** `phase-fidelity-1-contract-and-config` (merged into dev)

**Changes:**

- Added `ProjectConfig.fidelity_mode: Literal["exact","research"] = "research"`
  and `BowakaBacktestConfig.is_exact_mode` property.
- Added `compute_config_hash(cfg)` in `src/bowaka_lab/config/hashing.py`.
- Created `src/bowaka_lab/config/exact_mode_guards.py` with
  `assert_exact_mode_invariants(cfg)` enforcing: required blocklist
  ({TSLL, CONL, SMCX}); `exclude_leveraged_etp/inverse_etp/etn=true`;
  non-empty `realism.adv_tier_caps`; `signal_fade.enabled=false`.
- New YAML profiles:
  - `configs/bowaka_exact_current_strategy.yml` — fidelity_mode=exact;
    mirrors the source-strategy paper-mode contract.
  - `configs/bowaka_research_variant.yml` — fidelity_mode=research; replaces
    the legacy `bowaka_backtest_iex_exploratory.yml` (deleted).
- Notebook builders updated to load via `load_config_file(CONFIG_PATH)`
  with `assert_exact_mode_invariants(cfg)` + `compute_config_hash(cfg)`:
  `_build_03_prefilter_replay`, `_build_04_single_config_backtest`,
  `_build_05_entry_timing_counterfactuals`,
  `_build_06_exit_surface_and_stop_manager`,
  `_build_run_backtest_notebook`. Notebook 11 hashes the persisted
  config.json instead of using a `sha256:notebook_11` placeholder.
- `.gitignore` excludes `reference/` (source-strategy backup). README
  gained a "Reference: source strategy" + "Fidelity mode profiles" section.
- Test count: 598 passed, 3 skipped (PostgreSQL), 5 deselected.

**Tests added:**

- `tests/unit/test_fidelity_mode_field.py` — field default + YAML round-trip.
- `tests/unit/test_exact_profile_invariants.py` — guard happy path +
  each violation type (blocklist empty/partial, adv tiers empty, signal_fade
  enabled, etp/etn flags, aggregate error).
- `tests/unit/test_research_profile_loads.py` — research YAML loads cleanly.
- `tests/unit/test_notebook_uses_load_config_file.py` — every builder
  references `load_config_file(...)` and declares `CONFIG_PATH`.

**Tests updated (not deleted):**

- `tests/unit/test_config_loader.py` — refers to `bowaka_research_variant.yml`.
- `tests/unit/test_notebooks_03_04_structure.py` — checks `CONFIG_PATH`
  instead of inline START_DATE/STOP_PCT/etc.
- `tests/unit/test_notebooks_05_06_structure.py` — `OVERRIDE_*` knobs.
- `tests/unit/test_run_backtest_notebook.py` — `REQUIRED_PARAM_NAMES` collapsed
  to `{DATA_ROOT, ARTIFACTS_DIR, RUN_ID, CONFIG_PATH}`.

**Deferred (operator unblocks later phases):**

- Source-parity tests in Phases 2, 3, 6 (import functions from
  `reference/source_strategy/scripts/`) will need the reference zip
  unpacked. The zip already lives at
  `research_notebooks/bowaka_lab/reference/source_strategy/bowaka_backup.zip`;
  it has been unpacked locally but `reference/` is gitignored so the
  binary blob does not enter the repo.
