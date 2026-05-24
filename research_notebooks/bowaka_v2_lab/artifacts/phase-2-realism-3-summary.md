# Phase 2 — Source manifest hashing + explicit scanner config keys

**Branch:** `phase-2-realism-3-source-manifest-and-scanner-keys` off `dev`.
**Audit findings addressed:** P1-002 (contract hashes only the YAML), P1-003 (generated configs hide live scanner keys + `same_symbol_entries_per_day` plumbing).

## Changes

### 2.1 — Source-manifest extension
- `src/bowaka_v2_lab/reference/__init__.py` — `CONTRACT_SCHEMA_VERSION` bumped to 3. New `AUTHORITATIVE_SOURCE_FILES` constant lists every live source file the lab claims to replicate (config, strategy, scanner, features, schemas, backtest, universe builder).
- `compute_source_manifest(source_root)` — hashes every required file + any relative `bowaka_*` import statically discovered in `bowaka_v2_strategy.py` (uses `ast`, never executes). Raises `FileNotFoundError` with a recovery hint pointing at `mirror_bowaka_v2_source.ps1` when a required file is missing.
- `_hash_source_manifest(manifest)` — canonical-JSON SHA-256 over the manifest mapping.
- `build_contract_dict` extended to emit `source_manifest` + `source_manifest_hash` per the v3 schema.
- `source_manifest_hash()` — returns the frozen contract's manifest hash (or `""` when absent).
- `assert_source_manifest_unchanged()` — raises `ConfigParityError` listing every file that drifted / was added / went missing relative to the frozen contract. No-op for legacy v2 contracts; raises with a recovery hint when the live source tree cannot be located.

### 2.2 — Contract regenerated against the v3 schema
- `reference/actual_bowaka_v2_contract.yaml` — regenerated with the new `source_manifest` block (10 files: 7 authoritative + 3 statically-discovered `bowaka_*` imports). The contract sha256 now propagates to the failing-source test as well as the existing config-parity gate.

### 2.3 — Generated configs expose every live scanner key
- `src/bowaka_v2_lab/reference/import_config.py::build_config_from_contract` — the scanner block is now built by iterating `contract.scanner.items()` (was three hard-coded keys). Any key the contract grows automatically lands in every generated `bowaka_v2_actual_*.yml`.
- `src/bowaka_v2_lab/config/models.py::ScannerConfig` — extended with every live contract key (`enabled`, `debug_gate_dump`, `scan_interval_seconds`, `full_universe_refresh_interval_minutes`, `in_play_refresh_interval_seconds`, `signal_expiry_seconds`, `same_symbol_entries_per_day`, `symbol_cooldown_minutes`, `require_prior_daily_baseline`, `require_fresh_intraday_bar`). Defaults match the live contract.
- All six `configs/bowaka_v2_actual_*.yml` regenerated with the full scanner block.

### 2.4 — `same_symbol_entries_per_day` propagation
- `src/bowaka_v2_lab/sim/strategy_consumer.py::consume` — reads `scanner_cfg.get("same_symbol_entries_per_day", risk_cfg.get(..., 1))`. The scanner block is the canonical location per the live contract; the legacy `risk.` fallback stays for older configs the loader hasn't rejected yet.
- `src/bowaka_v2_lab/config/loader.py::_assert_same_symbol_entries_unambiguous` — raises `ConfigParityError` when a config sets the field in both `scanner` and `risk`.

### 2.5 — Tests
- `tests/parity/test_source_manifest_unchanged.py` — 3 tests: contract carries `source_manifest`, the rollup hash is correct, the manifest matches the live source tree. All `xfail` cleanly when the contract / source tree is unavailable.
- `tests/parity/test_scanner_keys_in_generated_configs.py` — 6 parametrized tests (one per `bowaka_v2_actual_*.yml`) asserting every contract scanner key is in the generated config. Plus one test that extends the loaded contract with an extra scanner value and asserts `build_config_from_contract` propagates it (proves the generator iterates the mapping, not a hard-coded list).
- `tests/parity/test_same_symbol_entries_per_day_propagation.py` — 4 tests: scanner-block read works, risk-block fallback works for legacy configs, both-blocks set raises `ConfigParityError`, default `ScannerConfig` carries the live value.

## Test results

| Group | Result |
|---|---|
| `tests/unit + tests/parity` | 774 passed (+14 vs Phase 1), 0 failed |
| `tests/integration + tests/reconcile` | 322 passed, 12 deselected, 0 failed (1 transient failure resolved by regenerating `configs/bowaka_v2_intended_realism.yml`) |
| `bowaka_common` | 97 passed (unchanged) |
