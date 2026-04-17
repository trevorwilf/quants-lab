# PMM Dynamic Optimization Report: nonkyc_ENA-USDT_5m_sweep_v1

Generated: 2026-04-09 19:16:04 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T19:16:04.586606+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 14660 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ENA-USDT
- **interval**: 5m
- **n_candles**: 52059
- **dataset_hash**: 17a0254f151835dcee408ffe44831d6c8b4f2e2a791da2d835784bd73fb2845c
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 955.3677691960808
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.9695147495028138 |
| buy_n_levels | 10 |
| buy_side_weight | 0.20912777933690255 |
| buy_spread_base | 3.538476099714045 |
| buy_spread_ratio | 1.836198292126765 |
| cooldown_time | 3980 |
| executor_refresh_time | 9588 |
| macd_fast | 39 |
| macd_signal | 5 |
| macd_slow | 44 |
| natr_length | 28 |
| sell_n_levels | 7 |
| sell_spread_base | 3.8044302848669833 |
| sell_spread_ratio | 1.5506074608104696 |
| stop_loss | 0.01351746189214886 |
| take_profit | 0.005453306496675398 |
| time_limit | 156702 |
| total_amount_quote | 955.3677691960808 |
| trailing_stop_activation | 0.02473481967033292 |
| trailing_stop_delta | 0.015686216721710857 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 955.3677691960808 |
| Selected | 955.3677691960808 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -3.5577
- **Net PnL (quote)**: -33.9891
- **Sharpe Ratio**: -4.9794
- **Max Drawdown %**: 3.5655
- **Profit Factor**: 0.42607744151391314
- **Trade Count**: 855
- **Total Fees (quote)**: 19.8011
- **Maker Fees**: 13.9533
- **Taker Fees**: 5.8478
- **Fee Drag %**: 2.0726
- **TP Min-Notional Failures**: 8043 :warning:
  > 8043 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0784
- **PnL Component**: -0.0362
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0267
- **Fee Drag Component**: -0.0104
- **Inventory Component**: -0.0050
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0083**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.25 | -12.19 | 0.30 | 64 | -0.0074 | n/a |
| 1 | -0.26 | -12.11 | 0.28 | 63 | -0.0073 | n/a |
| 2 | -0.14 | -9.44 | 0.16 | 68 | -0.0051 | n/a |
| 3 | -0.33 | -16.85 | 0.33 | 77 | -0.0086 | n/a |
| 4 | -0.42 | -3.12 | 0.65 | 84 | -0.0122 | n/a |
| 5 | -0.26 | -8.11 | 0.27 | 82 | -0.0076 | n/a |
| 6 | -0.26 | -13.79 | 0.27 | 101 | -0.0092 | n/a |
| 7 | -0.19 | -8.37 | 0.21 | 94 | -0.0062 | n/a |
| 8 | -0.82 | -19.99 | 0.84 | 106 | -0.0439 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.1261)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -4.59 | -6.38 | 4.60 | -0.1022 |
| fees_2x | -5.63 | -7.76 | 5.63 | -0.1261 |
| latency_plus1 | -3.62 | -5.08 | 3.63 | -0.0794 |
| latency_plus2 | -3.62 | -5.08 | 3.63 | -0.0794 |
| latency_plus3 | -3.74 | -5.25 | 3.75 | -0.0816 |
| low_liquidity | -4.03 | -5.61 | 4.03 | -0.0886 |
| very_low_liquidity | -4.89 | -7.16 | 4.91 | -0.1043 |
| high_slippage | -3.71 | -5.20 | 3.72 | -0.0811 |
| extreme_slippage | -4.02 | -5.65 | 4.02 | -0.0866 |
| combined_adverse | -5.39 | -7.47 | 5.39 | -0.1188 |
| spread_widen_10bps | -5.07 | -6.77 | 5.07 | -0.1071 |
| spread_widen_25bps | -4.88 | -6.36 | 4.89 | -0.1034 |
| thin_book | -2.91 | -7.93 | 2.92 | -0.0603 |
| very_thin_book | -3.29 | -9.26 | 3.34 | -0.1143 |
| entry_spread_stress | -4.90 | -6.47 | 4.91 | -0.1041 |
| combined_market_deterioration | -5.82 | -11.10 | 5.82 | -0.1239 |
| severe_adverse | -5.48 | -18.49 | 5.48 | -0.1141 |

