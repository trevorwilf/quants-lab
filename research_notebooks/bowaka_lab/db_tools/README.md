# db_tools — standalone Bowaka backfill

This folder ships a standalone Jupyter notebook + helper library that backfills
Alpaca asset, daily-bar, and minute-bar data into Bowaka Lab's storage layout.
It runs **before** Phase 2 of the main `bowaka_lab` implementation prompt ships;
`db_tools/_backfill_lib.py` does not import from `bowaka_lab.*`. When Phase 2
proper comes online, its Alpaca ETL reads this Parquet directly — no re-fetch.

The output Parquet uses the §8.3 partition layout. Mongo writes populate
`bowaka_asset_snapshots`, `bowaka_assets`, `bowaka_data_ingestion_runs`, and
`bowaka_daily_bar_audits` per §8.5 with indexes per §8.6.

## Prerequisites

1. `.env` at `research_notebooks/bowaka_lab/.env` (preferred) or repo root:
   ```dotenv
   ALPACA_API_KEY_ID=...
   ALPACA_API_SECRET_KEY=...
   MONGO_URI=mongodb://admin:admin@localhost:27017/quants_lab?authSource=admin
   # optional:
   MONGO_DATABASE=bowaka_lab
   ALPACA_PAPER=true
   ```
2. Mongo reachable at `MONGO_URI`. The `make run-db` stack from the repo root counts.
3. Alpaca paper-trading credentials (Basic Trading API data plan is fine for IEX).

## Quick start

```bash
cd research_notebooks/bowaka_lab
pip install -e .[dev]
python -m ipykernel install --user --name bowaka-lab
jupyter lab db_tools/bowaka_backfill.ipynb
```

In the notebook:

1. **Smoke test** (cell tagged `smoke`) — verify Alpaca + the configured feed.
2. **Estimate** (cell tagged `estimate`) — projected disk + API + wall clock.
3. **Stages** — run sequentially. Each stage is resumable; safe to interrupt and re-run.

## Headless via papermill

```bash
papermill db_tools/bowaka_backfill.ipynb /tmp/bowaka_backfill_out.ipynb \
  -p START_DATE 2024-12-01 -p END_DATE 2026-05-15 -p FEED iex
```

## Output layout

```
{out_dir}/
  parquet/
    assets/vendor=alpaca/snapshot_id=.../assets.parquet
    bars/vendor=alpaca/feed=iex/timeframe=1d/adjustment=raw/symbol=AAPL/part.parquet
    bars/vendor=alpaca/feed=iex/timeframe=1m/adjustment=raw/session_date=2026-05-12/symbol=AAPL.parquet
  scope/feed=iex/start=2024-12-01_end=2026-05-15/scope3.parquet
  manifest.json
  backfill.log
```

## Report sections backing each stage

| Stage | Report section |
|---|---|
| Smoke | §9 Alpaca adapter (no silent feed fallback) |
| Estimate | §8 data architecture |
| 1: Assets | §8.5 `bowaka_asset_snapshots` / `bowaka_assets` |
| 2: Daily bars | §9, §11.4 no-lookahead invariant |
| 3: Scope 3 | §11.4 no-lookahead ADV gate |
| 4: Minute bars | §10 calendar awareness |
| 5: Audits | §16.1 daily bar audit checklist |
| 6: Manifest | §8.5 `bowaka_data_ingestion_runs` |

> When Phase 2 of bowaka_lab proper ships, its Alpaca ETL reads this Parquet
> directly — no re-fetch.
