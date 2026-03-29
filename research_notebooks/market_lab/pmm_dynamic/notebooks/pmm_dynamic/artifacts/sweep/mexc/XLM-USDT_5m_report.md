# PMM Dynamic Optimization Report: mexc_XLM-USDT_5m_sweep_v1

Generated: 2026-03-29 00:23:23 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T00:23:23.619682+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 3050 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XLM-USDT
- **interval**: 5m
- **n_candles**: 52057
- **dataset_hash**: 4b8e2aab5c78808d1c97c91624d98e7ba341649f0f1f878ad3410b961fb0f61b
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 799.5363577498676
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.3156281751490282 |
| buy_n_levels | 8 |
| buy_side_weight | 0.22517585102441642 |
| buy_spread_base | 0.24951519019150437 |
| buy_spread_ratio | 1.7029924416446731 |
| cooldown_time | 6626 |
| executor_refresh_time | 3052 |
| macd_fast | 22 |
| macd_signal | 15 |
| macd_slow | 24 |
| natr_length | 30 |
| sell_n_levels | 8 |
| sell_spread_base | 4.699343568831401 |
| sell_spread_ratio | 1.9877249716822198 |
| stop_loss | 0.042384672375718996 |
| take_profit | 0.02556530528616568 |
| time_limit | 133552 |
| total_amount_quote | 799.5363577498676 |
| trailing_stop_activation | 0.00023318753905324474 |
| trailing_stop_delta | 0.0010897093553319502 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 799.5363577498676 |
| Selected | 799.5363577498676 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2.1532
- **Net PnL (quote)**: 17.2158
- **Sharpe Ratio**: 3.2082
- **Max Drawdown %**: 0.8004
- **Profit Factor**: 2.2823401915262536
- **Trade Count**: 1311
- **Total Fees (quote)**: 7.0030
- **Maker Fees**: 3.4991
- **Taker Fees**: 3.5039
- **Fee Drag %**: 0.8759

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0109
- **PnL Component**: 0.0213
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0060
- **Fee Drag Component**: -0.0044
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0068**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.68 | 7.65 | 0.23 | 233 | 0.0042 | n/a |
| 1 | 0.02 | 0.51 | 0.24 | 114 | -0.0184 | n/a |
| 2 | 0.63 | 6.47 | 0.17 | 118 | 0.0046 | n/a |
| 3 | 0.08 | 3.53 | 0.09 | 93 | -0.0002 | n/a |
| 4 | 0.30 | 12.51 | 0.03 | 134 | 0.0024 | n/a |
| 5 | -0.05 | -0.65 | 0.36 | 111 | -0.0037 | n/a |
| 6 | 0.69 | 7.64 | 0.18 | 119 | -0.0037 | n/a |
| 7 | 0.42 | 6.26 | 0.17 | 96 | -0.0100 | n/a |
| 8 | 0.08 | 7.62 | 0.03 | 80 | -0.0138 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.2406)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 1.72 | 2.56 | 0.84 | 0.0041 |
| fees_2x | 1.28 | 1.91 | 0.90 | -0.0169 |
| latency_plus1 | 1.68 | 2.46 | 0.80 | 0.0063 |
| latency_plus2 | 0.62 | 0.82 | 1.37 | -0.0134 |
| latency_plus3 | 0.61 | 0.85 | 1.01 | -0.0079 |
| low_liquidity | 2.15 | 3.21 | 0.80 | 0.0109 |
| very_low_liquidity | 2.16 | 3.22 | 0.80 | 0.0110 |
| high_slippage | 1.06 | 1.60 | 0.92 | -0.0252 |
| extreme_slippage | -1.13 | -1.71 | 1.50 | -0.1355 |
| combined_adverse | 0.17 | 0.26 | 1.03 | -0.0592 |
| spread_widen_10bps | 0.59 | 0.85 | 0.91 | -0.0157 |
| spread_widen_25bps | -4.21 | -2.59 | 4.24 | -0.1312 |
| thin_book | -2.12 | -1.82 | 2.37 | -0.0609 |
| very_thin_book | -5.15 | -3.54 | 5.52 | -0.1278 |
| entry_spread_stress | -0.36 | -0.46 | 1.51 | -0.0431 |
| combined_market_deterioration | -2.72 | -1.89 | 2.83 | -0.1147 |
| severe_adverse | -8.61 | -7.25 | 8.61 | -0.2406 |

## Holdout Validation

- **Holdout bars**: 8798
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0038)
- **Trend**: ranging (efficiency: 0.0177)
- **Best holdout score**: 0.0048 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1149 | 0.0048 | 0.90 | 0.44 | 258 |
| 1 | 0.0094 | -0.0288 | 2.07 | 5.56 | 111 |
| 2 | 0.0094 | -0.0985 | 10.93 | 4.32 | 211 |
| 3 | 0.0068 | -0.2635 | -0.76 | 7.93 | 199 |
| 4 | 0.0055 | -0.2639 | -0.51 | 11.12 | 269 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52057
- **Expected rows**: 52057
- **Missing rows**: 0
- **Forward-fill count**: 4
- **Forward-fill fraction**: 7.683884972241965e-05
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0089 <= 0
- **Objective score**: -0.008867341523939679
- **PnL %**: 0.22589734056921812
- **Trade count**: 137

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: 0.020643689002423242
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0238, 0.0197 |
| sell_spread_base | 0.0206, 0.0206 |
| stop_loss | 0.0185, 0.0202 |
| take_profit | 0.0206, 0.0206 |
| executor_refresh_time | 0.0164, 0.0131 |
| cooldown_time | 0.0070, 0.0224 |
| total_amount_quote | 0.0214, 0.0191 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4142715932714998
- **Max CV**: 1.2522405183931864
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: stop_loss, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3007 | 0.20364075906388088 | 0.5177035522427588 | 0.3355717260180373 |
| buy_spread_ratio | 0.2667 | 1.2139889215844264 | 2.4578953687271583 | 1.7916715146391944 |
| sell_spread_base | 0.4900 | 0.5744155898844759 | 2.5035012809538726 | 1.3647276114847608 |
| sell_spread_ratio | 0.1625 | 1.318204837377862 | 2.1560928270439916 | 1.6369199159530983 |
| buy_side_weight | 0.1804 | 0.4440309699537772 | 0.7582952654971844 | 0.6243322912678237 |
| amount_skew | 0.2815 | 1.1076912408367556 | 3.7041100765150983 | 2.5851922726426966 |
| stop_loss | 0.7018 | 0.018847630500580477 | 0.20331789197683592 | 0.08376292527303221 |
| take_profit | 1.2522 | 0.00563913646045074 | 0.10088166278714279 | 0.029674956165474102 |
| executor_refresh_time | 0.3191 | 4607.0 | 13061.0 | 7993.9 |
| cooldown_time | 0.4359 | 2084.0 | 7068.0 | 4258.2 |
| total_amount_quote | 0.1661 | 497.4160271705684 | 965.278127752921 | 797.643504003242 |

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
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.008867341523939679 | FAIL |
| recent_pnl | >= 0 | 0.22589734056921812 | PASS |
| recent_trades | >= 5 | 137 | PASS |
| worst_stress | > -10 | -0.24058100733757581 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0048 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.24058100733757581 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.008867341523939679, pnl=0.22589734056921812, trades=137, reason=recent objective score -0.0089 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4142715932714998 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52057 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0089 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35194
- **Holdout bars**: 8798
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T00:23:23.619682+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 3050
