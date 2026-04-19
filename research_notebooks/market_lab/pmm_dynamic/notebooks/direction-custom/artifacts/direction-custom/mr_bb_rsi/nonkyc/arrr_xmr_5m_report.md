# PMM Dynamic Optimization Report: nonkyc_ARRR-XMR_5m_mr_bb_rsi_v1

Generated: 2026-04-18 12:17:31 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T12:17:31.004416+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 5538 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-XMR
- **interval**: 5m
- **n_candles**: 51896
- **dataset_hash**: cd2c1fb899b7e9082ef2ee2c65d44253bacb491e795e8587d117fed5c18dd821
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 242.196610041943
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 16 |
| bb_length | 133 |
| bb_std | 1.0962751162918747 |
| bbp_entry_threshold | 0.3568472689866367 |
| cooldown_time | 14343 |
| max_atr_pct_for_entry | 0.06637835761393251 |
| min_volume_quantile | 0.3921194645491807 |
| rsi_entry_threshold | 46.801234588295934 |
| rsi_length | 9 |
| stop_loss | 0.06245281422286875 |
| take_profit | 0.02739369832098184 |
| take_profit_order_type | MARKET |
| time_limit | 276716 |
| total_amount_quote | 242.196610041943 |
| trailing_stop_activation | 0.017850805360539478 |
| trailing_stop_delta | 0.0028897512552519137 |
| trend_ema_length | 380 |
| use_trend_filter | False |
| volume_filter_window | 454 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 242.196610041943 |
| Selected | 242.196610041943 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.2320
- **Net PnL (quote)**: -0.5619
- **Sharpe Ratio**: -2.6733
- **Max Drawdown %**: 0.3602
- **Profit Factor**: 0.36002419910287287
- **Trade Count**: 1528
- **Total Fees (quote)**: 0.0894
- **Maker Fees**: 0.0315
- **Taker Fees**: 0.0579
- **Fee Drag %**: 0.0369

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0052
- **PnL Component**: -0.0023
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0027
- **Fee Drag Component**: -0.0002
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | 0.02 | 2.58 | 0.02 | 146 | 0.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | -0.07 | -27.41 | 0.08 | 197 | -0.2535 | n/a |
| 4 | 0.01 | 4.09 | 0.00 | 58 | 0.0000 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | -1.14 | -16.16 | 1.14 | 3270 | -0.3205 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.25 | -2.91 | 0.37 | -0.0056 |
| fees_2x | -0.27 | -3.15 | 0.38 | -0.0059 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -0.12 | -2.67 | 0.18 | -0.0026 |
| very_low_liquidity | -0.06 | -2.68 | 0.09 | -0.0013 |
| high_slippage | -0.24 | -2.75 | 0.36 | -0.0053 |
| extreme_slippage | -0.25 | -2.92 | 0.37 | -0.0054 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -0.38 | -5.05 | 0.42 | -0.1822 |
| spread_widen_25bps | -0.38 | -5.10 | 0.42 | -0.1832 |
| thin_book | 0.00 | 1.39 | 0.00 | -1000.0000 |
| very_thin_book | 0.00 | 1.39 | 0.00 | -1000.0000 |
| entry_spread_stress | -0.38 | -5.06 | 0.42 | -0.1825 |
| combined_market_deterioration | -0.03 | -8.37 | 0.04 | -0.2347 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0076)
- **Trend**: ranging (efficiency: 0.0061)
- **Best holdout score**: -0.2971 (rank #1)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0026 | -0.3131 | -0.81 | 0.81 | 2258 |
| 1 | 0.0004 | -0.2971 | -0.38 | 0.38 | 2258 |
| 2 | 0.0004 | -0.3005 | -0.36 | 0.36 | 2258 |
| 3 | 0.0003 | -0.3024 | -0.42 | 0.42 | 2258 |
| 4 | 0.0003 | -0.3003 | -0.35 | 0.35 | 2258 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51896
- **Expected rows**: 51899
- **Missing rows**: 3
- **Forward-fill count**: 499
- **Forward-fill fraction**: 0.009615384615384616
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2995 <= 0; recent PnL -0.5915% < 0
- **Objective score**: -0.2994632176828824
- **PnL %**: -0.591515506223578
- **Trade count**: 1623

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3006 <= 0; recent PnL -0.5915% < 0
- **Objective score**: -0.3005969687432346
- **PnL %**: -0.591515506223578
- **Trade count**: 1623

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3013 <= 0; recent PnL -0.5915% < 0
- **Objective score**: -0.3013082792163607
- **PnL %**: -0.591515506223578
- **Trade count**: 1623

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.35575496432245163
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.3189, -0.3939 |
| bb_std | -0.3175, -0.3798 |
| bbp_entry_threshold | -0.3805, -0.3175 |
| rsi_length | -0.3556, -0.3175 |
| rsi_entry_threshold | -0.3467, -0.3109 |
| trend_ema_length | -0.3558, -0.3558 |
| max_atr_pct_for_entry | -0.3558, -0.3558 |
| volume_filter_window | -0.3567, -0.3564 |
| min_volume_quantile | -0.3515, -0.3567 |
| stop_loss | -0.3633, -0.3520 |
| take_profit | -0.3558, -0.3558 |
| cooldown_time | -0.3558, -0.3558 |
| total_amount_quote | -0.3487, -0.3644 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3607191851642544
- **Max CV**: 0.6958902761930735
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2623 | 0.03231614306593067 | 0.06710892603773716 | 0.03934678726922953 |
| take_profit | 0.6959 | 0.005172288039604133 | 0.05771095129866184 | 0.029304519802019657 |
| cooldown_time | 0.2627 | 9497.0 | 24040.0 | 15175.8 |
| total_amount_quote | 0.2220 | 26.83378060542276 | 54.32352466686089 | 38.233006224895696 |

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
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.2994632176828824 | FAIL |
| recent_pnl | >= 0 | -0.591515506223578 | FAIL |
| recent_trades | >= 5 | 1623 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.31308064189986273 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.2994632176828824, pnl=-0.591515506223578, trades=1623, reason=recent objective score -0.2995 <= 0; recent PnL -0.5915% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.3005969687432346, pnl=-0.591515506223578, trades=1623, reason=recent objective score -0.3006 <= 0; recent PnL -0.5915% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.3013082792163607, pnl=-0.591515506223578, trades=1623, reason=recent objective score -0.3013 <= 0; recent PnL -0.5915% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3607191851642544 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51896 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2995 <= 0; recent PnL -0.5915% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3006 <= 0; recent PnL -0.5915% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.3013 <= 0; recent PnL -0.5915% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51896
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8062
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T12:17:31.004416+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 5538
- **validation_status**: validated_fail
