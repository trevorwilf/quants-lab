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

## Phase fidelity-4 — Broker / order / protection state simulation (2026-05-18)

**Branch:** `phase-fidelity-4-broker-state` (merged into dev)

**Changes:**

- New `BrokerSimConfig` in `config/models.py`: enabled flag, latency
  knobs, partial-fill / rejection / OCO-attach-failure probabilities,
  max_unprotected_seconds, fallback / flatten flags, GTC default TIF.
  All probabilities 0 by default — deterministic.
- New FSM types in `sim/orders.py`: `OrderStatus`, `ProtectionState`,
  `FillEvent`, `ParentOrder` (with `add_fill` for weighted-average price),
  `OcoBracket`.
- New module `sim/broker.py`:
  - `SimulatedBroker` with `submit_parent`, `attach_oco`,
    `submit_fallback_stop`, `flatten`, `step(now_ts, bar, quote)`.
  - Escalation ladder (retry → fallback → flatten) drives
    `protection_state` transitions on attach failure.
  - Bracket exits (stop, target) fire from `step()`'s `_step_active_brackets`
    sub-loop using the bar's high/low.
  - `BrokerEvent` dataclass + `events_df()` for the `order_events.parquet`
    artifact. Event-type constants (`EVT_PARENT_FILLED` etc.) exported.
- `BowakaPortfolioBacktester` constructor gains `broker: SimulatedBroker | None`
  and auto-constructs one when `cfg.broker_sim.enabled`. On every entry
  the engine submits a synthetic parent + attaches an OCO so
  `order_events.parquet` carries a stream that Phase 8 reconciliation can
  diff against paper logs. The engine still owns position lifecycle for
  the legacy/research path; the broker FSM is exercised end-to-end by its
  unit tests.
- `BowakaBacktestResult` gains `broker_events` + `order_events_df()`.
- `TradeRecord` extension: `parent_order_id`, `bracket_id`,
  `entry_event_type`, `protection_outcome`, `entry_slippage_pct`,
  `exit_slippage_pct`.

**Tests added:**

- `tests/unit/test_broker_state_machine.py` (11 tests): market /
  marketable_limit / partial / rejection / timeout parent fills;
  OCO attach success, retry → fallback, retry → flatten; stop-hit;
  target-hit; event artifact schema.
- `tests/integration/test_engine_with_broker_smoke.py`: end-to-end run
  with broker enabled, asserts parent_submitted + oco_attach_pending +
  oco_attached events in `order_events_df()`.

**Test count:** 653 passed, 3 skipped (PostgreSQL).

## Phase fidelity-5 — Exact sizing + ADV-tier enforcement (2026-05-18)

**Branch:** `phase-fidelity-5-sizing-and-adv` (merged into dev)

**Changes:**

- `PortfolioConfig` extended: `sizing_mode` accepts `equal_slice`,
  `risk_per_trade`, `legacy_fixed_notional`. New fields: `bankroll_dollars`,
  `equal_slice_per_position`, `equal_slice_bankroll_fraction` (null =
  auto-couple to max_gross_exposure_pct), `target_risk_dollars`,
  `max_per_trade_dollars`, `min_order_notional`, `expected_stop_slippage_pct`.
  `per_trade_notional` is now optional (only required for legacy mode).
- New `sim/sizing.py`:
  - `resolve_per_trade_dollars(portfolio)` → equal_slice math
    (`fraction × bankroll / max_concurrent`); legacy fallback when
    `bankroll_dollars=None` keeps pre-Phase-5 tests passing.
  - `resolve_qty_risk_per_trade(...)` →
    `floor(target_risk / (close × (stop_pct + slip_pct)))`.
- `BowakaPortfolioBacktester._qty_for` rewritten:
  routes through the resolver; applies `max_per_trade_dollars` clamp and
  `min_order_notional` floor.
- `_maybe_apply_realism_cap` now returns `(qty, diag)` with
  `adv_tier_index`, `adv_cap_dollars`, `adv_cap_qty`, `adv_cap_reason`.
  Diagnostics merge into the engine's `fill_diag` for reporting.
- `_check_shadow_risk` rebased on `_cached_per_trade_dollars` so the
  thresholds keep working when `per_trade_notional` is null.
- Exact-mode invariants extended: require `sizing_mode='equal_slice'`,
  explicit `bankroll_dollars`, explicit `equal_slice_bankroll_fraction`.
- Exact YAML profile populated with `bankroll_dollars=90000`,
  `equal_slice_bankroll_fraction=0.80` (so per-trade = $4000 at N=18).

**Tests added:**

- `tests/unit/test_sizing_equal_slice.py` (9 tests): explicit/auto fraction,
  fallback to legacy per_trade_notional, bad fraction, risk_per_trade
  math, legacy mode, validation guards.
