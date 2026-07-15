# Robust ladder notebook upgrade report

## Files created

- `ladder_lab_robust.py`
- `NONKYC_Crypto_oscillator_finder_v5_robust_60x15.ipynb`
- `KRAKEN_Crypto_oscillator_finder_v4_robust_60x15.ipynb`

These files are designed to sit in the same folder as the existing `ladder_lab.py`. The new module imports and reuses the existing exchange adapters, candle cache, screener, simulator, fill-stress logic, min-quantity checks, hourly realism checks, and output helpers. The original notebooks and `ladder_lab.py` are not overwritten.

## Main design changes

### 1. Generative rung placement

The optimizer now generates candidate ladder shapes instead of optimizing only one fixed rung count. Candidate families are:

1. **Percent-distance ladders**: buy/sell rungs are placed by percentage distance from the train-window anchor.
2. **Volatility-scaled ladders**: inner and outer distances are based on the train-window true-range / return-volatility estimate.
3. **Quantile ladders**: inner and outer rung distances are derived from the train-window high/low deviation quantiles.

All candidates are created from training data only. No test-window data is used to choose anchor, band width, spacing, rung count, or weights.

### 2. Rung-count optimization

The default search space is:

```python
gen_n_buy_range  = (4, 12)
gen_n_sell_range = (4, 12)
hard_max_active_orders = 24
preferred_max_rungs_per_side = 10
```

This lets the data choose fewer or more rungs while softly favoring your desired 8–10 rung-per-side region. The `hard_max_active_orders` cap prevents the optimizer from creating a ladder that is operationally too dense.

### 3. Frequent-small-trade preference

The score rewards activity only up to a target and penalizes concentrated or one-sided behavior:

```python
target_trades_per_15d = 8
max_single_rung_weight_pct = 18.0
```

The optimizer avoids giant 30%–45% single-rung weights by flattening candidate weights and by capping optimized shape weights.

### 4. Rolling 60-day train / 15-day holdout validation

The main validation loop is:

```text
previous 60 days: generate + select ladder
next 15 days: freeze ladder and test out-of-sample
step forward 15 days
repeat
```

With roughly 180 days of data, this produces up to eight true out-of-sample 15-day folds:

```text
Days 1-60    train -> Days 61-75    test
Days 16-75   train -> Days 76-90    test
Days 31-90   train -> Days 91-105   test
Days 46-105  train -> Days 106-120  test
Days 61-120  train -> Days 121-135  test
Days 76-135  train -> Days 136-150  test
Days 91-150  train -> Days 151-165  test
Days 106-165 train -> Days 166-180  test
```

### 5. 45-day and 60-day block summaries

The same 15-day OOS folds are aggregated two ways:

- **45-day pseudo-quarter blocks**: 3 consecutive 15-day holdouts.
- **60-day robustness blocks**: 4 consecutive 15-day holdouts.

This handles the data-length constraint honestly. Four clean 45-day quarters plus a prior 60-day training window would require more than 180 days, but the new notebooks still let you inspect stability across quarter-like blocks.

### 6. Robust objective

For each candidate, the per-window score is approximately:

```text
score =
    net_return
  - drawdown_penalty
  - downside_move_penalty
  - inventory_imbalance_penalty
  - buy/sell_fill_imbalance_penalty
  - low_trade_count_penalty
  - conservative_fill_degradation_penalty
  - excessive_rung_count_penalty
  + trade_frequency_bonus
  + rung_usage_bonus
```

Across folds, the market-level robust score is:

```text
robust_score = 25th_percentile(test_scores)
             - score_std_penalty * std(test_scores)
             - parameter_instability_penalty
```

This intentionally favors ladders that work reasonably well across many unseen windows instead of ladders that win one lucky period.

### 7. Conservative fill assumptions

The robust folds use the same simulator as the final deploy checks. Conservative stress includes:

```python
max_fills_per_bar = 1
rearm_cooldown = 1
slip_floor = 0.001
body_only = False
```

Finalization uses measured order-book spread where available:

```text
slip = max(slip_floor, measured_spread / 2)
```

### 8. Deployment output contract

The final JSON emits:

```json
{
  "symbol": "BASE/QUOTE",
  "trading_pair": "BASE-QUOTE",
  "exchange": "nonkyc or kraken",
  "passive_order_placement": true,
  "max_fund_value_quote": 1000,
  "total_amount_quote": 1000,
  "buy_prices": [ ... floats ... ],
  "sell_prices": [ ... floats ... ],
  "buy_amounts_pct": [ ... floats summing to about 100 ... ],
  "sell_amounts_pct": [ ... floats summing to about 100 ... ],
  "validation": "CONFIRMED | GATED | SUSPECT",
  "gates": [ ... ]
}
```

The notebooks print this contract and save it to JSON.

## Output files produced when notebooks are run

For NonKYC:

- `NONKYC_robust_60x15_v5_final_summary.csv`
- `NONKYC_robust_60x15_v5_walkforward_summary.csv`
- `NONKYC_robust_60x15_v5_fold_details.csv`
- `NONKYC_robust_60x15_v5_45d_blocks.csv`
- `NONKYC_robust_60x15_v5_60d_blocks.csv`
- `NONKYC_robust_60x15_v5_deploy_config.json`

For Kraken:

- `KRAKEN_robust_60x15_v4_final_summary.csv`
- `KRAKEN_robust_60x15_v4_walkforward_summary.csv`
- `KRAKEN_robust_60x15_v4_fold_details.csv`
- `KRAKEN_robust_60x15_v4_45d_blocks.csv`
- `KRAKEN_robust_60x15_v4_60d_blocks.csv`
- `KRAKEN_robust_60x15_v4_deploy_config.json`

## How to run quickly

Set an environment variable before launching Jupyter:

```bash
export LADDER_QUICK_TEST=12
```

Or edit the bootstrap cell:

```python
QUICK_TEST = 12
```

Quick mode reduces the scanned universe and candidate count. Use full mode before trusting any result.

## Suggested acceptance criteria before deployment

A generated ladder should be treated as deployable only when all of the following are true:

1. `validation == "CONFIRMED"`.
2. Robust walk-forward passed with at least the configured minimum fold count.
3. Positive OOS fold rate is at least 62.5% by default.
4. Two-sided OOS fold rate is at least 62.5% by default.
5. Median conservative OOS result is not worse than the configured floor.
6. Worst OOS fold is not beyond the configured max loss threshold.
7. Final deploy gates are empty.
8. Hourly fill ratio is not materially below the daily-bar sim.
9. The result is not dependent on a single lucky fold or a single deep rung.
10. Live/paper fills reconcile against expected fees, spread, slippage, and inventory behavior before scaling.

## Stop-ship conditions

Do not trust or deploy the generated parameters if any of these are present:

- `validation == "SUSPECT"`.
- Gate includes thin book, min-quantity failure, proxy/native divergence, or weak conservative deploy sim.
- Most OOS folds are one-sided.
- A high score comes from very few trades.
- The final ladder has large single-rung allocations despite the cap.
- Conservative stress flips a profitable result into an unacceptable loss.
- Hourly bars show far fewer fills than daily bars.
- The selected rung count or inner/outer distances are highly unstable across folds.
- The live exchange does not match the assumed maker/passive execution behavior.
