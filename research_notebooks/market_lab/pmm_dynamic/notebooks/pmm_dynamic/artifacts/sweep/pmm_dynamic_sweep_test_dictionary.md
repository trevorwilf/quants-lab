# PMM Dynamic Sweep Test Dictionary
Prepared for **Market Lab / PMM Dynamic**

**Scope:** This dictionary explains the validation and safety checks used in the PMM Dynamic sweep reports produced under:

`research_notebooks/market_lab/pmm_dynamic/notebooks/pmm_dynamic/artifacts/sweep`

It is written to help both technical reviewers and non-technical readers understand:
- what each reported test means,
- what problem it is trying to catch,
- how the code decides PASS / FAIL,
- how a human reviewer should interpret the result,
- and why the test is useful before paper trading or live deployment.

> **Important:** A good backtest is not enough. In this workflow, the validation tests are the “trust filters.”  
> A strategy can show strong PnL and still be **stop-ship** if it fails holdout, recent-market, parity, or stability checks.

---

## 1. How to read a PMM Dynamic sweep report

If you only have 60 seconds, read the report in this order:

1. **Stop-Ship Checks**  
   If any required stop-ship check fails, treat the candidate as **not deployment-ready**.

2. **Holdout Validation**  
   This tells you whether the exported candidate still works on data it did not see during optimization.

3. **Recent 28-Day Window**  
   This tells you whether the strategy still works in the most recent market conditions.

4. **Stress Test Results**  
   This shows whether the result survives worse fees, latency, liquidity, spread widening, and slippage.

5. **Walk-Forward Results**  
   This shows whether the result is consistent across multiple time slices, instead of just one lucky period.

6. **Sensitivity Analysis** and **Top-K Clustering**  
   These tell you whether the result is robust or just a fragile parameter accident.

7. **YAML Validation** and **Dataset Audit**  
   These make sure the exported config is structurally usable and the input data was not obviously broken.

---

## 2. PASS, FAIL, SKIPPED, and what they really mean

- **PASS** means the item met its coded rule.
- **FAIL** means the item ran and did not meet its coded rule.
- **SKIPPED / NOT_RUN** means there is no evidence either way. In a fail-closed process, “not run” should be treated as **not validated**.

> **Layman version:**  
> PASS means “this test did not disqualify the strategy.”  
> It does **not** mean “this strategy is safe to trade live.”

---

## 3. What is *not* a validation test

Some report sections are important, but they are **descriptive**, not protective:

### Selected Candidate Single-Run Diagnostics
This is the baseline backtest summary for the chosen candidate: PnL, Sharpe, max drawdown, trade count, fees, and similar metrics.

- **Useful for:** Understanding what the strategy looked like in one chosen run.
- **Not enough for trust:** A single strong run can still be overfit or stale.
- **Layman analogy:** This is like a student’s best practice exam score. It is not the same thing as passing the final exam under supervision.

### Selected Candidate Single-Run Objective
This is the internal optimization score breakdown.

- It is used to rank candidates.
- It is **not** a standalone proof that the strategy is robust.
- In objective version 2, the score rewards return and penalizes drawdown, tail risk, fee drag, inventory risk, poor trade count, and bad per-trade edge.

---

## 4. Test dictionary

### 4.1 Dataset Audit

**What it is**  
A data-health check on the candle dataset before trusting any optimization or backtest result.

**What it is testing for**  
Whether the candle history is structurally sane:
- timestamps go forward in order,
- there are no duplicate rows,
- OHLC values are logically valid,
- volumes are not negative,
- the expected number of rows is present,
- gaps are not excessive,
- forward-filled data is not excessive.

**How the code evaluates it**  
The strict audit fails if it finds disqualifying issues. Important default thresholds include:
- missing row fraction > **5%**
- longest gap > **100 × candle interval**
- forward-fill fraction > **25%**
- duplicate fraction > **0**
- OHLC violation fraction above threshold

