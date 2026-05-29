# Bowaka v2 Lab Audit and Notebook 10 Remediation Report — Revised After Notebook 10 Output Review

**Date:** 2026-05-29  
**Supersedes:** `/mnt/data/bowaka_v2_lab_audit_report_2026-05-28.md`  
**Scope:** `research_notebooks/bowaka_v2_lab` in the uploaded Quant Lab repository, compared against the uploaded Bowaka v2 strategy backup, with additional review of the user-provided Notebook 10 Optuna output in `/mnt/data/Pasted text.txt`.  
**Primary deliverable:** engineering/quant remediation plan to make `bowaka_v2_lab` a realistic, testable backtesting and Bayesian/Optuna optimization environment for Bowaka v2 using IEX data now and SIP later.

---

## 1. Executive summary

### 1.1 Bottom line after reviewing the new Notebook 10 output

The pasted Notebook 10 output **changes the emphasis but confirms the core conclusion**.

The earlier audit concluded that Notebook 10 was broken because saved checkpoint artifacts showed a false-success Optuna study: degraded folds, dynamic Optuna categorical search-space failures, and a successful-looking artifact. The new pasted output shows a different failure mode. In this run, the optimizer appears to start cleanly, create a fresh PostgreSQL-backed study, launch process-parallel workers, sample the full 30-parameter search space, and complete at least trials `0` through `59` without the previous visible dynamic-search-space exception. That is real progress.

However, the new output is **not evidence of working Bayesian optimization**. Every completed trial shown in the pasted output has exactly the same objective value: `-1.5`, despite large changes in signals, sizing, risk, execution, and exit parameters. I parsed the pasted text and found:

| Check | Result |
|---|---:|
| Parsed completed trials in pasted excerpt | `60` |
| Trial numbers present | `0` through `59` |
| Missing trial numbers in 0-59 | `[]` |
| Unique objective values | `[-1.5]` |
| Trials with 30 parameters parsed | `60 / 60` |
| Occurrences of `CategoricalDistribution does not support dynamic value space` | `0` |
| Occurrences of `ERROR` | `0` |
| Occurrences of `WARNING` | `1` |
| Trials with `soft > hard` signal-fade thresholds | `13 / 60` |
| Trials with `hard > critical` signal-fade thresholds | `1 / 60` |
| Trials with `target_pct <= stop_pct` | `16 / 60` |

This is a **constant-objective / no-trade / inactive-study failure**, not a valid Optuna run. It is especially dangerous because it looks superficially healthy: preflight passes, workers launch, parameters vary, trials finish, and a `best trial` is reported. But with a flat objective surface, TPE/Bayesian optimization has no signal. The reported `best trial` is merely the first or tie-selected trial among identical outcomes.

The revised conclusion is therefore:

> Notebook 10 has moved from “obviously failing with dynamic Optuna errors in historical artifacts” to “able to run, but still invalid because all sampled parameters produce the same penalty score.” It must still be treated as **blocked for parameter recommendations** until the no-trade/constant-objective failure is fixed and guarded by tests.

### 1.2 Suitability classification

| Stage | Suitability after new pasted output | Rationale |
|---|---:|---|
| Unit/integration research fixtures | **Partially suitable** | Many tests and abstractions exist. The new output shows some fail-closed/dynamic-search remediations may have improved. But key tests are still missing: constant-objective rejection, no-trade rejection, incumbent-padding rejection, and daily-adjustment read-path enforcement. |
| IEX research/backtesting validation | **Blocked until remediation** | IEX remains acceptable for proving the testing stack. The blocker is not “no SIP”; the blocker is that Notebook 10 can complete a large IEX study with every trial equal to `-1.5`. |
| Bayesian/Optuna parameter recommendations | **Blocked** | The pasted output proves parameter sampling is happening, but not optimization. A flat objective across widely different parameters means the optimizer cannot rank parameters. |
| Paper-trading experiment support | **Candidate after fixes** | Paper trading can use IEX as a partial-tape research feed, but only after the simulator produces non-zero candidate/entry/fill telemetry and after paper-vs-sim reconciliation proves the path is measuring the same behavior. |
| Live deployment / SIP-grade realism | **Not in scope yet** | The user already recognizes this. Lack of SIP should not block the IEX test-stack demo, but SIP migration must add NBBO/quotes/halts/LULD/partial-fill realism before live claims. |

### 1.3 What changed relative to the first report

**Changed / downgraded as the primary immediate failure:**

- The pasted run does **not** show the previous repeated `CategoricalDistribution does not support dynamic value space` failure. This suggests the incumbent enqueue / search-space versioning work may have partially fixed the dynamic categorical failure, at least for this run.
- The pasted run does **not** show worker crashes or `ERROR` lines in the excerpt.
- The pasted run does show all 30 search-space parameters being sampled across trials.

**Confirmed / strengthened:**

- Notebook 10 still cannot be trusted for optimization. The failure mode is now stronger and subtler: it can run for hours and still produce zero optimization signal.
- The incumbent baseline is still not a true actual-strategy baseline. The pasted output explicitly logs that two search-space keys absent from the contract were padded with search-space defaults: `execution.max_quote_age_seconds` and `execution.max_spread_bps`.
- The preflight is too weak. `preflight passed: 4 checks` is not enough evidence that the per-fold data, universe, daily adjustment, minute coverage, and scanner candidate path are valid.
- `objective_artifact_mode=objective_minimal` is inappropriate as the only evidence mode while debugging a no-trade / constant-objective optimizer. It suppresses exactly the artifacts needed to diagnose why all trials tie.
- The search space allows invalid or nonsensical parameter combinations, including unordered signal-fade thresholds and target values below or near stop values.
- The valid-trial filter and promotion/evidence semantics still need fail-closed gates for all-zero/no-trade/constant-objective studies.

### 1.4 Highest-priority findings in the revised audit

1. **P0 — Notebook 10 now shows a constant `-1.5` objective across at least 60 completed trials.** This is not Bayesian optimization. It is almost certainly a no-trade/no-fill or all-candidates-rejected condition being scored as a finite valid objective.
2. **P0 — The objective value `-1.5` is explainable as a deterministic penalty combination.** The artifact `iex__bowaka_v2_iex_walkforward_conservative_18b9e931_20260527.json` shows all three validation folds with `n_trades: 0`, `fill_rate: 0.0`, `net_return_pct: 0.0`, full quote coverage, and penalties `low_trade_count: 1.0` plus `fill_rate: 0.5`, giving `0.0 - 1.0 - 0.5 = -1.5` per fold. That matches the pasted output exactly.
3. **P0 — Trial 0 is not a clean actual-strategy incumbent.** The pasted run logs padding of `execution.max_quote_age_seconds` and `execution.max_spread_bps`. The actual contract uses nested `execution.quote_gate.max_quote_age_seconds` and `execution.quote_gate.max_spread_pct`; the lab search space uses flat bps/seconds keys. The incumbent should be constructed from the mapped lab config, not padded from search-space defaults.
4. **P0 — No-trade / zero-candidate studies are accepted as completed studies.** A zero-trade objective can be a useful diagnostic, but it must fail the optimization stage or be labeled `diagnostic_failed`, not produce best parameters.
5. **P0 — Search-space relation constraints are missing.** The pasted trials include many cases where `soft > hard`, and many where `target_pct <= stop_pct`. Those combinations are invalid or at least not comparable to the actual strategy.
6. **P0 — Current-code-parity still needs full per-fold data preflight.** The code path only runs full fold preflight for `intended_realism`, not IEX/current-code-parity. That is too weak for funding-demo quality.
7. **P0 — Daily adjustment read path remains a major risk.** Several lab daily-bar supplier paths still call `store.daily_bars(..., feed=feed)` without `adjustment`, while the common store defaults to `adjustment="raw"`. The manifest can say `split_adjusted` and still not prove that the simulator read split-adjusted daily bars.
8. **P1 — Historical dynamic-search-space failure should be kept as a regression test.** It is not visible in the new pasted output, but older artifacts prove it existed. Do not delete this issue; demote it from primary current symptom to regression guard.

### 1.5 Position on IEX vs SIP

IEX should **not** block the current objective. The correct standard is:

- Use IEX now to prove the **testing stack**, **lineage**, **walk-forward orchestration**, **fail-closed behavior**, **simulator determinism**, **paper-log reconciliation**, and **artifact generation**.
- Label IEX outputs as `current_code_parity`, `research_only`, `partial_tape`, and **not** production/SIP-grade.
- Do not use synthetic data except for deterministic unit/integration fixtures and deliberately constructed edge cases.
- Do not tell management that IEX proves production alpha; do tell management that IEX proves whether the lab can run a controlled, auditable optimization workflow before SIP money is spent.

The pasted Notebook 10 output is useful for the funding case precisely because it exposes what still must be fixed before spending on SIP: the lab must be able to distinguish “Optuna ran” from “Optuna optimized a valid strategy simulation.”

---

## 2. Artifacts inspected and new evidence

### 2.1 Uploaded archives and files

- Quant Lab repository archive: `/mnt/data/quantslab_hummingbot.zip`
- Bowaka v2 strategy archive: `/mnt/data/bowaka_backup_v2.zip`
- User-provided Notebook 10 output excerpt: `/mnt/data/Pasted text.txt`
- Prior audit report superseded by this report: `/mnt/data/bowaka_v2_lab_audit_report_2026-05-28.md`

Extracted paths used during this revised audit:

- Lab root: `/mnt/data/qlab/quants-lab/research_notebooks/bowaka_v2_lab`
- Shared lake root: `/mnt/data/qlab/quants-lab/research_notebooks/market_data`
- Uploaded strategy root: `/mnt/data/bowaka/scripts`
- Lab frozen reference strategy mirror: `/mnt/data/qlab/quants-lab/research_notebooks/bowaka_v2_lab/reference/source_strategy/scripts`

### 2.2 Execution limitations in this audit environment

I still did **not** execute a fresh Notebook 10 run in this container. The runtime environment here is missing core project dependencies such as `optuna`, `papermill`, `pyarrow`, and several lake/backtest dependencies. This revised report is therefore based on:

- static source inspection;
- repository artifacts;
- saved Optuna JSON outputs;
- the user-provided Notebook 10 run output;
- direct parsing of the pasted Notebook 10 output text.

The report separates confirmed source/artifact evidence from remediation hypotheses that require a clean rerun.

### 2.3 New pasted Notebook 10 output summary

The pasted output begins with:

```text
2026-05-28 12:58:58,970 INFO preflight passed: 4 checks
[I 2026-05-28 13:21:30,565] A new study created in RDB with name: iex__bowaka_v2_iex_walkforward_conservative_2d03910a_20260528
2026-05-28 13:21:30,646 INFO walk-forward study ...: 200 trials (25 random startup) x 3 folds, feed=iex, search_space_version=2; per-fold universe = daily point-in-time set (~703 eligible on 2025-08-27) (preflight probe sampled 100 symbols)
2026-05-28 13:21:30,658 WARNING incumbent baseline padded 2 search-space key(s) absent from the contract with search-space defaults: ['execution.max_quote_age_seconds', 'execution.max_spread_bps']
2026-05-28 13:21:30,676 INFO objective_artifact_mode=objective_minimal — per-trial fold backtests skip disk artifact writes
2026-05-28 13:21:30,685 INFO parallel preflight: mode=process_parallel n_workers=10 reason=ok
2026-05-28 13:21:30,685 INFO process_parallel mode — parent skips build_fold_contexts; workers rebuild via the dotted factory
```

The displayed trials then complete with varying parameters but identical values:

```text
Trial 3 finished with value: -1.5 ... Best is trial 3 with value: -1.5.
Trial 2 finished with value: -1.5 ... Best is trial 3 with value: -1.5.
Trial 0 finished with value: -1.5 ... Best is trial 3 with value: -1.5.
...
Trial 59 finished with value: -1.5 ... Best is trial 17 with value: -1.5.
```

The “Best is trial 17” transition is not an improvement. It is a tie-handling artifact. Trial 17 is no better than Trial 3, Trial 0, or Trial 59.

### 2.4 Why `-1.5` is probably a no-trade penalty, not strategy performance

The saved artifact:

