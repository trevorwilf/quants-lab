# PMM Dynamic Optimization Report: mexc_DOT-USDT_5m_sweep_v1

Generated: 2026-03-28 11:36:54 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T11:36:54.100166+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 9274 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOT-USDT
- **interval**: 5m
- **n_candles**: 51913
- **dataset_hash**: d69cc4623be7cf554bfc439f4013fabf160abb6950860ce5489354fbba4d1153
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 969.8142724414664
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.036771073396402 |
| buy_n_levels | 8 |
| buy_side_weight | 0.23136934985316143 |
| buy_spread_base | 2.604999501165396 |
| buy_spread_ratio | 1.8586952684657734 |
| cooldown_time | 2651 |
| executor_refresh_time | 7656 |
| macd_fast | 23 |
| macd_signal | 18 |
| macd_slow | 41 |
| natr_length | 22 |
| sell_n_levels | 5 |
| sell_spread_base | 2.995963783560626 |
| sell_spread_ratio | 1.8677041702479151 |
| stop_loss | 0.012479407977018171 |
| take_profit | 0.04256028365987668 |
| time_limit | 154298 |
| total_amount_quote | 969.8142724414664 |
| trailing_stop_activation | 0.0024007110790336228 |
| trailing_stop_delta | 0.001221246760190604 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 969.8142724414664 |
| Selected | 969.8142724414664 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 0.3441
- **Net PnL (quote)**: 3.3372
- **Sharpe Ratio**: 0.6040
- **Max Drawdown %**: 0.8276
- **Profit Factor**: 1.1233231401447552
- **Trade Count**: 647
- **Total Fees (quote)**: 3.5782
- **Maker Fees**: 1.7884
- **Taker Fees**: 1.7898
- **Fee Drag %**: 0.3690

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0060
- **PnL Component**: 0.0034
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0062
- **Fee Drag Component**: -0.0018
- **Inventory Component**: -0.0014
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0045**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.10 | -1.93 | 0.30 | 93 | -0.0049 | n/a |
| 1 | -0.31 | -4.52 | 0.39 | 80 | -0.0077 | n/a |
| 2 | 0.26 | 6.64 | 0.13 | 58 | -0.0000 | n/a |
| 3 | 0.10 | 3.14 | 0.18 | 49 | -0.0059 | n/a |
| 4 | 0.03 | 0.52 | 0.22 | 70 | -0.0030 | n/a |
| 5 | 0.15 | 3.92 | 0.14 | 78 | -0.0013 | n/a |
| 6 | 0.15 | 5.56 | 0.11 | 63 | 0.0005 | n/a |
| 7 | -0.20 | -2.35 | 0.41 | 63 | -0.0066 | n/a |
| 8 | 0.05 | 5.77 | 0.04 | 50 | -0.0013 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0912)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 0.16 | 0.28 | 0.84 | -0.0089 |
| fees_2x | -0.02 | -0.03 | 0.85 | -0.0118 |
| latency_plus1 | 0.34 | 0.60 | 0.83 | -0.0061 |
| latency_plus2 | 0.43 | 0.74 | 0.83 | -0.0053 |
| latency_plus3 | 0.47 | 0.82 | 0.75 | -0.0043 |
| low_liquidity | 0.34 | 0.60 | 0.83 | -0.0060 |
| very_low_liquidity | 0.34 | 0.60 | 0.83 | -0.0060 |
| high_slippage | -0.12 | -0.20 | 0.86 | -0.0109 |
| extreme_slippage | -1.04 | -1.84 | 1.06 | -0.0253 |
| combined_adverse | -0.31 | -0.53 | 0.87 | -0.0138 |
| spread_widen_10bps | -0.32 | -0.57 | 0.68 | -0.0116 |
| spread_widen_25bps | -1.21 | -1.89 | 1.25 | -0.0266 |
| thin_book | -2.29 | -1.54 | 2.35 | -0.0439 |
| very_thin_book | -2.08 | -2.15 | 2.10 | -0.0392 |
| entry_spread_stress | -0.60 | -1.07 | 0.66 | -0.0143 |
| combined_market_deterioration | -2.05 | -0.43 | 5.29 | -0.0643 |
| severe_adverse | -3.74 | -1.30 | 4.43 | -0.0912 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0044)
- **Trend**: ranging (efficiency: 0.0157)
- **Best holdout score**: 0.0068 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0486 | -0.0040 | 0.09 | 0.41 | 157 |
| 1 | 0.0012 | 0.0068 | 1.34 | 0.59 | 178 |
| 2 | 0.0007 | 0.0047 | 1.21 | 0.67 | 190 |
| 3 | 0.0004 | 0.0017 | 0.44 | 0.26 | 176 |
| 4 | -0.0001 | 0.0007 | 0.26 | 0.18 | 149 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51913
- **Expected rows**: 51913
- **Missing rows**: 0
- **Forward-fill count**: 1
- **Forward-fill fraction**: 1.926299770770327e-05
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0000 <= 0
- **Objective score**: -4.419357471759067e-05
- **PnL %**: 0.204886780280133
- **Trade count**: 108

## Sensitivity Analysis

- **Sensitivity penalty**: 0.35714285714285715
- **Baseline score**: -0.0036818123538433743
- **Sign flips**: 2
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0041, -0.0075 |
| sell_spread_base | -0.0037, -0.0029 |
| stop_loss | -0.0061, -0.0020 |
| take_profit | -0.0037, -0.0037 |
| executor_refresh_time | 0.0075, 0.0017 |
| cooldown_time | -0.0037, -0.0044 |
| total_amount_quote | -0.0040, -0.0087 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4099457288313042
- **Max CV**: 0.8619191708619267
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2569 | 1.0984034771014122 | 3.4034937687557774 | 2.3293687820650266 |
| buy_spread_ratio | 0.1935 | 1.3310423332783545 | 2.6774769785343233 | 2.0895447963644314 |
| sell_spread_base | 0.7757 | 0.36206456203757015 | 3.1186278611944704 | 1.107340556667086 |
| sell_spread_ratio | 0.2413 | 1.4606015369077627 | 2.976738983658122 | 2.350045561376392 |
| buy_side_weight | 0.2874 | 0.2304979090884267 | 0.6548697751110508 | 0.442222859180081 |
| amount_skew | 0.3023 | 1.3603820845065702 | 3.7197780247371393 | 2.469415246601036 |
| stop_loss | 0.4367 | 0.010188013046779965 | 0.028639061530315996 | 0.01609481082316818 |
| take_profit | 0.8619 | 0.007262545973301441 | 0.12574878567710188 | 0.04765578929263483 |
| executor_refresh_time | 0.4024 | 4475.0 | 12574.0 | 7810.7 |
| cooldown_time | 0.4564 | 626.0 | 6790.0 | 4105.4 |
| total_amount_quote | 0.2948 | 296.97311192835053 | 994.5689578050019 | 700.6902959641859 |

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
| recent_objective | > 0 | -4.419357471759067e-05 | FAIL |
| recent_pnl | >= 0 | 0.204886780280133 | PASS |
| recent_trades | >= 5 | 108 | PASS |
| worst_stress | > -10 | -0.09118497177337967 | PASS |
| sensitivity_penalty | < 0.50 | 0.35714285714285715 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.004021462060218037 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.09118497177337967 |
| sensitivity | PASS | penalty=0.35714285714285715 |
| recent_28d | FAIL | score=-4.419357471759067e-05, pnl=0.204886780280133, trades=108, reason=recent objective score -0.0000 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4099457288313042 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51913 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0000 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35079
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T11:36:54.100166+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 9274
