# PMM Dynamic Optimization Report: nonkyc_SHIB-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 15:33:06 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T15:33:06.346483+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 0 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: SHIB-USDT
- **interval**: 5m
- **n_candles**: 51881
- **dataset_hash**: ce5b454627ab2e98e5830e85cedfda41846ce9ffdf8fd5906cc06340cab43059
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 651.4134446984452
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 24 |
| bb_length | 188 |
| bb_std | 1.6327511091635718 |
| bbp_entry_threshold | 0.11437158408698307 |
| cooldown_time | 1319 |
| max_atr_pct_for_entry | 0.03542289163725381 |
| min_volume_quantile | 0.5767840416436928 |
| rsi_entry_threshold | 37.0317508724506 |
| rsi_length | 11 |
| stop_loss | 0.017925702542820283 |
| take_profit | 0.01050329226532709 |
| take_profit_order_type | MARKET |
| time_limit | 228093 |
| total_amount_quote | 651.4134446984452 |
| trailing_stop_activation | 0.038585903894877205 |
| trailing_stop_delta | 0.01447370693839907 |
| trend_ema_length | 279 |
| use_trend_filter | False |
| volume_filter_window | 443 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 651.4134446984452 |
| Selected | 651.4134446984452 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 0.0000
- **Net PnL (quote)**: 0.0000
- **Sharpe Ratio**: 0.0000
- **Max Drawdown %**: 0.0000
- **Profit Factor**: 0.0
- **Trade Count**: 0
- **Total Fees (quote)**: 0.0000
- **Maker Fees**: 0.0000
- **Taker Fees**: 0.0000
- **Fee Drag %**: 0.0000

## Selected Candidate Single-Run Objective

- **Raw Score**: -1000.0000
- **PnL Component**: 0.0000
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0000
- **Fee Drag Component**: -0.0000
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: True

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **fees_1.5x** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 0.00 | 0.00 | 0.00 | -1000.0000 |
| fees_2x | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 0.00 | 0.00 | 0.00 | -1000.0000 |
| very_low_liquidity | 0.00 | 0.00 | 0.00 | -1000.0000 |
| high_slippage | 0.00 | 0.00 | 0.00 | -1000.0000 |
| extreme_slippage | 0.00 | 0.00 | 0.00 | -1000.0000 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_25bps | 0.00 | 0.00 | 0.00 | -1000.0000 |
| thin_book | 0.00 | 0.00 | 0.00 | -1000.0000 |
| very_thin_book | 0.00 | 0.00 | 0.00 | -1000.0000 |
| entry_spread_stress | 0.00 | 0.00 | 0.00 | -1000.0000 |
| combined_market_deterioration | 0.00 | 0.00 | 0.00 | -1000.0000 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8771
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0026)
- **Trend**: ranging (efficiency: 0.0046)
- **Best holdout score**: -1000.0000 (rank #-1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 1 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 4 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51881
- **Expected rows**: 51923
- **Missing rows**: 42
- **Forward-fill count**: 136
- **Forward-fill fraction**: 0.0026213835508182184
- **Longest gap (seconds)**: 7200

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

- **Sensitivity penalty**: 0.0
- **Baseline score**: -1000.0
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -1000.0000, -1000.0000 |
| bb_std | -1000.0000, -1000.0000 |
| bbp_entry_threshold | -1000.0000, -1000.0000 |
| rsi_length | -1000.0000, -1000.0000 |
| rsi_entry_threshold | -1000.0000, -1000.0000 |
| trend_ema_length | -1000.0000, -1000.0000 |
| max_atr_pct_for_entry | -1000.0000, -1000.0000 |
| volume_filter_window | -1000.0000, -1000.0000 |
| min_volume_quantile | -1000.0000, -1000.0000 |
| stop_loss | -1000.0000, -1000.0000 |
| take_profit | -1000.0000, -1000.0000 |
| cooldown_time | -1000.0000, -1000.0000 |
| total_amount_quote | -1000.0000, -1000.0000 |

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
- runtime_sanity: **FAIL**
- objective_not_degenerate: **FAIL**
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
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_1.5x score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5465690930453482 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51881 |  |
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

- **Full bars**: 51881
- **Pre-release bars**: 43858
- **Dev bars**: 35087
- **Holdout bars**: 8771
- **Recent 28d bars**: 8023
- **Recent window start**: 1774097700

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T15:33:06.346483+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 0
- **validation_status**: validated_fail
