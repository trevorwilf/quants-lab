# PMM Dynamic Optimization Report: mexc_BTC-USDT_5m_sweep_v1

Generated: 2026-03-28 09:59:26 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T09:59:26.819983+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 8648 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 51838
- **dataset_hash**: fb460dea78dfed3375c25f312a86fe8cc130a2da1333cd7bf90aa6c3c9e2fcb2
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 993.245928630647
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.8732598686941344 |
| buy_n_levels | 8 |
| buy_side_weight | 0.3442878042253619 |
| buy_spread_base | 0.2527032366246473 |
| buy_spread_ratio | 1.4217911902121103 |
| cooldown_time | 366 |
| executor_refresh_time | 943 |
| macd_fast | 7 |
| macd_signal | 24 |
| macd_slow | 39 |
| natr_length | 15 |
| sell_n_levels | 7 |
| sell_spread_base | 0.25274430844920265 |
| sell_spread_ratio | 1.5070569995210883 |
| stop_loss | 0.24095163292652463 |
| take_profit | 0.026042289345758068 |
| time_limit | 171368 |
| total_amount_quote | 993.245928630647 |
| trailing_stop_activation | 0.012416105922160288 |
| trailing_stop_delta | 0.0017807963584336567 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 993.245928630647 |
| Selected | 993.245928630647 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 1633.6502
- **Net PnL (quote)**: 16226.1644
- **Sharpe Ratio**: 17.6698
- **Max Drawdown %**: 14.7464
- **Profit Factor**: 1.8904190566488273
- **Trade Count**: 25518
- **Total Fees (quote)**: 1224.1810
- **Maker Fees**: 619.7367
- **Taker Fees**: 604.4443
- **Fee Drag %**: 123.2505

## Selected Candidate Single-Run Objective

- **Raw Score**: 1.8731
- **PnL Component**: 2.8528
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1106
- **Fee Drag Component**: -0.6163
- **Inventory Component**: -0.2500
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.6047**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 176.22 | 40.41 | 6.02 | 2696 | 0.6573 | n/a |
| 1 | 227.28 | 33.84 | 4.41 | 2786 | 0.8391 | n/a |
| 2 | 190.39 | 39.66 | 4.10 | 2796 | 0.7228 | n/a |
| 3 | 59.75 | 35.01 | 2.98 | 2536 | 0.1416 | n/a |
| 4 | 53.89 | 30.41 | 4.30 | 2720 | 0.0892 | n/a |
| 5 | 182.01 | 41.86 | 6.14 | 2668 | 0.6786 | n/a |
| 6 | 203.17 | 33.73 | 9.50 | 2618 | 0.7273 | n/a |
| 7 | 145.97 | 43.83 | 5.26 | 2541 | 0.5520 | n/a |
| 8 | 121.30 | 38.61 | 3.35 | 2447 | 0.4634 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 0.7491)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 1587.51 | 17.24 | 14.31 | 1.5428 |
| fees_2x | 1545.53 | 17.02 | 14.57 | 1.2098 |
| latency_plus1 | 1390.58 | 16.62 | 13.57 | 1.7991 |
| latency_plus2 | 1143.13 | 15.15 | 13.03 | 1.6989 |
| latency_plus3 | 905.47 | 14.15 | 13.66 | 1.5494 |
| low_liquidity | 1633.65 | 17.67 | 14.75 | 1.8731 |
| very_low_liquidity | 1633.65 | 17.67 | 14.75 | 1.8731 |
| high_slippage | 1515.77 | 16.91 | 14.63 | 1.8064 |
| extreme_slippage | 1304.55 | 15.79 | 14.57 | 1.6742 |
| combined_adverse | 1244.52 | 15.46 | 13.54 | 1.4275 |
| spread_widen_10bps | 1461.72 | 16.75 | 13.98 | 1.7807 |
| spread_widen_25bps | 1305.75 | 15.53 | 14.95 | 1.6642 |
| thin_book | 1043.62 | 14.82 | 14.10 | 1.7278 |
| very_thin_book | 456.47 | 10.92 | 13.67 | 1.1877 |
| entry_spread_stress | 1425.58 | 16.42 | 14.45 | 1.7526 |
| combined_market_deterioration | 1142.08 | 14.75 | 13.80 | 1.5004 |
| severe_adverse | 365.81 | 9.04 | 15.44 | 0.7491 |

## Holdout Validation

- **Holdout bars**: 8762
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0026)
- **Trend**: ranging (efficiency: 0.0297)
- **Best holdout score**: 1.5221 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.3111 | 1.1426 | 403.70 | 11.47 | 5956 |
| 1 | 0.8219 | 1.5221 | 728.12 | 9.77 | 7389 |
| 2 | 0.7908 | 1.4948 | 659.03 | 9.09 | 7226 |
| 3 | 0.7518 | 1.4496 | 641.52 | 10.44 | 9359 |
| 4 | 0.7497 | 1.4896 | 674.12 | 11.01 | 2346 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51838
- **Expected rows**: 51878
- **Missing rows**: 40
- **Forward-fill count**: 268
- **Forward-fill fraction**: 0.00516995254446545
- **Longest gap (seconds)**: 3900

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.0041731194463284
- **PnL %**: 313.29696009630584
- **Trade count**: 5331

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.845682691037438
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.8434, 1.8486 |
| sell_spread_base | 1.8474, 1.8401 |
| stop_loss | 1.8457, 1.8457 |
| take_profit | 1.8465, 1.8468 |
| executor_refresh_time | 1.8457, 1.8677 |
| cooldown_time | 1.8457, 1.8457 |
| total_amount_quote | 1.8532, 1.8324 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.38551800779572026
- **Max CV**: 0.8729475505023525
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time
- **Scattered params**: take_profit, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3494 | 0.2157618741924353 | 0.6314818762225649 | 0.3451622306748444 |
| buy_spread_ratio | 0.1549 | 1.2010164193007766 | 2.01258115543238 | 1.4689016465263731 |
| sell_spread_base | 0.4093 | 0.20163962849312467 | 0.5535928572649467 | 0.283386972036076 |
| sell_spread_ratio | 0.1944 | 1.2486591144278094 | 2.085357698365916 | 1.6108161770647489 |
| buy_side_weight | 0.2768 | 0.28775398797898094 | 0.625384750719936 | 0.4027020465195171 |
| amount_skew | 0.2036 | 1.916544492196738 | 3.9725328986172004 | 3.2233426337754465 |
| stop_loss | 0.2862 | 0.0914927615970137 | 0.20354939284168963 | 0.14647806721800055 |
| take_profit | 0.7903 | 0.010428935347686977 | 0.1082089358427092 | 0.03902078757495272 |
| executor_refresh_time | 0.2547 | 323.0 | 696.0 | 491.3 |
| cooldown_time | 0.4481 | 68.0 | 286.0 | 162.6 |
| total_amount_quote | 0.8729 | 32.92967347972328 | 917.1391594035579 | 347.0048896475594 |

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
| recent_objective | > 0 | 1.0041731194463284 | PASS |
| recent_pnl | >= 0 | 313.29696009630584 | PASS |
| recent_trades | >= 5 | 5331 | PASS |
| worst_stress | > -10 | 0.7490562197011307 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.1426 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=0.7490562197011307 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.0041731194463284, pnl=313.29696009630584, trades=5331, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.38551800779572026 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51838 |  |
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
- **Dev bars**: 35051
- **Holdout bars**: 8762
- **Recent 28d bars**: 8025

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T09:59:26.819983+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 8648
