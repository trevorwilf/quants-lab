# PMM Dynamic Optimization Report: mexc_APT-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 07:43:53 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T07:43:53.092859+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 4650 |
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
- **total_amount_quote_ideal**: 937.0652659852298
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 17 |
| bb_length | 147 |
| bb_std | 1.5332561529542121 |
| bbp_entry_threshold | 0.35772966404932094 |
| cooldown_time | 50856 |
| max_atr_pct_for_entry | 0.011341206055841753 |
| min_volume_quantile | 0.3615091584111478 |
| rsi_entry_threshold | 30.663412113450846 |
| rsi_length | 10 |
| stop_loss | 0.07047513522438104 |
| take_profit | 0.0249529524416435 |
| take_profit_order_type | MARKET |
| time_limit | 236222 |
| total_amount_quote | 937.0652659852298 |
| trailing_stop_activation | 0.0002571518306854635 |
| trailing_stop_delta | 0.013850802168985214 |
| trend_ema_length | 274 |
| use_trend_filter | False |
| volume_filter_window | 384 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 937.0652659852298 |
| Selected | 937.0652659852298 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 15.1398
- **Net PnL (quote)**: 141.8696
- **Sharpe Ratio**: 2.4970
- **Max Drawdown %**: 9.7704
- **Profit Factor**: 2.8784618026473807
- **Trade Count**: 181
- **Total Fees (quote)**: 41.1706
- **Maker Fees**: 20.5670
- **Taker Fees**: 20.6036
- **Fee Drag %**: 4.3936

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0451
- **PnL Component**: 0.1410
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0733
- **Fee Drag Component**: -0.0220
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1547**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 2.55 | 6.26 | 1.62 | 24 | -0.0936 | n/a |
| 1 | 3.29 | 9.51 | 0.71 | 22 | -0.0877 | n/a |
| 2 | 1.11 | 6.49 | 0.54 | 19 | -0.1192 | n/a |
| 3 | 2.30 | 3.24 | 4.50 | 20 | -0.1344 | n/a |
| 4 | 3.37 | 6.01 | 1.32 | 19 | -0.1037 | n/a |
| 5 | -3.15 | -3.01 | 6.61 | 33 | -0.3985 | n/a |
| 6 | 0.54 | 1.05 | 1.96 | 9 | -0.1751 | n/a |
| 7 | 0.71 | 0.93 | 4.60 | 13 | -0.1782 | n/a |
| 8 | 1.67 | 6.07 | 0.66 | 13 | -0.1381 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.46 | -0.31 | 6.77 | -0.1228 |
| fees_2x | -2.06 | -0.46 | 6.82 | -0.1323 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 12.05 | 2.00 | 9.77 | 0.0181 |
| very_low_liquidity | -3.26 | -1.54 | 4.90 | -0.1218 |
| high_slippage | -2.36 | -0.53 | 6.85 | -0.1296 |
| extreme_slippage | -5.37 | -1.30 | 7.14 | -0.1682 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.86 | -0.35 | 6.78 | -0.1240 |
| spread_widen_25bps | -5.70 | -2.89 | 7.04 | -0.2694 |
| thin_book | 13.06 | 2.81 | 4.13 | 0.0791 |
| very_thin_book | 2.41 | 0.74 | 3.24 | -0.1073 |
| entry_spread_stress | -5.30 | -2.74 | 7.01 | -0.2649 |
| combined_market_deterioration | -4.75 | -1.08 | 7.03 | -0.1775 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0036)
- **Trend**: ranging (efficiency: 0.0082)
- **Best holdout score**: -0.0763 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9774 | -1000.0000 | -1.58 | 3.58 | 2 |
| 1 | -0.0812 | -0.1447 | -0.22 | 6.58 | 28 |
| 2 | -0.0831 | -0.0763 | 2.03 | 4.06 | 35 |
| 3 | -0.0832 | -1000.0000 | -2.13 | 2.39 | 2 |
| 4 | -0.0858 | -0.1789 | -5.00 | 6.83 | 32 |

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
- **Reason**: recent objective score -0.1850 <= 0; recent PnL -1.3676% < 0
- **Objective score**: -0.18498257221572095
- **PnL %**: -1.3675897172334905
- **Trade count**: 15

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2435 <= 0; recent PnL -2.8803% < 0; recent trades 4 < 5
- **Objective score**: -0.24347640320816044
- **PnL %**: -2.880253207498379
- **Trade count**: 4

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -3.4164% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -3.4163882229875875
- **Trade count**: 1

## Sensitivity Analysis

- **Sensitivity penalty**: 1.1923076923076923
- **Baseline score**: 0.07457232992359938
- **Sign flips**: 15
- **Collapse count**: 16
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1171, -0.1291 |
| bb_std | -0.1189, -0.1121 |
| bbp_entry_threshold | -0.1190, -0.1174 |
| rsi_length | -0.1256, -0.2488 |
| rsi_entry_threshold | -0.2488, -0.1134 |
| trend_ema_length | 0.0746, -0.1154 |
| max_atr_pct_for_entry | 0.0899, 0.0716 |
| volume_filter_window | 0.0724, 0.0738 |
| min_volume_quantile | -0.1189, 0.0692 |
| stop_loss | -0.1254, 0.0321 |
| take_profit | 0.0746, 0.0746 |
| cooldown_time | -0.1295, -0.1523 |
| total_amount_quote | 0.0740, 0.0842 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.41301194941636243
- **Max CV**: 0.5826318635689849
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3443 | 0.01849738783484617 | 0.05572280006045728 | 0.036389051499753175 |
| take_profit | 0.5826 | 0.005190915284051646 | 0.02431796026580459 | 0.010741479115558176 |
| cooldown_time | 0.5359 | 11630.0 | 73816.0 | 44282.6 |
| total_amount_quote | 0.1893 | 456.8996289638591 | 968.2731948105136 | 823.529982662084 |

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
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.18498257221572095 | FAIL |
| recent_pnl | >= 0 | -1.3675897172334905 | FAIL |
| recent_trades | >= 5 | 15 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 1.1923076923076923 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=1.1923076923076923 |
| recent_28d | FAIL | score=-0.18498257221572095, pnl=-1.3675897172334905, trades=15, reason=recent objective score -0.1850 <= 0; recent PnL -1.3676% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.24347640320816044, pnl=-2.880253207498379, trades=4, reason=recent objective score -0.2435 <= 0; recent PnL -2.8803% < 0; recent trades 4 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-3.4163882229875875, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -3.4164% < 0; recent trades 1 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.41301194941636243 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51635 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1850 <= 0; recent PnL -1.3676% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2435 <= 0; recent PnL -2.8803% < 0; recent trades 4 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -3.4164% < 0; recent trades 1 < 5 |
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
- **run_timestamp**: 2026-04-18T07:43:53.092859+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 4650
- **validation_status**: validated_fail
