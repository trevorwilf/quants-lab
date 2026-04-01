# PMM Dynamic Optimization Report: nonkyc_SAL-USDT_5m_sweep_v1

Generated: 2026-03-29 11:57:49 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T11:57:49.113044+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 7871 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: SAL-USDT
- **interval**: 5m
- **n_candles**: 51921
- **dataset_hash**: 086e79a8f773457e364bdbeba2776b708f5db3e275d4763f9eb6023379580118
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 548.528836638457
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.6270589024713247 |
| buy_n_levels | 8 |
| buy_side_weight | 0.3468414339542659 |
| buy_spread_base | 4.902114376781748 |
| buy_spread_ratio | 1.389901655039307 |
| cooldown_time | 1354 |
| executor_refresh_time | 2033 |
| macd_fast | 42 |
| macd_signal | 14 |
| macd_slow | 85 |
| natr_length | 40 |
| sell_n_levels | 8 |
| sell_spread_base | 1.8616941374643738 |
| sell_spread_ratio | 1.3408149921953483 |
| stop_loss | 0.22587659699491472 |
| take_profit | 0.08793098061512845 |
| time_limit | 102589 |
| total_amount_quote | 548.528836638457 |
| trailing_stop_activation | 0.039115308382408794 |
| trailing_stop_delta | 0.0031688516589981697 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 548.528836638457 |
| Selected | 548.528836638457 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 87.2580
- **Net PnL (quote)**: 478.6353
- **Sharpe Ratio**: 3.1825
- **Max Drawdown %**: 19.5513
- **Profit Factor**: 1.6135341916108656
- **Trade Count**: 3908
- **Total Fees (quote)**: 111.1209
- **Maker Fees**: 37.1938
- **Taker Fees**: 73.9271
- **Fee Drag %**: 20.2580

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.2932
- **PnL Component**: 0.6273
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1466
- **Fee Drag Component**: -0.1013
- **Inventory Component**: -0.0832
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0123**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 7.40 | 8.99 | 1.68 | 250 | 0.0047 | n/a |
| 1 | 7.05 | 8.17 | 1.03 | 89 | 0.0227 | n/a |
| 2 | 7.99 | 5.29 | 8.43 | 117 | -0.0234 | n/a |
| 3 | 10.30 | 12.72 | 1.07 | 180 | 0.0514 | n/a |
| 4 | -11.09 | -6.06 | 11.95 | 206 | -0.3413 | n/a |
| 5 | 5.89 | 9.31 | 1.23 | 114 | 0.0215 | n/a |
| 6 | 21.18 | 10.31 | 2.67 | 330 | 0.0861 | n/a |
| 7 | 1.04 | 1.03 | 5.90 | 249 | -0.1278 | n/a |
| 8 | 3.00 | 4.04 | 1.71 | 150 | -0.0292 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1590)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 77.13 | 2.89 | 19.76 | 0.1849 |
| fees_2x | 67.00 | 2.60 | 19.98 | 0.0715 |
| latency_plus1 | 91.05 | 3.24 | 19.54 | 0.3126 |
| latency_plus2 | 86.45 | 2.95 | 20.82 | 0.2736 |
| latency_plus3 | 76.69 | 2.73 | 19.31 | 0.2211 |
| low_liquidity | 51.84 | 2.69 | 15.30 | 0.1591 |
| very_low_liquidity | 29.26 | 1.86 | 14.09 | 0.0349 |
| high_slippage | 83.89 | 3.09 | 19.62 | 0.2744 |
| extreme_slippage | 77.14 | 2.90 | 19.74 | 0.2357 |
| combined_adverse | 40.03 | 2.14 | 16.89 | 0.0260 |
| spread_widen_10bps | 82.11 | 3.00 | 19.61 | 0.2599 |
| spread_widen_25bps | 71.03 | 2.73 | 19.69 | 0.2016 |
| thin_book | 36.61 | 1.99 | 18.58 | 0.0388 |
| very_thin_book | 11.31 | 2.36 | 3.99 | 0.0411 |
| entry_spread_stress | 77.48 | 2.91 | 19.63 | 0.2389 |
| combined_market_deterioration | 56.53 | 2.49 | 17.74 | 0.0995 |
| severe_adverse | 5.51 | 0.70 | 13.42 | -0.1590 |

## Holdout Validation

- **Holdout bars**: 8771
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0084)
- **Trend**: ranging (efficiency: 0.0031)
- **Best holdout score**: 0.0546 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0671 | 0.0135 | 19.47 | 7.48 | 656 |
| 1 | 0.0229 | -0.3901 | 3.97 | 30.33 | 1168 |
| 2 | 0.0185 | -0.2212 | 8.91 | 21.51 | 701 |
| 3 | 0.0179 | 0.0546 | 21.18 | 7.05 | 870 |
| 4 | 0.0154 | -0.2600 | 0.72 | 17.51 | 1083 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51921
- **Expected rows**: 51922
- **Missing rows**: 1
- **Forward-fill count**: 1026
- **Forward-fill fraction**: 0.019760790431617263
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1260 <= 0
- **Objective score**: -0.12604047665858029
- **PnL %**: 4.938410630040799
- **Trade count**: 417

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.37500335446348454
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.2794, 0.3485 |
| sell_spread_base | 0.4150, 0.2733 |
| stop_loss | 0.3840, 0.2766 |
| take_profit | 0.3750, 0.3750 |
| executor_refresh_time | 0.3398, 0.3750 |
| cooldown_time | 0.3750, 0.3750 |
| total_amount_quote | 0.3465, 0.2323 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3627615654897621
- **Max CV**: 1.0345054659416755
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, total_amount_quote
- **Scattered params**: sell_spread_base, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0728 | 4.5621058977927404 | 5.9845680392110525 | 5.3284914863255946 |
| buy_spread_ratio | 0.0634 | 1.2311316564868924 | 1.4887312490437319 | 1.3393138889242042 |
| sell_spread_base | 1.0345 | 0.21426531686711542 | 2.122301762185061 | 0.5944977706441416 |
| sell_spread_ratio | 0.1790 | 1.240103273552149 | 1.9831281185946197 | 1.4892304203738735 |
| buy_side_weight | 0.2781 | 0.21400221208440146 | 0.49994020170782055 | 0.3227136019274909 |
| amount_skew | 0.1447 | 2.504691968720723 | 3.9324022122541837 | 3.343612648099236 |
| stop_loss | 0.2655 | 0.11854494588877554 | 0.24843608726186395 | 0.18106737107488677 |
| take_profit | 0.3826 | 0.0378118522056899 | 0.13711177825183019 | 0.09187371805869313 |
| executor_refresh_time | 0.6559 | 343.0 | 4486.0 | 2247.6 |
| cooldown_time | 0.6937 | 397.0 | 4639.0 | 1721.3 |
| total_amount_quote | 0.2203 | 370.52753260130476 | 727.4370137218589 | 562.7998810800332 |

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
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.12604047665858029 | FAIL |
| recent_pnl | >= 0 | 4.938410630040799 | PASS |
| recent_trades | >= 5 | 417 | PASS |
| worst_stress | > -10 | -0.1590480987631521 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=0.013520536972102676 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.1590480987631521 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.12604047665858029, pnl=4.938410630040799, trades=417, reason=recent objective score -0.1260 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3627615654897621 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51921 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1260 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35086
- **Holdout bars**: 8771
- **Recent 28d bars**: 8064

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T11:57:49.113044+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 7871
