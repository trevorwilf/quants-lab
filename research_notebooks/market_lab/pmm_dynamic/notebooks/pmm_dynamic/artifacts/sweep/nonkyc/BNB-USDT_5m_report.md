# PMM Dynamic Optimization Report: nonkyc_BNB-USDT_5m_sweep_v1

Generated: 2026-04-09 17:35:12 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T17:35:12.002205+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 14371 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BNB-USDT
- **interval**: 5m
- **n_candles**: 52004
- **dataset_hash**: ac43c72786e44724afe1c532d26d1ed32eee1dab1f16f56fb6ca54e6eccf7de8
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 985.8426553164584
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.7852713289844244 |
| buy_n_levels | 5 |
| buy_side_weight | 0.2124680101263549 |
| buy_spread_base | 2.0118222752356334 |
| buy_spread_ratio | 2.8324280474935835 |
| cooldown_time | 3466 |
| executor_refresh_time | 14136 |
| macd_fast | 47 |
| macd_signal | 10 |
| macd_slow | 93 |
| natr_length | 32 |
| sell_n_levels | 6 |
| sell_spread_base | 1.9921330317650725 |
| sell_spread_ratio | 2.497242960501184 |
| stop_loss | 0.0451130480849211 |
| take_profit | 0.005240900969534725 |
| time_limit | 129424 |
| total_amount_quote | 985.8426553164584 |
| trailing_stop_activation | 0.07358213869443203 |
| trailing_stop_delta | 0.0010360313017450315 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 985.8426553164584 |
| Selected | 985.8426553164584 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -11.0512
- **Net PnL (quote)**: -108.9474
- **Sharpe Ratio**: -5.1086
- **Max Drawdown %**: 12.5568
- **Profit Factor**: 0.5326593735527478
- **Trade Count**: 1226
- **Total Fees (quote)**: 51.4995
- **Maker Fees**: 43.8186
- **Taker Fees**: 7.6809
- **Fee Drag %**: 5.2239
- **TP Min-Notional Failures**: 5153 :warning:
  > 5153 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.2969
- **PnL Component**: -0.1171
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0942
- **Fee Drag Component**: -0.0261
- **Inventory Component**: -0.0590
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0608**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.56 | -12.51 | 0.59 | 84 | -0.0363 | n/a |
| 1 | -0.32 | -9.12 | 0.37 | 82 | -0.0705 | n/a |
| 2 | -0.19 | -10.61 | 0.19 | 69 | -0.1234 | n/a |
| 3 | -0.17 | -9.38 | 0.19 | 69 | -0.1243 | n/a |
| 4 | -0.50 | -7.27 | 0.52 | 90 | -0.0774 | n/a |
| 5 | -0.24 | -7.38 | 0.26 | 90 | -0.0118 | n/a |
| 6 | -0.56 | -10.39 | 0.62 | 92 | -0.0443 | n/a |
| 7 | -0.12 | -7.43 | 0.13 | 89 | -0.0094 | n/a |
| 8 | -0.21 | -6.46 | 0.26 | 70 | -0.0113 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.4453)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -13.66 | -6.27 | 15.05 | -0.3597 |
| fees_2x | -16.28 | -7.40 | 17.54 | -0.4234 |
| latency_plus1 | -11.11 | -5.13 | 12.62 | -0.2980 |
| latency_plus2 | -10.89 | -5.32 | 12.30 | -0.2883 |
| latency_plus3 | -10.86 | -5.59 | 12.24 | -0.2844 |
| low_liquidity | -11.89 | -5.17 | 13.53 | -0.3159 |
| very_low_liquidity | -12.07 | -5.28 | 13.72 | -0.3177 |
| high_slippage | -11.25 | -5.19 | 12.75 | -0.3006 |
| extreme_slippage | -11.64 | -5.36 | 13.13 | -0.3081 |
| combined_adverse | -14.74 | -6.35 | 16.26 | -0.3837 |
| spread_widen_10bps | -13.10 | -5.30 | 14.74 | -0.3453 |
| spread_widen_25bps | -15.66 | -6.16 | 17.36 | -0.3958 |
| thin_book | -13.56 | -6.36 | 14.81 | -0.3378 |
| very_thin_book | -13.17 | -7.51 | 13.94 | -0.3083 |
| entry_spread_stress | -13.09 | -5.57 | 14.65 | -0.3406 |
| combined_market_deterioration | -15.24 | -6.32 | 16.73 | -0.3961 |
| severe_adverse | -18.48 | -9.53 | 19.47 | -0.4453 |

