# PMM Dynamic Optimization Report: mexc_ETH-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 01:31:05 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T01:31:05.218750+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 351 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ETH-USDT
- **interval**: 5m
- **n_candles**: 51776
- **dataset_hash**: 0a159e9ef0cdab57917794421d449cf8b954deb600b828f7b9a64d0ff8b9b973
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 127.05610019534868
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 23 |
| bb_length | 178 |
| bb_std | 2.825471556317423 |
| bbp_entry_threshold | 0.2992724580624494 |
| cooldown_time | 12175 |
| max_atr_pct_for_entry | 0.028957243800000598 |
| min_volume_quantile | 0.06930779245506877 |
| rsi_entry_threshold | 24.41389573920722 |
| rsi_length | 17 |
| stop_loss | 0.03730578490217708 |
| take_profit | 0.03850993036097254 |
| take_profit_order_type | MARKET |
| time_limit | 325593 |
| total_amount_quote | 127.05610019534868 |
| trailing_stop_activation | 0.00046619496145706724 |
| trailing_stop_delta | 0.01919635457195452 |
| trend_ema_length | 357 |
| use_trend_filter | False |
| volume_filter_window | 325 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 127.05610019534868 |
| Selected | 127.05610019534868 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -3.6125
- **Net PnL (quote)**: -4.5899
- **Sharpe Ratio**: -0.7195
- **Max Drawdown %**: 8.0843
- **Profit Factor**: 0.6879495782316062
- **Trade Count**: 28
- **Total Fees (quote)**: 1.4203
- **Maker Fees**: 0.7105
- **Taker Fees**: 0.7098
- **Fee Drag %**: 1.1179

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1915
- **PnL Component**: -0.0368
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0606
- **Fee Drag Component**: -0.0056
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0880
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -4.17 | -0.84 | 8.33 | -0.1979 |
| fees_2x | -4.73 | -0.96 | 8.58 | -0.2084 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -3.61 | -0.72 | 8.08 | -0.1915 |
| very_low_liquidity | -3.61 | -0.72 | 8.08 | -0.1915 |
| high_slippage | -1.15 | -0.19 | 5.01 | -0.1469 |
| extreme_slippage | -2.08 | -0.52 | 4.43 | -0.1943 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -4.65 | -0.93 | 8.35 | -0.2003 |
| spread_widen_25bps | -2.06 | -0.37 | 5.06 | -0.1487 |
| thin_book | -2.35 | -0.71 | 3.82 | -0.2108 |
| very_thin_book | -1.99 | -0.69 | 3.77 | -0.2143 |
| entry_spread_stress | -1.24 | -0.20 | 4.85 | -0.1427 |
| combined_market_deterioration | -3.09 | -0.82 | 4.08 | -0.2001 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0028)
- **Trend**: ranging (efficiency: 0.0070)
- **Best holdout score**: -1000.0000 (rank #-1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0957 | -1000.0000 | -2.70 | 2.98 | 3 |
| 1 | -0.1765 | -1000.0000 | -3.55 | 3.82 | 3 |
| 2 | -0.1765 | -1000.0000 | -2.70 | 2.98 | 3 |
| 3 | -0.1768 | -1000.0000 | -2.70 | 2.98 | 3 |
| 4 | -0.1798 | -1000.0000 | -2.70 | 2.98 | 3 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51776
- **Expected rows**: 51897
- **Missing rows**: 121
- **Forward-fill count**: 359
- **Forward-fill fraction**: 0.006933714462299134
- **Longest gap (seconds)**: 8400

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -1.5107% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -1.5106914816369907
- **Trade count**: 2

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1977 <= 0; recent PnL -0.0089% < 0; recent trades 4 < 5
- **Objective score**: -0.19773134255826885
- **PnL %**: -0.008854975911006435
- **Trade count**: 4

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.031142093746622065
- **Trade count**: 1

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.1913348411417011
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | -0.0937, -0.1717 |
| take_profit | -0.1913, -0.1913 |
| cooldown_time | -0.1974, -0.1913 |
| total_amount_quote | -0.1871, -0.1910 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.38829746033893864
- **Max CV**: 0.5402948210342315
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.1702 | 0.017605222087319808 | 0.029323514307985358 | 0.021342430239884764 |
| take_profit | 0.5403 | 0.008747021449403635 | 0.05334205991373632 | 0.02811858430765743 |
| cooldown_time | 0.3947 | 1219.0 | 15082.0 | 9398.1 |
| total_amount_quote | 0.4479 | 173.57382670209472 | 959.9010047688187 | 509.17956690112453 |

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
| recent_pnl | >= 0 | -1.5106914816369907 | FAIL |
| recent_trades | >= 5 | 2 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-1000.0, pnl=-1.5106914816369907, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -1.5107% < 0; recent trades 2 < 5 |
| recent_14d_info | FAIL | informational only; score=-0.19773134255826885, pnl=-0.008854975911006435, trades=4, reason=recent objective score -0.1977 <= 0; recent PnL -0.0089% < 0; recent trades 4 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.031142093746622065, trades=1, reason=recent objective score -1000.0000 <= 0; recent trades 1 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.38829746033893864 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51776 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -1.5107% < 0; recent trades 2 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1977 <= 0; recent PnL -0.0089% < 0; recent trades 4 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 1 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | false | NOT_RUN | — | — | — | not executed |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51776
- **Pre-release bars**: 43832
- **Dev bars**: 35066
- **Holdout bars**: 8766
- **Recent 28d bars**: 7944
- **Recent window start**: 1774053000

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T01:31:05.218750+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 351
