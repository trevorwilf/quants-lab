# PMM Dynamic Optimization Report: nonkyc_SOL-USDT_5m_sweep_v1

Generated: 2026-03-29 12:36:24 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T12:36:24.387683+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 11996 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: SOL-USDT
- **interval**: 5m
- **n_candles**: 51922
- **dataset_hash**: eacaabc7ff4d9c0bf15f857f6f2951abf8d6312a10a288d248b0861fa2a21e0f
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 962.0310720264569
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.9204060934273475 |
| buy_n_levels | 9 |
| buy_side_weight | 0.5288702883189127 |
| buy_spread_base | 5.170514362619248 |
| buy_spread_ratio | 1.9995596973413887 |
| cooldown_time | 306 |
| executor_refresh_time | 7317 |
| macd_fast | 49 |
| macd_signal | 29 |
| macd_slow | 65 |
| natr_length | 34 |
| sell_n_levels | 9 |
| sell_spread_base | 3.6265207075169505 |
| sell_spread_ratio | 1.3408251732362424 |
| stop_loss | 0.017677060349661683 |
| take_profit | 0.0065837976695370965 |
| time_limit | 29274 |
| total_amount_quote | 962.0310720264569 |
| trailing_stop_activation | 0.046053956876332965 |
| trailing_stop_delta | 0.0032752220575683346 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 962.0310720264569 |
| Selected | 962.0310720264569 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.7135
- **Net PnL (quote)**: -26.1047
- **Sharpe Ratio**: -5.5166
- **Max Drawdown %**: 2.7402
- **Profit Factor**: 0.34034605923712796
- **Trade Count**: 559
- **Total Fees (quote)**: 10.6079
- **Maker Fees**: 6.9265
- **Taker Fees**: 3.6814
- **Fee Drag %**: 1.1027

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0580
- **PnL Component**: -0.0275
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0206
- **Fee Drag Component**: -0.0055
- **Inventory Component**: -0.0044
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0499**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.12 | -7.78 | 0.16 | 41 | -0.0405 | n/a |
| 1 | -0.26 | -2.02 | 0.77 | 40 | -0.0508 | n/a |
| 2 | -0.19 | -9.95 | 0.25 | 35 | -0.0658 | n/a |
| 3 | -0.11 | -4.92 | 0.22 | 93 | -0.0067 | n/a |
| 4 | -0.76 | -5.81 | 0.80 | 43 | -0.0476 | n/a |
| 5 | -0.92 | -13.65 | 0.97 | 83 | -0.0211 | n/a |
| 6 | -0.12 | -5.73 | 0.16 | 39 | -0.0485 | n/a |
| 7 | -0.37 | -10.59 | 0.46 | 47 | -0.0216 | n/a |
| 8 | -0.06 | -3.88 | 0.12 | 83 | -0.0052 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.0833)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -3.26 | -6.56 | 3.29 | -0.0706 |
| fees_2x | -3.82 | -7.57 | 3.84 | -0.0833 |
| latency_plus1 | -2.71 | -5.51 | 2.74 | -0.0580 |
| latency_plus2 | -2.70 | -5.50 | 2.73 | -0.0579 |
| latency_plus3 | -2.72 | -5.52 | 2.74 | -0.0580 |
| low_liquidity | -2.71 | -5.52 | 2.74 | -0.0580 |
| very_low_liquidity | -2.71 | -5.52 | 2.74 | -0.0580 |
| high_slippage | -2.81 | -5.69 | 2.84 | -0.0598 |
| extreme_slippage | -3.00 | -6.02 | 3.03 | -0.0632 |
| combined_adverse | -3.36 | -6.72 | 3.38 | -0.0723 |
| spread_widen_10bps | -2.93 | -5.86 | 2.96 | -0.0628 |
| spread_widen_25bps | -3.70 | -5.94 | 3.95 | -0.0775 |
| thin_book | -2.56 | -3.84 | 2.60 | -0.0532 |
| very_thin_book | -1.54 | -3.14 | 1.56 | -0.0314 |
| entry_spread_stress | -3.65 | -5.94 | 3.87 | -0.0783 |
| combined_market_deterioration | -3.63 | -7.47 | 3.66 | -0.0761 |
| severe_adverse | -2.78 | -4.99 | 3.07 | -0.0614 |

## Holdout Validation

- **Holdout bars**: 8771
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0035)
- **Trend**: ranging (efficiency: 0.0210)
- **Best holdout score**: -0.0123 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0707 | -0.0131 | -0.52 | 0.65 | 88 |
| 1 | -0.0071 | -0.0210 | -0.98 | 0.98 | 142 |
| 2 | -0.0078 | -0.0173 | -0.75 | 0.78 | 143 |
| 3 | -0.0080 | -0.0391 | -1.66 | 1.67 | 502 |
| 4 | -0.0080 | -0.0123 | -0.49 | 0.51 | 154 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51922
- **Expected rows**: 51922
- **Missing rows**: 0
- **Forward-fill count**: 118
- **Forward-fill fraction**: 0.0022726397288240054
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0098 <= 0; recent PnL -0.3445% < 0
- **Objective score**: -0.009844208970885242
- **PnL %**: -0.3444777203968648
- **Trade count**: 54

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.11675269965556263
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0608, -0.1085 |
| sell_spread_base | -0.1211, -0.1241 |
| stop_loss | -0.1079, -0.1155 |
| take_profit | -0.1253, -0.0782 |
| executor_refresh_time | -0.0954, -0.0945 |
| cooldown_time | -0.1168, -0.0929 |
| total_amount_quote | -0.1272, -0.1739 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3511588822004928
- **Max CV**: 1.6698831684734192
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, total_amount_quote
- **Scattered params**: executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1383 | 3.290783202287306 | 5.170514362619248 | 3.9474806249017456 |
| buy_spread_ratio | 0.0559 | 1.9995596973413887 | 2.3366397161374683 | 2.1728290002880746 |
| sell_spread_base | 0.2975 | 1.9002156083335744 | 5.1416223805493 | 3.830897639641203 |
| sell_spread_ratio | 0.1438 | 1.270059132091653 | 1.848873510699305 | 1.4770071296902838 |
| buy_side_weight | 0.2983 | 0.2229060801269772 | 0.6006280583686101 | 0.3950448420216397 |
| amount_skew | 0.1217 | 2.620758475504349 | 3.9433346161901652 | 3.371356366379621 |
| stop_loss | 0.1956 | 0.010286524214490722 | 0.017677060349661683 | 0.012339427206974753 |
| take_profit | 0.1276 | 0.005243973339636829 | 0.0078841653288965 | 0.006451600933566374 |
| executor_refresh_time | 0.7105 | 520.0 | 11359.0 | 4801.7 |
| cooldown_time | 1.6699 | 60.0 | 4537.0 | 838.1 |
| total_amount_quote | 0.1037 | 692.9662264862035 | 996.936118207531 | 919.380369092315 |

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
| recent_objective | > 0 | -0.009844208970885242 | FAIL |
| recent_pnl | >= 0 | -0.3444777203968648 | FAIL |
| recent_trades | >= 5 | 54 | PASS |
| worst_stress | > -10 | -0.08326220063496109 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.013081210614897242 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.08326220063496109 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.009844208970885242, pnl=-0.3444777203968648, trades=54, reason=recent objective score -0.0098 <= 0; recent PnL -0.3445% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3511588822004928 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51922 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0098 <= 0; recent PnL -0.3445% < 0 |
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
- **run_timestamp**: 2026-03-29T12:36:24.387683+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 11996
