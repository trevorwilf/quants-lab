# PMM Dynamic Optimization Report: mexc_BNB-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 08:11:23 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T08:11:23.897538+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 4499 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BNB-USDT
- **interval**: 5m
- **n_candles**: 51679
- **dataset_hash**: 2ea0b273483a334383d43d93e5c78470f3d9fe17e9ac8390203a0b6f988d9650
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 136.15124740534753
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 20 |
| bb_length | 76 |
| bb_std | 2.892428393590463 |
| bbp_entry_threshold | 0.1257061696349824 |
| cooldown_time | 2791 |
| max_atr_pct_for_entry | 0.016956309990516245 |
| min_volume_quantile | 0.17773414246704194 |
| rsi_entry_threshold | 41.02332563260969 |
| rsi_length | 23 |
| stop_loss | 0.01670398772467805 |
| take_profit | 0.035549862006922006 |
| take_profit_order_type | MARKET |
| time_limit | 223081 |
| total_amount_quote | 136.15124740534753 |
| trailing_stop_activation | 0.0006091417091008067 |
| trailing_stop_delta | 0.01840051570834846 |
| trend_ema_length | 76 |
| use_trend_filter | False |
| volume_filter_window | 444 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 136.15124740534753 |
| Selected | 136.15124740534753 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.3263
- **Net PnL (quote)**: -3.1672
- **Sharpe Ratio**: -0.8710
- **Max Drawdown %**: 3.5192
- **Profit Factor**: 0.5950769232250025
- **Trade Count**: 51
- **Total Fees (quote)**: 2.0683
- **Maker Fees**: 1.0342
- **Taker Fees**: 1.0340
- **Fee Drag %**: 1.5191

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0576
- **PnL Component**: -0.0235
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0264
- **Fee Drag Component**: -0.0076
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2153**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.12 | -8.59 | 1.40 | 7 | -0.1948 | n/a |
| 1 | -1.15 | -9.67 | 1.15 | 3 | -1000.0000 | n/a |
| 2 | -0.63 | -2.32 | 1.30 | 30 | -0.1011 | n/a |
| 3 | -1.97 | -7.97 | 2.07 | 22 | -0.1503 | n/a |
| 4 | -1.78 | -8.07 | 1.86 | 7 | -0.2059 | n/a |
| 5 | -2.51 | -10.09 | 2.52 | 3 | -1000.0000 | n/a |
| 6 | -1.87 | -8.23 | 1.90 | 6 | -0.2247 | n/a |
| 7 | -1.04 | -8.04 | 1.17 | 5 | -0.2388 | n/a |
| 8 | -1.23 | -7.68 | 1.26 | 6 | -0.2243 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.31 | -0.50 | 3.25 | -0.0488 |
| fees_2x | -1.04 | -0.97 | 2.46 | -0.1841 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -2.33 | -0.87 | 3.52 | -0.0576 |
| very_low_liquidity | -2.33 | -0.87 | 3.52 | -0.0576 |
| high_slippage | -1.04 | -1.04 | 2.45 | -0.1981 |
| extreme_slippage | -1.49 | -1.68 | 2.12 | -0.2309 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.01 | -1.01 | 2.45 | -0.1978 |
| spread_widen_25bps | -1.23 | -1.28 | 1.76 | -0.2064 |
| thin_book | -1.14 | -0.67 | 3.34 | -0.0758 |
| very_thin_book | -1.65 | -1.36 | 3.45 | -0.1324 |
| entry_spread_stress | -1.04 | -1.21 | 1.75 | -0.2006 |
| combined_market_deterioration | -2.09 | -1.88 | 3.02 | -0.1546 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0019)
- **Trend**: ranging (efficiency: 0.0043)
- **Best holdout score**: -0.1049 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0288 | -0.2004 | -1.04 | 1.05 | 15 |
| 1 | -0.0704 | -0.1049 | -2.15 | 2.41 | 35 |
| 2 | -0.0989 | -0.1697 | -1.64 | 1.87 | 16 |
| 3 | -0.1008 | -0.1687 | -1.99 | 2.79 | 19 |
| 4 | -0.1057 | -0.1787 | -3.83 | 3.85 | 23 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51679
- **Expected rows**: 51841
- **Missing rows**: 162
- **Forward-fill count**: 191
- **Forward-fill fraction**: 0.003695891948373614
- **Longest gap (seconds)**: 16200

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -1.7592% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -1.7591574737770244
- **Trade count**: 2

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2049 <= 0; recent PnL -1.1754% < 0
- **Objective score**: -0.20491349541489412
- **PnL %**: -1.175404820134665
- **Trade count**: 9

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2136 <= 0; recent PnL -1.7852% < 0
- **Objective score**: -0.21363581050637642
- **PnL %**: -1.7852188154870792
- **Trade count**: 5

## Sensitivity Analysis

- **Sensitivity penalty**: 0.15384615384615385
- **Baseline score**: -0.05759199333449195
- **Sign flips**: 0
- **Collapse count**: 4
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0689, -0.2053 |
| bb_std | -0.2054, -0.0624 |
| bbp_entry_threshold | -0.0489, -0.2056 |
| rsi_length | -0.0597, -0.0583 |
| rsi_entry_threshold | -0.0557, -0.2056 |
| trend_ema_length | -0.0576, -0.0576 |
| max_atr_pct_for_entry | -0.0576, -0.0576 |
| volume_filter_window | -0.0576, -0.0576 |
| min_volume_quantile | -0.0576, -0.0576 |
| stop_loss | -0.0653, -0.0500 |
| take_profit | -0.0576, -0.0576 |
| cooldown_time | -0.0558, -0.0686 |
| total_amount_quote | -0.0576, -0.0576 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4509901859086453
- **Max CV**: 0.5471825917849674
- **Clustered params**: take_profit, cooldown_time, total_amount_quote
- **Scattered params**: stop_loss

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.5472 | 0.01670750093617065 | 0.06874894618786535 | 0.03412002072931457 |
| take_profit | 0.4333 | 0.013476221549946966 | 0.058808642046677774 | 0.03560555234638099 |
| cooldown_time | 0.4149 | 3988.0 | 13709.0 | 8648.4 |
| total_amount_quote | 0.4086 | 152.09706347846247 | 747.7834597116782 | 459.85661080887564 |

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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | -1.7591574737770244 | FAIL |
| recent_trades | >= 5 | 2 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.15384615384615385 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.20037145250041952 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.15384615384615385 |
| recent_28d | FAIL | score=-1000.0, pnl=-1.7591574737770244, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -1.7592% < 0; recent trades 2 < 5 |
| recent_14d_info | FAIL | informational only; score=-0.20491349541489412, pnl=-1.175404820134665, trades=9, reason=recent objective score -0.2049 <= 0; recent PnL -1.1754% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.21363581050637642, pnl=-1.7852188154870792, trades=5, reason=recent objective score -0.2136 <= 0; recent PnL -1.7852% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4509901859086453 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51679 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -1.7592% < 0; recent trades 2 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2049 <= 0; recent PnL -1.1754% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2136 <= 0; recent PnL -1.7852% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51679
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 7903
- **Recent window start**: 1774061400

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T08:11:23.897538+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 4499
- **validation_status**: validated_fail
