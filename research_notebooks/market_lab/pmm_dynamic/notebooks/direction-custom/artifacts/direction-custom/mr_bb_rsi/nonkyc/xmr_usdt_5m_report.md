# PMM Dynamic Optimization Report: nonkyc_XMR-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 16:10:16 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T16:10:16.339288+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 5902 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 51879
- **dataset_hash**: 3d72355642611fa656a9c6387b6b838ed5fda1a15b22792aa74b6b4591d5ad9d
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 676.0675407139497
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 27 |
| bb_length | 22 |
| bb_std | 2.576242970085383 |
| bbp_entry_threshold | 0.16400393216129025 |
| cooldown_time | 67977 |
| max_atr_pct_for_entry | 0.022080799536876482 |
| min_volume_quantile | 0.20561352915086972 |
| rsi_entry_threshold | 41.426279692709784 |
| rsi_length | 8 |
| stop_loss | 0.026597367928870987 |
| take_profit | 0.012098549487426119 |
| take_profit_order_type | MARKET |
| time_limit | 123306 |
| total_amount_quote | 676.0675407139497 |
| trailing_stop_activation | 0.000547133389994587 |
| trailing_stop_delta | 0.00029155770271493226 |
| trend_ema_length | 242 |
| use_trend_filter | False |
| volume_filter_window | 347 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 676.0675407139497 |
| Selected | 676.0675407139497 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0687
- **Net PnL (quote)**: -7.2249
- **Sharpe Ratio**: -0.4828
- **Max Drawdown %**: 2.6079
- **Profit Factor**: 0.44466551224656586
- **Trade Count**: 57
- **Total Fees (quote)**: 32.7487
- **Maker Fees**: 12.2950
- **Taker Fees**: 20.4536
- **Fee Drag %**: 4.8440

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0701
- **PnL Component**: -0.0107
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0196
- **Fee Drag Component**: -0.0242
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1839**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.98 | 2.55 | 0.90 | 51 | -0.0404 | n/a |
| 1 | -2.12 | -3.48 | 2.61 | 33 | -0.1576 | n/a |
| 2 | 2.53 | 4.80 | 1.54 | 53 | -0.0160 | n/a |
| 3 | -2.82 | -5.68 | 3.00 | 3 | -1000.0000 | n/a |
| 4 | 0.79 | 1.19 | 2.40 | 36 | -0.0949 | n/a |
| 5 | -2.82 | -5.56 | 3.13 | 13 | -0.2432 | n/a |
| 6 | -3.04 | -8.61 | 3.35 | 6 | -0.3095 | n/a |
| 7 | 0.23 | 0.55 | 1.15 | 39 | -0.1137 | n/a |
| 8 | -2.93 | -5.81 | 3.24 | 7 | -0.2336 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.06 | -2.11 | 1.35 | -0.1826 |
| fees_2x | -1.46 | -4.79 | 1.47 | -0.2491 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.08 | -0.50 | 2.87 | -0.1142 |
| very_low_liquidity | -1.06 | -0.45 | 2.92 | -0.1021 |
| high_slippage | -1.06 | -1.77 | 1.08 | -0.1006 |
| extreme_slippage | -1.01 | -2.03 | 1.24 | -0.1602 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.00 | -1.48 | 1.06 | -0.0892 |
| spread_widen_25bps | -1.04 | -1.64 | 1.36 | -0.1329 |
| thin_book | -1.94 | -0.46 | 4.89 | -0.1402 |
| very_thin_book | -2.24 | -1.33 | 3.37 | -0.0878 |
| entry_spread_stress | -1.09 | -1.77 | 1.15 | -0.1496 |
| combined_market_deterioration | -1.31 | -4.04 | 1.31 | -0.3664 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8774
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0040)
- **Trend**: ranging (efficiency: 0.0041)
- **Best holdout score**: -0.0701 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0350 | -0.4740 | -1.16 | 2.20 | 16 |
| 1 | -0.0601 | -0.2980 | -1.19 | 1.54 | 24 |
| 2 | -0.0643 | -0.2093 | -2.53 | 2.58 | 15 |
| 3 | -0.0693 | -0.3144 | -1.76 | 2.21 | 4 |
| 4 | -0.0715 | -0.0701 | -1.07 | 2.40 | 51 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51879
- **Expected rows**: 51939
- **Missing rows**: 60
- **Forward-fill count**: 249
- **Forward-fill fraction**: 0.004799629908055283
- **Longest gap (seconds)**: 12000

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1808 <= 0; recent PnL -2.9915% < 0
- **Objective score**: -0.180806814533543
- **PnL %**: -2.9914999911765534
- **Trade count**: 22

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1158 <= 0
- **Objective score**: -0.11582528796097132
- **PnL %**: 0.013602317665859726
- **Trade count**: 41

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1694 <= 0
- **Objective score**: -0.16944187604311203
- **PnL %**: 0.10486985737935554
- **Trade count**: 25

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07692307692307693
- **Baseline score**: -0.08962932700118036
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1033, -0.0785 |
| bb_std | -0.0963, -0.0741 |
| bbp_entry_threshold | -0.0877, -0.1083 |
| rsi_length | -0.0896, -0.0896 |
| rsi_entry_threshold | -0.0896, -0.1528 |
| trend_ema_length | -0.0896, -0.0851 |
| max_atr_pct_for_entry | -0.0896, -0.0896 |
| volume_filter_window | -0.0896, -0.0896 |
| min_volume_quantile | -0.0962, -0.0896 |
| stop_loss | -0.0941, -0.0843 |
| take_profit | -0.0896, -0.0896 |
| cooldown_time | -0.1494, -0.0665 |
| total_amount_quote | -0.0911, -0.0899 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4585757961135862
- **Max CV**: 0.674384713608178
- **Clustered params**: cooldown_time, total_amount_quote
- **Scattered params**: stop_loss, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.6744 | 0.015551156128375428 | 0.07231337436176481 | 0.0292107214464066 |
| take_profit | 0.5176 | 0.006008417328144216 | 0.025216780201275955 | 0.01109260169661531 |
| cooldown_time | 0.4460 | 5072.0 | 72077.0 | 47200.7 |
| total_amount_quote | 0.1963 | 445.3354926202758 | 986.2132486945668 | 804.7786735107426 |

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
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
| recent_objective | > 0 | -0.180806814533543 | FAIL |
| recent_pnl | >= 0 | -2.9914999911765534 | FAIL |
| recent_trades | >= 5 | 22 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.07692307692307693 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.4739682149689156 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.07692307692307693 |
| recent_28d | FAIL | score=-0.180806814533543, pnl=-2.9914999911765534, trades=22, reason=recent objective score -0.1808 <= 0; recent PnL -2.9915% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.11582528796097132, pnl=0.013602317665859726, trades=41, reason=recent objective score -0.1158 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.16944187604311203, pnl=0.10486985737935554, trades=25, reason=recent objective score -0.1694 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4585757961135862 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51879 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1808 <= 0; recent PnL -2.9915% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1158 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1694 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51879
- **Pre-release bars**: 43874
- **Dev bars**: 35100
- **Holdout bars**: 8774
- **Recent 28d bars**: 8005
- **Recent window start**: 1774102500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T16:10:16.339288+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 5902
- **validation_status**: validated_fail
