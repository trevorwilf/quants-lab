# PMM Dynamic Optimization Report: mexc_ICP-USDT_5m_sweep_v1

Generated: 2026-03-28 14:44:02 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T14:44:02.320816+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 9863 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ICP-USDT
- **interval**: 5m
- **n_candles**: 51903
- **dataset_hash**: c3cf23842fa76855e87622550c9a1ec9bcbd58b7f5c0276938845a3eba6d3271
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 36.6375983739606
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.37403143061825 |
| buy_n_levels | 2 |
| buy_side_weight | 0.47598851433728173 |
| buy_spread_base | 0.2352449507959607 |
| buy_spread_ratio | 1.7221532053626751 |
| cooldown_time | 505 |
| executor_refresh_time | 1295 |
| macd_fast | 47 |
| macd_signal | 19 |
| macd_slow | 88 |
| natr_length | 16 |
| sell_n_levels | 6 |
| sell_spread_base | 0.3357915740416743 |
| sell_spread_ratio | 1.3065449438402543 |
| stop_loss | 0.12580321337918338 |
| take_profit | 0.07795984451229117 |
| time_limit | 155509 |
| total_amount_quote | 36.6375983739606 |
| trailing_stop_activation | 0.02843776372903931 |
| trailing_stop_delta | 0.001021487029299847 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 36.6375983739606 |
| Selected | 36.6375983739606 |

> **WARNING**: Selected quote is within 5% of search minimum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3257.4134
- **Net PnL (quote)**: 1193.4380
- **Sharpe Ratio**: 7.0572
- **Max Drawdown %**: 46.4341
- **Profit Factor**: 1.605211403499817
- **Trade Count**: 6607
- **Total Fees (quote)**: 46.0156
- **Maker Fees**: 23.2750
- **Taker Fees**: 22.7406
- **Fee Drag %**: 125.5966

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.2776
- **PnL Component**: 3.5138
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.3483
- **Fee Drag Component**: -0.6280
- **Inventory Component**: -0.2500
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.9354**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 469.39 | 24.28 | 12.48 | 743 | 1.3196 | n/a |
| 1 | 370.30 | 40.53 | 9.43 | 622 | 1.1668 | n/a |
| 2 | 295.71 | 37.58 | 10.53 | 602 | 0.9867 | n/a |
| 3 | 174.63 | 33.89 | 5.26 | 528 | 0.6684 | n/a |
| 4 | 602.93 | 29.52 | 10.26 | 635 | 1.5559 | n/a |
| 5 | 294.50 | 32.80 | 11.09 | 625 | 0.9775 | n/a |
| 6 | 289.92 | 13.02 | 13.40 | 587 | 0.9507 | n/a |
| 7 | 298.28 | 35.31 | 8.90 | 522 | 1.0126 | n/a |
| 8 | 444.28 | 16.13 | 8.54 | 602 | 1.3188 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.2894)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3211.12 | 6.63 | 46.99 | 1.9511 |
| fees_2x | 3208.62 | 6.67 | 46.66 | 1.6490 |
| latency_plus1 | 2978.23 | 6.54 | 47.20 | 2.2360 |
| latency_plus2 | 2678.24 | 5.82 | 46.38 | 2.2152 |
| latency_plus3 | 2208.39 | 6.01 | 48.57 | 2.0991 |
| low_liquidity | 3329.02 | 6.68 | 46.74 | 2.3020 |
| very_low_liquidity | 3224.31 | 6.56 | 46.84 | 2.2792 |
| high_slippage | 3214.76 | 6.84 | 48.03 | 2.2579 |
| extreme_slippage | 3059.04 | 6.80 | 48.75 | 2.2094 |
| combined_adverse | 2936.17 | 5.97 | 49.17 | 1.9322 |
| spread_widen_10bps | 3191.98 | 6.60 | 46.87 | 2.2579 |
| spread_widen_25bps | 3134.85 | 6.59 | 48.09 | 2.2395 |
| thin_book | 1950.45 | 5.74 | 46.39 | 2.0157 |
| very_thin_book | 874.90 | 4.45 | 49.99 | 1.4668 |
| entry_spread_stress | 3196.25 | 6.66 | 47.07 | 2.2623 |
| combined_market_deterioration | 2442.03 | 6.28 | 51.09 | 1.8636 |
| severe_adverse | 922.69 | 4.26 | 49.59 | 1.2894 |

## Holdout Validation

- **Holdout bars**: 8774
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0044)
- **Trend**: ranging (efficiency: 0.0177)
- **Best holdout score**: 1.6101 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.7835 | 1.4010 | 572.33 | 17.66 | 1241 |
| 1 | 1.2700 | 1.5445 | 689.83 | 14.67 | 5344 |
| 2 | 1.2364 | 1.6101 | 732.81 | 12.86 | 4429 |
| 3 | 1.2101 | 1.4694 | 619.08 | 13.94 | 2966 |
| 4 | 1.1924 | 1.5511 | 687.96 | 13.21 | 6263 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51903
- **Expected rows**: 51937
- **Missing rows**: 34
- **Forward-fill count**: 39
- **Forward-fill fraction**: 0.0007514016530836368
- **Longest gap (seconds)**: 5400

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.5703124928621472
- **PnL %**: 633.5281812682421
- **Trade count**: 1113

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 2.0182791078384263
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 2.0106, 2.0291 |
| sell_spread_base | 1.9917, 2.0261 |
| stop_loss | 2.0456, 2.0271 |
| take_profit | 2.0183, 2.0183 |
| executor_refresh_time | 2.0183, 2.0273 |
| cooldown_time | 2.0183, 2.0183 |
| total_amount_quote | 2.0239, 2.0237 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2930450662572475
- **Max CV**: 0.6185396820578573
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time
- **Scattered params**: total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3467 | 0.2045982234345536 | 0.502398935875164 | 0.28874907266361055 |
| buy_spread_ratio | 0.1210 | 1.296825737779629 | 1.8901660845124588 | 1.490549555575267 |
| sell_spread_base | 0.2155 | 0.2019229566466214 | 0.37657466783328897 | 0.26235738712261136 |
| sell_spread_ratio | 0.1081 | 1.217536122024656 | 1.6661055566866825 | 1.4391887380724762 |
| buy_side_weight | 0.1196 | 0.3317044778411261 | 0.47417437771385934 | 0.4025534778968442 |
| amount_skew | 0.2327 | 2.028607662013358 | 3.997212887943058 | 3.113095767902461 |
| stop_loss | 0.2515 | 0.1121486481315696 | 0.2385841154146433 | 0.17447769806290223 |
| take_profit | 0.3741 | 0.040673890409209594 | 0.1260765373530403 | 0.07270935554336935 |
| executor_refresh_time | 0.3559 | 314.0 | 803.0 | 521.6 |
| cooldown_time | 0.4797 | 129.0 | 524.0 | 251.6 |
| total_amount_quote | 0.6185 | 46.080225183013 | 310.01784752933406 | 152.0307268039153 |

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
| recent_objective | > 0 | 1.5703124928621472 | PASS |
| recent_pnl | >= 0 | 633.5281812682421 | PASS |
| recent_trades | >= 5 | 1113 | PASS |
| worst_stress | > -10 | 1.2894258277673059 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.4010 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.2894258277673059 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.5703124928621472, pnl=633.5281812682421, trades=1113, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2930450662572475 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51903 |  |
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
- **Dev bars**: 35098
- **Holdout bars**: 8774
- **Recent 28d bars**: 8031

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T14:44:02.320816+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 9863
