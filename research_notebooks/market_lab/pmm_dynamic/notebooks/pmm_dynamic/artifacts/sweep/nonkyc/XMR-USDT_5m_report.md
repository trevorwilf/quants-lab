# PMM Dynamic Optimization Report: nonkyc_XMR-USDT_5m_sweep_v1

Generated: 2026-03-29 13:14:18 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T13:14:18.487171+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 6703 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 51922
- **dataset_hash**: 5f6fda99144cb0c64db37b8093b8fc0354490dd6ca9ea922ffbe3e2bd006e623
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 997.5117558828217
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.811018764626086 |
| buy_n_levels | 10 |
| buy_side_weight | 0.7098408685214288 |
| buy_spread_base | 1.7696221309204396 |
| buy_spread_ratio | 2.9135557271410875 |
| cooldown_time | 3600 |
| executor_refresh_time | 12267 |
| macd_fast | 41 |
| macd_signal | 17 |
| macd_slow | 65 |
| natr_length | 42 |
| sell_n_levels | 9 |
| sell_spread_base | 3.438873536294514 |
| sell_spread_ratio | 1.8489698708077484 |
| stop_loss | 0.011181056508103504 |
| take_profit | 0.005692405203922646 |
| time_limit | 101351 |
| total_amount_quote | 997.5117558828217 |
| trailing_stop_activation | 0.007755141530527924 |
| trailing_stop_delta | 0.0013735966276971362 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 997.5117558828217 |
| Selected | 997.5117558828217 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 17.1610
- **Net PnL (quote)**: 171.1833
- **Sharpe Ratio**: 2.0795
- **Max Drawdown %**: 0.4999
- **Profit Factor**: 5.388244392531251
- **Trade Count**: 653
- **Total Fees (quote)**: 30.8708
- **Maker Fees**: 14.4094
- **Taker Fees**: 16.4614
- **Fee Drag %**: 3.0948

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1370
- **PnL Component**: 0.1584
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0037
- **Fee Drag Component**: -0.0155
- **Inventory Component**: -0.0021
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0052**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.23 | 4.00 | 0.25 | 74 | -0.0038 | n/a |
| 1 | 0.07 | 2.84 | 0.13 | 76 | -0.0039 | n/a |
| 2 | 0.38 | 6.57 | 0.14 | 63 | -0.0009 | n/a |
| 3 | -0.01 | -0.23 | 0.15 | 85 | -0.0052 | n/a |
| 4 | 1.53 | 4.68 | 0.50 | 75 | 0.0066 | n/a |
| 5 | -0.00 | -0.01 | 0.21 | 85 | -0.0061 | n/a |
| 6 | -0.20 | -6.23 | 0.33 | 80 | -0.0086 | n/a |
| 7 | -0.21 | -5.13 | 0.34 | 92 | -0.0088 | n/a |
| 8 | 0.22 | 13.58 | 0.04 | 67 | -0.0015 | n/a |

## Stress Test Results

Worst Scenario: **very_thin_book** (score: -0.0406)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 15.61 | 1.91 | 0.64 | 0.1150 |
| fees_2x | 14.07 | 1.74 | 0.87 | 0.0920 |
| latency_plus1 | 17.14 | 2.08 | 0.48 | 0.1372 |
| latency_plus2 | 16.89 | 2.05 | 0.48 | 0.1350 |
| latency_plus3 | 16.09 | 1.95 | 0.48 | 0.1291 |
| low_liquidity | 9.48 | 2.69 | 0.93 | 0.0610 |
| very_low_liquidity | 5.55 | 3.08 | 1.37 | 0.0172 |
| high_slippage | 16.75 | 2.03 | 0.54 | 0.1332 |
| extreme_slippage | 15.93 | 1.94 | 0.62 | 0.1256 |
| combined_adverse | 7.17 | 2.07 | 1.37 | 0.0275 |
| spread_widen_10bps | 17.33 | 2.07 | 1.06 | 0.1269 |
| spread_widen_25bps | 15.08 | 1.92 | 1.32 | 0.1050 |
| thin_book | 13.86 | 1.84 | 1.19 | 0.1060 |
| very_thin_book | -1.43 | -1.22 | 1.97 | -0.0406 |
| entry_spread_stress | 17.32 | 2.07 | 0.95 | 0.1269 |
| combined_market_deterioration | 0.16 | 0.13 | 1.72 | -0.0324 |
| severe_adverse | 7.05 | 1.08 | 3.58 | 0.0176 |

## Holdout Validation

- **Holdout bars**: 8771
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0054)
- **Trend**: ranging (efficiency: 0.0158)
- **Best holdout score**: -0.0059 (rank #0)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0482 | -0.0059 | 0.31 | 0.34 | 194 |
| 1 | 0.0009 | -0.0416 | -0.59 | 0.82 | 177 |
| 2 | 0.0007 | -0.0091 | -0.20 | 0.31 | 159 |
| 3 | 0.0001 | -0.0082 | 0.06 | 0.35 | 186 |
| 4 | -0.0001 | -0.0570 | -0.12 | 0.29 | 166 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51922
- **Expected rows**: 51922
- **Missing rows**: 0
- **Forward-fill count**: 230
- **Forward-fill fraction**: 0.004429721505334925
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0036 <= 0
- **Objective score**: -0.0036040461627437808
- **PnL %**: 0.1904154785963338
- **Trade count**: 138

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.13327277698342044
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.1032, 0.1135 |
| sell_spread_base | 0.1327, 0.1302 |
| stop_loss | 0.1353, 0.1248 |
| take_profit | 0.1123, 0.1202 |
| executor_refresh_time | 0.1027, 0.1149 |
| cooldown_time | 0.1014, 0.0816 |
| total_amount_quote | 0.1214, 0.1428 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3468493790960612
- **Max CV**: 0.8147168863802307
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0879 | 1.974351295849159 | 2.4640841304628593 | 2.24858390660201 |
| buy_spread_ratio | 0.1242 | 1.9217333535545142 | 2.925725874904507 | 2.494334603090669 |
| sell_spread_base | 0.8147 | 0.28149453025177745 | 5.895345919780377 | 2.617477234319112 |
| sell_spread_ratio | 0.2156 | 1.3435364903901286 | 2.371256660967298 | 1.72341722695097 |
| buy_side_weight | 0.3248 | 0.23484594126144256 | 0.7112762089939647 | 0.454013205729483 |
| amount_skew | 0.1536 | 2.637521149254132 | 3.9985938472300946 | 3.3849217825461606 |
| stop_loss | 0.2040 | 0.012260411884841007 | 0.02198413804088998 | 0.015581495944157378 |
| take_profit | 0.3753 | 0.006183874664068052 | 0.019566931360301677 | 0.012001796893837208 |
| executor_refresh_time | 0.4221 | 1283.0 | 14111.0 | 9159.4 |
| cooldown_time | 0.7777 | 144.0 | 5368.0 | 2023.2 |
| total_amount_quote | 0.3155 | 160.17897297554933 | 953.7546474356368 | 735.085875994943 |

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
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.0036040461627437808 | FAIL |
| recent_pnl | >= 0 | 0.1904154785963338 | PASS |
| recent_trades | >= 5 | 138 | PASS |
| worst_stress | > -10 | -0.04055848402950462 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.005928814397087319 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_thin_book score=-0.04055848402950462 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.0036040461627437808, pnl=0.1904154785963338, trades=138, reason=recent objective score -0.0036 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3468493790960612 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51922 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0036 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35086
- **Holdout bars**: 8771
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T13:14:18.487171+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 6703