- `tests/unit/test_adv_tier_enforcement.py` (6 tests): reject_if_below,
  tier walk to $1M-$5M bucket, null catch-all, empty-tiers flat fallback,
  missing-ADV diagnostic, min_order_notional floor.
- `tests/unit/test_exact_mode_sizing_invariants.py` (4 tests): exact YAML
  passes; sizing_mode / bankroll / fraction violations each raise.

**Test count:** 672 passed, 3 skipped (PostgreSQL).

## Phase fidelity-6 — Source-aligned signal-fade scoring (2026-05-18)

**Branch:** `phase-fidelity-6-signal-fade` (merged into dev)

**Pragmatic deviation from spec:** The prompt called for a discriminated
union `signal_fade: SourceSignalFadeConfig | ResearchIntradayFadeConfig`
that would replace the legacy `SignalFadeConfig`. Replacing the existing
type would break ~25 tests that reference it. I added a sibling field
`source_signal_fade: SourceSignalFadeConfig | None` on
`BowakaBacktestConfig` instead, leaving the legacy integer-score
`SignalFadeConfig` untouched. The exact-mode invariant routes through the
new field; research mode keeps using the legacy hypothesis. Net behavior
matches the prompt's spirit (separate exact-mode contract vs research-only
hypothesis) without the test churn.

**Changes:**

- New `sim/source_signal_fade.py`:
  - Verbatim `_FADE_COMPONENTS` spec.
  - `compute_source_fade_score(features, signal_gates, weights=None)`
    returns `(score_in_[0,1], component_results)`.
  - `source_fade_score_to_band(score, *, soft, hard, critical)` →
    hold / soft / hard / critical.
- New `SourceSignalFadeConfig` Pydantic model (enabled / eval_time /
  telemetry_time / score_thresholds / exit_on / score_weights).
- `BowakaBacktestConfig.source_signal_fade: SourceSignalFadeConfig | None`
  field. Legacy `signal_fade` field untouched.
- Exact-mode invariant: `source_signal_fade` must be configured + disabled
  (mirrors source paper-mode YAML).
- Exact YAML populated with `source_signal_fade.enabled=false`, default
  thresholds soft 0.34 / hard 0.50 / critical 0.67, `exit_on=[hard,critical]`.

**Tests added:**

- `tests/integration/test_source_fade_parity.py` — 4 parameterized cases
  (all_pass, three_fail, all_fail, missing_feature) match the source
  excerpt at `tests/fixtures/source_compute_fade.py`. Boundary tests for
  band thresholds.
- `tests/unit/test_source_signal_fade_invariants.py` — exact profile
  loads, missing source_signal_fade raises, enabled=true raises.

**Test count:** 686 passed, 3 skipped (PostgreSQL).

## Phase fidelity-7 — Counterfactual entry rules + liquidity proxy fix (2026-05-18)

**Branch:** `phase-fidelity-7-counterfactuals-and-liquidity` (merged into dev)

**Changes:**

- `sim/counterfactuals.py`:
  - New `_entry_bar_for_opening_range_break(...)` — uses the first
    `or_window_minutes` bars as the opening range and returns the first
    subsequent bar with `high > or_high × (1 + breakout_buffer_pct)`.
  - New `_entry_bar_for_vwap_reclaim(...)` — computes cumulative VWAP from
    session open and returns the first bar where `open < vwap` and `close
    > vwap × (1 + reclaim_threshold_pct)`.
  - New `_find_entry_bar(rule, bars, trade_date)` dispatcher. Replaces the
    silent 09:45 fallback in `simulate_variant`.
  - `_entry_time_for_rule` now raises on non-fixed-time rules instead of
    silently returning 09:45.
  - `simulate_variant` returns `would_enter=False, exit_reason='no_breakout'`
    or `'no_reclaim'` when the OR / VWAP helpers find no entry bar.
- `notebooks/_build_08_liquidity_and_execution_quality.py`:
  - Title rewritten to spell out three independent proxies + the fact that
    the old `abs(exit_price - entry_price)` was an analysis bug.
  - `SPREAD_BUCKETS_CELL` now declares `quote_spread_bps`,
    `entry_minute_range_bps`, `first_minute_range_bps` columns (each left
    NaN where the underlying data isn't yet wired) and prints
    per-proxy availability instead of bucketing on a fake proxy.

**Tests added:**

- `tests/unit/test_counterfactual_or_break.py` (8 tests): OR-break first
  breakout, no-breakout returns None, buffer threshold, dispatcher routing,
  VWAP reclaim with dip → entry, VWAP no-dip → None, unknown rule raises,
  OR-vs-fixed-time differ for the same fixture (proves the silent-fallback
  bug is fixed).
- `tests/unit/test_notebook_08_no_outcome_range_proxy.py`: builder must
  not contain `(exit_price - entry_price)`; must declare the three new
  proxy columns.

**Test count:** 696 passed, 3 skipped (PostgreSQL).
