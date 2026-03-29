# PMM Dynamic Optimization Report: mexc_TRX-USDT_5m_sweep_v1

Generated: 2026-03-28 21:29:10 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T21:29:10.536646+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 10801 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: TRX-USDT
- **interval**: 5m
- **n_candles**: 51985
- **dataset_hash**: 12cd78a67ada25aa9a44f661324d7fd24c8028d034e18dbfaeb2a2d21ba71abe
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 808.0535387021059
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.500835376846409 |
| buy_n_levels | 9 |
| buy_side_weight | 0.28666575097707914 |
| buy_spread_base | 2.2212851697540463 |
| buy_spread_ratio | 2.1534778447823544 |
| cooldown_time | 140 |
| executor_refresh_time | 1655 |
| macd_fast | 27 |
| macd_signal | 13 |
| macd_slow | 43 |
| natr_length | 19 |
| sell_n_levels | 10 |
| sell_spread_base | 0.21315055964780083 |
| sell_spread_ratio | 1.3352216394794105 |
| stop_loss | 0.09221077180442719 |
| take_profit | 0.007083378482669564 |
| time_limit | 57447 |
| total_amount_quote | 808.0535387021059 |
| trailing_stop_activation | 0.03013031754138532 |
| trailing_stop_delta | 0.010939330766338254 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 808.0535387021059 |
| Selected | 808.0535387021059 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.7427
- **Net PnL (quote)**: -6.0018
- **Sharpe Ratio**: -1.1642
- **Max Drawdown %**: 1.0396
- **Profit Factor**: 0.7731620633902399
- **Trade Count**: 408
- **Total Fees (quote)**: 1.8067
- **Maker Fees**: 1.3228
- **Taker Fees**: 0.4838
- **Fee Drag %**: 0.2236

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0349
- **PnL Component**: -0.0075
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0078
- **Fee Drag Component**: -0.0011
- **Inventory Component**: -0.0184
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1719**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.09 | -2.96 | 0.15 | 41 | -0.0459 | n/a |
| 1 | -0.05 | -2.88 | 0.08 | 2 | -1000.0000 | n/a |
| 2 | -0.02 | -2.09 | 0.07 | 40 | -0.0463 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.02 | 1.61 | 0.05 | 45 | -0.0272 | n/a |
| 5 | -0.31 | -12.20 | 0.34 | 18 | -0.2206 | n/a |
| 6 | -0.01 | -1.33 | 0.03 | 5 | -0.4591 | n/a |
| 7 | -0.15 | -12.11 | 0.16 | 18 | -0.3451 | n/a |
| 8 | -0.10 | -5.36 | 0.15 | 21 | -0.1236 | n/a |

## Stress Test Results

Worst Scenario: **spread_widen_25bps** (score: -0.0529)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.85 | -1.34 | 1.05 | -0.0367 |
| fees_2x | -0.97 | -1.52 | 1.10 | -0.0387 |
| latency_plus1 | -0.63 | -0.98 | 0.98 | -0.0363 |
| latency_plus2 | -0.67 | -1.13 | 0.84 | -0.0319 |
| latency_plus3 | -0.53 | -0.99 | 0.65 | -0.0245 |
| low_liquidity | -0.74 | -1.16 | 1.04 | -0.0349 |
| very_low_liquidity | -0.74 | -1.16 | 1.04 | -0.0349 |
| high_slippage | -0.89 | -1.41 | 1.05 | -0.0365 |
| extreme_slippage | -1.19 | -1.89 | 1.31 | -0.0415 |
| combined_adverse | -0.90 | -1.42 | 1.04 | -0.0401 |
| spread_widen_10bps | -0.84 | -1.30 | 1.15 | -0.0368 |
| spread_widen_25bps | -1.51 | -2.51 | 1.81 | -0.0529 |
| thin_book | -0.43 | -1.03 | 0.61 | -0.0212 |
| very_thin_book | -0.24 | -0.81 | 0.68 | -0.0163 |
| entry_spread_stress | -1.00 | -1.49 | 1.26 | -0.0432 |
| combined_market_deterioration | -1.17 | -1.89 | 1.38 | -0.0364 |
| severe_adverse | -0.94 | -2.54 | 1.04 | -0.0232 |

## Holdout Validation

- **Holdout bars**: 8784
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0010)
- **Trend**: ranging (efficiency: 0.0121)
- **Best holdout score**: -0.0148 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0439 | -0.1579 | -0.06 | 0.10 | 32 |
| 1 | -0.0097 | -0.1579 | -0.06 | 0.10 | 32 |
| 2 | -0.0112 | -0.0148 | -0.22 | 0.25 | 90 |
| 3 | -0.0133 | -0.0642 | -0.23 | 0.25 | 70 |
| 4 | -0.0135 | -0.0767 | -0.20 | 0.24 | 73 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51985
- **Expected rows**: 51985
- **Missing rows**: 0
- **Forward-fill count**: 6
- **Forward-fill fraction**: 0.00011541790901221507
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0560 <= 0; recent PnL -0.0593% < 0
- **Objective score**: -0.05597501809957125
- **PnL %**: -0.05926540382388607
- **Trade count**: 72

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.054415747408165335
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0578, -0.0585 |
| sell_spread_base | -0.0475, -0.0425 |
| stop_loss | -0.0544, -0.0544 |
| take_profit | -0.0634, -0.0408 |
| executor_refresh_time | -0.0407, -0.0444 |
| cooldown_time | -0.0544, -0.0544 |
| total_amount_quote | -0.0544, -0.0351 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3386502904288159
- **Max CV**: 0.613456798593793
- **Clustered params**: buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, total_amount_quote
- **Scattered params**: buy_spread_base, take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.5118 | 0.5529324273036371 | 2.2212851697540463 | 0.9390507883514619 |
| buy_spread_ratio | 0.1377 | 1.9283917761446605 | 2.970295436331619 | 2.543648622128426 |
| sell_spread_base | 0.1127 | 0.21046636417337797 | 0.3024163356695559 | 0.2524515947552571 |
| sell_spread_ratio | 0.2042 | 1.3191317288965005 | 2.2292867574167112 | 1.8050129030341933 |
| buy_side_weight | 0.2765 | 0.20167978903975203 | 0.42912426033096607 | 0.2954251115483376 |
| amount_skew | 0.1646 | 1.500835376846409 | 2.651309016189963 | 2.1810529022384864 |
| stop_loss | 0.4999 | 0.01827212389945102 | 0.11454774272508288 | 0.0675980521827677 |
| take_profit | 0.5054 | 0.005065487816027712 | 0.01729767478609276 | 0.007545724161393623 |
| executor_refresh_time | 0.5611 | 713.0 | 3368.0 | 1464.9 |
| cooldown_time | 0.6135 | 140.0 | 2257.0 | 920.5 |
| total_amount_quote | 0.1379 | 574.1280771121524 | 984.6127923861466 | 894.9165537608444 |

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
| recent_objective | > 0 | -0.05597501809957125 | FAIL |
| recent_pnl | >= 0 | -0.05926540382388607 | FAIL |
| recent_trades | >= 5 | 72 | PASS |
| worst_stress | > -10 | -0.05292697738070129 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.15791746361473574 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=spread_widen_25bps score=-0.05292697738070129 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.05597501809957125, pnl=-0.05926540382388607, trades=72, reason=recent objective score -0.0560 <= 0; recent PnL -0.0593% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3386502904288159 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51985 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0560 <= 0; recent PnL -0.0593% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35136
- **Holdout bars**: 8784
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T21:29:10.536646+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 10801
