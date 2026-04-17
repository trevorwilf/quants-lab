# PMM Dynamic Optimization Report: nonkyc_ARB-USDT_5m_sweep_v1

Generated: 2026-04-09 14:59:31 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T14:59:31.761690+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 3217 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARB-USDT
- **interval**: 5m
- **n_candles**: 52002
- **dataset_hash**: 065f39c1b21a75b73f689f5a282e43c46ff7bea13fc937a1ce4f44817640527e
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 956.7395417595164
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.6658947536463518 |
| buy_n_levels | 10 |
| buy_side_weight | 0.48512760757873546 |
| buy_spread_base | 3.7134767772951283 |
| buy_spread_ratio | 2.0710846808275125 |
| cooldown_time | 3791 |
| executor_refresh_time | 9598 |
| macd_fast | 12 |
| macd_signal | 21 |
| macd_slow | 31 |
| natr_length | 39 |
| sell_n_levels | 3 |
| sell_spread_base | 4.77605099279035 |
| sell_spread_ratio | 2.9834912483340537 |
| stop_loss | 0.019463219595583125 |
| take_profit | 0.005228952580868265 |
| time_limit | 30491 |
| total_amount_quote | 956.7395417595164 |
| trailing_stop_activation | 0.034503292191384136 |
| trailing_stop_delta | 0.0023266668353677535 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 956.7395417595164 |
| Selected | 956.7395417595164 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -4.7150
- **Net PnL (quote)**: -45.1103
- **Sharpe Ratio**: -3.6561
- **Max Drawdown %**: 4.8285
- **Profit Factor**: 0.3108308421705867
- **Trade Count**: 615
- **Total Fees (quote)**: 19.3959
- **Maker Fees**: 13.7823
- **Taker Fees**: 5.6136
- **Fee Drag %**: 2.0273
- **TP Min-Notional Failures**: 2805 :warning:
  > 2805 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0983
- **PnL Component**: -0.0483
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0362
- **Fee Drag Component**: -0.0101
- **Inventory Component**: -0.0036
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0228**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.33 | -9.05 | 0.37 | 55 | -0.0087 | n/a |
| 1 | -0.79 | -15.47 | 0.80 | 56 | -0.0230 | n/a |
| 2 | -0.10 | -6.90 | 0.11 | 56 | -0.0044 | n/a |
| 3 | -0.13 | -3.85 | 0.19 | 75 | -0.0058 | n/a |
| 4 | -1.43 | -3.68 | 2.05 | 79 | -0.0384 | n/a |
| 5 | -0.74 | -14.28 | 0.86 | 66 | -0.0172 | n/a |
| 6 | -0.57 | -10.44 | 0.59 | 79 | -0.0257 | n/a |
| 7 | 0.04 | 1.63 | 0.10 | 52 | -0.0028 | n/a |
| 8 | -1.38 | -17.29 | 1.38 | 80 | -0.0915 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1606)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -5.73 | -4.43 | 5.84 | -0.1217 |
| fees_2x | -6.74 | -5.20 | 6.84 | -0.1451 |
| latency_plus1 | -4.72 | -3.66 | 4.83 | -0.0984 |
| latency_plus2 | -4.99 | -3.86 | 5.03 | -0.1031 |
| latency_plus3 | -4.71 | -3.46 | 4.77 | -0.0993 |
| low_liquidity | -5.49 | -7.43 | 5.52 | -0.1127 |
| very_low_liquidity | -6.36 | -8.61 | 6.41 | -0.1334 |
| high_slippage | -4.86 | -3.78 | 4.97 | -0.1010 |
| extreme_slippage | -5.15 | -4.02 | 5.27 | -0.1063 |
| combined_adverse | -6.64 | -8.86 | 6.68 | -0.1387 |
| spread_widen_10bps | -6.22 | -4.48 | 6.27 | -0.1290 |
| spread_widen_25bps | -7.31 | -4.67 | 7.41 | -0.1529 |
| thin_book | -5.28 | -3.79 | 5.35 | -0.1073 |
| very_thin_book | -4.59 | -3.94 | 4.61 | -0.0914 |
| entry_spread_stress | -5.63 | -4.00 | 5.75 | -0.1154 |
| combined_market_deterioration | -6.62 | -6.51 | 6.73 | -0.1402 |
| severe_adverse | -7.47 | -10.05 | 7.50 | -0.1606 |

