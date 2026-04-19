# PMM Dynamic Optimization Report: mexc_ASTER-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 07:53:09 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T07:53:09.901609+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 1492 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ASTER-USDT
- **interval**: 5m
- **n_candles**: 51638
- **dataset_hash**: e45fd8eb1018b5279e2487594ddecee8242a8e245dafe39428b8329849fd7db8
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 469.9966666129126
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 27 |
| bb_length | 30 |
| bb_std | 2.4535917955494715 |
| bbp_entry_threshold | 0.256658887195257 |
| cooldown_time | 12814 |
| max_atr_pct_for_entry | 0.0833625204684607 |
| min_volume_quantile | 0.27899842484579546 |
| rsi_entry_threshold | 42.969896851602805 |
| rsi_length | 28 |
| stop_loss | 0.04948070697993337 |
| take_profit | 0.02255631967535611 |
| take_profit_order_type | LIMIT |
| time_limit | 325617 |
| total_amount_quote | 469.9966666129126 |
| trailing_stop_activation | 0.001200131422739346 |
| trailing_stop_delta | 0.002629505203066353 |
| trend_ema_length | 352 |
| use_trend_filter | False |
| volume_filter_window | 337 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 469.9966666129126 |
| Selected | 469.9966666129126 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 40.4707
- **Net PnL (quote)**: 190.2107
- **Sharpe Ratio**: 3.1368
- **Max Drawdown %**: 9.2773
- **Profit Factor**: 2.997736681020566
- **Trade Count**: 129
- **Total Fees (quote)**: 23.5363
- **Maker Fees**: 11.7468
- **Taker Fees**: 11.7895
- **Fee Drag %**: 5.0078

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.2447
- **PnL Component**: 0.3398
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0696
- **Fee Drag Component**: -0.0250
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1550**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 4.71 | 7.89 | 2.07 | 14 | -0.1164 | n/a |
| 1 | -5.03 | -10.86 | 5.03 | 2 | -1000.0000 | n/a |
| 2 | -2.21 | -6.86 | 2.93 | 2 | -1000.0000 | n/a |
| 3 | 1.36 | 3.53 | 1.34 | 12 | -0.1508 | n/a |
| 4 | 3.92 | 6.67 | 1.94 | 11 | -0.1344 | n/a |
| 5 | 3.47 | 5.68 | 1.80 | 16 | -0.1190 | n/a |
| 6 | 0.27 | 0.96 | 0.64 | 6 | -0.1792 | n/a |
| 7 | -1.24 | -4.43 | 1.36 | 3 | -1000.0000 | n/a |
| 8 | -0.01 | -0.38 | 0.10 | 5 | -0.2014 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 37.97 | 2.97 | 9.66 | 0.2113 |
| fees_2x | 35.46 | 2.80 | 10.05 | 0.1775 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 40.40 | 3.13 | 9.28 | 0.2443 |
| very_low_liquidity | 40.87 | 3.16 | 9.23 | 0.2478 |
| high_slippage | 34.20 | 2.72 | 10.23 | 0.1919 |
| extreme_slippage | 22.31 | 1.90 | 12.18 | 0.0845 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 38.71 | 2.96 | 8.45 | 0.2384 |
| spread_widen_25bps | 30.07 | 2.33 | 13.13 | 0.1390 |
| thin_book | 8.47 | 2.01 | 7.19 | 0.0177 |
| very_thin_book | -2.29 | -1.14 | 4.90 | -0.2255 |
| entry_spread_stress | 38.37 | 2.92 | 8.35 | 0.2366 |
| combined_market_deterioration | -2.13 | -1.46 | 5.02 | -0.2180 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0027)
- **Trend**: ranging (efficiency: 0.0016)
- **Best holdout score**: -0.0936 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.8777 | -0.1445 | 0.29 | 3.16 | 20 |
| 1 | -0.1034 | -0.0936 | 3.62 | 2.20 | 23 |
| 2 | -0.1128 | -0.1194 | -0.50 | 1.90 | 26 |
| 3 | -0.1148 | -0.1072 | 4.69 | 1.84 | 16 |
| 4 | -0.1153 | -0.1466 | 1.81 | 1.86 | 13 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51638
- **Expected rows**: 51841
- **Missing rows**: 203
- **Forward-fill count**: 77
- **Forward-fill fraction**: 0.001491149928347341
- **Longest gap (seconds)**: 15900

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1759 <= 0
- **Objective score**: -0.17588720311525005
- **PnL %**: 0.2898151810649109
- **Trade count**: 7

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3158 <= 0; recent PnL -0.0147% < 0
- **Objective score**: -0.3157947928335183
- **PnL %**: -0.014671009098014219
- **Trade count**: 8

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -0.0009% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -0.0008977838511756805
- **Trade count**: 2

## Sensitivity Analysis

- **Sensitivity penalty**: 0.15384615384615385
- **Baseline score**: 0.2545545306270306
- **Sign flips**: 2
- **Collapse count**: 2
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | 0.2593, 0.2653 |
| bb_std | 0.2855, 0.2571 |
| bbp_entry_threshold | 0.2612, 0.2851 |
| rsi_length | 0.1434, 0.2354 |
| rsi_entry_threshold | -1000.0000, -0.2086 |
| trend_ema_length | 0.2546, 0.2546 |
| max_atr_pct_for_entry | 0.2546, 0.2546 |
| volume_filter_window | 0.2573, 0.2568 |
| min_volume_quantile | 0.2509, 0.2669 |
| stop_loss | 0.2316, 0.2772 |
| take_profit | 0.2546, 0.2546 |
| cooldown_time | 0.2702, 0.2091 |
| total_amount_quote | 0.2545, 0.2546 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4422768690185973
- **Max CV**: 0.8407637519775697
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3259 | 0.018015184943800316 | 0.07250983819015172 | 0.050258255119533926 |
| take_profit | 0.4012 | 0.005879756507440489 | 0.019736876775070793 | 0.011050899007883317 |
| cooldown_time | 0.8408 | 658.0 | 30542.0 | 12062.9 |
| total_amount_quote | 0.2013 | 482.90558175008493 | 986.1716973142832 | 767.0739109094993 |

## Execution Realism Assumptions

- **taker_probability**: 0.0
- **supports_post_only**: True
- **connector**: mexc
- **fill_participation_rate**: 0.1
- **latency_bars**: 1
- **slippage_bps**: 5.0
- **refresh_close_mode**: market_close

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: **FAIL**
- yaml_validates: **FAIL**
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.17588720311525005 | FAIL |
| recent_pnl | >= 0 | 0.2898151810649109 | PASS |
| recent_trades | >= 5 | 7 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.15384615384615385 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.14450077289194962 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.15384615384615385 |
| recent_28d | FAIL | score=-0.17588720311525005, pnl=0.2898151810649109, trades=7, reason=recent objective score -0.1759 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.3157947928335183, pnl=-0.014671009098014219, trades=8, reason=recent objective score -0.3158 <= 0; recent PnL -0.0147% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-0.0008977838511756805, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -0.0009% < 0; recent trades 2 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4422768690185973 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51638 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1759 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3158 <= 0; recent PnL -0.0147% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -0.0009% < 0; recent trades 2 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51638
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 7862
- **Recent window start**: 1774077600

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T07:53:09.901609+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 1492
- **validation_status**: validated_fail
