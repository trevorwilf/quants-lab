# Bowaka Lab — Implementation summary

**Date completed:** 2026-05-16
**Branch:** all phases merged to `dev`
**Final test result:** 318 passed, 2 deselected (live_alpaca), 0 failed.

## Phases completed

| Phase | Name | Branch | Tests added | Source files |
|---|---|---|---|---|
| 0 | Independent project skeleton | `phase-0-skeleton` | 8 | 5 (cli, __init__, conftest, 2 tests) |
| 1 | Config, hashing, path resolution, storage | `phase-1-config-storage` | 67 | 12 |
| 2 | Alpaca ETL, calendar, data quality audits | `phase-2-alpaca-etl` | 65 | 9 |
| 3 | Prefilter port with parity | `phase-3-prefilter-replay` | 32 | 3 |
| 4 | Bowaka portfolio backtester | `phase-4-backtester` | 31 | 11 (sim + metrics) |
| 5 | Counterfactuals + stop manager shadow | `phase-5-counterfactuals` | 18 | 3 |
| 6 | Signal fade scoring + buckets | `phase-6-signal-fade` | 16 | 4 |
| 7 | Paper-trading log import + reconciliation | `phase-7-paper-reconciliation` | 24 | 4 |
| 8 | Reports | `phase-8-reports` | 17 | 5 |
| 9 | Optuna + walk-forward + objective | `phase-9-optuna-walkforward` | 22 | 13 |
| 10 | Notebooks + QuantLab integration + final | `phase-10-quantlab-integration` | 10 + 12 notebooks | 3 root-repo patches |

22 merge commits on `dev` (11 phase commits + 11 `--no-ff` merge commits).

## Final test count

- 318 passing tests
- 2 deselected (`live_alpaca`, kept for collection-only verification)
- 0 failures
- ~25 seconds total runtime on Python 3.12.6 / Windows
- Live `MONGO_URI` Mongo + `BOWAKA_SOURCE_STRATEGY_ROOT` parity test + `BOWAKA_PAPER_LOGS_ROOT` live reconciliation test all green when env vars set.

## Independence verified

`research_notebooks/market_lab` was temporarily moved aside and:

- `import bowaka_lab` succeeds and prints `0.1.0`
- `python -m bowaka_lab.cli smoke --offline-fixtures` exits 0
- `pytest tests` collects and runs (subset that doesn't need market_lab present)

The independence grep returns zero matches:

```bash
grep -RnE "from\s+market_lab|import\s+market_lab|from\s+pmm_lab|import\s+pmm_lab" \
    research_notebooks/bowaka_lab/{src,tests,configs}
# rc=1 (no matches)
```

## Deviations from the handoff report

None substantive. The implementation tracks the report's named sections directly. Notable design choices:

- **Independence test source layout** (`tests/unit/test_independence.py`): builds the forbidden literals from short tokens (`"market" + "_" + "lab"`) so the test file itself doesn't trigger the project-level grep gate.
- **Parquet single-file reads** (`bowaka_lab.data.parquet_store`): use `ParquetFile(path).read()` instead of `pq.read_table(path)` because pyarrow 23 auto-infers Hive partition columns from the on-disk path, which would inject vendor/feed/etc. into the DataFrame.
- **Bar timestamps in synthetic fixtures**: anchored at 16:00 ET (`tests/_generate_daily_fixture.py`, `tests/_generate_minute_fixture.py`, `tests/unit/test_prefilter_no_lookahead.py`) so the NY `session_date` matches the calendar date. The no-lookahead test originally caught a UTC-midnight off-by-one in the fixture builder; this is documented as a `parity-note` in `daily_features.py`.
- **Soft-fade test scenarios** ([Report §13]): the report says "below VWAP alone → soft fade" but the score table assigns +2 to below-VWAP, which puts it in the "none" bucket. The unit test (`test_signal_fade_score::test_below_vwap_and_prior_close_above_entry_is_soft_fade`) instead constructs a 4-point scenario (below VWAP + below prior close) that lands in the soft (3-5) range. The score table is preserved; only the test scenario was adjusted.
- **Reconciliation precedence** (`bowaka_lab.reconcile.replay_comparator`): `signal_fade`-related rejections classify as `implementation_mismatch` *before* the generic `broker_rejection_mismatch` because the bot's after-close OPG behavior is a documented implementation bug.
- **Per-phase template adaptation**: the operator-only steps `/compact`, `/effort max`, and `ultrathink` are not invocable by the assistant. The rest of the per-phase template (branch off dev, implement deliverables and tests, run pytest, fix loop up to 5 cycles, commit, merge `--no-ff` to dev) was followed verbatim. No phase exceeded the 5-cycle fix budget.

## MVP status

`research-grade exploratory backtesting platform; live-trading approval requires SIP data + point-in-time universe + walk-forward validation per §31`.
