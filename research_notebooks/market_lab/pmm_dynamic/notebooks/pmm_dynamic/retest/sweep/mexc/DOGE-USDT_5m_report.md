# PMM Dynamic Optimization Report: mexc_DOGE-USDT_5m_retest_20260408

Generated: 2026-04-08 07:39:10 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T07:39:10.805993+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 4728 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOGE-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 1d58466299189a579d14bbf75d864cfaaa4e3e3d11f22088a619d830161b2fd4
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 620.0738460873774
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.2930299511371857 |
| buy_n_levels | 4 |
| buy_side_weight | 0.28861193843326727 |
| buy_spread_base | 3.1231350345050153 |
| buy_spread_ratio | 2.3980191911905977 |
| cooldown_time | 3918 |
| executor_refresh_time | 13787 |
| macd_fast | 6 |
| macd_signal | 9 |
| macd_slow | 21 |
| natr_length | 27 |
| sell_n_levels | 5 |
| sell_spread_base | 4.995502722335066 |
| sell_spread_ratio | 2.7703881664029746 |
| stop_loss | 0.01402205500862472 |
| take_profit | 0.00539947659923264 |
| time_limit | 163855 |
| total_amount_quote | 620.0738460873774 |
| trailing_stop_activation | 0.0023982470855810206 |
| trailing_stop_delta | 0.023740469531214007 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 620.0738460873774 |
| Selected | 620.0738460873774 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.3136
- **Net PnL (quote)**: -14.3458
- **Sharpe Ratio**: -0.3686
- **Max Drawdown %**: 6.6024
- **Profit Factor**: 0.6124572925335316
- **Trade Count**: 496
- **Total Fees (quote)**: 2.7998
- **Maker Fees**: 2.2953
- **Taker Fees**: 0.5044
- **Fee Drag %**: 0.4515

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0834
- **PnL Component**: -0.0234
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0495
- **Fee Drag Component**: -0.0023
- **Inventory Component**: -0.0081
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0072**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.20 | -6.49 | 0.32 | 52 | -0.0081 | n/a |
| 1 | -0.06 | -2.39 | 0.10 | 55 | -0.0051 | n/a |
| 2 | 0.05 | 1.73 | 0.14 | 52 | -0.0043 | n/a |
| 3 | 0.11 | 4.48 | 0.06 | 53 | -0.0031 | n/a |
| 4 | -0.72 | -8.27 | 0.74 | 66 | -0.0492 | n/a |
| 5 | -0.03 | -0.36 | 0.29 | 61 | -0.0063 | n/a |
| 6 | -0.17 | -5.24 | 0.25 | 49 | -0.0113 | n/a |
| 7 | -0.08 | -2.80 | 0.12 | 50 | -0.0054 | n/a |
| 8 | -0.13 | -3.57 | 0.23 | 58 | -0.0069 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1086)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.54 | -0.41 | 6.61 | -0.0868 |
| fees_2x | -2.77 | -0.46 | 6.61 | -0.0903 |
| latency_plus1 | -2.31 | -0.37 | 6.60 | -0.0834 |
| latency_plus2 | -2.31 | -0.37 | 6.60 | -0.0834 |
| latency_plus3 | -2.30 | -0.37 | 6.60 | -0.0832 |
| low_liquidity | -2.31 | -0.37 | 6.60 | -0.0834 |
| very_low_liquidity | -2.31 | -0.37 | 6.60 | -0.0834 |
| high_slippage | -2.52 | -0.41 | 6.61 | -0.0855 |
| extreme_slippage | -2.92 | -0.49 | 6.62 | -0.0898 |
| combined_adverse | -2.74 | -0.45 | 6.61 | -0.0890 |
| spread_widen_10bps | -2.76 | -0.45 | 6.69 | -0.0886 |
| spread_widen_25bps | -3.53 | -0.60 | 6.73 | -0.0969 |
| thin_book | -3.50 | -0.63 | 6.14 | -0.0908 |
| very_thin_book | -3.18 | -1.09 | 3.52 | -0.0671 |
| entry_spread_stress | -3.25 | -0.54 | 6.69 | -0.0936 |
| combined_market_deterioration | -4.44 | -2.56 | 4.51 | -0.0906 |
| severe_adverse | -4.67 | -0.77 | 6.65 | -0.1086 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0033)
- **Trend**: ranging (efficiency: 0.0035)
- **Best holdout score**: -0.0047 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0960 | -0.0087 | -0.22 | 0.34 | 115 |
| 1 | -0.0036 | -0.0082 | -0.19 | 0.22 | 217 |
| 2 | -0.0038 | -0.0047 | -0.10 | 0.20 | 199 |
| 3 | -0.0039 | -0.1715 | -2.15 | 2.18 | 432 |
| 4 | -0.0039 | -0.0957 | -3.61 | 4.05 | 532 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 86
- **Forward-fill fraction**: 0.0016589186165390328
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0081 <= 0; recent PnL -0.1743% < 0
- **Objective score**: -0.0081225591854472
- **PnL %**: -0.1743220490400723
- **Trade count**: 104

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0064 <= 0; recent PnL -0.1432% < 0
- **Objective score**: -0.006438909714408596
- **PnL %**: -0.1432466706686381
- **Trade count**: 51

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1297 <= 0; recent PnL -0.0396% < 0
- **Objective score**: -0.12973210176094524
- **PnL %**: -0.03957489467603928
- **Trade count**: 19

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.0906800532775577
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0869, -0.0998 |
| sell_spread_base | -0.0905, -0.0893 |
| stop_loss | -0.0844, -0.0936 |
| take_profit | -0.0902, -0.0896 |
| executor_refresh_time | -0.1161, -0.1013 |
| cooldown_time | -0.0935, -0.0876 |
| total_amount_quote | -0.0907, -0.0897 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3047424041658451
- **Max CV**: 1.301012824477827
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1453 | 2.3283208902407395 | 3.357598304647886 | 2.8272090779550743 |
| buy_spread_ratio | 0.0799 | 1.9524350105115154 | 2.618000290345425 | 2.4297917949010635 |
| sell_spread_base | 1.3010 | 0.2171069271680639 | 4.419798539723029 | 1.0040890979999904 |
| sell_spread_ratio | 0.1943 | 1.296680919752768 | 2.7074497062146343 | 1.9329496999980385 |
| buy_side_weight | 0.2189 | 0.2365973171508681 | 0.5024299775794907 | 0.3531709445476111 |
| amount_skew | 0.0771 | 2.999369675924649 | 3.817918608291029 | 3.2817550340040986 |
| stop_loss | 0.4312 | 0.010272119859728 | 0.029646877141945884 | 0.013487008420587398 |
| take_profit | 0.1947 | 0.005159734114686441 | 0.008885568711187435 | 0.005963624954351939 |
| executor_refresh_time | 0.2795 | 3923.0 | 11261.0 | 8137.4 |
| cooldown_time | 0.3027 | 1527.0 | 5425.0 | 3779.6 |
| total_amount_quote | 0.1274 | 690.3244045299865 | 992.3319144114702 | 832.9536956897413 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: PASS
- walkforward_robust: PASS
- walkforward_positive_majority: **FAIL**
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.0081225591854472 | FAIL |
| recent_pnl | >= 0 | -0.1743220490400723 | FAIL |
| recent_trades | >= 5 | 104 | PASS |
| worst_stress | > -10 | -0.10860442916153976 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.008718499573538587 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.10860442916153976 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.0081225591854472, pnl=-0.1743220490400723, trades=104, reason=recent objective score -0.0081 <= 0; recent PnL -0.1743% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.006438909714408596, pnl=-0.1432466706686381, trades=51, reason=recent objective score -0.0064 <= 0; recent PnL -0.1432% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.12973210176094524, pnl=-0.03957489467603928, trades=19, reason=recent objective score -0.1297 <= 0; recent PnL -0.0396% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3047424041658451 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0081 <= 0; recent PnL -0.1743% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0064 <= 0; recent PnL -0.1432% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1297 <= 0; recent PnL -0.0396% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51841
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065
- **Recent window start**: 1773207600

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T07:39:10.805993+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 4728
