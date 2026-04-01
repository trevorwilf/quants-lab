# PMM Dynamic Optimization Report: nonkyc_ZEC-XMR_5m_sweep_v1

Generated: 2026-03-29 14:28:18 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T14:28:18.801565+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 10532 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ZEC-XMR
- **interval**: 5m
- **n_candles**: 51921
- **dataset_hash**: 1d26c822903516fc14972c94305d5531dd903ace1ff7b7fa0ff03411621c0cf8
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 830.3236866418372
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.0154182212335927 |
| buy_n_levels | 7 |
| buy_side_weight | 0.4019528096354895 |
| buy_spread_base | 5.851983592499644 |
| buy_spread_ratio | 1.3013314125508229 |
| cooldown_time | 168 |
| executor_refresh_time | 1339 |
| macd_fast | 42 |
| macd_signal | 29 |
| macd_slow | 59 |
| natr_length | 9 |
| sell_n_levels | 2 |
| sell_spread_base | 0.6020416381889544 |
| sell_spread_ratio | 1.767281484745314 |
| stop_loss | 0.14451637850376625 |
| take_profit | 0.013262606341760148 |
| time_limit | 127974 |
| total_amount_quote | 830.3236866418372 |
| trailing_stop_activation | 0.011080864844408138 |
| trailing_stop_delta | 0.0010244701843869412 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 830.3236866418372 |
| Selected | 830.3236866418372 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.0320
- **Net PnL (quote)**: -0.2661
- **Sharpe Ratio**: -2.4295
- **Max Drawdown %**: 0.0431
- **Profit Factor**: 0.5524022241966124
- **Trade Count**: 2431
- **Total Fees (quote)**: 0.0461
- **Maker Fees**: 0.0162
- **Taker Fees**: 0.0299
- **Fee Drag %**: 0.0056

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0008
- **PnL Component**: -0.0003
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0003
- **Fee Drag Component**: -0.0000
- **Inventory Component**: -0.0001
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0005**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.01 | -10.11 | 0.01 | 184 | -0.0002 | n/a |
| 1 | -0.01 | -9.51 | 0.02 | 370 | -0.0003 | n/a |
| 2 | -0.00 | -0.14 | 0.00 | 319 | -0.0002 | n/a |
| 3 | 0.00 | 6.89 | 0.00 | 1 | -1000.0000 | n/a |
| 4 | -0.01 | -4.52 | 0.01 | 496 | -0.0004 | n/a |
| 5 | 0.00 | 1.13 | 0.00 | 96 | -0.0001 | n/a |
| 6 | 0.00 | 2.61 | 0.00 | 21 | -0.1160 | n/a |
| 7 | -0.00 | -5.08 | 0.00 | 54 | -0.2650 | n/a |
| 8 | -0.00 | -1.99 | 0.00 | 37 | -0.0705 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.0009)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.03 | -2.65 | 0.05 | -0.0008 |
| fees_2x | -0.04 | -2.87 | 0.05 | -0.0009 |
| latency_plus1 | -0.03 | -2.50 | 0.04 | -0.0008 |
| latency_plus2 | -0.03 | -2.56 | 0.04 | -0.0008 |
| latency_plus3 | -0.03 | -2.61 | 0.04 | -0.0008 |
| low_liquidity | -0.02 | -2.43 | 0.02 | -0.0004 |
| very_low_liquidity | -0.01 | -2.43 | 0.01 | -0.0002 |
| high_slippage | -0.03 | -2.50 | 0.04 | -0.0008 |
| extreme_slippage | -0.03 | -2.65 | 0.05 | -0.0008 |
| combined_adverse | -0.02 | -2.79 | 0.02 | -0.0004 |
| spread_widen_10bps | -0.03 | -2.46 | 0.04 | -0.0008 |
| spread_widen_25bps | -0.03 | -2.63 | 0.05 | -0.0008 |
| thin_book | -0.00 | -0.49 | 0.00 | -0.0001 |
| very_thin_book | -0.00 | -0.62 | 0.00 | -0.0000 |
| entry_spread_stress | -0.03 | -2.58 | 0.04 | -0.0008 |
| combined_market_deterioration | -0.00 | -0.07 | 0.00 | -0.0001 |
| severe_adverse | -0.00 | -0.72 | 0.00 | -0.0000 |

## Holdout Validation

- **Holdout bars**: 8771
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0076)
- **Trend**: ranging (efficiency: 0.0054)
- **Best holdout score**: -0.0001 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0008 | -0.0592 | -0.00 | 0.00 | 137 |
| 1 | -0.0003 | -0.2643 | -0.00 | 0.00 | 107 |
| 2 | -0.0003 | -0.0001 | -0.00 | 0.00 | 431 |
| 3 | -0.0003 | -0.0592 | -0.00 | 0.00 | 137 |
| 4 | -0.0003 | -0.1011 | -0.00 | 0.00 | 110 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51921
- **Expected rows**: 51922
- **Missing rows**: 1
- **Forward-fill count**: 1813
- **Forward-fill fraction**: 0.03491843377438801
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0000 <= 0
- **Objective score**: -4.268339791798559e-05
- **PnL %**: 0.005075700382775371
- **Trade count**: 161

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.000729159026229994
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0006, -0.0010 |
| sell_spread_base | -0.0007, -0.0007 |
| stop_loss | -0.0007, -0.0008 |
| take_profit | -0.0007, -0.0007 |
| executor_refresh_time | -0.0007, -0.0007 |
| cooldown_time | -0.0007, -0.0007 |
| total_amount_quote | -0.0007, -0.0008 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.40142543494344873
- **Max CV**: 0.9384085962133712
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0717 | 4.837063975258287 | 5.987310867588516 | 5.579339691008195 |
| buy_spread_ratio | 0.3170 | 1.2157416785314843 | 2.678462864397786 | 1.6798494125049106 |
| sell_spread_base | 0.9384 | 0.20765678160679082 | 1.8528604697910678 | 0.5314949752236279 |
| sell_spread_ratio | 0.2520 | 1.3238464367338412 | 2.888515024675675 | 2.1248767296311954 |
| buy_side_weight | 0.2334 | 0.4019528096354895 | 0.7554364245269847 | 0.5597465217289482 |
| amount_skew | 0.2870 | 1.170523476698179 | 3.703001930420542 | 2.8133752803329473 |
| stop_loss | 0.2641 | 0.07614172579054274 | 0.18745633707757242 | 0.1326922706825437 |
| take_profit | 0.8393 | 0.005611958522198046 | 0.04667300870906994 | 0.017370875058274296 |
| executor_refresh_time | 0.6532 | 655.0 | 12934.0 | 7307.1 |
| cooldown_time | 0.4942 | 61.0 | 275.0 | 154.7 |
| total_amount_quote | 0.0655 | 830.3236866418372 | 993.2512100100229 | 945.6386840722382 |

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
| recent_objective | > 0 | -4.268339791798559e-05 | FAIL |
| recent_pnl | >= 0 | 0.005075700382775371 | PASS |
| recent_trades | >= 5 | 161 | PASS |
| worst_stress | > -10 | -0.0009011440848195294 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.059213908411017944 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.0009011440848195294 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-4.268339791798559e-05, pnl=0.005075700382775371, trades=161, reason=recent objective score -0.0000 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.40142543494344873 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51921 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0000 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35086
- **Holdout bars**: 8771
- **Recent 28d bars**: 8064

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T14:28:18.801565+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 10532
