# PMM Dynamic Optimization Report: nonkyc_ETH-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 13:58:19 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T13:58:19.803567+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 1686 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ETH-USDT
- **interval**: 5m
- **n_candles**: 51916
- **dataset_hash**: 3ea92468fd7b175600d655e5a2dcb13945c821f817a78dcc23a966ee5fd06b70
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 571.3408606008397
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 27 |
| bb_length | 25 |
| bb_std | 2.114247668180009 |
| bbp_entry_threshold | 0.20286613246565005 |
| cooldown_time | 74484 |
| max_atr_pct_for_entry | 0.011518841530984819 |
| min_volume_quantile | 0.2529835596691781 |
| rsi_entry_threshold | 48.52860256759555 |
| rsi_length | 29 |
| stop_loss | 0.026645877320617375 |
| take_profit | 0.007615080162879476 |
| take_profit_order_type | MARKET |
| time_limit | 82082 |
| total_amount_quote | 571.3408606008397 |
| trailing_stop_activation | 0.001432858092403453 |
| trailing_stop_delta | 0.009697350548677 |
| trend_ema_length | 289 |
| use_trend_filter | True |
| volume_filter_window | 122 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 571.3408606008397 |
| Selected | 571.3408606008397 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0455
- **Net PnL (quote)**: -5.9731
- **Sharpe Ratio**: -0.4253
- **Max Drawdown %**: 2.8679
- **Profit Factor**: 0.4473971707873093
- **Trade Count**: 28
- **Total Fees (quote)**: 24.0378
- **Maker Fees**: 8.0046
- **Taker Fees**: 16.0332
- **Fee Drag %**: 4.2073

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1450
- **PnL Component**: -0.0105
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0215
- **Fee Drag Component**: -0.0210
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0880
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2621**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -3.35 | -8.53 | 3.36 | 8 | -0.2383 | n/a |
| 1 | -3.15 | -9.10 | 3.35 | 16 | -0.2173 | n/a |
| 2 | -0.91 | -3.77 | 1.23 | 21 | -0.1552 | n/a |
| 3 | 0.65 | 2.11 | 1.42 | 13 | -0.1632 | n/a |
| 4 | 0.92 | 2.46 | 1.37 | 10 | -0.1780 | n/a |
| 5 | -3.01 | -9.62 | 3.01 | 2 | -1000.0000 | n/a |
| 6 | -1.03 | -4.34 | 1.50 | 10 | -0.3083 | n/a |
| 7 | -3.47 | -10.43 | 3.47 | 6 | -0.3029 | n/a |
| 8 | -1.92 | -5.66 | 1.92 | 6 | -0.6136 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.23 | -0.81 | 2.54 | -0.4156 |
| fees_2x | -1.27 | -0.84 | 2.83 | -0.4749 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.03 | -0.42 | 2.86 | -0.1408 |
| very_low_liquidity | -1.04 | -0.43 | 2.86 | -0.1665 |
| high_slippage | -1.08 | -0.50 | 2.80 | -0.1804 |
| extreme_slippage | -1.23 | -0.81 | 2.54 | -0.4121 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.03 | -0.47 | 2.76 | -0.1747 |
| spread_widen_25bps | -1.08 | -0.49 | 2.58 | -0.1855 |
| thin_book | -3.07 | -1.73 | 3.37 | -0.2103 |
| very_thin_book | -2.90 | -1.76 | 3.13 | -0.2352 |
| entry_spread_stress | -3.95 | -1.58 | 4.06 | -0.1947 |
| combined_market_deterioration | -1.03 | -0.72 | 2.65 | -0.4839 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8770
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0028)
- **Trend**: ranging (efficiency: 0.0077)
- **Best holdout score**: -0.1906 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0725 | -0.1970 | -1.01 | 1.79 | 19 |
| 1 | -0.1617 | -0.1906 | -1.06 | 1.83 | 12 |
| 2 | -0.1619 | -0.2604 | -1.18 | 1.96 | 16 |
| 3 | -0.1642 | -0.2766 | -1.87 | 1.87 | 4 |
| 4 | -0.1644 | -0.2431 | -1.15 | 2.20 | 14 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51916
- **Expected rows**: 51918
- **Missing rows**: 2
- **Forward-fill count**: 116
- **Forward-fill fraction**: 0.002234378611603359
- **Longest gap (seconds)**: 900

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.4255 <= 0; recent PnL -2.2495% < 0
- **Objective score**: -0.42551480356477506
- **PnL %**: -2.2494608954869224
- **Trade count**: 8

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2343 <= 0; recent PnL -0.6543% < 0
- **Objective score**: -0.2342591082482952
- **PnL %**: -0.6543375481822049
- **Trade count**: 19

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3084 <= 0; recent PnL -0.3999% < 0
- **Objective score**: -0.30837184696530234
- **PnL %**: -0.3999133385459819
- **Trade count**: 8

## Sensitivity Analysis

- **Sensitivity penalty**: 0.15384615384615385
- **Baseline score**: -0.14458817863191487
- **Sign flips**: 0
- **Collapse count**: 4
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1766, -1000.0000 |
| bb_std | -1000.0000, -0.1520 |
| bbp_entry_threshold | -0.1520, -1000.0000 |
| rsi_length | -0.1789, -0.1740 |
| rsi_entry_threshold | -0.3554, -0.1686 |
| trend_ema_length | -0.1487, -0.1446 |
| max_atr_pct_for_entry | -0.1446, -0.1446 |
| volume_filter_window | -0.1492, -0.1446 |
| min_volume_quantile | -0.1492, -0.1446 |
| stop_loss | -0.1446, -0.1446 |
| take_profit | -0.1446, -0.1446 |
| cooldown_time | -0.1728, -0.1363 |
| total_amount_quote | -0.1446, -0.1446 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3875888116515537
- **Max CV**: 0.6762813840209785
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4349 | 0.021454914238433806 | 0.0688734063060474 | 0.03565927780353845 |
| take_profit | 0.6763 | 0.005286433702695528 | 0.03138839004150144 | 0.015457259440473024 |
| cooldown_time | 0.1503 | 39749.0 | 75798.0 | 65996.6 |
| total_amount_quote | 0.2888 | 409.9647701182288 | 974.1135249614969 | 635.6723934951533 |

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
| recent_objective | > 0 | -0.42551480356477506 | FAIL |
| recent_pnl | >= 0 | -2.2494608954869224 | FAIL |
| recent_trades | >= 5 | 8 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.15384615384615385 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.19704063814286357 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.15384615384615385 |
| recent_28d | FAIL | score=-0.42551480356477506, pnl=-2.2494608954869224, trades=8, reason=recent objective score -0.4255 <= 0; recent PnL -2.2495% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.2342591082482952, pnl=-0.6543375481822049, trades=19, reason=recent objective score -0.2343 <= 0; recent PnL -0.6543% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.30837184696530234, pnl=-0.3999133385459819, trades=8, reason=recent objective score -0.3084 <= 0; recent PnL -0.3999% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3875888116515537 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51916 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.4255 <= 0; recent PnL -2.2495% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2343 <= 0; recent PnL -0.6543% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.3084 <= 0; recent PnL -0.3999% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51916
- **Pre-release bars**: 43853
- **Dev bars**: 35083
- **Holdout bars**: 8770
- **Recent 28d bars**: 8063
- **Recent window start**: 1774096200

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T13:58:19.803567+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 1686
- **validation_status**: validated_fail
