# PMM Dynamic Optimization Report: mexc_ADA-USDT_5m_sweep_v1

Generated: 2026-03-28 06:01:57 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T06:01:57.370977+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 4603 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ADA-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 0f7ce3af0e96db45aaf6d46c0a6b9e7c1c8b87d97a0168d7973a321e45ebb1d4
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 883.5263103469186
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.158838567206081 |
| buy_n_levels | 8 |
| buy_side_weight | 0.2694857436533251 |
| buy_spread_base | 0.5656347209882555 |
| buy_spread_ratio | 2.6705507891248472 |
| cooldown_time | 1653 |
| executor_refresh_time | 1425 |
| macd_fast | 22 |
| macd_signal | 10 |
| macd_slow | 77 |
| natr_length | 39 |
| sell_n_levels | 7 |
| sell_spread_base | 1.5894565237711247 |
| sell_spread_ratio | 2.850750971071401 |
| stop_loss | 0.011787876755451622 |
| take_profit | 0.007558857629228513 |
| time_limit | 160912 |
| total_amount_quote | 883.5263103469186 |
| trailing_stop_activation | 0.0006165803041351808 |
| trailing_stop_delta | 0.0010272066367690523 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 883.5263103469186 |
| Selected | 883.5263103469186 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 0.4752
- **Net PnL (quote)**: 4.1982
- **Sharpe Ratio**: 1.3017
- **Max Drawdown %**: 0.3450
- **Profit Factor**: 1.1717623454710298
- **Trade Count**: 2005
- **Total Fees (quote)**: 4.8761
- **Maker Fees**: 2.4372
- **Taker Fees**: 2.4389
- **Fee Drag %**: 0.5519

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0023
- **PnL Component**: 0.0047
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0026
- **Fee Drag Component**: -0.0028
- **Inventory Component**: -0.0017
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0015**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.10 | 2.46 | 0.19 | 183 | -0.0025 | n/a |
| 1 | -0.17 | -5.06 | 0.24 | 85 | -0.0037 | n/a |
| 2 | 0.23 | 6.08 | 0.09 | 130 | 0.0013 | n/a |
| 3 | 0.17 | 7.47 | 0.03 | 80 | 0.0013 | n/a |
| 4 | -0.15 | -4.32 | 0.21 | 125 | -0.0050 | n/a |
| 5 | 0.25 | 5.73 | 0.10 | 118 | -0.0003 | n/a |
| 6 | 0.06 | 2.79 | 0.11 | 107 | -0.0005 | n/a |
| 7 | 0.19 | 12.77 | 0.03 | 90 | 0.0015 | n/a |
| 8 | -0.03 | -3.90 | 0.05 | 70 | -0.0152 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1525)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 0.20 | 0.55 | 0.35 | -0.0065 |
| fees_2x | -0.08 | -0.20 | 0.37 | -0.0108 |
| latency_plus1 | -0.73 | -1.46 | 0.84 | -0.0207 |
| latency_plus2 | -0.63 | -1.34 | 0.74 | -0.0172 |
| latency_plus3 | -1.45 | -3.23 | 1.52 | -0.0314 |
| low_liquidity | 0.48 | 1.30 | 0.35 | -0.0023 |
| very_low_liquidity | 0.48 | 1.30 | 0.35 | -0.0023 |
| high_slippage | -0.22 | -0.59 | 0.38 | -0.0095 |
| extreme_slippage | -1.60 | -4.44 | 1.60 | -0.0325 |
| combined_adverse | -1.82 | -3.69 | 1.90 | -0.0595 |
| spread_widen_10bps | -1.92 | -2.77 | 2.03 | -0.0443 |
| spread_widen_25bps | -4.50 | -5.22 | 4.61 | -0.1084 |
| thin_book | -1.47 | -0.54 | 3.42 | -0.0475 |
| very_thin_book | -1.51 | -0.32 | 5.59 | -0.0711 |
| entry_spread_stress | -2.64 | -3.73 | 2.79 | -0.0625 |
| combined_market_deterioration | -2.94 | -0.64 | 5.61 | -0.1207 |
| severe_adverse | -3.29 | -0.71 | 5.83 | -0.1525 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0039)
- **Trend**: ranging (efficiency: 0.0167)
- **Best holdout score**: 0.0327 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0774 | 0.0036 | 0.49 | 0.11 | 233 |
| 1 | 0.0039 | 0.0327 | 5.15 | 1.78 | 299 |
| 2 | 0.0028 | 0.0018 | 0.69 | 0.53 | 161 |
| 3 | 0.0027 | 0.0076 | 1.01 | 0.21 | 194 |
| 4 | 0.0024 | 0.0258 | 3.69 | 1.01 | 219 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 9
- **Forward-fill fraction**: 0.0001736077621959453
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0062 <= 0; recent PnL -0.1877% < 0
- **Objective score**: -0.006190802842577675
- **PnL %**: -0.18766261976739304
- **Trade count**: 189

## Sensitivity Analysis

- **Sensitivity penalty**: 0.6428571428571429
- **Baseline score**: -0.00018456174652994645
- **Sign flips**: 4
- **Collapse count**: 5
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0038, 0.0008 |
| sell_spread_base | -0.0005, 0.0007 |
| stop_loss | -0.0005, 0.0008 |
| take_profit | -0.0002, -0.0002 |
| executor_refresh_time | -0.0104, -0.0002 |
| cooldown_time | -0.0040, -0.0086 |
| total_amount_quote | -0.0002, -0.0002 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3699450989390366
- **Max CV**: 1.1290070352085406
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3628 | 0.39392594053017227 | 1.1279886285328342 | 0.7626530556076883 |
| buy_spread_ratio | 0.1349 | 1.4400141478529025 | 2.4053719457818703 | 2.0818168825344534 |
| sell_spread_base | 0.6181 | 0.20601828685316037 | 4.267161215286189 | 2.3279929051008446 |
| sell_spread_ratio | 0.2481 | 1.5031494315782965 | 2.8440500788663066 | 2.208739613158463 |
| buy_side_weight | 0.1777 | 0.3674736715574002 | 0.7808674780704477 | 0.6662443382771133 |
| amount_skew | 0.0928 | 2.1898895943928274 | 3.116753719901209 | 2.6270372700158435 |
| stop_loss | 0.2367 | 0.010145576879012989 | 0.019967572559771524 | 0.014012615946723216 |
| take_profit | 1.1290 | 0.005210624871460297 | 0.10646709530908811 | 0.03332780375592086 |
| executor_refresh_time | 0.5972 | 1305.0 | 9335.0 | 4473.4 |
| cooldown_time | 0.3210 | 1714.0 | 5132.0 | 3471.8 |
| total_amount_quote | 0.1510 | 619.7039533644662 | 998.1390191285202 | 808.0296912768256 |

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
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.006190802842577675 | FAIL |
| recent_pnl | >= 0 | -0.18766261976739304 | FAIL |
| recent_trades | >= 5 | 189 | PASS |
| worst_stress | > -10 | -0.15251789322399248 | PASS |
| sensitivity_penalty | < 0.50 | 0.6428571428571429 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0036 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.15251789322399248 |
| sensitivity | FAIL | penalty=0.6428571428571429 |
| recent_28d | FAIL | score=-0.006190802842577675, pnl=-0.18766261976739304, trades=189, reason=recent objective score -0.0062 <= 0; recent PnL -0.1877% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3699450989390366 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0062 <= 0; recent PnL -0.1877% < 0 |
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
- **run_timestamp**: 2026-03-28T06:01:57.370977+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 4603
