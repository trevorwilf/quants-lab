# PMM Dynamic Optimization Report: mexc_DOGE-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 00:23:14 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T00:23:14.539373+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 407 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOGE-USDT
- **interval**: 5m
- **n_candles**: 51785
- **dataset_hash**: 072b6d494891ac30e93af2480acab45c04139ebd0f8af4fcc471ff05a0b6a256
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 557.6043017708929
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 27 |
| bb_length | 86 |
| bb_std | 1.8266897931662145 |
| bbp_entry_threshold | 0.20922906066387814 |
| cooldown_time | 13978 |
| max_atr_pct_for_entry | 0.01597742070595855 |
| min_volume_quantile | 0.3832773251897112 |
| rsi_entry_threshold | 48.692931822960205 |
| rsi_length | 19 |
| stop_loss | 0.05368046104858742 |
| take_profit | 0.006041229422215764 |
| take_profit_order_type | LIMIT |
| time_limit | 119095 |
| total_amount_quote | 557.6043017708929 |
| trailing_stop_activation | 0.0002319930161702984 |
| trailing_stop_delta | 0.015198819146674404 |
| trend_ema_length | 376 |
| use_trend_filter | True |
| volume_filter_window | 567 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 557.6043017708929 |
| Selected | 557.6043017708929 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2.8949
- **Net PnL (quote)**: 16.1419
- **Sharpe Ratio**: 0.7677
- **Max Drawdown %**: 5.0334
- **Profit Factor**: 1.4720575452889033
- **Trade Count**: 65
- **Total Fees (quote)**: 14.2787
- **Maker Fees**: 7.1363
- **Taker Fees**: 7.1424
- **Fee Drag %**: 2.5607

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0223
- **PnL Component**: 0.0285
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0378
- **Fee Drag Component**: -0.0128
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 1.61 | 0.46 | 5.11 | -0.0418 |
| fees_2x | 0.33 | 0.14 | 5.19 | -0.0615 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 2.89 | 0.77 | 5.03 | -0.0223 |
| very_low_liquidity | 2.89 | 0.77 | 5.03 | -0.0224 |
| high_slippage | -0.31 | -0.02 | 5.23 | -0.0554 |
| extreme_slippage | -1.05 | -0.23 | 5.45 | -0.1068 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -0.70 | -0.09 | 5.74 | -0.0633 |
| spread_widen_25bps | -0.06 | 0.06 | 6.90 | -0.0770 |
| thin_book | -5.45 | -3.59 | 5.45 | -1000.0000 |
| very_thin_book | -5.45 | -3.59 | 5.45 | -1000.0000 |
| entry_spread_stress | 0.22 | 0.12 | 5.91 | -0.0554 |
| combined_market_deterioration | 0.57 | 0.20 | 5.08 | -0.0478 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0031)
- **Trend**: ranging (efficiency: 0.0060)
- **Best holdout score**: -0.1363 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0112 | -0.2393 | -2.10 | 2.46 | 9 |
| 1 | -0.1753 | -1000.0000 | -1.34 | 1.61 | 1 |
| 2 | -0.1763 | -1000.0000 | -2.63 | 2.99 | 3 |
| 3 | -0.1790 | -0.1363 | 1.99 | 1.26 | 14 |
| 4 | -0.1790 | -0.1515 | 0.81 | 2.74 | 16 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51785
- **Expected rows**: 51841
- **Missing rows**: 56
- **Forward-fill count**: 111
- **Forward-fill fraction**: 0.00214347784107367
- **Longest gap (seconds)**: 8100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1784 <= 0; recent PnL -1.0780% < 0
- **Objective score**: -0.17840104118654643
- **PnL %**: -1.0779977479815317
- **Trade count**: 20

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2251 <= 0; recent PnL -1.4768% < 0
- **Objective score**: -0.22514229140644176
- **PnL %**: -1.4767666509471293
- **Trade count**: 6

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2241 <= 0; recent PnL -1.3537% < 0
- **Objective score**: -0.22408305742047657
- **PnL %**: -1.3537493252269086
- **Trade count**: 5

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.11292089549739906
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | -0.1314, -0.0946 |
| take_profit | -0.1129, -0.1129 |
| cooldown_time | -0.1050, -0.1127 |
| total_amount_quote | -0.1129, -0.1129 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4708003487860924
- **Max CV**: 0.7681556608379033
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3336 | 0.026312532592985514 | 0.07266468613757349 | 0.052201370093272456 |
| take_profit | 0.3952 | 0.006041229422215764 | 0.019771894824971017 | 0.010373618419191348 |
| cooldown_time | 0.7682 | 1875.0 | 35473.0 | 14369.0 |
| total_amount_quote | 0.3863 | 226.5665491408592 | 936.8877325871366 | 627.8112646365109 |

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
| recent_objective | > 0 | -0.17840104118654643 | FAIL |
| recent_pnl | >= 0 | -1.0779977479815317 | FAIL |
| recent_trades | >= 5 | 20 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.23933772690052266 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.17840104118654643, pnl=-1.0779977479815317, trades=20, reason=recent objective score -0.1784 <= 0; recent PnL -1.0780% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.22514229140644176, pnl=-1.4767666509471293, trades=6, reason=recent objective score -0.2251 <= 0; recent PnL -1.4768% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.22408305742047657, pnl=-1.3537493252269086, trades=5, reason=recent objective score -0.2241 <= 0; recent PnL -1.3537% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4708003487860924 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51785 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1784 <= 0; recent PnL -1.0780% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2251 <= 0; recent PnL -1.4768% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2241 <= 0; recent PnL -1.3537% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | false | NOT_RUN | — | — | — | not executed |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51785
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8009
- **Recent window start**: 1774029600

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T00:23:14.539373+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 407
