# PMM Dynamic Optimization Report: mexc_DOT-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 08:38:51 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T08:38:51.989444+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 4194 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOT-USDT
- **interval**: 5m
- **n_candles**: 51840
- **dataset_hash**: 2173295c56f9aa70680f9a8eb443783f49032da25853a92073d2cb50df19fa58
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 696.2499501952425
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 17 |
| bb_length | 160 |
| bb_std | 1.6691154693266383 |
| bbp_entry_threshold | 0.39375623889655764 |
| cooldown_time | 13216 |
| max_atr_pct_for_entry | 0.0056707609312039295 |
| min_volume_quantile | 0.479360224450229 |
| rsi_entry_threshold | 43.9838735665825 |
| rsi_length | 10 |
| stop_loss | 0.029146493881511186 |
| take_profit | 0.053162796383338484 |
| take_profit_order_type | MARKET |
| time_limit | 322942 |
| total_amount_quote | 696.2499501952425 |
| trailing_stop_activation | 0.0005242795416870191 |
| trailing_stop_delta | 0.009584983926667817 |
| trend_ema_length | 144 |
| use_trend_filter | False |
| volume_filter_window | 207 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 696.2499501952425 |
| Selected | 696.2499501952425 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 10.2238
- **Net PnL (quote)**: 71.1830
- **Sharpe Ratio**: 1.6708
- **Max Drawdown %**: 7.9025
- **Profit Factor**: 1.4436342646818183
- **Trade Count**: 244
- **Total Fees (quote)**: 50.8434
- **Maker Fees**: 25.4095
- **Taker Fees**: 25.4339
- **Fee Drag %**: 7.3025

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0007
- **PnL Component**: 0.0973
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0593
- **Fee Drag Component**: -0.0365
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1422**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 3.41 | 5.22 | 1.80 | 31 | -0.0613 | n/a |
| 1 | -3.00 | -7.01 | 3.00 | 2 | -1000.0000 | n/a |
| 2 | 1.93 | 3.03 | 2.24 | 42 | -0.1145 | n/a |
| 3 | -1.88 | -2.66 | 3.02 | 10 | -0.2036 | n/a |
| 4 | 1.09 | 2.49 | 1.47 | 19 | -0.1436 | n/a |
| 5 | 1.12 | 1.49 | 3.38 | 22 | -0.1302 | n/a |
| 6 | 7.03 | 7.57 | 2.08 | 22 | -0.0636 | n/a |
| 7 | -1.38 | -2.72 | 3.01 | 17 | -0.1712 | n/a |
| 8 | 2.09 | 6.36 | 1.20 | 25 | -0.0918 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.38 | -0.64 | 2.97 | -0.1343 |
| fees_2x | -1.78 | -0.84 | 3.07 | -0.1410 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.02 | -0.47 | 2.94 | -0.1084 |
| very_low_liquidity | -1.12 | -0.53 | 2.95 | -0.0374 |
| high_slippage | -1.98 | -0.94 | 3.20 | -0.1401 |
| extreme_slippage | -1.16 | -0.68 | 3.17 | -0.1571 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.98 | -1.15 | 5.48 | -0.1087 |
| spread_widen_25bps | -1.38 | -0.54 | 3.19 | -0.1485 |
| thin_book | 4.21 | 1.11 | 6.33 | -0.0193 |
| very_thin_book | -2.30 | -1.21 | 3.00 | -0.1684 |
| entry_spread_stress | -3.42 | -1.19 | 5.57 | -0.1139 |
| combined_market_deterioration | -1.73 | -1.08 | 3.22 | -0.1774 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0041)
- **Trend**: ranging (efficiency: 0.0066)
- **Best holdout score**: 0.0314 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9996 | 0.0314 | 6.26 | 2.81 | 52 |
| 1 | -0.0266 | 0.0022 | 4.09 | 2.73 | 48 |
| 2 | -0.0340 | -0.0396 | 3.43 | 2.96 | 39 |
| 3 | -0.0353 | -0.1837 | -1.29 | 2.22 | 12 |
| 4 | -0.0384 | -0.2121 | -3.90 | 4.59 | 16 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51840
- **Expected rows**: 51841
- **Missing rows**: 1
- **Forward-fill count**: 22
- **Forward-fill fraction**: 0.0004243827160493827
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.02794333067401319
- **PnL %**: 4.7908037446789296
- **Trade count**: 55

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1926 <= 0; recent PnL -1.0491% < 0
- **Objective score**: -0.19257582211773772
- **PnL %**: -1.0490544181982155
- **Trade count**: 7

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2322 <= 0; recent PnL -2.7684% < 0
- **Objective score**: -0.23224566500627683
- **PnL %**: -2.7683649456434725
- **Trade count**: 5

## Sensitivity Analysis

- **Sensitivity penalty**: 1.0769230769230769
- **Baseline score**: 0.08431247475780343
- **Sign flips**: 14
- **Collapse count**: 14
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -1000.0000, -0.1368 |
| bb_std | -0.1346, -0.1145 |
| bbp_entry_threshold | -0.1360, -0.1516 |
| rsi_length | 0.0853, 0.0958 |
| rsi_entry_threshold | -0.0475, -0.2488 |
| trend_ema_length | 0.0843, 0.0843 |
| max_atr_pct_for_entry | 0.0908, 0.0622 |
| volume_filter_window | -0.1207, -0.1340 |
| min_volume_quantile | -0.0215, 0.0426 |
| stop_loss | -0.1330, -0.1759 |
| take_profit | 0.0843, 0.0843 |
| cooldown_time | 0.1360, -0.1436 |
| total_amount_quote | 0.0817, 0.0849 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.32137376290059105
- **Max CV**: 0.6558022426958792
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2550 | 0.023402316380123554 | 0.05382281964506783 | 0.03663156409474693 |
| take_profit | 0.2408 | 0.029502753414567467 | 0.05629236041231911 | 0.04219524790979419 |
| cooldown_time | 0.6558 | 844.0 | 18678.0 | 9885.0 |
| total_amount_quote | 0.1339 | 587.1322919812819 | 995.5746527991926 | 910.9972590059531 |

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
- holdout_passed: PASS
- holdout_no_collapse: PASS
- sensitivity_stable: **FAIL**
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.02794333067401319 | PASS |
| recent_pnl | >= 0 | 4.7908037446789296 | PASS |
| recent_trades | >= 5 | 55 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 1.0769230769230769 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | PASS | score=0.0314 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=1.0769230769230769 |
| recent_28d | PASS | score=0.02794333067401319, pnl=4.7908037446789296, trades=55, reason= |
| recent_14d_info | FAIL | informational only; score=-0.19257582211773772, pnl=-1.0490544181982155, trades=7, reason=recent objective score -0.1926 <= 0; recent PnL -1.0491% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.23224566500627683, pnl=-2.7683649456434725, trades=5, reason=recent objective score -0.2322 <= 0; recent PnL -2.7684% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.32137376290059105 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51840 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1926 <= 0; recent PnL -1.0491% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2322 <= 0; recent PnL -2.7684% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51840
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8064
- **Recent window start**: 1774012200

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T08:38:51.989444+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 4194
- **validation_status**: validated_fail