The stop-ship key `dataset_audit` passes only if `passed_strict == True`.

**How to evaluate it as a human**
- **Good:** Zero duplicates, small or zero missing fraction, small forward-fill fraction, no weird gaps.
- **Bad:** Missing history, lots of synthetic/forward-filled bars, or long outages.
- **Gray area:** A PASS with non-zero forward-fill or gaps can still deserve caution on illiquid markets.

**Why it matters to a layman**  
If the historical data is broken, every result built on top of it is suspect.  
It is like trying to judge a marathon when some lap times are missing.

**Typical red flags**
- Missing rows on a market-making strategy
- Long exchange outages
- A large share of fake “filled-in” candles
- Time ordering issues

**Repo references**
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/data/candles.py`
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/config/defaults.py`

---

### 4.2 Walk-Forward Results

**What it is**  
A time-series cross-validation test. The strategy is evaluated across multiple historical train/test windows instead of one single period.

**What it is testing for**  
Whether the strategy works repeatedly across time, rather than only in one lucky regime.

**How the code evaluates it**
- Default fold shape is:
  - **42 days** train
  - **14 days** test
  - **14 days** step
- A mandatory **embargo** is inserted between train and test:
  - default embargo bars = `max(macd_slow, natr_length) + 10`
- At least **2 folds** are required.
- The report’s aggregate score is computed with a **robust aggregate**:
  - `median(valid fold scores) - 0.5 × MAD`
  - if fewer than 50% of folds are valid, the aggregate is hard rejected

**What it is looking for**
- repeated profitability or at least non-collapse across time,
- acceptable behavior across different mini-regimes,
- protection against “one-period wonder” results.

**How to evaluate it as a human**
- **Good:** Most folds produce real trades, most folds are not rejected, and the fold results are not wildly inconsistent.
- **Concerning:** Many folds are hard rejected (`-1000`), many folds have zero trades, or the aggregate score is negative.
- **Very concerning:** The strategy only works in one or two folds and is dead elsewhere.

**Why it matters to a layman**  
This is like giving the strategy several quizzes from different months instead of grading it on one perfect answer sheet.

**Important nuance**
The stop-ship system does **not** require the walk-forward aggregate score to be positive.  
The coded gates only require:
- `walkforward_robust`: at least **50% of folds are non-rejected**
- `walkforward_positive_majority`: at least **50% of folds have non-negative PnL**

Also, the code counts **zero-PnL folds as non-negative**, so a human reviewer should still be skeptical if many folds have **0 trades** or **0 PnL**.

**Typical red flags**
- Many fold objectives = `-1000`
- Many zero-trade folds
- Negative aggregate score
- Huge dispersion from one fold to the next

**Repo references**
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/objective/walkforward.py`
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/objective/robustness.py`

---

### 4.3 Holdout Validation

**What it is**  
A true out-of-sample test on unseen data reserved from the end of the dataset.

**What it is testing for**  
Whether the optimized strategy generalizes to new data it did not see during optimization.

**How the code evaluates it**
- Default split is the last **20%** of data as holdout.
- The top candidate list is evaluated on holdout.
- The report shows the **best holdout candidate** for research purposes.
- But the stop-ship decision is based on the **exported candidate**, which is always **rank 0**.

For the exported candidate:
- `holdout_passed` requires:
  - holdout score **> 0**
  - and **no collapse**
- `holdout_no_collapse` requires:
  - exported holdout collapse = **False**

A collapse is flagged if:
- holdout score is more than **60% worse** than development score, or
- development score was positive but holdout score is **negative**

**How to evaluate it as a human**
- **Good:** The exported candidate stays positive on holdout and does not collapse.
- **Bad:** Holdout score is negative or much worse than dev.
- **Very bad:** A lower-ranked candidate did better on holdout than the exported candidate. That often means the “winner” was too tuned to the dev set.

**Why it matters to a layman**  
This is the closest thing to a final exam.  
The optimizer studied on the dev set; holdout is the test it never saw.

