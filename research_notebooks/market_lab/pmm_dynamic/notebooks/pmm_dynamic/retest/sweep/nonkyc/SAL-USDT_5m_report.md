# PMM Dynamic Optimization Report: nonkyc_SAL-USDT_5m_retest_20260403

Generated: 2026-04-04 06:57:36 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-04T06:57:36.508923+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 5711 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: SAL-USDT
- **interval**: 5m
- **n_candles**: 51924
- **dataset_hash**: 9aa57d2bfdda93b138fe20e743ffe5caf5a01219d3a369cc988af62a4a74e126
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 32.34699644414891
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.5282986067395394 |
| buy_n_levels | 2 |
| buy_side_weight | 0.3969037567405553 |
| buy_spread_base | 0.3208165935608999 |
| buy_spread_ratio | 2.809875140445916 |
| cooldown_time | 1432 |
| executor_refresh_time | 2315 |
| macd_fast | 41 |
| macd_signal | 27 |
| macd_slow | 85 |
| natr_length | 21 |
| sell_n_levels | 7 |
| sell_spread_base | 0.3069392453389463 |
| sell_spread_ratio | 1.4004684356574935 |
| stop_loss | 0.1888987855035083 |
| take_profit | 0.070109381943505 |
| time_limit | 169470 |
| total_amount_quote | 32.34699644414891 |
| trailing_stop_activation | 0.08475572428913168 |
| trailing_stop_delta | 0.002996687791931386 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 32.34699644414891 |
| Selected | 32.34699644414891 |

> **WARNING**: Selected quote is within 5% of search minimum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 1785.6769
- **Net PnL (quote)**: 577.6128
- **Sharpe Ratio**: 4.2213
- **Max Drawdown %**: 51.6794
- **Profit Factor**: 1.43663411939044
- **Trade Count**: 9668
- **Total Fees (quote)**: 170.3633
- **Maker Fees**: 73.5066
- **Taker Fees**: 96.8567
- **Fee Drag %**: 526.6743

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.3513
- **PnL Component**: 2.9369
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.3876
- **Fee Drag Component**: -2.6334
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.8138**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 390.55 | 16.81 | 20.59 | 946 | 0.9109 | n/a |
| 1 | 45.13 | 7.11 | 17.86 | 857 | -0.2628 | n/a |
| 2 | 409.99 | 17.62 | 26.54 | 939 | 0.8942 | n/a |
| 3 | 219.77 | 16.34 | 19.34 | 845 | 0.5085 | n/a |
| 4 | 381.14 | 24.97 | 8.72 | 988 | 0.9648 | n/a |
| 5 | 357.29 | 6.66 | 14.75 | 996 | 0.8641 | n/a |
| 6 | 432.83 | 19.29 | 22.66 | 943 | 0.9754 | n/a |
| 7 | 143.95 | 9.82 | 24.76 | 930 | 0.1878 | n/a |
| 8 | 325.26 | 20.09 | 15.38 | 938 | 0.7927 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -3.0690)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 1688.71 | 4.19 | 56.45 | -1.7096 |
| fees_2x | 1338.81 | 4.08 | 54.27 | -3.0690 |
| latency_plus1 | 1513.01 | 4.15 | 45.89 | -0.2689 |
| latency_plus2 | 1373.78 | 4.07 | 53.51 | -0.2078 |
| latency_plus3 | 1314.64 | 4.07 | 54.81 | -0.0932 |
| low_liquidity | 1321.97 | 4.07 | 44.41 | -0.1818 |
| very_low_liquidity | 1074.43 | 3.92 | 57.06 | 0.0255 |
| high_slippage | 1602.74 | 4.09 | 43.48 | -0.3453 |
| extreme_slippage | 1513.94 | 4.08 | 46.46 | -0.4259 |
| combined_adverse | 1134.68 | 3.94 | 46.34 | -1.2229 |
| spread_widen_10bps | 1747.89 | 4.27 | 41.38 | -0.2717 |
| spread_widen_25bps | 1653.74 | 4.20 | 48.53 | -0.3817 |
| thin_book | 919.44 | 3.75 | 59.21 | -0.1139 |
| very_thin_book | 456.72 | 3.19 | 42.30 | 0.1911 |
| entry_spread_stress | 1602.23 | 4.18 | 41.11 | -0.3511 |
| combined_market_deterioration | 1152.87 | 3.88 | 53.80 | -1.3392 |
| severe_adverse | 371.37 | 3.00 | 64.11 | -1.5371 |

## Holdout Validation

- **Holdout bars**: 8772
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0083)
- **Trend**: ranging (efficiency: 0.0029)
- **Best holdout score**: 1.2330 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -1.7102 | 0.9104 | 678.75 | 34.67 | 2149 |
| 1 | 1.2838 | 1.1530 | 2219.87 | 35.55 | 3323 |
| 2 | 1.2443 | 1.2330 | 1754.51 | 30.77 | 3322 |
| 3 | 1.2329 | 1.2301 | 1390.83 | 32.11 | 2456 |
| 4 | 1.1974 | 1.1686 | 1861.08 | 37.25 | 3457 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51924
- **Expected rows**: 51925
- **Missing rows**: 1
- **Forward-fill count**: 1045
- **Forward-fill fraction**: 0.020125568138047917
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.9584452653304456
- **PnL %**: 586.1091253152451
- **Trade count**: 1895

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -1.6608929194643482
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -1.7361, -1.7295 |
| sell_spread_base | -1.6615, -1.8427 |
| stop_loss | -1.5331, -1.9344 |
| take_profit | -1.8522, -1.6084 |
| executor_refresh_time | -1.5196, -1.8528 |
| cooldown_time | -1.4689, -1.6609 |
| total_amount_quote | -1.6840, -2.0598 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2974419747687791
- **Max CV**: 0.677609481912163
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2954 | 0.21537530282190706 | 0.5249887935966536 | 0.33797523335436935 |
| buy_spread_ratio | 0.1998 | 1.4545988382997512 | 2.4921847371278165 | 1.8543168160037973 |
| sell_spread_base | 0.2743 | 0.2017667550439643 | 0.43327041854946036 | 0.3182051274028518 |
| sell_spread_ratio | 0.3092 | 1.255896766678152 | 2.98841695763312 | 2.2689397612682187 |
| buy_side_weight | 0.2774 | 0.2871548163055735 | 0.608605665723032 | 0.4686617331732655 |
| amount_skew | 0.1560 | 2.3010940583558472 | 3.994241728740553 | 3.2996207309922196 |
| stop_loss | 0.1217 | 0.17173617103026179 | 0.24579367722924456 | 0.20843484031888257 |
| take_profit | 0.3464 | 0.03861849277977814 | 0.12490357722227147 | 0.08069369699218504 |
| executor_refresh_time | 0.3995 | 465.0 | 1478.0 | 751.8 |
| cooldown_time | 0.6776 | 63.0 | 626.0 | 264.3 |
| total_amount_quote | 0.2145 | 26.77543370894515 | 50.242910769456714 | 36.54344266412917 |

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
| recent_objective | > 0 | 0.9584452653304456 | PASS |
| recent_pnl | >= 0 | 586.1091253152451 | PASS |
| recent_trades | >= 5 | 1895 | PASS |
| worst_stress | > -10 | -3.0690170467913034 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.9104 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-3.0690170467913034 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.9584452653304456, pnl=586.1091253152451, trades=1895, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2974419747687791 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51924 |  |
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
- **Dev bars**: 35088
- **Holdout bars**: 8772
- **Recent 28d bars**: 8064

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-04T06:57:36.508923+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 5711
