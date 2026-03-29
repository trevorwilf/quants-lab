# PMM Dynamic Optimization Report: mexc_SUI-USDT_5m_sweep_v1

Generated: 2026-03-28 20:10:20 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T20:10:20.285418+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 10565 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SUI-USDT
- **interval**: 5m
- **n_candles**: 51985
- **dataset_hash**: e015bbd244d1b50b08dabef03129e1ea6c294f7ec491259ed0ac14419677c671
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 811.7931947958574
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.221115272592875 |
| buy_n_levels | 4 |
| buy_side_weight | 0.3144669477072461 |
| buy_spread_base | 1.263859258703595 |
| buy_spread_ratio | 2.508731899732103 |
| cooldown_time | 3679 |
| executor_refresh_time | 9814 |
| macd_fast | 43 |
| macd_signal | 16 |
| macd_slow | 74 |
| natr_length | 8 |
| sell_n_levels | 6 |
| sell_spread_base | 3.1535565681317164 |
| sell_spread_ratio | 2.3556101417525546 |
| stop_loss | 0.011821583570553098 |
| take_profit | 0.04459327508203142 |
| time_limit | 132798 |
| total_amount_quote | 811.7931947958574 |
| trailing_stop_activation | 0.0029416581271606177 |
| trailing_stop_delta | 0.0010541521840347688 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 811.7931947958574 |
| Selected | 811.7931947958574 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3.7526
- **Net PnL (quote)**: 30.4634
- **Sharpe Ratio**: 2.7349
- **Max Drawdown %**: 1.4902
- **Profit Factor**: 1.6687447353518625
- **Trade Count**: 1035
- **Total Fees (quote)**: 6.1066
- **Maker Fees**: 3.0496
- **Taker Fees**: 3.0569
- **Fee Drag %**: 0.7522

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0167
- **PnL Component**: 0.0368
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0112
- **Fee Drag Component**: -0.0038
- **Inventory Component**: -0.0051
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0040**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.74 | 5.39 | 0.20 | 133 | 0.0036 | n/a |
| 1 | -0.21 | -2.79 | 0.48 | 108 | -0.0078 | n/a |
| 2 | 0.34 | 7.37 | 0.13 | 98 | 0.0004 | n/a |
| 3 | 0.10 | 2.91 | 0.09 | 87 | -0.0017 | n/a |
| 4 | -0.17 | -3.51 | 0.43 | 105 | -0.0086 | n/a |
| 5 | 1.24 | 8.51 | 0.26 | 135 | 0.0082 | n/a |
| 6 | -0.22 | -5.99 | 0.30 | 506 | -0.0064 | n/a |
| 7 | 0.48 | 10.23 | 0.06 | 98 | -0.0013 | n/a |
| 8 | 0.04 | 1.61 | 0.13 | 84 | -0.0024 | n/a |

## Stress Test Results

Worst Scenario: **very_thin_book** (score: -0.0950)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3.38 | 2.47 | 1.49 | 0.0112 |
| fees_2x | 3.00 | 2.20 | 1.50 | 0.0056 |
| latency_plus1 | 2.71 | 2.09 | 1.49 | 0.0066 |
| latency_plus2 | 2.60 | 2.01 | 1.49 | 0.0055 |
| latency_plus3 | 1.93 | 1.52 | 1.49 | -0.0011 |
| low_liquidity | 3.75 | 2.73 | 1.49 | 0.0167 |
| very_low_liquidity | 3.75 | 2.73 | 1.49 | 0.0167 |
| high_slippage | 2.81 | 2.07 | 1.50 | 0.0075 |
| extreme_slippage | 0.93 | 0.71 | 1.51 | -0.0111 |
| combined_adverse | 1.39 | 1.09 | 1.50 | -0.0084 |
| spread_widen_10bps | 1.17 | 0.68 | 2.06 | -0.0151 |
| spread_widen_25bps | -0.93 | -0.69 | 1.99 | -0.0352 |
| thin_book | -3.24 | -2.63 | 4.22 | -0.0750 |
| very_thin_book | -4.59 | -1.81 | 5.89 | -0.0950 |
| entry_spread_stress | 0.33 | 0.28 | 1.96 | -0.0227 |
| combined_market_deterioration | -3.74 | -2.61 | 4.23 | -0.0827 |
| severe_adverse | -3.79 | -3.62 | 4.51 | -0.0833 |

