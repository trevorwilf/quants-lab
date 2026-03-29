# PMM Dynamic Optimization Report: mexc_ETH-USDT_5m_sweep_v1

Generated: 2026-03-28 12:43:16 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T12:43:16.156012+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 11451 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ETH-USDT
- **interval**: 5m
- **n_candles**: 51913
- **dataset_hash**: ef5a5e5beb16d7ce782dc2937c14fe55ea780fdac9a58602f60dca0a4363176e
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 245.32772681379095
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.814052534465738 |
| buy_n_levels | 10 |
| buy_side_weight | 0.40540372579862144 |
| buy_spread_base | 0.2145849103550443 |
| buy_spread_ratio | 1.3394228650750615 |
| cooldown_time | 444 |
| executor_refresh_time | 1007 |
| macd_fast | 8 |
| macd_signal | 23 |
| macd_slow | 21 |
| natr_length | 28 |
| sell_n_levels | 2 |
| sell_spread_base | 0.2954951529960825 |
| sell_spread_ratio | 2.1520338707272377 |
| stop_loss | 0.1706141156951959 |
| take_profit | 0.05142916697554174 |
| time_limit | 152814 |
| total_amount_quote | 245.32772681379095 |
| trailing_stop_activation | 0.009664492860669706 |
| trailing_stop_delta | 0.0013998124732475642 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 245.32772681379095 |
| Selected | 245.32772681379095 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2335.5943
- **Net PnL (quote)**: 5729.8603
- **Sharpe Ratio**: 14.6419
- **Max Drawdown %**: 16.2917
- **Profit Factor**: 2.13235341075569
- **Trade Count**: 16865
- **Total Fees (quote)**: 342.5229
- **Maker Fees**: 173.0203
- **Taker Fees**: 169.5026
- **Fee Drag %**: 139.6185

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.1183
- **PnL Component**: 3.1928
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1222
- **Fee Drag Component**: -0.6981
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.7478**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 325.14 | 39.66 | 8.44 | 1794 | 1.0610 | n/a |
| 1 | 323.79 | 27.29 | 6.10 | 1656 | 1.0822 | n/a |
| 2 | 342.99 | 34.88 | 7.16 | 1922 | 1.1086 | n/a |
| 3 | 132.87 | 38.27 | 2.62 | 1873 | 0.5088 | n/a |
| 4 | 140.85 | 28.60 | 3.00 | 1654 | 0.5415 | n/a |
| 5 | 205.42 | 32.89 | 9.85 | 1766 | 0.7216 | n/a |
| 6 | 246.25 | 31.38 | 9.19 | 1761 | 0.8522 | n/a |
| 7 | 246.83 | 39.63 | 5.48 | 1840 | 0.8809 | n/a |
| 8 | 169.22 | 41.03 | 3.89 | 1788 | 0.6439 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.0737)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2348.80 | 14.58 | 16.59 | 1.7800 |
| fees_2x | 2317.75 | 14.53 | 16.69 | 1.4221 |
| latency_plus1 | 2055.57 | 13.95 | 17.17 | 2.0862 |
| latency_plus2 | 1684.93 | 13.06 | 16.47 | 2.0032 |
| latency_plus3 | 1378.93 | 12.18 | 16.36 | 1.8870 |
| low_liquidity | 2335.59 | 14.64 | 16.29 | 2.1183 |
| very_low_liquidity | 2335.59 | 14.64 | 16.29 | 2.1183 |
| high_slippage | 2271.03 | 14.51 | 16.68 | 2.0967 |
| extreme_slippage | 2063.88 | 13.92 | 16.76 | 2.0133 |
| combined_adverse | 1943.14 | 13.52 | 17.17 | 1.7367 |
| spread_widen_10bps | 2231.52 | 14.27 | 16.08 | 2.0868 |
| spread_widen_25bps | 2184.69 | 14.08 | 15.67 | 2.0707 |
| thin_book | 1411.40 | 12.43 | 16.54 | 1.9307 |
| very_thin_book | 677.31 | 9.52 | 17.45 | 1.4762 |
| entry_spread_stress | 2196.06 | 14.22 | 15.70 | 2.0708 |
| combined_market_deterioration | 1704.49 | 12.74 | 16.86 | 1.7355 |
| severe_adverse | 544.00 | 8.20 | 17.48 | 1.0737 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0036)
- **Trend**: ranging (efficiency: 0.0346)
- **Best holdout score**: 1.6427 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.5960 | 1.3265 | 517.68 | 11.52 | 3950 |
| 1 | 1.2275 | 1.6427 | 799.39 | 10.00 | 3163 |
| 2 | 1.2151 | 1.6214 | 787.92 | 12.70 | 2541 |
| 3 | 1.2122 | 1.6149 | 767.80 | 10.10 | 4961 |
| 4 | 1.1922 | 1.6189 | 805.97 | 11.98 | 5051 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51913
- **Expected rows**: 51913
- **Missing rows**: 0
- **Forward-fill count**: 87
- **Forward-fill fraction**: 0.0016758808005701848
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.3369563637125208
- **PnL %**: 494.00055578236174
- **Trade count**: 3557

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.7256561930226781
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.7441, 1.7455 |
| sell_spread_base | 1.7465, 1.7288 |
| stop_loss | 1.7443, 1.7254 |
| take_profit | 1.7257, 1.7257 |
| executor_refresh_time | 1.7257, 1.7257 |
| cooldown_time | 1.7257, 1.7257 |
| total_amount_quote | 1.7128, 1.7153 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4088125594239095
- **Max CV**: 1.737553688740286
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time
- **Scattered params**: cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2034 | 0.20884755452296822 | 0.35261198689343753 | 0.27869025704814226 |
| buy_spread_ratio | 0.1288 | 1.2129657848675923 | 1.7817035302463196 | 1.4586130276522256 |
| sell_spread_base | 0.3775 | 0.20315885370707354 | 0.5444979651120482 | 0.29345626413875875 |
| sell_spread_ratio | 0.1765 | 1.6934901690584678 | 2.737688900555817 | 2.2698443717089782 |
| buy_side_weight | 0.2819 | 0.3082872808177078 | 0.6759312790934049 | 0.4405474688365083 |
| amount_skew | 0.0804 | 3.1033854465495136 | 3.936328906993908 | 3.617741829607522 |
| stop_loss | 0.2639 | 0.08617139356354638 | 0.22301196723767328 | 0.16649593268916957 |
| take_profit | 0.3396 | 0.03868141673368438 | 0.11426363531098431 | 0.07006444426436806 |
| executor_refresh_time | 0.3538 | 300.0 | 832.0 | 497.9 |
| cooldown_time | 0.5535 | 79.0 | 452.0 | 202.0 |
| total_amount_quote | 1.7376 | 25.2726926576062 | 940.1310894283216 | 161.07680125082504 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: PASS
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
- holdout_passed: PASS
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 1.3369563637125208 | PASS |
| recent_pnl | >= 0 | 494.00055578236174 | PASS |
| recent_trades | >= 5 | 3557 | PASS |
| worst_stress | > -10 | 1.0736799004860447 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.3265 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.0736799004860447 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.3369563637125208, pnl=494.00055578236174, trades=3557, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4088125594239095 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51913 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35079
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T12:43:16.156012+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 11451
