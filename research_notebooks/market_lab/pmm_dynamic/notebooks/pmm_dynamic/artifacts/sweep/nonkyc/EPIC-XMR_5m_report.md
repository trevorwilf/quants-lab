# PMM Dynamic Optimization Report: nonkyc_EPIC-XMR_5m_sweep_v1

Generated: 2026-03-29 09:21:15 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T09:21:15.061528+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 6561 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: EPIC-XMR
- **interval**: 5m
- **n_candles**: 32611
- **dataset_hash**: dd68eda9f266297449a3b1c3a45970824ab0d1e81a75503d3922276a2fcea5bd
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 901.49864494684
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.037393680890189 |
| buy_n_levels | 2 |
| buy_side_weight | 0.3873795417340462 |
| buy_spread_base | 3.023424791261331 |
| buy_spread_ratio | 2.726277971444055 |
| cooldown_time | 416 |
| executor_refresh_time | 8499 |
| macd_fast | 9 |
| macd_signal | 27 |
| macd_slow | 48 |
| natr_length | 9 |
| sell_n_levels | 8 |
| sell_spread_base | 5.830215413455707 |
| sell_spread_ratio | 1.9581700947874259 |
| stop_loss | 0.17246804774741503 |
| take_profit | 0.04277708200487069 |
| time_limit | 130230 |
| total_amount_quote | 901.49864494684 |
| trailing_stop_activation | 0.011368306752523556 |
| trailing_stop_delta | 0.0014148003082644202 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 901.49864494684 |
| Selected | 901.49864494684 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 0.1756
- **Net PnL (quote)**: 1.5828
- **Sharpe Ratio**: 3.3143
- **Max Drawdown %**: 0.0401
- **Profit Factor**: 54.920727625722265
- **Trade Count**: 1620
- **Total Fees (quote)**: 0.1618
- **Maker Fees**: 0.0528
- **Taker Fees**: 0.1089
- **Fee Drag %**: 0.0179

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0009
- **PnL Component**: 0.0018
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0003
- **Fee Drag Component**: -0.0001
- **Inventory Component**: -0.0004
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0005**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.01 | 4.42 | 0.01 | 156 | -0.0001 | n/a |
| 1 | 0.06 | 8.77 | 0.02 | 182 | 0.0001 | n/a |
| 2 | 0.01 | 6.91 | 0.00 | 59 | 0.0000 | n/a |
| 3 | 0.00 | 10.09 | 0.00 | 55 | 0.0000 | n/a |
| 4 | 0.01 | 6.41 | 0.00 | 108 | -0.0001 | n/a |
| 5 | 0.01 | 2.49 | 0.04 | 231 | -0.0011 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.05 | 4.98 | 0.02 | 365 | -0.0006 | n/a |
| 8 | -0.01 | -3.49 | 0.02 | 182 | -0.0005 | n/a |
| 9 | -0.10 | -9.49 | 0.11 | 266 | -0.2323 | n/a |
| 10 | 0.00 | 7.13 | 0.00 | 17 | -0.1320 | n/a |
| 11 | 0.01 | 1.35 | 0.01 | 229 | -0.0011 | n/a |
| 12 | 0.00 | 2.52 | 0.00 | 129 | -0.0002 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 0.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 0.17 | 3.17 | 0.04 | 0.0008 |
| fees_2x | 0.16 | 3.03 | 0.04 | 0.0007 |
| latency_plus1 | 0.18 | 3.31 | 0.04 | 0.0009 |
| latency_plus2 | 0.18 | 3.31 | 0.04 | 0.0009 |
| latency_plus3 | 0.18 | 3.31 | 0.04 | 0.0009 |
| low_liquidity | 0.09 | 3.31 | 0.02 | 0.0005 |
| very_low_liquidity | 0.04 | 3.32 | 0.01 | 0.0002 |
| high_slippage | 0.17 | 3.27 | 0.04 | 0.0009 |
| extreme_slippage | 0.17 | 3.19 | 0.04 | 0.0008 |
| combined_adverse | 0.08 | 3.13 | 0.02 | 0.0004 |
| spread_widen_10bps | 0.17 | 3.26 | 0.04 | 0.0009 |
| spread_widen_25bps | 0.19 | 2.69 | 0.08 | 0.0004 |
| thin_book | 0.03 | 3.88 | 0.00 | 0.0002 |
| very_thin_book | 0.01 | 1.82 | 0.00 | 0.0000 |
| entry_spread_stress | 0.19 | 2.72 | 0.08 | 0.0004 |
| combined_market_deterioration | 0.02 | 3.57 | 0.00 | 0.0001 |
| severe_adverse | 0.01 | 2.63 | 0.00 | 0.0000 |

