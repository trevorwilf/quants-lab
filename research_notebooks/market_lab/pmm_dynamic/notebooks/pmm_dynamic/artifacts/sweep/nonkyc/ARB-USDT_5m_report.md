# PMM Dynamic Optimization Report: nonkyc_ARB-USDT_5m_sweep_v1

Generated: 2026-04-08 18:55:55 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T18:55:55.835372+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 6707 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARB-USDT
- **interval**: 5m
- **n_candles**: 51894
- **dataset_hash**: 6a3c75ecede833f2291b0791df4ba54ebaa413ae21e77d483f3212af46486ff7
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 665.0656307944568
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.3196382317564783 |
| buy_n_levels | 9 |
| buy_side_weight | 0.21674366300155934 |
| buy_spread_base | 3.0616943177429206 |
| buy_spread_ratio | 2.497619610195171 |
| cooldown_time | 4428 |
| executor_refresh_time | 10291 |
| macd_fast | 19 |
| macd_signal | 18 |
| macd_slow | 85 |
| natr_length | 31 |
| sell_n_levels | 6 |
| sell_spread_base | 5.7138866329601035 |
| sell_spread_ratio | 2.830639637155982 |
| stop_loss | 0.02156431804463548 |
| take_profit | 0.005444650254308124 |
| time_limit | 146828 |
| total_amount_quote | 665.0656307944568 |
| trailing_stop_activation | 0.0337940318886829 |
| trailing_stop_delta | 0.004916127869927141 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 665.0656307944568 |
| Selected | 665.0656307944568 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -3.0671
- **Net PnL (quote)**: -20.3983
- **Sharpe Ratio**: -6.0963
- **Max Drawdown %**: 3.1326
- **Profit Factor**: 0.573293412108742
- **Trade Count**: 735
- **Total Fees (quote)**: 13.2197
- **Maker Fees**: 9.6530
- **Taker Fees**: 3.5666
- **Fee Drag %**: 1.9877
- **TP Min-Notional Failures**: 9449 :warning:
  > 9449 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0722
- **PnL Component**: -0.0312
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0235
- **Fee Drag Component**: -0.0099
- **Inventory Component**: -0.0075
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0108**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.29 | -8.87 | 0.32 | 76 | -0.0090 | n/a |
| 1 | -0.57 | -17.81 | 0.60 | 63 | -0.0396 | n/a |
| 2 | -0.09 | -6.01 | 0.11 | 59 | -0.0050 | n/a |
| 3 | -0.20 | -7.41 | 0.26 | 67 | -0.0076 | n/a |
| 4 | -0.04 | -0.50 | 0.35 | 80 | -0.0071 | n/a |
| 5 | -0.37 | -7.18 | 0.65 | 65 | -0.0125 | n/a |
| 6 | -0.63 | -16.88 | 0.66 | 78 | -0.0171 | n/a |
| 7 | -0.12 | -4.01 | 0.15 | 72 | -0.0058 | n/a |
| 8 | -0.75 | -13.82 | 0.77 | 72 | -0.0923 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1711)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -4.06 | -8.06 | 4.11 | -0.0949 |
| fees_2x | -5.05 | -9.98 | 5.10 | -0.1177 |
| latency_plus1 | -3.12 | -6.20 | 3.19 | -0.0732 |
| latency_plus2 | -3.15 | -5.82 | 3.28 | -0.0750 |
| latency_plus3 | -3.32 | -6.04 | 3.47 | -0.0785 |
| low_liquidity | -4.47 | -6.79 | 4.58 | -0.1007 |
| very_low_liquidity | -6.11 | -6.29 | 6.32 | -0.1382 |
| high_slippage | -3.20 | -6.37 | 3.26 | -0.0746 |
| extreme_slippage | -3.47 | -6.92 | 3.53 | -0.0794 |
| combined_adverse | -5.78 | -8.66 | 5.86 | -0.1298 |
| spread_widen_10bps | -3.82 | -6.44 | 3.93 | -0.0882 |
| spread_widen_25bps | -5.10 | -7.30 | 5.30 | -0.1140 |
| thin_book | -3.88 | -8.18 | 3.91 | -0.0831 |
| very_thin_book | -3.52 | -9.89 | 3.54 | -0.0736 |
| entry_spread_stress | -5.11 | -6.94 | 5.33 | -0.1155 |
| combined_market_deterioration | -6.10 | -10.27 | 6.26 | -0.1335 |
| severe_adverse | -8.03 | -12.29 | 8.24 | -0.1711 |

## Holdout Validation

