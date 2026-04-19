# PMM Dynamic Optimization Report: mexc_WLD-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 10:34:37 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T10:34:37.644074+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 6930 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: WLD-USDT
- **interval**: 5m
- **n_candles**: 51795
- **dataset_hash**: d5b3db1355c6a27a8f2b4d580b98e06ccc25cf641ec64487696d04425bfcd724
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 763.6811334774113
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 23 |
| bb_length | 40 |
| bb_std | 2.2905762746320866 |
| bbp_entry_threshold | 0.24536876591679413 |
| cooldown_time | 35896 |
| max_atr_pct_for_entry | 0.012880394405921682 |
| min_volume_quantile | 0.4536208397634185 |
| rsi_entry_threshold | 45.451123964046815 |
| rsi_length | 19 |
| stop_loss | 0.04210042059530478 |
| take_profit | 0.02702053245376641 |
| take_profit_order_type | LIMIT |
| time_limit | 122792 |
| total_amount_quote | 763.6811334774113 |
| trailing_stop_activation | 0.00018905154323259202 |
| trailing_stop_delta | 0.010845418827640882 |
| trend_ema_length | 235 |
| use_trend_filter | False |
| volume_filter_window | 398 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 763.6811334774113 |
| Selected | 763.6811334774113 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 26.8395
- **Net PnL (quote)**: 204.9679
- **Sharpe Ratio**: 6.3151
- **Max Drawdown %**: 2.6746
- **Profit Factor**: 49.19056066572369
- **Trade Count**: 124
- **Total Fees (quote)**: 26.6224
- **Maker Fees**: 13.2881
- **Taker Fees**: 13.3344
- **Fee Drag %**: 3.4861

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.2001
- **PnL Component**: 0.2378
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0201
- **Fee Drag Component**: -0.0174
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1577**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 2.17 | 3.95 | 3.11 | 16 | -0.1398 | n/a |
| 1 | 1.15 | 2.29 | 2.44 | 10 | -0.1684 | n/a |
| 2 | 0.63 | 1.90 | 0.83 | 12 | -0.1539 | n/a |
| 3 | 1.19 | 6.72 | 0.40 | 17 | -0.1250 | n/a |
| 4 | 3.71 | 9.06 | 0.68 | 11 | -0.1265 | n/a |
| 5 | 3.10 | 13.99 | 0.02 | 12 | -0.1231 | n/a |
| 6 | -3.14 | -6.09 | 3.52 | 3 | -1000.0000 | n/a |
| 7 | 0.56 | 6.07 | 0.25 | 4 | -0.1809 | n/a |
| 8 | -3.78 | -7.54 | 4.29 | 4 | -0.2558 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 25.10 | 5.94 | 2.70 | 0.1773 |
| fees_2x | 23.35 | 5.56 | 2.73 | 0.1544 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 24.20 | 5.64 | 2.72 | 0.1788 |
| very_low_liquidity | -2.08 | -2.34 | 2.65 | -0.1898 |
| high_slippage | 22.47 | 5.43 | 2.72 | 0.1647 |
| extreme_slippage | 13.74 | 3.49 | 2.82 | 0.0899 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 14.92 | 2.90 | 6.93 | 0.0697 |
| spread_widen_25bps | 0.50 | 0.17 | 10.15 | -0.0882 |
| thin_book | -1.25 | -0.50 | 4.17 | -0.1975 |
| very_thin_book | 4.14 | 2.96 | 1.20 | -0.0867 |
| entry_spread_stress | 8.83 | 1.75 | 9.45 | -0.0039 |
| combined_market_deterioration | -2.67 | -1.17 | 4.41 | -0.2146 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0036)
- **Trend**: ranging (efficiency: 0.0086)
- **Best holdout score**: -0.1135 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9000 | -0.2397 | -3.19 | 3.52 | 5 |
| 1 | -0.1154 | -0.1874 | -1.35 | 3.13 | 13 |
| 2 | -0.1158 | -0.1501 | 0.51 | 1.18 | 14 |
| 3 | -0.1166 | -0.1553 | 1.52 | 1.61 | 11 |
| 4 | -0.1219 | -0.1135 | 3.28 | 0.92 | 16 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51795
- **Expected rows**: 51841
- **Missing rows**: 46
- **Forward-fill count**: 28
- **Forward-fill fraction**: 0.0005405927213051453
- **Longest gap (seconds)**: 13500

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2469 <= 0; recent PnL -3.6899% < 0
- **Objective score**: -0.24694840855421818
- **PnL %**: -3.6899261443306943
- **Trade count**: 6

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -4.2971% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -4.297085438278461
- **Trade count**: 2

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1913 <= 0
- **Objective score**: -0.19134825576174982
- **PnL %**: 0.4399627912183034
- **Trade count**: 6

## Sensitivity Analysis

- **Sensitivity penalty**: 0.23076923076923078
- **Baseline score**: 0.1296470481347935
- **Sign flips**: 3
- **Collapse count**: 3
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | 0.1798, 0.1471 |
| bb_std | 0.1100, -0.1798 |
| bbp_entry_threshold | -0.1798, 0.1100 |
| rsi_length | 0.1240, 0.1049 |
| rsi_entry_threshold | 0.0686, -0.0787 |
| trend_ema_length | 0.1296, 0.1296 |
| max_atr_pct_for_entry | 0.1339, 0.1282 |
| volume_filter_window | 0.1391, 0.1474 |
| min_volume_quantile | 0.1558, 0.0876 |
| stop_loss | 0.1179, 0.1015 |
| take_profit | 0.1296, 0.1296 |
| cooldown_time | 0.0795, 0.1636 |
| total_amount_quote | 0.1268, 0.1291 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4602757661609067
- **Max CV**: 1.0669122406579437
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2699 | 0.032440233844395774 | 0.07621225672114776 | 0.05332021739894982 |
| take_profit | 0.4253 | 0.0062520760470160044 | 0.05632369568634637 | 0.034578746977784944 |
| cooldown_time | 1.0669 | 2973.0 | 58235.0 | 15440.3 |
| total_amount_quote | 0.0789 | 790.8392466885517 | 992.8345474025633 | 905.2015260095634 |

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
| recent_objective | > 0 | -0.24694840855421818 | FAIL |
| recent_pnl | >= 0 | -3.6899261443306943 | FAIL |
| recent_trades | >= 5 | 6 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.23076923076923078 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.23971245419630666 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.23076923076923078 |
| recent_28d | FAIL | score=-0.24694840855421818, pnl=-3.6899261443306943, trades=6, reason=recent objective score -0.2469 <= 0; recent PnL -3.6899% < 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=-4.297085438278461, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -4.2971% < 0; recent trades 2 < 5 |
| recent_7d_info | FAIL | informational only; score=-0.19134825576174982, pnl=0.4399627912183034, trades=6, reason=recent objective score -0.1913 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4602757661609067 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51795 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2469 <= 0; recent PnL -3.6899% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -4.2971% < 0; recent trades 2 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1913 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51795
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8019
- **Recent window start**: 1774026000

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T10:34:37.644074+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 6930
- **validation_status**: validated_fail
