# PMM Dynamic Optimization Report: mexc_XMR-USDC_5m_sweep_v1

Generated: 2026-03-29 01:31:18 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T01:31:18.119655+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 9586 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XMR-USDC
- **interval**: 5m
- **n_candles**: 52057
- **dataset_hash**: 333054e799e5944c438f3f3a2d6d841f5bd806aca4975f52f6bdd11db442a318
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 251.51503453966734
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.364314052131415 |
| buy_n_levels | 8 |
| buy_side_weight | 0.43897396053616655 |
| buy_spread_base | 0.27183854981012684 |
| buy_spread_ratio | 1.421374661346707 |
| cooldown_time | 494 |
| executor_refresh_time | 982 |
| macd_fast | 12 |
| macd_signal | 9 |
| macd_slow | 29 |
| natr_length | 28 |
| sell_n_levels | 3 |
| sell_spread_base | 0.2453057959707106 |
| sell_spread_ratio | 1.237094252287272 |
| stop_loss | 0.21173726999619175 |
| take_profit | 0.04228109077622128 |
| time_limit | 172766 |
| total_amount_quote | 251.51503453966734 |
| trailing_stop_activation | 0.02627863813640979 |
| trailing_stop_delta | 0.001651790554683698 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 251.51503453966734 |
| Selected | 251.51503453966734 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 4363.2913
- **Net PnL (quote)**: 10974.3335
- **Sharpe Ratio**: 11.7178
- **Max Drawdown %**: 33.0473
- **Profit Factor**: 1.3374637827688651
- **Trade Count**: 24315
- **Total Fees (quote)**: 358.6578
- **Maker Fees**: 180.8912
- **Taker Fees**: 177.7666
- **Fee Drag %**: 142.5989

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.5804
- **PnL Component**: 3.7985
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.2479
- **Fee Drag Component**: -0.7130
- **Inventory Component**: -0.2500
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.9277**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 414.97 | 37.13 | 12.98 | 2481 | 1.2134 | n/a |
| 1 | 306.78 | 50.17 | 4.99 | 2522 | 1.0430 | n/a |
| 2 | 385.56 | 30.67 | 4.97 | 2568 | 1.2208 | n/a |
| 3 | 68.89 | 24.75 | 6.03 | 2494 | 0.1648 | n/a |
| 4 | 626.99 | 37.72 | 13.04 | 2305 | 1.5628 | n/a |
| 5 | 430.41 | 35.12 | 8.86 | 2537 | 1.2736 | n/a |
| 6 | 325.00 | 29.43 | 15.11 | 2615 | 1.0127 | n/a |
| 7 | 215.87 | 39.41 | 7.33 | 2528 | 0.7795 | n/a |
| 8 | 115.77 | 33.29 | 6.39 | 2563 | 0.4066 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.7195)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 4300.74 | 11.68 | 32.40 | 2.2125 |
| fees_2x | 4237.05 | 11.60 | 32.82 | 1.8434 |
| latency_plus1 | 3628.71 | 11.20 | 32.46 | 2.5009 |
| latency_plus2 | 2960.04 | 10.51 | 32.47 | 2.4019 |
| latency_plus3 | 2407.82 | 9.93 | 31.22 | 2.2893 |
| low_liquidity | 4011.48 | 11.49 | 32.21 | 2.5558 |
| very_low_liquidity | 3474.70 | 11.06 | 31.30 | 2.5072 |
| high_slippage | 4230.41 | 11.59 | 32.60 | 2.5620 |
| extreme_slippage | 4048.87 | 11.35 | 31.92 | 2.5275 |
| combined_adverse | 3272.25 | 10.73 | 31.56 | 2.1817 |
| spread_widen_10bps | 4189.28 | 11.53 | 32.35 | 2.5510 |
| spread_widen_25bps | 4094.02 | 11.33 | 31.86 | 2.5393 |
| thin_book | 2626.31 | 10.10 | 33.02 | 2.3965 |
| very_thin_book | 1244.76 | 8.24 | 32.25 | 1.8954 |
| entry_spread_stress | 4189.39 | 11.51 | 32.32 | 2.5461 |
| combined_market_deterioration | 3119.32 | 10.62 | 32.32 | 2.1824 |
| severe_adverse | 1342.54 | 8.03 | 32.33 | 1.7195 |

## Holdout Validation

- **Holdout bars**: 8798
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0044)
- **Trend**: ranging (efficiency: 0.0165)
- **Best holdout score**: 1.9522 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 2.1499 | 1.5990 | 770.54 | 21.01 | 5817 |
| 1 | 1.4347 | 1.8952 | 1198.68 | 17.93 | 4782 |
| 2 | 1.4153 | 1.9522 | 1276.62 | 20.06 | 5702 |
| 3 | 1.3307 | 1.9430 | 1206.47 | 19.25 | 5349 |
| 4 | 1.3227 | 1.8610 | 1085.44 | 21.29 | 5463 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52057
- **Expected rows**: 52057
- **Missing rows**: 0
- **Forward-fill count**: 64
- **Forward-fill fraction**: 0.0012294215955587144
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.9371165302107688
- **PnL %**: 295.5401458846539
- **Trade count**: 5126

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 2.0305095838708382
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 2.0363, 2.0347 |
| sell_spread_base | 2.0270, 2.0241 |
| stop_loss | 2.0143, 2.0102 |
| take_profit | 2.0239, 2.0261 |
| executor_refresh_time | 2.0305, 1.9966 |
| cooldown_time | 2.0305, 2.0305 |
| total_amount_quote | 2.0080, 2.0299 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.31389254142663536
- **Max CV**: 0.8847054395283211
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time
- **Scattered params**: total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3306 | 0.20451875293171412 | 0.47994213547889997 | 0.31803316413112437 |
| buy_spread_ratio | 0.1613 | 1.2185985580629681 | 1.9303739027169375 | 1.4579293946417817 |
| sell_spread_base | 0.3103 | 0.20934271878833854 | 0.5030916309230079 | 0.28128431829275585 |
| sell_spread_ratio | 0.1376 | 1.328820699340841 | 1.9562598743189925 | 1.5686004481056675 |
| buy_side_weight | 0.1669 | 0.32265190197564514 | 0.5675417578155959 | 0.47808353497615796 |
| amount_skew | 0.0692 | 3.227993063035108 | 3.957997743005149 | 3.6674292172240457 |
| stop_loss | 0.2252 | 0.12375064164542507 | 0.24919246180159435 | 0.18462948660316017 |
| take_profit | 0.3794 | 0.016363358604716417 | 0.06549172222658897 | 0.04669411201281158 |
| executor_refresh_time | 0.3978 | 300.0 | 888.0 | 539.0 |
| cooldown_time | 0.3899 | 74.0 | 268.0 | 177.7 |
| total_amount_quote | 0.8847 | 25.980759289352505 | 313.01768609224644 | 105.19880028582675 |

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
| recent_objective | > 0 | 0.9371165302107688 | PASS |
| recent_pnl | >= 0 | 295.5401458846539 | PASS |
| recent_trades | >= 5 | 5126 | PASS |
| worst_stress | > -10 | 1.7194570176909931 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.5990 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.7194570176909931 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.9371165302107688, pnl=295.5401458846539, trades=5126, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.31389254142663536 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52057 |  |
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
- **Dev bars**: 35194
- **Holdout bars**: 8798
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T01:31:18.119655+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 9586