```text
artifacts/optuna/iex__bowaka_v2_iex_walkforward_conservative_18b9e931_20260527.json
```

has this structure:

```json
{
  "status": "ok",
  "n_trials_requested": 1,
  "best_value": -1.5,
  "fold_scores": [-1.5, -1.5, -1.5],
  "fold_metrics": [
    {
      "net_return_pct": 0.0,
      "mtm_max_drawdown_pct": 0.0,
      "worst_day_loss_pct": 0.0,
      "n_trades": 0,
      "fill_rate": 0.0,
      "historical_quote_coverage_pct": 100.0,
      "missing_quote_count": 0
    }
  ],
  "penalty_breakdown": {
    "low_trade_count": 1.0,
    "fill_rate": 0.5
  }
}
```

The objective code has default penalties consistent with this:

```text
score = net_return - penalties
score = 0.0 - low_trade_count_penalty(1.0) - fill_rate_penalty(0.5)
score = -1.5
```

Therefore the pasted run most likely means that every trial produced no valid trades/fills in every fold, not that the strategy generated identical economic performance under all sampled parameter sets.

This distinction matters. A no-trade result can be legitimate for a single overly strict configuration. It cannot be accepted as a valid 60-trial Bayesian optimization surface.

---
## 3. Strategy parity: uploaded Bowaka v2 vs lab reference

### 3.1 Core result

The lab’s frozen reference copy appears to match the uploaded Bowaka v2 strategy for the core files that matter to the simulator/contract:

- `bowaka_v2_config.yaml`
- `bowaka_v2_strategy.py`
- `bowaka_intraday_scanner.py`
- `bowaka_universe_builder.py`
- `bowaka_v2_features.py`
- `bowaka_v2_volume_curve.py`

A recursive diff between the uploaded strategy root and the lab reference mirror showed only wrapper, log, data, archive, and convenience files present in the uploaded backup but not relevant to the frozen core copy. Therefore, the main parity risk is **not** that the lab reference is obviously stale relative to the uploaded Bowaka v2 strategy. The main risk is that the lab **maps, simulates, tests, optimizes, and reports** the strategy incorrectly.

### 3.2 Actual Bowaka v2 contract summary

The actual strategy config has the following important operational contract:

#### Data / environment

- `strategy.environment: paper`
- `data.feed: iex`
- `data.allow_non_sip_for_research_only: true`
- `data.live_requires_sip: true`
- `data.daily_timeframe: 1D`
- `data.intraday_timeframe: 1m`
- `data.timezone: America/New_York`
- `data.min_history_trading_days: 45`
- `data.require_adjusted_daily_bars: true`
- `data.require_split_adjustment: true`
- `data.max_bar_age_seconds: 90`
- `data.max_quote_age_seconds: 15`

#### Session / scanner cadence

- Market session start: `09:30`
- Scanner start: `09:45`
- Scanner end: `15:30`
- Session end / strategy end: `15:55`
- Loop interval: `5` seconds

#### Universe

The strategy is designed around operating equities and explicitly filters away common synthetic/leveraged/non-equity instruments:

- allowed exchanges include `NASDAQ`, `NYSE`, `AMEX`, `ARCA`, `BATS`;
- OTC excluded;
- ETFs, leveraged/inverse ETPs, ETNs, warrants, units, rights, preferreds excluded;
- explicit ticker blocklist includes names such as `TSLL`, `CONL`, and `SMCX`;
- price range roughly `$1` to `$20`;
- average dollar volume minimum roughly `$250k`.

#### Signal gates

The strategy uses intraday momentum / relative volume / range-expansion gates, including:

- `rvol_so_far_min: 0.7`
- `projected_full_day_rvol_min: 0.5`
- `prior_atr_pct_min: 0.06`
- `range_expansion_so_far_min: 0.5`
- `close_location_so_far_min: 0.60`
- `ema_distance_min: -0.05`
- `ema_slope_min: -0.05`
- max guards such as `rvol_so_far_max: 8`, `projected_full_day_rvol_max: 8`, `range_expansion_so_far_max: 2.5`, `gap_pct_max: 0.25`, `current_return_pct_max: 0.5`.

The simulator must preserve the exact causal timing of these features. The daily baselines must be prior-day only; the forming-session bar must include only information available by the scan timestamp.

#### Execution

Actual execution contract includes:

- `parent_order_style: market`
- `marketable_limit_slippage_pct: 0.005`
- `marketable_limit_timeout_seconds: 30`
- `bracket_pricing_mode: actual_fill`
- quote gate enabled;
- `quote_gate.max_spread_pct: 0.01` (100 bps);
- `quote_gate.max_quote_age_seconds: 15`;
- `quote_gate.require_bid_ask_positive: true`;
- price chase gate enabled;
- halt gate enabled;
- default venue code `XNAS`.

The lab config remaps this into simplified top-level fields like `execution.limit_offset_bps`, `execution.max_quote_age_seconds`, `execution.max_spread_bps`, and `execution.order_type`. That remapping can be valid, but only if a behavioral parity test proves equivalence.

#### Sizing / risk

Actual strategy uses equal-slice / risk-limited sizing:

- `sizing_mode: equal_slice`
- fixed bankroll approximately `$90,000`
- max concurrent positions `18`
- equal-slice bankroll fraction `0.80`
- target risk dollars `$200`
- min notional `$500`

Risk controls include:

- daily loss percentage limit `0.03`
- per-slice loss limit `0.025`
- max gross exposure `0.80`
- max total entries/day `10`
- max lots/symbol `3`
- max stopouts/day `2`
- stop trading after `2` consecutive stopouts
- ADV tier caps / shadow gates.

#### Exits / protection

Actual exit contract includes:

- `stop_pct: 0.025`
- `target_pct: 0.15`
- `max_hold_days: 3`
- time stop around `15:45`
- signal-fade logic with telemetry/activation states;
- `bracket_pricing_mode: actual_fill`, meaning OCO stop/target prices are based on the actual fill, not signal price;
- protected-position invariant: fallback stop / flatten / block entries if bracket protection fails.

This exit/protection logic is one of the hardest parts to simulate correctly. It is not enough for the simulator to mark “entry then stop/target” using daily bars. The simulator must model parent fill timestamp/price, bracket attachment, unprotected time, same-minute stop/target ambiguity, gap-through-stop, time stops, max-hold exits at session open, and kill switches updated intraday.

---

## 4. Lab architecture: what is already present and useful

The lab is already much more mature than a one-off notebook. Important components include:

### 4.1 Config and frozen-contract infrastructure

- `reference/actual_bowaka_v2_contract.yaml` stores the frozen actual strategy contract.
- `reference/source_strategy/scripts/` stores a local mirror of the strategy source.
- `reference/import_config.py` maps actual strategy config into lab config.
- The contract captures source file hashes and can detect source drift.

This is a strong foundation. The next step is to make the incumbent baseline and simulation contract consume the **mapped** lab config consistently, not raw nested live keys in some places and lab keys in others.

### 4.2 Data-quality framework

The lab has a meaningful data-quality system:

- `data/data_quality.py` defines `DataQualityError` and `StartupDataQualityError`.
- Adjustment mismatch and split-adjustment mismatch are explicit checks.
- `evaluate_startup_dq(...)` gates `intended_realism` on all required checks and gates `current_code_parity` on adjustment-related checks.
- Quote coverage is measured and can gate `intended_realism`.

This design is correct directionally. The problem is not that the project has no data-quality concept; the problem is that Notebook 10’s saved output proves the invalid-run path can still leak into successful-looking artifacts.

### 4.3 Event-driven simulator

`sim/backtester.py` contains event-loop and realism features that are important for Bowaka:

- scanner cadence and per-session scan times;
- candidate/event logging;
- quote coverage rows;
- fill records;
- partial-fill count;
- missing quote count;
- ambiguous same-bar exit count;
- protected-position state metrics;
- mark-to-market daily equity reporting;
- finalize quote-coverage check;
- execution-quality report.

The simulator appears intentionally built around live-code parity and realism. The missing piece is proof that every live-relevant path is exercised and fail-closed under Notebook 10.

### 4.4 Optuna / walk-forward infrastructure

`optuna/walkforward_runner.py` includes:

- walk-forward splits;
- search-space versioning;
- objective artifact modes;
- final holdout guard;
- incumbent trial support;
- PostgreSQL storage support;
- memory/parallelism logic;
- invalid-study artifact support;
- promotion-gate evidence.

This is valuable infrastructure, but Notebook 10 exposes exactly where it must be hardened: invalid folds/trials and dynamic search-space failures must not be allowed to produce “OK” studies.

### 4.5 Tests already present

The test suite is broad and includes tests for:

- shipping config validation;
- backtester determinism;
- IEX single-session fixture runs;
- quote / synthetic quote behavior;
- current-code-parity data-quality failure on raw lake;
- intended-realism failure on raw/missing SIP/missing quotes;
- holdout exclusion;
- scan matrix parity;
- scanner replay;
- feature divergence;
- full-fold preflight;
- objective mark-to-market drawdown;
- low-trade penalty;
- parallel memory guard;
- PostgreSQL parallel smoke, opt-in;
- paper-log reconciliation;
- promotion evidence shape;
- incumbent baseline trial.

That breadth is good. The problem is that several tests are smoke-scale, opt-in, synthetic-only, or validate a narrow mock path rather than the current Notebook 10 / real-IEX path.

---

## 5. Shared market-data lake assessment

### 5.1 Lake structure

The market-data lake is organized under `research_notebooks/market_data` with partitioned directories such as:

```text
bars/vendor=<vendor>/feed=<feed>/timeframe=1d/adjustment=<adjustment>/symbol=<symbol>/part.parquet
bars/vendor=<vendor>/feed=<feed>/timeframe=1m/adjustment=<adjustment>/symbol=<symbol>/year=<yyyy>/month=<mm>/part.parquet
assets/vendor=<vendor>/snapshot_id=<snapshot>/assets.parquet
corporate_actions/...
_ingestion/manifest.json
_ingestion/audits/...
```

The ingestion manifest inspected from the uploaded repository says:

```json
{
  "generated_at": "2026-05-28T22:16:37.440355+00:00",
  "feed": "iex",
  "adjustment": "split_adjusted",
  "start_date": "2024-01-01",
  "end_date": "2026-05-27",
  "daily_fetch_start": "2023-11-25",
  "counts": {
    "assets": 6503,
    "daily": {
      "symbols_requested": 6503,
      "symbols_written": 1523,
      "symbols_extended": 678,
      "symbols_up_to_date": 4258,
      "symbols_empty": 44,
      "symbols_failed": 0
    },
    "minute": {
      "pairs_requested": 420265,
      "pairs_written": 0,
      "pairs_skipped_resume": 419332,
      "pairs_empty": 933,
      "batches_failed": 0,
      "months_written": 0
    },
    "audit_rows": 6477
  },
  "dataset_hashes": {
    "lake": "sha256:4629a73eae5deed13873d8980daf429e1186e7dc2b6b48535b9853e666f7dbef"
  }
}
```

The manifest implies the intended lake is IEX and split-adjusted. That is compatible with the current goal: prove the test stack using IEX and keep SIP as the future realism upgrade.

### 5.2 Critical issue: manifest adjustment vs reader adjustment

The code path inspected suggests a likely mismatch:

- `bowaka_common.marketdata.store.MarketDataStore.daily_bars(...)` defaults `adjustment="raw"`.
- `bowaka_common.marketdata.catalog.available_symbols(...)` defaults `adjustment="raw"`.
- `bowaka_v2_lab.data.suppliers.make_lake_suppliers(...).daily_bars_supplier()` calls `store.daily_bars(symbol, start, end, feed=feed)` without passing an adjustment.
- `build_daily_cache_from_lake(...)` should also be checked for the same default behavior.

Therefore, even when the lake manifest says `split_adjusted`, the backtester may read raw daily bars unless the adjustment is threaded explicitly.

This is a P0 simulation-validity issue because Bowaka’s signals depend on prior daily baselines:

- ATR percentage;
- EMA distance/slope;
- RVOL / projected RVOL baselines;
- gap percentage;
- price filters;
- split-sensitive ranges and close locations.

