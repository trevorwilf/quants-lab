# PMM Dynamic Optimization Report: mexc_XRP-USDT_5m_sweep_v1

Generated: 2026-03-29 03:11:41 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T03:11:41.534755+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 6651 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XRP-USDT
- **interval**: 5m
- **n_candles**: 52058
- **dataset_hash**: 81b661fe4311fcdb64cb7cf524ffa0cf841c36f8d13b7518af96f5137fc07117
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 931.1899195989268
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.0803885333146566 |
| buy_n_levels | 5 |
| buy_side_weight | 0.28415138363208853 |
| buy_spread_base | 4.028056595573287 |
| buy_spread_ratio | 2.2834577874854243 |
| cooldown_time | 333 |
| executor_refresh_time | 1929 |
| macd_fast | 26 |
| macd_signal | 26 |
| macd_slow | 28 |
| natr_length | 8 |
| sell_n_levels | 5 |
| sell_spread_base | 0.26994074482751235 |
| sell_spread_ratio | 1.268738506025901 |
| stop_loss | 0.10251988168873422 |
| take_profit | 0.005546187386469495 |
| time_limit | 139326 |
| total_amount_quote | 931.1899195989268 |
| trailing_stop_activation | 0.015854478859077297 |
| trailing_stop_delta | 0.0027673653314896104 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 931.1899195989268 |
| Selected | 931.1899195989268 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3.0225
- **Net PnL (quote)**: 28.1453
- **Sharpe Ratio**: 2.6543
- **Max Drawdown %**: 0.6380
- **Profit Factor**: 1.7029532418526303
- **Trade Count**: 1132
- **Total Fees (quote)**: 4.6460
- **Maker Fees**: 4.2602
- **Taker Fees**: 0.3857
- **Fee Drag %**: 0.4989

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0128
- **PnL Component**: 0.0298
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0048
- **Fee Drag Component**: -0.0025
- **Inventory Component**: -0.0096
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0041**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.16 | 5.46 | 0.14 | 157 | -0.0040 | n/a |
| 1 | 0.04 | 1.40 | 0.16 | 94 | -0.0043 | n/a |
| 2 | 0.12 | 7.52 | 0.05 | 99 | -0.0039 | n/a |
| 3 | 0.02 | 2.71 | 0.04 | 62 | -0.0035 | n/a |
| 4 | 0.34 | 7.88 | 0.08 | 130 | -0.0037 | n/a |
| 5 | 0.02 | 0.58 | 0.17 | 101 | -0.0045 | n/a |
| 6 | -0.00 | -0.03 | 0.05 | 73 | -0.0021 | n/a |
| 7 | 0.09 | 4.41 | 0.06 | 42 | -0.0332 | n/a |
| 8 | 0.06 | 6.76 | 0.02 | 59 | -0.0015 | n/a |

## Stress Test Results

Worst Scenario: **thin_book** (score: -0.0627)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2.77 | 2.44 | 0.64 | 0.0091 |
| fees_2x | 2.52 | 2.23 | 0.64 | 0.0054 |
| latency_plus1 | 2.84 | 2.38 | 0.72 | 0.0100 |
| latency_plus2 | 2.35 | 2.54 | 0.35 | 0.0099 |
| latency_plus3 | 0.23 | 0.54 | 0.52 | -0.0114 |
| low_liquidity | 3.02 | 2.65 | 0.64 | 0.0128 |
| very_low_liquidity | 3.02 | 2.65 | 0.64 | 0.0128 |
| high_slippage | 2.92 | 2.57 | 0.64 | 0.0118 |
| extreme_slippage | 2.71 | 2.39 | 0.64 | 0.0097 |
| combined_adverse | 2.50 | 2.10 | 0.73 | 0.0055 |
| spread_widen_10bps | 2.03 | 1.80 | 0.69 | 0.0043 |
| spread_widen_25bps | 1.57 | 1.38 | 0.89 | 0.0010 |
| thin_book | -2.85 | -1.73 | 3.69 | -0.0627 |
| very_thin_book | -2.61 | -1.71 | 2.81 | -0.0539 |
| entry_spread_stress | 1.80 | 1.60 | 0.71 | 0.0030 |
| combined_market_deterioration | -1.08 | -2.38 | 1.26 | -0.0296 |
| severe_adverse | -1.27 | -3.95 | 1.33 | -0.0288 |

