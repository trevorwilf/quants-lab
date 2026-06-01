# Phase 6 (scan-matrix runtime) — acceptance criteria

> **Provenance.** Extracted verbatim from the "Phase 6" section of the Claude Code
> prompt `bowaka_v2_lab_optuna_speedup_v2_claude_code_prompt.md` (now archived at
> `docs/old_cc_prompts/`, gitignored). This is the *original acceptance criteria +
> "research-only" framing* — the tasks, the required parity tests, and the rule that
> the path ships default-off. It is **not** the engineering spec proper; that lives in
> `docs/audits/2026-05-24_bowaka_v2_full_scan_feature_matrix_precompute.md` (column
> schemas, dtype policy, partition layout, manifest format, gate-ordering invariants).
>
> Phase 6 is **deferred / scaffolding-only** as of this writing — see
> `phase-6-scan-matrix-runtime-handoff.md`. The parity bridge and the vectorized gate
> evaluator are not built. This doc is the acceptance contract for whoever picks it up.

---

## Phase 6 — Scan-matrix runtime (research-only, default-off, parity-gated)

**Branch.** `feature/phase-6-scan-matrix-runtime` off `dev`.

**Goal.** Ship the four research deliverables for the scan-matrix path: (1) correct memory estimator using actual PIT symbol counts, (2) runtime *compatibility* mode that produces per-scan candidate events identical to the existing `evaluate_one_scan(...)`, (3) full session and fold parity tests, (4) vectorized gate evaluation behind a parity-checked switch. The report explicitly classifies this as research-only: this phase **does not flip the default** and **does not enable** matrix runtime in any merged config. The deliverables and tests are what land; the operator decides when to use them after evaluating the parity results.

**Reference.** Report §1.2 (do not enable yet), §4 P6, §6.1, §10.x, §11.2 Phase 6, §13 PR-equivalent risk.

### Tasks

1. **Memory estimator fix.**
   - In `src/bowaka_v2_lab/scanner/scan_matrix.py:_estimate_matrix_size_gib(...)` and the call site at lines 680-687: replace the hard-coded `est_n_symbols = 100` with the actual point-in-time eligible-symbol count for the resolved sessions.
   - Concretely: pass `eligible_symbols_by_session: Mapping[date, Sequence[str]]` into the estimator (already computable from `build_pit_universe_for_sessions(...)`) and use `max(len(eligible_symbols_by_session.get(s, ())) for s in sessions)` as `est_n_symbols`. Document the change in a comment referencing report §4 P6 ("about 704 eligible on 2025-08-27 vs the hard-coded 100, a 7x understatement").
   - Update `_estimate_matrix_size_gib(...)`'s signature so existing callers that do not have eligible-symbol context can still pass an explicit override; default behaviour is the corrected one.

2. **Runtime compatibility mode.**
   - In `src/bowaka_v2_lab/scanner/scan_matrix_runtime.py` (currently a stub that raises `MatrixRuntimeNotImplementedError` at lines 81, 113, 131): implement a `MatrixRuntimeCompatibilityMode` class whose `evaluate_one_scan_compat(scan_ts, eligible_symbols, matrix_partition) -> list[CandidateEvent]` returns a candidate-event list **field-by-field equal** to what `scanner/scan_loop.py:evaluate_one_scan(scan_ts, eligible_symbols, daily_cache, bars_supplier, quote_supplier, cfg)` returns for the same inputs. The compat mode is the parity bridge: it uses the matrix's precomputed features in the same arithmetic order the loop uses, with identical tie-breaking and identical skip-reason strings.
   - Keep the `MatrixRuntimeNotImplementedError`-raising symbols for the *vectorized* gate path (task 4 below). The compatibility mode is a separate class that does not raise; it is opt-in via `optuna.acceleration.scan_matrix.runtime_mode: Literal["disabled", "compatibility", "vectorized"] = "disabled"`.

3. **Config wiring.**
   - In the existing `optuna.acceleration.scan_matrix` block (already present, see `bowaka_v2_actual_iex_current_code_optuna.yml:80-92`):
     ```yaml
     optuna:
       acceleration:
         scan_matrix:
           enabled: false                     # existing
           runtime_mode: disabled             # NEW — disabled | compatibility | vectorized
           require_parity_manifest: true      # existing
           # ... existing fields preserved
     ```
   - `runtime_mode` consumers:
     - `disabled` (default): scanner uses `evaluate_one_scan(...)` directly. No matrix used at runtime. Pre-existing behaviour.
     - `compatibility`: scanner consults `MatrixRuntimeCompatibilityMode.evaluate_one_scan_compat(...)`. Matrix partition must exist (built ahead of time by `scan_matrix.build_session_partition(...)`).
     - `vectorized`: scanner consults the vectorized gate path (task 4). Requires the parity manifest to be present (`scan_matrix.require_parity_manifest: true` → reject runtime if manifest missing).
   - In `src/bowaka_v2_lab/sim/backtester.py`, find the existing opt-in check at lines 717-731 (matrix backtester branch) and switch from a binary flag to the three-mode resolution. Keep the existing `MatrixRuntimeNotImplementedError` raise for any mode that fails parity at the manifest level.

