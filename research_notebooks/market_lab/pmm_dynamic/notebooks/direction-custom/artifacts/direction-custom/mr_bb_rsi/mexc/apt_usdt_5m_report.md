# PMM Dynamic Optimization Report: mexc_APT-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 06:58:23 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T06:58:23.295489+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 7806 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: APT-USDT
- **interval**: 5m
- **n_candles**: 51635
- **dataset_hash**: b0b457637cb81628d02526a35bdcbe17138fea08f7c3af204fde8cdb00cf6384
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 357.14471632724684
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 15 |
| bb_length | 150 |
| bb_std | 1.4891759863395173 |
| bbp_entry_threshold | 0.34496265851897995 |
| cooldown_time | 40627 |
| max_atr_pct_for_entry | 0.07733931136238954 |
| min_volume_quantile | 0.32812719622982955 |
| rsi_entry_threshold | 49.169077962566355 |
| rsi_length | 12 |
| stop_loss | 0.04790222777515514 |
| take_profit | 0.0302653501576809 |
| take_profit_order_type | LIMIT |
| time_limit | 58860 |
| total_amount_quote | 357.14471632724684 |
| trailing_stop_activation | 9.750158437505814e-05 |
| trailing_stop_delta | 0.0070978288208256276 |
| trend_ema_length | 394 |
| use_trend_filter | False |
| volume_filter_window | 152 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 357.14471632724684 |
| Selected | 357.14471632724684 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 13.8299
- **Net PnL (quote)**: 49.3926
- **Sharpe Ratio**: 2.5343
- **Max Drawdown %**: 6.6307
- **Profit Factor**: 1.9121928122350011
- **Trade Count**: 165
- **Total Fees (quote)**: 20.5855
- **Maker Fees**: 10.2858
- **Taker Fees**: 10.2998
- **Fee Drag %**: 5.7639

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0504
- **PnL Component**: 0.1295
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0497
- **Fee Drag Component**: -0.0288
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1258**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 4.12 | 11.12 | 0.80 | 23 | -0.0773 | n/a |
| 1 | 3.13 | 6.58 | 2.29 | 19 | -0.1137 | n/a |
| 2 | 3.09 | 8.07 | 1.14 | 21 | -0.0978 | n/a |
| 3 | 1.61 | 3.37 | 1.28 | 23 | -0.1055 | n/a |
| 4 | -4.29 | -7.94 | 4.90 | 10 | -0.2424 | n/a |
| 5 | 3.17 | 8.73 | 0.87 | 17 | -0.1096 | n/a |
| 6 | 8.79 | 11.33 | 2.06 | 17 | -0.0667 | n/a |
| 7 | -3.99 | -6.48 | 4.89 | 10 | -0.2398 | n/a |
| 8 | 0.19 | 0.99 | 0.74 | 10 | -0.1651 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 10.95 | 2.03 | 7.01 | 0.0076 |
| fees_2x | 8.06 | 1.52 | 7.40 | -0.0362 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 12.15 | 2.24 | 6.69 | 0.0354 |
| very_low_liquidity | -1.13 | -0.11 | 7.23 | -0.0904 |
| high_slippage | 6.61 | 1.27 | 7.58 | -0.0222 |
| extreme_slippage | -4.34 | -1.22 | 4.99 | -0.0892 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -3.10 | -1.55 | 3.79 | -0.2134 |
| spread_widen_25bps | -2.98 | -1.44 | 3.63 | -0.2070 |
| thin_book | -2.52 | -1.29 | 3.50 | -0.2430 |
| very_thin_book | -4.35 | -2.39 | 4.85 | -0.2643 |
| entry_spread_stress | -2.70 | -1.31 | 3.59 | -0.2077 |
| combined_market_deterioration | -2.84 | -1.45 | 3.77 | -0.2795 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0036)
- **Trend**: ranging (efficiency: 0.0082)
- **Best holdout score**: -0.0770 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9748 | -0.0770 | 4.65 | 5.39 | 31 |
| 1 | -0.0625 | -0.1806 | -2.31 | 2.99 | 17 |
| 2 | -0.0681 | -0.0791 | 5.57 | 2.23 | 22 |
| 3 | -0.0766 | -0.2443 | -2.24 | 3.22 | 8 |
| 4 | -0.0769 | -0.1779 | -1.14 | 1.25 | 11 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51635
- **Expected rows**: 51841
- **Missing rows**: 206
- **Forward-fill count**: 58
- **Forward-fill fraction**: 0.0011232691004163843
- **Longest gap (seconds)**: 25800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2639 <= 0; recent PnL -4.1994% < 0
- **Objective score**: -0.2638833347518585
- **PnL %**: -4.199444305996965
- **Trade count**: 15

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2474 <= 0; recent PnL -1.1596% < 0
- **Objective score**: -0.24737275490805186
- **PnL %**: -1.159581482913768
- **Trade count**: 6

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -3.0888% < 0; recent trades 3 < 5
- **Objective score**: -1000.0
- **PnL %**: -3.0887650593970974
- **Trade count**: 3

## Sensitivity Analysis

- **Sensitivity penalty**: 0.46153846153846156
- **Baseline score**: 0.09572942562417987
- **Sign flips**: 6
- **Collapse count**: 6
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.2101, -0.1205 |
| bb_std | -0.2133, 0.0585 |
| bbp_entry_threshold | 0.0961, -0.2133 |
| rsi_length | 0.0991, 0.1048 |
| rsi_entry_threshold | 0.0747, -0.0697 |
| trend_ema_length | 0.0957, 0.0957 |
| max_atr_pct_for_entry | 0.0957, 0.0957 |
| volume_filter_window | 0.0757, 0.1009 |
| min_volume_quantile | 0.0944, 0.1173 |
| stop_loss | 0.0805, 0.1004 |
| take_profit | 0.0957, 0.0957 |
| cooldown_time | 0.0601, -0.1890 |
| total_amount_quote | 0.0915, 0.0875 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.49015540501069105
- **Max CV**: 0.8558000072960462
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4079 | 0.019686591301499082 | 0.0649703166478409 | 0.03837131056577418 |
| take_profit | 0.5552 | 0.005789456067229993 | 0.03146434207561984 | 0.01547277972620903 |
| cooldown_time | 0.8558 | 3401.0 | 35167.0 | 14277.0 |
| total_amount_quote | 0.1417 | 634.2892483478098 | 973.6329063512316 | 834.5602785507292 |

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
| recent_objective | > 0 | -0.2638833347518585 | FAIL |
| recent_pnl | >= 0 | -4.199444305996965 | FAIL |
| recent_trades | >= 5 | 15 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.46153846153846156 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.07701261567148601 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.46153846153846156 |
| recent_28d | FAIL | score=-0.2638833347518585, pnl=-4.199444305996965, trades=15, reason=recent objective score -0.2639 <= 0; recent PnL -4.1994% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.24737275490805186, pnl=-1.159581482913768, trades=6, reason=recent objective score -0.2474 <= 0; recent PnL -1.1596% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-3.0887650593970974, trades=3, reason=recent objective score -1000.0000 <= 0; recent PnL -3.0888% < 0; recent trades 3 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.49015540501069105 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51635 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2639 <= 0; recent PnL -4.1994% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2474 <= 0; recent PnL -1.1596% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -3.0888% < 0; recent trades 3 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51635
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 7859
- **Recent window start**: 1774074300

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T06:58:23.295489+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 7806
- **validation_status**: validated_fail
