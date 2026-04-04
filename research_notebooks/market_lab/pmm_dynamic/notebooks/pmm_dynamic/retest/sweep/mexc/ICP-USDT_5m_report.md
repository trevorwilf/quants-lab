# PMM Dynamic Optimization Report: mexc_ICP-USDT_5m_retest_20260403

Generated: 2026-04-04 03:02:41 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-04T03:02:41.785996+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 10953 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ICP-USDT
- **interval**: 5m
- **n_candles**: 51869
- **dataset_hash**: bcdb3f4b1bc0e8d40690caff9832f7dc8fdc14eba33587d5713f61f5baa8664c
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 99.97934417239942
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.9935854242147846 |
| buy_n_levels | 10 |
| buy_side_weight | 0.3494492529582641 |
| buy_spread_base | 0.20272350752115792 |
| buy_spread_ratio | 2.0325568995278727 |
| cooldown_time | 160 |
| executor_refresh_time | 1046 |
| macd_fast | 15 |
| macd_signal | 30 |
| macd_slow | 41 |
| natr_length | 25 |
| sell_n_levels | 8 |
| sell_spread_base | 0.20656776795712498 |
| sell_spread_ratio | 1.3403060350914628 |
| stop_loss | 0.18927587614581365 |
| take_profit | 0.05156018480611654 |
| time_limit | 141806 |
| total_amount_quote | 99.97934417239942 |
| trailing_stop_activation | 0.03464995252664652 |
| trailing_stop_delta | 0.002302699486796987 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 99.97934417239942 |
| Selected | 99.97934417239942 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3485.3211
- **Net PnL (quote)**: 3484.6012
- **Sharpe Ratio**: 6.3033
- **Max Drawdown %**: 31.2719
- **Profit Factor**: 1.4939096180365516
- **Trade Count**: 16923
- **Total Fees (quote)**: 161.8836
- **Maker Fees**: 81.9196
- **Taker Fees**: 79.9640
- **Fee Drag %**: 161.9170

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.2759
- **PnL Component**: 3.5794
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.2345
- **Fee Drag Component**: -0.8096
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **1.0481**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 363.67 | 33.44 | 8.78 | 1858 | 1.1343 | n/a |
| 1 | 426.00 | 51.82 | 5.93 | 1542 | 1.2975 | n/a |
| 2 | 182.44 | 35.31 | 9.28 | 1494 | 0.6546 | n/a |
| 3 | 339.95 | 38.04 | 4.49 | 1459 | 1.1342 | n/a |
| 4 | 497.52 | 38.94 | 7.28 | 1693 | 1.4053 | n/a |
| 5 | 401.22 | 30.01 | 12.95 | 1637 | 1.1897 | n/a |
| 6 | 63.66 | 19.67 | 6.08 | 1176 | 0.1436 | n/a |
| 7 | 271.51 | 45.31 | 5.06 | 1398 | 0.9620 | n/a |
| 8 | 187.49 | 6.74 | 5.31 | 1428 | 0.7019 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.2513)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3431.15 | 6.05 | 31.80 | 1.8556 |
| fees_2x | 3348.91 | 6.22 | 31.88 | 1.4325 |
| latency_plus1 | 2968.47 | 5.82 | 33.37 | 2.1933 |
| latency_plus2 | 2553.33 | 5.58 | 33.41 | 2.1465 |
| latency_plus3 | 1952.15 | 6.02 | 32.00 | 2.0264 |
| low_liquidity | 3430.36 | 6.56 | 32.40 | 2.2685 |
| very_low_liquidity | 3507.07 | 6.05 | 32.88 | 2.2892 |
| high_slippage | 3318.34 | 6.20 | 32.37 | 2.2253 |
| extreme_slippage | 3151.30 | 5.64 | 31.74 | 2.1884 |
| combined_adverse | 2949.83 | 5.96 | 34.46 | 1.8357 |
| spread_widen_10bps | 3364.65 | 5.91 | 31.29 | 2.2417 |
| spread_widen_25bps | 3212.24 | 5.01 | 32.05 | 2.1999 |
| thin_book | 2103.53 | 4.84 | 40.97 | 2.0599 |
| very_thin_book | 927.49 | 5.33 | 38.79 | 1.5716 |
| entry_spread_stress | 3239.85 | 5.66 | 31.36 | 2.2149 |
| combined_market_deterioration | 2652.55 | 5.17 | 34.68 | 1.8631 |
| severe_adverse | 835.87 | 4.94 | 40.65 | 1.2513 |

