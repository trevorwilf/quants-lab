# PMM Dynamic Optimization Report: nonkyc_ARRR-XMR_5m_sweep_v1

Generated: 2026-03-29 06:55:28 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T06:55:28.050853+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 7631 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-XMR
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 0bd9141762d7debd7736df6a4d8fc4eaa78522541a7ae62e2ac04c323bf8529b
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 614.1251262333785
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.6042690963786246 |
| buy_n_levels | 8 |
| buy_side_weight | 0.5748641308947742 |
| buy_spread_base | 5.187778431420069 |
| buy_spread_ratio | 2.6508427234072065 |
| cooldown_time | 286 |
| executor_refresh_time | 7406 |
| macd_fast | 18 |
| macd_signal | 5 |
| macd_slow | 91 |
| natr_length | 15 |
| sell_n_levels | 6 |
| sell_spread_base | 1.890720413405929 |
| sell_spread_ratio | 2.0620745411937613 |
| stop_loss | 0.16728191880267676 |
| take_profit | 0.0606321208935608 |
| time_limit | 68458 |
| total_amount_quote | 614.1251262333785 |
| trailing_stop_activation | 0.011588266069481741 |
| trailing_stop_delta | 0.0052230674655871666 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 614.1251262333785 |
| Selected | 614.1251262333785 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 0.0061
- **Net PnL (quote)**: 0.0372
- **Sharpe Ratio**: 0.1036
- **Max Drawdown %**: 0.0745
- **Profit Factor**: 1.0997603119692818
- **Trade Count**: 1285
- **Total Fees (quote)**: 0.0993
- **Maker Fees**: 0.0330
- **Taker Fees**: 0.0663
- **Fee Drag %**: 0.0162

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0007
- **PnL Component**: 0.0001
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0006
- **Fee Drag Component**: -0.0001
- **Inventory Component**: -0.0002
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0006**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.03 | -8.50 | 0.03 | 243 | -0.0008 | n/a |
| 1 | 0.00 | 1.67 | 0.00 | 140 | -0.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.14 | 0.04 | 219 | -0.0005 | n/a |
| 5 | -0.01 | -8.24 | 0.01 | 102 | -0.0003 | n/a |
| 6 | 0.00 | 8.29 | 0.00 | 6 | -0.1760 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **very_thin_book** (score: -0.0880)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.00 | -0.03 | 0.08 | -0.0009 |
| fees_2x | -0.01 | -0.17 | 0.08 | -0.0010 |
| latency_plus1 | 0.01 | 0.10 | 0.07 | -0.0007 |
| latency_plus2 | 0.01 | 0.10 | 0.07 | -0.0007 |
| latency_plus3 | 0.01 | 0.10 | 0.07 | -0.0007 |
| low_liquidity | 0.00 | 0.10 | 0.04 | -0.0004 |
| very_low_liquidity | 0.00 | 0.10 | 0.02 | -0.0002 |
| high_slippage | 0.00 | 0.06 | 0.07 | -0.0008 |
| extreme_slippage | -0.00 | -0.03 | 0.07 | -0.0008 |
| combined_adverse | -0.00 | -0.08 | 0.04 | -0.0004 |
| spread_widen_10bps | 0.01 | 0.11 | 0.08 | -0.0008 |
| spread_widen_25bps | 0.00 | 0.03 | 0.08 | -0.0008 |
| thin_book | -0.00 | -0.72 | 0.01 | -0.0001 |
| very_thin_book | 0.00 | 0.56 | 0.00 | -0.0880 |
| entry_spread_stress | 0.00 | 0.07 | 0.08 | -0.0008 |
| combined_market_deterioration | -0.01 | -1.24 | 0.02 | -0.0003 |
| severe_adverse | -0.00 | -0.81 | 0.01 | -0.0001 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0076)
- **Trend**: ranging (efficiency: 0.0060)
- **Best holdout score**: -0.0002 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0444 | -0.0002 | -0.01 | 0.02 | 150 |
| 1 | 0.0000 | -0.2285 | -0.93 | 0.98 | 4226 |
| 2 | 0.0000 | -0.1570 | -0.10 | 0.16 | 1346 |
| 3 | 0.0000 | -0.1977 | -0.13 | 0.17 | 934 |
| 4 | 0.0000 | -0.2330 | -0.43 | 0.48 | 3855 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 493
- **Forward-fill fraction**: 0.009509847418066781
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1040 <= 0; recent worst stress -1000.0000 < -10.0
- **Objective score**: -0.10399700376061095
- **PnL %**: 0.0010105356395840336
- **Trade count**: 24

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: -0.000722358212191616
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0004, -0.0006 |
| sell_spread_base | -0.0007, -0.0007 |
| stop_loss | -0.0008, -0.0012 |
| take_profit | -0.0007, -0.0007 |
| executor_refresh_time | -0.0081, -0.0007 |
| cooldown_time | -0.4714, -0.0007 |
| total_amount_quote | -0.0007, -0.0008 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2952019078429166
- **Max CV**: 0.6383632749738163
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1032 | 4.3592491279140475 | 5.961990549916272 | 5.132684696629485 |
| buy_spread_ratio | 0.2270 | 1.3605503742740777 | 2.655277164159705 | 2.080201196285926 |
| sell_spread_base | 0.6384 | 0.26253775162949106 | 5.984252858094034 | 3.33454854102109 |
| sell_spread_ratio | 0.2120 | 1.4416327112452452 | 2.776177976191183 | 2.1532143577195564 |
| buy_side_weight | 0.1944 | 0.24682841005896414 | 0.4682787767111432 | 0.3644180044416929 |
| amount_skew | 0.3935 | 1.0960282767763654 | 3.8107929183919347 | 2.20316112102742 |
| stop_loss | 0.1841 | 0.13571280975351463 | 0.24522418046404534 | 0.1999390187279463 |
| take_profit | 0.1608 | 0.012197658295751616 | 0.0217606460122081 | 0.016629660649550067 |
| executor_refresh_time | 0.4896 | 1386.0 | 5561.0 | 3009.3 |
| cooldown_time | 0.4855 | 222.0 | 1266.0 | 605.2 |
| total_amount_quote | 0.1587 | 508.06441658604797 | 933.7684058629212 | 808.8808946587185 |

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
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.10399700376061095 | FAIL |
| recent_pnl | >= 0 | 0.0010105356395840336 | PASS |
| recent_trades | >= 5 | 24 | PASS |
| worst_stress | > -10 | -0.0880105165929529 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.00020989116630862686 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_thin_book score=-0.0880105165929529 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | FAIL | score=-0.10399700376061095, pnl=0.0010105356395840336, trades=24, reason=recent objective score -0.1040 <= 0; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2952019078429166 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1040 <= 0; recent worst stress -1000.0000 < -10.0 |
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
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T06:55:28.050853+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 7631