## Holdout Validation

- **Holdout bars**: 8787
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0035)
- **Trend**: ranging (efficiency: 0.0076)
- **Best holdout score**: -0.0109 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1294 | -0.0144 | -0.58 | 0.64 | 139 |
| 1 | -0.0064 | -0.0692 | -2.38 | 2.60 | 454 |
| 2 | -0.0064 | -0.0180 | -0.69 | 0.75 | 138 |
| 3 | -0.0065 | -0.1423 | -2.09 | 2.19 | 531 |
| 4 | -0.0066 | -0.0109 | -0.39 | 0.46 | 177 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52002
- **Expected rows**: 52002
- **Missing rows**: 0
- **Forward-fill count**: 160
- **Forward-fill fraction**: 0.003076804738279297
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0865 <= 0; recent PnL -1.5040% < 0
- **Objective score**: -0.08650368540517255
- **PnL %**: -1.5040215525224356
- **Trade count**: 117

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1985 <= 0; recent PnL -0.3944% < 0
- **Objective score**: -0.19854111966651336
- **PnL %**: -0.3944219273017877
- **Trade count**: 43

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3162 <= 0; recent PnL -0.0958% < 0
- **Objective score**: -0.31621778945764434
- **PnL %**: -0.09579318642078286
- **Trade count**: 18

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.13673312204130228
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1839, -0.2051 |
| sell_spread_base | -0.1320, -0.1471 |
| stop_loss | -0.1632, -0.1601 |
| take_profit | -0.1732, -0.1644 |
| executor_refresh_time | -0.1430, -0.1591 |
| cooldown_time | -0.1314, -0.1518 |
| total_amount_quote | -0.1889, -0.1267 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.22544873563032894
- **Max CV**: 0.801979189036383
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1512 | 2.069173449510432 | 3.9854317035775093 | 3.0645586780601954 |
| buy_spread_ratio | 0.1033 | 1.8751920360496006 | 2.8462443511144424 | 2.3311019536752693 |
| sell_spread_base | 0.8020 | 0.5645743369780407 | 4.870430130069644 | 1.9963589630781187 |
| sell_spread_ratio | 0.1549 | 1.814893789588842 | 2.925358022415208 | 2.453266241481528 |
| buy_side_weight | 0.2065 | 0.23681473733950748 | 0.4239177855304941 | 0.31287001136257586 |
| amount_skew | 0.0626 | 2.933183088067263 | 3.4936042644972454 | 3.1539760647958612 |
| stop_loss | 0.2086 | 0.01083209076049925 | 0.01857567198722133 | 0.014639919786027567 |
| take_profit | 0.1489 | 0.005156472904183521 | 0.00763637261315712 | 0.005821447974938441 |
| executor_refresh_time | 0.1442 | 8760.0 | 13799.0 | 11789.3 |
| cooldown_time | 0.4096 | 1088.0 | 6606.0 | 4350.9 |
| total_amount_quote | 0.0881 | 732.703975168211 | 989.8043159449085 | 913.7619488096727 |

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
| recent_objective | > 0 | -0.08650368540517255 | FAIL |
| recent_pnl | >= 0 | -1.5040215525224356 | FAIL |
| recent_trades | >= 5 | 117 | PASS |
| worst_stress | > -10 | -0.16055174519138388 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.014367572549874327 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.16055174519138388 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.08650368540517255, pnl=-1.5040215525224356, trades=117, reason=recent objective score -0.0865 <= 0; recent PnL -1.5040% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.19854111966651336, pnl=-0.3944219273017877, trades=43, reason=recent objective score -0.1985 <= 0; recent PnL -0.3944% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.31621778945764434, pnl=-0.09579318642078286, trades=18, reason=recent objective score -0.3162 <= 0; recent PnL -0.0958% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.22544873563032894 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52002 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0865 <= 0; recent PnL -1.5040% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1985 <= 0; recent PnL -0.3944% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.3162 <= 0; recent PnL -0.0958% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52002
- **Pre-release bars**: 43937
- **Dev bars**: 35150
- **Holdout bars**: 8787
- **Recent 28d bars**: 8065
- **Recent window start**: 1773321300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T14:59:31.761690+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 3217
