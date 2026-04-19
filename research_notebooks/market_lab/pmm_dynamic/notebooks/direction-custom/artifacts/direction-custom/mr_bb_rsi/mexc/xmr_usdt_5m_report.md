# PMM Dynamic Optimization Report: mexc_XMR-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 11:12:52 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T11:12:52.390943+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 7559 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 51660
- **dataset_hash**: c054d78e088e8439619be7b7e6fb3f75066b1dab256dece43dd3936d3e3cfe08
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 992.3503840183424
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 22 |
| bb_length | 22 |
| bb_std | 2.6265400503098753 |
| bbp_entry_threshold | 0.22759114610130343 |
| cooldown_time | 4867 |
| max_atr_pct_for_entry | 0.0636866936675822 |
| min_volume_quantile | 0.4173023805583736 |
| rsi_entry_threshold | 45.29985598465566 |
| rsi_length | 25 |
| stop_loss | 0.030465158202787394 |
| take_profit | 0.009121121843040706 |
| take_profit_order_type | LIMIT |
| time_limit | 336469 |
| total_amount_quote | 992.3503840183424 |
| trailing_stop_activation | 0.0027273584561177486 |
| trailing_stop_delta | 4.595776263591092e-06 |
| trend_ema_length | 218 |
| use_trend_filter | True |
| volume_filter_window | 560 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 992.3503840183424 |
| Selected | 992.3503840183424 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 28.6301
- **Net PnL (quote)**: 284.1112
- **Sharpe Ratio**: 4.1673
- **Max Drawdown %**: 4.6264
- **Profit Factor**: 2.522642986693708
- **Trade Count**: 193
- **Total Fees (quote)**: 46.8951
- **Maker Fees**: 23.4144
- **Taker Fees**: 23.4806
- **Fee Drag %**: 4.7257

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1926
- **PnL Component**: 0.2518
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0347
- **Fee Drag Component**: -0.0236
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2443**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.41 | 1.02 | 1.91 | 36 | -0.0689 | n/a |
| 1 | 2.93 | 4.61 | 1.76 | 30 | -0.0678 | n/a |
| 2 | -1.13 | -4.65 | 1.77 | 5 | -0.5239 | n/a |
| 3 | 1.41 | 2.24 | 2.45 | 10 | -0.1666 | n/a |
| 4 | -1.37 | -2.96 | 3.08 | 5 | -0.2179 | n/a |
| 5 | -1.32 | -4.74 | 1.89 | 4 | -0.3183 | n/a |
| 6 | -1.46 | -5.05 | 2.31 | 5 | -0.2131 | n/a |
| 7 | 0.65 | 1.61 | 1.68 | 29 | -0.0929 | n/a |
| 8 | -1.56 | -7.96 | 1.56 | 2 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 26.27 | 3.84 | 4.92 | 0.1601 |
| fees_2x | 23.90 | 3.51 | 5.22 | 0.1271 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 27.89 | 4.05 | 4.00 | 0.1374 |
| very_low_liquidity | 23.98 | 3.51 | 4.21 | 0.0427 |
| high_slippage | 22.71 | 3.38 | 5.36 | 0.1401 |
| extreme_slippage | 10.88 | 1.71 | 7.39 | 0.0233 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 28.00 | 3.88 | 4.70 | -0.0018 |
| spread_widen_25bps | 19.80 | 2.64 | 4.88 | -0.0938 |
| thin_book | 13.02 | 3.10 | 4.30 | 0.0799 |
| very_thin_book | 5.88 | 2.47 | 2.21 | -0.0743 |
| entry_spread_stress | 26.36 | 3.59 | 4.88 | -0.0208 |
| combined_market_deterioration | 9.30 | 1.77 | 5.67 | 0.0251 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0033)
- **Trend**: ranging (efficiency: 0.0028)
- **Best holdout score**: 0.0163 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9037 | -0.3492 | -1.40 | 1.67 | 5 |
| 1 | -0.0501 | 0.0163 | 5.33 | 2.18 | 47 |
| 2 | -0.0581 | -0.1314 | -1.58 | 2.67 | 27 |
| 3 | -0.0589 | -0.3357 | -2.02 | 2.30 | 5 |
| 4 | -0.0595 | -0.2830 | -1.10 | 1.27 | 6 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51660
- **Expected rows**: 51841
- **Missing rows**: 181
- **Forward-fill count**: 149
- **Forward-fill fraction**: 0.0028842431281455674
- **Longest gap (seconds)**: 29100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1771 <= 0; recent PnL -1.8937% < 0
- **Objective score**: -0.17712592220070608
- **PnL %**: -1.8936842155361062
- **Trade count**: 16

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0414 <= 0
- **Objective score**: -0.04143135228832998
- **PnL %**: 0.5846203349459993
- **Trade count**: 42

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1508 <= 0
- **Objective score**: -0.15082282022740884
- **PnL %**: 0.17082489363588801
- **Trade count**: 15

## Sensitivity Analysis

- **Sensitivity penalty**: 0.19230769230769232
- **Baseline score**: -0.08859194739132337
- **Sign flips**: 1
- **Collapse count**: 4
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0930, -0.0942 |
| bb_std | -0.1365, -0.0781 |
| bbp_entry_threshold | -0.0790, -0.1164 |
| rsi_length | -0.0120, -0.2315 |
| rsi_entry_threshold | -1000.0000, 0.0933 |
| trend_ema_length | -0.2318, -0.0543 |
| max_atr_pct_for_entry | -0.0886, -0.0886 |
| volume_filter_window | -0.0934, -0.0870 |
| min_volume_quantile | -0.0225, -0.0821 |
| stop_loss | -0.1038, -0.1234 |
| take_profit | -0.0886, -0.0886 |
| cooldown_time | -0.0931, -0.0907 |
| total_amount_quote | -0.0898, -0.0872 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4128889521524304
- **Max CV**: 0.7120341465622747
- **Clustered params**: take_profit, total_amount_quote
- **Scattered params**: stop_loss, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.5351 | 0.015130328481903777 | 0.05220691949490697 | 0.0288843578267592 |
| take_profit | 0.3087 | 0.0052840809296501165 | 0.011021527022319686 | 0.00776959726671034 |
| cooldown_time | 0.7120 | 930.0 | 14679.0 | 7042.0 |
| total_amount_quote | 0.0957 | 761.7746307613116 | 994.7010881391788 | 906.9804209525342 |

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
- walkforward_positive_majority: **FAIL**
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
| recent_objective | > 0 | -0.17712592220070608 | FAIL |
| recent_pnl | >= 0 | -1.8936842155361062 | FAIL |
| recent_trades | >= 5 | 16 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.19230769230769232 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.3492385554972814 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.19230769230769232 |
| recent_28d | FAIL | score=-0.17712592220070608, pnl=-1.8936842155361062, trades=16, reason=recent objective score -0.1771 <= 0; recent PnL -1.8937% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.04143135228832998, pnl=0.5846203349459993, trades=42, reason=recent objective score -0.0414 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.15082282022740884, pnl=0.17082489363588801, trades=15, reason=recent objective score -0.1508 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4128889521524304 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51660 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1771 <= 0; recent PnL -1.8937% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0414 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1508 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51660
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 7884
- **Recent window start**: 1774067700

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T11:12:52.390943+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 7559
- **validation_status**: validated_fail