**Important nuance**
The report’s “best holdout rank” is **not** the actual deployment gate.  
The deployment gate uses the **exported candidate only**.

**Typical red flags**
- `Holdout passed: NO`
- `Collapse detected: YES`
- Best holdout rank is not `0`
- Positive dev score but negative holdout score

**Repo references**
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/objective/holdout.py`

---

### 4.4 Stress Test Results

**What it is**  
A set of adverse scenario re-runs where the same strategy is tested under worse execution conditions.

**What it is testing for**  
Whether the strategy survives more realistic or more hostile live conditions:
- higher fees,
- more latency,
- worse slippage,
- worse fills,
- wider spreads,
- thinner books,
- combinations of the above.

**How the code evaluates it**
- The simulator re-runs the candidate under every defined stress scenario.
- The report records metrics and objective under each scenario.
- The **Worst Scenario** is the scenario with the **lowest objective score**.
- The stop-ship key `stress_not_collapsed` passes if:
  - `worst_score > -10.0`

**How to evaluate it as a human**
- **Good:** Performance degrades gradually, but the strategy remains functional.
- **Bad:** One realistic scenario destroys the edge or creates large drawdown.
- **Very bad:** Small increases in costs or latency flip the strategy from good to useless.

**Why it matters to a layman**  
A car should not only drive well on a clean dry road.  
Stress testing checks whether it still behaves when the road gets wet, rough, or crowded.

**Important nuance**
The coded threshold `worst_score > -10` is a **crash-test threshold**, not a “healthy strategy” threshold.  
A candidate can pass `stress_not_collapsed` and still be too weak for real money.

**Typical red flags**
- Worst scenario objective turns negative
- Drawdown jumps sharply
- Mild stress already damages the result
- Performance depends on unrealistically cheap trading or unrealistically fast execution

**Repo references**
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/objective/stress.py`
- `research_notebooks/market_lab/pmm_dynamic/configs/stress_scenarios.yaml`

---

### 4.5 Recent 28-Day Window

**What it is**  
A warm-started replay of the **most recent 28 calendar days** of the dataset.

**What it is testing for**  
Whether the strategy still works in the most recent market conditions, instead of only in older history.

**How the code evaluates it**
The recent-window gate passes only if all of these hold:
- recent objective score **> 0**
- recent PnL **>= 0**
- recent trade count **>= 5**
- recent max drawdown **<= 50%**
- if recent stress is run, worst recent stress score **>= -10**

**How to evaluate it as a human**
- **Good:** Positive recent score, non-negative recent PnL, enough trades to matter.
- **Bad:** Negative recent PnL or recent objective <= 0.
- **Very bad:** The strategy once worked historically but has clearly stopped working in the latest market regime.

**Why it matters to a layman**  
Markets change. A strategy that worked months ago may now be stale.  
This test asks: “Is it still alive now?”

**Typical red flags**
- Recent objective <= 0
- Recent PnL < 0
- Too few trades to trust
- Recent drawdown is far worse than development history

**Repo references**
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/objective/recent_window.py`

---

### 4.6 Sensitivity Analysis

**What it is**  
A fragility test. The framework slightly perturbs important parameters and checks whether the strategy still works.

**What it is testing for**  
Whether the result depends on a knife-edge setting. Robust strategies should survive small parameter changes.

**How the code evaluates it**
By default, the framework perturbs these parameters by **±10%**:
- `buy_spread_base`
- `sell_spread_base`
- `stop_loss`
- `take_profit`
- `executor_refresh_time`
- `cooldown_time`
- `total_amount_quote`

It then checks:
- **Sign flip:** baseline score positive -> perturbed score negative, or vice versa
- **Collapse:** perturbed score drops by more than **50%** of baseline score magnitude

Penalty formula:
- `sensitivity_penalty = (sign_flips + collapse_count) / valid_perturbations`

Stop-ship rule:
- `sensitivity_stable` passes if penalty **< 0.50**

**How to evaluate it as a human**
- **Good:** Most perturbations leave the score in the same general neighborhood.
- **Bad:** One or two parameters are extremely brittle.
- **Very bad:** Small changes break the strategy repeatedly.

**Why it matters to a layman**  
This is like checking whether a recipe still tastes okay if you use a little more or a little less salt.  
If the whole recipe only works at one exact number, it is fragile.

**Typical red flags**
- High penalty
- Sign flips
- One specific risk-control parameter collapses the score
- Many perturbed configs are rejected

**Repo references**
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/optuna/sensitivity.py`

