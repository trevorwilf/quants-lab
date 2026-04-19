# PMM Dynamic Optimization Report: nonkyc_RXD-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 15:13:19 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T15:13:19.517895+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 87 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: RXD-USDT
- **interval**: 5m
- **n_candles**: 51867
- **dataset_hash**: 08f7981bd294fd379baa2f726dfabab62783216b1e79f8b4ddc9b0dd5760d6c0
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 354.67886404106343
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 22 |
| bb_length | 72 |
| bb_std | 1.8843900601835801 |
| bbp_entry_threshold | 0.2790720923551763 |
| cooldown_time | 18104 |
| max_atr_pct_for_entry | 0.011730309689087623 |
| min_volume_quantile | 0.24512937992512998 |
| rsi_entry_threshold | 44.01431853572401 |
| rsi_length | 23 |
| stop_loss | 0.015923153481992094 |
| take_profit | 0.024502010577975304 |
| take_profit_order_type | MARKET |
| time_limit | 261128 |
| total_amount_quote | 354.67886404106343 |
| trailing_stop_activation | 0.034470314459462456 |
| trailing_stop_delta | 0.008085499082851347 |
| trend_ema_length | 146 |
| use_trend_filter | True |
| volume_filter_window | 527 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 354.67886404106343 |
| Selected | 354.67886404106343 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.9455
- **Net PnL (quote)**: -6.9002
- **Sharpe Ratio**: -4.2122
- **Max Drawdown %**: 1.9876
- **Profit Factor**: 0.0
- **Trade Count**: 398
- **Total Fees (quote)**: 1.0781
- **Maker Fees**: 0.3804
- **Taker Fees**: 0.6977
- **Fee Drag %**: 0.3040

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.3263
- **PnL Component**: -0.0196
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0149
- **Fee Drag Component**: -0.0015
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | -1.95 | -12.43 | 1.99 | 398 | -0.3273 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.10 | -4.52 | 2.14 | -0.3293 |
| fees_2x | -2.25 | -4.81 | 2.29 | -0.3323 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.95 | -8.27 | 1.97 | -0.3277 |
| very_low_liquidity | -0.98 | -8.28 | 0.99 | -0.3093 |
| high_slippage | -1.99 | -4.31 | 2.04 | -0.3272 |
| extreme_slippage | -2.09 | -4.49 | 2.13 | -0.3289 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.95 | -5.10 | 1.99 | -0.3263 |
| spread_widen_25bps | -1.95 | -5.07 | 1.98 | -0.3263 |
| thin_book | 0.00 | 0.00 | 0.00 | -1000.0000 |
| very_thin_book | 0.00 | 0.00 | 0.00 | -1000.0000 |
| entry_spread_stress | -1.95 | -5.15 | 1.99 | -0.3263 |
| combined_market_deterioration | 0.00 | 0.00 | 0.00 | -1000.0000 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0050)
- **Trend**: ranging (efficiency: 0.0046)
- **Best holdout score**: 0.0237 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.1631 | -1000.0000 | 0.00 | 0.00 | 0 |
| 1 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 4 | -1000.0000 | 0.0237 | 3.48 | 1.22 | 245 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51867
- **Expected rows**: 51899
- **Missing rows**: 32
- **Forward-fill count**: 2948
- **Forward-fill fraction**: 0.056837680991767406
- **Longest gap (seconds)**: 4500

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.038461538461538464
- **Baseline score**: -0.323596236795409
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.3236, -0.3236 |
| bb_std | -0.3236, -0.3236 |
| bbp_entry_threshold | -0.3236, -0.3236 |
| rsi_length | -0.3236, -0.3236 |
| rsi_entry_threshold | -0.3236, -1000.0000 |
| trend_ema_length | -0.3239, -0.3236 |
| max_atr_pct_for_entry | -0.3236, -0.3236 |
| volume_filter_window | -0.3236, -0.3236 |
| min_volume_quantile | -0.3236, -0.3236 |
| stop_loss | -0.3264, -0.3208 |
| take_profit | -0.3236, -0.3236 |
| cooldown_time | -0.3236, -0.3236 |
| total_amount_quote | -0.3273, -0.3212 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5465690930453482
- **Max CV**: 0.7035440873964931
- **Clustered params**: stop_loss
- **Scattered params**: take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4511 | 0.015846488196553956 | 0.06760341855737632 | 0.03903996279418816 |
| take_profit | 0.5016 | 0.005570740712340032 | 0.025877575042778093 | 0.014127329229890708 |
| cooldown_time | 0.7035 | 1319.0 | 81404.0 | 45223.8 |
| total_amount_quote | 0.5300 | 27.846360259215086 | 973.6975036774652 | 581.5399116555404 |

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
- walkforward_robust: **FAIL**
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | 0.0 | PASS |
| recent_trades | >= 5 | 0 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.038461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.038461538461538464 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5465690930453482 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51867 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51867
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8033
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T15:13:19.517895+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 87
- **validation_status**: validated_fail
