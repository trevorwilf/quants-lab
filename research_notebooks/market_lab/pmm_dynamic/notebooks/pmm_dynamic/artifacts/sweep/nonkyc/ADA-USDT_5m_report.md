# PMM Dynamic Optimization Report: nonkyc_ADA-USDT_5m_sweep_v1

Generated: 2026-04-08 18:29:56 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T18:29:56.726849+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 6498 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ADA-USDT
- **interval**: 5m
- **n_candles**: 51913
- **dataset_hash**: 1c911062e11fa8d80dede30de4243a7f9d355bce63121113550e664133598db7
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 836.076295158862
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.6799193732537936 |
| buy_n_levels | 7 |
| buy_side_weight | 0.28407847244800405 |
| buy_spread_base | 5.653611808192476 |
| buy_spread_ratio | 2.692420263550117 |
| cooldown_time | 5469 |
| executor_refresh_time | 14002 |
| macd_fast | 17 |
| macd_signal | 15 |
| macd_slow | 27 |
| natr_length | 32 |
| sell_n_levels | 8 |
| sell_spread_base | 0.922335490745015 |
| sell_spread_ratio | 1.3041009879338665 |
| stop_loss | 0.04041871552028129 |
| take_profit | 0.006988867087523885 |
| time_limit | 5650 |
| total_amount_quote | 836.076295158862 |
| trailing_stop_activation | 0.09441522845457115 |
| trailing_stop_delta | 0.03609526857505374 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 836.076295158862 |
| Selected | 836.076295158862 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -4.6429
- **Net PnL (quote)**: -38.8183
- **Sharpe Ratio**: -0.4772
- **Max Drawdown %**: 9.9812
- **Profit Factor**: 0.1728521953703465
- **Trade Count**: 668
- **Total Fees (quote)**: 10.8593
- **Maker Fees**: 5.4689
- **Taker Fees**: 5.3904
- **Fee Drag %**: 1.2988
- **TP Min-Notional Failures**: 5720 :warning:
  > 5720 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1481
- **PnL Component**: -0.0475
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0749
- **Fee Drag Component**: -0.0065
- **Inventory Component**: -0.0040
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0277**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.38 | -12.79 | 0.42 | 55 | -0.0236 | n/a |
| 1 | -0.32 | -7.17 | 0.38 | 61 | -0.0243 | n/a |
| 2 | -0.55 | -17.55 | 0.56 | 49 | -0.1204 | n/a |
| 3 | -0.08 | -2.95 | 0.16 | 46 | -0.0223 | n/a |
| 4 | -0.46 | -6.59 | 0.56 | 72 | -0.0174 | n/a |
| 5 | 0.00 | 0.09 | 0.11 | 80 | -0.0055 | n/a |
| 6 | -0.16 | -4.70 | 0.22 | 116 | -0.0246 | n/a |
| 7 | -0.38 | -10.83 | 0.39 | 62 | -0.1003 | n/a |
| 8 | -0.42 | -10.71 | 0.43 | 58 | -0.0873 | n/a |

## Stress Test Results

