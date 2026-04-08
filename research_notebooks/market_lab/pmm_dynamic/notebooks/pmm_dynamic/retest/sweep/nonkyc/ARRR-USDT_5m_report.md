# PMM Dynamic Optimization Report: nonkyc_ARRR-USDT_5m_retest_20260408

Generated: 2026-04-08 11:37:10 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T11:37:10.993153+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 8613 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-USDT
- **interval**: 5m
- **n_candles**: 51863
- **dataset_hash**: 5c294b353325b056b101525771ab8696623955f4a3fdca36d4e980d295625fa5
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 58.343781276227304
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.6443943332278232 |
| buy_n_levels | 7 |
| buy_side_weight | 0.6238209848680198 |
| buy_spread_base | 2.9965235218995008 |
| buy_spread_ratio | 1.2090858967188662 |
| cooldown_time | 167 |
| executor_refresh_time | 1851 |
| macd_fast | 34 |
| macd_signal | 10 |
| macd_slow | 36 |
| natr_length | 44 |
| sell_n_levels | 7 |
| sell_spread_base | 1.2817527234909962 |
| sell_spread_ratio | 1.7195609154611278 |
| stop_loss | 0.1183408332856209 |
| take_profit | 0.005651554953596211 |
| time_limit | 16000 |
| total_amount_quote | 58.343781276227304 |
| trailing_stop_activation | 0.013902414430535175 |
| trailing_stop_delta | 0.0014147586622226612 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 58.343781276227304 |
| Selected | 58.343781276227304 |

> **WARNING**: Selected quote is within 5% of search minimum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 341.3248
- **Net PnL (quote)**: 199.1418
- **Sharpe Ratio**: 6.6976
- **Max Drawdown %**: 12.1794
- **Profit Factor**: 2.573041904805742
- **Trade Count**: 2320
- **Total Fees (quote)**: 56.8991
- **Maker Fees**: 30.5602
- **Taker Fees**: 26.3388
- **Fee Drag %**: 97.5238

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.8379
- **PnL Component**: 1.4846
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0913
- **Fee Drag Component**: -0.4876
- **Inventory Component**: -0.0654
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.0838**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 35.15 | 17.12 | 2.23 | 81 | 0.2508 | n/a |
| 1 | 21.93 | 16.10 | 2.63 | 73 | 0.1513 | n/a |
| 2 | 7.05 | 9.96 | 1.01 | 29 | -0.0335 | n/a |
| 3 | 24.03 | 9.06 | 5.19 | 64 | 0.1509 | n/a |
| 4 | 26.68 | 11.66 | 9.24 | 96 | 0.1288 | n/a |
| 5 | 17.88 | 14.08 | 2.32 | 103 | 0.1087 | n/a |
| 6 | 0.78 | 1.56 | 2.37 | 47 | -0.0394 | n/a |
| 7 | -2.23 | -3.19 | 3.26 | 36 | -0.1920 | n/a |
| 8 | 11.19 | 7.83 | 2.87 | 78 | 0.0589 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -1.4079)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 292.46 | 6.04 | 13.30 | 0.4614 |
| fees_2x | 243.61 | 5.33 | 14.74 | 0.0668 |
| latency_plus1 | 275.48 | 5.35 | 16.37 | 0.5830 |
| latency_plus2 | 248.90 | 4.79 | 16.15 | 0.5008 |
| latency_plus3 | 204.86 | 4.38 | 17.63 | 0.3682 |
| low_liquidity | 283.46 | 5.24 | 22.83 | 0.5257 |
| very_low_liquidity | 262.00 | 5.28 | 24.31 | 0.4986 |
| high_slippage | 330.01 | 6.55 | 12.41 | 0.8087 |
| extreme_slippage | 307.40 | 6.26 | 12.92 | 0.7478 |
| combined_adverse | 145.74 | 3.12 | 31.05 | -0.2252 |
| spread_widen_10bps | 351.85 | 6.33 | 14.98 | 0.7679 |
| spread_widen_25bps | 300.86 | 4.99 | 24.58 | 0.4814 |
| thin_book | 130.54 | 5.07 | 11.66 | 0.4643 |
| very_thin_book | 16.88 | 1.26 | 16.23 | -0.1389 |
| entry_spread_stress | 359.63 | 6.19 | 15.11 | 0.7498 |
| combined_market_deterioration | 135.83 | 3.56 | 27.79 | -0.1280 |
| severe_adverse | -40.50 | -0.60 | 52.23 | -1.4079 |

