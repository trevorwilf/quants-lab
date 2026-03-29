# PMM Dynamic Optimization Report: mexc_RENDER-USDT_5m_sweep_v1

Generated: 2026-03-28 17:28:34 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T17:28:34.031176+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 11517 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: RENDER-USDT
- **interval**: 5m
- **n_candles**: 51985
- **dataset_hash**: 96d167a8f27a82d9f5914420e2bebde1ec8406a2fc542e9a3e02ebc72e7c96bf
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 837.6941375624145
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.4550258649843233 |
| buy_n_levels | 10 |
| buy_side_weight | 0.3619263867977944 |
| buy_spread_base | 2.811528287525034 |
| buy_spread_ratio | 1.7872044867713477 |
| cooldown_time | 3942 |
| executor_refresh_time | 1079 |
| macd_fast | 8 |
| macd_signal | 20 |
| macd_slow | 35 |
| natr_length | 32 |
| sell_n_levels | 7 |
| sell_spread_base | 2.1060056715944424 |
| sell_spread_ratio | 2.2756966978131263 |
| stop_loss | 0.01786128252770283 |
| take_profit | 0.006761872799983505 |
| time_limit | 51529 |
| total_amount_quote | 837.6941375624145 |
| trailing_stop_activation | 0.00011556487823657425 |
| trailing_stop_delta | 0.0011378219566139424 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 837.6941375624145 |
| Selected | 837.6941375624145 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2.5034
- **Net PnL (quote)**: 20.9711
- **Sharpe Ratio**: 3.9806
- **Max Drawdown %**: 0.6152
- **Profit Factor**: 2.2455694081947795
- **Trade Count**: 502
- **Total Fees (quote)**: 3.0837
- **Maker Fees**: 1.5394
- **Taker Fees**: 1.5443
- **Fee Drag %**: 0.3681

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0183
- **PnL Component**: 0.0247
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0046
- **Fee Drag Component**: -0.0018
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0010**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.38 | 6.45 | 0.12 | 58 | 0.0027 | n/a |
| 1 | -0.51 | -5.75 | 0.63 | 43 | -0.0381 | n/a |
| 2 | 0.12 | 4.06 | 0.08 | 27 | -0.0916 | n/a |
| 3 | 0.09 | 9.32 | 0.04 | 96 | 0.0006 | n/a |
| 4 | 0.12 | 5.14 | 0.05 | 53 | 0.0006 | n/a |
| 5 | 0.43 | 12.01 | 0.06 | 59 | 0.0037 | n/a |
| 6 | 0.19 | 4.93 | 0.14 | 51 | 0.0006 | n/a |
| 7 | 0.75 | 12.61 | 0.07 | 58 | 0.0067 | n/a |
| 8 | 0.09 | 6.40 | 0.04 | 38 | -0.0474 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0736)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2.32 | 3.70 | 0.63 | 0.0154 |
| fees_2x | 2.14 | 3.42 | 0.65 | 0.0126 |
| latency_plus1 | 2.64 | 4.02 | 0.62 | 0.0196 |
| latency_plus2 | 3.35 | 4.18 | 0.67 | 0.0261 |
| latency_plus3 | 1.97 | 2.96 | 0.80 | 0.0099 |
| low_liquidity | 2.49 | 3.97 | 0.62 | 0.0182 |
| very_low_liquidity | 2.44 | 3.87 | 0.62 | 0.0176 |
| high_slippage | 2.04 | 3.31 | 0.66 | 0.0134 |
| extreme_slippage | 1.12 | 1.88 | 0.76 | 0.0036 |
| combined_adverse | 1.99 | 3.11 | 0.68 | 0.0118 |
| spread_widen_10bps | 2.12 | 3.38 | 0.68 | 0.0141 |
| spread_widen_25bps | 1.52 | 2.34 | 0.70 | 0.0078 |
| thin_book | -1.49 | -1.54 | 2.24 | -0.0330 |
| very_thin_book | -1.41 | -0.43 | 3.96 | -0.0443 |
| entry_spread_stress | 1.75 | 2.74 | 0.68 | 0.0104 |
| combined_market_deterioration | 0.39 | 0.60 | 1.33 | -0.0086 |
| severe_adverse | -3.08 | -0.95 | 4.08 | -0.0736 |

## Holdout Validation

- **Holdout bars**: 8784
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0049)
- **Trend**: ranging (efficiency: 0.0157)
- **Best holdout score**: 0.0141 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0277 | 0.0109 | 1.26 | 0.14 | 129 |
| 1 | 0.0022 | 0.0107 | 1.69 | 0.27 | 450 |
| 2 | 0.0021 | 0.0141 | 2.58 | 0.65 | 235 |
| 3 | 0.0016 | 0.0027 | 0.89 | 0.60 | 216 |
| 4 | 0.0012 | 0.0085 | 1.43 | 0.34 | 390 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51985
- **Expected rows**: 51985
- **Missing rows**: 0
- **Forward-fill count**: 6
- **Forward-fill fraction**: 0.00011541790901221507
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.00035827298552932425
- **PnL %**: 0.18433859797377128
- **Trade count**: 95

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.03136269611350142
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0320, 0.0298 |
| sell_spread_base | 0.0314, 0.0322 |
| stop_loss | 0.0294, 0.0339 |
| take_profit | 0.0314, 0.0314 |
| executor_refresh_time | 0.0314, 0.0314 |
| cooldown_time | 0.0484, 0.0551 |
| total_amount_quote | 0.0315, 0.0590 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.42784185364185984
- **Max CV**: 0.8553655978547207
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, total_amount_quote
- **Scattered params**: take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2225 | 0.8324778362259906 | 2.2634737245953054 | 1.6805824970235488 |
| buy_spread_ratio | 0.1761 | 1.4215842684108329 | 2.65846366640342 | 1.9455173812453808 |
| sell_spread_base | 0.4984 | 1.0013082899039305 | 5.390040582439128 | 2.9245846136530416 |
| sell_spread_ratio | 0.1888 | 1.2442465511018184 | 2.391889641189397 | 1.912768038319749 |
| buy_side_weight | 0.2999 | 0.21172894115985907 | 0.4710172333465549 | 0.32282926732853495 |
| amount_skew | 0.3968 | 1.3547474126849028 | 3.8509611735190674 | 2.458565129042022 |
| stop_loss | 0.3221 | 0.012356728315657426 | 0.030273496088782187 | 0.01732790177430493 |
| take_profit | 0.8554 | 0.005539142580544523 | 0.06541918601680752 | 0.023894626117600865 |
| executor_refresh_time | 0.7980 | 426.0 | 12160.0 | 5807.0 |
| cooldown_time | 0.7095 | 458.0 | 4481.0 | 2013.1 |
| total_amount_quote | 0.2387 | 414.69164766990275 | 948.902320748116 | 747.3442578753898 |

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
- holdout_passed: PASS
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.00035827298552932425 | PASS |
| recent_pnl | >= 0 | 0.18433859797377128 | PASS |
| recent_trades | >= 5 | 95 | PASS |
| worst_stress | > -10 | -0.07361397431625845 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0109 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.07361397431625845 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.00035827298552932425, pnl=0.18433859797377128, trades=95, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.42784185364185984 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51985 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35136
- **Holdout bars**: 8784
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T17:28:34.031176+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 11517
