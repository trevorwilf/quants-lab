# PMM Dynamic Optimization Report: mexc_WXT-USDT_5m_sweep_v1

Generated: 2026-03-28 23:39:38 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T23:39:38.585692+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 7901 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: WXT-USDT
- **interval**: 5m
- **n_candles**: 52043
- **dataset_hash**: ae2d428a4b97a58b33090075954ed249f1b0e3bd83d1130902ebf9bab3bc2187
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 623.4359346305696
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.1094669462699422 |
| buy_n_levels | 8 |
| buy_side_weight | 0.2541869961592841 |
| buy_spread_base | 0.36804147408833143 |
| buy_spread_ratio | 1.3475567475737245 |
| cooldown_time | 6262 |
| executor_refresh_time | 2877 |
| macd_fast | 13 |
| macd_signal | 22 |
| macd_slow | 52 |
| natr_length | 32 |
| sell_n_levels | 6 |
| sell_spread_base | 0.3078900802469352 |
| sell_spread_ratio | 1.3296431113884635 |
| stop_loss | 0.055605934964316234 |
| take_profit | 0.026360860752850337 |
| time_limit | 29565 |
| total_amount_quote | 623.4359346305696 |
| trailing_stop_activation | 0.07589046971867158 |
| trailing_stop_delta | 0.04443015899543865 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 623.4359346305696 |
| Selected | 623.4359346305696 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.5876
- **Net PnL (quote)**: -3.6636
- **Sharpe Ratio**: -0.4907
- **Max Drawdown %**: 1.9834
- **Profit Factor**: 1.0165972582401985
- **Trade Count**: 100
- **Total Fees (quote)**: 1.2851
- **Maker Fees**: 0.7769
- **Taker Fees**: 0.5082
- **Fee Drag %**: 0.2061

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0268
- **PnL Component**: -0.0059
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0149
- **Fee Drag Component**: -0.0010
- **Inventory Component**: -0.0048
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1584**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.03 | 0.23 | 0.63 | 9 | -0.1686 | n/a |
| 1 | -0.29 | -4.25 | 0.42 | 4 | -0.4225 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | -0.28 | -0.99 | 1.71 | 73 | -0.0846 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | -0.06 | -0.06 | 2.27 | 84 | -0.1064 | n/a |
| 7 | -1.79 | -5.04 | 2.79 | 94 | -0.1709 | n/a |
| 8 | 0.10 | 0.70 | 0.60 | 38 | -0.1159 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1318)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.69 | -0.58 | 1.99 | -0.0284 |
| fees_2x | -0.79 | -0.67 | 2.00 | -0.0300 |
| latency_plus1 | -0.62 | -0.52 | 2.02 | -0.0274 |
| latency_plus2 | -0.46 | -0.40 | 1.71 | -0.0186 |
| latency_plus3 | -0.10 | -0.07 | 1.70 | -0.0150 |
| low_liquidity | -0.59 | -0.50 | 1.98 | -0.0268 |
| very_low_liquidity | -3.00 | -1.88 | 4.82 | -0.1188 |
| high_slippage | -0.79 | -0.66 | 2.02 | -0.0291 |
| extreme_slippage | -1.20 | -1.01 | 2.08 | -0.0337 |
| combined_adverse | -0.93 | -0.78 | 2.06 | -0.0313 |
| spread_widen_10bps | -0.77 | -0.65 | 1.98 | -0.0286 |
| spread_widen_25bps | -1.04 | -0.89 | 1.99 | -0.0314 |
| thin_book | -3.90 | -2.26 | 4.68 | -0.1171 |
| very_thin_book | -1.09 | -0.94 | 2.64 | -0.0473 |
| entry_spread_stress | -0.86 | -0.73 | 1.99 | -0.0296 |
| combined_market_deterioration | -3.12 | -1.95 | 4.88 | -0.1142 |
| severe_adverse | -4.39 | -2.63 | 5.12 | -0.1318 |

## Holdout Validation

- **Holdout bars**: 8795
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0025)
- **Trend**: ranging (efficiency: 0.0251)
- **Best holdout score**: -0.1495 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0793 | -0.1495 | -1.84 | 4.03 | 184 |
| 1 | -0.1638 | -0.1564 | -1.69 | 3.53 | 181 |
| 2 | -0.1639 | -0.3019 | -4.95 | 8.12 | 202 |
| 3 | -0.1664 | -0.2064 | -3.38 | 4.70 | 209 |
| 4 | -0.1687 | -0.2842 | -4.63 | 5.59 | 162 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52043
- **Expected rows**: 52043
- **Missing rows**: 0
- **Forward-fill count**: 618
- **Forward-fill fraction**: 0.011874795841899967
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0722 <= 0; recent PnL -0.1679% < 0
- **Objective score**: -0.07224011218746038
- **PnL %**: -0.16792206763779885
- **Trade count**: 56

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: -0.13808813827864402
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.2046, -0.1301 |
| sell_spread_base | -0.1584, -0.3705 |
| stop_loss | -0.1430, -0.1301 |
| take_profit | -0.1398, -0.1471 |
| executor_refresh_time | -0.1337, -0.2194 |
| cooldown_time | -0.0885, -0.0963 |
| total_amount_quote | -0.2719, -0.1379 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.31610062434168423
- **Max CV**: 0.8547595903849915
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, cooldown_time, total_amount_quote
- **Scattered params**: stop_loss, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1295 | 0.20322247135929192 | 0.30289763466895664 | 0.2671353236953654 |
| buy_spread_ratio | 0.0938 | 1.2187449262901366 | 1.5583266753508096 | 1.3763900532899682 |
| sell_spread_base | 0.2809 | 0.21477584219675186 | 0.46028579385054774 | 0.2948971726878509 |
| sell_spread_ratio | 0.2091 | 1.2212184895717995 | 2.303071851924939 | 1.5837532070938225 |
| buy_side_weight | 0.2248 | 0.23777576983030466 | 0.4437027459034932 | 0.3149631144909958 |
| amount_skew | 0.1752 | 1.7994925022143997 | 3.1442160781905613 | 2.521263036813969 |
| stop_loss | 0.6960 | 0.024093947174480677 | 0.15000134685194647 | 0.06402152207586252 |
| take_profit | 0.2430 | 0.005953063686253461 | 0.011651558674308416 | 0.00894889653355721 |
| executor_refresh_time | 0.8548 | 307.0 | 4159.0 | 1425.7 |
| cooldown_time | 0.3718 | 1551.0 | 7103.0 | 4377.8 |
| total_amount_quote | 0.1982 | 441.12884516606937 | 997.1794226748758 | 790.0692539572387 |

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
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.07224011218746038 | FAIL |
| recent_pnl | >= 0 | -0.16792206763779885 | FAIL |
| recent_trades | >= 5 | 56 | PASS |
| worst_stress | > -10 | -0.13183823464515912 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.1494850922405704 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.13183823464515912 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | FAIL | score=-0.07224011218746038, pnl=-0.16792206763779885, trades=56, reason=recent objective score -0.0722 <= 0; recent PnL -0.1679% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.31610062434168423 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52043 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0722 <= 0; recent PnL -0.1679% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35183
- **Holdout bars**: 8795
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T23:39:38.585692+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 7901
