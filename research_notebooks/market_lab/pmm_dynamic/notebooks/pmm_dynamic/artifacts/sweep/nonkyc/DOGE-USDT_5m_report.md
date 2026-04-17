# PMM Dynamic Optimization Report: nonkyc_DOGE-USDT_5m_sweep_v1

Generated: 2026-04-09 18:50:16 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T18:50:16.139757+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 10696 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: DOGE-USDT
- **interval**: 5m
- **n_candles**: 52059
- **dataset_hash**: 9ffe8352662e5a1d8047b6c9a15c18e4777c14337132d02f8900dc2752ed283c
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 857.6969357489553
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.0159189209957624 |
| buy_n_levels | 8 |
| buy_side_weight | 0.2437084514652463 |
| buy_spread_base | 3.5242725015014833 |
| buy_spread_ratio | 1.7664806300573601 |
| cooldown_time | 4643 |
| executor_refresh_time | 13117 |
| macd_fast | 10 |
| macd_signal | 23 |
| macd_slow | 65 |
| natr_length | 27 |
| sell_n_levels | 8 |
| sell_spread_base | 4.959858475021874 |
| sell_spread_ratio | 1.9346693548505869 |
| stop_loss | 0.02574120992052785 |
| take_profit | 0.005653222572966151 |
| time_limit | 7744 |
| total_amount_quote | 857.6969357489553 |
| trailing_stop_activation | 0.012771690061224666 |
| trailing_stop_delta | 0.001958998420246453 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 857.6969357489553 |
| Selected | 857.6969357489553 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.2177
- **Net PnL (quote)**: -19.0209
- **Sharpe Ratio**: -3.1592
- **Max Drawdown %**: 2.7070
- **Profit Factor**: 0.5498511084679353
- **Trade Count**: 635
- **Total Fees (quote)**: 15.7186
- **Maker Fees**: 9.5445
- **Taker Fees**: 6.1741
- **Fee Drag %**: 1.8327
- **TP Min-Notional Failures**: 828 :warning:
  > 828 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0558
- **PnL Component**: -0.0224
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0203
- **Fee Drag Component**: -0.0092
- **Inventory Component**: -0.0039
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0276**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.68 | -14.77 | 0.72 | 72 | -0.0518 | n/a |
| 1 | -0.19 | -6.46 | 0.21 | 88 | -0.0064 | n/a |
| 2 | -0.47 | -12.30 | 0.51 | 84 | -0.0474 | n/a |
| 3 | -0.08 | -4.17 | 0.13 | 67 | -0.0065 | n/a |
| 4 | -0.43 | -2.93 | 0.64 | 85 | -0.0237 | n/a |
| 5 | -0.23 | -3.76 | 0.30 | 82 | -0.0206 | n/a |
| 6 | -0.24 | -6.77 | 0.25 | 89 | -0.0167 | n/a |
| 7 | -0.13 | -7.77 | 0.13 | 41 | -0.0409 | n/a |
| 8 | -0.42 | -9.72 | 0.44 | 52 | -0.0128 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.2366)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -3.13 | -4.45 | 3.50 | -0.0758 |
| fees_2x | -4.05 | -5.73 | 4.36 | -0.1024 |
| latency_plus1 | -2.22 | -3.19 | 2.71 | -0.0559 |
| latency_plus2 | -2.34 | -3.12 | 2.83 | -0.0580 |
| latency_plus3 | -2.56 | -3.83 | 3.05 | -0.0618 |
| low_liquidity | -2.86 | -4.34 | 3.43 | -0.0681 |
| very_low_liquidity | -4.02 | -6.70 | 4.17 | -0.0865 |
| high_slippage | -2.40 | -3.42 | 2.86 | -0.0588 |
| extreme_slippage | -2.76 | -3.94 | 3.17 | -0.0649 |
| combined_adverse | -4.01 | -6.12 | 4.43 | -0.0923 |
| spread_widen_10bps | -2.56 | -3.61 | 3.16 | -0.0630 |
| spread_widen_25bps | -3.54 | -5.46 | 4.09 | -0.0869 |
| thin_book | -4.27 | -8.15 | 4.47 | -0.1003 |
| very_thin_book | -5.23 | -11.23 | 5.25 | -0.1684 |
| entry_spread_stress | -2.47 | -3.47 | 3.15 | -0.0621 |
| combined_market_deterioration | -5.28 | -9.68 | 5.42 | -0.1293 |
| severe_adverse | -7.34 | -14.94 | 7.36 | -0.2366 |

