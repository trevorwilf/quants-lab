# PMM Dynamic Optimization Report: nonkyc_ARB-USDT_5m_sweep_v1

Generated: 2026-03-29 05:12:15 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T05:12:15.801066+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 1761 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARB-USDT
- **interval**: 5m
- **n_candles**: 51840
- **dataset_hash**: bfd1fa8108c4ea57639ef9e71f0db60bdb73d4a8e30680137e93d28824b6e6d7
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 801.0340248915945
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.781889830585434 |
| buy_n_levels | 7 |
| buy_side_weight | 0.20858641536322942 |
| buy_spread_base | 3.9603449428685287 |
| buy_spread_ratio | 1.8498281737666593 |
| cooldown_time | 448 |
| executor_refresh_time | 2634 |
| macd_fast | 20 |
| macd_signal | 28 |
| macd_slow | 22 |
| natr_length | 18 |
| sell_n_levels | 8 |
| sell_spread_base | 3.2592118527764424 |
| sell_spread_ratio | 1.2532735256433287 |
| stop_loss | 0.016137747685562743 |
| take_profit | 0.005418157151359408 |
| time_limit | 66969 |
| total_amount_quote | 801.0340248915945 |
| trailing_stop_activation | 0.03394393657301109 |
| trailing_stop_delta | 0.003865485064980348 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 801.0340248915945 |
| Selected | 801.0340248915945 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.0294
- **Net PnL (quote)**: -16.2565
- **Sharpe Ratio**: -2.3050
- **Max Drawdown %**: 2.1390
- **Profit Factor**: 0.44423480071512683
- **Trade Count**: 677
- **Total Fees (quote)**: 9.7222
- **Maker Fees**: 6.7757
- **Taker Fees**: 2.9465
- **Fee Drag %**: 1.2137

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0463
- **PnL Component**: -0.0205
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0160
- **Fee Drag Component**: -0.0061
- **Inventory Component**: -0.0036
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0066**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.16 | -3.06 | 0.32 | 72 | -0.0061 | n/a |
| 1 | -0.19 | -8.05 | 0.27 | 56 | -0.0061 | n/a |
| 2 | -0.12 | -8.12 | 0.15 | 34 | -0.0683 | n/a |
| 3 | -0.06 | -5.10 | 0.09 | 38 | -0.0511 | n/a |
| 4 | 0.08 | 0.62 | 0.52 | 80 | -0.0056 | n/a |
| 5 | -0.26 | -7.60 | 0.36 | 70 | -0.0078 | n/a |
| 6 | -0.17 | -7.29 | 0.20 | 61 | -0.0053 | n/a |
| 7 | -0.61 | -10.11 | 0.64 | 58 | -0.0133 | n/a |
| 8 | -0.02 | -0.81 | 0.10 | 119 | -0.0054 | n/a |

## Stress Test Results

Worst Scenario: **spread_widen_25bps** (score: -0.1210)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.64 | -3.01 | 2.65 | -0.0593 |
| fees_2x | -3.24 | -3.72 | 3.25 | -0.0732 |
| latency_plus1 | -2.05 | -2.32 | 2.16 | -0.0465 |
| latency_plus2 | -2.18 | -2.47 | 2.29 | -0.0488 |
| latency_plus3 | -2.22 | -2.37 | 2.47 | -0.0506 |
| low_liquidity | -2.38 | -2.52 | 2.45 | -0.0501 |
| very_low_liquidity | -2.56 | -3.00 | 2.57 | -0.0547 |
| high_slippage | -2.12 | -2.42 | 2.21 | -0.0477 |
| extreme_slippage | -2.31 | -2.65 | 2.35 | -0.0507 |
| combined_adverse | -3.03 | -3.22 | 3.04 | -0.0641 |
| spread_widen_10bps | -2.56 | -2.90 | 2.59 | -0.0527 |
| spread_widen_25bps | -5.92 | -6.35 | 6.09 | -0.1210 |
| thin_book | -1.74 | -1.77 | 1.74 | -0.0354 |
| very_thin_book | -1.27 | -0.53 | 3.41 | -0.0400 |
| entry_spread_stress | -3.13 | -3.84 | 3.29 | -0.0660 |
| combined_market_deterioration | -3.00 | -3.47 | 3.18 | -0.0654 |
| severe_adverse | -4.46 | -4.27 | 4.52 | -0.0923 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0040)
- **Trend**: ranging (efficiency: 0.0232)
- **Best holdout score**: -0.0134 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0836 | -0.0134 | -0.51 | 0.68 | 142 |
| 1 | -0.0064 | -0.0280 | -1.26 | 1.28 | 191 |
| 2 | -0.0065 | -0.0320 | -1.45 | 1.50 | 176 |
| 3 | -0.0070 | -0.0143 | -0.58 | 0.65 | 157 |
| 4 | -0.0073 | -0.0134 | -0.51 | 0.68 | 142 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51840
- **Expected rows**: 51841
- **Missing rows**: 1
- **Forward-fill count**: 129
- **Forward-fill fraction**: 0.002488425925925926
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0245 <= 0; recent PnL -0.9100% < 0
- **Objective score**: -0.024467896589218992
- **PnL %**: -0.9100407084239979
- **Trade count**: 241

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: -0.08878964654917632
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1252, -0.1505 |
| sell_spread_base | -0.0794, -0.1083 |
| stop_loss | -0.1083, -0.0819 |
| take_profit | -0.0989, -0.0603 |
| executor_refresh_time | -0.1394, -0.0842 |
| cooldown_time | -0.0888, -0.0888 |
| total_amount_quote | -0.0879, -0.2551 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.25277147263302086
- **Max CV**: 0.5886140578734629
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1604 | 2.4408146150773824 | 3.9603449428685287 | 3.120183134474499 |
| buy_spread_ratio | 0.1013 | 1.8498281737666593 | 2.6958747138534482 | 2.3492277405895523 |
| sell_spread_base | 0.3190 | 1.80822634377529 | 5.861769423713396 | 4.082469809686852 |
| sell_spread_ratio | 0.2763 | 1.2532735256433287 | 2.9377122668501445 | 1.9190608366200084 |
| buy_side_weight | 0.3225 | 0.20858641536322942 | 0.5706378890645402 | 0.3579629550785119 |
| amount_skew | 0.1458 | 2.7108179344867303 | 3.981693756783791 | 3.3813478830016366 |
| stop_loss | 0.1975 | 0.010356727381583572 | 0.016302752729125014 | 0.012508660841659334 |
| take_profit | 0.1367 | 0.005279839018512407 | 0.007898304117718689 | 0.006244147294685283 |
| executor_refresh_time | 0.4559 | 2634.0 | 13163.0 | 8118.8 |
| cooldown_time | 0.5886 | 448.0 | 6856.0 | 3219.7 |
| total_amount_quote | 0.0766 | 801.0340248915945 | 982.8248892654788 | 918.273779729028 |

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
- walkforward_positive_majority: **FAIL**
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.024467896589218992 | FAIL |
| recent_pnl | >= 0 | -0.9100407084239979 | FAIL |
| recent_trades | >= 5 | 241 | PASS |
| worst_stress | > -10 | -0.1209771658227681 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.013402037407469968 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=spread_widen_25bps score=-0.1209771658227681 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | FAIL | score=-0.024467896589218992, pnl=-0.9100407084239979, trades=241, reason=recent objective score -0.0245 <= 0; recent PnL -0.9100% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.25277147263302086 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51840 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0245 <= 0; recent PnL -0.9100% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8064

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T05:12:15.801066+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 1761
