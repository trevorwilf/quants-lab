# PMM Dynamic Optimization Report: nonkyc_ZSD-USDT_5m_sweep_v1

Generated: 2026-04-10 04:59:21 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-10T04:59:21.145712+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 14458 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ZSD-USDT
- **interval**: 5m
- **n_candles**: 52165
- **dataset_hash**: e4301e27c29bac1f6ad08a2ef55045d286a5d1f3b7755c7e0b57191d1a4664c9
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 102.01572187714552
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.499467566140477 |
| buy_n_levels | 7 |
| buy_side_weight | 0.649434666359318 |
| buy_spread_base | 2.36646677566646 |
| buy_spread_ratio | 2.497639031439048 |
| cooldown_time | 1948 |
| executor_refresh_time | 2774 |
| macd_fast | 25 |
| macd_signal | 17 |
| macd_slow | 27 |
| natr_length | 45 |
| sell_n_levels | 5 |
| sell_spread_base | 2.2769980723874146 |
| sell_spread_ratio | 1.5948623607266061 |
| stop_loss | 0.1543844260776129 |
| take_profit | 0.11311273856321795 |
| time_limit | 115088 |
| total_amount_quote | 102.01572187714552 |
| trailing_stop_activation | 0.007546796207944733 |
| trailing_stop_delta | 0.0023846875778644858 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 102.01572187714552 |
| Selected | 102.01572187714552 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 13.7133
- **Net PnL (quote)**: 13.9897
- **Sharpe Ratio**: 5.5559
- **Max Drawdown %**: 0.5332
- **Profit Factor**: 24.35912434917167
- **Trade Count**: 728
- **Total Fees (quote)**: 5.2387
- **Maker Fees**: 1.8634
- **Taker Fees**: 3.3754
- **Fee Drag %**: 5.1352

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0751
- **PnL Component**: 0.1285
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0040
- **Fee Drag Component**: -0.0257
- **Inventory Component**: -0.0233
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0031**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.54 | 3.29 | 0.38 | 72 | 0.0001 | n/a |
| 1 | 0.53 | 7.49 | 0.12 | 55 | 0.0026 | n/a |
| 2 | 0.34 | 7.70 | 0.12 | 22 | -0.1107 | n/a |
| 3 | 0.61 | 4.40 | 0.51 | 79 | -0.0004 | n/a |
| 4 | 0.98 | 9.86 | 0.11 | 72 | 0.0064 | n/a |
| 5 | 0.33 | 3.58 | 0.24 | 70 | -0.0011 | n/a |
| 6 | -0.13 | -1.15 | 0.33 | 62 | -0.0064 | n/a |
| 7 | 0.10 | 0.43 | 0.50 | 62 | -0.0051 | n/a |
| 8 | -0.12 | -2.45 | 0.21 | 36 | -0.1930 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0271)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 11.15 | 4.54 | 0.56 | 0.0389 |
| fees_2x | 8.58 | 3.51 | 0.58 | 0.0023 |
| latency_plus1 | 12.94 | 5.56 | 0.53 | 0.0698 |
| latency_plus2 | 13.05 | 5.13 | 0.64 | 0.0692 |
| latency_plus3 | 12.45 | 4.60 | 0.81 | 0.0609 |
| low_liquidity | 9.98 | 5.11 | 1.01 | 0.0494 |
| very_low_liquidity | 8.17 | 2.70 | 0.89 | 0.0260 |
| high_slippage | 12.89 | 5.23 | 0.54 | 0.0676 |
| extreme_slippage | 11.23 | 4.58 | 0.55 | 0.0526 |
| combined_adverse | 7.42 | 3.84 | 1.03 | 0.0188 |
| spread_widen_10bps | 13.06 | 5.18 | 0.55 | 0.0700 |
| spread_widen_25bps | 12.80 | 4.81 | 0.95 | 0.0648 |
| thin_book | 6.13 | 3.45 | 1.06 | 0.0204 |
| very_thin_book | 1.33 | 2.37 | 0.27 | 0.0066 |
| entry_spread_stress | 13.13 | 5.53 | 0.55 | 0.0715 |
| combined_market_deterioration | 6.80 | 3.02 | 0.75 | 0.0104 |
| severe_adverse | 1.14 | 0.86 | 0.72 | -0.0271 |