## Holdout Validation

- **Holdout bars**: 8798
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0035)
- **Trend**: ranging (efficiency: 0.0065)
- **Best holdout score**: -0.0128 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1022 | -0.0128 | -0.46 | 0.50 | 213 |
| 1 | -0.0067 | -0.0700 | -1.87 | 1.98 | 485 |
| 2 | -0.0069 | -0.0290 | -1.13 | 1.21 | 460 |
| 3 | -0.0070 | -0.0774 | -1.30 | 1.32 | 440 |
| 4 | -0.0073 | -0.0162 | -0.60 | 0.64 | 218 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52059
- **Expected rows**: 52059
- **Missing rows**: 0
- **Forward-fill count**: 131
- **Forward-fill fraction**: 0.002516375650704009
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0367 <= 0; recent PnL -1.0067% < 0
- **Objective score**: -0.03673648645689166
- **PnL %**: -1.0067482273598027
- **Trade count**: 198

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0093 <= 0; recent PnL -0.2644% < 0
- **Objective score**: -0.009322203823873705
- **PnL %**: -0.26437549974657537
- **Trade count**: 103

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0229 <= 0; recent PnL -0.0140% < 0
- **Objective score**: -0.022930127201594857
- **PnL %**: -0.014041656093065473
- **Trade count**: 45

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.1325019848574056
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0847, -0.1705 |
| sell_spread_base | -0.0903, -0.1314 |
| stop_loss | -0.1448, -0.1458 |
| take_profit | -0.1021, -0.1233 |
| executor_refresh_time | -0.1120, -0.1204 |
| cooldown_time | -0.1429, -0.1263 |
| total_amount_quote | -0.1267, -0.1332 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.23678785949687023
- **Max CV**: 0.7081883076796802
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1222 | 3.092773618545732 | 4.357796746946988 | 3.7703058106171015 |
| buy_spread_ratio | 0.2147 | 1.2690254707968593 | 2.4991909781279618 | 1.8601632428694699 |
| sell_spread_base | 0.7082 | 0.3808312403558853 | 3.493574521838191 | 1.3374883941904856 |
| sell_spread_ratio | 0.1311 | 1.3328315532597235 | 1.960738648596792 | 1.6761576978060553 |
| buy_side_weight | 0.2004 | 0.20653463777056702 | 0.3872440895598744 | 0.3006296633859007 |
| amount_skew | 0.3089 | 1.2739287390103629 | 3.29920022588357 | 2.208347278856157 |
| stop_loss | 0.1938 | 0.01132255149052903 | 0.020598634109657152 | 0.01567995891870346 |
| take_profit | 0.1539 | 0.005159238166564571 | 0.008232189613995463 | 0.0063903071336657135 |
| executor_refresh_time | 0.3126 | 3610.0 | 11277.0 | 8584.9 |
| cooldown_time | 0.1221 | 4069.0 | 6363.0 | 5343.1 |
| total_amount_quote | 0.1368 | 717.260119693824 | 991.5563439289491 | 872.0038058762768 |

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
| recent_objective | > 0 | -0.03673648645689166 | FAIL |
| recent_pnl | >= 0 | -1.0067482273598027 | FAIL |
| recent_trades | >= 5 | 198 | PASS |
| worst_stress | > -10 | -0.12608131198040665 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.012816560625472402 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.12608131198040665 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.03673648645689166, pnl=-1.0067482273598027, trades=198, reason=recent objective score -0.0367 <= 0; recent PnL -1.0067% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.009322203823873705, pnl=-0.26437549974657537, trades=103, reason=recent objective score -0.0093 <= 0; recent PnL -0.2644% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.022930127201594857, pnl=-0.014041656093065473, trades=45, reason=recent objective score -0.0229 <= 0; recent PnL -0.0140% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.23678785949687023 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52059 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0367 <= 0; recent PnL -1.0067% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0093 <= 0; recent PnL -0.2644% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0229 <= 0; recent PnL -0.0140% < 0 |
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
- **run_timestamp**: 2026-04-09T19:16:04.586606+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 14660