## Holdout Validation

- **Holdout bars**: 8759
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0076)
- **Trend**: ranging (efficiency: 0.0042)
- **Best holdout score**: 0.1699 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.2850 | -0.0426 | 2.99 | 4.17 | 114 |
| 1 | 0.1562 | -0.0322 | 29.84 | 4.96 | 142 |
| 2 | 0.1556 | 0.1699 | 115.18 | 8.00 | 785 |
| 3 | 0.1542 | -0.2220 | 42.42 | 13.40 | 659 |
| 4 | 0.1490 | 0.0588 | 28.63 | 3.36 | 317 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51863
- **Expected rows**: 51863
- **Missing rows**: 0
- **Forward-fill count**: 583
- **Forward-fill fraction**: 0.011241154580336657
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.14104467724343064
- **PnL %**: 24.188514203317297
- **Trade count**: 151

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.09681625868448225
- **PnL %**: 16.468949246098763
- **Trade count**: 76

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0549 <= 0
- **Objective score**: -0.054945416859438156
- **PnL %**: 2.9473721464495877
- **Trade count**: 36

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: 0.8265562126569848
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.8809, 0.4093 |
| sell_spread_base | 0.9247, 0.8093 |
| stop_loss | 0.8508, 0.7820 |
| take_profit | 0.7959, 0.7616 |
| executor_refresh_time | 0.8266, 0.7287 |
| cooldown_time | 0.8266, 0.8266 |
| total_amount_quote | 0.6812, 0.8485 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5810431626421942
- **Max CV**: 1.345044865219136
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew
- **Scattered params**: sell_spread_base, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1459 | 1.7959831243084257 | 2.879044918232065 | 2.4044190059232973 |
| buy_spread_ratio | 0.1990 | 1.2173254924279353 | 2.2434228223086987 | 1.576906466583706 |
| sell_spread_base | 0.9484 | 0.25516552479988164 | 3.112279171379599 | 0.9101715125824221 |
| sell_spread_ratio | 0.2669 | 1.243242155589134 | 2.962902655731959 | 1.8781149692419696 |
| buy_side_weight | 0.1555 | 0.4701175039021613 | 0.7612155554697716 | 0.6605710329572856 |
| amount_skew | 0.1777 | 2.2140196357497794 | 3.7898697119951565 | 3.080750294584871 |
| stop_loss | 0.5581 | 0.04742313922225405 | 0.24024190321531816 | 0.12024226263636754 |
| take_profit | 0.7473 | 0.0054136562505477685 | 0.03633411773660375 | 0.014376842427357789 |
| executor_refresh_time | 1.1433 | 319.0 | 11359.0 | 3210.8 |
| cooldown_time | 1.3450 | 67.0 | 3956.0 | 920.9 |
| total_amount_quote | 0.7044 | 31.975639119262397 | 215.3344744893322 | 78.69670385313626 |

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
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.14104467724343064 | PASS |
| recent_pnl | >= 0 | 24.188514203317297 | PASS |
| recent_trades | >= 5 | 151 | PASS |
| worst_stress | > -10 | -1.4078527082078163 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.04261515370888638 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-1.4078527082078163 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | PASS | score=0.14104467724343064, pnl=24.188514203317297, trades=151, reason= |
| recent_14d_info | PASS | informational only; score=0.09681625868448225, pnl=16.468949246098763, trades=76, reason= |
| recent_7d_info | FAIL | informational only; score=-0.054945416859438156, pnl=2.9473721464495877, trades=36, reason=recent objective score -0.0549 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5810431626421942 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51863 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0549 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51863
- **Pre-release bars**: 43798
- **Dev bars**: 35039
- **Holdout bars**: 8759
- **Recent 28d bars**: 8065
- **Recent window start**: 1773214800

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T11:37:10.993153+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 8613
