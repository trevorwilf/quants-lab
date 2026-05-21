# Phase 3 summary — Point-in-time universe builder

**Branch:** `phase-3-realism-pit-universe` (off `dev`)
**Audit refs:** P0-005, §11 Phase 3, Ticket 5.
**Status:** complete, merged to `dev`.

## What shipped

- **`universe/builder.py`** — `build_pit_universe(session_date, cfg, lake_store)`
  and `build_pit_universe_for_sessions(...)`; `UniverseRecord` dataclass. Replaces
  `synthetic_universe()` for non-smoke configs.
- **Filter chain** (ordered, each rejection reason recorded): allowed exchanges,
  OTC, instrument-class exclusions, ticker blocklist (`TSLL/CONL/SMCX`), price
  band (`prior_close` only — no current-day leakage), prior 20-day ADV minimum,
  delisting/status. Prior-day bars come strictly from sessions *before*
  `session_date`.
- **`universe/persist.py`** — per-session `universe_snapshot_{date}.parquet` +
  `universe_funnel_{date}.json` (starting count + count by rejection reason).
- **`universe_hash`** — sha256 of the sorted eligible-symbol list; recorded in
  `run_manifest.json["universe_hashes_by_session"]` and on every candidate event.
- **Synthetic-universe refusal** — `--allow-synthetic-universe` is honored only
  in `smoke_fixture` mode; the backtester refuses a synthetic universe in
  non-smoke modes.
- **Instrument-class heuristic** — the lake asset master has no instrument-class
  field (`asset_class` is `us_equity` for all symbols), so excluded instruments
  (ETF / leveraged / inverse ETP / ETN / warrant / unit / right / preferred) are
  classified by name keywords + issuer-family tokens + symbol-suffix rules.
  Ambiguous matches → `instrument_class = "heuristic"` → treated as `unknown` →
  honors `simulation.unknown_instrument_class_policy` (fail_open / fail_closed).

## Files

Code: `universe/__init__.py`, `universe/builder.py`, `universe/persist.py` (new);
`sim/backtester.py`, `cli_runners.py`, `cli.py`, `optuna/walkforward_runner.py`.
Tests: 8 added + a shared `tests/fixtures/universe_fixture.py`
(`test_universe_{blocklist,etf_exclusion,price_band,no_leakage,delisting}.py`,
`test_synthetic_universe_refused_in_realism.py`,
`test_universe_snapshot_artifacts.py`, `test_universe_hash_in_candidate_events.py`).
Two realism DQ tests updated to build a PIT universe (they previously passed a
synthetic universe purely to exercise the DQ gate).

**Result:** 413 passed, 1 skipped, 12 deselected (slow/live), 0 failed.
env-check passes on all 5 shipping configs.

## Acceptance criteria

| Criterion | Status |
|---|---|
| PIT universe replaces synthetic for non-smoke configs | PASS |
| Live blocklist / exclusions / price band / ADV min match the contract | PASS |
| No current-day data leakage in the filters | PASS |
| Universe artifacts present; `universe_hash` in events + manifest | PASS |
| env-check passes on all shipping configs | PASS (5/5) |

## Notes

- The blocklist tickers (`TSLL/CONL/SMCX`, leveraged ETPs) are not present in the
  current Alpaca asset-master snapshot, so the blocklist filter is exercised by
  tests rather than the live lake — the filter itself is correct.
- End-to-end against the real lake an `intended_realism` session resolves
  6483 assets → ~672 eligible symbols.
