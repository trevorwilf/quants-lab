# PMM Dynamic Optimization Report: mexc_ICP-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 09:15:43 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T09:15:43.146932+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 7943 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ICP-USDT
- **interval**: 5m
- **n_candles**: 51776
- **dataset_hash**: bcaa5bfaf31b517b064adc15745423369c2c07d40f73d8a15cefdbe1d4cb5879
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 959.862822142623
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 30 |
| bb_length | 145 |
| bb_std | 1.4014818492904686 |
| bbp_entry_threshold | 0.1813850126731239 |
| cooldown_time | 2119 |
| max_atr_pct_for_entry | 0.04759998711513349 |
| min_volume_quantile | 0.5326257878777502 |
| rsi_entry_threshold | 34.52140081880373 |
| rsi_length | 29 |
| stop_loss | 0.04829067347375261 |
| take_profit | 0.00839655883123538 |
| take_profit_order_type | MARKET |
| time_limit | 322452 |
| total_amount_quote | 959.862822142623 |
| trailing_stop_activation | 0.0004319394585772007 |
| trailing_stop_delta | 0.015044894643256191 |
| trend_ema_length | 194 |
| use_trend_filter | False |
| volume_filter_window | 376 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 959.862822142623 |
| Selected | 959.862822142623 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 28.1502
- **Net PnL (quote)**: 270.2032
- **Sharpe Ratio**: 3.5033
- **Max Drawdown %**: 5.1951
- **Profit Factor**: 3.6626164385786595
- **Trade Count**: 150
- **Total Fees (quote)**: 42.4157
- **Maker Fees**: 21.1766
- **Taker Fees**: 21.2391
- **Fee Drag %**: 4.4189

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1863
- **PnL Component**: 0.2480
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0390
- **Fee Drag Component**: -0.0221
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1187**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.41 | -2.67 | 3.43 | 33 | -0.1116 | n/a |
| 1 | 3.38 | 8.35 | 0.79 | 18 | -0.1029 | n/a |
| 2 | 2.38 | 4.79 | 2.10 | 20 | -0.1150 | n/a |
| 3 | -4.63 | -5.11 | 4.90 | 3 | -1000.0000 | n/a |
| 4 | 6.42 | 7.21 | 2.33 | 27 | -0.0528 | n/a |
| 5 | 0.33 | 0.61 | 3.34 | 15 | -0.1648 | n/a |
| 6 | -1.88 | -5.20 | 3.01 | 3 | -1000.0000 | n/a |
| 7 | -2.36 | -7.67 | 2.96 | 5 | -0.2271 | n/a |
| 8 | 0.06 | 0.24 | 2.01 | 30 | -0.0976 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 25.94 | 3.25 | 5.23 | 0.1575 |
| fees_2x | -1.08 | -0.25 | 4.77 | -0.1880 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 26.44 | 3.41 | 5.19 | 0.1737 |
| very_low_liquidity | 24.56 | 3.19 | 5.22 | 0.1593 |
| high_slippage | -1.21 | -0.29 | 4.78 | -0.1868 |
| extreme_slippage | -2.51 | -0.65 | 4.93 | -0.1932 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.07 | -0.25 | 4.74 | -0.1850 |
| spread_widen_25bps | -1.26 | -0.27 | 4.75 | -0.1872 |
| thin_book | 7.62 | 1.53 | 5.99 | 0.0205 |
| very_thin_book | 2.55 | 0.89 | 2.52 | -0.1249 |
| entry_spread_stress | -1.37 | -0.33 | 4.75 | -0.1882 |
| combined_market_deterioration | 12.10 | 2.04 | 7.08 | 0.0414 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0040)
- **Trend**: ranging (efficiency: 0.0030)
- **Best holdout score**: -0.2007 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9069 | -0.2071 | -1.47 | 3.04 | 8 |
| 1 | -0.0342 | -0.2348 | -3.66 | 5.31 | 11 |
| 2 | -0.0431 | -0.2007 | -1.75 | 3.31 | 11 |
| 3 | -0.0626 | -1000.0000 | -1.04 | 1.39 | 3 |
| 4 | -0.0641 | -0.2100 | -1.49 | 2.93 | 7 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51776
- **Expected rows**: 51841
- **Missing rows**: 65
- **Forward-fill count**: 213
- **Forward-fill fraction**: 0.004113875154511743
- **Longest gap (seconds)**: 19800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -1.3791% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -1.3791336295976468
- **Trade count**: 1

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2128 <= 0; recent PnL -1.7969% < 0
- **Objective score**: -0.2127734852798252
- **PnL %**: -1.7968615905151266
- **Trade count**: 9

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -1.3688% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -1.368820345434619
- **Trade count**: 1

## Sensitivity Analysis

- **Sensitivity penalty**: 0.4230769230769231
- **Baseline score**: 0.038506748823772696
- **Sign flips**: 5
- **Collapse count**: 6
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | 0.0377, 0.0385 |
| bb_std | 0.0368, 0.0385 |
| bbp_entry_threshold | 0.0385, 0.0368 |
| rsi_length | -0.2270, -0.2641 |
| rsi_entry_threshold | -0.2417, 0.0598 |
| trend_ema_length | 0.0385, 0.0385 |
| max_atr_pct_for_entry | 0.0385, 0.0385 |
| volume_filter_window | 0.0356, 0.0328 |
| min_volume_quantile | 0.0551, 0.0038 |
| stop_loss | -0.1880, 0.0767 |
| take_profit | 0.0385, 0.0385 |
| cooldown_time | 0.0385, -0.1963 |
| total_amount_quote | 0.0297, 0.0452 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.48840181110421843
- **Max CV**: 1.0628339833182328
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2086 | 0.02884552198420448 | 0.055361397258942874 | 0.039425880329589526 |
| take_profit | 0.5405 | 0.00656935665699061 | 0.041059216322659436 | 0.019528853689019743 |
| cooldown_time | 1.0628 | 1592.0 | 30870.0 | 8236.8 |
| total_amount_quote | 0.1416 | 639.9847674422941 | 952.9946244592866 | 806.3066846503698 |

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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | -1.3791336295976468 | FAIL |
| recent_trades | >= 5 | 1 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.4230769230769231 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.2070578987767026 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.4230769230769231 |
| recent_28d | FAIL | score=-1000.0, pnl=-1.3791336295976468, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -1.3791% < 0; recent trades 1 < 5 |
| recent_14d_info | FAIL | informational only; score=-0.2127734852798252, pnl=-1.7968615905151266, trades=9, reason=recent objective score -0.2128 <= 0; recent PnL -1.7969% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-1.368820345434619, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -1.3688% < 0; recent trades 1 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.48840181110421843 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51776 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -1.3791% < 0; recent trades 1 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2128 <= 0; recent PnL -1.7969% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -1.3688% < 0; recent trades 1 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51776
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8000
- **Recent window start**: 1774032000

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T09:15:43.146932+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 7943
- **validation_status**: validated_fail