If the daily baselines are raw while the strategy requires adjusted/split-adjusted data, every optimized threshold can become invalid.

### 5.3 Required fix

Add a single adjustment resolver and use it everywhere daily bars are read:

```python
def daily_adjustment_for_config(cfg: Mapping[str, Any]) -> str:
    md = cfg.get("market_data", {}) or {}
    if md.get("require_split_adjustment") or md.get("require_adjusted_daily_bars"):
        return "split_adjusted"
    return str(md.get("daily_adjustment", "raw"))
```

Then ensure all daily lake readers pass it explicitly:

```python
adjustment = daily_adjustment_for_config(cfg)
store.daily_bars(symbol, start, end, feed=feed, adjustment=adjustment)
available_symbols(root, timeframe="1d", feed=feed, adjustment=adjustment)
```

The implementation should not rely on default `raw` for any Bowaka v2 actual-contract run.

### 5.4 Required tests

Add tests that prove the reader uses the requested adjustment partition, not the raw default.

#### Test: split-adjusted partition is actually read

Create a tiny lake with both raw and split-adjusted daily bars for the same symbol where the values are intentionally different:

- raw close: `100`
- split-adjusted close: `10`

Set:

```yaml
market_data:
  require_adjusted_daily_bars: true
  require_split_adjustment: true
```

Assert that the daily cache and features use the adjusted close `10`, not raw close `100`.

Acceptance criteria:

- The test fails on the current unpatched path if it defaults to raw.
- The test passes only when `adjustment="split_adjusted"` is explicitly propagated.
- The run manifest records the effective daily adjustment used.

#### Test: manifest says split-adjusted but partition read is raw

Create a lake where manifest says `split_adjusted`, but only raw partitions exist. The run must fail before optimization starts with a precise error:

```text
required adjusted/split_adjusted daily bars but no split_adjusted daily partition was found
```

Acceptance criteria:

- Failure occurs in preflight, not inside a trial after minutes of work.
- Study artifact is `status: "failed"` with empty `best_params`.

---

## 6. Notebook 10 deep investigation — revised with pasted output

### 6.1 What Notebook 10 is intended to do

`notebooks/10_optuna_walkforward.ipynb` is a thin orchestrator. Its intended job is to:

1. bootstrap local `src/` paths;
2. resolve the active config through `bowaka_v2_lab.optuna.autoconfig.resolve_walkforward_config`;
3. run `bowaka_v2_lab.optuna.walkforward_runner.run_walkforward_study`;
4. write a complete, auditable Optuna artifact package.

The notebook should not contain strategy logic. That architecture is correct. The problem is not that Notebook 10 is conceptually wrong; the problem is that the Python code it orchestrates can produce invalid studies that look operationally successful.

### 6.2 Current workstation config remains appropriate in principle

Notebook 10 points by default to:

```text
configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml
```

Important settings include:

```yaml
market_data:
  feed: iex
  require_adjusted_daily_bars: true
  require_split_adjustment: true

simulation:
  mode: current_code_parity

optuna:
  n_trials: 200
  n_startup_trials: 25
  n_jobs: 10
  objective_artifact_mode: objective_minimal
  storage: ${OPTUNA_STORAGE:-postgresql+psycopg2://optuna:optuna@optuna-postgres:5432/optuna}
```

This is a reasonable IEX research/paper workflow **only if** it fails closed on invalid data, invalid objective surfaces, and inactive/no-trade studies. The pasted run shows that those fail-closed guards are currently insufficient.

### 6.3 New pasted output: what it proves

The new output proves several positive things:

- the run reached Optuna study creation;
- RDB storage was used;
- the configured run requested `200` trials and `3` validation folds;
- IEX and `search_space_version=2` were selected;
- process-parallel mode with `n_workers=10` was accepted;
- the previous visible dynamic categorical failure did not appear in the pasted excerpt;
- trials varied across the 30 search-space parameters;
- at least trials `0` through `59` completed in the pasted excerpt.

This is useful progress compared with the older saved checkpoint run where trials 1-199 visibly failed with dynamic-search-space errors.

### 6.4 New pasted output: what it does not prove

The pasted output does **not** prove any of the following:

- that strategy candidates were generated;
- that scanner gates passed for any symbols;
- that any parent orders were submitted;
- that any fills occurred;
- that fills used actual-fill bracket semantics;
- that PIT universe construction was correct for all folds;
- that split-adjusted daily bars were actually read by the simulator;
- that the current-code-parity worker contexts matched the parent preflight context;
- that objective values respond to parameters;
- that Bayesian optimization learned anything;
- that Trial 0 equals the actual Bowaka v2 strategy.

The run is still invalid as an optimization because all shown objective values are identical.

### 6.5 Constant objective is now the primary Notebook 10 blocker

A valid Optuna run should produce an objective distribution with some variance unless every trial truly produces identical trades, identical fills, and identical risk path. That is effectively impossible here because the sampled parameters vary widely:

- signal thresholds vary across permissive and restrictive ranges;
- `sizing.max_concurrent_positions` varies from `1` to `30`;
- `execution.max_quote_age_seconds` varies from `1` to `120`;
- `execution.max_spread_bps` varies from `7` to `200`;
- `exits.stop_pct` varies from about `0.011` to `0.199`;
- `exits.target_pct` varies from about `0.028` to `0.392`.

Yet every parsed trial in the pasted excerpt has value `-1.5`.

This means one of the following is almost certainly true:

1. **No candidates pass the scanner gates in any trial.** The backtester may be producing no opportunities because of data alignment, baseline calculation, missing adjusted daily data, restrictive gates, or point-in-time universe mismatch.
2. **Candidates pass but entries are never submitted.** The entry decision path may be blocked by risk, sizing, quote gate, spread gate, price gate, min-notional, max exposure, or unprotected-position controls.
3. **Orders are submitted but never filled.** The simulator may be using a fill model that rejects all orders under IEX/current-code-parity conditions.
4. **The objective collapses all low-activity outcomes to the same penalty.** If no trades occur, the current penalty function produces a fixed `-1.5`, hiding which upstream gate caused the inactivity.
5. **Per-trial artifacts are suppressed by `objective_minimal`.** The runner may be omitting the candidate/gate/fill artifacts needed to distinguish cases 1-4.

The immediate fix is not to run more trials. The immediate fix is to run **fewer trials with much richer diagnostics** and fail closed when the objective surface is flat.

### 6.6 Objective code explains the exact `-1.5` score

The objective layer uses penalties including:

- `low_trade_count = 1.0`
- `fill_rate = 0.5`
- `min_trade_count = 10`

The saved single-trial artifact with `best_value = -1.5` shows:

- `net_return_pct = 0.0`
- `n_trades = 0`
- `fill_rate = 0.0`
- quote coverage at `100.0%`
- `low_trade_count` penalty `1.0`
- `fill_rate` penalty `0.5`

This produces `-1.5` exactly. Therefore the pasted run should be treated as **repeated no-trade penalty scoring** until proven otherwise by per-fold candidate/entry/order/fill telemetry.

### 6.7 Incumbent baseline defect is confirmed by the pasted output

The pasted output logs:

```text
WARNING incumbent baseline padded 2 search-space key(s) absent from the contract with search-space defaults: ['execution.max_quote_age_seconds', 'execution.max_spread_bps']
```

This is not harmless. Those two keys are behaviorally important execution gates.

The actual strategy contract has nested keys such as:

```yaml
execution:
  quote_gate:
    max_quote_age_seconds: 15
    max_spread_pct: 0.01
```

The lab search space has flat keys:

```yaml
execution.max_quote_age_seconds
execution.max_spread_bps
```

Current source inspection shows the runner builds incumbent params from `_incumbent_baseline_params()` and then pads missing search-space keys from search-space midpoint/default values. Source comments even say these are “lab-only knobs” not in the contract. But they are not lab-only in behavior; they correspond to actual quote-gate behavior after mapping.

The pasted Trial 0 parameters include:

```text
'execution.max_quote_age_seconds': 60
'execution.max_spread_bps': 102
```

The actual-derived lab config should use approximately:

```text
execution.max_quote_age_seconds = 15
execution.max_spread_bps = 100
```

Therefore Trial 0 is **not** a strict actual-strategy incumbent. Any report that says “optimized parameters beat the actual strategy baseline” is invalid until Trial 0 is built from the fully mapped lab config and fails if any behavior key is padded.

### 6.8 Search-space constraints are currently invalid

The search-space source comments say:

```python
# signal-fade score thresholds (soft < hard < critical); live 0.34/0.5/0.67
```

But the three thresholds are sampled independently:

```python
"exits.signal_fade.score_thresholds.soft":     ("uniform", 0.10, 0.50)
"exits.signal_fade.score_thresholds.hard":     ("uniform", 0.30, 0.70)
"exits.signal_fade.score_thresholds.critical": ("uniform", 0.50, 0.90)
```

The pasted output confirms the issue: 13 of the parsed 60 trials have `soft > hard`, and 1 has `hard > critical`.

The same issue exists for stop/target. The search space samples:

```python
"exits.stop_pct":   ("uniform", 0.01, 0.20)
"exits.target_pct": ("uniform", 0.02, 0.40)
```

The pasted output has 16 of 60 parsed trials with `target_pct <= stop_pct`. Some of those may be deliberate counterfactuals, but they should not be in the default conservative optimization search unless the objective explicitly treats them as allowed low-reward/risk variants. If the goal is realistic Bowaka v2 parameter optimization, these should be constrained.

Important implementation caution: do **not** fix this with dynamic per-trial Optuna distributions using the same parameter names, because that can reintroduce the dynamic search-space failure. Use stable distributions plus deterministic transforms, explicit gap parameters, rejection/pruning with clear invalid-relation reasons, or separate parameter names/versioned search spaces.

### 6.9 Full-fold preflight remains too narrow

Source inspection still shows:

```python
if sim_cfg.mode == "intended_realism":
    run_full_fold_preflight(...)
```

The pasted output says only:

```text
preflight passed: 4 checks
```

For Notebook 10, that is insufficient. The current-code-parity IEX mode should not require SIP-grade quote realism, but it must still prove hard prerequisites:

- effective daily adjustment used by suppliers is `split_adjusted` when the strategy requires split adjustment;
- minute bars exist for every validation scan/exit window;
- daily lookback exists for every symbol/session used;
- point-in-time universe is non-empty and above a configured minimum per fold;
- candidate scanner can produce a non-empty telemetry table in at least a debug/probe pass;
- fold windows do not overlap final holdout;
- worker processes rebuild identical config/data contexts.

### 6.10 `objective_minimal` is unsafe while Notebook 10 is being debugged

The pasted run says:

```text
objective_artifact_mode=objective_minimal — per-trial fold backtests skip disk artifact writes
```

That may be appropriate after the pipeline is proven. It is not appropriate while all objective values tie at `-1.5`.

Required temporary mode:

```yaml
optuna:
  objective_artifact_mode: debug_first_trials
  debug_artifact_trials: [0, 1, 2]
  write_candidate_gate_telemetry: true
  write_entry_decision_telemetry: true
  write_order_fill_telemetry: true
```

At minimum, the first incumbent trial and two sampled trials must write:

- per-fold universe count;
- candidate count before each gate;
- candidate count after each gate;
- entry submissions;
- risk/sizing rejects by reason;
- quote gate rejects by reason;
- order submissions;
- fill attempts;
- fills;
- exit events;
- final fold metrics.

Without this, Notebook 10 can consume hours and produce no diagnosis.

### 6.11 Dynamic-search-space failure is demoted but not closed

The new pasted output does not show the prior dynamic Optuna categorical failure. That changes the priority: it is no longer the primary current symptom.

It is still not fully closed because older repository artifacts show the failure existed. The regression protection must remain:

- search-space hash in study name/user attrs;
- categorical choices hash in study user attrs;
- fail closed if an existing RDB study has a different search-space hash;
- no per-trial mutation of distribution choices/ranges for the same parameter names;
- tests against in-memory, SQLite, and PostgreSQL storage;
- explicit test that changing `TIME_STOP_EXIT_TIME_CHOICES` under the same study name fails with a clear hash mismatch instead of running.

