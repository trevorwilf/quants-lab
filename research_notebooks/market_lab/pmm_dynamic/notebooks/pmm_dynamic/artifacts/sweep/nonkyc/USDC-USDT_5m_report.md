# PMM Dynamic Optimization Report: nonkyc_USDC-USDT_5m_sweep_v1

Generated: 2026-04-10 02:01:07 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-10T02:01:07.092949+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 11241 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: USDC-USDT
- **interval**: 5m
- **n_candles**: 52112
- **dataset_hash**: 3bb8fd0753add6efd0d3304a94d26b653db5f48af28bc4836ee664789a0f2a58
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 984.0880990718651
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.89817031553526 |
| buy_n_levels | 10 |
| buy_side_weight | 0.6930350527208743 |
| buy_spread_base | 1.8722514021974512 |
| buy_spread_ratio | 1.7823380869545207 |
| cooldown_time | 4483 |
| executor_refresh_time | 1590 |
| macd_fast | 8 |
| macd_signal | 8 |
| macd_slow | 39 |
| natr_length | 27 |
| sell_n_levels | 7 |
| sell_spread_base | 5.9500777844067 |
| sell_spread_ratio | 2.6254059293252188 |
| stop_loss | 0.02128476539205161 |
| take_profit | 0.014132470878551717 |
| time_limit | 38041 |
| total_amount_quote | 984.0880990718651 |
| trailing_stop_activation | 0.0036756142073950337 |
| trailing_stop_delta | 0.0010857231844299004 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 984.0880990718651 |
| Selected | 984.0880990718651 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.6658
- **Net PnL (quote)**: -6.5521
- **Sharpe Ratio**: -2.0849
- **Max Drawdown %**: 0.6871
- **Profit Factor**: 0.2673926912265158
- **Trade Count**: 772
- **Total Fees (quote)**: 30.8561
- **Maker Fees**: 10.9371
- **Taker Fees**: 19.9190
- **Fee Drag %**: 3.1355
- **TP Min-Notional Failures**: 18 :warning:
  > 18 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0659
- **PnL Component**: -0.0067
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0052
- **Fee Drag Component**: -0.0157
- **Inventory Component**: -0.0142
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0648**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.00 | -0.28 | 0.01 | 57 | -0.0023 | n/a |
| 1 | -0.01 | -2.34 | 0.01 | 62 | -0.0024 | n/a |
| 2 | -0.03 | -10.58 | 0.04 | 66 | -0.0268 | n/a |
| 3 | -0.11 | -5.12 | 0.11 | 70 | -0.0460 | n/a |
| 4 | -0.05 | -7.43 | 0.05 | 75 | -0.1045 | n/a |
| 5 | -0.02 | -6.85 | 0.02 | 62 | -0.0845 | n/a |
| 6 | -0.30 | -8.36 | 0.30 | 76 | -0.0369 | n/a |
| 7 | -0.21 | -9.15 | 0.21 | 97 | -0.0836 | n/a |
| 8 | -0.14 | -13.90 | 0.14 | 129 | -0.0752 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.2556)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.23 | -6.41 | 2.24 | -0.2109 |
| fees_2x | -3.80 | -9.79 | 3.81 | -0.2556 |
| latency_plus1 | -0.67 | -2.10 | 0.69 | -0.0651 |
| latency_plus2 | -0.67 | -2.12 | 0.69 | -0.0572 |
| latency_plus3 | -0.62 | -2.03 | 0.64 | -0.0641 |
| low_liquidity | -0.64 | -2.03 | 0.66 | -0.0538 |
| very_low_liquidity | -0.66 | -2.37 | 0.68 | -0.0502 |
| high_slippage | -1.17 | -3.55 | 1.19 | -0.1415 |
| extreme_slippage | -2.18 | -6.11 | 2.19 | -0.2049 |
| combined_adverse | -2.50 | -7.00 | 2.51 | -0.2255 |
| spread_widen_10bps | -1.34 | -3.94 | 1.35 | -0.1237 |
| spread_widen_25bps | -2.54 | -5.60 | 2.56 | -0.2445 |
| thin_book | -0.67 | -2.32 | 0.70 | -0.0661 |
| very_thin_book | -0.25 | -2.32 | 0.28 | -0.0352 |
| entry_spread_stress | -1.72 | -4.49 | 1.73 | -0.1447 |
| combined_market_deterioration | -2.81 | -8.96 | 2.81 | -0.2001 |
| severe_adverse | -3.18 | -7.48 | 3.19 | -0.2164 |

