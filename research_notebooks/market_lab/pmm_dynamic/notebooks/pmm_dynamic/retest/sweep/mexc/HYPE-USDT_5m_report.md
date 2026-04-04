# PMM Dynamic Optimization Report: mexc_HYPE-USDT_5m_retest_20260403

Generated: 2026-04-04 02:04:49 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-04T02:04:49.440304+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 3486 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: HYPE-USDT
- **interval**: 5m
- **n_candles**: 51860
- **dataset_hash**: 5bb3f2862f1cc28e5a729b97b57a9eb025092c542fac7b9f248f0ceb5d81abe5
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 574.1260541210901
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.6527485598219083 |
| buy_n_levels | 2 |
| buy_side_weight | 0.45380277074202774 |
| buy_spread_base | 0.33857387698388935 |
| buy_spread_ratio | 1.7479871236833677 |
| cooldown_time | 326 |
| executor_refresh_time | 1492 |
| macd_fast | 6 |
| macd_signal | 19 |
| macd_slow | 20 |
| natr_length | 42 |
| sell_n_levels | 2 |
| sell_spread_base | 0.30126662421720024 |
| sell_spread_ratio | 1.2310697645533173 |
| stop_loss | 0.1585213415975264 |
| take_profit | 0.04888983026257034 |
| time_limit | 164835 |
| total_amount_quote | 574.1260541210901 |
| trailing_stop_activation | 0.022767222839815065 |
| trailing_stop_delta | 0.0012775591790540222 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 574.1260541210901 |
| Selected | 574.1260541210901 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3546.9785
- **Net PnL (quote)**: 20364.1279
- **Sharpe Ratio**: 9.8599
- **Max Drawdown %**: 19.9582
- **Profit Factor**: 1.6150011009912884
- **Trade Count**: 16099
- **Total Fees (quote)**: 768.0296
- **Maker Fees**: 388.4794
- **Taker Fees**: 379.5502
- **Fee Drag %**: 133.7737

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.5203
- **PnL Component**: 3.5965
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1497
- **Fee Drag Component**: -0.6689
- **Inventory Component**: -0.2500
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **1.0288**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 349.98 | 26.00 | 9.27 | 1592 | 1.1129 | n/a |
| 1 | 436.88 | 42.02 | 5.82 | 1581 | 1.3192 | n/a |
| 2 | 286.66 | 32.85 | 6.70 | 1490 | 0.9873 | n/a |
| 3 | 288.66 | 44.10 | 6.80 | 1635 | 0.9881 | n/a |
| 4 | 333.53 | 36.39 | 8.83 | 1556 | 1.0844 | n/a |
| 5 | 652.16 | 31.91 | 13.22 | 1655 | 1.5907 | n/a |
| 6 | 236.95 | 39.03 | 6.91 | 1633 | 0.8453 | n/a |
| 7 | 419.29 | 47.26 | 4.31 | 1589 | 1.2964 | n/a |
| 8 | 277.83 | 42.02 | 5.77 | 1478 | 0.9731 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.7485)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3545.56 | 9.86 | 19.96 | 2.1904 |
| fees_2x | 3503.44 | 9.77 | 19.90 | 1.8500 |
| latency_plus1 | 3204.38 | 9.51 | 19.95 | 2.4834 |
| latency_plus2 | 2775.83 | 9.20 | 20.75 | 2.4141 |
| latency_plus3 | 2231.95 | 8.52 | 20.18 | 2.2882 |
| low_liquidity | 3481.88 | 9.87 | 19.61 | 2.5170 |
| very_low_liquidity | 3469.86 | 9.93 | 19.28 | 2.5303 |
| high_slippage | 3567.41 | 9.89 | 19.95 | 2.5292 |
| extreme_slippage | 3399.76 | 9.68 | 20.08 | 2.4955 |
| combined_adverse | 2995.81 | 9.35 | 19.52 | 2.1388 |
| spread_widen_10bps | 3403.14 | 9.60 | 19.88 | 2.4811 |
| spread_widen_25bps | 3362.70 | 9.52 | 19.85 | 2.4808 |
| thin_book | 2352.71 | 8.78 | 21.38 | 2.3630 |
| very_thin_book | 1257.42 | 7.36 | 22.48 | 1.9821 |
| entry_spread_stress | 3481.16 | 9.63 | 20.00 | 2.5082 |
| combined_market_deterioration | 2944.58 | 9.28 | 20.60 | 2.2202 |
| severe_adverse | 1282.20 | 7.21 | 20.26 | 1.7485 |