### 6.12 Required Notebook 10 acceptance criteria after the new evidence

Notebook 10 should be considered fixed only when a fresh run in a clean environment satisfies all of the following:

1. A 1-trial incumbent debug run produces non-empty per-fold telemetry or explicitly fails with a no-signal diagnostic.
2. Trial 0 is built from the mapped actual lab config. No behavior key is padded from search-space defaults.
3. The effective daily adjustment read by every daily supplier is recorded and equals `split_adjusted` when required.
4. The current-code-parity fold preflight validates daily/minute/PIT universe prerequisites for all validation and holdout windows.
5. A 3-trial debug run writes candidate/gate/entry/order/fill artifacts for all folds.
6. A 20-trial short run has more than one unique objective value after rounding to a reasonable precision, unless the run fails with `CONSTANT_OBJECTIVE_SURFACE`.
7. A 20-trial short run has a minimum valid-trade-count gate or explicitly fails with `NO_TRADE_STUDY`.
8. Search-space relation constraints are enforced or invalid combinations are pruned before simulation with explicit reasons.
9. Dynamic search-space errors are zero.
10. The best trial has non-zero evidence of strategy activity: candidates, entry attempts, and either fills or explicit fill-model rejection diagnostics.
11. `promotion_evidence` separates `study_valid`, `reviewable_for_research`, `parameter_recommendation_allowed`, `promotable_to_paper`, and `promotable_to_live`.
12. A full 200-trial run is attempted only after the 3-trial and 20-trial gates pass.

---
## 7. Critical issues and remediation plan — revised ranking

This section ranks issues by probability of causing invalid inference or a false-positive parameter recommendation. The ordering changed after the pasted Notebook 10 output. The dynamic-search-space failure remains important, but the current primary blocker is now the constant `-1.5` objective / no-trade study.

### P0-001 — Notebook 10 accepts a constant-objective Optuna study as if optimization is occurring

**Evidence:** The pasted Notebook 10 output shows trials `0` through `59` completing with value `-1.5` despite wide parameter variation. Parsed objective values have exactly one unique value: `[-1.5]`.

**Impact:** Catastrophic for optimization credibility. Optuna can appear to run for hours, but the posterior/sampler receives no performance signal. Any `best_params` are arbitrary tie artifacts.

**Likely root cause:** All folds are returning the same no-trade penalty score. The artifact `18b9e931_20260527` confirms that `n_trades=0`, `fill_rate=0.0`, `net_return_pct=0.0`, `low_trade_count=1.0`, and `fill_rate=0.5` produce `-1.5`.

**Fix:** Add study-level objective-surface validation after the startup phase and before accepting any result.

```python
def validate_objective_surface(trials, *, min_trials=10, decimals=8):
    completed = [t for t in trials if t.state.name == "COMPLETE" and t.value is not None]
    valid = [t for t in completed if not t.user_attrs.get("invalid_trial")]
    if len(valid) >= min_trials:
        unique = {round(float(t.value), decimals) for t in valid}
        if len(unique) <= 1:
            raise OptunaStudyInvalidError(
                "CONSTANT_OBJECTIVE_SURFACE: all valid completed trials have the "
                f"same objective value {sorted(unique)}; optimization signal is absent"
            )
```

**Acceptance tests:**

1. Simulate 20 completed trials all valued `-1.5`; assert the runner writes a failed artifact and raises `CONSTANT_OBJECTIVE_SURFACE`.
2. Simulate 20 completed trials with at least two rounded objective values and valid activity metrics; assert the surface gate passes.
3. Ensure the gate is disabled only for a deliberately labeled smoke test, not for Notebook 10 production research runs.

---

### P0-002 — No-trade / no-fill folds are scored as finite valid optimization outcomes

**Evidence:** Saved artifact `18b9e931_20260527` has `n_trades=0` and `fill_rate=0.0` in all folds, yet `status: ok` and `best_value: -1.5`. The pasted run repeats the same score across all shown trials.

**Impact:** Catastrophic. A no-trade strategy can become the “best” strategy because all trials tie at a finite penalty.

**Fix:** Split objective scoring from optimization validity. A no-trade fold may have a diagnostic score, but a no-trade study should not be eligible for best-parameter reporting.

Recommended fold/trial activity schema:

```json
{
  "fold_id": "f0_2025-08-27",
  "universe_count": 703,
  "scanner_candidate_count": 124,
  "candidate_after_signal_gates": 9,
  "entry_attempt_count": 3,
  "order_submission_count": 3,
  "fill_count": 2,
  "exit_count": 2,
  "n_trades": 2,
  "activity_status": "active"
}
```

Recommended validation:

```python
def validate_trial_activity(fold_metrics, cfg):
    total_candidates = sum(m.get("scanner_candidate_count", 0) for m in fold_metrics)
    total_entries = sum(m.get("entry_attempt_count", 0) for m in fold_metrics)
    total_trades = sum(m.get("n_trades", 0) for m in fold_metrics)

    if total_candidates == 0:
        return "NO_CANDIDATES"
    if total_entries == 0:
        return "NO_ENTRY_ATTEMPTS"
    if total_trades < cfg.optuna.quality_gates.min_total_trades:
        return "INSUFFICIENT_TRADES"
    return "OK"
```

**Acceptance tests:**

- `test_walkforward_rejects_all_zero_trade_trials`
- `test_walkforward_distinguishes_no_candidates_from_no_fills`
- `test_no_trade_study_has_no_best_params_and_not_reviewable`
- `test_zero_trade_fold_allowed_only_if_total_study_activity_passes_floor`

---

### P0-003 — Incumbent baseline Trial 0 is padded and not guaranteed to equal actual Bowaka v2

**Evidence:** The pasted output logs padding of `execution.max_quote_age_seconds` and `execution.max_spread_bps`. Source code pads missing keys from search-space midpoint/default values. Trial 0 in the pasted run uses `execution.max_quote_age_seconds: 60` and `execution.max_spread_bps: 102`, while actual-derived values should be approximately `15` and `100`.

**Impact:** Severe. The lab cannot claim the optimizer compares against the actual strategy baseline if the incumbent is a hybrid of actual keys and search-space defaults.

**Fix:** Build incumbent params from the fully imported/mapped lab config, not from raw contract dotted lookup.

```python
def _incumbent_baseline_params_from_mapped_config(config_path: Path) -> dict[str, Any]:
    cfg = load_and_resolve_lab_config(config_path)
    params = {}
    missing = []
    for name in SEARCH_SPACE_SPEC:
        value = dotted_lookup(cfg, name, default=MISSING)
        if value is MISSING:
            missing.append(name)
        else:
            params[name] = value
    if missing:
        raise OptunaStudyInvalidError(
            "INCUMBENT_MAPPING_INCOMPLETE: missing search-space keys "
            f"in mapped lab config: {missing}"
        )
    return params
```

If a key is truly lab-only and not incumbent comparable, it should be excluded from the incumbent comparison or explicitly marked as such in promotion evidence. Do not silently pad behavior keys.

**Acceptance tests:**

- `test_incumbent_trial_uses_mapped_actual_config_without_padding`
- assert exact key values:
  - `execution.max_quote_age_seconds == 15`
  - `execution.max_spread_bps == 100`
  - `exits.stop_pct == 0.025`
  - `exits.target_pct == 0.15`
  - `sizing.equal_slice_bankroll_fraction == 0.80`
- assert the pasted warning cannot occur in a production Notebook 10 run.

---

### P0-004 — Search space permits invalid parameter relations

**Evidence:** Parsed pasted output found 13/60 trials with `soft > hard`, 1/60 with `hard > critical`, and 16/60 with `target_pct <= stop_pct`.

**Impact:** High. Invalid parameter relations waste trials, distort TPE learning, and can make results incomparable with the actual strategy.

**Fix options:**

1. **Stable transform with gap parameters** — preferred to avoid dynamic distribution ranges:

```python
soft = trial.suggest_float("exits.signal_fade.score_thresholds.soft", 0.10, 0.50)
hard_gap = trial.suggest_float("exits.signal_fade.score_thresholds.hard_gap", 0.01, 0.30)
critical_gap = trial.suggest_float("exits.signal_fade.score_thresholds.critical_gap", 0.01, 0.30)
hard = min(0.70, soft + hard_gap)
critical = min(0.90, hard + critical_gap)
```

This changes parameter names and requires `SEARCH_SPACE_VERSION` bump plus config export mapping.

2. **Reject/prune invalid combinations early** — simplest but can waste sampler suggestions:

```python
if not (soft < hard < critical):
    raise optuna.TrialPruned("invalid_fade_threshold_order")
if target_pct <= stop_pct * min_reward_risk:
    raise optuna.TrialPruned("invalid_reward_risk")
```

3. **Sample stop plus reward/risk ratio:**

```python
stop_pct = trial.suggest_float("exits.stop_pct", 0.01, 0.12)
rr = trial.suggest_float("exits.reward_risk_ratio", 1.5, 8.0)
target_pct = min(0.40, stop_pct * rr)
```

**Do not** use per-trial dynamic ranges under the same Optuna parameter names unless the distribution compatibility is explicitly tested, because that can reintroduce the older dynamic search-space failure.

**Acceptance tests:**

- Sample 10,000 generated configs and assert `soft < hard < critical` always holds.
- Sample 10,000 generated configs and assert reward/risk constraints always hold.
- Exported best params must contain actual strategy keys, not internal gap-only keys without mapping.
- Search-space version and hash must change when parameterization changes.

---

### P0-005 — Current-code-parity skips full-fold preflight and can launch invalid IEX studies

**Evidence:** Source inspection shows `run_full_fold_preflight(...)` is only called when `simulation.mode == "intended_realism"`. The pasted run only reports `preflight passed: 4 checks` and then launches 200 trials.

**Impact:** Severe. The IEX mode can start large studies without proving per-fold data readiness.

**Fix:** Add a current-code-parity full-fold preflight with hard/warn distinctions.

Hard-fail for current-code-parity:

- missing split-adjusted daily bars when required;
- daily lookback insufficient for any validation session;
- minute bars missing for scan/exit windows;
- PIT universe count below minimum;
- manifest/partition lineage mismatch;
- fold overlap with final holdout;
- zero scanner candidates in a diagnostic probe when the probe uses intentionally permissive gates.

Warn-only for current-code-parity:

- missing SIP/NBBO;
- missing historical quote feed, if current-code-parity is explicitly allowed;
- halt/LULD feed unavailable, if labeled as IEX paper-research limitation.

**Acceptance tests:**

- `test_current_code_parity_full_fold_preflight_blocks_missing_minute_coverage`
- `test_current_code_parity_full_fold_preflight_blocks_adjustment_mismatch`
- `test_current_code_parity_full_fold_preflight_blocks_empty_pit_universe`
- `test_current_code_parity_full_fold_preflight_warns_missing_quotes_but_records_limitation`

---

### P0-006 — Daily adjustment read path likely defaults to raw despite split-adjusted requirement

**Evidence:** Several daily-bar supplier paths call `store.daily_bars(symbol, start, end, feed=feed)` without passing `adjustment`. The common `MarketDataStore.daily_bars` default is `adjustment="raw"`. The actual strategy requires adjusted/split-adjusted daily bars.

**Impact:** Catastrophic for Bowaka v2 features. ATR%, RVOL, EMA, gap, price filters, range expansion, and historical volume baselines can all be wrong around splits/reverse splits.

**Fix:** Thread `daily_adjustment` through all daily readers and caches:

- `data/suppliers.py`
- `data/cached_suppliers.py`
- `data/daily_cache_batch.py`
- PIT universe builders if they read daily data;
- autoconfig lake probes;
- preflight probes;
- run manifest and dataset manifest.

Recommended call shape:

```python
store.daily_bars(
    symbol,
    start,
    end,
    feed=feed,
    adjustment=cfg.market_data.daily_adjustment,
)
```

**Acceptance tests:**

- Synthetic raw/split-adjusted sentinel lake: raw and split-adjusted prices intentionally differ; simulator must use split-adjusted when required.
- Feature cache and direct supplier must produce identical adjusted daily baselines.
- Run manifest must include `effective_daily_adjustment: split_adjusted`.
- If only raw daily partitions exist and split adjustment is required, Notebook 10 fails before trials.

