# bowaka_common — Strategy-neutral infrastructure

Shared package consumed by `bowaka_lab` (v1) and `bowaka_v2_lab` (v2).

## Dependency direction (enforced by tests)

- `bowaka_common` imports nothing from `bowaka_lab` or `bowaka_v2_lab`.
- `bowaka_lab` may import from `bowaka_common`.
- `bowaka_v2_lab` may import from `bowaka_common`.

Strategy logic (entry rules, exit rules, sizing logic, broker simulation,
strategy-specific schemas) belongs in the strategy lab, not here. Generic
data ingestion, calendar utilities, storage adapters, walk-forward planners,
performance metrics, and artifact writers belong here.

## Installation

```bash
cd research_notebooks/bowaka_common
pip install -e .[dev]
```

## Contents

| Sub-package | What lives here |
|---|---|
| `data/` | Alpaca client, asset classification, bar / quote fetchers, candidate-doc schemas, rate-limit helpers |
| `calendar/` | XNYS-aware session boundary helpers |
| `storage/` | MongoDB store, Parquet store, dataset hashing |
| `marketdata/` | **Shared market-data lake** — `MarketDataStore` reader, canonical Hive layout, Alpaca ingestion (`run_backfill`), coverage + dataset hashing |
| `quality/` | Daily / intraday / quote audit reports |
| `artifacts/` | run_manifest / dataset_manifest / code_manifest builders; atomic writer |
| `research/` | Walk-forward splits, robustness / sensitivity / stress helpers |
| `sim/` | Generic same-bar stop / target ambiguity resolver (strategy logic stays in lab) |
| `metrics/` | Bucket analysis, diagnostics, MFE/MAE, portfolio and trade metrics |
| `utils/` | env auto-discovery, time aware-ts helpers, generic IDs, hashing, IO helpers, logging, serialization |

## Shared market-data lake

`bowaka_common.marketdata` is the canonical Alpaca market-data store, consumed by
both labs so neither owns the data or the on-disk layout:

- **`MarketDataStore`** — read API for daily/minute bars, quotes, corporate
  actions, and asset snapshots. Resolve the lake root with
  `resolve_market_data_root()` — precedence: explicit arg > `MARKET_DATA_ROOT`
  env var > the in-repo default `research_notebooks/market_data`.
- **`layout`** — the single source of truth for the partitioned-Parquet layout.
- **`run_backfill`** — Parquet-only Alpaca ingestion (no Mongo dual-write).
- **`available_symbols` / `date_coverage` / `dataset_hash`** — catalog queries.

The lake lives at `research_notebooks/market_data/` (gitignored). Migrate a
legacy `bowaka_lab/db_tools/bowaka_data` tree with `scripts/migrate_market_data.py`
(`make migrate-market-data`).
