# Phase 6 — Scan-matrix runtime (research-only, default-off, parity-gated)

Speedup report v2 §4 P6, §6.1, §11.2 Phase 6.

## What landed

- **Memory estimator fix** (`scanner/scan_matrix.py`):
  `_estimate_matrix_size_gib(..., eligible_symbols_by_session=None)` —
  when the PIT map is supplied the estimate uses `max(len(eligible))`
  across the supplied sessions (the prompt's "7× understatement"
  guard). `build_scan_matrix` probes the first ≤5 sessions of the
  resolved scope via `build_pit_universe_for_sessions(...)` +
  `eligible_symbols(...)` and passes that map into the estimator;
  the legacy hard-coded `est_n_symbols=100` is preserved as a
  conservative fallback when the probe fails.
- **`MatrixRuntimeCompatibilityMode`** (`scanner/scan_matrix_runtime.py`)
  — the parity-bridge class for `runtime_mode='compatibility'`.
  Construction is admitted so callers can probe the API surface and
  the Phase 6 parity tests target it; `evaluate_one_scan_compat`
  raises `MatrixRuntimeNotImplementedError` with an actionable
  message until the per-symbol dict reconstruction + gate ordering
  + event_id determinism parity proof against `evaluate_one_scan`
  is shipped.
- **Three-mode `runtime_mode` config field**: `"disabled"` (default,
  legacy scanner) / `"compatibility"` (matrix-backed parity bridge)
  / `"vectorized"` (numpy gate masks). `resolve_runtime_mode(cfg)`
  reads + normalises (lowercases + raises on unknown values so a
  typo never silently degrades to disabled).
- **`assert_backtester_matrix_opt_in_is_supported`** refactored:
  * `enabled=False` OR `runtime_mode='disabled'` → no-op (the matrix
    can be built for inspection without firing the runtime path).
  * `runtime_mode='vectorized'` without the parity manifest →
    `MatrixParityManifestMissingError`.
  * `runtime_mode='vectorized'` WITH the manifest → still refused
    pending the parity proof.
  * `runtime_mode='compatibility'` → refused with the actionable
    message pointing at the legacy default.
- **`scanner/scan_matrix_vectorized.py`** (new scaffolding) —
  `evaluate_one_scan_vectorized(...)` exists for parity-test targeting
  + future implementation; raises
  `MatrixRuntimeNotImplementedError` for the same reason as the
  compatibility-mode evaluator.
- **`runtime_mode: disabled`** emitted by the importer in every
  `--purpose optuna` config; the 3 committed optuna configs +
  4 workstation overlays were regenerated.
- **`backtester.py`** opt-in now resolves `runtime_mode` +
  `require_parity_manifest` and passes them to the guard so
  `enabled=True` + the default `runtime_mode='disabled'` is admissible
  (Phase 6 lets the matrix be built for inspection without firing the
  runtime path).
- **`ProfileCounters.scanner_symbol_evals`** — cumulative `int`
  counter; bumped by both the legacy + matrix evaluators (when they
  exist) so a benchmark can compare per-scan symbol-eval work
  directly.

## Existing tests updated

- `tests/unit/scanner/test_scan_matrix_runtime_opt_in_guard.py` —
  `test_assert_enabled_raises` renamed to
  `test_assert_enabled_with_non_disabled_runtime_mode_raises` and now
  passes `runtime_mode="compatibility"`. Adds the new
  `test_assert_enabled_with_default_runtime_mode_is_a_no_op` to lock
  in the Phase 6 admission semantic.
- `test_backtester_refuses_matrix_enabled_at_run_start` config now
  sets `runtime_mode: compatibility` so the guard fires.

## New tests

- `tests/unit/scanner/test_scan_matrix_memory_estimate_uses_actual_pit_symbols.py`
  (4): PIT map increases the estimate; absent map preserves legacy;
  smaller PIT counts keep the conservative `n_symbols` floor; 700
  eligible symbols produce a ~7× legacy estimate ratio.
- `tests/unit/scanner/test_scan_matrix_runtime_mode_resolution.py`
  (6): default is disabled; explicit disabled / compatibility /
  vectorized resolve; case-insensitive; unknown mode raises.
- `tests/unit/scanner/test_scan_matrix_runtime_refuses_non_disabled_modes.py`
  (6): disabled is a no-op; vectorized w/o manifest →
  `MatrixParityManifestMissingError`; vectorized w/ manifest →
  `MatrixRuntimeNotImplementedError`; compatibility refused;
  `MatrixRuntimeCompatibilityMode` constructible but evaluator
  refused; legacy `evaluate_one_scan_from_matrix(_vectorized)`
  stubs still refuse + the new `evaluate_one_scan_vectorized` stub.
- `tests/integration/test_scan_matrix_runtime_mode_disabled_is_default.py`
  (parametrized across every `configs/bowaka_v2_*.yml`): every
  committed config defaults `runtime_mode` to `"disabled"`.

## Deferred to follow-up

The compatibility-mode parity bridge
(`MatrixRuntimeCompatibilityMode.evaluate_one_scan_compat`) and the
vectorized gate evaluator (`evaluate_one_scan_vectorized`) are
scaffolding-only in this build. Implementing them requires:

1. Reconstructing per-symbol `session_bar` / `forming_feats` dicts
   from the matrix partition's `dyn_float64` / `dyn_int64` /
   `dyn_uint8` columns in the SAME arithmetic order the legacy
   loop uses.
2. Routing through the existing `apply_v2_gates` /
   `compute_signal_strength` (no gate re-implementation).
3. `build_candidate_event` with byte-identical event IDs.
4. Vectorized version: numpy boolean masks per gate + stable
   argsort on scores + per-row event construction.

The parity tests `test_scan_matrix_feature_row_parity`,
`test_scan_matrix_full_session_candidate_parity`,
`test_scan_matrix_full_fold_backtest_parity` from the prompt are
ALSO deferred — they need the parity bridge in place. The Phase 6
scaffolding's refusal at the backtester opt-in boundary ensures no
production caller can enable these modes silently; the deferred work
is documented for the next remediation pickup.

## Tests

| Gate | Result | Time |
|---|---|---|
| `make test-fast` | **1048 passed**, 0 failed | 46.4s |
| `make test-integration` (timeout=300) | **348 passed**, 2 skipped (PG-gated), 15 deselected (live + slow) | 13:37 |

## Default-off discipline

- `optuna.acceleration.scan_matrix.enabled` remains `false` in every
  committed config.
- `optuna.acceleration.scan_matrix.runtime_mode` defaults to
  `"disabled"` in every committed config (asserted by
  `test_scan_matrix_runtime_mode_disabled_is_default`).
- `enabled=True` + `runtime_mode='disabled'` is admissible — the
  matrix can be precomputed via `bowaka-v2-lab scan-matrix build`
  without firing the runtime path.

## Branch

`feature/phase-6-scan-matrix-runtime` — merged to `dev` with `--no-ff`.