## Holdout Validation

- **Holdout bars**: 8820
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0060)
- **Trend**: ranging (efficiency: 0.0008)
- **Best holdout score**: -0.0172 (rank #2)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0240 | -0.0180 | -0.47 | 1.07 | 145 |
| 1 | 0.0028 | -0.1231 | 1.96 | 2.45 | 547 |
| 2 | 0.0025 | -0.0172 | 0.66 | 0.66 | 268 |
| 3 | 0.0024 | -0.0248 | 0.03 | 0.88 | 264 |
| 4 | 0.0022 | -0.0594 | 0.71 | 0.98 | 232 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52165
- **Expected rows**: 52165
- **Missing rows**: 0
- **Forward-fill count**: 1050
- **Forward-fill fraction**: 0.020128438608262245
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0499 <= 0; recent PnL -0.0124% < 0
- **Objective score**: -0.049906117182236795
- **PnL %**: -0.012429586551126678
- **Trade count**: 88

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0031 <= 0
- **Objective score**: -0.0031315185003673173
- **PnL %**: 0.08066638355494377
- **Trade count**: 52

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0844 <= 0
- **Objective score**: -0.08444940602037095
- **PnL %**: 0.2982613783888408
- **Trade count**: 29

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.05787053138489872
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0395, 0.0720 |
| sell_spread_base | 0.0609, 0.0528 |
| stop_loss | 0.0579, 0.0579 |
| take_profit | 0.0579, 0.0579 |
| executor_refresh_time | 0.0494, 0.0628 |
| cooldown_time | 0.0389, 0.0322 |
| total_amount_quote | 0.0553, 0.0581 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.377477456423548
- **Max CV**: 0.7804875836607754
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: stop_loss, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2020 | 1.4041319450459928 | 2.5088250534751655 | 1.9623959411368095 |
| buy_spread_ratio | 0.1148 | 2.0479311357174996 | 2.9671709882572954 | 2.550856145527581 |
| sell_spread_base | 0.4255 | 1.282418093897017 | 4.855634276372018 | 2.5499811170760003 |
| sell_spread_ratio | 0.1814 | 1.3514214930434594 | 2.281189820420212 | 1.8337880274203588 |
| buy_side_weight | 0.2301 | 0.32657477968002635 | 0.6583670938802013 | 0.46289525990547 |
| amount_skew | 0.4407 | 1.2712808843293801 | 3.8753034130413573 | 2.1783411416017886 |
| stop_loss | 0.5782 | 0.024659821270339544 | 0.17737902233582908 | 0.08546405321211274 |
| take_profit | 0.7805 | 0.00962982154651013 | 0.09266380929189447 | 0.031136152514178377 |
| executor_refresh_time | 0.3679 | 3923.0 | 13918.0 | 8470.2 |
| cooldown_time | 0.3501 | 1477.0 | 6936.0 | 4981.2 |
| total_amount_quote | 0.4811 | 46.04760160373277 | 237.76131244838723 | 144.6592551503224 |

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
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.049906117182236795 | FAIL |
| recent_pnl | >= 0 | -0.012429586551126678 | FAIL |
| recent_trades | >= 5 | 88 | PASS |
| worst_stress | > -10 | -0.027127622907190035 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.01801901515821877 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.027127622907190035 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.049906117182236795, pnl=-0.012429586551126678, trades=88, reason=recent objective score -0.0499 <= 0; recent PnL -0.0124% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.0031315185003673173, pnl=0.08066638355494377, trades=52, reason=recent objective score -0.0031 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.08444940602037095, pnl=0.2982613783888408, trades=29, reason=recent objective score -0.0844 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.377477456423548 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52165 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0499 <= 0; recent PnL -0.0124% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0031 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0844 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52165
- **Pre-release bars**: 44100
- **Dev bars**: 35280
- **Holdout bars**: 8820
- **Recent 28d bars**: 8065
- **Recent window start**: 1773370200

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-10T04:59:21.145712+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 14458
