I now have comprehensive coverage. Let me produce the final report.

## Purpose & data flow (how this subsystem fits the backtest pipeline)

`config_universe` is the entry stage of the v2 backtest: it (1) turns the frozen live-strategy contract into runnable lab YAML, validates/loads it, and audits any divergence; and (2) builds the per-session point-in-time (PIT) tradable universe the scanner/backtester operate on.

- **Contract → config**: `reference/__init__.py` freezes the live `bowaka_v2_config.yaml` into `actual_bowaka_v2_contract.yaml` (sections + source-file hash manifest). `reference/import_config.py:build_config_from_contract` maps that contract into a `BowakaV2Config` dict; `import_actual_config` validates and writes the YAML (+ optional sip_tightened sidecar). The shipped `configs/bowaka_v2_intended_realism.yml` and `bowaka_v2_actual_sip_intended_realism.yml` are outputs of this mapper (currently byte-identical to each other).
- **Load/validate**: `config/loader.py:load_config` expands env vars, rejects unknown top-level keys, refuses `quarantined/` paths, and rejects ambiguous `same_symbol_entries_per_day`. `config/models.py` (Pydantic v2, `extra="forbid"`) enforces invariants and resolves mode-coupled policy defaults.
- **Parity gate**: `config/config_diff.py` flattens lab cfg vs contract leaf-by-leaf; `config/parity_sidecar.py` layers declared-diff classification on top. `undeclared_diff_paths` is the hard refusal gate for intended_realism/optuna runs.
- **PIT universe**: `universe/builder.py:build_pit_universe` reads the lake asset master + strictly-prior daily bars to produce one `UniverseRecord` per symbol; `to_scanner_snapshot`/`eligible_symbols`/`universe_hash`/`dq_cache_symbol_set`/`funnel` feed the scanner, DQ cache, and reports.

Note: there are **two** universe builders — the PIT `universe/builder.py` (live path) and a legacy `scanner/universe_builder.py:build_universe_snapshot` (used by `data/universe_pit.py` and `test_universe_pit_snapshot.py`).

## Behavioral spec