---

### 4.7 Top-K Clustering

**What it is**  
A check on the optimizer’s best trials to see whether the winners cluster around similar parameter values.

**What it is testing for**  
Whether the optimizer found a stable “good region” or just a scattered set of lucky accidents.

**How the code evaluates it**
- Looks at the top **K = 10** completed trials by default.
- Uses continuous parameters only.
- Computes coefficient of variation (**CV = std / mean**) per parameter.
- A parameter is “clustered” if `CV < 0.50`.
- The overall result is considered clustered if the **mean CV < 0.50**.

**How to evaluate it as a human**
- **Good:** Most important parameters live in a relatively tight region.
- **Bad:** The top trials are all over the map.
- **Mixed:** Overall cluster passes, but a few parameters are scattered; that can still signal weak identifiability.

**Why it matters to a layman**  
If the best 10 winners all look similar, that is encouraging.  
If the best 10 winners all need totally different settings, the edge may be noisy or accidental.

**Typical red flags**
- Mean CV above threshold
- Key spread or risk parameters are scattered
- Timing parameters are highly unstable

**Repo references**
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/optuna/clustering.py`

---

### 4.8 YAML Validation

**What it is**  
A structural validation of the exported PMM Dynamic controller YAML.

**What it is testing for**  
Whether the exported config is syntactically and semantically coherent enough to be used by the downstream controller.

**How the code evaluates it**
The validator checks items such as:
- required keys exist,
- controller name/type are correct,
- spread arrays are present and positive,
- amount percentages are present, positive, and sum correctly,
- list lengths match,
- `macd_fast < macd_slow`,
- stop loss / take profit / time limit are positive,
- trailing-stop structure is valid if present,
- types are correct,
- no NaNs are present.

**How to evaluate it as a human**
- **Good:** Valid with zero errors; warnings are acceptable only if understood.
- **Bad:** Any structural error.
- **Very important:** YAML PASS only means the config is well-formed. It does **not** mean the strategy is good.

**Why it matters to a layman**  
This is like making sure the recipe card is readable and complete before you hand it to the cook.

**Typical red flags**
- Missing required keys
- Bad array lengths
- Invalid MACD ordering
- Amount percentages that do not add up
- Warnings you cannot explain

**Repo references**
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/export/validate_export.py`

---

### 4.9 Frozen Parity and Long Parity

**What they are**  
Feature-parity checks that compare PMM Lab’s feature calculations against frozen expected outputs.

**What they are testing for**  
Whether the research notebook / simulator computes the same indicator and feature values expected by the controller-side logic.

**Why this is a big deal**  
A strategy can look fine in simulation but fail live if the live controller computes signals differently.

**How the code evaluates them**
- Compares feature outputs against frozen fixtures
- Uses tight numeric tolerances
- `frozen_parity` is used as a stop-ship gate
- `long_parity` may be optional if a long fixture is not present

**How to evaluate it as a human**
- **Good:** PASS
- **Bad:** FAIL means live-vs-lab mismatch risk
- **Important nuance:** If the parity test was not run, some stop-ship views may still show it as FAIL because “not validated” is treated conservatively

**Why it matters to a layman**  
This is like checking whether two thermometers read the same temperature.  
If they disagree, your “measured” strategy may not be the one you actually trade.

**Repo references**
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/parity/feature_parity.py`
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/report/report_md.py`

---

### 4.10 Validation Coverage

