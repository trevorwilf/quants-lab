# PMM Dynamic Optimization Report: mexc_ADA-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-17 21:02:40 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-17T21:02:40.204645+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 530 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ADA-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 2f57816c3d8b3f9b5f9372d0a1c91ea78d483995616987788b68ea80e7bac510
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 744.0943010037035
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 15 |
| bb_length | 103 |
| bb_std | 1.7930200487214194 |
| bbp_entry_threshold | 0.3180709496327549 |
| cooldown_time | 15645 |
| max_atr_pct_for_entry | 0.06800353633267277 |
| min_volume_quantile | 0.23128892783893304 |
| rsi_entry_threshold | 30.39967678589895 |
| rsi_length | 20 |
| stop_loss | 0.03772478856411055 |
| take_profit | 0.008651608439422745 |
| take_profit_order_type | MARKET |
| time_limit | 281287 |
| total_amount_quote | 744.0943010037035 |
| trailing_stop_activation | 0.00033854361653591527 |
| trailing_stop_delta | 0.014651578337894143 |
| trend_ema_length | 393 |
| use_trend_filter | False |
| volume_filter_window | 537 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 744.0943010037035 |
| Selected | 744.0943010037035 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0550
- **Net PnL (quote)**: -7.8502
- **Sharpe Ratio**: -0.2364
- **Max Drawdown %**: 4.2022
- **Profit Factor**: 0.8677143874671507
- **Trade Count**: 29
- **Total Fees (quote)**: 7.7385
- **Maker Fees**: 3.8693
- **Taker Fees**: 3.8692
- **Fee Drag %**: 1.0400

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1316
- **PnL Component**: -0.0106
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0315
- **Fee Drag Component**: -0.0052
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0840
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.57 | -0.38 | 4.52 | -0.1338 |
| fees_2x | -1.10 | -0.46 | 3.87 | -0.1929 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.06 | -0.24 | 4.20 | -0.1316 |
| very_low_liquidity | -1.06 | -0.24 | 4.20 | -0.1316 |
| high_slippage | -1.22 | -0.52 | 3.89 | -0.1919 |
| extreme_slippage | -2.42 | -1.08 | 4.20 | -0.2065 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.23 | -0.27 | 4.67 | -0.1369 |
| spread_widen_25bps | -2.25 | -0.52 | 5.50 | -0.1415 |
| thin_book | -1.14 | -0.33 | 3.76 | -0.2017 |
| very_thin_book | -3.74 | -2.19 | 3.88 | -1000.0000 |
| entry_spread_stress | -1.32 | -0.29 | 4.91 | -0.1396 |
| combined_market_deterioration | -2.91 | -1.29 | 4.00 | -0.2611 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0033)
- **Trend**: ranging (efficiency: 0.0042)
- **Best holdout score**: -0.1460 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0658 | -0.1789 | 0.87 | 0.37 | 4 |
| 1 | -0.1545 | -0.1789 | 0.87 | 0.37 | 4 |
| 2 | -0.1556 | -0.1639 | 1.60 | 0.36 | 6 |
| 3 | -0.1558 | -1000.0000 | 0.58 | 1.01 | 3 |
| 4 | -0.1560 | -0.1460 | 2.79 | 1.02 | 9 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 55
- **Forward-fill fraction**: 0.0010609363245307768
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2201 <= 0; recent PnL -2.0975% < 0
- **Objective score**: -0.22008422584070758
- **PnL %**: -2.097543270671047
- **Trade count**: 5

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.1681% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.168100582341359
- **Trade count**: 1

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.1314794662228698
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | -0.1366, -0.0517 |
| take_profit | -0.1315, -0.1315 |
| cooldown_time | -0.1315, -0.1315 |
| total_amount_quote | -0.1315, -0.1315 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4708264259681003
- **Max CV**: 0.6031735407077841
- **Clustered params**: stop_loss, take_profit
- **Scattered params**: cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3121 | 0.020898554449959722 | 0.06367206481088537 | 0.03965293094727213 |
| take_profit | 0.3724 | 0.005162191008281326 | 0.01600585702196764 | 0.008510659797799665 |
| cooldown_time | 0.5956 | 3529.0 | 47966.0 | 22686.6 |
| total_amount_quote | 0.6032 | 38.60421107315099 | 744.0943010037035 | 398.00931820827134 |

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
| recent_objective | > 0 | -0.22008422584070758 | FAIL |
| recent_pnl | >= 0 | -2.097543270671047 | FAIL |
| recent_trades | >= 5 | 5 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.17893266083633388 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.22008422584070758, pnl=-2.097543270671047, trades=5, reason=recent objective score -0.2201 <= 0; recent PnL -2.0975% < 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=-2.168100582341359, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -2.1681% < 0; recent trades 1 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4708264259681003 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2201 <= 0; recent PnL -2.0975% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.1681% < 0; recent trades 1 < 5 |
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
- **Recent window start**: 1774011900

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-17T21:02:40.204645+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 530
