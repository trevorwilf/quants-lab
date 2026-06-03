# Scan-matrix verify — screener-universe dataset_hash parity fix

**Date:** 2026-06-02 · **Branch:** `fix/scan-matrix-verify-screener-universe-parity` (off `dev`, merged `--no-ff`)

Follow-up to the walk-forward scan-matrix speedup (see
`optuna_walkforward_scan_matrix_speedup.md`). Surfaced during the first real
operator matrix prep (`matrix_prep.ps1` → `scan-matrix verify`).

## Symptom

A freshly-built 65-session validation matrix (manifest `dataset_hash`
`e8129d9d…`) failed `scan-matrix verify --vectorized-check` with a single
`dataset_hash_drift` issue (`recomputed_dataset_hash` `bac15d58…`),
`vectorized_checked: true`, no cell issues. The lake had NOT changed — a rebuild
would reproduce the identical failure.

## Root cause (P0 — no screener matrix could ever be certified)

The matrix dataset_hash mixes in `symbol_universe_hash(symbols)`
(`data/lineage.py`). The BUILD and the VERIFY drift-check resolved `symbols`
**differently** for a screener config (one with a `universe:` screener block and
**no explicit `universe.symbols`** — i.e. the real workstation config):

- `build_scan_matrix` → empty `universe.symbols` → falls back to the
  **PIT-eligible union** over the first ≤5 sessions → `symbol_universe_hash(<~hundreds>)`.
- `_expected_manifest_dataset_hash` (verify) → read raw `universe.symbols` (`[]`)
  with **no PIT fallback** → `symbol_universe_hash([])`.

Different symbol sets → different `dataset_hash` → a guaranteed false-positive
`dataset_hash_drift` on every screener matrix. The Phase-2 fold-parity gate
never caught it because its synthetic lake uses an **explicit** symbol list (no
asymmetry).

## Fix (`scanner/scan_matrix.py`)

- New `_resolve_lineage_symbols(cfg, *, eligible_pit=None, sessions=None,
  lake_root=None)` — single source of truth for the lineage symbol set:
  explicit `universe.symbols` if present, else the PIT-eligible union (probed via
  `_eligible_pit_union_for_lineage` over the first ≤5 sessions).
- `build_scan_matrix` now calls it (`eligible_pit=` the probe it already ran) —
  **identical output**, so existing manifests' hashes are unchanged.
- `_expected_manifest_dataset_hash` now calls it (`sessions=` parsed from the
  manifest, `lake_root=` resolved when `uses_lake`) so verify reproduces the
  build's PIT union. Genuine drift (changed lake partitions, or a changed PIT
  universe) is still caught — only the false positive is removed; the contract is
  not loosened.

**Proof:** re-verifying the operator's existing staging matrix with the fix →
`status: ok`, `issues: []`, recomputed `dataset_hash == e8129d9d…` (matches the
manifest exactly → the lake never changed), `parity_proof.json`
`verifier_version: 2` written. The multi-hour build was salvaged — no rebuild.

## Pre-existing failure also fixed (`tests/fixtures/scan_matrix_parity.py`)

While regression-testing, `tests/parity/test_scan_matrix_vectorized_objective_parity.py`
(`slow`, deselected by the default suite) was found failing **on plain `dev`**
(confirmed by `git stash` of this fix → still fails). Cause: the parity fixture
built the matrix to `…/matrix` (no scope segment), but `build_fold_contexts` →
`resolve_scan_matrix_store_root` (Phase 1) appends `/validation` → looks in
`…/matrix/validation` → manifest missing. The operator flow is unaffected (its
build + config paths both end in `/validation`, so the resolver does not
double-append). Fix: the fixture now builds to `…/matrix/validation`, mirroring
the real layout. Tests that open the store directly (`ScanMatrixStore(fx.store_root)`)
are unaffected; the resolver-driven ones now resolve correctly.

## Tests

- `tests/unit/scanner/test_lineage_symbol_resolution_parity.py` (NEW, 4, lake-free):
  the build-vs-verify hash agreement for a screener config + the helper contract;
  asserts the empty-symbols hash WOULD have diverged (locks the bug shut).
- Re-ran green: scanner+lineage unit (202), all 8 scan-matrix parity-fixture
  consumers + cli build/verify (11, incl. the now-fixed `objective_parity`), the
  Phase 1–4 verify-walkforward-speedup set (41).

## Operator note (`matrix_prep.ps1`, repo root — user-owned, left uncommitted)

Two bugs fixed in the wrapper while diagnosing: (1) `Invoke-Cli` leaked the CLI's
stdout into its return value so `$rc` became `[<json…>, 0]` and `$rc -ne 0`
(an array filter) faked a build failure — fixed with `| Out-Host`; (2) added a
`-SkipBuild` switch to verify+promote an already-built staging matrix without a
multi-hour rebuild. These live in the working tree only; the user version-controls
their own script.