---

### P0-007 — `objective_minimal` hides the evidence needed to diagnose inactive studies

**Evidence:** Pasted output explicitly says per-trial fold backtests skip disk artifact writes. In the same run, all objective values tie at `-1.5`.

**Impact:** High. Debugging cannot identify whether failure occurs at universe, scanner, risk, quote, order, fill, or exit stage.

**Fix:** Introduce an automatic diagnostic escalation:

```python
if trial_number < cfg.optuna.debug_first_n_trials:
    artifact_mode = "full_debug"
elif objective_surface_is_constant_so_far:
    artifact_mode = "full_debug"
else:
    artifact_mode = cfg.optuna.objective_artifact_mode
```

At minimum, write debug artifacts for Trial 0 and the first two random trials.

**Acceptance tests:**

- In Notebook 10 mode, first debug trials always write candidate/gate/entry/order/fill summaries.
- If all first `N` trials tie, the next trial escalates to debug artifact mode before study failure.

---

### P0-008 — Valid-trial and promotion evidence semantics are unsafe

**Evidence:** Historical artifacts show `status: ok` with invalid/degraded studies. The current pasted output can still produce best-trial logs during a flat/no-trade surface.

**Impact:** High. Reviewers may mistake “study completed” or “best trial exists” for a valid parameter recommendation.

**Fix:** Separate these concepts:

```json
{
  "study_execution_completed": true,
  "study_valid": false,
  "invalid_reasons": ["CONSTANT_OBJECTIVE_SURFACE", "NO_TRADE_STUDY"],
  "reviewable_for_research": false,
  "parameter_recommendation_allowed": false,
  "promotable_to_paper": false,
  "promotable_to_live": false,
  "best_params": null
}
```

A run can be operationally complete but scientifically invalid.

**Acceptance tests:**

- no-trade study => no best params and no promotion;
- constant-objective study => no best params and no promotion;
- invalid incumbent padding => no incumbent comparison and no promotion;
- valid IEX research run => `reviewable_for_research=true` but `promotable_to_live=false`.

---

### P1-001 — Dynamic Optuna categorical search-space failure remains a regression risk

**Evidence:** Older artifacts showed repeated `CategoricalDistribution does not support dynamic value space`; the new pasted output does not show it.

**Impact:** Medium-to-high if it regresses. It can silently collapse all non-incumbent trials.

**Fix:** Keep the previous remediation but demote it from the primary current symptom:

- include search-space hash in study name and study user attrs;
- fail if existing RDB study hash differs;
- keep incumbent enqueue separate from distribution definition;
- avoid dynamic distributions under stable parameter names;
- test against PostgreSQL, not just in-memory Optuna.

**Acceptance tests:**

- 3-trial incumbent + sampled run completes in PostgreSQL without dynamic errors.
- Reusing a study with changed categorical choices fails with `SEARCH_SPACE_HASH_MISMATCH` before trials.

---

### P1-002 — Stale artifacts contaminate evidence

**Evidence:** Older executed notebooks/artifacts contain stale key names such as `exits.stop_loss_pct`, `exits.take_profit_pct`, and `sizing.dollars_per_position`.

**Impact:** Medium. Reviewers can accidentally treat stale outputs as current Bowaka v2 evidence.

**Fix:** Quarantine stale artifacts and add CI checks that non-quarantined evidence does not contain stale contract keys.

---

> **Revision note for Sections 8 onward:** The broader completeness review, phased plan, command workflow, and evidence-package recommendations from the first report remain largely valid. Where those sections mention the older dynamic-search-space failure as the dominant Notebook 10 symptom, reinterpret it under the revised ranking above: dynamic search-space errors are now a regression risk, while the constant `-1.5` no-trade/objective-surface failure is the current primary blocker.

## 8. Completeness review: what Bowaka v2 lab tests and what is missing

### 8.1 Data lineage and reproducibility

#### Already present

- Lake manifest and dataset hashes.
- Code/config hashes in artifacts.
- Source contract hash.
- Dataset hash stability tests.
- Config snapshot artifacts.

#### Missing / weak

- Daily adjustment actually used by readers is not guaranteed in artifacts.
- Resolved autoconfig path is temporary by default (`/tmp/bowaka_wf_autocfg_.../walkforward_resolved.yml`), which weakens lineage.
- Tests do not prove manifest adjustment and partition adjustment agree.
- No strong stale-artifact exclusion in evidence generation.

#### Required work

- Persist resolved Notebook 10 config under `artifacts/resolved_configs/<study_name>.yml`.
- Include `effective_daily_adjustment`, `minute_adjustment`, `manifest_adjustment`, and `partition_adjustments_seen` in every run manifest.
- Fail if resolved config file cannot be recovered from artifact.
- Hash the resolved config, not just the base config.

---

### 8.2 Data quality and corporate actions

#### Already present

- Adjustment mismatch checks.
- Split-adjustment mismatch checks.
- Audit-row imported checks.
- Quote coverage checks.
- Corporate-actions directory exists in lake layout.

#### Missing / weak

- Daily reader may not use split-adjusted partitions.
- No explicit comparison between raw and split-adjusted partitions for symbols with split actions.
- No proof that reverse splits in microcaps are handled correctly in prior baselines.
- No test for symbol changes/renames, delistings, halted securities, or survivorship across the lake.

#### Required work

- Add corporate-action replay fixtures for at least one split and one reverse split.
- Validate that the PIT universe uses the symbol state as of each session, not current listings only.
- Validate that post-split daily baselines do not jump due raw historical data.
- Validate excluded instruments remain excluded even if price/volume criteria pass.

---

### 8.3 Point-in-time universe

#### Already present

- PIT universe builder exists.
- Universe snapshot artifacts exist.
- Tests for universe hash in candidate events and snapshots exist.
- Actual strategy universe classification is mirrored.

#### Missing / weak

- It is unclear whether every fold/session in Notebook 10 rebuilds the full actual universe from the lake or uses a capped sample for performance.
- Saved checkpoint showed `universe_pit_sample` with eligible count but `pit_union_symbol_count: 0` in output summary, which is inconsistent and must be investigated.
- Need prove no final-holdout symbols leak into training universe construction if future metadata is used.

#### Required work

- For every fold, emit:
  - number of raw assets;
  - number excluded by instrument class;
  - number excluded by price;
  - number excluded by ADV;
  - final eligible symbol count;
  - symbol list hash.
- Add a test that PIT universe for a known date excludes a symbol that only becomes eligible after that date.
- Add a test that training/validation/final holdout each have separately hashed universe snapshots.

---

### 8.4 Feature/label timing and look-ahead risk

#### Already present

- Feature functions compute prior daily baselines and forming-session features.
- Tests exist for signal appearing intraday and feature parity.
- Holdout guard tests exist.

#### Missing / weak

- Need prove daily features never include the current session daily close/volume.
- Need prove volume curve uses only historical data available before the session, not the session being traded.
- Need prove all joins respect timezone and session boundaries, especially around DST transitions and half days.
- Need feature drift tests between actual scanner and lab scanner over real IEX historical partitions.

#### Required work

- Golden-master scanner replay for a small set of real IEX sessions:
  - run actual scanner in replay mode;
  - run lab scanner replay;
  - compare every candidate/gate field.
- Add DST/half-day calendar fixtures.
- Add a test that deliberately injects current-day daily volume into the daily cache and verifies the leak detector catches it.

---

### 8.5 Execution and fill realism

#### Already present

- Marketable limit fill simulation exists.
- Quote coverage metrics exist.
- Partial-fill tests exist.
- Same-minute stop/target ambiguity test exists.
- Gap-through-stop test exists.
- Fill-rate and slippage metrics are recorded.

#### Missing / weak

- IEX current-code-parity may use zero-spread fallback due missing historical quotes. That is acceptable for parity labeling but not for realistic execution claims.
- Price-chase gate and halt gate are partly excluded from optimization because the lake lacks required feeds.
- Queue position is not modeled.
- Market impact is likely simple or absent.
- Sub-minute sequencing is approximated from 1-minute bars; this is a major limitation for small-cap spikes.
- Opening gap and late-day liquidity degradation need more stress cases.

#### Required work now, using IEX

- Keep zero-spread fallback for IEX current-code-parity but label all fill metrics accordingly.
- Add adverse fill stress matrix:
  - +25 bps slippage;
  - +50 bps slippage;
  - +100 bps slippage;
  - spread multiplier 1.5x / 2x / 3x;
  - partial-fill cap by notional/ADV bucket;
  - no-fill when signal bar range does not support fill.
- Require optimized parameters to be robust under these stress cases before they are even paper-candidate recommendations.

#### Required later, with SIP

- Real historical NBBO quote coverage.
- Quote age and spread gates using real quotes.
- LULD/halt feed.
- Better order-book / queue proxy.
- Paper/live execution reconciliation by symbol/ADV/spread/time-of-day bucket.

---

### 8.6 Risk and portfolio realism

#### Already present

- Daily loss limits.
- Gross exposure limits.
- Stopout limits.
- Max entries/day.
- Max lots/symbol.
- Protected position state.
- Multi-day hold tests.

#### Missing / weak

- Need prove risk state updates intraday before later scan decisions in all event orders.
- Need stress tests for correlated symbols all stopping simultaneously.
- Need buying-power / margin / settlement / PDT constraints if relevant to broker account.
- Need rounding to lot size / min notional / share quantity constraints at the exact broker level.
- Need realistic rejects and partial exits under low liquidity.

#### Required work

- Add a portfolio stress fixture with 18 simultaneous positions and multiple same-day stopouts.
- Validate kill-switch behavior against actual strategy logs.
- Add broker-constraint config fields and tests for min share increment, buying power, fractional-share disallowance, and rejected orders.

---

### 8.7 Objective function and Bayesian optimization

#### Already present

- Objective uses net return, drawdown, worst-day loss, penalties, quote coverage, fill rate, etc.
- Low-trade penalty exists.
- Robustness/sensitivity infrastructure exists.
- Final holdout is guarded.

#### Missing / weak

- Objective can still accept degraded folds if not explicitly rejected.
- Need minimum trade count by fold and by regime, not just aggregate.
- Need multiple seeds or repeated studies to show parameter stability.
- Need parameter importance and local robustness around best params.
- Need enforce that final holdout is never used in Optuna trial selection.
- Need ensure optimized risk controls are not silently treated as alpha parameters.

#### Required work

- Add `min_trades_per_validation_fold` and `min_active_days_per_fold` gates.
- Add `min_valid_fold_fraction = 1.0` for real studies.
- Add “incumbent must be valid” gate.
- Run at least 3 repeated Optuna studies with different sampler seeds and compare top parameter regions.
- Use nested walk-forward or rolling validation; never tune on final holdout.
- Generate a finalist report showing:
  - best vs incumbent;
  - best vs simple baseline;
  - all fold scores;
  - worst fold details;
  - parameter stability;
  - stress matrix results;
  - final-holdout result, computed once after selection.

---

### 8.8 Paper-log reconciliation

#### Already present

- Paper-log fixtures exist.
- Reconciliation tests exist.
- Synthetic paper-recon tests exist.

#### Missing / weak

- Need real Bowaka v2 paper-trading logs for recent IEX sessions.
- Need candidate-by-candidate reconciliation:
  - actual scanner candidate emitted?;
  - lab would emit?;
  - actual rejection reason?;
  - lab rejection reason?;
  - actual order submitted?;
  - simulated order submitted?;
  - actual fill price/qty/time?;
  - simulated fill price/qty/time?;
  - actual bracket attach?;
  - simulated protected-position state?;
  - actual exit?;
  - simulated exit?
- Need reconciliation tolerances by metric and severity.

#### Required work

Collect at least 10 paper-trading sessions and build a reconciliation report:

| Metric | Acceptance threshold for IEX current-code-parity |
|---|---:|
| Candidate event recall | >= 99% for events with matching data availability |
| Gate/rejection reason exact match | >= 95% |
| Entry decision match | >= 95% |
| Fill/no-fill match | >= 85% initially, stricter later |
| Fill price median absolute error | documented and bucketed by spread/ADV |
| Exit reason match | >= 90% for deterministic stop/time/max-hold cases |
| Bracket attach / protection event match | 100% for deterministic event logs |
| Daily realized PnL sign match | >= 90%, with explainable exceptions |

