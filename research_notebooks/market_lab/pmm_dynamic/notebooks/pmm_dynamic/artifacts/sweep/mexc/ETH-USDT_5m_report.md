# PMM Dynamic Optimization Report: mexc_ETH-USDT_5m_sweep_v1

Generated: 2026-04-09 03:51:49 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T03:51:49.364522+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 8821 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ETH-USDT
- **interval**: 5m
- **n_candles**: 51871
- **dataset_hash**: fad660a10cd65d6e25b77e1bdc2d3cfe9c3bd6f75993edc97b16107c5f3b9b6e
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 949.8955818322721
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.900171941367693 |
| buy_n_levels | 5 |
| buy_side_weight | 0.206590523508763 |
| buy_spread_base | 3.6051656266224916 |
| buy_spread_ratio | 2.3610014264206463 |
| cooldown_time | 6372 |
| executor_refresh_time | 2932 |
| macd_fast | 16 |
| macd_signal | 8 |
| macd_slow | 47 |
| natr_length | 39 |
| sell_n_levels | 6 |
| sell_spread_base | 3.307516937818232 |
| sell_spread_ratio | 2.2104477464433216 |
| stop_loss | 0.015323608705675515 |
| take_profit | 0.0065971832054465655 |
| time_limit | 101519 |
| total_amount_quote | 949.8955818322721 |
| trailing_stop_activation | 0.07943387237067989 |
| trailing_stop_delta | 0.011489970422122645 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 949.8955818322721 |
| Selected | 949.8955818322721 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.1936
- **Net PnL (quote)**: -20.8368
- **Sharpe Ratio**: -3.2972
- **Max Drawdown %**: 3.0460
- **Profit Factor**: 0.8326971387629523
- **Trade Count**: 654
- **Total Fees (quote)**: 3.2655
- **Maker Fees**: 2.7423
- **Taker Fees**: 0.5232
- **Fee Drag %**: 0.3438
- **TP Min-Notional Failures**: 3430 :warning:
  > 3430 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0610
- **PnL Component**: -0.0222
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0228
- **Fee Drag Component**: -0.0017
- **Inventory Component**: -0.0141
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0125**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.05 | 2.18 | 0.13 | 47 | -0.0139 | n/a |
| 1 | -0.13 | -5.42 | 0.23 | 56 | -0.0046 | n/a |
| 2 | 0.03 | 2.80 | 0.07 | 48 | -0.0097 | n/a |
| 3 | 0.06 | 6.67 | 0.03 | 45 | -0.0211 | n/a |
| 4 | -0.39 | -15.58 | 0.39 | 59 | -0.0252 | n/a |
| 5 | -0.15 | -5.32 | 0.16 | 50 | -0.0042 | n/a |
| 6 | 0.01 | 0.78 | 0.04 | 54 | -0.0017 | n/a |
| 7 | 0.02 | 1.41 | 0.08 | 45 | -0.0219 | n/a |
| 8 | -0.13 | -4.16 | 0.23 | 58 | -0.0095 | n/a |

## Stress Test Results

Worst Scenario: **entry_spread_stress** (score: -0.0795)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.37 | -3.55 | 3.09 | -0.0640 |
| fees_2x | -2.54 | -3.81 | 3.20 | -0.0675 |
| latency_plus1 | -2.12 | -3.16 | 3.08 | -0.0604 |
| latency_plus2 | -2.35 | -3.67 | 3.11 | -0.0630 |
| latency_plus3 | -2.36 | -3.68 | 3.15 | -0.0634 |
| low_liquidity | -2.19 | -3.30 | 3.05 | -0.0610 |
| very_low_liquidity | -2.19 | -3.30 | 3.05 | -0.0610 |
| high_slippage | -2.33 | -3.50 | 3.09 | -0.0628 |
| extreme_slippage | -2.61 | -3.89 | 3.27 | -0.0670 |
| combined_adverse | -2.42 | -3.59 | 3.16 | -0.0650 |
| spread_widen_10bps | -2.94 | -4.10 | 3.61 | -0.0741 |
| spread_widen_25bps | -3.12 | -5.13 | 3.62 | -0.0742 |
| thin_book | -2.90 | -6.95 | 3.24 | -0.0627 |
| very_thin_book | -1.01 | -6.04 | 1.08 | -0.0216 |
| entry_spread_stress | -3.26 | -4.43 | 3.89 | -0.0795 |
| combined_market_deterioration | -3.07 | -5.94 | 3.57 | -0.0705 |
| severe_adverse | -3.72 | -9.28 | 3.80 | -0.0755 |