## Holdout Validation

- **Holdout bars**: 8784
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0042)
- **Trend**: ranging (efficiency: 0.0266)
- **Best holdout score**: 0.0029 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0391 | -0.0029 | 0.55 | 0.30 | 641 |
| 1 | -0.0007 | -0.0053 | -0.11 | 0.46 | 148 |
| 2 | -0.0012 | -0.0112 | -0.39 | 0.81 | 165 |
| 3 | -0.0019 | -0.0010 | 0.29 | 0.19 | 126 |
| 4 | -0.0021 | 0.0029 | 1.18 | 0.51 | 136 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51985
- **Expected rows**: 51985
- **Missing rows**: 0
- **Forward-fill count**: 23
- **Forward-fill fraction**: 0.0004424353178801577
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0081 <= 0
- **Objective score**: -0.008058874406209822
- **PnL %**: 0.037880137759506174
- **Trade count**: 186

## Sensitivity Analysis

- **Sensitivity penalty**: 1.0714285714285714
- **Baseline score**: 0.020743025959613463
- **Sign flips**: 5
- **Collapse count**: 10
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0127, -0.0026 |
| sell_spread_base | 0.0208, 0.0061 |
| stop_loss | 0.0064, 0.0063 |
| take_profit | 0.0207, 0.0207 |
| executor_refresh_time | 0.0072, -0.0109 |
| cooldown_time | 0.0067, -0.0014 |
| total_amount_quote | 0.0214, -0.0186 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.41300157581001673
- **Max CV**: 0.7601229073667521
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1963 | 1.472941068013238 | 3.1263493751144473 | 2.2806703894258407 |
| buy_spread_ratio | 0.1574 | 1.60950914381851 | 2.840634273269121 | 2.285125955039421 |
| sell_spread_base | 0.7515 | 0.3806262780303814 | 5.890464696535258 | 2.542806940150248 |
| sell_spread_ratio | 0.3583 | 1.211688542967311 | 2.9752730228226505 | 1.7998698240012192 |
| buy_side_weight | 0.3044 | 0.21204105792555672 | 0.47591163104705675 | 0.3221460019920179 |
| amount_skew | 0.0805 | 2.8734041286684584 | 3.7562804944124615 | 3.2689208850797895 |
| stop_loss | 0.5719 | 0.010139871031487955 | 0.03853420734311504 | 0.014876429741565538 |
| take_profit | 0.7601 | 0.007899563454099404 | 0.07627369536118536 | 0.025585344409311244 |
| executor_refresh_time | 0.6658 | 1571.0 | 12914.0 | 7192.3 |
| cooldown_time | 0.5443 | 281.0 | 5870.0 | 3600.6 |
| total_amount_quote | 0.1524 | 598.0153848820391 | 947.2455110070367 | 797.2946771249116 |

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
- holdout_no_collapse: PASS
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.008058874406209822 | FAIL |
| recent_pnl | >= 0 | 0.037880137759506174 | PASS |
| recent_trades | >= 5 | 186 | PASS |
| worst_stress | > -10 | -0.09503546354249194 | PASS |
| sensitivity_penalty | < 0.50 | 1.0714285714285714 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.002896947776354843 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_thin_book score=-0.09503546354249194 |
| sensitivity | FAIL | penalty=1.0714285714285714 |
| recent_28d | FAIL | score=-0.008058874406209822, pnl=0.037880137759506174, trades=186, reason=recent objective score -0.0081 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.41300157581001673 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51985 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0081 <= 0 |
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
- **run_timestamp**: 2026-03-28T20:10:20.285418+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 10565
