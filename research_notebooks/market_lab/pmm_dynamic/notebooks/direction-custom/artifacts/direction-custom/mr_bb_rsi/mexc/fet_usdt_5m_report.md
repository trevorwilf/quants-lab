# PMM Dynamic Optimization Report: mexc_FET-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 08:57:34 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T08:57:34.312430+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 6681 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: FET-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: e5d033834887b2151ae930eee1b45f767bfe8b3bc2b64b4b86eb7e0fc955d92d
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 795.8213493634328
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 29 |
| bb_length | 24 |
| bb_std | 1.3277994448521913 |
| bbp_entry_threshold | 0.383201870660772 |
| cooldown_time | 48961 |
| max_atr_pct_for_entry | 0.006200772273219486 |
| min_volume_quantile | 0.33803618369334076 |
| rsi_entry_threshold | 49.84492372802803 |
| rsi_length | 12 |
| stop_loss | 0.040450949664041114 |
| take_profit | 0.04010976304613275 |
| take_profit_order_type | MARKET |
| time_limit | 110959 |
| total_amount_quote | 795.8213493634328 |
| trailing_stop_activation | 0.007089760815089453 |
| trailing_stop_delta | 0.01078133361569049 |
| trend_ema_length | 280 |
| use_trend_filter | False |
| volume_filter_window | 461 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 795.8213493634328 |
| Selected | 795.8213493634328 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 15.7413
- **Net PnL (quote)**: 125.2723
- **Sharpe Ratio**: 2.8334
- **Max Drawdown %**: 3.3882
- **Profit Factor**: inf
- **Trade Count**: 66
- **Total Fees (quote)**: 7.4248
- **Maker Fees**: 3.6991
- **Taker Fees**: 3.7257
- **Fee Drag %**: 0.9330

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1156
- **PnL Component**: 0.1462
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0254
- **Fee Drag Component**: -0.0047
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2568**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 3.72 | 4.01 | 2.31 | 17 | -0.1583 | n/a |
| 1 | 0.62 | 3.63 | 0.91 | 3 | -1000.0000 | n/a |
| 2 | 2.99 | 3.93 | 2.81 | 11 | -0.1491 | n/a |
| 3 | 0.24 | 0.47 | 2.64 | 4 | -0.2359 | n/a |
| 4 | 2.79 | 3.50 | 2.27 | 17 | -0.1230 | n/a |
| 5 | -4.13 | -8.03 | 4.13 | 3 | -1000.0000 | n/a |
| 6 | -2.69 | -4.59 | 3.81 | 9 | -0.2209 | n/a |
| 7 | -4.13 | -7.82 | 4.33 | 6 | -0.4108 | n/a |
| 8 | -4.13 | -6.61 | 4.17 | 4 | -0.5257 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 15.27 | 2.75 | 3.40 | 0.1092 |
| fees_2x | 14.81 | 2.67 | 3.41 | 0.1027 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 14.85 | 2.69 | 3.41 | 0.1079 |
| very_low_liquidity | 14.65 | 2.69 | 3.42 | 0.1062 |
| high_slippage | 14.57 | 2.64 | 3.42 | 0.1052 |
| extreme_slippage | 12.23 | 2.24 | 3.48 | 0.0841 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 14.90 | 2.67 | 3.41 | 0.1082 |
| spread_widen_25bps | 15.14 | 2.62 | 3.39 | 0.1098 |
| thin_book | 0.25 | 0.12 | 4.11 | -0.1582 |
| very_thin_book | -3.61 | -2.58 | 4.01 | -0.2513 |
| entry_spread_stress | 15.43 | 2.70 | 3.39 | 0.1124 |
| combined_market_deterioration | 1.01 | 0.30 | 4.09 | -0.1277 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0043)
- **Trend**: ranging (efficiency: 0.0140)
- **Best holdout score**: -0.1345 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9422 | -0.2205 | -2.69 | 3.81 | 9 |
| 1 | -0.1029 | -0.1724 | 1.48 | 0.85 | 5 |
| 2 | -0.1043 | -0.2296 | -2.73 | 3.82 | 7 |
| 3 | -0.1046 | -0.1345 | 3.61 | 1.16 | 10 |
| 4 | -0.1054 | -1000.0000 | -3.28 | 3.56 | 2 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 63
- **Forward-fill fraction**: 0.001215254335371617
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2048 <= 0; recent PnL -3.2232% < 0
- **Objective score**: -0.2048213017642262
- **PnL %**: -3.223158935034536
- **Trade count**: 15

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1489 <= 0
- **Objective score**: -0.1489288828239065
- **PnL %**: 0.7567136838865656
- **Trade count**: 14

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1494 <= 0
- **Objective score**: -0.1493980075713684
- **PnL %**: 0.7567136838865656
- **Trade count**: 14

## Sensitivity Analysis

- **Sensitivity penalty**: 0.2692307692307692
- **Baseline score**: -0.050655402223006914
- **Sign flips**: 0
- **Collapse count**: 7
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0124, -0.0217 |
| bb_std | -0.0532, -0.0553 |
| bbp_entry_threshold | -0.1280, -0.0295 |
| rsi_length | -0.0152, -0.0559 |
| rsi_entry_threshold | -0.1178, -1000.0000 |
| trend_ema_length | -0.0675, -0.0467 |
| max_atr_pct_for_entry | -1000.0000, -0.1341 |
| volume_filter_window | -0.0069, -0.0686 |
| min_volume_quantile | -0.0145, -0.0580 |
| stop_loss | -0.0867, -0.0369 |
| take_profit | -0.0507, -0.0507 |
| cooldown_time | -0.1011, -0.0271 |
| total_amount_quote | -0.0454, -0.0496 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.43059400050066926
- **Max CV**: 0.9131761820572605
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3989 | 0.02153809174217338 | 0.06811987948210152 | 0.036570469862706886 |
| take_profit | 0.9132 | 0.005835665470600478 | 0.05771490213456771 | 0.018596358387811176 |
| cooldown_time | 0.2997 | 22466.0 | 65514.0 | 43492.5 |
| total_amount_quote | 0.1106 | 692.5830795391616 | 982.5078206609227 | 847.8875460621708 |

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
| recent_objective | > 0 | -0.2048213017642262 | FAIL |
| recent_pnl | >= 0 | -3.223158935034536 | FAIL |
| recent_trades | >= 5 | 15 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.2692307692307692 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.22045897176184237 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.2692307692307692 |
| recent_28d | FAIL | score=-0.2048213017642262, pnl=-3.223158935034536, trades=15, reason=recent objective score -0.2048 <= 0; recent PnL -3.2232% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.1489288828239065, pnl=0.7567136838865656, trades=14, reason=recent objective score -0.1489 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.1493980075713684, pnl=0.7567136838865656, trades=14, reason=recent objective score -0.1494 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.43059400050066926 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2048 <= 0; recent PnL -3.2232% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1489 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1494 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51841
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065
- **Recent window start**: 1774012200

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T08:57:34.312430+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 6681
- **validation_status**: validated_fail
