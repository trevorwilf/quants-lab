# PMM Dynamic Optimization Report: mexc_FET-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 02:03:50 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T02:03:50.136155+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 419 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: FET-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: e5d033834887b2151ae930eee1b45f767bfe8b3bc2b64b4b86eb7e0fc955d92d
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 911.1219661791193
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 13 |
| bb_length | 148 |
| bb_std | 2.855171828425735 |
| bbp_entry_threshold | 0.1135845708257207 |
| cooldown_time | 11879 |
| max_atr_pct_for_entry | 0.09360163585533685 |
| min_volume_quantile | 0.568787820214471 |
| rsi_entry_threshold | 45.519543938532415 |
| rsi_length | 11 |
| stop_loss | 0.030280672804982377 |
| take_profit | 0.008882516896376647 |
| take_profit_order_type | MARKET |
| time_limit | 295954 |
| total_amount_quote | 911.1219661791193 |
| trailing_stop_activation | 0.002390674939838581 |
| trailing_stop_delta | 0.009673134614560968 |
| trend_ema_length | 144 |
| use_trend_filter | False |
| volume_filter_window | 319 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 911.1219661791193 |
| Selected | 911.1219661791193 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 7.7537
- **Net PnL (quote)**: 70.6459
- **Sharpe Ratio**: 1.9228
- **Max Drawdown %**: 4.2918
- **Profit Factor**: 2.001890163399836
- **Trade Count**: 57
- **Total Fees (quote)**: 10.7092
- **Maker Fees**: 5.3465
- **Taker Fees**: 5.3627
- **Fee Drag %**: 1.1754

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0364
- **PnL Component**: 0.0747
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0322
- **Fee Drag Component**: -0.0059
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 7.17 | 1.79 | 4.32 | 0.0278 |
| fees_2x | 6.58 | 1.65 | 4.36 | 0.0191 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.04 | -0.33 | 4.31 | -0.1847 |
| very_low_liquidity | -1.62 | -1.86 | 1.88 | -0.4960 |
| high_slippage | 6.18 | 1.59 | 4.35 | 0.0215 |
| extreme_slippage | -1.73 | -0.61 | 4.47 | -0.2088 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 6.55 | 1.70 | 4.35 | 0.0250 |
| spread_widen_25bps | -1.26 | -0.44 | 4.44 | -0.2038 |
| thin_book | -3.12 | -2.18 | 3.12 | -1000.0000 |
| very_thin_book | -2.88 | -2.10 | 3.11 | -1000.0000 |
| entry_spread_stress | 5.91 | 1.54 | 4.47 | 0.0180 |
| combined_market_deterioration | -3.18 | -2.23 | 3.18 | -1000.0000 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0043)
- **Trend**: ranging (efficiency: 0.0140)
- **Best holdout score**: -0.0715 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9818 | -0.1510 | 0.37 | 0.30 | 12 |
| 1 | -0.1566 | -0.0715 | -1.51 | 3.07 | 42 |
| 2 | -0.1566 | -0.0905 | 1.53 | 0.11 | 24 |
| 3 | -0.1570 | -0.1939 | -2.15 | 3.09 | 13 |
| 4 | -0.1612 | -0.1453 | 0.42 | 0.66 | 14 |

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
- **Reason**: recent objective score -0.1934 <= 0; recent trades 4 < 5
- **Objective score**: -0.193448587493262
- **PnL %**: 0.13440882088974743
- **Trade count**: 4

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 3 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.04008631440360965
- **Trade count**: 3

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.04028752376043927
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | 0.0299, 0.0494 |
| take_profit | 0.0403, 0.0403 |
| cooldown_time | 0.0391, 0.0271 |
| total_amount_quote | 0.0389, 0.0422 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3801426811825912
- **Max CV**: 0.7573932744179176
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.1819 | 0.026551116168477846 | 0.047774583642554394 | 0.03476894023672899 |
| take_profit | 0.3980 | 0.005720292836646595 | 0.01717979978617249 | 0.008631856653071823 |
| cooldown_time | 0.7574 | 11879.0 | 85225.0 | 32750.9 |
| total_amount_quote | 0.1833 | 503.49160986428075 | 973.6975036774652 | 786.6574613639642 |

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
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.193448587493262 | FAIL |
| recent_pnl | >= 0 | 0.13440882088974743 | PASS |
| recent_trades | >= 5 | 4 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1510396971260414 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.193448587493262, pnl=0.13440882088974743, trades=4, reason=recent objective score -0.1934 <= 0; recent trades 4 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.04008631440360965, trades=3, reason=recent objective score -1000.0000 <= 0; recent trades 3 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3801426811825912 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1934 <= 0; recent trades 4 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 3 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | false | NOT_RUN | — | — | — | not executed |
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
- **run_timestamp**: 2026-04-18T02:03:50.136155+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 419
