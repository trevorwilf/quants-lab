# PMM Dynamic Optimization Report: mexc_TON-USDT_5m_sweep_v1

Generated: 2026-03-28 20:49:42 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T20:49:42.551416+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 11265 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: TON-USDT
- **interval**: 5m
- **n_candles**: 51986
- **dataset_hash**: 925c492c62e018225d7dc76202ce2b6870cd6061cc64eea617dbb58376011e9f
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 678.7117765546244
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.1879106564112547 |
| buy_n_levels | 10 |
| buy_side_weight | 0.4313347787104023 |
| buy_spread_base | 2.568735665345852 |
| buy_spread_ratio | 1.942792380406064 |
| cooldown_time | 459 |
| executor_refresh_time | 8198 |
| macd_fast | 45 |
| macd_signal | 15 |
| macd_slow | 86 |
| natr_length | 30 |
| sell_n_levels | 8 |
| sell_spread_base | 3.499285071132285 |
| sell_spread_ratio | 1.3350215666973824 |
| stop_loss | 0.014313996463421075 |
| take_profit | 0.005246702649291513 |
| time_limit | 119395 |
| total_amount_quote | 678.7117765546244 |
| trailing_stop_activation | 0.0032639484218802634 |
| trailing_stop_delta | 0.0018962862326897315 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 678.7117765546244 |
| Selected | 678.7117765546244 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 1.5577
- **Net PnL (quote)**: 10.5720
- **Sharpe Ratio**: 2.2036
- **Max Drawdown %**: 0.4776
- **Profit Factor**: 1.4719828675797961
- **Trade Count**: 612
- **Total Fees (quote)**: 3.2142
- **Maker Fees**: 1.6253
- **Taker Fees**: 1.5889
- **Fee Drag %**: 0.4736

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0072
- **PnL Component**: 0.0155
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0036
- **Fee Drag Component**: -0.0024
- **Inventory Component**: -0.0023
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0028**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.22 | 4.09 | 0.16 | 81 | -0.0016 | n/a |
| 1 | 0.21 | 6.35 | 0.06 | 54 | -0.0009 | n/a |
| 2 | 0.15 | 7.71 | 0.05 | 62 | -0.0014 | n/a |
| 3 | 0.13 | 7.84 | 0.05 | 53 | -0.0016 | n/a |
| 4 | -0.21 | -7.39 | 0.23 | 62 | -0.0065 | n/a |
| 5 | -0.41 | -4.21 | 0.67 | 73 | -0.0118 | n/a |
| 6 | -0.13 | -3.71 | 0.23 | 51 | -0.0055 | n/a |
| 7 | 0.37 | 8.90 | 0.05 | 75 | 0.0007 | n/a |
| 8 | 0.00 | 0.27 | 0.07 | 44 | -0.0269 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1107)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 1.32 | 1.88 | 0.54 | 0.0032 |
| fees_2x | 1.08 | 1.55 | 0.61 | -0.0008 |
| latency_plus1 | 1.56 | 2.20 | 0.48 | 0.0071 |
| latency_plus2 | 1.64 | 2.33 | 0.48 | 0.0080 |
| latency_plus3 | 1.20 | 1.71 | 0.50 | 0.0035 |
| low_liquidity | 1.56 | 2.20 | 0.48 | 0.0072 |
| very_low_liquidity | 1.56 | 2.20 | 0.48 | 0.0072 |
| high_slippage | 0.97 | 1.41 | 0.63 | 0.0002 |
| extreme_slippage | -0.20 | -0.29 | 1.14 | -0.0152 |
| combined_adverse | 0.73 | 1.07 | 0.69 | -0.0038 |
| spread_widen_10bps | 0.49 | 0.67 | 1.34 | -0.0124 |
| spread_widen_25bps | 0.13 | 0.17 | 1.56 | -0.0149 |
| thin_book | -0.70 | -1.05 | 1.48 | -0.0222 |
| very_thin_book | -2.11 | -0.53 | 4.79 | -0.0608 |
| entry_spread_stress | 1.19 | 1.42 | 0.95 | -0.0000 |
| combined_market_deterioration | -2.49 | -5.28 | 2.58 | -0.0498 |
| severe_adverse | -2.35 | -0.18 | 9.39 | -0.1107 |

