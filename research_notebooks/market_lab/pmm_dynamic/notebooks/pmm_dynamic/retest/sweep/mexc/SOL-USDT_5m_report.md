# PMM Dynamic Optimization Report: mexc_SOL-USDT_5m_retest_20260403

Generated: 2026-04-04 04:07:32 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-04T04:07:32.592849+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 10246 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SOL-USDT
- **interval**: 5m
- **n_candles**: 51862
- **dataset_hash**: a05f7d7870c2d2204281b01bab8ccb669dd8ec68aa16bbf0da86eb961ea30363
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 558.5979394867304
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.4397962058842935 |
| buy_n_levels | 5 |
| buy_side_weight | 0.3869037127927026 |
| buy_spread_base | 0.4297618068329945 |
| buy_spread_ratio | 1.3684577192828968 |
| cooldown_time | 460 |
| executor_refresh_time | 1469 |
| macd_fast | 43 |
| macd_signal | 23 |
| macd_slow | 74 |
| natr_length | 37 |
| sell_n_levels | 2 |
| sell_spread_base | 0.227455008823785 |
| sell_spread_ratio | 1.5372277643184074 |
| stop_loss | 0.22337943448180703 |
| take_profit | 0.07903377456192326 |
| time_limit | 157452 |
| total_amount_quote | 558.5979394867304 |
| trailing_stop_activation | 0.01665522438197165 |
| trailing_stop_delta | 0.001592178925010296 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 558.5979394867304 |
| Selected | 558.5979394867304 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2010.8030
- **Net PnL (quote)**: 11232.3042
- **Sharpe Ratio**: 12.1829
- **Max Drawdown %**: 16.9662
- **Profit Factor**: 2.1071928393700787
- **Trade Count**: 16952
- **Total Fees (quote)**: 730.6898
- **Maker Fees**: 370.6814
- **Taker Fees**: 360.0084
- **Fee Drag %**: 130.8078

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.0136
- **PnL Component**: 3.0497
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1272
- **Fee Drag Component**: -0.6540
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.7107**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 232.44 | 34.24 | 5.58 | 1736 | 0.8481 | n/a |
| 1 | 239.80 | 17.98 | 3.86 | 1685 | 0.8875 | n/a |
| 2 | 247.59 | 24.69 | 4.81 | 1713 | 0.9029 | n/a |
| 3 | 162.85 | 47.67 | 3.15 | 1696 | 0.6378 | n/a |
| 4 | 202.26 | 44.08 | 7.39 | 1708 | 0.7404 | n/a |
| 5 | 246.12 | 26.80 | 20.85 | 1776 | 0.7696 | n/a |
| 6 | 174.10 | 38.55 | 8.74 | 1707 | 0.6316 | n/a |
| 7 | 237.88 | 42.05 | 4.76 | 1696 | 0.8702 | n/a |
| 8 | 151.82 | 45.60 | 6.30 | 1671 | 0.5703 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.0645)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 1960.29 | 12.06 | 16.80 | 1.6693 |
| fees_2x | 1924.72 | 11.95 | 16.91 | 1.3276 |
| latency_plus1 | 1791.60 | 11.84 | 16.71 | 1.9594 |
| latency_plus2 | 1566.60 | 11.25 | 17.21 | 1.9032 |
| latency_plus3 | 1275.75 | 10.61 | 17.26 | 1.7909 |
| low_liquidity | 2010.80 | 12.18 | 16.97 | 2.0136 |
| very_low_liquidity | 2010.80 | 12.18 | 16.97 | 2.0136 |
| high_slippage | 1909.49 | 11.98 | 16.74 | 1.9712 |
| extreme_slippage | 1769.48 | 11.92 | 16.81 | 1.9040 |
| combined_adverse | 1705.73 | 11.62 | 16.93 | 1.6141 |
| spread_widen_10bps | 1932.10 | 12.19 | 16.76 | 1.9855 |
| spread_widen_25bps | 1825.45 | 11.74 | 16.47 | 1.9337 |
| thin_book | 1300.53 | 10.51 | 17.28 | 1.8352 |
| very_thin_book | 626.69 | 8.17 | 17.35 | 1.3897 |
| entry_spread_stress | 1883.28 | 11.92 | 16.55 | 1.9595 |
| combined_market_deterioration | 1519.17 | 11.00 | 16.79 | 1.6143 |
| severe_adverse | 592.01 | 7.59 | 18.30 | 1.0645 |

## Holdout Validation

- **Holdout bars**: 8759
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0038)
- **Trend**: ranging (efficiency: 0.0065)
- **Best holdout score**: 1.8098 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.5390 | 1.4031 | 546.99 | 9.58 | 3851 |
| 1 | 1.2017 | 1.7328 | 868.48 | 9.58 | 4636 |
| 2 | 1.2009 | 1.7317 | 900.73 | 9.86 | 6375 |
| 3 | 1.1342 | 1.7613 | 926.73 | 8.93 | 5252 |
| 4 | 1.1180 | 1.8098 | 948.19 | 8.82 | 5894 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51862
- **Expected rows**: 51862
- **Missing rows**: 0
- **Forward-fill count**: 254
- **Forward-fill fraction**: 0.004897612895761829
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.479248431801082
- **PnL %**: 572.1293514772092
- **Trade count**: 3604

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.7835767515024326
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.7787, 1.7782 |
| sell_spread_base | 1.7869, 1.7793 |
| stop_loss | 1.7724, 1.7786 |
| take_profit | 1.7836, 1.7836 |
| executor_refresh_time | 1.7690, 1.7836 |
| cooldown_time | 1.7836, 1.7836 |
| total_amount_quote | 1.7652, 1.7813 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.30376271783862996
- **Max CV**: 0.9042503170530125
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time
- **Scattered params**: total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1499 | 0.20926308730805893 | 0.34119239554237696 | 0.2652686573316776 |
| buy_spread_ratio | 0.1447 | 1.2092043699145318 | 1.8175069942644115 | 1.4738138095240036 |
| sell_spread_base | 0.1710 | 0.2017165859407965 | 0.34357806264156127 | 0.2566480201609739 |
| sell_spread_ratio | 0.1904 | 1.2380532162769253 | 2.1290337815727196 | 1.6337051988835203 |
| buy_side_weight | 0.2270 | 0.30343946007022204 | 0.7065362889713663 | 0.46487660067437997 |
| amount_skew | 0.2388 | 2.0299506649091454 | 3.717594705835758 | 2.674695966830494 |
| stop_loss | 0.1893 | 0.12363516680491118 | 0.22018465540503301 | 0.1871409542647453 |
| take_profit | 0.4576 | 0.0333492311917768 | 0.12472923181093296 | 0.06477531295946477 |
| executor_refresh_time | 0.2502 | 409.0 | 843.0 | 542.5 |
| cooldown_time | 0.4183 | 75.0 | 274.0 | 177.9 |
| total_amount_quote | 0.9043 | 29.518613343700736 | 397.3918144158661 | 120.0174532892332 |

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
| recent_objective | > 0 | 1.479248431801082 | PASS |
| recent_pnl | >= 0 | 572.1293514772092 | PASS |
| recent_trades | >= 5 | 3604 | PASS |
| worst_stress | > -10 | 1.0644740262266454 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.4031 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.0644740262266454 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.479248431801082, pnl=572.1293514772092, trades=3604, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.30376271783862996 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51862 |  |
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
- **Dev bars**: 35038
- **Holdout bars**: 8759
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-04T04:07:32.592849+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 10246
