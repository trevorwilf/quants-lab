# Shared Market-Data Lake — Implementation Summary

Implements the Claude Code prompt `docs/old_cc_prompts/bowaka_shared_marketdata_lake_claude_code_prompt.md` (archived, gitignored): a single,
strategy-neutral Alpaca market-data lake (`bowaka_common.marketdata`) consumed by
both `bowaka_lab` (v1) and `bowaka_v2_lab` (v2), ending the dual-copy / dual-store
duplication.

## Phases

| Phase | Branch | Result |
|---|---|---|
| 1 — `bowaka_common.marketdata` shared layer | `marketdata-1-common-layer` | merged |
| 2 — migration tooling & in-repo lake scaffolding | `marketdata-2-migration-infra` | merged |
| 3 — bowaka_lab lake-backed read adapter | `marketdata-3-rewire-v1` | merged |
| 4 — wire bowaka_v2_lab to the shared lake | `marketdata-4-wire-v2` | merged |
| 5 — dedup, cleanup, docs | `marketdata-5-dedup-docs` | merged |

Each phase branched off `dev`, was tested, and auto-merged on green.

## Tests added per phase

| Phase | New tests | Suite |
|---|---|---|
| 1 | 35 | `bowaka_common` (`test_marketdata_*`) |
| 2 | 5 | `tests/repo` (migration + gitignore) |
| 3 | 3 | `bowaka_lab` (`test_market_data_adapter`) |
| 4 | 16 | `bowaka_v2_lab` (loaders / suppliers / backtester-on-lake) |
| 5 | 0 | docs only |

**59 new tests.**

## Final test counts

- `bowaka_common`: **72 passed** (37 baseline + 35).
- `bowaka_lab`: **734 passed, 4 failed, 3 skipped** (731 baseline passes + 3 new).
- `bowaka_v2_lab`: **240 passed, 2 skipped** (224 baseline + 16); slow notebook
  tests (`test_notebook_05/10/11`) still green after the rebuild.
- `tests/repo`: **20 passed** (15 baseline + 5).

### v1 baseline preservation

Pre-flight baseline: `bowaka_lab` = 731 passed / 4 failed / 3 skipped. After all
phases: 734 passed (731 pre-existing + 3 new adapter tests) / **the same 4 failed**
/ 3 skipped — no regression.

The 4 v1 failures are **pre-existing and environment-driven**: `test_bucket_analysis.py`
× 3 (version-sensitive "json_string_variants") and `test_optuna_live_postgres.py` × 1.
They fail because the `ql-jupyter` container's dependency versions do not match the
pinned regression set (`requirements-regression.txt`); they are unrelated to this
work and out of scope per the failure protocol.

## Architecture delivered

- `bowaka_common/marketdata/` — `layout` (canonical Hive layout), `store`
  (`MarketDataStore` + `resolve_market_data_root`), `backfill` (Parquet-only
  Alpaca ingestion, migrated from `db_tools/_backfill_lib.py`), `catalog`
  (coverage + dataset hashing).
- Canonical lake: `research_notebooks/market_data/` (in-repo, gitignored,
  visible in the `ql-jupyter` container with no Docker change). Overridable via
  `MARKET_DATA_ROOT`.
- `scripts/migrate_market_data.py` — transcodes the legacy parquet tree into the
  lake (minute bars regrouped per symbol/month); idempotent, verified.
- v1: `bowaka_lab/data/market_data.py` adapter (`MarketDataStore`,
  `scope_3_universe`).
- v2: `loaders.py` `source="alpaca"` delegates to `MarketDataStore`;
  `data/suppliers.py` (`make_lake_suppliers`, `build_daily_cache_from_lake`);
  `market_data.shared_root` config; notebooks 02/04/05/11 are config-driven.

## Deviations from the prompt (and why)

1. **`db_tools/_backfill_lib.py` was left intact, not converted to a re-export
   shim.** It is pinned by `bowaka_lab/tests/unit/test_backfill_lib.py` (33 tests)
   and `tests/integration/test_backfill_lib_mongo.py` against the legacy
   Mongo / `out_dir` API. Shimming it to the Mongo-free
   `bowaka_common.marketdata.backfill` would break ~33 v1 tests and violate the
   non-negotiable v1 regression gate. The legacy tool remains the v1 Mongo-backed
   backfill; the canonical Parquet-only backfill is
   `bowaka_common.marketdata.run_backfill`. Phase 3 instead delivered an
   **additive** `bowaka_lab/data/market_data.py` adapter.

2. **The `.gitignore` lines for `db_tools/bowaka_data/parquet/{bars,assets}/`
   were kept, not removed.** The ~301k-file legacy tree still exists on disk;
   removing the ignore now would expose 301k untracked files. A comment marks
   the lines for removal once the operator deletes that directory (runbook step).

## Mongo dedup

`bowaka_common.marketdata.backfill` is Parquet-only — no Mongo client, no Mongo
config (verified by `test_marketdata_backfill_no_mongo.py`). The legacy
`_backfill_lib.py` retains its Mongo writers and is decommissioned together with
the legacy data tree (operator runbook).

## Operator runbook (not automated)

The one-time migration of the real ~301k-file dataset, smoke-testing both labs on
real data, and deleting `db_tools/bowaka_data/` remain operator steps — see the
operator runbook — now `marketdata_operator_runbook.md` (co-located here), extracted from the archived `docs/old_cc_prompts/bowaka_shared_marketdata_lake_claude_code_prompt.md`.
No Docker changes are needed (the lake is in-repo, already mounted at `/quants-lab`).