**What it is**  
A summary table showing which validations passed, failed, or were skipped.

**What it is testing for**  
Nothing new by itself. It is a summary layer.

**How to evaluate it as a human**
- Use it as the quick dashboard.
- If `Validation Coverage` disagrees with a detailed section, inspect the detailed section and stop-ship table.
- Coverage is generally more reliable than the raw execution manifest for pass/fail interpretation.

**Why it matters to a layman**  
It is the “traffic light” page.

---

### 4.11 Validation Execution Manifest

**What it is**  
A ledger showing what validations ran, on which dataset slice, and with what status field.

**What it is testing for**  
Again, not a new test. It is an audit trail.

**How to evaluate it as a human**
- Use it to verify that the intended validation actually ran.
- Use it to confirm dataset slice labels such as `full`, `pre_release_holdout`, or `recent_28d`.
- Treat it as execution evidence, not the final word on semantic pass/fail.

**Current reporting quirk to know**
The manifest uses a generic status mapper that looks for fields like:
- `.passed`
- `.passed_strict`
- `.valid`
- `.is_clustered`

Some validation objects do not expose the “right” field for this generic mapper.  
That means the manifest can show **FAIL** even when the dedicated section and validation coverage say **PASS**.

In practice:
- trust the **dedicated test section** first,
- then the **Stop-Ship Checks**,
- then **Validation Coverage**,
- and treat the manifest as the **execution ledger**.

**Why it matters to a layman**  
It tells you what was run, but not always the best interpretation of the result.

**Repo references**
- `research_notebooks/market_lab/pmm_dynamic/pmm_lab/report/report_md.py`

---

## 5. Stop-Ship Checks dictionary

These are the most important gates in the report.  
Think of them as **minimum deployment safety checks**, not performance badges.

| Stop-Ship Key | Plain-English meaning | Exact coded rule | How to interpret a failure |
|---|---|---|---|
| `dataset_audit` | The input market data was not badly broken | `dataset_audit.passed_strict == True` | Broken or low-quality data can invalidate every downstream result |
| `runtime_sanity` | The simulator actually produced a real trading run | `trade_count >= 5` and `pnl_pct != 0.0` and `total_fees_quote > 0` | The simulation may be inert, degenerate, or not exercising realistic paths |
| `objective_not_degenerate` | The chosen score is a real score, not a hard reject | `raw_score != -1000` and `is_rejected == False` | Usually means too few trades or a fundamentally invalid candidate |
| `stress_not_collapsed` | The worst stress scenario did not crash below the hard threshold | `worst_score > -10.0` | The strategy blows up under adverse conditions; even a PASS here is only a low bar |
| `yaml_validates` | The exported controller YAML is structurally valid | `validation_result.valid == True` | The config may be unusable or unsafe to export |
| `walkforward_robust` | At least half the folds produced non-rejected results | `valid_folds / total_folds >= 0.5` | The strategy may only work in isolated periods |
| `walkforward_positive_majority` | At least half the folds had non-negative PnL | `positive_folds / total_folds >= 0.5` | The strategy may lose in most periods; note that zero-PnL folds still count as non-negative |
| `holdout_passed` | The exported candidate worked on unseen holdout data | `exported_holdout_score > 0` and no exported collapse | Strong sign of overfitting if this fails |
| `holdout_no_collapse` | The exported candidate did not materially degrade on holdout | `exported_holdout_collapse == False` | Dev-to-holdout drop was too large; the edge may not generalize |
| `sensitivity_stable` | Small parameter changes did not break the result too often | `sensitivity_penalty < 0.50` | The candidate may be a knife-edge parameter accident |
| `recent_28d_passed` | The strategy still behaves acceptably in the most recent 28 days | `recent_window_result.passed == True` | The strategy may be stale even if older history looked good |
| `frozen_parity` | Research features match frozen expected controller-side values | `parity_result.passed == True` | Live and research signal generation may not match |
| `top_k_clustered` | The best trials cluster into a stable parameter region | `cluster_report.is_clustered == True` | The optimizer may have found scattered lucky winners instead of a robust region |

