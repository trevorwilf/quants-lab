# PMM Dynamic Optimization Report: mexc_ICP-USDT_5m_retest_20260408

Generated: 2026-04-08 09:38:35 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T09:38:35.059308+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 14079 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ICP-USDT
- **interval**: 5m
- **n_candles**: 51831
- **dataset_hash**: 23690b5a6ddc4e26269538caefc7e264a11fe1522ea3b462c57a6e543c8fc7da
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 745.1544116280091
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.907940842202869 |
| buy_n_levels | 8 |
| buy_side_weight | 0.7827616358563942 |
| buy_spread_base | 2.1409262490910774 |
| buy_spread_ratio | 1.373969036993535 |
| cooldown_time | 63 |
| executor_refresh_time | 2428 |
| macd_fast | 28 |
| macd_signal | 5 |
| macd_slow | 30 |
| natr_length | 31 |
| sell_n_levels | 10 |
| sell_spread_base | 3.5919027296442523 |
| sell_spread_ratio | 1.8432742890300013 |
| stop_loss | 0.011492212262946496 |
| take_profit | 0.035808962860734796 |
| time_limit | 54404 |
| total_amount_quote | 745.1544116280091 |
| trailing_stop_activation | 0.0020092547950329538 |
| trailing_stop_delta | 0.0012497661284844544 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 745.1544116280091 |
| Selected | 745.1544116280091 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 11.7358
- **Net PnL (quote)**: 87.4500
- **Sharpe Ratio**: 4.6403
- **Max Drawdown %**: 1.8604
- **Profit Factor**: 2.262513995379527
- **Trade Count**: 1765
- **Total Fees (quote)**: 10.4303
- **Maker Fees**: 5.2053
- **Taker Fees**: 5.2249
- **Fee Drag %**: 1.3997

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0864
- **PnL Component**: 0.1110
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0140
- **Fee Drag Component**: -0.0070
- **Inventory Component**: -0.0036
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0012**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.48 | -2.46 | 1.04 | 233 | -0.0156 | n/a |
| 1 | 1.61 | 6.13 | 0.31 | 213 | 0.0106 | n/a |
| 2 | 0.22 | 9.22 | 0.06 | 165 | -0.0007 | n/a |
| 3 | 0.95 | 8.92 | 0.09 | 152 | 0.0083 | n/a |
| 4 | 4.45 | 8.14 | 0.15 | 181 | 0.0398 | n/a |
| 5 | 0.99 | 6.90 | 0.47 | 201 | 0.0034 | n/a |
| 6 | 0.35 | 1.89 | 0.53 | 152 | -0.0011 | n/a |
| 7 | 0.49 | 13.81 | 0.07 | 181 | 0.0019 | n/a |
| 8 | -0.54 | -7.59 | 0.61 | 179 | -0.0127 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1053)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 11.04 | 4.37 | 1.88 | 0.0764 |
| fees_2x | 10.34 | 4.10 | 1.90 | 0.0665 |
| latency_plus1 | 6.90 | 4.25 | 1.90 | 0.0420 |
| latency_plus2 | 5.45 | 2.90 | 2.39 | 0.0247 |
| latency_plus3 | 5.22 | 4.02 | 1.08 | 0.0324 |
| low_liquidity | 11.74 | 4.64 | 1.86 | 0.0864 |
| very_low_liquidity | 11.70 | 4.63 | 1.86 | 0.0861 |
| high_slippage | 9.98 | 3.98 | 1.89 | 0.0703 |
| extreme_slippage | 6.48 | 2.64 | 1.96 | 0.0318 |
| combined_adverse | 4.51 | 2.82 | 1.94 | 0.0156 |
| spread_widen_10bps | 13.83 | 3.86 | 1.90 | 0.1046 |
| spread_widen_25bps | 11.84 | 3.30 | 1.84 | 0.0863 |
| thin_book | 0.17 | 0.13 | 1.61 | -0.0166 |
| very_thin_book | -1.33 | -1.71 | 1.66 | -0.0296 |
| entry_spread_stress | 13.48 | 3.73 | 1.92 | 0.0999 |
| combined_market_deterioration | 2.77 | 0.76 | 5.04 | -0.0223 |
| severe_adverse | -4.32 | -1.51 | 4.50 | -0.1053 |

