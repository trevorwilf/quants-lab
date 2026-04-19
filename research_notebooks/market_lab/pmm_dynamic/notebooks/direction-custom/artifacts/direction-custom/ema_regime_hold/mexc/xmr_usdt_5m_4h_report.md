# PMM Dynamic Optimization Report: mexc_XMR-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:18:44 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:18:44.796219+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 492 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XMR-USDT
- **interval**: 5m+4h
- **n_candles**: 103804
- **dataset_hash**: fd23956e2f6d4d738969a70914f7c32d9f035e5b5c773f09458ca2291bcd4712
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 863.2573741082017
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 62807 |
| min_volume_quantile | 0.599225560382437 |
| regime_adx_length | 25 |
| regime_adx_threshold | 12.141717180122303 |
| regime_ema_fast | 98 |
| regime_ema_slow | 142 |
| stop_loss | 0.0505058767229565 |
| take_profit | 0.056323205507281295 |
| take_profit_order_type | MARKET |
| time_limit | 40639 |
| total_amount_quote | 863.2573741082017 |
| trailing_stop_activation | 0.00021010041195013065 |
| trailing_stop_delta | 0.022977727319118554 |
| volume_filter_window | 339 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 863.2573741082017 |
| Selected | 863.2573741082017 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0020
- **Net PnL (quote)**: -8.6501
- **Sharpe Ratio**: -0.1309
- **Max Drawdown %**: 5.1156
- **Profit Factor**: 0.8972499425567171
- **Trade Count**: 95
- **Total Fees (quote)**: 17.1697
- **Maker Fees**: 8.5840
- **Taker Fees**: 8.5857
- **Fee Drag %**: 1.9889

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0585
- **PnL Component**: -0.0101
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0384
- **Fee Drag Component**: -0.0099
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1917**

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
| 8 | 0.98 | 3.23 | 0.88 | 18 | -0.1268 | n/a |
| 9 | 0.03 | 0.17 | 5.15 | 26 | -0.3087 | n/a |
| 10 | 1.17 | 1.76 | 3.20 | 35 | -0.0763 | n/a |
| 11 | 6.04 | 5.78 | 4.29 | 26 | -0.0745 | n/a |
| 12 | -1.67 | -1.72 | 4.60 | 32 | -0.3706 | n/a |
| 13 | 2.17 | 4.95 | 2.15 | 33 | -0.0662 | n/a |
| 14 | -3.53 | -7.00 | 5.11 | 13 | -0.2244 | n/a |
| 15 | 2.74 | 3.48 | 2.92 | 22 | -0.1106 | n/a |
| 16 | 5.86 | 5.56 | 3.15 | 25 | -0.1591 | n/a |
| 17 | 0.40 | 2.29 | 0.87 | 4 | -0.1870 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 20 | 0.08 | 0.26 | 1.74 | 6 | -0.1889 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.08 | -0.23 | 4.30 | -0.0586 |
| fees_2x | -1.58 | -0.35 | 4.33 | -0.0663 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.44 | -0.46 | 3.44 | -0.1404 |
| very_low_liquidity | -4.76 | -0.79 | 9.45 | -0.1276 |
| high_slippage | -1.82 | -0.42 | 4.32 | -0.0638 |
| extreme_slippage | -1.16 | -0.14 | 5.38 | -0.0661 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.45 | -0.35 | 4.96 | -0.1038 |
| spread_widen_25bps | -3.52 | -0.78 | 5.12 | -0.1688 |
| thin_book | -2.37 | -0.99 | 3.06 | -0.2158 |
| very_thin_book | -2.11 | -0.87 | 3.07 | -0.2252 |
| entry_spread_stress | -1.77 | -0.43 | 4.97 | -0.1072 |
| combined_market_deterioration | -4.77 | -1.15 | 6.40 | -0.1625 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19203
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0045)
- **Trend**: ranging (efficiency: 0.0155)
- **Best holdout score**: -0.2207 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0293 | -0.2207 | -3.53 | 7.66 | 19 |
| 1 | -0.4047 | -0.2502 | -2.69 | 7.08 | 8 |
| 2 | -0.4568 | -0.2507 | -3.51 | 5.02 | 6 |
| 3 | -0.4986 | -1000.0000 | -3.72 | 5.74 | 2 |
| 4 | -0.5516 | -1000.0000 | -1.87 | 5.65 | 2 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103804
- **Expected rows**: 104082
- **Missing rows**: 278
- **Forward-fill count**: 150
- **Forward-fill fraction**: 0.0014450310199992293
- **Longest gap (seconds)**: 29100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2168 <= 0; recent PnL -0.7897% < 0; recent trades 4 < 5
- **Objective score**: -0.21676220561697715
- **PnL %**: -0.789728491641525
- **Trade count**: 4

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2168 <= 0; recent PnL -0.7897% < 0; recent trades 4 < 5
- **Objective score**: -0.21682612433427467
- **PnL %**: -0.789728491641525
- **Trade count**: 4

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2170 <= 0; recent PnL -0.7897% < 0; recent trades 4 < 5
- **Objective score**: -0.21697068468909292
- **PnL %**: -0.789728491641525
- **Trade count**: 4