### Notes on stop-ship interpretation

- A stop-ship **FAIL** should be treated as a real blocker unless the team explicitly decides the gate is non-binding for that run.
- A stop-ship **PASS** means “not disqualified by this rule,” not “safe for live trading.”
- In the current implementation, **not running** some tests can still surface as a stop-ship failure, especially parity-related checks. That is conservative behavior.

---

## 6. Stress Test Results scenarios dictionary

The report includes named adverse scenarios.  
These are not random labels; each one changes specific simulator assumptions.

### 6.1 Cost and fee stress

| Scenario | What changes in the simulator | Plain-English meaning | What a reviewer should look for |
|---|---|---|---|
| `fees_1.5x` | Maker fee × 1.5, taker fee × 1.5 | Trading is 50% more expensive than expected | A robust strategy should still work if fees are a bit worse than assumed |
| `fees_2x` | Maker fee × 2, taker fee × 2 | Trading costs double | If doubling fees destroys the edge, the strategy may only work on paper-thin margins |

### 6.2 Timing and latency stress

| Scenario | What changes in the simulator | Plain-English meaning | What a reviewer should look for |
|---|---|---|---|
| `latency_plus1` | `latency_bars + 1` | Orders are one candle later than ideal | Mild latency should not totally erase the edge |
| `latency_plus2` | `latency_bars + 2` | Orders are two candles late | Useful when the strategy depends on fast reaction |
| `latency_plus3` | `latency_bars + 3` | Orders are three candles late | A strong drop here means the strategy is very timing-sensitive |

### 6.3 Liquidity, book depth, and fill stress

| Scenario | What changes in the simulator | Plain-English meaning | What a reviewer should look for |
|---|---|---|---|
| `low_liquidity` | Fill participation rate × 0.5 | Only half as much size is realistically fillable | The strategy should still function with smaller achievable fills |
| `very_low_liquidity` | Fill participation rate × 0.25 | Only a quarter of expected fillable size is available | Big damage here suggests dependence on unrealistic liquidity |
| `thin_book` | Maker fill probability forced to 0.3 | Quotes are resting in a thin book and get filled less often | Useful for checking whether the model assumes too much passive fill quality |
| `very_thin_book` | Maker fill probability forced to 0.1 | The order book is extremely thin | If this kills the strategy, live fills may be much worse than backtest fills |

### 6.4 Slippage and spread-cost stress

| Scenario | What changes in the simulator | Plain-English meaning | What a reviewer should look for |
|---|---|---|---|
| `high_slippage` | Slippage × 2 | Exits and adverse fills are twice as costly | A realistic market-making strategy should degrade, but not collapse instantly |
| `extreme_slippage` | Slippage × 4 | Exit costs are much worse than assumed | Heavy damage here suggests the edge is too dependent on optimistic execution |
| `spread_widen_10bps` | Entry spread cost widened by 10 bps | The market becomes a bit wider and less favorable | Useful for adverse selection and spread-regime robustness |
| `spread_widen_25bps` | Entry spread cost widened by 25 bps | The market gets materially wider | Strong damage here means the strategy may be fragile when spreads move out |
| `entry_spread_stress` | Entry spread cost + 15 bps | Each entry is simply more expensive | Good for checking whether the edge disappears under worse quote quality |

### 6.5 Combined adverse conditions

| Scenario | What changes in the simulator | Plain-English meaning | What a reviewer should look for |
|---|---|---|---|
| `combined_adverse` | Fees 1.5×, latency +1, slippage 2×, fill participation 0.5× | A bundle of moderate execution problems | Good for “everyday bad conditions,” not just one issue at a time |
| `combined_market_deterioration` | Spread +10 bps, fill probability 0.5, slippage 2×, fees 1.5× | The market itself becomes less tradable | Useful for checking whether the edge depends on friendly microstructure |
| `severe_adverse` | Spread +25 bps, fill probability 0.2, latency +2, slippage 3×, fees 2× | A hard stress bundle approximating very poor conditions | Usually the main crash-test scenario; if this is catastrophic, the strategy is highly fragile |

