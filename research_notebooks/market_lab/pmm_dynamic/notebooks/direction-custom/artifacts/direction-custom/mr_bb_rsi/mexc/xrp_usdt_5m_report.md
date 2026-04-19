# PMM Dynamic Optimization Report: mexc_XRP-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 11:22:04 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T11:22:04.116463+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 1872 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XRP-USDT
- **interval**: 5m
- **n_candles**: 51661
- **dataset_hash**: 3f7d0742a3157cd65ae675a560e63bf9f2507f9e46ced1e04107fb172ea5800c
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 830.2815883184182
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 27 |
| bb_length | 168 |
| bb_std | 1.5631300502892047 |
| bbp_entry_threshold | 0.38187744473922536 |
| cooldown_time | 3490 |
| max_atr_pct_for_entry | 0.022425647903267634 |
| min_volume_quantile | 0.3339407605266258 |
| rsi_entry_threshold | 35.071667618174786 |
| rsi_length | 11 |
| stop_loss | 0.041227355881680694 |
| take_profit | 0.008183672874922606 |
| take_profit_order_type | MARKET |
| time_limit | 175027 |
| total_amount_quote | 830.2815883184182 |
| trailing_stop_activation | 0.00038678846721465563 |
| trailing_stop_delta | 0.006171875927967905 |
| trend_ema_length | 377 |
| use_trend_filter | False |
| volume_filter_window | 338 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 830.2815883184182 |
| Selected | 830.2815883184182 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 18.7695
- **Net PnL (quote)**: 155.8394
- **Sharpe Ratio**: 2.6662
- **Max Drawdown %**: 6.4458
- **Profit Factor**: 2.3415286864141414
- **Trade Count**: 174
- **Total Fees (quote)**: 57.4982
- **Maker Fees**: 28.7277
- **Taker Fees**: 28.7704
- **Fee Drag %**: 6.9251

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0882
- **PnL Component**: 0.1720
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0483
- **Fee Drag Component**: -0.0346
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1789**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.85 | 2.45 | 2.09 | 22 | -0.1236 | n/a |
| 1 | 0.69 | 3.68 | 1.07 | 15 | -0.1440 | n/a |
| 2 | -1.00 | -5.70 | 1.04 | 13 | -0.1674 | n/a |
| 3 | 0.64 | 2.11 | 1.78 | 19 | -0.1347 | n/a |
| 4 | -1.51 | -8.99 | 1.57 | 2 | -1000.0000 | n/a |
| 5 | -1.17 | -2.49 | 2.15 | 9 | -0.1937 | n/a |
| 6 | 1.16 | 6.44 | 0.49 | 7 | -0.1656 | n/a |
| 7 | -1.38 | -5.37 | 2.15 | 9 | -0.1959 | n/a |
| 8 | 0.23 | 1.52 | 0.44 | 5 | -0.1818 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 15.31 | 2.20 | 6.63 | 0.0399 |
| fees_2x | 11.84 | 1.73 | 7.03 | -0.0110 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 18.77 | 2.67 | 6.45 | 0.0882 |
| very_low_liquidity | 18.77 | 2.67 | 6.45 | 0.0882 |
| high_slippage | 10.10 | 1.50 | 7.65 | 0.0034 |
| extreme_slippage | -4.68 | -0.80 | 10.94 | -0.2126 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 11.00 | 1.48 | 9.42 | -0.2299 |
| spread_widen_25bps | -1.01 | -0.13 | 4.93 | -0.0986 |
| thin_book | -2.75 | -1.88 | 4.20 | -0.1946 |
| very_thin_book | 1.83 | 1.11 | 1.52 | -0.1134 |
| entry_spread_stress | -3.47 | -0.26 | 13.61 | -0.4071 |
| combined_market_deterioration | -4.32 | -1.51 | 7.97 | -0.1810 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8763
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0027)
- **Trend**: ranging (efficiency: 0.0011)
- **Best holdout score**: -0.1064 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9559 | -0.2356 | -3.00 | 3.76 | 6 |
| 1 | -0.1187 | -0.1064 | 2.01 | 3.84 | 27 |
| 2 | -0.1213 | -0.2223 | -2.41 | 2.48 | 6 |
| 3 | -0.1262 | -0.1140 | -1.66 | 2.70 | 32 |
| 4 | -0.1262 | -0.3485 | -3.41 | 3.48 | 5 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51661
- **Expected rows**: 51883
- **Missing rows**: 222
- **Forward-fill count**: 902
- **Forward-fill fraction**: 0.017459979481620563
- **Longest gap (seconds)**: 7800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1765 <= 0; recent PnL -0.2663% < 0
- **Objective score**: -0.1765061226903715
- **PnL %**: -0.26628275597099466
- **Trade count**: 9

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2391 <= 0; recent PnL -0.3950% < 0
- **Objective score**: -0.23914619281157512
- **PnL %**: -0.3949762713713459
- **Trade count**: 7

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -0.4114% < 0; recent trades 3 < 5
- **Objective score**: -1000.0
- **PnL %**: -0.41143743537382405
- **Trade count**: 3

## Sensitivity Analysis

- **Sensitivity penalty**: 0.5384615384615384
- **Baseline score**: 0.08190360951629169
- **Sign flips**: 6
- **Collapse count**: 8
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | 0.0950, -0.2992 |
| bb_std | 0.0815, -0.1223 |
| bbp_entry_threshold | -0.1171, 0.0685 |
| rsi_length | 0.0314, 0.1213 |
| rsi_entry_threshold | -0.1679, -0.2346 |
| trend_ema_length | 0.0819, 0.0819 |
| max_atr_pct_for_entry | 0.0819, 0.0819 |
| volume_filter_window | 0.1220, 0.0711 |
| min_volume_quantile | 0.0050, 0.1057 |
| stop_loss | 0.0655, 0.1035 |
| take_profit | 0.0819, 0.0819 |
| cooldown_time | -0.0045, 0.1254 |
| total_amount_quote | 0.0819, 0.0819 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5835972406714607
- **Max CV**: 1.161553101704517
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3035 | 0.03487711215819329 | 0.07912751133248637 | 0.05787661334794009 |
| take_profit | 0.4767 | 0.005658330331067333 | 0.026295895966506232 | 0.0140789922852229 |
| cooldown_time | 1.1616 | 1027.0 | 22460.0 | 6531.4 |
| total_amount_quote | 0.3927 | 125.6333150888971 | 538.7591825094662 | 312.50464395831443 |

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
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.1765061226903715 | FAIL |
| recent_pnl | >= 0 | -0.26628275597099466 | FAIL |
| recent_trades | >= 5 | 9 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.5384615384615384 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.23556434530264317 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=0.5384615384615384 |
| recent_28d | FAIL | score=-0.1765061226903715, pnl=-0.26628275597099466, trades=9, reason=recent objective score -0.1765 <= 0; recent PnL -0.2663% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.23914619281157512, pnl=-0.3949762713713459, trades=7, reason=recent objective score -0.2391 <= 0; recent PnL -0.3950% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-0.41143743537382405, trades=3, reason=recent objective score -1000.0000 <= 0; recent PnL -0.4114% < 0; recent trades 3 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5835972406714607 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51661 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1765 <= 0; recent PnL -0.2663% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2391 <= 0; recent PnL -0.3950% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -0.4114% < 0; recent trades 3 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51661
- **Pre-release bars**: 43818
- **Dev bars**: 35055
- **Holdout bars**: 8763
- **Recent 28d bars**: 7843
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T11:22:04.116463+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 1872
- **validation_status**: validated_fail