## Holdout Validation

- **Holdout bars**: 8806
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0039)
- **Trend**: ranging (efficiency: 0.0190)
- **Best holdout score**: -0.0026 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0250 | -0.0051 | -0.04 | 0.17 | 300 |
| 1 | -0.0015 | -0.0026 | 0.18 | 0.16 | 279 |
| 2 | -0.0022 | -0.0056 | 0.82 | 0.38 | 337 |
| 3 | -0.0025 | -0.0052 | 1.29 | 0.78 | 323 |
| 4 | -0.0026 | -0.0134 | -0.19 | 0.52 | 292 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52058
- **Expected rows**: 52098
- **Missing rows**: 40
- **Forward-fill count**: 362
- **Forward-fill fraction**: 0.006953782319720312
- **Longest gap (seconds)**: 7500

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0100 <= 0; recent PnL -0.0445% < 0
- **Objective score**: -0.00999576458424045
- **PnL %**: -0.044490828442433905
- **Trade count**: 118

## Sensitivity Analysis

- **Sensitivity penalty**: 0.8571428571428571
- **Baseline score**: -0.002746541636182289
- **Sign flips**: 1
- **Collapse count**: 11
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0343, -0.0844 |
| sell_spread_base | -0.0116, -0.0114 |
| stop_loss | -0.0235, -0.0043 |
| take_profit | -0.0057, -0.0162 |
| executor_refresh_time | -0.0177, -0.0607 |
| cooldown_time | -0.0027, -0.0166 |
| total_amount_quote | -0.0027, -0.0103 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3765442768998357
- **Max CV**: 0.8031462655273973
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1585 | 2.69616626652784 | 4.437176952909241 | 3.6559168424574318 |
| buy_spread_ratio | 0.1440 | 1.7204323049581338 | 2.815506804605653 | 2.1823495319172905 |
| sell_spread_base | 0.5909 | 0.203391982042458 | 0.713093493961111 | 0.26646459542760587 |
| sell_spread_ratio | 0.2093 | 1.215521389490216 | 2.2968344441797286 | 1.659359224286779 |
| buy_side_weight | 0.3423 | 0.2104778298558214 | 0.6099683207670838 | 0.3551242179135453 |
| amount_skew | 0.1246 | 2.7877087913043668 | 3.8862023176971623 | 3.2425472139710294 |
| stop_loss | 0.4538 | 0.03496714854346902 | 0.20560352315274139 | 0.11015637673449763 |
| take_profit | 0.8031 | 0.00512309698796821 | 0.06348924464314645 | 0.023398274388984078 |
| executor_refresh_time | 0.7270 | 429.0 | 2993.0 | 1190.5 |
| cooldown_time | 0.4967 | 102.0 | 568.0 | 365.2 |
| total_amount_quote | 0.0917 | 728.9347666274261 | 983.4679102469572 | 887.4591788442665 |

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
| recent_objective | > 0 | -0.00999576458424045 | FAIL |
| recent_pnl | >= 0 | -0.044490828442433905 | FAIL |
| recent_trades | >= 5 | 118 | PASS |
| worst_stress | > -10 | -0.06274722643320371 | PASS |
| sensitivity_penalty | < 0.50 | 0.8571428571428571 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.005090086828333465 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=thin_book score=-0.06274722643320371 |
| sensitivity | FAIL | penalty=0.8571428571428571 |
| recent_28d | FAIL | score=-0.00999576458424045, pnl=-0.044490828442433905, trades=118, reason=recent objective score -0.0100 <= 0; recent PnL -0.0445% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3765442768998357 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52058 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0100 <= 0; recent PnL -0.0445% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35227
- **Holdout bars**: 8806
- **Recent 28d bars**: 8025

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T03:11:41.534755+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 6651
