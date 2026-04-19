# PMM Dynamic Optimization Report: nonkyc_DIVI-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 13:13:32 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T13:13:32.588451+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 4786 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: DIVI-USDT
- **interval**: 5m
- **n_candles**: 47473
- **dataset_hash**: baa3a740ff4f8f8e6e292b522cdc4e4e29f1c0537ec9ad33c4141380e10ad2ca
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 488.17980852902343
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 28 |
| bb_length | 151 |
| bb_std | 2.813959465503873 |
| bbp_entry_threshold | 0.054659333857625836 |
| cooldown_time | 37335 |
| max_atr_pct_for_entry | 0.02549124494428737 |
| min_volume_quantile | 0.14952504230138886 |
| rsi_entry_threshold | 23.96161427684863 |
| rsi_length | 13 |
| stop_loss | 0.04748489063264923 |
| take_profit | 0.04915076299391851 |
| take_profit_order_type | LIMIT |
| time_limit | 141984 |
| total_amount_quote | 488.17980852902343 |
| trailing_stop_activation | 0.03951413927203561 |
| trailing_stop_delta | 0.0014218702118329652 |
| trend_ema_length | 304 |
| use_trend_filter | False |
| volume_filter_window | 146 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 488.17980852902343 |
| Selected | 488.17980852902343 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 30.6942
- **Net PnL (quote)**: 149.8430
- **Sharpe Ratio**: 2.6619
- **Max Drawdown %**: 4.6770
- **Profit Factor**: 11.21813274524203
- **Trade Count**: 144
- **Total Fees (quote)**: 5.7059
- **Maker Fees**: 1.9123
- **Taker Fees**: 3.7936
- **Fee Drag %**: 1.1688
- **TP Min-Notional Failures**: 1 :warning:
  > 1 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.2267
- **PnL Component**: 0.2677
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0351
- **Fee Drag Component**: -0.0058
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.0019**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 5.57 | 5.14 | 1.90 | 42 | 0.0056 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 7.74 | 4.17 | 1.97 | 35 | -0.0019 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 10.32 | 4.30 | 2.06 | 33 | 0.0124 | n/a |
| 6 | -5.09 | -23.58 | 5.18 | 40 | -0.4963 | n/a |
| 7 | 12.11 | 3.97 | 4.02 | 41 | 0.0458 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 30.11 | 2.63 | 4.75 | 0.2187 |
| fees_2x | 29.53 | 2.60 | 4.82 | 0.2108 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 17.03 | 2.60 | 2.72 | 0.1337 |
| very_low_liquidity | 8.52 | 2.62 | 1.37 | 0.0698 |
| high_slippage | 30.50 | 2.66 | 4.69 | 0.2251 |
| extreme_slippage | 30.11 | 2.64 | 4.70 | 0.2220 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.22 | -0.43 | 6.23 | -0.2062 |
| spread_widen_25bps | -1.26 | -0.45 | 6.24 | -0.2071 |
| thin_book | -0.03 | -0.04 | 0.82 | -1000.0000 |
| very_thin_book | -0.03 | -0.04 | 0.82 | -1000.0000 |
| entry_spread_stress | -1.23 | -0.44 | 6.23 | -0.2065 |
| combined_market_deterioration | 7.09 | 2.15 | 1.15 | 0.0094 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 7883
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0060)
- **Trend**: ranging (efficiency: 0.0023)
- **Best holdout score**: 0.0210 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.8867 | -0.0115 | 5.38 | 4.69 | 74 |
| 1 | 0.0075 | -0.1698 | 1.47 | 0.01 | 4 |
| 2 | 0.0073 | -1000.0000 | 1.30 | 0.01 | 3 |
| 3 | 0.0047 | -0.4527 | -3.74 | 4.91 | 20 |
| 4 | 0.0022 | 0.0210 | 6.59 | 3.84 | 48 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 47473
- **Expected rows**: 47480
- **Missing rows**: 7
- **Forward-fill count**: 1442
- **Forward-fill fraction**: 0.030375160617614222
- **Longest gap (seconds)**: 900

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.04615509331633178
- **PnL %**: 12.113736917420105
- **Trade count**: 41

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
- **Baseline score**: 0.33556874366717065
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | 0.3356, 0.2752 |
| bb_std | 0.2645, 0.3356 |
| bbp_entry_threshold | 0.3356, 0.3356 |
| rsi_length | 0.2074, 0.3356 |
| rsi_entry_threshold | 0.2974, 0.2063 |
| trend_ema_length | 0.3356, 0.3356 |
| max_atr_pct_for_entry | 0.3356, 0.3356 |
| volume_filter_window | 0.2806, 0.2806 |
| min_volume_quantile | 0.2806, 0.3356 |
| stop_loss | 0.3524, 0.0293 |
| take_profit | 0.3356, 0.3356 |
| cooldown_time | 0.3356, 0.3356 |
| total_amount_quote | 0.3263, 0.3458 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.292146638811897
- **Max CV**: 0.5366661177992073
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.1664 | 0.0269093310814879 | 0.04444572647727821 | 0.03654464430409456 |
| take_profit | 0.2729 | 0.02483286015277518 | 0.05759297530058288 | 0.042757226511197545 |
| cooldown_time | 0.5367 | 10527.0 | 78872.0 | 43843.2 |
| total_amount_quote | 0.1927 | 296.5201354057292 | 628.8929054291912 | 480.0821937413637 |

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
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.04615509331633178 | PASS |
| recent_pnl | >= 0 | 12.113736917420105 | PASS |
| recent_trades | >= 5 | 41 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.038461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.011545659862142886 |
| walkforward | PASS | 8 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.038461538461538464 |
| recent_28d | PASS | score=0.04615509331633178, pnl=12.113736917420105, trades=41, reason= |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.292146638811897 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 47473 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 47473
- **Pre-release bars**: 39415
- **Dev bars**: 31532
- **Holdout bars**: 7883
- **Recent 28d bars**: 8058
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T13:13:32.588451+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 4786
- **validation_status**: validated_fail