## Holdout Validation

- **Holdout bars**: 8789
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0034)
- **Trend**: ranging (efficiency: 0.0127)
- **Best holdout score**: -0.0039 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0518 | -0.0108 | -0.29 | 0.65 | 140 |
| 1 | 0.0005 | -0.0111 | 0.16 | 1.36 | 246 |
| 2 | 0.0003 | -0.0095 | -0.27 | 0.76 | 173 |
| 3 | 0.0002 | -0.0047 | 0.18 | 0.56 | 378 |
| 4 | -0.0001 | -0.0039 | 0.44 | 0.89 | 164 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51986
- **Expected rows**: 52013
- **Missing rows**: 27
- **Forward-fill count**: 108
- **Forward-fill fraction**: 0.002077482399107452
- **Longest gap (seconds)**: 8400

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0089 <= 0; recent PnL -0.1327% < 0
- **Objective score**: -0.008919007503654847
- **PnL %**: -0.1327383580704184
- **Trade count**: 136

## Sensitivity Analysis

- **Sensitivity penalty**: 0.5714285714285714
- **Baseline score**: -0.0015517973076714935
- **Sign flips**: 2
- **Collapse count**: 6
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0009, -0.0443 |
| sell_spread_base | -0.0017, -0.0015 |
| stop_loss | -0.0261, 0.0019 |
| take_profit | -0.0017, -0.0015 |
| executor_refresh_time | -0.0251, -0.0282 |
| cooldown_time | -0.0016, -0.0016 |
| total_amount_quote | -0.0235, -0.0161 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.33429458018980385
- **Max CV**: 0.7180375759969257
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3290 | 0.8406930570873759 | 3.061073376671183 | 2.114564611116324 |
| buy_spread_ratio | 0.1235 | 1.3428898507184912 | 2.048149036839737 | 1.7509399341988607 |
| sell_spread_base | 0.7180 | 0.40322623193152024 | 5.478666501433386 | 2.363576424856305 |
| sell_spread_ratio | 0.1096 | 1.2565878411117457 | 1.6962871130458979 | 1.4551107346485463 |
| buy_side_weight | 0.2164 | 0.2524239342010832 | 0.595246352064148 | 0.476630734160487 |
| amount_skew | 0.1481 | 2.1096279867470384 | 3.7207134820304204 | 2.9885035852575443 |
| stop_loss | 0.3266 | 0.010080458630606196 | 0.025335919431166237 | 0.014328106321769254 |
| take_profit | 0.6379 | 0.006582347786587026 | 0.055852993896158845 | 0.026577657263088573 |
| executor_refresh_time | 0.4499 | 1191.0 | 12413.0 | 6725.1 |
| cooldown_time | 0.4972 | 255.0 | 3784.0 | 2295.8 |
| total_amount_quote | 0.1210 | 695.7219713317578 | 983.4675354373312 | 877.8278698999227 |

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
| recent_objective | > 0 | -0.008919007503654847 | FAIL |
| recent_pnl | >= 0 | -0.1327383580704184 | FAIL |
| recent_trades | >= 5 | 136 | PASS |
| worst_stress | > -10 | -0.11074200041242331 | PASS |
| sensitivity_penalty | < 0.50 | 0.5714285714285714 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.010780277810150462 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.11074200041242331 |
| sensitivity | FAIL | penalty=0.5714285714285714 |
| recent_28d | FAIL | score=-0.008919007503654847, pnl=-0.1327383580704184, trades=136, reason=recent objective score -0.0089 <= 0; recent PnL -0.1327% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.33429458018980385 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51986 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0089 <= 0; recent PnL -0.1327% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35159
- **Holdout bars**: 8789
- **Recent 28d bars**: 8038

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T20:49:42.551416+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 11265
