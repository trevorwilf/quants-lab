# PMM Dynamic Optimization Report: mexc_LTC-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 03:46:00 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T03:46:00.462828+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 232 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: LTC-USDT
- **interval**: 5m
- **n_candles**: 51839
- **dataset_hash**: dbf3b0fdb3f19dd93a0c69259c1b6e65ba245cc3a322249eca03697f823182e2
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 158.4239079871365
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 29 |
| bb_length | 137 |
| bb_std | 1.1636941477916338 |
| bbp_entry_threshold | 0.08313407682382948 |
| cooldown_time | 3469 |
| max_atr_pct_for_entry | 0.06317351723177027 |
| min_volume_quantile | 0.5849730944266957 |
| rsi_entry_threshold | 23.51069473745467 |
| rsi_length | 18 |
| stop_loss | 0.0158686961803436 |
| take_profit | 0.012226715491072107 |
| take_profit_order_type | LIMIT |
| time_limit | 168592 |
| total_amount_quote | 158.4239079871365 |
| trailing_stop_activation | 0.01944965351931267 |
| trailing_stop_delta | 0.011113275102311283 |
| trend_ema_length | 53 |
| use_trend_filter | False |
| volume_filter_window | 370 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 158.4239079871365 |
| Selected | 158.4239079871365 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 12.2333
- **Net PnL (quote)**: 19.3805
- **Sharpe Ratio**: 2.2928
- **Max Drawdown %**: 8.0177
- **Profit Factor**: 1.4865447130440186
- **Trade Count**: 47
- **Total Fees (quote)**: 2.9194
- **Maker Fees**: 2.3554
- **Taker Fees**: 0.5641
- **Fee Drag %**: 1.8428

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0335
- **PnL Component**: 0.1154
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0601
- **Fee Drag Component**: -0.0092
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0120
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 11.30 | 2.12 | 8.16 | 0.0194 |
| fees_2x | -1.16 | -0.28 | 7.49 | -0.1997 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 12.23 | 2.29 | 8.02 | 0.0335 |
| very_low_liquidity | 12.23 | 2.29 | 8.02 | 0.0335 |
| high_slippage | 11.33 | 2.13 | 8.27 | 0.0235 |
| extreme_slippage | -1.58 | -0.39 | 8.01 | -0.2041 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 13.28 | 2.40 | 7.98 | 0.0428 |
| spread_widen_25bps | -2.67 | -1.48 | 4.85 | -0.4448 |
| thin_book | -2.27 | -0.63 | 6.68 | -0.2163 |
| very_thin_book | -2.16 | -1.48 | 3.69 | -1000.0000 |
| entry_spread_stress | -2.29 | -0.65 | 5.34 | -0.2064 |
| combined_market_deterioration | -1.18 | -0.45 | 4.88 | -0.2152 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0025)
- **Trend**: ranging (efficiency: 0.0019)
- **Best holdout score**: -0.3043 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9833 | -1000.0000 | -1.18 | 1.18 | 1 |
| 1 | -0.1616 | -0.3749 | -1.42 | 2.08 | 4 |
| 2 | -0.1689 | -0.3043 | -1.30 | 2.76 | 8 |
| 3 | -0.1726 | -1000.0000 | -1.18 | 1.18 | 1 |
| 4 | -0.1736 | -1000.0000 | -1.60 | 1.67 | 2 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51839
- **Expected rows**: 51841
- **Missing rows**: 2
- **Forward-fill count**: 53
- **Forward-fill fraction**: 0.0010223962653600571
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -1.6757% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -1.6757483546223906
- **Trade count**: 2

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -0.9347% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -0.9347068857655847
- **Trade count**: 2

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -0.6767% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -0.6767066986298871
- **Trade count**: 1

## Sensitivity Analysis

- **Sensitivity penalty**: 0.375
- **Baseline score**: -0.08095383655092353
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | -0.2054, -0.0363 |
| take_profit | -0.1952, -0.1976 |
| cooldown_time | -0.0810, -0.0377 |
| total_amount_quote | -0.0810, -0.0810 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5649843896349909
- **Max CV**: 0.656635329062766
- **Clustered params**: cooldown_time
- **Scattered params**: stop_loss, take_profit, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.5912 | 0.015238993314530064 | 0.06717140412955218 | 0.02845127685392273 |
| take_profit | 0.6098 | 0.005316964166722777 | 0.044104449691377806 | 0.02146895675534248 |
| cooldown_time | 0.4024 | 3469.0 | 60681.0 | 42021.1 |
| total_amount_quote | 0.6566 | 124.37339223653501 | 966.4309270416543 | 468.4670778041974 |

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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | -1.6757483546223906 | FAIL |
| recent_trades | >= 5 | 2 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.375 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.375 |
| recent_28d | FAIL | score=-1000.0, pnl=-1.6757483546223906, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -1.6757% < 0; recent trades 2 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=-0.9347068857655847, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -0.9347% < 0; recent trades 2 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-0.6767066986298871, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -0.6767% < 0; recent trades 1 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5649843896349909 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51839 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -1.6757% < 0; recent trades 2 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -0.9347% < 0; recent trades 2 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -0.6767% < 0; recent trades 1 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | false | NOT_RUN | — | — | — | not executed |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51839
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8063
- **Recent window start**: 1774012500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T03:46:00.462828+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 232
