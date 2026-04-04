# PMM Dynamic Optimization Report: nonkyc_ARRR-USDT_5m_retest_20260403

Generated: 2026-04-04 06:02:14 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-04T06:02:14.012645+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 3426 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-USDT
- **interval**: 5m
- **n_candles**: 51860
- **dataset_hash**: 882dbb893ba80b25856c9b0d62f39afad234a903579478103e2bd8a9375b6f77
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 122.66160156074345
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.472681216774002 |
| buy_n_levels | 5 |
| buy_side_weight | 0.3360201915541959 |
| buy_spread_base | 0.3360230569281189 |
| buy_spread_ratio | 1.2188748618269736 |
| cooldown_time | 1170 |
| executor_refresh_time | 1870 |
| macd_fast | 28 |
| macd_signal | 30 |
| macd_slow | 30 |
| natr_length | 48 |
| sell_n_levels | 9 |
| sell_spread_base | 0.22113214244647023 |
| sell_spread_ratio | 1.2082628129428532 |
| stop_loss | 0.226685119020283 |
| take_profit | 0.08385439858393325 |
| time_limit | 171332 |
| total_amount_quote | 122.66160156074345 |
| trailing_stop_activation | 0.061021122424415715 |
| trailing_stop_delta | 0.0018401133455305339 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 122.66160156074345 |
| Selected | 122.66160156074345 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3047.4548
- **Net PnL (quote)**: 3738.0569
- **Sharpe Ratio**: 5.9045
- **Max Drawdown %**: 43.6309
- **Profit Factor**: 1.3061023939272194
- **Trade Count**: 16203
- **Total Fees (quote)**: 815.6085
- **Maker Fees**: 277.9681
- **Taker Fees**: 537.6404
- **Fee Drag %**: 664.9257

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.4665
- **PnL Component**: 3.4492
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.3272
- **Fee Drag Component**: -3.3246
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.2482**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 360.56 | 17.42 | 13.76 | 1432 | 0.8490 | n/a |
| 1 | 375.50 | 22.02 | 10.99 | 1321 | 0.9113 | n/a |
| 2 | 112.94 | 17.82 | 10.56 | 1260 | 0.1562 | n/a |
| 3 | 395.96 | 24.99 | 15.19 | 1450 | 0.9209 | n/a |
| 4 | 217.52 | 11.78 | 39.10 | 1373 | 0.2937 | n/a |
| 5 | 243.01 | 21.59 | 19.36 | 1436 | 0.5172 | n/a |
| 6 | 102.91 | 17.67 | 11.80 | 1263 | 0.0963 | n/a |
| 7 | 153.84 | 19.89 | 8.51 | 1278 | 0.3401 | n/a |
| 8 | 117.24 | 18.69 | 11.80 | 1264 | 0.1765 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -3.6947)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2991.79 | 5.83 | 44.24 | -2.0933 |
| fees_2x | 2913.61 | 5.76 | 44.01 | -3.6947 |
| latency_plus1 | 2991.21 | 5.83 | 44.19 | -0.3301 |
| latency_plus2 | 2611.68 | 5.68 | 44.10 | -0.1828 |
| latency_plus3 | 2328.19 | 5.51 | 44.18 | -0.0002 |
| low_liquidity | 3009.61 | 5.81 | 42.67 | -0.0117 |
| very_low_liquidity | 2212.82 | 5.36 | 44.59 | 0.2741 |
| high_slippage | 3099.43 | 5.88 | 43.85 | -0.4339 |
| extreme_slippage | 3000.78 | 5.83 | 44.22 | -0.4425 |
| combined_adverse | 2624.63 | 5.62 | 44.50 | -1.2768 |
| spread_widen_10bps | 3038.11 | 5.89 | 43.55 | -0.4655 |
| spread_widen_25bps | 2942.87 | 5.81 | 44.53 | -0.4781 |
| thin_book | 2053.07 | 5.26 | 45.61 | 0.2730 |
| very_thin_book | 1286.18 | 4.62 | 45.33 | 0.7545 |
| entry_spread_stress | 3055.21 | 5.86 | 44.19 | -0.4602 |
| combined_market_deterioration | 2524.06 | 5.50 | 44.70 | -1.3283 |
| severe_adverse | 1353.07 | 4.71 | 46.31 | -0.9807 |

## Holdout Validation

- **Holdout bars**: 8759
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0079)
- **Trend**: ranging (efficiency: 0.0155)
- **Best holdout score**: 1.0865 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -2.0806 | 0.5898 | 392.05 | 10.46 | 2960 |
| 1 | 1.1124 | 0.8277 | 1024.72 | 7.49 | 5699 |
| 2 | 1.0821 | 0.9485 | 1310.17 | 7.77 | 3067 |
| 3 | 1.0627 | 0.6078 | 854.57 | 7.99 | 7202 |
| 4 | 1.0503 | 1.0865 | 1441.85 | 7.96 | 3195 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51860
- **Expected rows**: 51860
- **Missing rows**: 0
- **Forward-fill count**: 549
- **Forward-fill fraction**: 0.010586193598148863
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.672331007723008
- **PnL %**: 424.00098409056744
- **Trade count**: 2604

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -2.317712359899716
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -2.2288, -2.3688 |
| sell_spread_base | -2.2266, -2.3705 |
| stop_loss | -2.2536, -2.3028 |
| take_profit | -2.2978, -2.3132 |
| executor_refresh_time | -2.3177, -2.5543 |
| cooldown_time | -1.9165, -2.3177 |
| total_amount_quote | -2.2620, -2.3509 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.34612140589019486
- **Max CV**: 0.6701532828321848
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time
- **Scattered params**: take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.4377 | 0.20643195878647855 | 0.6930595041901725 | 0.34927326675179216 |
| buy_spread_ratio | 0.1390 | 1.2576765566684538 | 2.032936357911545 | 1.6854569166566722 |
| sell_spread_base | 0.3010 | 0.25461551835326773 | 0.5171681605762056 | 0.342578016605423 |
| sell_spread_ratio | 0.1297 | 1.2045244130781758 | 1.7049831015050394 | 1.3779311225411786 |
| buy_side_weight | 0.2269 | 0.22981781208632426 | 0.43130364267246357 | 0.32919542742534896 |
| amount_skew | 0.2721 | 1.2750715425066617 | 3.6781766254933537 | 2.6363437756282058 |
| stop_loss | 0.0526 | 0.2122560247302232 | 0.2456218048177782 | 0.23214814214149587 |
| take_profit | 0.5160 | 0.03491046660146588 | 0.1190788618816893 | 0.06520491845471953 |
| executor_refresh_time | 0.4622 | 315.0 | 1119.0 | 537.4 |
| cooldown_time | 0.6702 | 70.0 | 900.0 | 342.2 |
| total_amount_quote | 0.6001 | 25.01678019779115 | 145.21187624372376 | 62.569790777991884 |

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
| recent_objective | > 0 | 0.672331007723008 | PASS |
| recent_pnl | >= 0 | 424.00098409056744 | PASS |
| recent_trades | >= 5 | 2604 | PASS |
| worst_stress | > -10 | -3.6946577110741585 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.5898 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-3.6946577110741585 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.672331007723008, pnl=424.00098409056744, trades=2604, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.34612140589019486 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51860 |  |
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
- **Dev bars**: 35036
- **Holdout bars**: 8759
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-04T06:02:14.012645+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 3426
