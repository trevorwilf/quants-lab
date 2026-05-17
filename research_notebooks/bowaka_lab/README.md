# Bowaka Lab

Independent US equities research/backtesting lab for the Bowaka strategy.

## Independence

This project does not import from `research_notebooks/market_lab` or `pmm_lab`.
The independence test asserts that no source file references either package.

```bash
! grep -RnE "from\s+market_lab|import\s+market_lab|from\s+pmm_lab|import\s+pmm_lab" \
    src tests configs
```

The only acceptable matches are explicit `# do not import` comments and README text.

## Install

```bash
cd research_notebooks/bowaka_lab
pip install -e .[dev]
```

## Environment

```bash
cp .env.example .env
# Fill in MONGO_URI and (optionally) Alpaca credentials.
```

Required for tests:

- `MONGO_URI` — MongoDB connection string. Live-mongo tests are skipped if unset.

Optional:

- `BOWAKA_SOURCE_STRATEGY_ROOT` — path to legacy bowaka prefilter source root. If set,
  the parity test will compare against `$BOWAKA_SOURCE_STRATEGY_ROOT/scripts/bowaka_prefilter.py`.
- `BOWAKA_PAPER_LOGS_ROOT` — path to legacy bowaka paper-trading logs. Live reconciliation
  test runs only if set.
- `ALPACA_API_KEY_ID` / `ALPACA_API_SECRET_KEY` — required only for `live_alpaca` tests.

## Quick smoke test

```bash
make test
make smoke
```

## Run notebooks

```bash
jupyter lab notebooks/
```

Each notebook begins with a bootstrap cell that inserts `src/` into `sys.path` so
the package imports work even when the notebook runs inside the root QuantLab
container without `pip install -e`.

## Run through root QuantLab

```bash
make trigger-task task=bowaka_lab_research_pipeline config=bowaka_lab_tasks.yml source=1
```

## Data limitations

IEX-only runs are exploratory. SIP/consolidated data is preferred for final validation.
Current-universe runs are survivorship-biased.

## Research status

Research-grade exploratory backtesting platform. Not live-trading approval. See
`bowaka_lab_project_handoff_report.md §31` for promotion criteria.