## Sensitivity Analysis

- **Sensitivity penalty**: 0.5
- **Baseline score**: -0.05847976172024894
- **Sign flips**: 3
- **Collapse count**: 7
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.0585, -0.0585 |
| regime_ema_slow | -0.0585, -0.0929 |
| regime_adx_length | -0.2512, 0.0688 |
| regime_adx_threshold | -0.0016, 0.0781 |
| volume_filter_window | -0.1260, -0.2215 |
| min_volume_quantile | -0.0779, -0.1800 |
| stop_loss | -0.0666, -0.0575 |
| take_profit | -0.0585, -0.0585 |
| cooldown_time | 0.0724, -0.1774 |
| total_amount_quote | -0.0591, -0.0936 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4589525676478915
- **Max CV**: 0.5504112743841855
- **Clustered params**: stop_loss, cooldown_time
- **Scattered params**: take_profit, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3118 | 0.022961564713937427 | 0.0825158425491216 | 0.055062194596098034 |
| take_profit | 0.5017 | 0.01645477416780652 | 0.0975378740598951 | 0.05026376831071021 |
| cooldown_time | 0.4719 | 4806.0 | 83356.0 | 56104.9 |
| total_amount_quote | 0.5504 | 106.24832349355319 | 995.5531452501601 | 516.7602651403199 |

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
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.21676220561697715 | FAIL |
| recent_pnl | >= 0 | -0.789728491641525 | FAIL |
| recent_trades | >= 5 | 4 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.5 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.22071173467290212 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=0.5 |
| recent_28d | FAIL | score=-0.21676220561697715, pnl=-0.789728491641525, trades=4, reason=recent objective score -0.2168 <= 0; recent PnL -0.7897% < 0; recent trades 4 < 5 |
| recent_14d_info | FAIL | informational only; score=-0.21682612433427467, pnl=-0.789728491641525, trades=4, reason=recent objective score -0.2168 <= 0; recent PnL -0.7897% < 0; recent trades 4 < 5 |
| recent_7d_info | FAIL | informational only; score=-0.21697068468909292, pnl=-0.789728491641525, trades=4, reason=recent objective score -0.2170 <= 0; recent PnL -0.7897% < 0; recent trades 4 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4589525676478915 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103804 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2168 <= 0; recent PnL -0.7897% < 0; recent trades 4 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2168 <= 0; recent PnL -0.7897% < 0; recent trades 4 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2170 <= 0; recent PnL -0.7897% < 0; recent trades 4 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103804
- **Pre-release bars**: 96017
- **Dev bars**: 76814
- **Holdout bars**: 19203
- **Recent 28d bars**: 7787
- **Recent window start**: 1774097400

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:18:44.796219+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 492
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
