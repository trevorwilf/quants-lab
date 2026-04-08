# PMM Dynamic Optimization Report: mexc_HYPE-USDT_5m_retest_20260408

Generated: 2026-04-08 04:57:29 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T04:57:29.326915+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 9847 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: HYPE-USDT
- **interval**: 5m
- **n_candles**: 51838
- **dataset_hash**: ceacadf7657c051b418fc94d1a1f3e57590efb77c455175150d14b645d2dcd29
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 66.46856635146756
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.552159561033414 |
| buy_n_levels | 5 |
| buy_side_weight | 0.4789009457707269 |
| buy_spread_base | 0.39456422619595777 |
| buy_spread_ratio | 1.9461556187020845 |
| cooldown_time | 185 |
| executor_refresh_time | 1019 |
| macd_fast | 14 |
| macd_signal | 11 |
| macd_slow | 26 |
| natr_length | 33 |
| sell_n_levels | 4 |
| sell_spread_base | 0.2990806298654899 |
| sell_spread_ratio | 2.3394319602302787 |
| stop_loss | 0.18149250586590188 |
| take_profit | 0.025506606230470866 |
| time_limit | 169423 |
| total_amount_quote | 66.46856635146756 |
| trailing_stop_activation | 0.022819347793424243 |
| trailing_stop_delta | 0.001320429598071859 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 66.46856635146756 |
| Selected | 66.46856635146756 |

