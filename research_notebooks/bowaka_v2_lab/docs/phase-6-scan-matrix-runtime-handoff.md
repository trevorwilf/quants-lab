# Phase 6 (scan-matrix runtime) — engineering hand-off

**Audience:** quant analysts + software engineers picking up the
Phase 6 scan-matrix-runtime work on the `bowaka_v2_lab` codebase.

**Goal of Phase 6:** make the walk-forward Optuna study fast enough
to run **5,000–10,000 trials in under 24 hours** on the workstation
profile, **without fidelity degradation** vs the legacy scanner.

**Current state of the project (updated 2026-06-16): SHIPPED.** The parity bridge
and the vectorized gate evaluator are built and live (`scan_matrix_vectorized.py`,
`runtime_mode: vectorized`), parity-locked by the three-way tests — see
`speedup_phase_6_completion_summary.md`. This handoff is retained for the §7
parity-test list + design rationale; the "not built / scaffolding" framing below is
historical (pre-implementation).

This document is a self-contained briefing. Every other Phase 6
artifact is listed at the end under
[§9 Documents to read](#9-documents-to-read).

---

## 1. Why Phase 6 is necessary

The walk-forward Optuna study performance budget is dominated by the
per-trial scanner loop:

| Stage | Approximate share of trial wall-clock |
|---|---|
| Fold context setup (amortized across trials in a worker) | ~3% |
| DQ rebuild on cache hit | ~1% |
| **Per-symbol gate evaluation in `evaluate_one_scan`** | **~92%** |
| Portfolio / fill / exit walk | ~4% |

Phase 1–5 in the Optuna speedup-v2 work (prompt archived at
`docs/old_cc_prompts/bowaka_v2_lab_optuna_speedup_v2_claude_code_prompt.md`)
attacked the 8% of overhead around the scanner. Phase 6 is the only
work that touches the 92%.

### 1.1 Speedup arithmetic

Current per-trial cost is ~38 minutes on the live IEX lake
(~703 eligible symbols × ~21 sessions × N scan times per session × 3
folds). For 10,000 trials in 24 hours on 8 workers:

```
target = 24h × 8 workers ÷ 10,000 trials = ~1.15 min/trial
required speedup = 38 / 1.15 ≈ 33×
```

**No fidelity-preserving lever produces 33×.** The realistic stack:

| Lever | Multiplier | Fidelity-preserving? |
|---|---|---|
| Phase 6 vectorized scanner | ~5–15× (estimate; uncertain) | ✓ if parity bridge passes |
| `workstation_16w` overlay | ~2× | ✓ if Postgres scales past 8 threads |
| Tighter `universe.min_adv_dollars` (703→~200 symbols) | ~3.5× | ✗ |
| Fewer scan times per session | ~N× | ✗ |
| Reduced sessions per fold | linear | ✗ |

The **only fidelity-preserving path** that yields >2× is Phase 6
vectorized mode. The compatibility-mode path is a smaller win
(~2–3× scanner) but is a foundational step toward vectorized.

### 1.2 What "fidelity" means here

The legacy `bowaka_v2_lab.scanner.scan_loop.evaluate_one_scan(...)`
function is the spec. A Phase 6 runtime is **fidelity-preserving**
when:

* The list of `CandidateEvent` objects it emits for any
  `(scan_ts, eligible_symbols)` input matches the legacy list
  field-by-field — same symbols, same timestamps, same scores
  within `1e-12`, same `skip_reasons` (including order), same
  event IDs.
* The downstream `BacktestResult` (trade list, daily equity, fold
  metrics) is identical at the global parity-tolerance floats
  (`1e-12` for trade prices/qty, `1e-9` for objective values).

The parity test files in `tests/parity/test_scan_matrix_*.py`
(see [§7 Parity tests](#7-parity-tests-the-acceptance-spec)) are the
machine-checkable form of this definition.

---

## 2. The three runtime modes

`optuna.acceleration.scan_matrix.runtime_mode` is a string field with
three values, defaulting to `"disabled"` in every shipped config:

| Mode | Behaviour today | Behaviour when Phase 6 ships |
|---|---|---|
| `disabled` | Legacy `evaluate_one_scan` path | unchanged |
| `compatibility` | Refused at backtester opt-in (`MatrixRuntimeNotImplementedError`) | Matrix-backed per-symbol evaluator returning byte-equal candidate events |
| `vectorized` | Refused (`MatrixParityManifestMissingError` w/o manifest; `MatrixRuntimeNotImplementedError` w/ manifest) | NumPy boolean-mask gate evaluation across all symbols at a scan |

The runtime-mode resolution is in
`src/bowaka_v2_lab/scanner/scan_matrix_runtime.py:resolve_runtime_mode`.

The backtester opt-in boundary that enforces "still refused" is in
`src/bowaka_v2_lab/sim/backtester.py` —
`assert_backtester_matrix_opt_in_is_supported(...)` is invoked when
`optuna.acceleration.scan_matrix.enabled` is true. With
`runtime_mode == "disabled"` (the committed default) the gate is a
no-op.

---

## 3. Build order (recommended)

Each step has a measurement gate before the next step starts.

### Step A — Production-load test the scan-matrix builder (1–2 days)

The Phase 8 builder (`scan_matrix.build_scan_matrix`) is already
fully shipped. CLI:

```bash
bowaka-v2-lab scan-matrix build --config configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml --scope validation
bowaka-v2-lab scan-matrix verify --store-root <path> --config <same>
```

**Expected outcome:** matrix partitions land at
`artifacts/cache/scan_matrix/validation/<session>/...`. The verify
subcommand compares random rows against the legacy feature
computation and reports drift.

**Pre-Phase-6 fixes you may hit:** the memory estimator was corrected
in Phase 6 step 1 (uses actual PIT symbol counts, not hard-coded
100), so the budget refusal is now realistic. The builder is serial
in this build — Phase 9 may parallelize it.

### Step B — Compatibility-mode parity bridge (2–4 days)

Implement `MatrixRuntimeCompatibilityMode.evaluate_one_scan_compat(
scan_ts, eligible_symbols)` in
`src/bowaka_v2_lab/scanner/scan_matrix_runtime.py`. **Requirement:**
the candidate-event list it returns is field-by-field equal to
`scanner.scan_loop.evaluate_one_scan` for the same inputs.

The class is constructible today (the parity tests can target it);
only the method body raises `MatrixRuntimeNotImplementedError`.

#### Algorithm (mirrors `evaluate_one_scan` exactly)

1. Resolve the per-session matrix partition for `scan_ts.date()`.
2. Resolve the scan-index `scan_idx` from the matrix's
   `scan_times[scan_ts]` lookup (matrix doc §4).
3. For each `symbol` in `eligible_symbols`:
   a. Look up the symbol's row index in the partition's
      `symbol_index` (matrix doc §5).
   b. Read the dynamic columns: `dyn_float64[col][scan_idx, row]`,
      `dyn_int64[col][scan_idx, row]`, `dyn_uint8[col][scan_idx, row]`.
   c. Read the static columns: `static_float64[col][row]`,
      `static_int8[col][row]`.
   d. **Reconstruct the per-symbol dicts** the legacy path produces:
      `session_bar = {...}` and `forming_feats = {...}`. Field names
      must match `scanner.scan_loop._build_session_bar` and
      `scanner.scan_loop._build_forming_feats` exactly. See the
      matrix doc §6 for the column→field mapping.
   e. Call the **existing**
      `scanner.gate_logic.apply_v2_gates(session_bar, forming_feats,
      cfg)` and `scanner.gate_logic.compute_signal_strength(...)`. Do
      not re-implement gate logic.
   f. Track skip reasons. **The first gate that drops a symbol owns
      `skip_reasons[0]`** — matches legacy ordering.
   g. Build the candidate event via
      `scanner.event_builder.build_candidate_event(...)`.
4. Apply scanner-state side effects identically to the legacy path
   (`signal_emits_per_symbol_today`, `symbol_last_emit_ts`).
5. Return the `CandidateEvent` list **in the order the legacy
   `passing.sort(key=lambda x: -x[0])` produces.** Use
   `np.argsort(-scores, kind="stable")` so tied scores keep the
   original index order — the legacy `sorted` is stable and the
   parity test `test_scan_matrix_stable_score_tie_order.py` pins
   this exact behaviour.

#### Wire it into the backtester

In `sim/backtester.py:_handle_scan` (search for the existing
`run_one_scan` call), branch on `resolve_runtime_mode(cfg_dict)`:

```python
runtime_mode = resolve_runtime_mode(cfg_dict)
if runtime_mode == "compatibility":
    compat = MatrixRuntimeCompatibilityMode(
        matrix_partition=ctx.scan_matrix_partition_for_session(session),
        cfg=cfg_dict,
    )
    candidate_events = compat.evaluate_one_scan_compat(
        scan_ts, eligible_symbols,
    )
else:
    candidate_events, scan_result = run_one_scan(...)
```

You will need to plumb the scan-matrix partition lookup onto
`FoldRuntimeContext` (currently absent). The matrix store is
opened once per fold context build; expose a method like
`partition_for_session(session_date)` that lazily loads the
mem-mapped `.npy` files.

Then remove the refusal in
`assert_backtester_matrix_opt_in_is_supported(runtime_mode=
"compatibility")` once the parity tests pass.

### Step C — Compatibility-mode parity tests (1–2 days)

The acceptance gates are the three parity tests in
`tests/parity/`:

* `test_scan_matrix_feature_row_parity.py` — every matrix column
  equals the legacy per-symbol feature computation within `1e-12`.
  Already passes for the builder; will keep passing as you don't
  change the matrix layout.
* `test_scan_matrix_full_session_candidate_parity.py` — run
  `evaluate_one_scan(...)` over a full fixture session and assert
  the resulting candidate-event list element-by-element equal to
  `MatrixRuntimeCompatibilityMode.evaluate_one_scan_compat(...)`
  over the same grid. Equality includes symbol, timestamp, score
  within `1e-12`, `skip_reasons` (exact list-equality),
  and ordering. This is your primary acceptance test for Step B.
* `test_scan_matrix_full_fold_backtest_parity.py` — run a full
  one-fold backtest in `runtime_mode=disabled` (legacy) and
  `runtime_mode=compatibility` modes. Assert identical
  `FoldResult` fields, identical `daily_equity`, identical trade
  list (price / qty / timestamp exact).

The tests are scaffolded with `MatrixRuntimeNotImplementedError`
markers today; remove the markers as you implement Step B.

### Step D — Vectorized gate evaluator (3–5 days)

Implement `evaluate_one_scan_vectorized(...)` in
`src/bowaka_v2_lab/scanner/scan_matrix_vectorized.py`. The body
**replaces** the per-symbol Python loop with NumPy mask operations
across all symbols at the scan:

1. Resolve matrix partition + `scan_idx` as in compatibility mode.
2. For each gate (signal threshold, ATR cap, RVOL window,
   ema_slope, gap_pct, etc.), build a boolean mask over the
   eligible symbols at `scan_idx`. Use the partition's `dyn_uint8`
   missing-value flags per matrix doc §6 — never NaN-compare.
3. Compose gate masks with `&` and `~`. The **first** gate that
   drops a symbol determines its `skip_reasons[0]`; track this by
   recording the rank at which each symbol was masked out.
4. Compute signal scores for the surviving rows (vectorized
   numerical compute on the matrix columns).
5. `np.argsort(-scores, kind="stable")` for the candidate event
   order.
6. Construct `CandidateEvent` objects row-wise for passing
   symbols. The order MUST match what the legacy `sorted(passing,
   key=lambda x: -x[0])` produces — matrix doc §17.3 is explicit.

#### Hard constraints from the matrix doc

* `MATRIX_SENSITIVE_PREFIXES` is the search-space-leaf list that
  invalidates the matrix. The runtime must refuse at the
  `assert_search_space_compatible_with_matrix(...)` check if any
  search-space override names a key under those prefixes. The
  constants are in `scanner.scan_matrix.MATRIX_SENSITIVE_PREFIXES`.
* Missing-value semantics use the per-column `dyn_uint8` validity
  flag. Gates mask on the flag before comparing the float column.
  See `test_scan_matrix_missing_value_gate_semantics.py` for the
  enforced behaviour.
* Holdout reads are gated via
  `ScanMatrixStore.assert_can_read(date, purpose=...)`. The runtime
  must declare `purpose="objective"` during tuning;
  `purpose="final_holdout"` is the one authorised reader of the
  holdout window. See
  `tests/unit/scanner/test_scan_matrix_holdout_read_guard.py`.

### Step E — Vectorized parity tests + integration (2–3 days)

Run the same `test_scan_matrix_full_session_candidate_parity.py`
and `test_scan_matrix_full_fold_backtest_parity.py` in
`runtime_mode=vectorized` AND `runtime_mode=compatibility` AND
`runtime_mode=disabled` — all three must produce identical results.

Remove the `assert_backtester_matrix_opt_in_is_supported(
runtime_mode="vectorized", parity_manifest_present=True)` refusal
once the parity tests pass.

The parity manifest is built by
`scanner.scan_matrix.build_scan_matrix(...)` when
`require_parity_manifest=true` in the config. Leave that flag at
true in every shipped optuna config so the vectorized path refuses
at startup if the manifest is missing.

### Step F — Flip the workstation overlay default + benchmark (1 day)

After all parity tests pass:

* Flip
  `optuna.acceleration.scan_matrix.enabled: true` and
  `runtime_mode: vectorized` in the workstation overlay configs
  (NOT the base shipping config — the base stays research-only).
* Run `scripts/benchmark_optuna_workers.py` with the matrix
  pre-built and capture wall-clock + counters per worker count.
* Document the actual measured speedup in
  `artifacts/benchmarks/phase_6_matrix_vectorized.json` and append
  a "post-Phase-6 retrospective" section to the phase-6 artifact
  summary.

---

## 4. PostgreSQL scaling for >8 workers

Phase 6 makes per-trial work faster; you'll then want to run more
workers concurrently. The workstation has 18 cores but PostgreSQL
is locked to 8 threads in `docker-compose-db.yml`. To go past 8w:

1. Raise `POSTGRES_MAX_CONNECTIONS` and
   `POSTGRES_SHARED_BUFFERS` in the compose file.
2. Verify the `MemoryBudget.from_system()` postgres reserve
   (currently 8 GiB) is still adequate at the new connection
   count; bump `postgres_gib_estimate` if not.
3. Re-run `scripts/benchmark_optuna_workers.py --workers 8,10,12,16`
   and pick the worker count that gives the best
   trials-per-hour without saturating Postgres.

The benchmark-only `workstation_10w.yml` / `workstation_12w.yml` /
`workstation_16w.yml` overlays are intentionally not promoted —
the operator turns these on per benchmark, never as a production
default, until Phase 6 lands AND the PostgreSQL tune is measured.

---

## 5. Expected per-trial cost after Phase 6

These are extrapolations — Phase 6 has not been implemented or
measured. Numbers are mid-range estimates with low confidence;
budget +50% headroom for parity-test debugging and integration.

| Configuration | Per-trial estimate | 10,000 trials in 24h? |
|---|---|---|
| Today (no Phase 6) | ~38 min | No — 16+ days |
| Compatibility mode, 8 workers | ~15–20 min | No — 7–10 days |
| Vectorized mode, 8 workers | ~3–8 min | Tight — 1.7–4.5 days |
| Vectorized + 16 workers | ~1.5–4 min | Achievable — 12–28 hours |

The **5,000-trial / 24h target** is comfortably achievable with
vectorized + 8 workers if the optimistic end of the vectorized
estimate holds. The **10,000-trial / 24h target** likely requires
vectorized + 16 workers + the Postgres tune.

---

## 6. Risks and known unknowns

* **Parity-test debugging is the dominant cost.** The matrix
  reconstruction has to match legacy gate ordering, score tie
  stability, skip-reason ordering, and event-id determinism. Budget
  twice as much time for parity-test fixing as for writing the
  vectorized code.
* **The vectorized speedup is unmeasured.** The 5–15× estimate
  comes from the matrix-doc author's design memo, not a working
  prototype. If a meaningful fraction of `apply_v2_gates` doesn't
  lift cleanly into NumPy (Python branches, lookup-table gates),
  the actual speedup may be 3–5× rather than 10×.
* **Matrix build cost is upfront.** Building the full validation
  matrix on the IEX lake (~6,500 symbols × ~600 trading days ×
  N scan times) is hours-scale on the workstation. It amortizes
  over many trials but adds to the first-launch wall-clock. Plan
  to build the matrix once nightly outside the study run.
* **Memory budget on the matrix.** The matrix doc §9 sizes the
  matrix as a function of `n_sessions × n_scans × n_symbols`. The
  Phase 6 memory-estimator fix
  (`scan_matrix._estimate_matrix_size_gib`) now uses actual PIT
  symbol counts (not the hard-coded 100), so the budget refusal is
  realistic. On the 192 GiB workstation, the IEX-only matrix fits
  comfortably; a SIP/IEX combined matrix may not.
* **The compatibility-mode path may yield less than 2×.** If most
  of `evaluate_one_scan`'s time is spent inside `apply_v2_gates`
  (the gate arithmetic itself) rather than the dict construction,
  compatibility mode's benefit is bounded. **Build a quick
  prototype of compatibility mode FIRST** before committing to
  vectorized — if compatibility mode's measured speedup is small,
  you'll know vectorized is the only path forward.

---

## 7. Parity tests (the acceptance spec)

| Test file | What it locks in |
|---|---|
| `tests/parity/test_scan_matrix_feature_row_parity.py` | Per-symbol matrix columns equal the legacy feature computation within `1e-12`. The build of the matrix passes this today. |
| `tests/parity/test_scan_matrix_full_session_candidate_parity.py` | Whole-session candidate-event list equal between legacy and `MatrixRuntimeCompatibilityMode`. **Currently scaffolded; will fail until Step B is built.** |
| `tests/parity/test_scan_matrix_full_fold_backtest_parity.py` | Whole-fold `FoldResult` + `daily_equity` + trade list equal across all three modes. **Currently scaffolded; will fail until Steps B–E are built.** |
| `tests/unit/scanner/test_scan_matrix_stable_score_tie_order.py` | `np.argsort(-scores, kind="stable")` must match the legacy `sorted(passing, key=lambda x: -x[0])` for tied scores. |
| `tests/unit/scanner/test_scan_matrix_missing_value_gate_semantics.py` | Gates mask on the `dyn_uint8` validity flag; no NaN comparison ever. |
| `tests/unit/scanner/test_scan_matrix_holdout_read_guard.py` | `purpose="objective"` cannot read holdout-window partitions; only `purpose="final_holdout"` can. |
| `tests/unit/scanner/test_scan_matrix_refuses_matrix_sensitive_search_space.py` | A search-space override under `MATRIX_SENSITIVE_PREFIXES` refuses at study start. |
| `tests/unit/scanner/test_scan_matrix_manifest_hash.py` | Matrix manifest hash is stable + content-addressed. |
| `tests/unit/scanner/test_scan_matrix_memory_budget_refuses_unsafe_plan.py` | Memory budget refuses a launch whose estimated matrix footprint breaches the reserve. |
| `tests/unit/scanner/test_scan_matrix_memory_estimate_uses_actual_pit_symbols.py` | Pinned the 7× understatement fix landed in Phase 6 step 1. |
| `tests/unit/scanner/test_scan_matrix_runtime_mode_resolution.py` | `resolve_runtime_mode` accepts `disabled / compatibility / vectorized`; raises on unknowns. |
| `tests/unit/scanner/test_scan_matrix_runtime_refuses_non_disabled_modes.py` | Backtester opt-in still refuses non-disabled modes until parity proven (will need updating as modes land). |
| `tests/integration/test_scan_matrix_runtime_mode_disabled_is_default.py` | Every committed config defaults `runtime_mode` to `disabled`. |
| `tests/integration/test_scan_matrix_cli_build_verify.py` | `bowaka-v2-lab scan-matrix build|verify` CLI subcommands work end-to-end. |

**Acceptance gate for declaring Phase 6 done:** the full integration
suite (`make test-integration --timeout=300`) passes with
`runtime_mode=compatibility` AND `runtime_mode=vectorized` enabled
in the test configs, and the parity tests above all pass.

---

## 8. Existing scaffolding inventory

The implementation lives in three modules. All three are imported
from `bowaka_v2_lab.scanner`:

| Path | Lines | What it contains |
|---|---|---|
| `src/bowaka_v2_lab/scanner/scan_matrix.py` | ~800 | Column schemas (`DYNAMIC_FLOAT64_COLUMNS` etc.); `ScanMatrixManifest`, `ScanMatrixSession`, `ScanMatrixStore`; `HoldoutMatrixReadError`; `compute_matrix_input_hash`; `MATRIX_SENSITIVE_PREFIXES`; `assert_search_space_compatible_with_matrix`; `build_session_partition` (the per-session builder); `build_scan_matrix` (the driver); `verify_scan_matrix` (CLI verify); `_estimate_matrix_size_gib` with the Phase 6 PIT-symbols fix. **The Phase 8 builder is fully shipped here.** |
| `src/bowaka_v2_lab/scanner/scan_matrix_runtime.py` | ~200 | `MatrixRuntimeNotImplementedError`, `MatrixParityManifestMissingError`; `resolve_runtime_mode(cfg)`; `MatrixRuntimeCompatibilityMode` (constructible; evaluator raises); `assert_backtester_matrix_opt_in_is_supported(enabled, runtime_mode, parity_manifest_present)`; the legacy `evaluate_one_scan_from_matrix(_vectorized)` stubs from speedup-v1 that still raise. |
| `src/bowaka_v2_lab/scanner/scan_matrix_vectorized.py` | ~55 | `evaluate_one_scan_vectorized` — pure scaffolding, raises `MatrixRuntimeNotImplementedError`. |

CLI subcommand (already shipped, exercise it to validate the
builder against your lake):

```bash
bowaka-v2-lab scan-matrix build \
  --config configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml \
  --scope validation \
  --workers 8 \
  --reserve-system-gib 62

bowaka-v2-lab scan-matrix verify \
  --store-root artifacts/cache/scan_matrix/validation \
  --config configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml \
  --sample-count 10
```

---

## 9. Documents to read

Listed in recommended read order.

| # | Path | Why |
|---|---|---|
| 1 | `research_notebooks/bowaka_v2_lab/docs/phase-6-scan-matrix-runtime-handoff.md` | This file. The 30-minute briefing. |
| 2 | `research_notebooks/bowaka_v2_lab/artifacts/phase-6-speedup-v2-summary.md` | What landed in this build (memory estimator, three-mode config, refusal scaffolding) and what was explicitly deferred. ~15 minutes. |
| 3 | `research_notebooks/bowaka_v2_lab/docs/phase-6-acceptance-criteria.md` | The original acceptance criteria for Phase 6: tasks, required parity tests, the "research-only" framing — extracted from the now-archived `docs/old_cc_prompts/bowaka_v2_lab_optuna_speedup_v2_claude_code_prompt.md`. ~20 minutes. |
| 4 | `docs/audits/2026-05-24_bowaka_v2_full_scan_feature_matrix_precompute.md` | **The matrix design spec proper.** Column schemas, dtype policy, partition layout, manifest format, missing-value gate semantics, stable score sort, gate-ordering invariants. **This is where the engineering spec lives.** 1-2 hours. |
| 5 | `src/bowaka_v2_lab/scanner/scan_matrix.py` | Read top-to-bottom. The builder logic shows how matrix columns relate to legacy scanner inputs. ~30 minutes. |
| 6 | `src/bowaka_v2_lab/scanner/scan_matrix_runtime.py` | The runtime scaffolding + the three-mode resolver + the opt-in guard. ~15 minutes. |
| 7 | `src/bowaka_v2_lab/scanner/scan_matrix_vectorized.py` | Just the API stub. ~2 minutes. |
| 8 | All `tests/parity/test_scan_matrix_*.py` + `tests/unit/scanner/test_scan_matrix_*.py` + `tests/integration/test_scan_matrix_*.py` | Each test is a concrete acceptance contract. Read every assert. ~1 hour total. |
| 9 | `research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/scanner/scan_loop.py` | The legacy `evaluate_one_scan` you must match. Pay close attention to gate ordering, `passing` list construction, the `sorted(...)` call, and how `skip_reasons` are accumulated. |
| 10 | `research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/scanner/event_builder.py` | `build_candidate_event(...)` is what both modes must call to produce events. Event IDs are deterministic — match them exactly. |
| 11 | `research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/scanner/gate_logic.py` | `apply_v2_gates` + `compute_signal_strength`. Compatibility mode reuses these; vectorized mode must produce mathematically identical output for the gates that matter. |

### Supporting context (older work; useful for context but not Phase 6)

| Path | Why it may help |
|---|---|
| `research_notebooks/bowaka_v2_lab/artifacts/phase-8-speedup-summary.md` | The Phase 8 (speedup-v1) builder that's already shipped. |
| `research_notebooks/bowaka_v2_lab/artifacts/phase-9-speedup-summary.md` | The original (speedup-v1) runtime scaffolding work that the current Phase 6 picks up. |
| `research_notebooks/bowaka_v2_lab/artifacts/final-summary-speedup-v2.md` | The full speedup-v2 inventory of caches, flags, and benchmark scripts. |
| `research_notebooks/bowaka_v2_lab/CLAUDE.md` | Project conventions: testing, branching, config-parity rules. |
| `CLAUDE.md` (repo root) | Repo-wide conventions. |

---

## 10. Branch + workflow conventions

Per the existing project pattern (every prior phase did this):

* Cut a branch off `dev`: `feature/phase-6-step-<X>-<short-slug>`,
  one branch per step in §3.
* Run the comprehensive testing protocol at the end of each step
  (`make test-fast`, then `make test`, then
  `make test-integration` — see `Makefile` for full commands).
* Merge with `--no-ff` once green.
* **Do NOT merge to `main` without operator sign-off** — that
  matches the operator's instruction at the start of speedup-v2.
* Write a per-step artifact summary at
  `research_notebooks/bowaka_v2_lab/artifacts/phase-6-step-<X>-summary.md`
  documenting what landed and what was deferred.

---

## 11. Out of scope for Phase 6 (will not be addressed by this work)

* The 8 completed trials at `value=-1.5` (floor). Phase 6 makes
  trials cheaper to run; it does NOT change the strategy
  parameters or the lake state that produces those outcomes.
  Investigate separately — likely a `_degraded_fold` cascade, but
  could also reflect that the strategy's IEX-only current-code
  contract simply doesn't produce profitable trades on the current
  workstation lake.
* The bowaka_common Alpaca SDK `adjustment` kwarg (already landed
  on `dev` as `78600e7` — `bowaka_common.marketdata.backfill`).
* The source-manifest drift on `bowaka_v2_config.yaml` from
  upstream live-code edits — operator regenerates via
  `python -m bowaka_v2_lab.reference` after reviewing diffs.

---

## 12. Quick-start commands for the new team

```bash
# Get the repo onto the workstation
git clone https://github.com/<org>/quants-lab.git
cd quants-lab && git checkout dev

# Bring up the dependency stack
docker compose -f quantslab_desktop_compose.yaml up -d

# Open the lab in a terminal
cd research_notebooks/bowaka_v2_lab

# Verify Phase 6 scaffolding is current
python -m pytest tests/unit/scanner/test_scan_matrix_*.py -q --tb=short

# Build the scan matrix against the live lake (Step A)
python -m bowaka_v2_lab.cli scan-matrix build \
  --config configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml \
  --scope validation

# Verify the build
python -m bowaka_v2_lab.cli scan-matrix verify \
  --store-root artifacts/cache/scan_matrix/validation \
  --config configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml
```

After Step A passes, start the compatibility-mode implementation
in `src/bowaka_v2_lab/scanner/scan_matrix_runtime.py`.

---

**End of hand-off briefing.** Questions: file an issue tagged
`phase-6` against the repo, or reach out to the operator who owns
this workstream.
