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
| `quality/` | Daily / intraday / quote audit reports |
| `artifacts/` | run_manifest / dataset_manifest / code_manifest builders; atomic writer |
| `research/` | Walk-forward splits, robustness / sensitivity / stress helpers |
| `sim/` | Generic same-bar stop / target ambiguity resolver (strategy logic stays in lab) |
| `metrics/` | Bucket analysis, diagnostics, MFE/MAE, portfolio and trade metrics |
| `utils/` | env auto-discovery, time aware-ts helpers, generic IDs, hashing, IO helpers, logging, serialization |
