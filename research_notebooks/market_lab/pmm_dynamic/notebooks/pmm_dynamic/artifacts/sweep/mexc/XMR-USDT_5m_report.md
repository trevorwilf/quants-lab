# PMM Dynamic Optimization Report: mexc_XMR-USDT_5m_sweep_v1

Generated: 2026-03-29 02:34:21 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T02:34:21.714628+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 9890 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 52057
- **dataset_hash**: 88e349c6ee49bc51b9ec85b17312099aabdfb74578ec18e3af46eefe0ff12a42
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 114.30431663483091
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.9217768770135697 |
| buy_n_levels | 4 |
| buy_side_weight | 0.2866282988405748 |
| buy_spread_base | 0.21853712335669573 |
| buy_spread_ratio | 1.4886016785540177 |
| cooldown_time | 577 |
| executor_refresh_time | 1002 |
| macd_fast | 46 |
| macd_signal | 30 |
| macd_slow | 72 |
| natr_length | 21 |
| sell_n_levels | 3 |
| sell_spread_base | 0.21188076539588027 |
| sell_spread_ratio | 2.365483901271052 |
| stop_loss | 0.2379149389285799 |
| take_profit | 0.06382910436551359 |
| time_limit | 171940 |
| total_amount_quote | 114.30431663483091 |
| trailing_stop_activation | 0.023414572673379444 |
| trailing_stop_delta | 0.0011887161806460405 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 114.30431663483091 |
| Selected | 114.30431663483091 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 4562.5224
- **Net PnL (quote)**: 5215.1600
- **Sharpe Ratio**: 12.2233
- **Max Drawdown %**: 27.9702
- **Profit Factor**: 1.3385240652637804
- **Trade Count**: 17042
- **Total Fees (quote)**: 187.2572
- **Maker Fees**: 94.2680
- **Taker Fees**: 92.9893
- **Fee Drag %**: 163.8234

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.5564
- **PnL Component**: 3.8421
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.2098
- **Fee Drag Component**: -0.8191
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **1.0460**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 435.73 | 40.87 | 12.41 | 1720 | 1.2615 | n/a |
| 1 | 332.80 | 54.78 | 3.88 | 1689 | 1.1178 | n/a |
| 2 | 328.26 | 47.33 | 3.00 | 1736 | 1.1185 | n/a |
| 3 | 111.53 | 36.18 | 4.01 | 1640 | 0.4046 | n/a |
| 4 | 640.92 | 40.86 | 11.76 | 1641 | 1.5908 | n/a |
| 5 | 525.38 | 37.37 | 9.73 | 1698 | 1.4334 | n/a |
| 6 | 335.04 | 36.81 | 12.50 | 1685 | 1.0583 | n/a |
| 7 | 291.56 | 51.92 | 3.83 | 1741 | 1.0202 | n/a |
| 8 | 117.09 | 37.22 | 4.60 | 1739 | 0.4290 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.7174)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 4503.27 | 12.08 | 28.22 | 2.1311 |
| fees_2x | 4513.35 | 12.08 | 27.56 | 1.7305 |
| latency_plus1 | 3871.17 | 11.61 | 27.08 | 2.5058 |
| latency_plus2 | 3084.00 | 11.14 | 26.95 | 2.4082 |
| latency_plus3 | 2529.74 | 10.62 | 25.63 | 2.3200 |
| low_liquidity | 4499.64 | 12.23 | 27.64 | 2.5543 |
| very_low_liquidity | 4478.22 | 12.14 | 27.73 | 2.5595 |
| high_slippage | 4441.99 | 12.00 | 27.68 | 2.5365 |
| extreme_slippage | 4155.38 | 11.78 | 26.75 | 2.4864 |
| combined_adverse | 3735.17 | 11.50 | 27.78 | 2.1272 |
| spread_widen_10bps | 4395.17 | 12.15 | 27.23 | 2.5296 |
| spread_widen_25bps | 4398.53 | 12.04 | 27.28 | 2.5341 |
| thin_book | 2976.34 | 10.74 | 30.66 | 2.4424 |
| very_thin_book | 1476.53 | 8.86 | 28.72 | 2.0395 |
| entry_spread_stress | 4475.08 | 11.99 | 27.50 | 2.5470 |
| combined_market_deterioration | 3539.15 | 11.20 | 28.87 | 2.1810 |
| severe_adverse | 1410.95 | 8.47 | 30.14 | 1.7174 |

## Holdout Validation

- **Holdout bars**: 8798
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0047)
- **Trend**: ranging (efficiency: 0.0164)
- **Best holdout score**: 1.9286 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 2.1369 | 1.6451 | 810.77 | 19.57 | 3919 |
| 1 | 1.3162 | 1.9286 | 1241.82 | 18.51 | 2806 |
| 2 | 1.2338 | 1.8315 | 1071.64 | 20.30 | 2607 |
| 3 | 1.2330 | 1.9080 | 1163.72 | 21.89 | 2874 |
| 4 | 1.2035 | 1.7803 | 975.90 | 21.36 | 5368 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52057
- **Expected rows**: 52057
- **Missing rows**: 0
- **Forward-fill count**: 48
- **Forward-fill fraction**: 0.0009220661966690359
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.1395687188896446
- **PnL %**: 383.57660671970126
- **Trade count**: 3532

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.9732078327213132
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.9500, 1.9584 |
| sell_spread_base | 1.9430, 1.9316 |
| stop_loss | 1.9745, 1.9474 |
| take_profit | 1.9732, 1.9732 |
| executor_refresh_time | 1.9732, 1.9732 |
| cooldown_time | 1.9691, 1.9732 |
| total_amount_quote | 1.9685, 1.9552 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3508849304467048
- **Max CV**: 0.7197446658937012
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time
- **Scattered params**: cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2367 | 0.2231436303433285 | 0.468545602345154 | 0.3564924251527144 |
| buy_spread_ratio | 0.2356 | 1.2612929577854863 | 2.5205242967554806 | 1.6233214936076894 |
| sell_spread_base | 0.3076 | 0.2003982995921781 | 0.4525816217221877 | 0.29643899528134804 |
| sell_spread_ratio | 0.3070 | 1.2040001815433004 | 2.774680189218168 | 1.7918455401955107 |
| buy_side_weight | 0.1922 | 0.4004141252805181 | 0.68293878616172 | 0.4985210477566002 |
| amount_skew | 0.1941 | 2.317182332245767 | 3.9249309193093613 | 3.2189695733838115 |
| stop_loss | 0.3496 | 0.08666222268036271 | 0.23939544697604073 | 0.15934308536723035 |
| take_profit | 0.4625 | 0.02675865912642915 | 0.10356011739316494 | 0.05972396678360964 |
| executor_refresh_time | 0.3361 | 318.0 | 775.0 | 515.3 |
| cooldown_time | 0.5186 | 66.0 | 273.0 | 145.0 |
| total_amount_quote | 0.7197 | 28.961096546125564 | 209.17485331107414 | 96.7802424351323 |

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
| recent_objective | > 0 | 1.1395687188896446 | PASS |
| recent_pnl | >= 0 | 383.57660671970126 | PASS |
| recent_trades | >= 5 | 3532 | PASS |
| worst_stress | > -10 | 1.7173755863919749 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.6451 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.7173755863919749 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.1395687188896446, pnl=383.57660671970126, trades=3532, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3508849304467048 |

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
- **run_timestamp**: 2026-03-29T02:34:21.714628+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 9890