- **Holdout bars**: 8767
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0035)
- **Trend**: ranging (efficiency: 0.0077)
- **Best holdout score**: -0.0145 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1217 | -0.0180 | -0.75 | 0.77 | 157 |
| 1 | -0.0074 | -0.0217 | -0.77 | 0.81 | 234 |
| 2 | -0.0074 | -0.0145 | -0.50 | 0.54 | 259 |
| 3 | -0.0076 | -0.0300 | -1.03 | 1.17 | 209 |
| 4 | -0.0078 | -0.0212 | -0.53 | 0.75 | 295 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51894
- **Expected rows**: 51902
- **Missing rows**: 8
- **Forward-fill count**: 160
- **Forward-fill fraction**: 0.0030832080780051644
- **Longest gap (seconds)**: 2700

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1204 <= 0; recent PnL -1.0799% < 0
- **Objective score**: -0.1203682241057433
- **PnL %**: -1.0799091293475112
- **Trade count**: 115

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1658 <= 0; recent PnL -0.3662% < 0
- **Objective score**: -0.1657766137297241
- **PnL %**: -0.3662431105560712
- **Trade count**: 49

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2251 <= 0; recent PnL -0.1602% < 0
- **Objective score**: -0.22512299325575474
- **PnL %**: -0.16015249830473338
- **Trade count**: 22

## Sensitivity Analysis

- **Sensitivity penalty**: 0.35714285714285715
- **Baseline score**: -0.10901415529842477
- **Sign flips**: 0
- **Collapse count**: 5
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.3172, -0.1718 |
| sell_spread_base | -0.1077, -0.2111 |
| stop_loss | -0.1303, -0.1392 |
| take_profit | -0.1444, -0.1147 |
| executor_refresh_time | -0.1913, -0.1389 |
| cooldown_time | -0.1897, -0.1406 |
| total_amount_quote | -0.1109, -0.1124 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.22089950668181754
- **Max CV**: 0.4543739825953813
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1631 | 2.1472459960874426 | 4.134843336513925 | 2.985642669015579 |
| buy_spread_ratio | 0.1348 | 1.5014004447160274 | 2.636802268808437 | 2.3416405407357184 |
| sell_spread_base | 0.4342 | 2.0710909924596943 | 5.745819301570801 | 3.7176548441548363 |
| sell_spread_ratio | 0.1100 | 2.129270103399802 | 2.9343039576550622 | 2.442103905849243 |
| buy_side_weight | 0.1392 | 0.20028890808742095 | 0.3035569326701255 | 0.23600650892559472 |
| amount_skew | 0.1471 | 1.6202570238559313 | 2.97048099037047 | 2.543139802648171 |
| stop_loss | 0.2853 | 0.01025391213424068 | 0.02542524488874648 | 0.017190246940232405 |
| take_profit | 0.4544 | 0.005108829543589248 | 0.015174880725129972 | 0.0067038352339807246 |
| executor_refresh_time | 0.2106 | 5269.0 | 12630.0 | 9554.1 |
| cooldown_time | 0.2102 | 3692.0 | 6884.0 | 5625.5 |
| total_amount_quote | 0.1411 | 657.4369777065624 | 961.5276309064893 | 791.2888121664137 |

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
| recent_objective | > 0 | -0.1203682241057433 | FAIL |
| recent_pnl | >= 0 | -1.0799091293475112 | FAIL |
| recent_trades | >= 5 | 115 | PASS |
| worst_stress | > -10 | -0.17109510551963455 | PASS |
| sensitivity_penalty | < 0.50 | 0.35714285714285715 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.018022176173696933 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.17109510551963455 |
| sensitivity | PASS | penalty=0.35714285714285715 |
| recent_28d | FAIL | score=-0.1203682241057433, pnl=-1.0799091293475112, trades=115, reason=recent objective score -0.1204 <= 0; recent PnL -1.0799% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.1657766137297241, pnl=-0.3662431105560712, trades=49, reason=recent objective score -0.1658 <= 0; recent PnL -0.3662% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.22512299325575474, pnl=-0.16015249830473338, trades=22, reason=recent objective score -0.2251 <= 0; recent PnL -0.1602% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.22089950668181754 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51894 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1204 <= 0; recent PnL -1.0799% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1658 <= 0; recent PnL -0.3662% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2251 <= 0; recent PnL -0.1602% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51894
- **Pre-release bars**: 43837
- **Dev bars**: 35070
- **Holdout bars**: 8767
- **Recent 28d bars**: 8057
- **Recent window start**: 1773251100

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T18:55:55.835372+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 6707
