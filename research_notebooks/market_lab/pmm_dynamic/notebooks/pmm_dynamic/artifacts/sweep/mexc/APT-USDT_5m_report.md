# PMM Dynamic Optimization Report: mexc_APT-USDT_5m_sweep_v1

Generated: 2026-03-28 06:38:41 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T06:38:41.769368+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 7381 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: APT-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 7656a43f210991e383c0ecaa9c53d9fe73b7410a3ccabd093ae92e70ba66fdf7
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 881.1740340546743
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.670380154646355 |
| buy_n_levels | 5 |
| buy_side_weight | 0.20650658221448304 |
| buy_spread_base | 2.1365653951682124 |
| buy_spread_ratio | 2.541392555771228 |
| cooldown_time | 2515 |
| executor_refresh_time | 3962 |
| macd_fast | 38 |
| macd_signal | 11 |
| macd_slow | 42 |
| natr_length | 47 |
| sell_n_levels | 9 |
| sell_spread_base | 4.672217151413237 |
| sell_spread_ratio | 1.336761791038137 |
| stop_loss | 0.013340788492611859 |
| take_profit | 0.0058853687566104845 |
| time_limit | 171734 |
| total_amount_quote | 881.1740340546743 |
| trailing_stop_activation | 0.052151969820407526 |
| trailing_stop_delta | 0.0025760028307467335 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 881.1740340546743 |
| Selected | 881.1740340546743 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.1651
- **Net PnL (quote)**: -10.2667
- **Sharpe Ratio**: -2.7930
- **Max Drawdown %**: 1.2456
- **Profit Factor**: 0.6747458101197239
- **Trade Count**: 730
- **Total Fees (quote)**: 2.4391
- **Maker Fees**: 2.0016
- **Taker Fees**: 0.4375
- **Fee Drag %**: 0.2768

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0242
- **PnL Component**: -0.0117
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0093
- **Fee Drag Component**: -0.0014
- **Inventory Component**: -0.0018
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0040**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.07 | -3.51 | 0.15 | 104 | -0.0038 | n/a |
| 1 | -0.28 | -10.07 | 0.31 | 91 | -0.0099 | n/a |
| 2 | 0.01 | 1.08 | 0.08 | 65 | -0.0023 | n/a |
| 3 | 0.11 | 8.72 | 0.03 | 56 | -0.0010 | n/a |
| 4 | -0.33 | -9.52 | 0.36 | 82 | -0.0097 | n/a |
| 5 | -0.04 | -2.05 | 0.09 | 95 | -0.0031 | n/a |
| 6 | -0.07 | -3.31 | 0.10 | 82 | -0.0034 | n/a |
| 7 | -0.10 | -2.78 | 0.22 | 84 | -0.0075 | n/a |
| 8 | 0.02 | 1.19 | 0.07 | 61 | -0.0022 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0524)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.30 | -3.12 | 1.37 | -0.0273 |
| fees_2x | -1.44 | -3.45 | 1.50 | -0.0304 |
| latency_plus1 | -1.17 | -3.29 | 1.28 | -0.0245 |
| latency_plus2 | -1.20 | -3.37 | 1.31 | -0.0250 |
| latency_plus3 | -1.16 | -3.26 | 1.26 | -0.0243 |
| low_liquidity | -1.17 | -2.79 | 1.25 | -0.0242 |
| very_low_liquidity | -1.17 | -2.79 | 1.25 | -0.0242 |
| high_slippage | -1.29 | -3.09 | 1.36 | -0.0264 |
| extreme_slippage | -1.54 | -3.70 | 1.60 | -0.0307 |
| combined_adverse | -1.43 | -4.01 | 1.52 | -0.0297 |
| spread_widen_10bps | -1.37 | -3.75 | 1.47 | -0.0280 |
| spread_widen_25bps | -1.53 | -4.13 | 1.61 | -0.0307 |
| thin_book | -2.08 | -0.87 | 3.54 | -0.0506 |
| very_thin_book | -1.07 | -7.59 | 1.10 | -0.0214 |
| entry_spread_stress | -1.47 | -3.15 | 1.58 | -0.0298 |
| combined_market_deterioration | -2.21 | -4.66 | 2.30 | -0.0434 |
| severe_adverse | -2.72 | -4.98 | 2.81 | -0.0524 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0042)
- **Trend**: ranging (efficiency: 0.0311)
- **Best holdout score**: -0.0068 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0383 | -0.0068 | -0.26 | 0.27 | 193 |
| 1 | -0.0035 | -0.0093 | -0.30 | 0.35 | 212 |
| 2 | -0.0035 | -0.0086 | -0.36 | 0.39 | 165 |
| 3 | -0.0036 | -0.0090 | -0.32 | 0.43 | 748 |
| 4 | -0.0038 | -0.0077 | -0.31 | 0.34 | 169 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 20
- **Forward-fill fraction**: 0.00038579502710210065
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0045 <= 0
- **Objective score**: -0.004500739627132122
- **PnL %**: 0.011255626930590196
- **Trade count**: 132

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.02956552781903623
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0259, -0.0282 |
| sell_spread_base | -0.0273, -0.0301 |
| stop_loss | -0.0279, -0.0320 |
| take_profit | -0.0248, -0.0276 |
| executor_refresh_time | -0.0306, -0.0276 |
| cooldown_time | -0.0239, -0.0280 |
| total_amount_quote | -0.0284, -0.0295 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3017004651257309
- **Max CV**: 0.8000730418376739
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, total_amount_quote
- **Scattered params**: executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1880 | 1.6909361753788035 | 2.94127986904957 | 2.026484594465493 |
| buy_spread_ratio | 0.1467 | 1.8682213480004002 | 2.8689815739223663 | 2.559518304029737 |
| sell_spread_base | 0.4507 | 1.5632096819334211 | 5.863772112651034 | 3.476552514304103 |
| sell_spread_ratio | 0.4064 | 1.2187275985911001 | 2.9948728166178484 | 1.9404193241891057 |
| buy_side_weight | 0.2202 | 0.21980617832431132 | 0.4068096655424107 | 0.2974348147389765 |
| amount_skew | 0.1162 | 2.3770616322770044 | 3.353959161075111 | 2.8757810381419175 |
| stop_loss | 0.2158 | 0.010198001200253578 | 0.018731390068277735 | 0.012073198546394822 |
| take_profit | 0.1200 | 0.005573993617062659 | 0.008170254185028506 | 0.006556803537407609 |
| executor_refresh_time | 0.5196 | 352.0 | 14227.0 | 8329.6 |
| cooldown_time | 0.8001 | 88.0 | 3214.0 | 1359.6 |
| total_amount_quote | 0.1350 | 626.3608250794643 | 999.3288204546292 | 809.7294574919749 |

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
| recent_objective | > 0 | -0.004500739627132122 | FAIL |
| recent_pnl | >= 0 | 0.011255626930590196 | PASS |
| recent_trades | >= 5 | 132 | PASS |
| worst_stress | > -10 | -0.052397576062608454 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.0067898719774243214 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.052397576062608454 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.004500739627132122, pnl=0.011255626930590196, trades=132, reason=recent objective score -0.0045 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3017004651257309 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0045 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T06:38:41.769368+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 7381
