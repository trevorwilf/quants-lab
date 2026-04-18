# PMM Dynamic Optimization Report: mexc_HYPE-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 02:37:52 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T02:37:52.554239+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 175 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: HYPE-USDT
- **interval**: 5m
- **n_candles**: 51820
- **dataset_hash**: 649baf2d0497e4fdff5efa3bf0a3f209b87ad5988b1bb7361146b8ae25c9654d
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 670.1394257360353
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 8 |
| bb_length | 125 |
| bb_std | 2.1141714169194046 |
| bbp_entry_threshold | 0.24942602819691156 |
| cooldown_time | 10556 |
| max_atr_pct_for_entry | 0.052883925781815055 |
| min_volume_quantile | 0.11928913100011082 |
| rsi_entry_threshold | 44.91886995858774 |
| rsi_length | 18 |
| stop_loss | 0.07873249990710049 |
| take_profit | 0.005933032263463212 |
| take_profit_order_type | MARKET |
| time_limit | 6536 |
| total_amount_quote | 670.1394257360353 |
| trailing_stop_activation | 0.02021022342163579 |
| trailing_stop_delta | 0.00893730449644856 |
| trend_ema_length | 400 |
| use_trend_filter | True |
| volume_filter_window | 215 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 670.1394257360353 |
| Selected | 670.1394257360353 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0213
- **Net PnL (quote)**: -6.8439
- **Sharpe Ratio**: -0.4216
- **Max Drawdown %**: 4.0309
- **Profit Factor**: 0.7471199213689669
- **Trade Count**: 9
- **Total Fees (quote)**: 2.4116
- **Maker Fees**: 1.2062
- **Taker Fees**: 1.2053
- **Fee Drag %**: 0.3599

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.2064
- **PnL Component**: -0.0103
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0302
- **Fee Drag Component**: -0.0018
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1640
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.20 | -0.50 | 4.06 | -0.2093 |
| fees_2x | -1.38 | -0.58 | 4.08 | -0.2122 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.02 | -0.42 | 4.03 | -0.2064 |
| very_low_liquidity | -1.02 | -0.42 | 4.03 | -0.2064 |
| high_slippage | -1.47 | -0.62 | 4.09 | -0.2114 |
| extreme_slippage | -2.37 | -1.02 | 4.28 | -0.2180 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.17 | -0.88 | 4.12 | -0.2147 |
| spread_widen_25bps | -2.47 | -0.99 | 4.19 | -0.2143 |
| thin_book | -1.17 | -0.60 | 2.45 | -0.2651 |
| very_thin_book | 2.02 | 1.14 | 2.43 | -0.1524 |
| entry_spread_stress | -2.27 | -0.91 | 4.14 | -0.2159 |
| combined_market_deterioration | -1.12 | -0.56 | 2.45 | -0.2072 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8780
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0042)
- **Trend**: ranging (efficiency: 0.0162)
- **Best holdout score**: -0.2012 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.1032 | -0.2012 | -1.39 | 3.38 | 10 |
| 1 | -0.1533 | -0.2404 | -3.87 | 5.26 | 10 |
| 2 | -0.1562 | -0.3157 | -1.28 | 2.46 | 6 |
| 3 | -0.1569 | -0.2405 | -3.65 | 5.05 | 9 |
| 4 | -0.1570 | -0.2437 | -3.92 | 5.31 | 10 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51820
- **Expected rows**: 51968
- **Missing rows**: 148
- **Forward-fill count**: 274
- **Forward-fill fraction**: 0.005287533770744886
- **Longest gap (seconds)**: 26700

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3936 <= 0; recent PnL -1.5217% < 0; recent trades 4 < 5
- **Objective score**: -0.3936222738809809
- **PnL %**: -1.5216638035205317
- **Trade count**: 4

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2130 <= 0; recent PnL -1.5295% < 0
- **Objective score**: -0.21301302474788225
- **PnL %**: -1.5295062511204391
- **Trade count**: 7

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -1.9249% < 0; recent trades 3 < 5
- **Objective score**: -1000.0
- **PnL %**: -1.9248828019310475
- **Trade count**: 3

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.2063551080510853
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | -0.2064, -0.2064 |
| take_profit | -0.2132, -0.2101 |
| cooldown_time | -0.2362, -0.2070 |
| total_amount_quote | -0.2064, -0.2064 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5892519003177976
- **Max CV**: 1.2743751886455643
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3927 | 0.02486864315906332 | 0.07873249990710049 | 0.04420818850945392 |
| take_profit | 1.2744 | 0.005627944294668299 | 0.050455058168264504 | 0.010912813145034388 |
| cooldown_time | 0.4122 | 10556.0 | 85298.0 | 52445.4 |
| total_amount_quote | 0.2778 | 399.262412197153 | 955.1893115708262 | 605.9350193339121 |

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
- walkforward_robust: **FAIL**
- walkforward_positive_majority: **FAIL**
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
| recent_objective | > 0 | -0.3936222738809809 | FAIL |
| recent_pnl | >= 0 | -1.5216638035205317 | FAIL |
| recent_trades | >= 5 | 4 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.20117265932334444 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.3936222738809809, pnl=-1.5216638035205317, trades=4, reason=recent objective score -0.3936 <= 0; recent PnL -1.5217% < 0; recent trades 4 < 5 |
| recent_14d_info | FAIL | informational only; score=-0.21301302474788225, pnl=-1.5295062511204391, trades=7, reason=recent objective score -0.2130 <= 0; recent PnL -1.5295% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-1.9248828019310475, trades=3, reason=recent objective score -1000.0000 <= 0; recent PnL -1.9249% < 0; recent trades 3 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5892519003177976 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51820 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3936 <= 0; recent PnL -1.5217% < 0; recent trades 4 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2130 <= 0; recent PnL -1.5295% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -1.9249% < 0; recent trades 3 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | false | NOT_RUN | — | — | — | not executed |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51820
- **Pre-release bars**: 43903
- **Dev bars**: 35123
- **Holdout bars**: 8780
- **Recent 28d bars**: 7917
- **Recent window start**: 1774057200

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T02:37:52.554239+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 175