4. **Vectorized gate evaluation (behind parity manifest).**
   - File: `src/bowaka_v2_lab/scanner/scan_matrix_vectorized.py`. Public:
     ```python
     def evaluate_one_scan_vectorized(
         scan_ts: pd.Timestamp,
         eligible_symbols: Sequence[str],
         matrix_partition: MatrixPartition,
         cfg: Mapping[str, Any],
     ) -> list[CandidateEvent]: ...
     ```
     Implement gate evaluation as numpy vector ops over `matrix_partition` columns: each gate (signal threshold, ATR cap, RVOL window, ema_slope, gap_pct, etc.) is a boolean mask. Compose via `&`/`~`. Candidate events are constructed in the same order as the row indices in the matrix partition (which must mirror the eligible-symbol order from compat mode). Skip reasons are tracked by per-gate masks: the **first** gate that drops a symbol determines its `skip_reasons[0]` — this is how `evaluate_one_scan` orders skip reasons in the legacy path.
   - The vectorized path **must not be enabled in any merged config**: `runtime_mode` defaults to `disabled` everywhere. The path exists for research and benchmarking only.

5. **Parity tests.**
   - The expert report calls for: `test_scan_matrix_feature_row_parity` (may already exist — expand), `test_scan_matrix_full_session_candidate_parity`, `test_scan_matrix_full_fold_backtest_parity`, `test_scan_matrix_memory_estimate_uses_actual_pit_symbols`. Implement all four if missing; expand if present.

6. **Profile counters.**
   - Add `scanner_symbol_evals` (count of `(symbol, scan_ts)` pairs evaluated by the scanner, regardless of path). Same default-off pattern.

### Tests (new or expanded)

- `tests/unit/scanner/test_scan_matrix_memory_estimate_uses_actual_pit_symbols.py`
  - Build a tiny eligible-symbol map with sessions of varying counts (e.g. 50, 80, 200 eligible). Call the estimator. Assert it uses `max(counts) == 200`, not the legacy `100`.
  - Assert `MemoryBudget.assert_launch_safe(est_size_gib)` raises when the corrected estimate exceeds the budget but the legacy estimate would not have (this is the "7x understatement" guard).

- `tests/parity/test_scan_matrix_feature_row_parity.py`
  - For a fixture session and a fixture matrix partition: assert every feature column the matrix exposes equals the legacy `evaluate_one_scan(...)` per-symbol feature computation within `1e-12`.

- `tests/parity/test_scan_matrix_full_session_candidate_parity.py`
  - Run `evaluate_one_scan(...)` over a full fixture session's scan-time grid. Run `MatrixRuntimeCompatibilityMode.evaluate_one_scan_compat(...)` over the same grid against the precomputed matrix partition. Assert the lists of `CandidateEvent` are equal element-by-element (symbol, timestamp, score within `1e-12`, skip_reasons exact list-equality, ordering exact).
  - Then run `evaluate_one_scan_vectorized(...)` over the same grid; assert the same equality (vectorized must match compat which matches legacy).

- `tests/parity/test_scan_matrix_full_fold_backtest_parity.py`
  - Run a full one-fold backtest in three modes: `runtime_mode=disabled` (legacy), `compatibility`, `vectorized`. Assert: identical `FoldResult` fields, identical `daily_equity`, identical trade list (price/qty/timestamp exact). Use the global parity tolerance for floats.

- `tests/integration/test_scan_matrix_runtime_mode_disabled_is_default.py`
  - Load every config in `configs/`. Assert `optuna.acceleration.scan_matrix.runtime_mode == "disabled"` in all of them (or absent, which the loader defaults to `disabled`).

- `tests/unit/scanner/test_scan_matrix_runtime_requires_parity_manifest.py`
  - With `runtime_mode="vectorized"` and `require_parity_manifest: true` but no manifest file present: assert `MatrixRuntimeNotImplementedError` (or a clearer `MatrixParityManifestMissingError`) is raised at backtester startup, before any scan loop runs.

### Acceptance

- `make test-fast`, `make test`, `make test-integration`, `make test-reconcile` green.
- All Phase 6 parity tests pass on the fixture.
- `optuna.acceleration.scan_matrix.runtime_mode` defaults to `disabled` in every config under `configs/`.
- No production behaviour change. The vectorized path exists, is correct on the fixture, and is not enabled.