**PIT universe builder (`universe/builder.py`)**
- Filters applied in fixed order, **non-short-circuiting** (all applicable reasons recorded): exchange→OTC→instrument-class→blocklist→price-band→ADV→delisting (builder.py:552-592).
- `prior_close`/`prior_adv` computed only from sessions `< session_date` via `searchsorted(..., side="left")` (builder.py:401-411) — no current-day leakage.
- ADV = mean of trailing-20 `close*volume` over prior sessions (`_ADV_WINDOW=20`, builder.py:68, 406-410).
- Full per-symbol daily history is read once 1970→today and **process-local cached** keyed by `(lake_root, symbol, feed, adjustment)` (builder.py:324-359).
- `daily_adjustment` resolved from cfg via `daily_adjustment_for_config` (builder.py:502); split/adjusted requirement forces `split_adjusted` (adjustment.py:26).
- Instrument classification is a name+symbol-suffix **heuristic** (builder.py:126-168): name keywords (inverse before leveraged), ETF-family issuers, then 5th-letter W/U/R suffix → `heuristic` unless name reads operating. Excluded classes always dropped; `heuristic` honors `unknown_instrument_class_policy` (builder.py:561-567).
- `exclude_otc` defaults True; OTC venues frozenset (builder.py:49, 557).
- Allowed exchanges default `NASDAQ/NYSE/AMEX/ARCA/BATS`; unknown exchange → `exchange_not_allowed`; venue code maps via `_VENUE_CODE_BY_EXCHANGE`, defaulting `XNAS` (builder.py:236).
- `no_prior_bar` when `prior_close is None`; ADV gate also fires `adv_below_min` when `prior_adv is None` and not already `no_prior_bar` (builder.py:583-588).
- Delisting: `_status_active` treats `active`/`active_tradable`/**empty string** as active (builder.py:446-448).
- Loud warning (not error) when NO symbol has a prior bar — diagnoses raw-vs-split adjustment mismatch → empty universe (builder.py:531-539).
- `universe_hash` = sha256 of sorted eligible symbols (builder.py:634-641); `to_scanner_snapshot` emits `synthetic: False` (builder.py:668); `dq_cache_symbol_set` shape-robust over raw vs snapshot shapes (builder.py:671-698).

**Contract→config mapper (`reference/import_config.py`)**
- universe MAP: only `price_min/max`→`min/max_price`, `avg_dollar_volume_min`→`min_adv_dollars`; hardcodes `asset_classes=["operating_equity"]`, `exclude_pattern_class=True` (import_config.py:177-183).
- scanner: copies every contract scanner key verbatim, `setdefault min_signal_strength=0.0` (import_config.py:191-192).
- execution MAP: `parent_order_style`→`order_type`, `marketable_limit_slippage_pct*10000`→`limit_offset_bps`, `quote_gate.max_spread_pct*10000`→`max_spread_bps` (import_config.py:204-210).
- signals/sizing/risk/exits copied verbatim; sip_tightened overlays 5 thresholds (import_config.py:198-201).
- market_data threads `require_adjusted_daily_bars`/`require_split_adjustment`/`max_bar_age_seconds`/`max_quote_age_seconds` from contract `data:` (import_config.py:221-232).
- optuna purpose injects full optuna/finalist blocks with hardcoded backtest dates `2023-11-27→2026-05-20` (import_config.py:270-373).
- `regenerate_generated_configs` keys off the `GENERATED bowaka_v2 lab config` marker, recovers args from file content, rewrites in place (import_config.py:456-496).

**Loader/models** — env `${VAR:-default}` expansion (loader.py:48-63); mode-coupled policy resolution table (models.py:29-148); realism modes require full signal-gate set + explicit `require_adjusted_daily_bars` (models.py:601-654).

## Knobs

- `universe.allowed_exchanges` (default `NASDAQ/NYSE/AMEX/ARCA/BATS`) — builder.py:205-209.
- `universe.exclude_otc` (default True) — builder.py:557.
- `universe.ticker_blocklist` (additive to `TSLL/CONL/SMCX`) — builder.py:212-216.
- `universe.price_min/max` aka `min_price/max_price` (defaults 1.0/20.0) — builder.py:219-226; schema models.py:206-207.
- `universe.avg_dollar_volume_min` aka `min_adv_dollars` (default 250_000) — builder.py:229-232; models.py:208.
- `universe.asset_classes` (default `["operating_equity"]`), `exclude_pattern_class` (True), `symbols` (None) — models.py:205-210; only consumed by the legacy `scanner/universe_builder.py`, NOT by PIT builder.
- `market_data.feed` (iex|sip) — builder.py:498; `require_split_adjustment`(False)/`require_adjusted_daily_bars`(None) → adjustment.py.
- `simulation.unknown_instrument_class_policy` (mode-resolved fail_open/fail_closed) — builder.py:508, 565.
- Loader: unknown top-level keys rejected (loader.py:18-45,109); `preflight`/`finalist_evaluation` allowed.

## Invariants & guards

- `extra="forbid"` strict models reject unknown keys (models.py:18-19).
- Mode validators: realism modes require all signal gates set (models.py:601-624) and explicit `require_adjusted_daily_bars` (models.py:626-654) — **fail-loud**.
- `_assert_not_quarantined` raises on quarantined path (loader.py:76-92) — fail-loud.
- `_assert_same_symbol_entries_unambiguous` raises `ConfigParityError` on dual definition (loader.py:126-151) — fail-loud.
- `assert_source_manifest_unchanged` raises on source drift (reference/__init__.py:266-318) — fail-loud.
- `undeclared_diff_paths` non-empty → refusal gate (parity_sidecar.py:221-232) — fail-loud.
- `load_parity_sidecar`/`load_parity_overrides` raise on malformed sidecar (parity_sidecar.py:108-127) — fail-loud.

**Silent fallbacks (flagged):**
- builder.py:355-356 — `_full_daily_history` swallows ANY exception from `daily_bars` → empty DataFrame → symbol silently gets `(None,None)` → `no_prior_bar`. A transient lake read error silently drops a symbol.
- builder.py:429-438 — `_load_asset_master` swallows exceptions on `latest_snapshot_id`/`assets` → empty master → `build_pit_universe` returns `{}` (builder.py:516-517) = empty universe with **no warning** (the loud NO-prior-bar warning at 531 never fires because `symbols` is empty).
- builder.py:236 — unknown exchange silently maps venue_code to `XNAS` default (forensic field, but still a silent default).
- builder.py:447-448 — `_status_active` treats **empty/blank status** as active (silent keep) — a master with a missing status column never delists.
- loader.py:60-61 — unresolved `${VAR}` (no default) left verbatim, only "caught" downstream.
- import_config.py:207,209 — `float(... .get(key, 0.0))` defaults missing slippage/spread to 0.0 silently → `limit_offset_bps=0`/`max_spread_bps=0` if contract key absent.
- adjustment.py:26 — `require_adjusted_daily_bars` (point/dividend adjust) silently mapped to `split_adjusted` (split-only), conflating two adjustment kinds.

## Leads

- **builder.py:355-356** — bare `except Exception` on `daily_bars` silently converts read errors into `no_prior_bar` rejection; a partial lake outage silently shrinks the universe (realism gap).
- **builder.py:434-438** — `_load_asset_master` swallows `assets()` errors → empty universe returned silently (builder.py:516); the diagnostic warning at 531 is bypassed. Empty-universe-from-error is indistinguishable from genuinely-empty.
- **builder.py:447-448** — `_status_active("")` → True. If the asset master lacks/blank `status`, every symbol passes the delisting gate; survivorship guard becomes a no-op silently.
- **import_config.py:177-183** — contract `universe.allowed_exchanges`, `exclude_otc`, `ticker_blocklist`, and all the `exclude_etf/etn/...` flags are **NOT mapped** into the lab universe config (only price/ADV/asset_classes are). The PIT builder relies on its own hardcoded `DEFAULT_ALLOWED_EXCHANGES`/`DEFAULT_TICKER_BLOCKLIST` instead of the contract values — if the live contract changes its blocklist/exchanges, generated configs won't carry it (parity gap; config_diff only diffs keys present on both sides so it won't flag the omission either, config_diff.py:138-139).
- **builder.py:51 vs contract** — `DEFAULT_TICKER_BLOCKLIST=("TSLL","CONL","SMCX")` is hardcoded and additive; if contract `ticker_blocklist` diverges it's silently merged, never replaced. No way to *remove* a default-blocked ticker.
- **builder.py:236 / `_venue_code_for`** — unknown exchange defaults to `XNAS` (NASDAQ) even for a symbol already flagged `exchange_not_allowed`; mislabels venue in forensics.
- **adjustment.py:22-26** — `require_adjusted_daily_bars: true` resolves to `split_adjusted`, not a true total-return/dividend adjustment. The two contract flags (`require_adjusted_daily_bars`, `require_split_adjustment`) collapse to the same string — dividend adjustment is never actually applied (realism gap).
- **import_config.py:248-249** — backtest dates hardcoded `2024-09-01→2024-12-31` (and optuna `2023-11-27→2026-05-20`) baked into every generated config regardless of current lake range; stale as the lake grows (the YAML header even admits train=24 is infeasible).
- **config_diff.py:135-153** — `universe`/`scanner`/`execution` only diff keys present on BOTH sides; a contract key absent from the lab schema (e.g. `exclude_etf`, `halt_gate`, `price_chase_gate`, `score:` block) is **never** a mismatch → silent parity blind spot. The whole `score:` and `historical_features:` contract sections are not modeled in lab config at all.
- **models.py:386 + import_config.py:213-215** — `risk.max_concurrent_positions` is Optional and risk copied verbatim; the contract sets `sizing.max_concurrent_positions: 1` but `risk` reads from sizing only "Phase 5 wires the read" — verify the wiring actually happened.
- **import_config.py:191** — scanner copies `bar_source: openalgo`, `fetch_concurrency`, `alpaca_*` verbatim into lab configs (visible in shipped YAML lines 107-110) though the lab ignores them (accept-and-ignore per models.py:242-249); they pollute the generated config and the parity diff surface.
- **parity_sidecar.py vs config_diff.py** — TWO sidecar formats coexist: `<stem>.parity.yml` (`intentional_overrides`) and `<stem>.parity_sidecar.yaml` (`declared_diffs`). `load_parity_overrides` (config_diff.py:89-99) reads both; `load_parity_sidecar` reads only the latter. Divergent-format risk / dead-path ambiguity.
- **builder.py:276** — ADV uses `tail(_ADV_WINDOW).mean()` over available prior sessions; with <20 prior bars it averages whatever exists (e.g. 3 bars) with no minimum-history guard, unlike contract `data.min_history_trading_days: 45` (contract line 26) — that 45-day minimum is **not enforced anywhere** in the PIT builder (realism gap).
- **builder.py:154-166** — symbol-suffix heuristic: a genuine 5-char operating ticker ending W/U/R with a generic name (no INC/CORP) is misclassified `heuristic`→dropped under fail_closed (false exclusion in intended_realism).
- **scanner/universe_builder.py:49** — legacy builder defaults `max_price=1000.0`, `min_adv=1_000_000` (stale pre-remediation values, contradicting the live $20/$250k); `data/universe_pit.py` still calls this legacy path — dead/divergent code that could screen the wrong universe if used.
- **scanner/universe_builder.py:66-68** — `fillna(0)` on missing baselines silently treats a no-baseline symbol as price 0 → fails min_price (not `no_prior_bar`); divergent semantics from the PIT builder.
- **builder.py:321** — module-global cache `_PIT_DAILY_FULL_HISTORY_CACHE` never bounded/evicted; over a long process it holds full history for every symbol (memory growth; comment claims immutability within a study but no LRU).
- **models.py:610 + import_config.py:64** — mapper `CONFIG_MODES` excludes `fast_realism`, but model validators include it in realism requirements; generating a fast_realism config via the mapper is impossible though the schema supports it (capability gap).

## Test coverage hooks

- PIT builder: `test_universe_no_leakage.py`, `test_universe_price_band.py`, `test_universe_blocklist.py`, `test_universe_delisting.py`, `test_universe_etf_exclusion.py`, `unit/optuna/test_pit_universe_union.py`, `parity/test_dq_cache_key_symbols_parity.py` (covers `dq_cache_symbol_set` both shapes + empty), `integration/test_universe_snapshot_artifacts.py`, `test_universe_hash_in_candidate_events.py`.
- Config models/loader: `test_config_models.py`, `test_config_loader.py`, `test_simulation_mode_defaults_coupled.py`, `test_realism_mode_requires_full_signals.py`, `test_marketdata_config_require_adjusted_unset_for_realism_modes_raises.py`, `test_quarantined_optuna_config_not_loadable.py`.
- Mapper/diff/sidecar/parity: `test_import_actual_config_roundtrip.py`, `parity/test_config_parity_*`, `test_optuna_refuses_parity_diff.py`, `integration/test_config_diff_artifact.py`, `integration/test_regen_actual_configs.py`, `parity/test_three_generated_configs_byte_stable.py`, `parity/test_scanner_keys_in_generated_configs.py`, `parity/test_import_actual_config_emits_adjustment_flags.py`.

**Behaviors with NO direct test (flagged):**
- `_load_asset_master` exception-swallow → empty universe path (builder.py:434-438) — no test for lake-error-returns-empty.
- `_status_active("")`/missing-status-column → active (builder.py:447-448) — delisting tests only cover explicit `delisted/inactive/suspended`, not blank.
- `daily_bars` raising inside `_full_daily_history` (builder.py:355) — no test of the silent fallback.
- The NO-prior-bar diagnostic warning (builder.py:531-539) — no test asserts it fires.
- `funnel()` (builder.py:701-721) and `to_scanner_snapshot`'s `synthetic: False` marker — no dedicated unit test.
- `_venue_code_for` unknown-exchange → XNAS default — untested.
- ADV with <20 prior bars / missing `min_history_trading_days:45` enforcement — untested.
- `exclude_otc=False` override path (builder.py:557) — untested.
- `parity_sidecar.py` `classify_config_parity`/`undeclared_diff_paths` merge logic — no test file found targeting `parity_sidecar` directly (only `config_diff`-level parity tests).
- The contract→config **omission** of `allowed_exchanges`/`exclude_*`/`ticker_blocklist` — no test asserts these are (or should be) mapped.

Relevant files: `universe/builder.py`, `data/adjustment.py`, `scanner/universe_builder.py`, `data/universe_pit.py`, `config/models.py`, `config/loader.py`, `config/config_diff.py`, `config/parity_sidecar.py`, `reference/__init__.py`, `reference/import_config.py`, `reference/actual_bowaka_v2_contract.yaml`.