Paper reconciliation is not required to buy SIP, but it is required before any optimized parameters are treated as paper-candidate or live-candidate.

---

## 9. Recommended phased implementation plan

### Phase 0 — Freeze evidence and make failures visible

**Goal:** Stop accepting invalid studies.

Tasks:

1. Quarantine stale artifacts with old parameter keys.
2. Add artifact stale-key CI test.
3. Add failed-study artifact requirements:
   - `status: "failed"`
   - empty `best_params`
   - `best_value: null`
   - explicit `failure_reason`
   - fold/trial error summary.
4. Add degraded-fold invalid-trial test.
5. Add dynamic-search-space failure regression test.
6. Add Notebook 10 output validator that rejects:
   - sentinel best value;
   - degraded folds;
   - dynamic Optuna errors;
   - stale key names;
   - missing resolved config artifact.

Acceptance criteria:

- Replaying the checkpoint failure pattern produces a failed artifact and raises.
- There is no path from all-invalid trials to `status: "ok"`.

---

### Phase 1 — Fix daily adjustment and IEX lake preflight

**Goal:** Use IEX data without hidden raw/adjustment mismatch.

Tasks:

1. Implement `daily_adjustment_for_config`.
2. Pass adjustment to all daily readers and symbol probes.
3. Add split-adjusted-vs-raw sentinel tests.
4. Add current-code-parity full-fold preflight for hard prerequisites.
5. Persist effective data policies in manifests.
6. Fail if manifest says split-adjusted but partition read path is raw or missing.

Acceptance criteria:

- A tiny lake with raw and split-adjusted partitions proves the adjusted partition is used.
- Notebook 10 short IEX run fails immediately if required partitions are absent.
- Notebook 10 short IEX run proceeds only when daily/minute prerequisites pass.

---

### Phase 2 — Prove strategy-contract parity

**Goal:** Trial 0 and scanner/backtester behavior match the actual Bowaka v2 contract.

Tasks:

1. Make incumbent baseline come from the mapped actual lab config.
2. Remove silent padding for behaviorally meaningful keys.
3. Add exact incumbent test for every search-space key.
4. Add scanner replay golden master comparing actual scanner and lab replay on selected IEX sessions.
5. Add config-diff report that shows actual config -> lab config mapping and any intentional differences.

Acceptance criteria:

- Trial 0 exactly equals the actual-derived lab config for all search-space keys.
- Scanner replay candidate/gate fields match within defined tolerances.
- Any unmapped live key has a documented simulator equivalent or explicit limitation.

---

### Phase 3 — Make Notebook 10 a reliable production research runner

**Goal:** Notebook 10 becomes a thin, reproducible, validated runner.

Tasks:

1. Move all logic into Python functions or CLI.
2. Notebook only calls the runner and displays artifacts.
3. Persist resolved config under artifacts.
4. Include preflight summary before optimization.
5. Include post-run validation summary after optimization.
6. Add Papermill IEX short-run test.
7. Add PostgreSQL parallel test as required CI job, not optional local-only smoke.

Acceptance criteria:

- `N_TRIALS=3`, `N_STARTUP_TRIALS=1`, `N_JOBS=1`, IEX short run completes with at least two non-incumbent trials and no dynamic errors.
- `N_JOBS=2` PostgreSQL run completes in CI with identical search-space hash across workers.
- Notebook fails if the Python runner fails.

---

### Phase 4 — Upgrade execution realism under IEX constraints

**Goal:** Make IEX research more conservative without pretending it is SIP.

Tasks:

1. Add slippage/spread stress matrix.
2. Add ADV bucket partial-fill caps.
3. Add no-fill scenarios for bars that do not support marketable limit execution.
4. Add adverse-selection penalty by signal spike size or bar extension.
5. Add late-day liquidity stress.
6. Add gap-through-stop and same-minute ambiguity reporting to objective penalties.

Acceptance criteria:

- Finalist parameter sets remain acceptable under conservative stress cases.
- Any parameter set that wins only under zero-spread fallback is rejected.

---

### Phase 5 — Improve optimization methodology

**Goal:** Prevent overfitting and data snooping.

Tasks:

1. Add repeated Optuna studies with different sampler seeds.
2. Add parameter stability report.
3. Add local perturbation robustness around best params.
4. Add fold-level minimum trade count and active-day count.
5. Add regime segmentation:
   - high/low volatility;
   - high/low liquidity;
   - market trend / risk-on-risk-off;
   - ADV buckets;
   - time of day.
6. Keep final holdout untouched until finalist selection.

Acceptance criteria:

- Top parameter region is stable across seeds and folds.
- Best parameters are not a knife-edge.
- Final holdout is reported separately and not used to tune.

---

### Phase 6 — Paper reconciliation

**Goal:** Compare simulator to actual Bowaka v2 paper behavior.

Tasks:

1. Collect paper logs for at least 10 sessions.
2. Build event-level reconciliation report.
3. Bucket fill error by symbol, ADV, spread proxy, time-of-day, and signal strength.
4. Use reconciliation errors to calibrate slippage/no-fill models.
5. Require reconciliation gates before paper-candidate parameters.

Acceptance criteria:

- Candidate/gate parity is high.
- Fill model error is measured and conservatively bounded.
- Sim-vs-paper PnL differences are explainable.

---

### Phase 7 — SIP migration readiness

**Goal:** Once SIP is funded, switch from IEX current-code-parity to intended realism.

Tasks:

1. Add SIP bars and quotes partitions.
2. Add NBBO quote coverage gates.
3. Add LULD/halt feed.
4. Add SIP-vs-IEX feature divergence report.
5. Recalibrate RVOL thresholds; actual config already comments that SIP thresholding should differ from IEX.
6. Rerun the full test matrix and Notebook 10 in intended-realism mode.

Acceptance criteria:

- Intended-realism preflight passes all required checks.
- Quote coverage exceeds threshold for every fold.
- IEX-to-SIP feature divergences are measured and understood.
- Paper reconciliation passes with SIP-grade quotes.

---

## 10. Concrete tests to add or strengthen

### 10.1 Notebook 10 / Optuna validity tests

#### `test_notebook_10_iex_short_run_no_dynamic_space_errors`

Run Notebook 10 or the underlying runner against a tiny but real IEX-style lake with:

- split-adjusted daily bars;
- minute bars;
- no quotes;
- `simulation.mode: current_code_parity`;
- `N_TRIALS=3`;
- `N_STARTUP_TRIALS=1`;
- `INCUMBENT_TRIAL=True`.

Assert:

- `status == "ok"` only if all folds are valid;
- no output contains `CategoricalDistribution does not support dynamic value space`;
- trial 0 is incumbent;
- trials 1 and 2 sample all variables;
- `promotion_evidence.parameter_recommendation_allowed == false` for IEX-only run.

#### `test_walkforward_rejects_any_degraded_fold_real_modes`

Monkeypatch one fold to return `_degraded_fold` with finite score. Assert `OptunaStudyInvalidError`.

#### `test_walkforward_failed_trials_do_not_leave_best_params`

Force all trials to fail dynamically or structurally. Assert failed artifact has:

```json
{
  "status": "failed",
  "best_params": {},
  "best_value": null
}
```

#### `test_study_search_space_hash_mismatch_refuses_reuse`

Create a study with one categorical choice set; rerun with same study name and different choices. Assert clear failure before optimization.

---

### 10.2 Data adjustment tests

#### `test_daily_supplier_uses_split_adjusted_when_required`

Build raw and split-adjusted daily partitions with intentionally different values. Assert feature baseline uses split-adjusted values.

#### `test_autoconfig_does_not_treat_raw_daily_as_adjusted_capability`

Autoconfig capability probe must report `has_required_daily_adjustment=false` when only raw exists and adjusted is required.

#### `test_manifest_partition_adjustment_consistency`

Manifest says split-adjusted but no split-adjusted partition exists. Assert preflight failure.

---

### 10.3 Incumbent baseline tests

#### `test_incumbent_baseline_uses_mapped_lab_config_for_all_search_keys`

Assert every `SEARCH_SPACE_SPEC` key exists in the actual-derived lab config and equals the incumbent trial value.

Specific hard assertions:

```python
assert params["execution.max_quote_age_seconds"] == 15
assert params["execution.max_spread_bps"] == 100
assert params["exits.stop_pct"] == 0.025
assert params["exits.target_pct"] == 0.15
assert params["sizing.equal_slice_bankroll_fraction"] == 0.80
```

#### `test_no_incumbent_padding_for_behavioral_keys`

If any behavioral key is padded from search-space midpoint, fail.

---

### 10.4 Promotion evidence tests

#### `test_invalid_study_not_promotable`

Any invalid/degraded study must set all promotion booleans false.

#### `test_iex_valid_research_run_not_parameter_recommendation`

Valid IEX research run can be reviewable, but not a paper/live parameter recommendation.

#### `test_promotion_requires_paper_reconciliation_for_paper_candidate`

A run cannot become `paper_candidate` without a reconciliation artifact meeting thresholds.

---

### 10.5 Strategy parity tests

#### `test_actual_scanner_replay_matches_lab_replay_on_iex_session`

Run both actual scanner replay and lab replay over a known IEX session. Compare:

- candidate symbols;
- scan timestamps;
- feature values;
- gate pass/fail;
- rejection reasons;
- signal strength.

#### `test_execution_gate_mapping_matches_actual_strategy`

Assert mapped lab execution config exactly reflects actual execution config:

- parent order style;
- limit/slippage offset;
- quote age;
- spread threshold;
- price chase thresholds;
- halt gate availability/limitation;
- bracket pricing mode.

---

### 10.6 Paper reconciliation tests

#### `test_real_paper_log_reconciliation_recent_sessions`

Use actual Bowaka v2 paper logs for multiple sessions. Assert event-level metrics meet current-code-parity thresholds.

#### `test_fill_model_calibration_artifact_exists`

For any optimization report intended for parameter review, require a fill-calibration artifact or explicit refusal reason.

---

## 11. Suggested command workflow for engineers

From the lab root:

```bash
cd quants-lab/research_notebooks/bowaka_v2_lab
```

Create a clean environment with the required dependencies:

```bash
python -m pip install -e ../bowaka_common
python -m pip install -e ".[dev]"
```

Run fast static/config tests first:

```bash
pytest tests/integration/test_all_shipping_configs_validate.py \
       tests/integration/test_import_actual_config_roundtrip.py \
       tests/integration/test_current_code_parity_fails_on_raw_lake_when_required.py \
       tests/integration/test_walkforward_runner_invalid_study.py \
       tests/integration/test_run_validation_folds_propagates_startup_dq.py
```

Run Notebook 10 short IEX proof after remediation:

```bash
papermill notebooks/10_optuna_walkforward.ipynb \
  artifacts/executed_notebooks/10_optuna_walkforward_iex_short_$(date +%Y%m%d_%H%M%S).ipynb \
  -p CONFIG_PATH configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml \
  -p FEED iex \
  -p N_TRIALS 3 \
  -p N_STARTUP_TRIALS 1 \
  -p N_JOBS 1 \
  -p INCUMBENT_TRIAL true
```

Run PostgreSQL two-worker proof in CI:

```bash
export BOWAKA_TEST_POSTGRES=1
export OPTUNA_STORAGE='postgresql+psycopg2://optuna:optuna@optuna-postgres:5432/optuna'
pytest tests/integration/test_parallel_smoke_two_workers_postgres.py
```

Before showing results to management, run an artifact validator that checks:

```text
- no stale parameter keys;
- no dynamic Optuna errors;
- no degraded folds;
- no sentinel best value;
- no missing resolved config;
- no raw daily adjustment when adjusted is required;
- promotion evidence is conservative;
- IEX partial-tape caveat is present.
```

---

## 12. Recommended evidence package for SIP funding approval

The funding case should not claim IEX proves production edge. It should claim the lab is technically ready to evaluate Bowaka v2 rigorously and fail closed.

Recommended package:

