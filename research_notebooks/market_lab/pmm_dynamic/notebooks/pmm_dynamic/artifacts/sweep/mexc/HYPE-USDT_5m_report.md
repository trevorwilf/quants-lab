# PMM Dynamic Optimization Report: mexc_HYPE-USDT_5m_sweep_v1

Generated: 2026-03-28 13:46:37 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T13:46:37.486734+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 6165 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: HYPE-USDT
- **interval**: 5m
- **n_candles**: 51911
- **dataset_hash**: 4a651f847665e052aa1f7ac280abad4068a02129f1138c092c022439c32fbf94
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 88.55573647858455
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.9491083995674776 |
| buy_n_levels | 5 |
| buy_side_weight | 0.424998657653356 |
| buy_spread_base | 0.26153603911074835 |
| buy_spread_ratio | 1.4827311611779666 |
| cooldown_time | 397 |
| executor_refresh_time | 940 |
| macd_fast | 29 |
| macd_signal | 18 |
| macd_slow | 66 |
| natr_length | 20 |
| sell_n_levels | 5 |
| sell_spread_base | 0.2025193472439575 |
| sell_spread_ratio | 1.4166438993967188 |
| stop_loss | 0.18655661449652403 |
| take_profit | 0.06521780458577209 |
| time_limit | 162179 |
| total_amount_quote | 88.55573647858455 |
| trailing_stop_activation | 0.02839311459191359 |
| trailing_stop_delta | 0.0010735456822248163 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 88.55573647858455 |
| Selected | 88.55573647858455 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3834.0715
- **Net PnL (quote)**: 3395.2903
- **Sharpe Ratio**: 11.3963
- **Max Drawdown %**: 18.9281
- **Profit Factor**: 1.4904356546577766
- **Trade Count**: 24252
- **Total Fees (quote)**: 140.2268
- **Maker Fees**: 70.9416
- **Taker Fees**: 69.2852
- **Fee Drag %**: 158.3486

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.4821
- **PnL Component**: 3.6723
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1420
- **Fee Drag Component**: -0.7917
- **Inventory Component**: -0.2498
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **1.1221**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 544.23 | 39.10 | 14.17 | 2476 | 1.4243 | n/a |
| 1 | 397.31 | 42.86 | 7.60 | 2168 | 1.2264 | n/a |
| 2 | 356.28 | 39.48 | 8.61 | 2118 | 1.1327 | n/a |
| 3 | 304.73 | 49.91 | 5.85 | 2354 | 1.0309 | n/a |
| 4 | 368.20 | 36.28 | 8.14 | 2399 | 1.1568 | n/a |
| 5 | 657.79 | 36.90 | 13.97 | 2374 | 1.5866 | n/a |
| 6 | 453.19 | 31.04 | 6.75 | 2406 | 1.3280 | n/a |
| 7 | 343.30 | 47.87 | 6.05 | 2356 | 1.1190 | n/a |
| 8 | 328.17 | 47.09 | 4.55 | 2241 | 1.0975 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.5398)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3752.63 | 11.29 | 19.10 | 2.0659 |
| fees_2x | 3688.34 | 11.25 | 19.30 | 1.6598 |
| latency_plus1 | 3208.35 | 10.83 | 19.11 | 2.4192 |
| latency_plus2 | 2577.13 | 9.81 | 18.91 | 2.3217 |
| latency_plus3 | 2088.06 | 9.35 | 19.65 | 2.2106 |
| low_liquidity | 3793.43 | 11.25 | 19.13 | 2.4750 |
| very_low_liquidity | 3756.14 | 11.20 | 18.81 | 2.4778 |
| high_slippage | 3739.55 | 11.20 | 19.39 | 2.4641 |
| extreme_slippage | 3429.89 | 10.90 | 19.80 | 2.3838 |
| combined_adverse | 3052.91 | 10.52 | 19.21 | 2.0438 |
| spread_widen_10bps | 3627.54 | 11.18 | 19.24 | 2.4365 |
| spread_widen_25bps | 3579.66 | 11.01 | 19.43 | 2.4236 |
| thin_book | 2241.57 | 9.22 | 23.00 | 2.2780 |
| very_thin_book | 1098.86 | 7.29 | 25.11 | 1.8177 |
| entry_spread_stress | 3667.33 | 11.17 | 19.37 | 2.4423 |
| combined_market_deterioration | 2795.13 | 9.98 | 20.47 | 2.0985 |
| severe_adverse | 1072.59 | 7.12 | 24.25 | 1.5398 |

