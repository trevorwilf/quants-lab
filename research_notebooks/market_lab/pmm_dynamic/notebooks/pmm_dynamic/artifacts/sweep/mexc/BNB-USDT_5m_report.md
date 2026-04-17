# PMM Dynamic Optimization Report: mexc_BNB-USDT_5m_sweep_v1

Generated: 2026-04-09 02:11:21 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T02:11:21.021949+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 9309 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BNB-USDT
- **interval**: 5m
- **n_candles**: 51845
- **dataset_hash**: df0d6826fef6f7298480bde0ea5c23158bcd60b233ec9204f4189d1d4e3e5453
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 994.4389685648351
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.052745230525991 |
| buy_n_levels | 6 |
| buy_side_weight | 0.29437011988910433 |
| buy_spread_base | 2.9725014532071783 |
| buy_spread_ratio | 2.4333752604742163 |
| cooldown_time | 4941 |
| executor_refresh_time | 2558 |
| macd_fast | 42 |
| macd_signal | 11 |
| macd_slow | 57 |
| natr_length | 40 |
| sell_n_levels | 3 |
| sell_spread_base | 5.074086825301406 |
| sell_spread_ratio | 1.7765744424863334 |
| stop_loss | 0.015539072382194678 |
| take_profit | 0.006175180601887436 |
| time_limit | 111059 |
| total_amount_quote | 994.4389685648351 |
| trailing_stop_activation | 0.08732798675331697 |
| trailing_stop_delta | 0.004063796225995044 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 994.4389685648351 |
| Selected | 994.4389685648351 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.7418
- **Net PnL (quote)**: -27.2654
- **Sharpe Ratio**: -4.2346
- **Max Drawdown %**: 3.1515
- **Profit Factor**: 0.7364987248786152
- **Trade Count**: 746
- **Total Fees (quote)**: 3.7165
- **Maker Fees**: 3.1153
- **Taker Fees**: 0.6012
- **Fee Drag %**: 0.3737
- **TP Min-Notional Failures**: 4041 :warning:
  > 4041 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0719
- **PnL Component**: -0.0278
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0236
- **Fee Drag Component**: -0.0019
- **Inventory Component**: -0.0184
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0261**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.20 | -3.95 | 0.42 | 63 | -0.0071 | n/a |
| 1 | -0.16 | -6.42 | 0.21 | 67 | -0.0052 | n/a |
| 2 | -0.04 | -2.25 | 0.11 | 63 | -0.0068 | n/a |
| 3 | -0.05 | -4.18 | 0.08 | 60 | -0.0198 | n/a |
| 4 | -0.28 | -6.85 | 0.30 | 68 | -0.0369 | n/a |
| 5 | -0.24 | -8.12 | 0.26 | 78 | -0.0324 | n/a |
| 6 | -0.05 | -1.09 | 0.23 | 77 | -0.0078 | n/a |
| 7 | -0.10 | -4.29 | 0.12 | 67 | -0.0232 | n/a |
| 8 | -0.15 | -3.56 | 0.35 | 86 | -0.0239 | n/a |

## Stress Test Results

Worst Scenario: **spread_widen_25bps** (score: -0.1033)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.93 | -4.52 | 3.33 | -0.0761 |
| fees_2x | -3.12 | -4.80 | 3.51 | -0.0804 |
| latency_plus1 | -2.79 | -4.33 | 3.20 | -0.0728 |
| latency_plus2 | -2.18 | -4.53 | 2.42 | -0.0568 |
| latency_plus3 | -2.52 | -4.76 | 2.81 | -0.0649 |
| low_liquidity | -2.74 | -4.23 | 3.15 | -0.0719 |
| very_low_liquidity | -2.74 | -4.23 | 3.15 | -0.0719 |
| high_slippage | -2.89 | -4.45 | 3.30 | -0.0746 |
| extreme_slippage | -3.20 | -4.89 | 3.60 | -0.0800 |
| combined_adverse | -3.13 | -4.83 | 3.53 | -0.0797 |
| spread_widen_10bps | -3.07 | -5.19 | 3.42 | -0.0767 |
| spread_widen_25bps | -4.32 | -6.02 | 4.72 | -0.1033 |
| thin_book | -2.22 | -4.95 | 2.46 | -0.0568 |
| very_thin_book | -1.60 | -6.09 | 1.69 | -0.0367 |
| entry_spread_stress | -3.57 | -4.89 | 4.02 | -0.0910 |
| combined_market_deterioration | -3.61 | -6.27 | 3.92 | -0.0860 |
| severe_adverse | -3.97 | -7.92 | 4.20 | -0.0887 |