### 12.1 Must include

1. Fresh test report from clean environment.
2. Fresh Notebook 10 short IEX run with:
   - 3+ trials;
   - incumbent trial;
   - non-incumbent trials;
   - no dynamic search-space errors;
   - no degraded folds;
   - split-adjusted daily read path proved;
   - resolved config artifact;
   - full preflight artifact.
3. One broader IEX walk-forward run after the short proof passes.
4. Artifact validation report.
5. Strategy parity report showing actual Bowaka v2 config -> lab config mapping.
6. IEX limitation statement.
7. SIP migration checklist.

### 12.2 Must not include as evidence

- The stale 2026-05-21 Notebook 10 artifact with old parameter keys.
- The checkpoint run that reported `status: ok` after failed trials.
- Any synthetic-only optimization as evidence of Bowaka v2 performance.
- Any run where `best_value` comes from degraded folds or no trades.
- Any run where daily adjustment is not explicitly recorded.

### 12.3 Suggested management-facing wording

> The IEX runs are not being used to claim production readiness. They are being used to prove the test harness, data lineage, walk-forward optimization, fail-closed behavior, and artifact reproducibility. SIP funding will allow us to replace IEX partial-tape assumptions with SIP/NBBO quote coverage and run the same validated framework at the intended realism tier.

---

## 13. Specific code remediation checklist

### 13.1 `data/suppliers.py`

- Add config-aware adjustment parameter to `make_lake_suppliers` or pass `cfg` to it.
- Update `daily_bars_supplier`:

```python
return store.daily_bars(symbol, start, end, feed=feed, adjustment=daily_adjustment)
```

- Update forward/minute supplier if any adjustment concept is required for minute bars, though current minute bars are likely raw.
- Ensure `build_daily_cache_from_lake` also passes adjustment.

### 13.2 `optuna/autoconfig.py`

- Replace `lake_has_bars` with structured capability probe.
- Pass adjustment to `available_symbols`.
- Check daily and minute coverage.
- Write capability probe to artifacts.
- Do not use `/tmp` as the only resolved config location for notebook runs.

### 13.3 `optuna/walkforward_runner.py`

- Treat `StartupDataQualityError`, `DataQualityError`, `PreflightError`, `HoldoutGuardError`, `OptunaStudyInvalidError`, and any known data-contract errors as structural.
- Mark degraded folds explicitly.
- Reject trials with degraded/non-ok folds.
- Run current-code-parity full-fold preflight for hard prerequisites.
- Enforce search-space hash compatibility before reusing an Optuna study.
- Build incumbent from mapped lab config.
- Fail if incumbent comparison is partial unless explicitly configured as research-only partial-comparison.

### 13.4 `optuna/promotion_gates.py`

- Rename or split `promotable` semantics.
- Add data-validity and study-validity inputs.
- Add paper-reconciliation and SIP/quote-coverage requirements for higher tiers.
- Make IEX valid runs reviewable but not promotable parameter recommendations by default.

### 13.5 Tests

- Add the tests in Section 10.
- Convert PostgreSQL test from optional to required in at least one CI job.
- Add real IEX Notebook 10 short-run test, not just synthetic Papermill smoke.
- Add stale artifact key test.

---

## 14. Quant methodology recommendations

### 14.1 Do not optimize too many risk controls as alpha

The current search space includes both signal parameters and risk controls. That is acceptable for research, but parameter recommendations become hard to interpret if Optuna improves objective by simply loosening risk controls.

Recommended approach:

- Run Study A with risk controls frozen to actual config.
- Run Study B with risk controls tunable but labeled `risk_policy_experiment`.
- Compare signal-only improvements separately from risk-policy changes.
- Do not promote risk-control changes without separate risk approval.

### 14.2 Use multiple objectives/reports, not one scalar only

A single scalar objective should not be the only output. Each finalist needs:

- median fold score;
- worst fold score;
- fold score dispersion;
- net return;
- max drawdown;
- worst day loss;
- trade count;
- turnover;
- fill rate;
- missing quote count;
- partial fill count;
- stopout count;
- exposure utilization;
- no-trade days;
- stress matrix pass/fail;
- final holdout result.

### 14.3 Penalize low sample size aggressively

Microcap/momentum strategies can produce attractive metrics from very few trades. Require minimums:

- minimum trades per validation fold;
- minimum active trading days per fold;
- minimum number of symbols traded;
- no single symbol contributes more than a specified fraction of PnL;
- no single day contributes more than a specified fraction of total PnL.

### 14.4 Regime analysis is mandatory before paper recommendations

Break results down by:

- price bucket;
- ADV bucket;
- ATR bucket;
- RVOL bucket;
- spread proxy bucket;
- time of day;
- market index regime;
- high/low volatility day;
- earnings/news proxy if available.

A parameter set that only works in one narrow regime should be labeled research-only.

### 14.5 Robustness around best parameters

For each finalist, perturb each selected parameter by ±5%, ±10%, and one discrete step. Reject if small changes destroy performance. This catches knife-edge overfit thresholds.

---

## 15. Final checklist before the next Notebook 10 run

Do not run the full 200-trial workstation study again until all of this is true:

```text
[ ] Stale artifacts quarantined.
[ ] Daily adjustment read path fixed and tested.
[ ] Current-code-parity full-fold preflight added.
[ ] Degraded folds invalidate trials.
[ ] Invalid trial sets fail the whole study.
[ ] Search-space hash compatibility enforced.
[ ] Incumbent baseline built from mapped actual lab config.
[ ] Promotion evidence semantics fixed.
[ ] Notebook 10 writes resolved config to artifacts.
[ ] Papermill IEX short-run test passes.
[ ] PostgreSQL two-worker test passes.
[ ] Artifact validator passes on the fresh Notebook 10 output.
```

Only after the short run passes should the 200-trial workstation config be run.

---

## 16. Final conclusion

The lab is directionally strong and already contains many of the components a serious quant review would expect. The uploaded actual strategy and the lab reference copy appear aligned at the core-source level. The blocking issues are in the **simulation/optimization evidence path**, especially Notebook 10.

The most important remediation is to make the system fail closed:

- no raw daily bars when adjusted are required;
- no current-code-parity run without hard data prerequisites;
- no degraded fold counted as a valid fold;
- no dynamic search-space failure counted as a completed optimization;
- no “promotable” evidence from invalid or IEX-only research runs;
- no incumbent baseline unless it truly equals the mapped actual strategy.

Using IEX now is reasonable and should not block the work. The right deliverable for management is not “IEX proves Bowaka v2 is profitable.” The right deliverable is “the Bowaka v2 lab can ingest real IEX data, reproduce the actual strategy contract, run walk-forward optimization, reject invalid studies, preserve lineage, and produce conservative artifacts; SIP will upgrade the same validated framework to intended realism.”

Until the P0 issues are fixed and a fresh Notebook 10 short run passes, **Notebook 10’s optimization outputs should not be used for parameter selection, paper-trading recommendations, or SIP-funding evidence except as examples of failure modes now being remediated.**

---

## Appendix A — Source-code evidence map

The following references are the main code locations used for this audit. Line numbers may drift after remediation, so treat them as orientation markers rather than permanent anchors.

### A.1 Autoconfig feed detection

File:

```text
src/bowaka_v2_lab/optuna/autoconfig.py
```

Relevant behavior:

- `lake_has_bars(...)` returns true if at least one daily-bar symbol exists for the feed.
- It calls `available_symbols(... timeframe="1d", feed=feed)` without an adjustment argument.
- `detect_best_feed(...)` chooses:
  - SIP + quotes -> `intended_realism`
  - SIP bars without quotes -> `current_code_parity`
  - IEX bars -> `current_code_parity`
  - no bars -> `smoke_fixture`

Risk:

- The probe is not enough to prove the lake supports the actual study range or adjusted daily baselines.

Required change:

- Replace boolean detection with structured capability report and pass the required adjustment.

### A.2 Daily suppliers and raw default risk

Files:

```text
src/bowaka_v2_lab/data/suppliers.py
../bowaka_common/src/bowaka_common/marketdata/store.py
../bowaka_common/src/bowaka_common/marketdata/catalog.py
```

Relevant behavior:

- `make_lake_suppliers(...).daily_bars_supplier()` calls `store.daily_bars(symbol, start, end, feed=feed)`.
- `MarketDataStore.daily_bars(...)` defaults `adjustment="raw"`.
- `available_symbols(...)` also defaults `adjustment="raw"`.

Risk:

- Actual strategy requires adjusted/split-adjusted daily bars, but the lab may read raw daily partitions unless patched.

Required change:

- Thread effective daily adjustment through all daily reads and probes.

### A.3 Data-quality gating

File:

```text
src/bowaka_v2_lab/data/data_quality.py
```

Relevant behavior:

- `evaluate_startup_dq(...)` gates `current_code_parity` only on adjustment-enforcement failures.
- This is directionally correct for IEX: missing quotes can be tolerated/warned, but raw/adjustment mismatch cannot.

Risk:

- The checkpoint output showed adjustment failures being logged as non-structural fold failures, which means the intended structural exception path was not effective in that run.

Required change:

- Ensure every data-quality startup failure raises a structural exception that cannot be degraded into fold metrics.

### A.4 Walk-forward full-fold preflight

File:

```text
src/bowaka_v2_lab/optuna/walkforward_runner.py
```

Relevant behavior:

- Full per-fold preflight currently runs only for `simulation.mode == "intended_realism"`.
- Current-code-parity is not fully preflighted across all fold windows.

Risk:

- IEX current-code-parity can discover hard data failures only during trial execution.

Required change:

- Add current-code-parity full-fold preflight with a reduced but hard gate set.

### A.5 Fold degradation and valid-trial filtering

File:

```text
src/bowaka_v2_lab/optuna/walkforward_runner.py
```

Relevant behavior:

- `_degraded_fold(...)` creates finite bad metrics.
- `_run_validation_folds(...)` appends degraded folds for broad non-structural exceptions.
- Valid-trial filtering rejects sentinel scores and missing fold metrics, but not degraded/non-ok fold metrics.

Risk:

- Degraded trial can become the best valid trial.

Required change:

- Store fold status and reject any degraded/non-ok fold for real studies.

### A.6 Search space

File:

```text
src/bowaka_v2_lab/optuna/search_space.py
```

Relevant behavior:

- `SEARCH_SPACE_VERSION = 2`.
- Search space includes signal gates, sizing, risk, execution quote age/spread, stop/target/max-hold/time-stop/fade thresholds.
- Time stop exit time is categorical.

Risk:

- Saved Notebook 10 checkpoint showed dynamic categorical search-space failures. Current code may have remediated some causes, but it is not proven until a fresh run passes.

Required change:

- Hash and enforce the search space at study creation and across workers.

### A.7 Incumbent baseline

File:

```text
src/bowaka_v2_lab/optuna/walkforward_runner.py
```

Relevant behavior:

- `_incumbent_baseline_params()` reads the raw frozen contract and dotted-looks up search-space keys.
- Missing keys can be padded from search-space defaults before enqueueing.

Risk:

- Lab-mapped keys such as `execution.max_quote_age_seconds` may not equal actual nested strategy keys.

Required change:

- Build incumbent from the actual-derived lab config after the same mapping used for shipping configs.

### A.8 Promotion gate

File:

```text
src/bowaka_v2_lab/optuna/promotion_gates.py
```

Relevant behavior:

- IEX caps effective tier at `research_only`.
- `promotable` can be true if requested tier is already `research_only`.

Risk:

- `promotable: true` can be misunderstood as a usable parameter recommendation. In the checkpoint it appeared in an invalid study.

Required change:

- Split `reviewable_for_research`, `parameter_recommendation_allowed`, `promotable_to_paper`, and `promotable_to_live`.

### A.9 Current Notebook 10 tests

Files:

```text
tests/integration/test_notebook_10_runs.py
tests/integration/test_notebook_10_incumbent_default_on.py
```

Relevant behavior:

- Papermill test executes Notebook 10 with `FEED="synthetic"` against a tiny lake.
- It validates notebook plumbing, not real IEX current-code-parity behavior.

Risk:

- Synthetic notebook smoke can pass while the real IEX Notebook 10 path remains broken.