## Holdout Validation

- **Holdout bars**: 4909
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0082)
- **Trend**: ranging (efficiency: 0.0092)
- **Best holdout score**: 0.0002 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0005 | -0.0001 | 0.04 | 0.02 | 535 |
| 1 | -0.0000 | 0.0002 | 0.05 | 0.03 | 306 |
| 2 | -0.0000 | -0.0000 | 0.00 | 0.00 | 51 |
| 3 | -0.0001 | -0.0013 | 0.01 | 0.07 | 482 |
| 4 | -0.0001 | -0.2965 | -1.04 | 1.05 | 1855 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 32611
- **Expected rows**: 32611
- **Missing rows**: 0
- **Forward-fill count**: 580
- **Forward-fill fraction**: 0.017785409831038608
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0032 <= 0; recent PnL -0.0976% < 0
- **Objective score**: -0.0032096314859587517
- **PnL %**: -0.097645672768017
- **Trade count**: 512

## Sensitivity Analysis

- **Sensitivity penalty**: 0.2857142857142857
- **Baseline score**: -0.00041317848526935177
- **Sign flips**: 0
- **Collapse count**: 4
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1663, -0.0090 |
| sell_spread_base | -0.0004, -0.0004 |
| stop_loss | -0.0004, -0.0002 |
| take_profit | -0.0004, -0.0004 |
| executor_refresh_time | -0.0096, -0.2949 |
| cooldown_time | -0.0004, -0.0004 |
| total_amount_quote | -0.0004, -0.0005 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.40124371982417273
- **Max CV**: 1.075070165257278
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2640 | 2.7205537635594133 | 5.974430858327699 | 4.397009986899113 |
| buy_spread_ratio | 0.1954 | 1.266786243330869 | 2.954483773843372 | 2.409251433455 |
| sell_spread_base | 1.0751 | 0.20388900224327905 | 5.840115220922757 | 2.0644324936409775 |
| sell_spread_ratio | 0.2133 | 1.2123811857508182 | 2.7897437096486923 | 2.1067379598314413 |
| buy_side_weight | 0.2352 | 0.28271168852863615 | 0.5353658635103085 | 0.40373343328640177 |
| amount_skew | 0.2370 | 1.757969633249608 | 3.6816698141510753 | 2.574695155640274 |
| stop_loss | 0.4277 | 0.05386891155662472 | 0.240036705592521 | 0.14835217738685214 |
| take_profit | 0.8932 | 0.0052097532086846235 | 0.07793180502395225 | 0.030556571503042078 |
| executor_refresh_time | 0.1493 | 5641.0 | 9764.0 | 7911.2 |
| cooldown_time | 0.6504 | 214.0 | 1927.0 | 837.3 |
| total_amount_quote | 0.0731 | 729.477792076561 | 952.9765400683673 | 864.1946397584237 |

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
| recent_objective | > 0 | -0.0032096314859587517 | FAIL |
| recent_pnl | >= 0 | -0.097645672768017 | FAIL |
| recent_trades | >= 5 | 512 | PASS |
| worst_stress | > -10 | 1.4118447322018296e-05 | PASS |
| sensitivity_penalty | < 0.50 | 0.2857142857142857 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.00014005393986222094 |
| walkforward | PASS | 13 folds |
| stress | PASS | worst=severe_adverse score=1.4118447322018296e-05 |
| sensitivity | PASS | penalty=0.2857142857142857 |
| recent_28d | FAIL | score=-0.0032096314859587517, pnl=-0.097645672768017, trades=512, reason=recent objective score -0.0032 <= 0; recent PnL -0.0976% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.40124371982417273 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 32611 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0032 <= 0; recent PnL -0.0976% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 19637
- **Holdout bars**: 4909
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T09:21:15.061528+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 6561
