# PMM Dynamic Optimization Report: mexc_ICP-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 03:11:39 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T03:11:39.353060+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 306 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ICP-USDT
- **interval**: 5m
- **n_candles**: 51776
- **dataset_hash**: bcaa5bfaf31b517b064adc15745423369c2c07d40f73d8a15cefdbe1d4cb5879
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 428.8687244343293
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 26 |
| bb_length | 102 |
| bb_std | 1.5130616028056352 |
| bbp_entry_threshold | 0.20605181936857228 |
| cooldown_time | 22416 |
| max_atr_pct_for_entry | 0.07933637221721833 |
| min_volume_quantile | 0.009042649194306772 |
| rsi_entry_threshold | 31.96438259517617 |
| rsi_length | 28 |
| stop_loss | 0.06145220432426716 |
| take_profit | 0.008313920803008912 |
| take_profit_order_type | LIMIT |
| time_limit | 225637 |
| total_amount_quote | 428.8687244343293 |
| trailing_stop_activation | 0.0009046702826138475 |
| trailing_stop_delta | 0.005865215395138429 |
| trend_ema_length | 346 |
| use_trend_filter | False |
| volume_filter_window | 466 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 428.8687244343293 |
| Selected | 428.8687244343293 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 25.0072
- **Net PnL (quote)**: 107.2481
- **Sharpe Ratio**: 4.3632
- **Max Drawdown %**: 2.5219
- **Profit Factor**: 215.25516884296218
- **Trade Count**: 63
- **Total Fees (quote)**: 8.9437
- **Maker Fees**: 4.4602
- **Taker Fees**: 4.4835
- **Fee Drag %**: 2.0854

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1937
- **PnL Component**: 0.2232
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0189
- **Fee Drag Component**: -0.0104
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 23.96 | 4.19 | 2.55 | 0.1799 |
| fees_2x | 22.92 | 4.02 | 2.57 | 0.1661 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 25.13 | 4.39 | 2.52 | 0.1947 |
| very_low_liquidity | 22.72 | 3.92 | 2.78 | 0.1734 |
| high_slippage | 22.39 | 3.97 | 2.56 | 0.1723 |
| extreme_slippage | 17.16 | 3.15 | 2.63 | 0.1280 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 23.00 | 3.89 | 2.60 | 0.1768 |
| spread_widen_25bps | 23.07 | 3.51 | 2.64 | 0.1769 |
| thin_book | -3.39 | -1.15 | 6.06 | -0.2418 |
| very_thin_book | 1.51 | 0.93 | 1.58 | -0.1701 |
| entry_spread_stress | 22.71 | 3.54 | 2.62 | 0.1742 |
| combined_market_deterioration | -3.72 | -1.27 | 6.14 | -0.2388 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0040)
- **Trend**: ranging (efficiency: 0.0030)
- **Best holdout score**: -0.2094 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9032 | -0.2360 | -3.09 | 4.66 | 8 |
| 1 | -0.1206 | -0.2186 | -1.84 | 3.05 | 6 |
| 2 | -0.1294 | -0.2284 | -2.01 | 4.55 | 7 |
| 3 | -0.1309 | -0.2094 | -1.17 | 2.16 | 5 |
| 4 | -0.1326 | -0.2098 | -1.21 | 2.16 | 5 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51776
- **Expected rows**: 51841
- **Missing rows**: 65
- **Forward-fill count**: 213
- **Forward-fill fraction**: 0.004113875154511743
- **Longest gap (seconds)**: 19800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.3460% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.3460047872400507
- **Trade count**: 1

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.5120 <= 0; recent PnL -1.8701% < 0; recent trades 4 < 5
- **Objective score**: -0.5120374029826247
- **PnL %**: -1.8700943192698987
- **Trade count**: 4

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -0.9763% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -0.9762705958588084
- **Trade count**: 1

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.13851158864719337
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | 0.1610, 0.1472 |
| take_profit | 0.1385, 0.1385 |
| cooldown_time | 0.1391, 0.1416 |
| total_amount_quote | 0.1390, 0.1382 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.45425450772092285
- **Max CV**: 0.8777567619049276
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3254 | 0.01602026660556986 | 0.036504969362634886 | 0.023040319724671396 |
| take_profit | 0.2941 | 0.005172047218999946 | 0.011244489459784197 | 0.007073517537257576 |
| cooldown_time | 0.8778 | 717.0 | 57455.0 | 19016.1 |
| total_amount_quote | 0.3198 | 403.31668615092894 | 965.6870008088262 | 698.4183384031655 |

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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | -2.3460047872400507 | FAIL |
| recent_trades | >= 5 | 1 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.23598745459590548 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-1000.0, pnl=-2.3460047872400507, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -2.3460% < 0; recent trades 1 < 5 |
| recent_14d_info | FAIL | informational only; score=-0.5120374029826247, pnl=-1.8700943192698987, trades=4, reason=recent objective score -0.5120 <= 0; recent PnL -1.8701% < 0; recent trades 4 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-0.9762705958588084, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -0.9763% < 0; recent trades 1 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.45425450772092285 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51776 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.3460% < 0; recent trades 1 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.5120 <= 0; recent PnL -1.8701% < 0; recent trades 4 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -0.9763% < 0; recent trades 1 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | false | NOT_RUN | — | — | — | not executed |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51776
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8000
- **Recent window start**: 1774032000

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T03:11:39.353060+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 306