## Holdout Validation

- **Holdout bars**: 8796
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0019)
- **Trend**: ranging (efficiency: 0.0027)
- **Best holdout score**: -0.0523 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.3711 | -0.0523 | -0.80 | 0.81 | 188 |
| 1 | -0.0278 | -0.2071 | -4.11 | 5.35 | 340 |
| 2 | -0.0293 | -0.2867 | -4.31 | 6.53 | 327 |
| 3 | -0.0341 | -0.1485 | -1.71 | 3.17 | 363 |
| 4 | -0.0364 | -0.0848 | -1.88 | 2.21 | 347 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52004
- **Expected rows**: 52048
- **Missing rows**: 44
- **Forward-fill count**: 252
- **Forward-fill fraction**: 0.0048457810937620185
- **Longest gap (seconds)**: 13200

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0137 <= 0; recent PnL -0.3516% < 0
- **Objective score**: -0.013741707132368518
- **PnL %**: -0.35161295547319404
- **Trade count**: 124

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0088 <= 0; recent PnL -0.1180% < 0
- **Objective score**: -0.008814752769264658
- **PnL %**: -0.11799879805632486
- **Trade count**: 53

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1745 <= 0; recent PnL -0.0314% < 0
- **Objective score**: -0.17448946269251184
- **PnL %**: -0.03140679833643768
- **Trade count**: 21

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.36262134127069906
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.6293, -0.3785 |
| sell_spread_base | -0.3664, -0.3601 |
| stop_loss | -0.3909, -0.3621 |
| take_profit | -0.3855, -0.3938 |
| executor_refresh_time | -0.3262, -0.3402 |
| cooldown_time | -0.3917, -0.3969 |
| total_amount_quote | -0.3626, -0.3629 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2790293735566161
- **Max CV**: 0.7157259852190857
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3290 | 1.5024758074927587 | 4.279393449523238 | 2.8605691905352013 |
| buy_spread_ratio | 0.1528 | 1.7383132357108413 | 2.832526482310446 | 2.409186840371611 |
| sell_spread_base | 0.5997 | 0.2563972395246032 | 2.9430319153671793 | 1.4321790375817696 |
| sell_spread_ratio | 0.1747 | 1.3169209085478684 | 2.4512332406603496 | 1.8417380481436687 |
| buy_side_weight | 0.4419 | 0.20068355574646313 | 0.6950430214380581 | 0.349375554037749 |
| amount_skew | 0.1648 | 2.4871860684276133 | 3.994921355486923 | 3.2862262432395086 |
| stop_loss | 0.7157 | 0.015475829437315807 | 0.16598562416431878 | 0.07345833016203393 |
| take_profit | 0.0408 | 0.005017481015308264 | 0.005634742636927662 | 0.005240320180201563 |
| executor_refresh_time | 0.0793 | 11320.0 | 14363.0 | 13166.2 |
| cooldown_time | 0.1107 | 4939.0 | 7161.0 | 6199.0 |
| total_amount_quote | 0.2599 | 431.58222233063645 | 983.0281166279917 | 804.9285588652207 |

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
| recent_objective | > 0 | -0.013741707132368518 | FAIL |
| recent_pnl | >= 0 | -0.35161295547319404 | FAIL |
| recent_trades | >= 5 | 124 | PASS |
| worst_stress | > -10 | -0.44531983541533793 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.052270057339299195 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.44531983541533793 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.013741707132368518, pnl=-0.35161295547319404, trades=124, reason=recent objective score -0.0137 <= 0; recent PnL -0.3516% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.008814752769264658, pnl=-0.11799879805632486, trades=53, reason=recent objective score -0.0088 <= 0; recent PnL -0.1180% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.17448946269251184, pnl=-0.03140679833643768, trades=21, reason=recent objective score -0.1745 <= 0; recent PnL -0.0314% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2790293735566161 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52004 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0137 <= 0; recent PnL -0.3516% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0088 <= 0; recent PnL -0.1180% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1745 <= 0; recent PnL -0.0314% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52004
- **Pre-release bars**: 43983
- **Dev bars**: 35187
- **Holdout bars**: 8796
- **Recent 28d bars**: 8021
- **Recent window start**: 1773335100

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T17:35:12.002205+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 14371