Worst Scenario: **very_low_liquidity** (score: -0.2530)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -5.29 | -0.56 | 10.00 | -0.1716 |
| fees_2x | -5.94 | -0.65 | 10.02 | -0.1895 |
| latency_plus1 | -5.38 | -0.57 | 9.98 | -0.1589 |
| latency_plus2 | -4.65 | -0.48 | 9.98 | -0.1515 |
| latency_plus3 | -4.53 | -0.46 | 9.98 | -0.1567 |
| low_liquidity | -7.04 | -0.80 | 9.98 | -0.2001 |
| very_low_liquidity | -9.92 | -1.19 | 9.99 | -0.2530 |
| high_slippage | -4.80 | -0.50 | 9.98 | -0.1546 |
| extreme_slippage | -5.13 | -0.54 | 9.99 | -0.1658 |
| combined_adverse | -7.73 | -0.89 | 10.00 | -0.2246 |
| spread_widen_10bps | -4.76 | -0.49 | 9.99 | -0.1576 |
| spread_widen_25bps | -4.83 | -0.50 | 10.01 | -0.1628 |
| thin_book | -3.67 | -11.09 | 3.69 | -0.1212 |
| very_thin_book | -3.30 | -10.51 | 3.31 | -0.1426 |
| entry_spread_stress | -4.58 | -0.47 | 10.00 | -0.1490 |
| combined_market_deterioration | -6.15 | -1.24 | 6.17 | -0.1766 |
| severe_adverse | -5.37 | -15.33 | 5.47 | -0.1618 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0030)
- **Trend**: ranging (efficiency: 0.0016)
- **Best holdout score**: -0.0543 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.2005 | -0.0543 | -0.55 | 0.58 | 207 |
| 1 | -0.0107 | -0.1730 | -2.53 | 2.53 | 1185 |
| 2 | -0.0112 | -0.1518 | -2.01 | 2.27 | 1023 |
| 3 | -0.0147 | -0.1050 | -0.97 | 1.00 | 399 |
| 4 | -0.0151 | -0.0918 | -0.92 | 1.19 | 534 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51913
- **Expected rows**: 51913
- **Missing rows**: 0
- **Forward-fill count**: 251
- **Forward-fill fraction**: 0.0048350124246335216
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0633 <= 0; recent PnL -0.5614% < 0
- **Objective score**: -0.06330562246189256
- **PnL %**: -0.5614030105936206
- **Trade count**: 374

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0734 <= 0; recent PnL -0.1617% < 0
- **Objective score**: -0.07340663960055713
- **PnL %**: -0.16170763878005395
- **Trade count**: 333

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0870 <= 0; recent PnL -0.1488% < 0
- **Objective score**: -0.08704686081731429
- **PnL %**: -0.14876397442120085
- **Trade count**: 297

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.19701954899713586
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1525, -0.2498 |
| sell_spread_base | -0.1898, -0.2154 |
| stop_loss | -0.1995, -0.1930 |
| take_profit | -0.1749, -0.2928 |
| executor_refresh_time | -0.1686, -0.2082 |
| cooldown_time | -0.1794, -0.2355 |
| total_amount_quote | -0.1806, -0.2326 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.25848083634917446
- **Max CV**: 0.9392464443670686
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1054 | 4.052959275923515 | 5.682567985671986 | 5.031086706761867 |
| buy_spread_ratio | 0.0532 | 1.8920951939770736 | 2.1839723345337676 | 2.0396632465579936 |
| sell_spread_base | 0.9392 | 0.3106494026980995 | 3.9888273507382044 | 1.4923317492405257 |
| sell_spread_ratio | 0.1923 | 1.4381439462507741 | 2.951535026363591 | 2.3419009689045955 |
| buy_side_weight | 0.2667 | 0.28321021252864276 | 0.6231059619483095 | 0.38594880784282204 |
| amount_skew | 0.1141 | 2.591478264014188 | 3.86612803775673 | 3.0798796046581223 |
| stop_loss | 0.4307 | 0.01318296473096888 | 0.04683396936525286 | 0.027064262867003232 |
| take_profit | 0.2939 | 0.005077807965545565 | 0.010955820279854783 | 0.006025726404770719 |
| executor_refresh_time | 0.2083 | 8148.0 | 14358.0 | 11354.9 |
| cooldown_time | 0.1343 | 4510.0 | 6868.0 | 5726.2 |
| total_amount_quote | 0.1050 | 648.5140865853672 | 960.7759983531785 | 866.9449903058588 |

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
| recent_objective | > 0 | -0.06330562246189256 | FAIL |
| recent_pnl | >= 0 | -0.5614030105936206 | FAIL |
| recent_trades | >= 5 | 374 | PASS |
| worst_stress | > -10 | -0.25297979508246776 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.054326074503880536 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_low_liquidity score=-0.25297979508246776 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.06330562246189256, pnl=-0.5614030105936206, trades=374, reason=recent objective score -0.0633 <= 0; recent PnL -0.5614% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.07340663960055713, pnl=-0.16170763878005395, trades=333, reason=recent objective score -0.0734 <= 0; recent PnL -0.1617% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.08704686081731429, pnl=-0.14876397442120085, trades=297, reason=recent objective score -0.0870 <= 0; recent PnL -0.1488% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.25848083634917446 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51913 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0633 <= 0; recent PnL -0.5614% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0734 <= 0; recent PnL -0.1617% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0870 <= 0; recent PnL -0.1488% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51913
- **Pre-release bars**: 43848
- **Dev bars**: 35079
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065
- **Recent window start**: 1773251100

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T18:29:56.726849+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 6498