Required change:

- Add a real IEX current-code-parity short-run Notebook 10 test.

### A.10 Current raw-lake current-code-parity test

File:

```text
tests/integration/test_current_code_parity_fails_on_raw_lake_when_required.py
```

Relevant behavior:

- Builds raw lake and asserts current-code-parity fails when adjusted data is required.

Value:

- Good test and should be kept.

Gap:

- Does not prove that a split-adjusted lake is actually read using split-adjusted partitions. Add raw-vs-split sentinel value test.

### A.11 Current startup-DQ propagation test

File:

```text
tests/integration/test_run_validation_folds_propagates_startup_dq.py
```

Relevant behavior:

- Monkeypatches fold runner to raise `StartupDataQualityError` and expects propagation.

Value:

- Good regression test.

Gap:

- Does not exercise the real `run_backtest` path inside Notebook 10 / objective workers. Add end-to-end real-path test.

### A.12 Current invalid-study test

File:

```text
tests/integration/test_walkforward_runner_invalid_study.py
```

Relevant behavior:

- Tests all-sentinel study failure and structural exception failure.

Value:

- Good and aligned with the right fail-closed philosophy.

Gap:

- Needs an additional case where fold metrics are finite but marked degraded/non-ok.

### A.13 PostgreSQL parallel test

File:

```text
tests/integration/test_parallel_smoke_two_workers_postgres.py
```

Relevant behavior:

- Requires `BOWAKA_TEST_POSTGRES=1` and a PostgreSQL URL.

Value:

- Essential for real Notebook 10 because workstation config uses PostgreSQL and parallel workers.

Gap:

- Optional tests are often skipped. For serious signoff, this must be a required CI job.

---

## Appendix B — Fresh-run validation template

Use the following as the minimum JSON validation policy for any new Notebook 10 output.

```json
{
  "required_top_level": {
    "status": "ok",
    "simulation_mode": "current_code_parity",
    "feed": "iex",
    "suitability_tier": "research_only",
    "partial_tape": true
  },
  "forbidden_text": [
    "CategoricalDistribution does not support dynamic value space",
    "failed non-structurally: current_code_parity run aborted",
    "stop_loss_pct",
    "take_profit_pct",
    "dollars_per_position"
  ],
  "required_numeric_conditions": {
    "n_trials_completed": ">= N_TRIALS",
    "valid_trial_count": ">= 2",
    "degraded_fold_count": "== 0",
    "dynamic_search_space_error_count": "== 0",
    "best_value": "> _FAILED_TRIAL_SCORE + epsilon",
    "min_trade_count_per_valid_fold": ">= configured_min"
  },
  "required_artifacts": [
    "resolved_config.yml",
    "preflight_report.json",
    "study_metadata.json",
    "trial_summary.parquet_or_json",
    "promotion_evidence.json",
    "artifact_validation_report.json"
  ],
  "promotion_policy": {
    "reviewable_for_research": true,
    "parameter_recommendation_allowed": false,
    "promotable_to_paper": false,
    "promotable_to_live": false
  }
}
```

For any broader IEX run, the same validator should run automatically and fail the notebook if the policy is violated.

---

## Appendix C — Suggested issue backlog

The following backlog can be copied into tickets.

| ID | Priority | Owner | Title | Acceptance criteria |
|---|---:|---|---|---|
| BOWAKA-LAB-001 | P0 | Engineer | Reject degraded folds in Optuna valid-trial filter | A trial with any degraded/non-ok fold is invalid; all-invalid study writes failed artifact and raises. |
| BOWAKA-LAB-002 | P0 | Engineer | Thread split-adjusted daily adjustment through all readers | Raw-vs-split sentinel test proves adjusted partition is used. |
| BOWAKA-LAB-003 | P0 | Engineer | Add current-code-parity full-fold preflight | Missing daily/minute/adjustment coverage fails before trials; missing quotes warn only. |
| BOWAKA-LAB-004 | P0 | Engineer | Enforce search-space hash compatibility | Reusing a study with changed categorical choices fails before optimization. |
| BOWAKA-LAB-005 | P0 | Engineer | Build incumbent from mapped actual lab config | Trial 0 exactly equals mapped active strategy for every search-space key. |
| BOWAKA-LAB-006 | P0 | Engineer | Fix promotion evidence semantics | Invalid/IEX-only run cannot show generic `promotable: true` as parameter recommendation. |
| BOWAKA-LAB-007 | P0 | Engineer | Quarantine stale artifacts and add stale-key check | Non-quarantined artifacts contain no old key names. |
| BOWAKA-LAB-008 | P1 | Quant+Engineer | Add IEX Notebook 10 short-run Papermill test | 3-trial IEX run passes without dynamic errors or degraded folds. |
| BOWAKA-LAB-009 | P1 | Engineer | Make PostgreSQL parallel smoke mandatory in CI | Two-worker PostgreSQL run is part of CI signoff. |
| BOWAKA-LAB-010 | P1 | Quant | Add scanner replay golden master against actual Bowaka scanner | Candidate/gate parity report for selected IEX sessions. |
| BOWAKA-LAB-011 | P1 | Quant | Add slippage/spread/partial-fill stress matrix | Finalists report pass/fail under conservative IEX stress assumptions. |
| BOWAKA-LAB-012 | P1 | Quant+Engineer | Add event-level paper reconciliation for real sessions | 10-session paper reconciliation artifact with thresholds. |
| BOWAKA-LAB-013 | P2 | Quant | Add regime/stability analysis | Top parameter regions stable across folds/seeds/regimes. |
| BOWAKA-LAB-014 | P2 | Engineer | Persist resolved autoconfig config under artifacts | Every study can replay exact resolved config. |
| BOWAKA-LAB-015 | P2 | Quant+Engineer | SIP readiness capability report | Once SIP is available, same preflight proves SIP bars+quotes+halt feed coverage. |



---

## Appendix D — Immediate revised Notebook 10 rescue workflow

This workflow should be executed before another 200-trial optimization. The goal is to locate why all trials receive `-1.5`, not to find profitable parameters.

### D.1 Freeze the current broken output as a regression fixture

Save the pasted run output and parsed summary as:

```text
artifacts/regression_fixtures/notebook10_constant_objective_20260528.log
artifacts/regression_fixtures/notebook10_constant_objective_20260528_summary.json
```

Required summary fields:

```json
{
  "parsed_trials": 60,
  "trial_numbers": [0, 59],
  "unique_values": [-1.5],
  "has_dynamic_categorical_error": false,
  "incumbent_padded_keys": [
    "execution.max_quote_age_seconds",
    "execution.max_spread_bps"
  ],
  "soft_gt_hard_count": 13,
  "hard_gt_critical_count": 1,
  "target_le_stop_count": 16
}
```

Add a regression test that fails if such a run is accepted as valid.

### D.2 Run a single incumbent debug fold, not a full study

Configuration override:

```yaml
optuna:
  n_trials: 1
  n_jobs: 1
  objective_artifact_mode: full_debug
  incumbent_trial: true
  quality_gates:
    require_nonzero_candidates: true
    require_nonzero_entry_attempts: true
    min_total_trades: 1
```

Required output:

- effective daily adjustment = `split_adjusted`;
- per-fold PIT universe count;
- scanner candidates before gates;
- candidates after each signal gate;
- risk/sizing rejects;
- quote/spread/age rejects;
- order submissions;
- fills;
- exit events.

If candidates are zero, stop and debug scanner/data. If candidates exist but entries are zero, debug risk/sizing/entry gates. If orders exist but fills are zero, debug execution/fill model.

### D.3 Run a three-trial debug study

Run Trial 0 incumbent plus two sampled trials with full debug artifacts. Acceptance criteria:

- no padded incumbent behavior keys;
- all three trials have full fold telemetry;
- at least one of candidate/entry/fill counts varies across trials;
- objective values are not all identical unless the run is marked invalid with `CONSTANT_OBJECTIVE_SURFACE`;
- no dynamic Optuna distribution errors.

### D.4 Run a 20-trial short study

Only after D.3 passes, run:

```yaml
optuna:
  n_trials: 20
  n_startup_trials: 10
  n_jobs: 2
  objective_artifact_mode: debug_first_trials
  debug_first_n_trials: 3
```

Acceptance criteria:

- at least two unique rounded objective values;
- minimum activity gates pass;
- invalid relation constraints never reach simulation;
- best trial has non-zero trade/fill evidence or explicit reason why no-fill is valid;
- study artifact says `study_valid: true` only if all gates pass.

### D.5 Only then run 200 trials

The full 200-trial run should be started only after:

- D.1 regression fixture exists;
- D.2 incumbent debug run passes;
- D.3 three-trial debug run passes;
- D.4 twenty-trial short run passes;
- daily adjustment read-path tests pass;
- incumbent mapping test passes;
- search-space relation tests pass;
- current-code-parity full-fold preflight tests pass.

---

## Appendix E — Engineering issue list created by the pasted output

### E.1 `Notebook10ConstantObjectiveInvalidStudy`

**Type:** P0 bug  
**Owner:** optimization/walk-forward engineer  
**Acceptance:** A completed study with all trial values equal to `-1.5` fails with `CONSTANT_OBJECTIVE_SURFACE`; artifact has `study_valid=false` and no `best_params`.

### E.2 `Notebook10NoTradeStudyInvalid`

**Type:** P0 bug  
**Owner:** simulator/objective engineer  
**Acceptance:** Any non-smoke optimization with all folds/trials `n_trades=0` fails with `NO_TRADE_STUDY` unless explicitly configured as a diagnostic no-trade test.

### E.3 `IncumbentBaselineNoPadding`

**Type:** P0 bug  
**Owner:** config/contract engineer  
**Acceptance:** Trial 0 uses mapped actual lab config values for every search-space behavior key. The warning `incumbent baseline padded ...` cannot occur in Notebook 10.

### E.4 `CurrentCodeParityFullFoldPreflight`

**Type:** P0 bug  
**Owner:** data/simulation engineer  
**Acceptance:** IEX/current-code-parity runs validate daily adjustment, daily/minute coverage, PIT universe, and fold windows before trials. Missing SIP/quotes are recorded as limitations, not hard blockers.

### E.5 `DailyAdjustmentThreading`

**Type:** P0 bug  
**Owner:** data engineer  
**Acceptance:** Every daily-bar supplier passes explicit `adjustment=split_adjusted` when required, and tests prove raw partitions are not read accidentally.

### E.6 `SearchSpaceRelationConstraints`

**Type:** P0/P1 bug  
**Owner:** optimization engineer / quant  
**Acceptance:** Sampled configs always satisfy `soft < hard < critical`; default optimization search enforces a minimum reward/risk relationship; search-space version is bumped.

### E.7 `DebugArtifactsForInactiveTrials`

**Type:** P1 feature  
**Owner:** simulator/evidence engineer  
**Acceptance:** Trial 0 and early sampled trials write candidate/gate/entry/order/fill telemetry even when `objective_artifact_mode` is otherwise minimal.

---

## Appendix F — Revised final conclusion

The pasted Notebook 10 output is valuable because it narrows the current failure mode. It suggests that the most visible previous failure — dynamic Optuna categorical distribution errors — may have been partially remediated. But it also proves that Notebook 10 remains unsuitable for Bayesian parameter recommendations.

The current primary failure is not “Optuna cannot run.” It is worse: **Optuna can run while producing no optimization signal at all.** Every displayed trial scores `-1.5`; the saved artifact structure strongly indicates this is the deterministic no-trade/zero-fill penalty. That must be treated as a failed study, not a valid but unprofitable optimization.

The project should continue using IEX for the funding-demo phase. Do not block on SIP. But the demo must show that the lab can:

1. read the correct adjusted data;
2. build correct point-in-time universes;
3. generate candidate and gate telemetry;
4. simulate entries/fills/exits with realistic enough IEX current-code parity;
5. reject inactive/no-trade/constant-objective studies;
6. preserve exact lineage;
7. produce an evidence package that an external quant and engineer can reproduce.

Until those gates pass, `bowaka_v2_lab` remains **research infrastructure under repair**, not a valid optimization engine for Bowaka v2 parameters.