## Holdout Validation

- **Holdout bars**: 8756
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0040)
- **Trend**: ranging (efficiency: 0.0052)
- **Best holdout score**: 0.0084 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0094 | -0.0003 | 0.71 | 0.53 | 363 |
| 1 | 0.0091 | -0.0308 | -0.38 | 0.97 | 1272 |
| 2 | 0.0091 | 0.0084 | 2.61 | 0.73 | 180 |
| 3 | 0.0086 | -0.0319 | 2.17 | 0.98 | 1489 |
| 4 | 0.0085 | -0.0214 | 2.99 | 1.29 | 435 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51831
- **Expected rows**: 51845
- **Missing rows**: 14
- **Forward-fill count**: 154
- **Forward-fill fraction**: 0.0029711948447840096
- **Longest gap (seconds)**: 1800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0127 <= 0; recent PnL -0.3172% < 0
- **Objective score**: -0.01268417943881842
- **PnL %**: -0.3171855348692444
- **Trade count**: 310

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.002510164986208626
- **PnL %**: 0.6159509123310102
- **Trade count**: 142

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0086 <= 0
- **Objective score**: -0.008603456281764187
- **PnL %**: 0.029669793703167097
- **Trade count**: 48

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: 0.08594663644206817
- **Sign flips**: 1
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1227, 0.0754 |
| sell_spread_base | 0.0863, 0.0802 |
| stop_loss | 0.0797, 0.0857 |
| take_profit | 0.0859, 0.0859 |
| executor_refresh_time | 0.0859, 0.0502 |
| cooldown_time | 0.0859, 0.0859 |
| total_amount_quote | 0.0858, 0.0858 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4582630505938939
- **Max CV**: 0.8714993529786684
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, take_profit
- **Scattered params**: sell_spread_base, amount_skew, stop_loss, executor_refresh_time, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1771 | 1.8676745003755097 | 3.289204485552501 | 2.605868837337501 |
| buy_spread_ratio | 0.1770 | 1.2188511136799343 | 2.0674377329315186 | 1.462171980037955 |
| sell_spread_base | 0.8715 | 0.24032364247754215 | 3.9581910063044687 | 1.3826158833549045 |
| sell_spread_ratio | 0.1993 | 1.4238540543814815 | 2.851507778433957 | 2.170230890834605 |
| buy_side_weight | 0.1759 | 0.49019962217273044 | 0.7940514873825993 | 0.678837436126906 |
| amount_skew | 0.5231 | 1.199778264751202 | 3.6988852279579523 | 1.8215913152879466 |
| stop_loss | 0.8131 | 0.018332916594790034 | 0.19577584494486303 | 0.06792889280396545 |
| take_profit | 0.3864 | 0.009697268606697765 | 0.033680711502688435 | 0.01956764665922975 |
| executor_refresh_time | 0.6413 | 437.0 | 3461.0 | 1605.9 |
| cooldown_time | 0.5728 | 189.0 | 895.0 | 476.7 |
| total_amount_quote | 0.5033 | 140.9527526412926 | 970.5616319952172 | 569.3158857505064 |

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
| recent_objective | > 0 | -0.01268417943881842 | FAIL |
| recent_pnl | >= 0 | -0.3171855348692444 | FAIL |
| recent_trades | >= 5 | 310 | PASS |
| worst_stress | > -10 | -0.10525512898938594 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.00026273117754904013 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.10525512898938594 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.01268417943881842, pnl=-0.3171855348692444, trades=310, reason=recent objective score -0.0127 <= 0; recent PnL -0.3172% < 0 |
| recent_14d_info | PASS | informational only; score=0.002510164986208626, pnl=0.6159509123310102, trades=142, reason= |
| recent_7d_info | FAIL | informational only; score=-0.008603456281764187, pnl=0.029669793703167097, trades=48, reason=recent objective score -0.0086 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4582630505938939 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51831 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0127 <= 0; recent PnL -0.3172% < 0 |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0086 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51831
- **Pre-release bars**: 43780
- **Dev bars**: 35024
- **Holdout bars**: 8756
- **Recent 28d bars**: 8051
- **Recent window start**: 1773213000

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T09:38:35.059308+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 14079
