# PMM Dynamic Optimization Report: nonkyc_BTC-USDT_5m_sweep_v1

Generated: 2026-03-29 07:35:26 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T07:35:26.237304+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 9191 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: a1d814eb854a88d014fd54a79ebc8726cfc9147593499f7ba1bc3560bdbbdf5d
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 789.0515066514606
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.9149362357717714 |
| buy_n_levels | 6 |
| buy_side_weight | 0.2601786317983714 |
| buy_spread_base | 4.0788199767379805 |
| buy_spread_ratio | 2.2879161825137455 |
| cooldown_time | 3625 |
| executor_refresh_time | 10442 |
| macd_fast | 28 |
| macd_signal | 15 |
| macd_slow | 87 |
| natr_length | 36 |
| sell_n_levels | 10 |
| sell_spread_base | 3.381851417242178 |
| sell_spread_ratio | 1.8560531103089932 |
| stop_loss | 0.12455924716125032 |
| take_profit | 0.005002166913019134 |
| time_limit | 91830 |
| total_amount_quote | 789.0515066514606 |
| trailing_stop_activation | 0.09651914508053097 |
| trailing_stop_delta | 0.004871687088776414 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 789.0515066514606 |
| Selected | 789.0515066514606 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 0.1109
- **Net PnL (quote)**: 0.8749
- **Sharpe Ratio**: 0.1237
- **Max Drawdown %**: 0.8813
- **Profit Factor**: 1.3445305386937045
- **Trade Count**: 578
- **Total Fees (quote)**: 8.6651
- **Maker Fees**: 7.2428
- **Taker Fees**: 1.4223
- **Fee Drag %**: 1.0982

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0214
- **PnL Component**: 0.0011
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0066
- **Fee Drag Component**: -0.0055
- **Inventory Component**: -0.0103
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0189**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.24 | -3.92 | 0.50 | 67 | -0.0166 | n/a |
| 1 | -0.02 | -0.72 | 0.17 | 60 | -0.0103 | n/a |
| 2 | -0.00 | -0.13 | 0.13 | 63 | -0.0100 | n/a |
| 3 | -0.02 | -1.08 | 0.06 | 44 | -0.0334 | n/a |
| 4 | -0.13 | -2.95 | 0.18 | 53 | -0.0264 | n/a |
| 5 | -0.23 | -4.20 | 0.31 | 57 | -0.0153 | n/a |
| 6 | 0.09 | 2.21 | 0.10 | 79 | -0.0105 | n/a |
| 7 | -0.21 | -3.33 | 0.42 | 78 | -0.0160 | n/a |
| 8 | -0.03 | -2.38 | 0.08 | 28 | -0.0942 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0581)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.44 | -0.42 | 1.19 | -0.0320 |
| fees_2x | -0.99 | -0.96 | 1.60 | -0.0434 |
| latency_plus1 | 0.75 | 0.58 | 0.88 | -0.0148 |
| latency_plus2 | 0.49 | 0.39 | 1.04 | -0.0197 |
| latency_plus3 | 0.73 | 0.56 | 0.88 | -0.0150 |
| low_liquidity | 0.11 | 0.12 | 0.88 | -0.0214 |
| very_low_liquidity | 0.11 | 0.12 | 0.88 | -0.0214 |
| high_slippage | 0.07 | 0.08 | 0.88 | -0.0219 |
| extreme_slippage | -0.02 | -0.01 | 0.88 | -0.0228 |
| combined_adverse | 0.16 | 0.14 | 1.26 | -0.0263 |
| spread_widen_10bps | 0.40 | 0.38 | 0.87 | -0.0187 |
| spread_widen_25bps | -0.39 | -0.33 | 1.57 | -0.0344 |
| thin_book | -0.33 | -0.28 | 1.44 | -0.0330 |
| very_thin_book | -1.17 | -3.60 | 1.22 | -0.0302 |
| entry_spread_stress | -0.42 | -0.39 | 1.34 | -0.0325 |
| combined_market_deterioration | 0.17 | 0.16 | 1.26 | -0.0250 |
| severe_adverse | -2.32 | -5.13 | 2.33 | -0.0581 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0028)
- **Trend**: ranging (efficiency: 0.0183)
- **Best holdout score**: -0.0216 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0397 | -0.0216 | -0.39 | 0.55 | 166 |
| 1 | -0.0091 | -0.0985 | -3.51 | 3.70 | 261 |
| 2 | -0.0093 | -0.0248 | -0.82 | 0.89 | 197 |
| 3 | -0.0098 | -0.0327 | -0.89 | 1.14 | 200 |
| 4 | -0.0098 | -0.0281 | -0.91 | 1.24 | 181 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 277
- **Forward-fill fraction**: 0.005343261125364094
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0125 <= 0; recent PnL -0.2454% < 0
- **Objective score**: -0.012536976667636462
- **PnL %**: -0.24537915536861996
- **Trade count**: 106

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: -0.04507600269290722
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1079, -0.0774 |
| sell_spread_base | -0.0352, -0.0598 |
| stop_loss | -0.0443, -0.0448 |
| take_profit | -0.0449, -0.0380 |
| executor_refresh_time | -0.0364, -0.0422 |
| cooldown_time | -0.0451, -0.0540 |
| total_amount_quote | -0.0450, -0.2006 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3469397526383198
- **Max CV**: 0.9786596923594291
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1523 | 3.526815032235788 | 5.500625171681278 | 4.525636700312286 |
| buy_spread_ratio | 0.1970 | 1.550730876385949 | 2.979132483580594 | 2.306443785070914 |
| sell_spread_base | 0.5041 | 0.44266436926632285 | 2.497788631350599 | 1.396350607380324 |
| sell_spread_ratio | 0.2514 | 1.3718221967164697 | 2.7037680483954736 | 1.737719484958106 |
| buy_side_weight | 0.3360 | 0.20131838627036833 | 0.5388753484985829 | 0.2890882410209056 |
| amount_skew | 0.1881 | 2.1844932889504474 | 3.978769381577579 | 3.2770522967728732 |
| stop_loss | 0.9787 | 0.012283597072306387 | 0.1313341566162349 | 0.046665311428132454 |
| take_profit | 0.3716 | 0.005040477528705371 | 0.012876977733053362 | 0.006389473455160485 |
| executor_refresh_time | 0.3758 | 3625.0 | 13089.0 | 9052.3 |
| cooldown_time | 0.3468 | 1209.0 | 5938.0 | 4161.4 |
| total_amount_quote | 0.1145 | 719.5813795226798 | 998.5822590095676 | 890.0038454702102 |

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
| recent_objective | > 0 | -0.012536976667636462 | FAIL |
| recent_pnl | >= 0 | -0.24537915536861996 | FAIL |
| recent_trades | >= 5 | 106 | PASS |
| worst_stress | > -10 | -0.058074935485098116 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.021552652788361625 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.058074935485098116 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | FAIL | score=-0.012536976667636462, pnl=-0.24537915536861996, trades=106, reason=recent objective score -0.0125 <= 0; recent PnL -0.2454% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3469397526383198 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0125 <= 0; recent PnL -0.2454% < 0 |
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
- **run_timestamp**: 2026-03-29T07:35:26.237304+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 9191