## Holdout Validation

- **Holdout bars**: 8760
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0049)
- **Trend**: ranging (efficiency: 0.0031)
- **Best holdout score**: 2.1755 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 2.1344 | 1.8452 | 914.72 | 9.07 | 3747 |
| 1 | 1.4632 | 2.1381 | 1448.49 | 8.61 | 2923 |
| 2 | 1.4268 | 2.1745 | 1535.41 | 11.44 | 3144 |
| 3 | 1.4047 | 2.1648 | 1414.51 | 9.06 | 4949 |
| 4 | 1.3623 | 2.1755 | 1459.98 | 10.44 | 6573 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51860
- **Expected rows**: 51868
- **Missing rows**: 8
- **Forward-fill count**: 177
- **Forward-fill fraction**: 0.0034130350944851524
- **Longest gap (seconds)**: 2700

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.3515777238687487
- **PnL %**: 494.1646384888881
- **Trade count**: 3326

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 2.3784117073295983
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 2.3634, 2.3870 |
| sell_spread_base | 2.3804, 2.3901 |
| stop_loss | 2.3866, 2.4107 |
| take_profit | 2.3784, 2.3784 |
| executor_refresh_time | 2.3713, 2.3784 |
| cooldown_time | 2.3784, 2.3795 |
| total_amount_quote | 2.3999, 2.3927 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3805054601776398
- **Max CV**: 0.9093919126001012
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time
- **Scattered params**: take_profit, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3542 | 0.20511687380756752 | 0.5424598453743235 | 0.2838800337509143 |
| buy_spread_ratio | 0.3278 | 1.2402447466415492 | 2.682333014040456 | 1.7828921498387618 |
| sell_spread_base | 0.3691 | 0.20289354963953285 | 0.6123044038565701 | 0.3207472574381166 |
| sell_spread_ratio | 0.3044 | 1.2148370233465366 | 2.779143150525123 | 1.8989580760271 |
| buy_side_weight | 0.1604 | 0.36942933270357076 | 0.5676062204682439 | 0.4587045395476773 |
| amount_skew | 0.1743 | 1.958194043401974 | 3.9161850425675415 | 3.0294077149637832 |
| stop_loss | 0.2765 | 0.11820395549717959 | 0.248297962085849 | 0.17224055398267835 |
| take_profit | 0.6571 | 0.02446328360924917 | 0.14493062676805163 | 0.057205948964933806 |
| executor_refresh_time | 0.3534 | 303.0 | 816.0 | 445.0 |
| cooldown_time | 0.2990 | 132.0 | 284.0 | 181.0 |
| total_amount_quote | 0.9094 | 31.52988249445057 | 831.422485666275 | 410.74500228869545 |

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
| recent_objective | > 0 | 1.3515777238687487 | PASS |
| recent_pnl | >= 0 | 494.1646384888881 | PASS |
| recent_trades | >= 5 | 3326 | PASS |
| worst_stress | > -10 | 1.7485194994703177 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.8452 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.7485194994703177 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.3515777238687487, pnl=494.1646384888881, trades=3326, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3805054601776398 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51860 |  |
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
- **Dev bars**: 35043
- **Holdout bars**: 8760
- **Recent 28d bars**: 8057

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-04T02:04:49.440304+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 3486