## Holdout Validation

- **Holdout bars**: 8774
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0057)
- **Trend**: ranging (efficiency: 0.0078)
- **Best holdout score**: 2.0994 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 2.0109 | 1.8273 | 940.12 | 11.15 | 5462 |
| 1 | 1.4848 | 2.0994 | 1426.79 | 11.88 | 6123 |
| 2 | 1.4656 | 1.9682 | 1262.76 | 13.31 | 3134 |
| 3 | 1.4457 | 2.0066 | 1265.02 | 13.16 | 7891 |
| 4 | 1.4323 | 1.9841 | 1224.33 | 10.61 | 8366 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51911
- **Expected rows**: 51939
- **Missing rows**: 28
- **Forward-fill count**: 93
- **Forward-fill fraction**: 0.0017915278072084915
- **Longest gap (seconds)**: 7500

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.5755797193487866
- **PnL %**: 674.2479973740152
- **Trade count**: 4678

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 2.44875719563683
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 2.4663, 2.4292 |
| sell_spread_base | 2.4423, 2.4528 |
| stop_loss | 2.4651, 2.4272 |
| take_profit | 2.4488, 2.4488 |
| executor_refresh_time | 2.4488, 2.4221 |
| cooldown_time | 2.4488, 2.4488 |
| total_amount_quote | 2.4335, 2.4472 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.24692728628981309
- **Max CV**: 0.5268466994751279
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time
- **Scattered params**: take_profit, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1961 | 0.20273502721018946 | 0.32587359889416967 | 0.252195611709808 |
| buy_spread_ratio | 0.0959 | 1.2015265880891763 | 1.591761592616377 | 1.312636292259927 |
| sell_spread_base | 0.1927 | 0.2016518842877243 | 0.3466073972384271 | 0.2369767225658977 |
| sell_spread_ratio | 0.0512 | 1.272551832243295 | 1.4723992318306454 | 1.3939951648208526 |
| buy_side_weight | 0.1149 | 0.42166864516768937 | 0.5859044200525785 | 0.47174702537885116 |
| amount_skew | 0.2208 | 1.6348782581248982 | 3.876033257201054 | 2.8386855386247305 |
| stop_loss | 0.2438 | 0.11889664255598328 | 0.2427763114213442 | 0.16894600185024958 |
| take_profit | 0.5064 | 0.028923996028444372 | 0.1437416673280476 | 0.08044059369165871 |
| executor_refresh_time | 0.2973 | 300.0 | 736.0 | 481.6 |
| cooldown_time | 0.2703 | 109.0 | 253.0 | 176.2 |
| total_amount_quote | 0.5268 | 32.55063324004817 | 210.3514005122749 | 112.00962705022702 |

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
| recent_objective | > 0 | 1.5755797193487866 | PASS |
| recent_pnl | >= 0 | 674.2479973740152 | PASS |
| recent_trades | >= 5 | 4678 | PASS |
| worst_stress | > -10 | 1.5398201361840123 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.8273 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.5398201361840123 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.5755797193487866, pnl=674.2479973740152, trades=4678, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.24692728628981309 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51911 |  |
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
- **Dev bars**: 35100
- **Holdout bars**: 8774
- **Recent 28d bars**: 8037

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T13:46:37.486734+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 6165