### How to judge stress scenarios in plain English

- **Healthy result:** The strategy gets worse, but stays coherent.
- **Weak result:** One or two realistic scenarios push the score close to zero or negative.
- **Bad result:** Mild or moderate stress already causes collapse.
- **Very bad result:** The strategy only works if fees, fills, and timing are unrealistically favorable.

> **Rule of thumb:**  
> The more realistic the stress scenario, the more seriously you should treat a bad result.  
> A strategy that only survives “perfect conditions” is not robust enough for deployment.

---

## 7. Quick reviewer cheat sheet

### If you are non-technical
Use this simplified checklist:

- **Did any stop-ship checks fail?**  
  If yes, do not treat the strategy as deployment-ready.

- **Did holdout fail?**  
  If yes, the strategy may be overfit.

- **Did recent 28-day fail?**  
  If yes, the strategy may no longer work in current conditions.

- **Did stress results fall apart under realistic worsening?**  
  If yes, live trading may be much worse than the backtest.

- **Did sensitivity show fragility?**  
  If yes, the “best” parameters may just be lucky.

### If you are doing a deeper technical review
Prefer this reading order:

1. Stop-Ship Checks
2. Holdout Validation
3. Recent 28-Day Window
4. Stress Test Results
5. Walk-Forward Results
6. Sensitivity Analysis
7. Top-K Clustering
8. YAML Validation
9. Dataset Audit
10. Validation Coverage
11. Validation Execution Manifest

---

## 8. Practical acceptance guidance

### Research only
Use this label when:
- one or more stop-ship checks fail,
- holdout fails,
- recent 28-day fails,
- parity is missing or failed,
- or stress/sensitivity reveal clear fragility.

### Backtesting only
Use this label when:
- the result is structurally valid,
- but out-of-sample or recent-market evidence is still weak.

### Paper-trading candidate
Use this label only when:
- all required stop-ship checks pass,
- holdout and recent-window results are acceptable,
- stress deterioration is understandable,
- sensitivity is stable,
- and YAML/parity are validated.

### Potential live candidate
This report alone is **not enough** for a live green light.  
Even after all stop-ship checks pass, a live candidate still needs:
- connector/exchange compatibility review,
- fee and min-notional realism review,
- paper trading,
- and operational safeguards.

---

## 9. One-page summary

If you remember only five ideas, remember these:

1. **Stop-Ship first.**  
   That is the quickest answer to “Is this blocked?”

2. **Holdout is the final exam.**  
   Good dev results without holdout are not trustworthy.

3. **Recent 28-day is the freshness test.**  
   Old alpha can die.

4. **Stress tests are execution realism tests.**  
   A strategy that only works under perfect fills is not robust.

5. **Sensitivity and clustering tell you whether the optimizer found a real region or a lucky needle.**

---

## 10. Repo reference map

- Stop-ship logic:  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/report/report_md.py`

- Walk-forward logic:  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/objective/walkforward.py`

- Robust aggregate logic:  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/objective/robustness.py`

- Holdout logic:  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/objective/holdout.py`

- Recent 28-day logic:  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/objective/recent_window.py`

- Stress engine and scenario application:  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/objective/stress.py`

- Stress scenario definitions:  
  `research_notebooks/market_lab/pmm_dynamic/configs/stress_scenarios.yaml`

- Sensitivity logic:  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/optuna/sensitivity.py`

- Top-k clustering logic:  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/optuna/clustering.py`

- Dataset audit thresholds:  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/data/candles.py`  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/config/defaults.py`

- YAML validation:  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/export/validate_export.py`

- Feature parity:  
  `research_notebooks/market_lab/pmm_dynamic/pmm_lab/parity/feature_parity.py`
