# PMM Dynamic Optimization Report: mexc_WLFI-USDT_5m_sweep_v1

Generated: 2026-03-28 22:54:23 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T22:54:23.056060+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 1492 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: WLFI-USDT
- **interval**: 5m
- **n_candles**: 51985
- **dataset_hash**: 7672061bfe54f294627a2b347262360761a0fb07b870676952e4ffe716ce1380
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 894.9755814747851
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.2971304058674606 |
| buy_n_levels | 9 |
| buy_side_weight | 0.3709891802854467 |
| buy_spread_base | 0.46480020386269666 |
| buy_spread_ratio | 1.500597909937737 |
| cooldown_time | 2817 |
| executor_refresh_time | 6073 |
| macd_fast | 43 |
| macd_signal | 17 |
| macd_slow | 76 |
| natr_length | 44 |
| sell_n_levels | 2 |
| sell_spread_base | 1.6289977593256426 |
| sell_spread_ratio | 1.503055246368445 |
| stop_loss | 0.010577550265465505 |
| take_profit | 0.009016403692741754 |
| time_limit | 89656 |
| total_amount_quote | 894.9755814747851 |
| trailing_stop_activation | 0.004289784726385938 |
| trailing_stop_delta | 0.0011869414869506898 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 894.9755814747851 |
| Selected | 894.9755814747851 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 1.6824
- **Net PnL (quote)**: 15.0574
- **Sharpe Ratio**: 0.4038
- **Max Drawdown %**: 5.3887
- **Profit Factor**: 1.215082915138319
- **Trade Count**: 1051
- **Total Fees (quote)**: 8.2334
- **Maker Fees**: 4.1144
- **Taker Fees**: 4.1190
- **Fee Drag %**: 0.9200

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0285
- **PnL Component**: 0.0167
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0404
- **Fee Drag Component**: -0.0046
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0075**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.84 | 4.85 | 0.70 | 178 | 0.0022 | n/a |
| 1 | -0.08 | -0.95 | 0.37 | 152 | -0.0222 | n/a |
| 2 | 0.06 | 1.03 | 0.28 | 65 | -0.0019 | n/a |
| 3 | 0.65 | 13.83 | 0.06 | 51 | 0.0058 | n/a |
| 4 | 0.40 | 4.05 | 0.62 | 122 | -0.0129 | n/a |
| 5 | -0.64 | -4.00 | 1.07 | 135 | -0.0181 | n/a |
| 6 | 1.62 | 6.27 | 0.66 | 148 | 0.0103 | n/a |
| 7 | 1.27 | 5.55 | 0.35 | 103 | 0.0095 | n/a |
| 8 | 0.22 | 9.21 | 0.11 | 39 | -0.0428 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1429)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 1.22 | 0.31 | 5.42 | -0.0355 |
| fees_2x | 0.76 | 0.23 | 5.45 | -0.0426 |
| latency_plus1 | 1.54 | 0.38 | 5.39 | -0.0298 |
| latency_plus2 | 1.23 | 0.32 | 5.39 | -0.0328 |
| latency_plus3 | 0.73 | 0.22 | 5.39 | -0.0377 |
| low_liquidity | 1.68 | 0.40 | 5.39 | -0.0285 |
| very_low_liquidity | 1.68 | 0.40 | 5.39 | -0.0285 |
| high_slippage | 0.53 | 0.18 | 5.46 | -0.0404 |
| extreme_slippage | -1.77 | -0.27 | 5.60 | -0.0646 |
| combined_adverse | -0.05 | 0.07 | 5.49 | -0.0487 |
| spread_widen_10bps | 1.31 | 0.33 | 5.54 | -0.0399 |
| spread_widen_25bps | -0.95 | -0.11 | 5.71 | -0.0644 |
| thin_book | -2.82 | -0.48 | 7.89 | -0.0998 |
| very_thin_book | -3.79 | -0.60 | 7.20 | -0.0983 |
| entry_spread_stress | -0.51 | -0.02 | 5.69 | -0.0593 |
| combined_market_deterioration | -3.58 | -0.64 | 7.28 | -0.1188 |
| severe_adverse | -7.06 | -1.22 | 7.45 | -0.1429 |

## Holdout Validation

- **Holdout bars**: 8784
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0053)
- **Trend**: ranging (efficiency: 0.0196)
- **Best holdout score**: 0.0133 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0857 | 0.0125 | 2.17 | 1.00 | 307 |
| 1 | 0.0153 | 0.0133 | 6.57 | 4.60 | 361 |
| 2 | 0.0153 | 0.0008 | 2.37 | 2.20 | 543 |
| 3 | 0.0142 | -0.0418 | -0.39 | 4.26 | 506 |
| 4 | 0.0135 | -0.0324 | 0.54 | 4.22 | 353 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51985
- **Expected rows**: 51985
- **Missing rows**: 0
- **Forward-fill count**: 10
- **Forward-fill fraction**: 0.0001923631816870251
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.0059604600012060525
- **PnL %**: 0.7223839775481409
- **Trade count**: 88

## Sensitivity Analysis

- **Sensitivity penalty**: 0.7857142857142857
- **Baseline score**: -0.001989205645238027
- **Sign flips**: 3
- **Collapse count**: 8
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0015, 0.0061 |
| sell_spread_base | -0.0014, -0.0090 |
| stop_loss | 0.0054, -0.0054 |
| take_profit | -0.0020, -0.0020 |
| executor_refresh_time | -0.0131, -0.0231 |
| cooldown_time | -0.0122, -0.0193 |
| total_amount_quote | -0.0087, -0.0087 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.34089664061152664
- **Max CV**: 0.9906551885048662
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2134 | 0.23319494699294316 | 0.4504024631091557 | 0.31232206754506514 |
| buy_spread_ratio | 0.0942 | 1.2118337590545631 | 1.646683385561457 | 1.3767017071857532 |
| sell_spread_base | 0.8320 | 0.22686525637520275 | 5.39206733212132 | 2.1478511353561607 |
| sell_spread_ratio | 0.2037 | 1.5512046382130944 | 2.7724436186067174 | 1.971052100383411 |
| buy_side_weight | 0.1697 | 0.4618254411790183 | 0.7873907946581713 | 0.6532228059585174 |
| amount_skew | 0.2237 | 1.0683492310764513 | 2.2883843652647933 | 1.6418766456770293 |
| stop_loss | 0.1035 | 0.010235030218168644 | 0.015118346903636821 | 0.012930843790980421 |
| take_profit | 0.9907 | 0.0055294182566901235 | 0.06190160619258273 | 0.016677098742191754 |
| executor_refresh_time | 0.2961 | 5540.0 | 11976.0 | 8365.2 |
| cooldown_time | 0.2549 | 2455.0 | 6394.0 | 4127.4 |
| total_amount_quote | 0.3682 | 242.95633281986608 | 959.4549596837292 | 606.2750982565303 |

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
- sensitivity_stable: **FAIL**
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.0059604600012060525 | PASS |
| recent_pnl | >= 0 | 0.7223839775481409 | PASS |
| recent_trades | >= 5 | 88 | PASS |
| worst_stress | > -10 | -0.1429288657871441 | PASS |
| sensitivity_penalty | < 0.50 | 0.7857142857142857 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0125 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.1429288657871441 |
| sensitivity | FAIL | penalty=0.7857142857142857 |
| recent_28d | PASS | score=0.0059604600012060525, pnl=0.7223839775481409, trades=88, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.34089664061152664 |

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
- **run_timestamp**: 2026-03-28T22:54:23.056060+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 1492