> **WARNING**: Selected quote is within 5% of search minimum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 4155.6738
- **Net PnL (quote)**: 2762.2168
- **Sharpe Ratio**: 9.6263
- **Max Drawdown %**: 20.7673
- **Profit Factor**: 1.7145729215182237
- **Trade Count**: 15103
- **Total Fees (quote)**: 92.0788
- **Maker Fees**: 46.5953
- **Taker Fees**: 45.4835
- **Fee Drag %**: 138.5298

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.6446
- **PnL Component**: 3.7508
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1558
- **Fee Drag Component**: -0.6926
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **1.0300**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 310.70 | 31.66 | 9.18 | 1392 | 1.0276 | n/a |
| 1 | 446.85 | 39.21 | 10.19 | 1582 | 1.2979 | n/a |
| 2 | 312.82 | 37.50 | 6.12 | 1426 | 1.0572 | n/a |
| 3 | 392.76 | 43.37 | 7.43 | 1472 | 1.2219 | n/a |
| 4 | 410.67 | 34.12 | 14.05 | 1380 | 1.2071 | n/a |
| 5 | 555.32 | 32.12 | 12.03 | 1496 | 1.4654 | n/a |
| 6 | 286.84 | 46.62 | 7.37 | 1471 | 0.9805 | n/a |
| 7 | 321.03 | 38.99 | 5.36 | 1445 | 1.0794 | n/a |
| 8 | 318.78 | 34.44 | 6.63 | 1458 | 1.0640 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.6278)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 4156.80 | 9.60 | 21.38 | 2.3027 |
| fees_2x | 4137.51 | 9.58 | 21.03 | 1.9579 |
| latency_plus1 | 3766.05 | 10.07 | 21.48 | 2.6187 |
| latency_plus2 | 3255.56 | 9.54 | 21.65 | 2.5561 |
| latency_plus3 | 2524.98 | 8.96 | 21.66 | 2.4028 |
| low_liquidity | 4220.23 | 9.09 | 20.95 | 2.6586 |
| very_low_liquidity | 4173.34 | 9.36 | 21.17 | 2.6497 |
| high_slippage | 4123.85 | 9.58 | 21.19 | 2.6404 |
| extreme_slippage | 3894.30 | 9.41 | 21.05 | 2.5929 |
| combined_adverse | 3716.97 | 10.00 | 21.40 | 2.3069 |
| spread_widen_10bps | 4126.43 | 9.92 | 20.83 | 2.6452 |
| spread_widen_25bps | 4124.54 | 9.42 | 21.10 | 2.6516 |
| thin_book | 2434.98 | 8.88 | 20.28 | 2.4156 |
| very_thin_book | 1120.61 | 7.10 | 21.80 | 1.9127 |
| entry_spread_stress | 4250.66 | 9.95 | 20.80 | 2.6820 |
| combined_market_deterioration | 3300.78 | 9.52 | 21.44 | 2.3174 |
| severe_adverse | 1055.15 | 6.91 | 25.81 | 1.6278 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0043)
- **Trend**: ranging (efficiency: 0.0040)
- **Best holdout score**: 2.0282 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 2.1362 | 1.8145 | 877.24 | 8.20 | 3300 |
| 1 | 1.4365 | 1.9817 | 1143.83 | 9.18 | 6488 |
| 2 | 1.4322 | 2.0282 | 1259.92 | 7.77 | 5514 |
| 3 | 1.4208 | 2.0086 | 1226.23 | 9.04 | 6318 |
| 4 | 1.4131 | 1.9344 | 1132.20 | 9.15 | 6483 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51838
- **Expected rows**: 51841
- **Missing rows**: 3
- **Forward-fill count**: 221
- **Forward-fill fraction**: 0.004263281762413674
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.482412446795377
- **PnL %**: 585.8590444468548
- **Trade count**: 3053

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.6852047161896601
- **PnL %**: 185.76478722337853
- **Trade count**: 1528

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.14780395087438672
- **PnL %**: 56.78218992742398
- **Trade count**: 694

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 2.507883056261252
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 2.5503, 2.5066 |
| sell_spread_base | 2.5355, 2.5362 |
| stop_loss | 2.5356, 2.5243 |
| take_profit | 2.5079, 2.5079 |
| executor_refresh_time | 2.5079, 2.5079 |
| cooldown_time | 2.5079, 2.5079 |
| total_amount_quote | 2.5419, 2.5077 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3517824973159272
- **Max CV**: 0.8667239939059835
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time
- **Scattered params**: take_profit, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1679 | 0.2125798850861612 | 0.3148836524828766 | 0.2569211464526606 |
| buy_spread_ratio | 0.1668 | 1.2459501184880015 | 2.0324214879215585 | 1.5193774318749622 |
| sell_spread_base | 0.2037 | 0.21953596932761257 | 0.41942836279832857 | 0.2853176731043092 |
| sell_spread_ratio | 0.1671 | 1.2646253866513364 | 2.0676445560515075 | 1.598788115835493 |
| buy_side_weight | 0.0627 | 0.3717427000109586 | 0.4505997864481187 | 0.414519899208219 |
| amount_skew | 0.4812 | 1.010142137131334 | 3.799391471137112 | 2.521201378479568 |
| stop_loss | 0.2742 | 0.09504057911158563 | 0.2211790679767084 | 0.15546683619102641 |
| take_profit | 0.7631 | 0.019422716056916825 | 0.1470821579164466 | 0.06779032026565722 |
| executor_refresh_time | 0.3124 | 300.0 | 772.0 | 474.7 |
| cooldown_time | 0.4039 | 75.0 | 290.0 | 160.4 |
| total_amount_quote | 0.8667 | 77.24466921857855 | 888.3436328393216 | 371.67960771490726 |

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
| recent_objective | > 0 | 1.482412446795377 | PASS |
| recent_pnl | >= 0 | 585.8590444468548 | PASS |
| recent_trades | >= 5 | 3053 | PASS |
| worst_stress | > -10 | 1.6277764429048918 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.8145 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.6277764429048918 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.482412446795377, pnl=585.8590444468548, trades=3053, reason= |
| recent_14d_info | PASS | informational only; score=0.6852047161896601, pnl=185.76478722337853, trades=1528, reason= |
| recent_7d_info | PASS | informational only; score=0.14780395087438672, pnl=56.78218992742398, trades=694, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3517824973159272 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51838 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | PASS | recent_7d_info | — | — |  |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51838
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8062
- **Recent window start**: 1773197700

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T04:57:29.326915+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 9847
