# PMM Dynamic Optimization Report: mexc_LTC-USDT_5m_sweep_v1

Generated: 2026-03-28 15:42:40 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T15:42:40.040771+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 8436 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: LTC-USDT
- **interval**: 5m
- **n_candles**: 51914
- **dataset_hash**: c7ee1d299bf0f0f31150e6d52a9e577c9d7ff7ec1ff2f1bae066b7124d9c083f
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 124.32141175483109
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.9504871974020812 |
| buy_n_levels | 6 |
| buy_side_weight | 0.4335525337857684 |
| buy_spread_base | 0.2508397337482668 |
| buy_spread_ratio | 1.5654701011021959 |
| cooldown_time | 376 |
| executor_refresh_time | 1072 |
| macd_fast | 43 |
| macd_signal | 5 |
| macd_slow | 100 |
| natr_length | 24 |
| sell_n_levels | 7 |
| sell_spread_base | 0.22509543387163225 |
| sell_spread_ratio | 1.8139634402299885 |
| stop_loss | 0.1796370818976396 |
| take_profit | 0.027345025825701006 |
| time_limit | 166159 |
| total_amount_quote | 124.32141175483109 |
| trailing_stop_activation | 0.01737351922362884 |
| trailing_stop_delta | 0.001859265110895975 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 124.32141175483109 |
| Selected | 124.32141175483109 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2531.3921
- **Net PnL (quote)**: 3147.0625
- **Sharpe Ratio**: 10.1344
- **Max Drawdown %**: 27.2610
- **Profit Factor**: 1.90242662141224
- **Trade Count**: 21140
- **Total Fees (quote)**: 166.6036
- **Maker Fees**: 84.3166
- **Taker Fees**: 82.2871
- **Fee Drag %**: 134.0104

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.1408
- **PnL Component**: 3.2701
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.2045
- **Fee Drag Component**: -0.6701
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.7767**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 328.11 | 36.10 | 6.42 | 2123 | 1.0870 | n/a |
| 1 | 170.36 | 35.93 | 8.91 | 2165 | 0.6117 | n/a |
| 2 | 316.09 | 37.87 | 5.14 | 2119 | 1.0719 | n/a |
| 3 | 124.12 | 47.77 | 3.86 | 2193 | 0.4630 | n/a |
| 4 | 245.61 | 44.77 | 5.89 | 2142 | 0.8801 | n/a |
| 5 | 328.84 | 40.77 | 10.15 | 2040 | 1.0633 | n/a |
| 6 | 271.27 | 12.08 | 9.32 | 2081 | 0.9246 | n/a |
| 7 | 172.07 | 41.13 | 4.20 | 1920 | 0.6583 | n/a |
| 8 | 111.19 | 41.11 | 5.55 | 2017 | 0.3962 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.0684)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2521.32 | 9.42 | 33.34 | 1.7553 |
| fees_2x | 2439.03 | 9.86 | 27.48 | 1.4435 |
| latency_plus1 | 2212.30 | 10.50 | 18.63 | 2.1548 |
| latency_plus2 | 1839.20 | 8.90 | 27.39 | 1.9916 |
| latency_plus3 | 1460.84 | 8.07 | 24.74 | 1.8777 |
| low_liquidity | 2531.39 | 10.13 | 27.26 | 2.1408 |
| very_low_liquidity | 2528.94 | 10.13 | 27.26 | 2.1406 |
| high_slippage | 2444.15 | 9.13 | 33.42 | 2.0678 |
| extreme_slippage | 2270.83 | 9.08 | 30.91 | 2.0214 |
| combined_adverse | 2094.24 | 10.51 | 16.04 | 1.8325 |
| spread_widen_10bps | 2493.54 | 9.57 | 28.81 | 2.1183 |
| spread_widen_25bps | 2328.18 | 9.37 | 28.02 | 2.0637 |
| thin_book | 1594.52 | 7.46 | 45.24 | 1.8490 |
| very_thin_book | 704.81 | 5.96 | 42.70 | 1.3236 |
| entry_spread_stress | 2412.57 | 9.88 | 20.72 | 2.1541 |
| combined_market_deterioration | 1884.19 | 8.00 | 37.91 | 1.7186 |
| severe_adverse | 663.18 | 5.46 | 38.96 | 1.0684 |

## Holdout Validation

- **Holdout bars**: 8778
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0032)
- **Trend**: ranging (efficiency: 0.0202)
- **Best holdout score**: 1.5854 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.6046 | 1.3128 | 506.80 | 12.33 | 4657 |
| 1 | 1.1141 | 1.5416 | 758.36 | 16.53 | 5551 |
| 2 | 1.0917 | 1.5150 | 708.54 | 16.87 | 2255 |
| 3 | 1.0778 | 1.5854 | 774.50 | 18.10 | 4646 |
| 4 | 1.0632 | 1.5091 | 688.30 | 12.08 | 4477 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51914
- **Expected rows**: 51957
- **Missing rows**: 43
- **Forward-fill count**: 8
- **Forward-fill fraction**: 0.00015410101321416188
- **Longest gap (seconds)**: 13200

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.8148361098485685
- **PnL %**: 240.6803089588344
- **Trade count**: 4113

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.7978774194271812
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.7763, 1.7341 |
| sell_spread_base | 1.8319, 1.7856 |
| stop_loss | 1.7851, 1.6610 |
| take_profit | 1.7954, 1.8010 |
| executor_refresh_time | 1.7979, 1.7979 |
| cooldown_time | 1.7979, 1.7979 |
| total_amount_quote | 1.7658, 1.7629 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.42154337101716555
- **Max CV**: 1.227676193210484
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time
- **Scattered params**: take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2633 | 0.20606552569526768 | 0.45214933088598974 | 0.2695804007602753 |
| buy_spread_ratio | 0.2190 | 1.407359749331065 | 2.6669997449169163 | 1.9574749484104665 |
| sell_spread_base | 0.2885 | 0.2078869610532279 | 0.5271603073152598 | 0.3461700734653479 |
| sell_spread_ratio | 0.2520 | 1.2079972940991988 | 2.4586473780570652 | 1.7832249769937618 |
| buy_side_weight | 0.2276 | 0.27381965692826427 | 0.5933148488693664 | 0.4586715902292625 |
| amount_skew | 0.2224 | 1.6750476788097732 | 3.870603485518818 | 2.8970968161236224 |
| stop_loss | 0.4171 | 0.07493022639763272 | 0.22316275190345364 | 0.12571682001451795 |
| take_profit | 0.6545 | 0.01784926667071017 | 0.08849012255424783 | 0.03819539828730611 |
| executor_refresh_time | 0.3068 | 332.0 | 816.0 | 495.2 |
| cooldown_time | 0.5580 | 84.0 | 518.0 | 219.7 |
| total_amount_quote | 1.2277 | 26.418950282059413 | 462.27943043161383 | 107.2766590949997 |

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
| recent_objective | > 0 | 0.8148361098485685 | PASS |
| recent_pnl | >= 0 | 240.6803089588344 | PASS |
| recent_trades | >= 5 | 4113 | PASS |
| worst_stress | > -10 | 1.0683791387728112 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.3128 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.0683791387728112 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.8148361098485685, pnl=240.6803089588344, trades=4113, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.42154337101716555 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51914 |  |
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
- **Dev bars**: 35114
- **Holdout bars**: 8778
- **Recent 28d bars**: 8022

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T15:42:40.040771+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 8436
