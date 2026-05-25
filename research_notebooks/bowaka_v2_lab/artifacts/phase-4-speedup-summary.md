# Phase 4 — ScanSessionContext + gate-dump suppression

Speedup report §5.4 / §10.4 / §11.2.

## What landed

- **`scanner/scan_context.py`** (new):
  `ScanSessionContext` frozen dataclass holding
  `universe_meta_by_sym`, `cache_by_sym`, `config_hash_v`,
  `volume_curve_fraction_by_scan_bucket` (one entry per `(scan_ts,
  adv_bucket)` for every bucket the session's universe actually
  populates), and `collect_gate_dump`. Plus
  `build_scan_session_context(cfg, daily_cache, universe_snapshot,
  scan_times, volume_curve, *, collect_gate_dump)`.
- **`scanner/scan_loop.py`:**
  - `evaluate_one_scan(..., scan_context=None, collect_gate_dump=True)`.
    When `scan_context is None`, the inline build path is used (no
    behaviour change). When supplied, every per-symbol rebuild
    (`universe_meta_by_sym`, `cache_by_sym`, `config_hash_v`,
    volume-curve fraction lookup) is replaced with a context read.
  - New `ScanResult.rejection_counts: dict[str, int]` field. When
    `collect_gate_dump=False`, every per-symbol skip / gate-failure /
    max-entries-cap row is replaced with a counter bump there;
    `result.gate_dump` is empty, but per-reason totals still tally
    correctly.
- **`sim/event_loop.py::run_one_scan`** now accepts `scan_context` and
  `collect_gate_dump`, threading both into `evaluate_one_scan`.
- **`sim/backtester.py`:**
  - Builds one `ScanSessionContext` per session via
    `build_scan_session_context(...)` and passes it into BOTH SCAN call
    sites (smoke path + event-driven path). `collect_gate_dump =
    (artifact_mode == "full")`, so objective-minimal mode now skips the
    per-symbol nested dumps and uses the bounded counters.
  - The `gate_rejection_breakdown` in `sess_count` merges
    `scan_result.gate_dump` rows AND `scan_result.rejection_counts`, so
    funnel reporting stays correct in both modes.
- **Default-off discipline preserved.** Full mode keeps writing the
  legacy `gate_dump.parquet` with the legacy column set. The only
  behavioural change in full mode is the per-session precompute (the
  speedup) — gate_dump.parquet contents are unchanged.

## New tests

- `tests/parity/test_scan_loop_context_parity_full_mode.py` (3 parametrised).
- `tests/parity/test_scan_loop_objective_mode_emissions_match.py` (2).
- `tests/integration/test_full_mode_gate_dump_unchanged.py` (2).
- `tests/integration/test_objective_minimal_with_scan_context_parity.py` (1).

## Result

`make test` (full unit + parity + integration + reconcile, excluding
slow/live): **1218 passed, 0 failed, 12 deselected** (9:54).

## Branch

`feature/phase-4-scanner-context` merged to `dev` with `--no-ff`. Phase 5
takes off from `dev` next — that's the one that flips the
`objective_artifact_mode`, `cached_suppliers`, and (new) `scan_context`
flags on for the actual-IEX/SIP optuna configs.
