# Per-trial scan-floor speedup (matrix vectorized runtime)

Goal: cut the post-matrix per-trial wall-clock so a 5000-trial walk-forward study
fits a 24–48 h budget (≈2.7–5.8 min/trial at n_jobs=10). Numba scan-feature
kernels are BUILD-time only and do not touch the per-trial path; this targets the
real per-trial residual instead.

## Measurement (cProfile, one validation fold, real /opt-cache lake, off-9p)

Profiled `_run_fold_backtest_objective` for one fold (incumbent-ish params). Top
of the per-trial cost was NOT the exit walk (my prior hypothesis) but the **matrix
vectorized scan runtime**:

| function | tottime | calls |
|---|---|---|
| `evaluate_one_scan_vectorized` | 29.8s (110.3s cum) | 7,612 |
| numpy `memmap.__getitem__` | 18.6s | 65.8M |
| `_nan_to_none` | 18.3s | 40.1M |
| `_reconstruct_session_bar` | 14.2s | 2.86M |
| `_reconstruct_forming_feats` | 6.1s | 2.86M |

`build_data_quality_report` (259s) is a separate one-time cost cached across
trials, not the per-trial residual.

## Optimization — skip discarded per-cell reconstruction (dead-work elimination)

`evaluate_one_scan_vectorized` already computes gates + score as vectorized numpy
masks. But its per-symbol loop reconstructed the per-cell `session_bar` +
`forming_feats` dicts (14 `_nan_to_none` each) for EVERY symbol that cleared the
cheap pre-checks. In objective mode (`collect_gate_dump=False`, the per-trial
path) those dicts are consumed ONLY by a gate_dump row or a PASSING candidate's
event — a gate-FAILING symbol (the vast majority) discarded them. Fixed
(`scanner/scan_matrix_vectorized.py`): when a symbol fails the gates AND the
gate-dump isn't collected, count the rejection and skip the reconstruction (+ the
per-gate dict / vcf / baseline scalars). **Result is byte-identical** — this
removes computation whose output was thrown away, not a semantic change.

## Accuracy gates (results provably unchanged)

- The existing three-way parity tests run exactly the changed path
  (`collect_gate_dump=False`) and assert `vectorized == compatibility == legacy`
  on real trades/scores (1e-9): `tests/parity/test_scan_matrix_vectorized_{objective_parity,full_fold_parity,tie_order}.py`,
  `tests/parity/test_scan_matrix_{full_fold_backtest_parity,tie_order}.py`,
  `tests/integration/test_scan_matrix_compatibility_objective_parity.py` — all green.
- New self-contained regression lock
  `tests/parity/test_scan_matrix_vectorized_gate_fail_skip.py`: a 1-scan/1-symbol
  matrix session that clears the pre-checks then fails an impossible gate —
  asserts the reconstruct is NOT called in objective mode (monkeypatched to
  raise) yet the GATE_FAILED rejection is counted, AND that gate-dump mode still
  reconstructs. Deterministic, no lake/matrix build.

## Measured effect (cProfiled, same fold)

`evaluate_one_scan_vectorized` cumtime 110.3s → **36.3s**; `_nan_to_none` /
`_reconstruct_*` dropped out of the top entirely; memmap reads 65.8M → 20M;
cProfiled fold 442.6s → 367.9s. Real (non-cProfiled) warm per-trial + the
5000-trial projection are being measured separately; if this single change does
not reach the 24–48 h window, the next pass is the bar-slice/event path
(`_getitem_axis`, `Series.__init__`, `datetimes.__iter__`) in the sim.

`make test-all`: unit+parity+scanner 1484 passed / 1 skip, modulo the documented
pre-existing failures (prod mirror ×2, dirty notebooks 10/13 ×2) + the §0.2 WSL test.
