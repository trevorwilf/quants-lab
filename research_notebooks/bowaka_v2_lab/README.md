# Bowaka v2 Lab — Research-Only QuantsLab Integration

> ⚠️ **Research and backtesting only.** This package does NOT promote any
> strategy variant to paper or live trading. Promotion to higher tiers
> (paper / live) requires SIP-validated walk-forward results and paper-vs-sim
> reconciliation, neither of which can be produced from this lab in isolation.

**Strategy identifier:** `bowaka_v2`

**Feed policy:** the IEX feed is acceptable for research / methodology checks
but cannot support any promotion claim. Configurations explicitly select
`market_data.feed` between `iex` and `sip`; any configuration using `iex`
is automatically capped at the `research_only` suitability tier by the
promotion gate.

## Installation

```bash
cd research_notebooks/bowaka_v2_lab
pip install -e .[dev]
```

## Environment variables

Copy `.env.example` to `.env` and populate. Required:

- `MONGO_URI` — MongoDB connection string (auth source `admin`).
- `BOWAKA_V2_SOURCE_ROOT` — absolute path to the read-only v2 archive.

Optional:

- `BOWAKA_V2_PAPER_LOGS_ROOT` — absolute path to paper-trading log root used by
  Phase 7 reconciliation tests.
- `ALPACA_API_KEY_ID` / `ALPACA_API_SECRET_KEY` / `ALPACA_PAPER` /
  `BOWAKA_V2_ALPACA_FEED` — only required by tests marked `live_alpaca`.

## Quick start

```bash
# 1. Verify environment + config
python -m bowaka_v2_lab.cli env-check --config configs/bowaka_v2_backtest_smoke.yml

# 2. Run unit tests
python -m pytest tests -q --tb=short -m "not live_alpaca and not slow"
```

## Linked reference

The companion design document is `bowaka_v2_quants_lab_integration_plan_revised.md`
(supplied by the operator). All cross-references in source are written as
`[Report §X.Y]`.

## Architecture (one paragraph)

`bowaka_v2_lab` is the strategy lab; `bowaka_common` (sibling package) is the
strategy-neutral data / artifact / research infrastructure. Both labs
(`bowaka_lab` for v1, `bowaka_v2_lab` for v2) consume `bowaka_common`. No
cross-strategy imports are permitted; tests under `tests/repo/` enforce this
at the repository level.
