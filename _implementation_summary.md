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

## Phase fidelity-2 — Prefilter replay artifacts + asset_snapshot (2026-05-17)

**Branch:** `phase-fidelity-2-prefilter-artifacts` (merged into dev)

**Changes:**

- Added `bowaka_lab.data.assets.load_latest_asset_snapshot(data_root)` that
  scans `<data_root>/parquet/assets/vendor=alpaca/snapshot_id=*/assets.parquet`
  and returns the newest snapshot (empty DataFrame when none exist).
- Extended `assert_exact_mode_invariants(cfg, *, asset_snapshot=None)` so
  exact mode fails closed on an empty asset snapshot.
- Notebooks 03 + run_backtest load the snapshot before invariants and pass
  it through `replay_prefilter_over_window(..., asset_snapshot=...)`.
- Notebook 03 persists a new `all_decisions.parquet` containing every
  per-(signal_date, symbol) row from the prefilter (passed + rejected),
  lineage-tagged with `config_hash`, `data_feed`, `asset_snapshot_id`.
  Candidates parquet gets the same lineage columns.
- `aggregate_prefilter_funnel` now returns a `by_instrument_class` block
  derived from each `CandidateSet.all_decisions` frame; the weekly report
  Section 5 renders it via the new `instrument_class_breakdown` helper.
- `ArtifactPaths` gains `all_decisions` (this phase) plus pre-allocated
  properties for `entry_skips`, `order_events`, `signal_fade_telemetry`,
  `reconciliation_status` (used in Phases 3–8).

**Tests added:**

- `tests/integration/test_prefilter_parity_with_source.py` extended with
  `classify_instrument` parity tests against a verbatim source excerpt
  copied to `tests/fixtures/source_classify_instrument.py`.
- `tests/unit/test_all_decisions_artifact.py` — `apply_prefilter` returns
  `all_decisions` as a superset of `candidates` with rejection reasons,
  instrument class, classification reason, and `final_decision`.
- `tests/unit/test_notebook_03_persists_all_decisions.py` — AST/regex
  test asserting the builder loads the asset snapshot, passes it through,
  and saves `paths.all_decisions` with lineage tags.
- `tests/unit/test_funnel_includes_instrument_class.py` — funnel dict
  contains the per-class breakdown; `instrument_class_breakdown` helper
  renders a tidy frame.
- Updated `tests/unit/test_prefilter_funnel_aggregation.py` to allow the
  new `by_instrument_class` top-level key.

**Test count:** 621 passed, 3 skipped (PostgreSQL).

## Phase fidelity-3 — Intraday confirmation + quote-aware fills (2026-05-17)

**Branch:** `phase-fidelity-3-confirmation-and-quotes` (merged into dev)

**Changes:**

- New `bowaka_lab.data.quote_loader.QuoteLoader` partitioned-parquet reader,
  callable like `MinuteBarLoader`; returns empty DataFrame on missing
  partition.
- New `bowaka_lab.sim.intraday_confirmation` module with
  `ConfirmationResult` dataclass and `confirm_entry()` — semantic parity
  with source `_confirm_entry` (lines 1943-1991): bid/ask validity, spread
  cap, quote-age cap, price-band chase/failure. Returns stable fail-reason
  strings (`no_quote`, `spread>X`, `quote_age>Xs`, `chase>X`, `failure<X`,
  `bad_quote_timestamp`). Helper `latest_quote_at_or_before(quotes, ts)`.
- `EntryConfig.intraday_confirmation: IntradayConfirmationConfig` field
  (Pydantic nested), default `enabled=false` so research configs that
  don't pass a quote_loader keep working unchanged.
- `BowakaPortfolioBacktester` constructor accepts `quote_loader`; when
  `entry.intraday_confirmation.enabled` it routes through the gate:
    - Exact mode + no quote → entry skipped with `no_quote_exact_mode`.
    - Research mode + no quote → enters with `fill_label='no_quote'`.
    - Failed confirmation → entry skipped, reason recorded.
    - Passed → uses ask-based quote fill (via `buy_from_quote`) when
      `cfg.entry.use_quotes_if_available`.
  Engine init raises in exact mode if `intraday_confirmation.enabled=false`.
- New artifact path `ArtifactPaths.entry_skips` (parquet); the result
  carries an `entry_skips: list[EntrySkipRecord]` plus `entry_skips_df()`.
- `assert_exact_mode_invariants` extended: requires
  `intraday_confirmation.enabled=true`, `max_spread_pct <= 0.01`,
  `max_quote_age_seconds <= 15`. Exact YAML profile reflects these.

**Tests added:**

- `tests/integration/test_confirmation_parity_with_source.py` — 8
  parameterized cases against a verbatim source excerpt at
  `tests/fixtures/source_confirm_entry.py`.
- `tests/unit/test_quote_loader.py` — partition discovery, multi-symbol
  aggregation, derived-column backfill.
- `tests/unit/test_portfolio_engine_confirmation_research_mode.py` —
  valid quote enters, missing quote falls back to bar fill, stale quote
  skips, wide spread skips, entry_skips_df schema.
- `tests/unit/test_portfolio_engine_confirmation_exact_mode.py` — exact
  + no quote skips, exact + disabled raises, exact-mode invariant blocks
  loose thresholds.

**Test count:** 641 passed, 3 skipped (PostgreSQL).