## Holdout Validation

- **Holdout bars**: 8809
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0014)
- **Trend**: ranging (efficiency: 0.0005)
- **Best holdout score**: -0.0381 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1607 | -0.0610 | -0.52 | 0.52 | 183 |
| 1 | -0.0044 | -0.0381 | -0.39 | 0.49 | 168 |
| 2 | -0.0057 | -0.0522 | -0.70 | 0.75 | 179 |
| 3 | -0.0059 | -0.1355 | -0.69 | 0.82 | 309 |
| 4 | -0.0059 | -0.1686 | -1.80 | 1.84 | 457 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52112
- **Expected rows**: 52112
- **Missing rows**: 0
- **Forward-fill count**: 522
- **Forward-fill fraction**: 0.010016886705557261
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0750 <= 0; recent PnL -0.2169% < 0
- **Objective score**: -0.07495620611932162
- **PnL %**: -0.2168651004014534
- **Trade count**: 205

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0588 <= 0; recent PnL -0.0744% < 0
- **Objective score**: -0.05884910329956645
- **PnL %**: -0.07444061269031896
- **Trade count**: 78

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0880 <= 0; recent PnL -0.0598% < 0
- **Objective score**: -0.08796364251355962
- **PnL %**: -0.05981588405305009
- **Trade count**: 44

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.06653605204956552
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0683, -0.0791 |
| sell_spread_base | -0.0658, -0.0677 |
| stop_loss | -0.0665, -0.0665 |
| take_profit | -0.0665, -0.0665 |
| executor_refresh_time | -0.0665, -0.0668 |
| cooldown_time | -0.0633, -0.0650 |
| total_amount_quote | -0.0664, -0.0668 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3980728283163144
- **Max CV**: 1.03596526107267
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0850 | 1.5422332611349514 | 2.0320825780660092 | 1.6941282996541862 |
| buy_spread_ratio | 0.1294 | 1.326049163356043 | 1.951249676739615 | 1.5801910635842815 |
| sell_spread_base | 1.0360 | 0.31662422596823736 | 5.9915451481851285 | 2.0883642140689487 |
| sell_spread_ratio | 0.2866 | 1.3203548618662886 | 2.9301087387823035 | 2.3169096957940343 |
| buy_side_weight | 0.1788 | 0.4121053214981069 | 0.6458557183412923 | 0.5433590444757338 |
| amount_skew | 0.1275 | 2.7522065512373537 | 3.998748070834987 | 3.387790596878324 |
| stop_loss | 0.8801 | 0.011785623391296053 | 0.13977970699523953 | 0.048254497292666274 |
| take_profit | 0.6344 | 0.006512403368908223 | 0.03844097755037341 | 0.01655631326957607 |
| executor_refresh_time | 0.6716 | 970.0 | 10186.0 | 4510.9 |
| cooldown_time | 0.2615 | 3430.0 | 7109.0 | 5291.2 |
| total_amount_quote | 0.0879 | 749.4104618298189 | 999.2983670055057 | 902.1844367179012 |

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
| recent_objective | > 0 | -0.07495620611932162 | FAIL |
| recent_pnl | >= 0 | -0.2168651004014534 | FAIL |
| recent_trades | >= 5 | 205 | PASS |
| worst_stress | > -10 | -0.2555697846793986 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.06097509940615081 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.2555697846793986 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.07495620611932162, pnl=-0.2168651004014534, trades=205, reason=recent objective score -0.0750 <= 0; recent PnL -0.2169% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.05884910329956645, pnl=-0.07444061269031896, trades=78, reason=recent objective score -0.0588 <= 0; recent PnL -0.0744% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.08796364251355962, pnl=-0.05981588405305009, trades=44, reason=recent objective score -0.0880 <= 0; recent PnL -0.0598% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3980728283163144 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52112 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0750 <= 0; recent PnL -0.2169% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0588 <= 0; recent PnL -0.0744% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0880 <= 0; recent PnL -0.0598% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52112
- **Pre-release bars**: 44047
- **Dev bars**: 35238
- **Holdout bars**: 8809
- **Recent 28d bars**: 8065
- **Recent window start**: 1773354300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-10T02:01:07.092949+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 11241
