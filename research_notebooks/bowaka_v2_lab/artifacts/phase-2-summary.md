# Phase 2 summary — Data lineage and data-quality

**Branch:** `phase-2-realism-data-lineage-and-dq` (off `dev`)
**Audit refs:** P0-011, §11 Phase 2, Ticket 10.
**Status:** complete, merged to `dev`.

## What shipped

- **`data/lineage.py`** — content-derived `dataset_hash`: SHA-256 over
  `{lake_manifest_hash, feed, adjustment, date_range, symbol_universe_hash,
  daily/minute/quote partition hashes, assets_snapshot_id, corp_actions_hash,
  lab_config_hash}`. Lake-backed runs hash the real lake; synthetic/smoke runs
  hash deterministically from config + symbols + dates. Reproducible — a changed
  parquet size changes the hash. The dataset manifest's `provider` is now the
  real provider (lake → `alpaca`; synthetic → `fixture`), not hardcoded.
- **`data/data_quality.py`** — substantive `data_quality_report.json`: per-symbol
  checks (`missing_sessions`, `duplicate_sessions`, `ohlc_violations`,
  `zero_volume_sessions`, `large_gap_flags`, `passed_research_audit`) loaded from
  the lake's `_ingestion/audits/audit_*.parquet`; per-run coverage checks;
  quote-partition availability; adjustment-mismatch check. Aggregated to global
  pass/fail with per-symbol failure detail.
- **Realism fail-closed** — an `intended_realism` run is refused (CLI exit
  non-zero, `run_manifest.json["startup_dq_failure"]` set) when a required DQ
  check fails: insufficient coverage (missing ≥ 1% of expected pairs, or zero
  symbols), adjustment mismatch, or missing required quotes. `smoke_fixture` /
  `current_code_parity` runs are not DQ-gated. The DQ gate runs *before* the
  config-parity gate.
- **`MarketDataConfig.require_adjusted_daily_bars`** added.
- **`promotion/checklist.py`** — the data-quality check now also asserts
  `checks` is non-empty.
- **`.gitattributes`** (lab) — pins `*.yml` / `*.yaml` to LF so the frozen
  contract and the generated realism config round-trip byte-identically across
  OSes (Windows checkouts no longer rewrite LF→CRLF).

## Files

Code: `data/lineage.py` (new), `data/data_quality.py` (new), `sim/backtester.py`,
`config/models.py`, `promotion/checklist.py`. New: `.gitattributes`.
Tests: 6 added — `tests/unit/test_dataset_hash_stable.py`,
`test_data_quality_checks_populated.py`, `test_realism_fails_on_adjustment_mismatch.py`,
`test_coverage_missing_fails_realism.py`, `test_lineage_hash_includes_lake_manifest.py`;
`tests/integration/test_lake_audit_imported.py`.

**Result:** 392 passed, 1 skipped, 12 deselected (slow/live), 0 failed.
env-check passes on all 5 shipping configs.

## Acceptance criteria

| Criterion | Status |
|---|---|
| `data_quality_report.json["checks"]` non-empty on lake runs | PASS |
| Dataset hash content-derived and reproducible | PASS |
| Realism mode fails closed on missing data / adjustment / coverage | PASS |
| env-check passes on all shipping configs | PASS (5/5) |

## Notes

- A `cli backtest --config bowaka_v2_intended_realism.yml` (SIP feed) against
  the current IEX-only lake resolves to **zero symbols** and fails closed with a
  precise `startup_dq_failure` — this is correct and is exactly the Phase Z
  "fail with a precise startup DQ reason" outcome. Running realism end-to-end
  needs a SIP lake (operator backfill).
- Lineage hashing walks the full lake `bars/` tree; on the 6460-symbol lake this
  adds ~tens of seconds to lake-backed run startup. Acceptable; a later phase
  could cache partition listings.