## Holdout Validation

- **Holdout bars**: 8762
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0029)
- **Trend**: ranging (efficiency: 0.0009)
- **Best holdout score**: -0.0023 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0703 | -0.0023 | 0.01 | 0.09 | 108 |
| 1 | -0.0033 | -0.0303 | -0.21 | 1.14 | 237 |
| 2 | -0.0037 | -0.1580 | -5.09 | 6.00 | 614 |
| 3 | -0.0038 | -0.0681 | -2.22 | 2.68 | 359 |
| 4 | -0.0038 | -0.0203 | -0.47 | 0.73 | 370 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51871
- **Expected rows**: 51877
- **Missing rows**: 6
- **Forward-fill count**: 247
- **Forward-fill fraction**: 0.0047618129590715425
- **Longest gap (seconds)**: 1800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0074 <= 0; recent PnL -0.1350% < 0
- **Objective score**: -0.007361465846072335
- **PnL %**: -0.1349702071204571
- **Trade count**: 109

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0091 <= 0; recent PnL -0.0575% < 0
- **Objective score**: -0.009124227063130763
- **PnL %**: -0.0575287311620055
- **Trade count**: 58

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1364 <= 0
- **Objective score**: -0.13637393237368406
- **PnL %**: 0.006624721020756397
- **Trade count**: 25

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: -0.07162082487545436
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1571, -0.0990 |
| sell_spread_base | -0.0664, -0.0777 |
| stop_loss | -0.0691, -0.0824 |
| take_profit | -0.0752, -0.0707 |
| executor_refresh_time | -0.0758, -0.0894 |
| cooldown_time | -0.0812, -0.0939 |
| total_amount_quote | -0.0867, -0.1800 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3677454001922165
- **Max CV**: 0.7996433947467364
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0902 | 2.866831059573829 | 3.7861626524985654 | 3.3992212969931037 |
| buy_spread_ratio | 0.0684 | 2.158317518338161 | 2.666128529738518 | 2.337677781966934 |
| sell_spread_base | 0.7984 | 0.20248966728945533 | 2.7428122347487847 | 1.051315764446688 |
| sell_spread_ratio | 0.2159 | 1.3742253416730152 | 2.759998153143493 | 1.9481678512448686 |
| buy_side_weight | 0.3583 | 0.20608617222217682 | 0.5963529710603798 | 0.3814787048248366 |
| amount_skew | 0.1420 | 2.7025203100808897 | 3.9423416089895382 | 3.3937002054421797 |
| stop_loss | 0.7996 | 0.010208521933361083 | 0.05442837815905617 | 0.016900721710647718 |
| take_profit | 0.5978 | 0.005404170090034959 | 0.02117035024986708 | 0.010959095372781547 |
| executor_refresh_time | 0.5412 | 1533.0 | 10111.0 | 5171.8 |
| cooldown_time | 0.3013 | 960.0 | 4453.0 | 3201.3 |
| total_amount_quote | 0.1320 | 616.2731169569104 | 996.222507836957 | 844.0328737202437 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.0
- **supports_post_only**: True
- **connector**: mexc
- **fill_participation_rate**: 0.1
- **latency_bars**: 1
- **slippage_bps**: 5.0
- **touch_through**: False
- **maker_fill_probability**: 1.0
- **refresh_close_mode**: market_close

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: PASS
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
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
| recent_objective | > 0 | -0.007361465846072335 | FAIL |
| recent_pnl | >= 0 | -0.1349702071204571 | FAIL |
| recent_trades | >= 5 | 109 | PASS |
| worst_stress | > -10 | -0.07953280100030985 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.00227565585883242 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=entry_spread_stress score=-0.07953280100030985 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.007361465846072335, pnl=-0.1349702071204571, trades=109, reason=recent objective score -0.0074 <= 0; recent PnL -0.1350% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.009124227063130763, pnl=-0.0575287311620055, trades=58, reason=recent objective score -0.0091 <= 0; recent PnL -0.0575% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.13637393237368406, pnl=0.006624721020756397, trades=25, reason=recent objective score -0.1364 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3677454001922165 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51871 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0074 <= 0; recent PnL -0.1350% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0091 <= 0; recent PnL -0.0575% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1364 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51871
- **Pre-release bars**: 43812
- **Dev bars**: 35050
- **Holdout bars**: 8762
- **Recent 28d bars**: 8059
- **Recent window start**: 1773283200

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T03:51:49.364522+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 8821
