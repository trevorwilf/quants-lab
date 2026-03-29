# PMM Dynamic Optimization Report: mexc_ASTER-USDT_5m_sweep_v1

Generated: 2026-03-28 07:14:53 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T07:14:53.824439+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 10248 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ASTER-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 6020868258067063e19cdd378503b6fe6fd198772a00b184cb82afc1b89be38c
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 778.4137681789434
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.211940302311444 |
| buy_n_levels | 7 |
| buy_side_weight | 0.5937851515802728 |
| buy_spread_base | 2.472443690933231 |
| buy_spread_ratio | 1.6762967398650248 |
| cooldown_time | 1002 |
| executor_refresh_time | 4896 |
| macd_fast | 14 |
| macd_signal | 25 |
| macd_slow | 94 |
| natr_length | 34 |
| sell_n_levels | 5 |
| sell_spread_base | 3.126156377858542 |
| sell_spread_ratio | 1.5605442073967009 |
| stop_loss | 0.014274042919487955 |
| take_profit | 0.07491450680761604 |
| time_limit | 49722 |
| total_amount_quote | 778.4137681789434 |
| trailing_stop_activation | 0.0007664890164397871 |
| trailing_stop_delta | 0.0011815194112931014 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 778.4137681789434 |
| Selected | 778.4137681789434 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 7.0464
- **Net PnL (quote)**: 54.8503
- **Sharpe Ratio**: 2.6690
- **Max Drawdown %**: 2.7877
- **Profit Factor**: 2.0834463145043403
- **Trade Count**: 742
- **Total Fees (quote)**: 7.0041
- **Maker Fees**: 3.4959
- **Taker Fees**: 3.5083
- **Fee Drag %**: 0.8998

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0426
- **PnL Component**: 0.0681
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0209
- **Fee Drag Component**: -0.0045
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.0003**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 1.02 | 8.95 | 0.08 | 99 | 0.0090 | n/a |
| 1 | 0.96 | 3.66 | 0.75 | 100 | 0.0030 | n/a |
| 2 | 0.48 | 6.55 | 0.29 | 84 | 0.0021 | n/a |
| 3 | 0.69 | 6.13 | 0.04 | 52 | 0.0063 | n/a |
| 4 | -0.17 | -0.12 | 2.99 | 56 | -0.0246 | n/a |
| 5 | 1.16 | 10.67 | 0.10 | 64 | 0.0104 | n/a |
| 6 | 0.16 | 1.75 | 0.49 | 54 | -0.0024 | n/a |
| 7 | 0.55 | 8.12 | 0.20 | 58 | 0.0036 | n/a |
| 8 | 0.06 | 2.37 | 0.06 | 39 | -0.0981 | n/a |

## Stress Test Results

Worst Scenario: **very_thin_book** (score: -0.0614)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 6.60 | 2.50 | 2.81 | 0.0360 |
| fees_2x | 6.15 | 2.33 | 2.82 | 0.0294 |
| latency_plus1 | 7.07 | 2.68 | 2.79 | 0.0429 |
| latency_plus2 | 6.99 | 2.65 | 2.79 | 0.0421 |
| latency_plus3 | 6.43 | 2.43 | 2.80 | 0.0368 |
| low_liquidity | 7.05 | 2.67 | 2.79 | 0.0426 |
| very_low_liquidity | 7.05 | 2.67 | 2.79 | 0.0426 |
| high_slippage | 5.92 | 2.25 | 2.83 | 0.0317 |
| extreme_slippage | 3.67 | 1.42 | 2.91 | 0.0096 |
| combined_adverse | 5.50 | 2.09 | 2.84 | 0.0254 |
| spread_widen_10bps | 3.44 | 1.34 | 3.10 | 0.0061 |
| spread_widen_25bps | 2.21 | 0.87 | 3.16 | -0.0063 |
| thin_book | -0.79 | -0.76 | 1.22 | -0.0201 |
| very_thin_book | -2.57 | -1.60 | 3.57 | -0.0614 |
| entry_spread_stress | 3.52 | 1.35 | 3.11 | 0.0069 |
| combined_market_deterioration | 1.37 | 1.23 | 1.19 | -0.0009 |
| severe_adverse | 2.83 | 0.65 | 6.70 | -0.0466 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0047)
- **Trend**: ranging (efficiency: 0.0022)
- **Best holdout score**: 0.0080 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0094 | 0.0080 | 1.26 | 0.49 | 134 |
| 1 | 0.0074 | -0.0422 | -0.89 | 3.00 | 156 |
| 2 | 0.0069 | -0.0078 | 0.78 | 1.79 | 150 |
| 3 | 0.0061 | -0.0098 | 0.59 | 1.75 | 149 |
| 4 | 0.0056 | 0.0047 | 2.02 | 1.11 | 294 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 3
- **Forward-fill fraction**: 5.7869254065315096e-05
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.007142424984771163
- **PnL %**: 1.4781051514441859
- **Trade count**: 106

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: 0.06845611863851356
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0579, 0.0690 |
| sell_spread_base | 0.0685, 0.0685 |
| stop_loss | 0.0640, 0.0655 |
| take_profit | 0.0685, 0.0685 |
| executor_refresh_time | 0.0786, 0.1299 |
| cooldown_time | 0.0685, 0.0685 |
| total_amount_quote | 0.0144, 0.0685 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2808711900297739
- **Max CV**: 0.8323558948195354
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2521 | 1.2660735170900062 | 3.308604663130787 | 2.2852509149642115 |
| buy_spread_ratio | 0.1084 | 1.3779478528128424 | 1.9868368317051535 | 1.6082470682324093 |
| sell_spread_base | 0.8324 | 0.27918364028995857 | 4.049858953913441 | 1.4110371279884542 |
| sell_spread_ratio | 0.1203 | 1.2461320353449112 | 1.731693761260781 | 1.4703683190116703 |
| buy_side_weight | 0.0903 | 0.514370936830207 | 0.6696285362603586 | 0.6064219013835197 |
| amount_skew | 0.2092 | 1.9684970267701387 | 3.7210751124443524 | 2.807771811077759 |
| stop_loss | 0.4238 | 0.010381719755247319 | 0.03240589709696666 | 0.015145141497407782 |
| take_profit | 0.4657 | 0.028294275775146913 | 0.14549293934207014 | 0.08801738471256855 |
| executor_refresh_time | 0.1830 | 6677.0 | 11023.0 | 8521.8 |
| cooldown_time | 0.1986 | 2245.0 | 4973.0 | 3865.3 |
| total_amount_quote | 0.2058 | 465.5241515881157 | 869.1729831267678 | 664.1027937651429 |

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
| recent_objective | > 0 | 0.007142424984771163 | PASS |
| recent_pnl | >= 0 | 1.4781051514441859 | PASS |
| recent_trades | >= 5 | 106 | PASS |
| worst_stress | > -10 | -0.06136225614239839 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0080 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_thin_book score=-0.06136225614239839 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | PASS | score=0.007142424984771163, pnl=1.4781051514441859, trades=106, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2808711900297739 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
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
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T07:14:53.824439+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 10248
