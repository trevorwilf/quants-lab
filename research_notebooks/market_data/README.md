# Shared market-data lake

This directory is the canonical, **strategy-neutral** Alpaca market-data lake for
the quants-lab repo. Both `bowaka_lab` (v1) and `bowaka_v2_lab` (v2) read it
through `bowaka_common.marketdata.MarketDataStore` — neither lab owns the data or
the on-disk layout.

## Location

The lake lives here (`research_notebooks/market_data/`) by default. The repo is
bind-mounted into the `ql-jupyter` container at `/quants-lab`, so the lake is
visible and writable there with no extra Docker configuration. To relocate it
(for example onto a shared drive for other projects), set `MARKET_DATA_ROOT` in
the repo-root `.env` — `bowaka_common.marketdata.resolve_market_data_root()`
honours it.

## Layout

```
bars/vendor=<v>/feed=<f>/timeframe=1d/adjustment=<a>/symbol=<s>/part.parquet
bars/vendor=<v>/feed=<f>/timeframe=1m/adjustment=<a>/symbol=<s>/year=<Y>/month=<M>/part.parquet
quotes/vendor=<v>/feed=<f>/symbol=<s>/year=<Y>/month=<M>/part.parquet
assets/vendor=<v>/snapshot_id=<id>/assets.parquet
corporate_actions/vendor=<v>/symbol=<s>/part.parquet
_ingestion/{manifest.json, runs/, audits/, migration_report.json}
```

The layout is defined once, in `bowaka_common.marketdata.layout`.

## Populating it

- **Migrate** the legacy `bowaka_lab/db_tools/bowaka_data/parquet` tree:
  `python scripts/migrate_market_data.py` (or `make migrate-market-data`).
- **Backfill** fresh data from Alpaca: `bowaka_common.marketdata.run_backfill`.

## Git

Everything under this directory **except this README** is gitignored — the lake
holds large generated data and is never committed.