## Holdout Validation

- **Holdout bars**: 8763
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0043)
- **Trend**: ranging (efficiency: 0.0045)
- **Best holdout score**: 1.6685 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.7636 | 1.3516 | 502.89 | 7.48 | 3029 |
| 1 | 1.3457 | 1.6685 | 757.09 | 8.58 | 4327 |
| 2 | 1.3190 | 1.2854 | 505.02 | 12.14 | 3708 |
| 3 | 1.3052 | 1.6606 | 765.04 | 9.59 | 3087 |
| 4 | 1.2957 | 1.4188 | 577.21 | 11.13 | 5936 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51869
- **Expected rows**: 51884
- **Missing rows**: 15
- **Forward-fill count**: 110
- **Forward-fill fraction**: 0.0021207272166419247
- **Longest gap (seconds)**: 4500

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.0428881630689795
- **PnL %**: 330.7177220986298
- **Trade count**: 2590

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.9481666913533902
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.9462, 1.9293 |
| sell_spread_base | 1.9422, 1.9370 |
| stop_loss | 1.9422, 1.9245 |
| take_profit | 1.9482, 1.9408 |
| executor_refresh_time | 1.9482, 1.9482 |
| cooldown_time | 1.9482, 1.9482 |
| total_amount_quote | 1.9537, 1.9449 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.30603887927507095
- **Max CV**: 0.6752220817103172
- **Clustered params**: buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time
- **Scattered params**: buy_spread_base, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.5801 | 0.20278470603221732 | 0.8086916430410961 | 0.3085246116815973 |
| buy_spread_ratio | 0.1513 | 1.2260323921984309 | 1.8253926475690998 | 1.453423247745326 |
| sell_spread_base | 0.2313 | 0.2019789265914938 | 0.42611274168078994 | 0.27145291886388057 |
| sell_spread_ratio | 0.1147 | 1.2203380158702308 | 1.6436439494673643 | 1.4157996919895255 |
| buy_side_weight | 0.1158 | 0.3233620740818496 | 0.510895870925107 | 0.42875569982918094 |
| amount_skew | 0.3323 | 1.5105686724344147 | 3.902170361047657 | 2.7355804890504514 |
| stop_loss | 0.2923 | 0.09645933363195607 | 0.24854294432403923 | 0.17183009757306386 |
| take_profit | 0.3861 | 0.03501913598287528 | 0.09806039822136699 | 0.06518864808429806 |
| executor_refresh_time | 0.2582 | 334.0 | 711.0 | 491.8 |
| cooldown_time | 0.2291 | 110.0 | 257.0 | 193.4 |
| total_amount_quote | 0.6752 | 34.67189451916698 | 211.28594301756056 | 90.93786526108092 |

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
| recent_objective | > 0 | 1.0428881630689795 | PASS |
| recent_pnl | >= 0 | 330.7177220986298 | PASS |
| recent_trades | >= 5 | 2590 | PASS |
| worst_stress | > -10 | 1.2512909997217911 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.3516 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.2512909997217911 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.0428881630689795, pnl=330.7177220986298, trades=2590, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.30603887927507095 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51869 |  |
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
- **Dev bars**: 35056
- **Holdout bars**: 8763
- **Recent 28d bars**: 8050

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-04T03:02:41.785996+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 10953