## Holdout Validation

- **Holdout bars**: 8759
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0021)
- **Trend**: ranging (efficiency: 0.0039)
- **Best holdout score**: -0.0178 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0876 | -0.0190 | -0.11 | 0.27 | 157 |
| 1 | -0.0042 | -0.0338 | -0.42 | 1.22 | 320 |
| 2 | -0.0048 | -0.0317 | 0.40 | 0.84 | 460 |
| 3 | -0.0054 | -0.0364 | -0.62 | 1.18 | 864 |
| 4 | -0.0054 | -0.0178 | -0.32 | 0.48 | 172 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51845
- **Expected rows**: 51860
- **Missing rows**: 15
- **Forward-fill count**: 126
- **Forward-fill fraction**: 0.0024303211495804804
- **Longest gap (seconds)**: 4800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0412 <= 0; recent PnL -0.3845% < 0
- **Objective score**: -0.04124772670234465
- **PnL %**: -0.38452742482247565
- **Trade count**: 162

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0637 <= 0; recent PnL -0.2700% < 0
- **Objective score**: -0.06370673230016255
- **PnL %**: -0.26995183923773003
- **Trade count**: 83

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1331 <= 0; recent PnL -0.1454% < 0
- **Objective score**: -0.13311570379565
- **PnL %**: -0.1453588151461809
- **Trade count**: 38

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.10137640901442882
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0860, -0.1053 |
| sell_spread_base | -0.1063, -0.1160 |
| stop_loss | -0.0928, -0.0823 |
| take_profit | -0.1054, -0.1002 |
| executor_refresh_time | -0.0907, -0.1169 |
| cooldown_time | -0.1016, -0.1106 |
| total_amount_quote | -0.1032, -0.1006 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.45289255917779125
- **Max CV**: 2.075195972790936
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1504 | 2.279615668883229 | 3.571664333553302 | 3.1152327491764757 |
| buy_spread_ratio | 0.1001 | 1.8533543266616275 | 2.7463289430205897 | 2.3925333884078555 |
| sell_spread_base | 1.0701 | 0.29827876797110364 | 5.948670514755272 | 1.9460598477365985 |
| sell_spread_ratio | 0.2081 | 1.2459715073944815 | 2.455964882382045 | 1.6669912564536447 |
| buy_side_weight | 0.2079 | 0.21121668166991822 | 0.43810253471337746 | 0.310113281384442 |
| amount_skew | 0.1365 | 2.2225234000292065 | 3.5022196945849835 | 2.9975836993812375 |
| stop_loss | 0.3166 | 0.01170939951330895 | 0.02963934980967665 | 0.016627772935752433 |
| take_profit | 2.0752 | 0.005051326623422517 | 0.1370023270533965 | 0.019856451473501645 |
| executor_refresh_time | 0.4099 | 2558.0 | 9079.0 | 6019.9 |
| cooldown_time | 0.1909 | 2337.0 | 5157.0 | 4348.8 |
| total_amount_quote | 0.1162 | 684.044007105026 | 994.4389685648351 | 902.5694713331411 |

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
| recent_objective | > 0 | -0.04124772670234465 | FAIL |
| recent_pnl | >= 0 | -0.38452742482247565 | FAIL |
| recent_trades | >= 5 | 162 | PASS |
| worst_stress | > -10 | -0.10325380482935417 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.01896848345893038 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=spread_widen_25bps score=-0.10325380482935417 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.04124772670234465, pnl=-0.38452742482247565, trades=162, reason=recent objective score -0.0412 <= 0; recent PnL -0.3845% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.06370673230016255, pnl=-0.26995183923773003, trades=83, reason=recent objective score -0.0637 <= 0; recent PnL -0.2700% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.13311570379565, pnl=-0.1453588151461809, trades=38, reason=recent objective score -0.1331 <= 0; recent PnL -0.1454% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.45289255917779125 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51845 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0412 <= 0; recent PnL -0.3845% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0637 <= 0; recent PnL -0.2700% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1331 <= 0; recent PnL -0.1454% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51845
- **Pre-release bars**: 43795
- **Dev bars**: 35036
- **Holdout bars**: 8759
- **Recent 28d bars**: 8050
- **Recent window start**: 1773278400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T02:11:21.021949+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 9309