## Holdout Validation

- **Holdout bars**: 8798
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0033)
- **Trend**: ranging (efficiency: 0.0008)
- **Best holdout score**: -0.0133 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1462 | -0.0133 | -0.41 | 0.43 | 160 |
| 1 | -0.0077 | -0.0452 | -1.02 | 1.48 | 383 |
| 2 | -0.0077 | -0.1091 | -3.30 | 3.39 | 721 |
| 3 | -0.0078 | -0.0859 | -3.07 | 3.16 | 479 |
| 4 | -0.0081 | -0.0433 | -1.65 | 1.70 | 621 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52059
- **Expected rows**: 52059
- **Missing rows**: 0
- **Forward-fill count**: 77
- **Forward-fill fraction**: 0.0014790910313298372
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0107 <= 0; recent PnL -0.4243% < 0
- **Objective score**: -0.010724431551175839
- **PnL %**: -0.42426976806245553
- **Trade count**: 74

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0981 <= 0
- **Objective score**: -0.09805063495486979
- **PnL %**: 0.027650858780450874
- **Trade count**: 26

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1600 <= 0; recent worst stress -1000.0000 < -10.0
- **Objective score**: -0.15999648357680532
- **PnL %**: 0.01400812554136235
- **Trade count**: 10

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.07116229404766666
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0497, -0.0866 |
| sell_spread_base | -0.0711, -0.0712 |
| stop_loss | -0.0675, -0.0642 |
| take_profit | -0.0704, -0.0747 |
| executor_refresh_time | -0.0694, -0.0623 |
| cooldown_time | -0.0802, -0.0612 |
| total_amount_quote | -0.0719, -0.0782 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.39295818479913813
- **Max CV**: 1.2313961203138493
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1837 | 2.2633232279446904 | 4.5199303065535235 | 3.637248524024443 |
| buy_spread_ratio | 0.1592 | 1.5654059740236315 | 2.5904936618283516 | 1.9479399864244011 |
| sell_spread_base | 1.2314 | 0.2444890982891824 | 4.278700815229848 | 0.9743378007467396 |
| sell_spread_ratio | 0.2170 | 1.2849798245701667 | 2.934826840357994 | 2.1024008356624138 |
| buy_side_weight | 0.1413 | 0.2023316675259117 | 0.2903961895935979 | 0.24265144913340936 |
| amount_skew | 0.1567 | 1.8305877373512356 | 2.8065041213544335 | 2.2055248750719283 |
| stop_loss | 0.8235 | 0.011688708511297627 | 0.07243289838309523 | 0.02196731815910086 |
| take_profit | 0.1544 | 0.0050267257096024125 | 0.00791561518969363 | 0.005683960333892638 |
| executor_refresh_time | 0.2837 | 4582.0 | 14060.0 | 10613.6 |
| cooldown_time | 0.8664 | 526.0 | 6822.0 | 2963.2 |
| total_amount_quote | 0.1052 | 696.6626206408135 | 999.6523060674432 | 876.630930341495 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
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
| recent_objective | > 0 | -0.010724431551175839 | FAIL |
| recent_pnl | >= 0 | -0.42426976806245553 | FAIL |
| recent_trades | >= 5 | 74 | PASS |
| worst_stress | > -10 | -0.23656564397352486 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.013281861735772255 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.23656564397352486 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.010724431551175839, pnl=-0.42426976806245553, trades=74, reason=recent objective score -0.0107 <= 0; recent PnL -0.4243% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.09805063495486979, pnl=0.027650858780450874, trades=26, reason=recent objective score -0.0981 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.15999648357680532, pnl=0.01400812554136235, trades=10, reason=recent objective score -0.1600 <= 0; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.39295818479913813 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52059 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0107 <= 0; recent PnL -0.4243% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0981 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1600 <= 0; recent worst stress -1000.0000 < -10.0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52059
- **Pre-release bars**: 43994
- **Dev bars**: 35196
- **Holdout bars**: 8798
- **Recent 28d bars**: 8065
- **Recent window start**: 1773338400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T18:50:16.139757+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 10696
