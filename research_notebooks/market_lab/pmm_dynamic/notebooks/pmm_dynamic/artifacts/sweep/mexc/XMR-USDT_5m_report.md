# PMM Dynamic Optimization Report: mexc_XMR-USDT_5m_sweep_v1

Generated: 2026-04-09 12:50:17 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T12:50:17.697142+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 13132 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 51954
- **dataset_hash**: c4a7ae7c80245122aef97fe89bef4bf3d9d56b57211476336d06e8de4e6c9781
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 873.1667970838517
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.202575873172499 |
| buy_n_levels | 9 |
| buy_side_weight | 0.6120072000911128 |
| buy_spread_base | 3.7566120065846214 |
| buy_spread_ratio | 1.3095305783990658 |
| cooldown_time | 1033 |
| executor_refresh_time | 1988 |
| macd_fast | 41 |
| macd_signal | 16 |
| macd_slow | 82 |
| natr_length | 25 |
| sell_n_levels | 8 |
| sell_spread_base | 2.386240140118572 |
| sell_spread_ratio | 2.0346269151041354 |
| stop_loss | 0.13735063326946564 |
| take_profit | 0.07442106396647435 |
| time_limit | 54558 |
| total_amount_quote | 873.1667970838517 |
| trailing_stop_activation | 0.0035057300758263243 |
| trailing_stop_delta | 0.0011228102033812334 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 873.1667970838517 |
| Selected | 873.1667970838517 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 5.7937
- **Net PnL (quote)**: 50.5887
- **Sharpe Ratio**: 2.7331
- **Max Drawdown %**: 3.3522
- **Profit Factor**: 2.0684173411855635
- **Trade Count**: 1429
- **Total Fees (quote)**: 7.4424
- **Maker Fees**: 3.7192
- **Taker Fees**: 3.7232
- **Fee Drag %**: 0.8523

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0124
- **PnL Component**: 0.0563
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0251
- **Fee Drag Component**: -0.0043
- **Inventory Component**: -0.0142
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.0002**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.20 | 6.99 | 0.10 | 53 | 0.0011 | n/a |
| 1 | -0.06 | -0.55 | 0.65 | 67 | -0.0058 | n/a |
| 2 | -0.02 | -0.35 | 0.21 | 79 | -0.0020 | n/a |
| 3 | 0.28 | 3.87 | 0.20 | 61 | 0.0010 | n/a |
| 4 | 1.02 | 4.92 | 1.01 | 94 | 0.0020 | n/a |
| 5 | 0.77 | 6.63 | 0.63 | 77 | 0.0026 | n/a |
| 6 | -1.18 | -7.83 | 1.40 | 65 | -0.0227 | n/a |
| 7 | 0.18 | 15.62 | 0.01 | 55 | 0.0015 | n/a |
| 8 | -0.27 | -5.66 | 0.34 | 87 | -0.0073 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0916)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 5.37 | 2.54 | 3.36 | 0.0061 |
| fees_2x | 4.94 | 2.34 | 3.38 | -0.0002 |
| latency_plus1 | 5.50 | 2.59 | 3.35 | 0.0095 |
| latency_plus2 | 4.40 | 2.18 | 3.31 | -0.0003 |
| latency_plus3 | 4.60 | 2.11 | 3.48 | -0.0012 |
| low_liquidity | 5.79 | 2.73 | 3.35 | 0.0124 |
| very_low_liquidity | 5.78 | 2.73 | 3.35 | 0.0123 |
| high_slippage | 4.73 | 2.24 | 3.37 | 0.0021 |
| extreme_slippage | 2.60 | 1.25 | 3.41 | -0.0190 |
| combined_adverse | 4.00 | 1.90 | 3.38 | -0.0073 |
| spread_widen_10bps | 3.53 | 1.34 | 4.62 | -0.0212 |
| spread_widen_25bps | 1.31 | 0.53 | 4.72 | -0.0428 |
| thin_book | -0.78 | -0.34 | 4.51 | -0.0542 |
| very_thin_book | -0.61 | -0.50 | 2.82 | -0.0324 |
| entry_spread_stress | 3.92 | 1.52 | 4.54 | -0.0157 |
| combined_market_deterioration | -1.00 | -0.38 | 4.72 | -0.0653 |
| severe_adverse | -3.63 | -1.39 | 5.31 | -0.0916 |

## Holdout Validation

- **Holdout bars**: 8784
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0036)
- **Trend**: ranging (efficiency: 0.0030)
- **Best holdout score**: -0.0132 (rank #3)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0396 | -0.0205 | -0.95 | 1.40 | 126 |
| 1 | 0.0033 | -0.0329 | 2.37 | 1.77 | 634 |
| 2 | 0.0032 | -0.0159 | 0.15 | 0.55 | 1045 |
| 3 | 0.0031 | -0.0132 | 1.29 | 2.24 | 172 |
| 4 | 0.0016 | -0.0219 | 1.67 | 1.43 | 660 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51954
- **Expected rows**: 51986
- **Missing rows**: 32
- **Forward-fill count**: 97
- **Forward-fill fraction**: 0.0018670362243523116
- **Longest gap (seconds)**: 9900

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.0013141766674305835
- **PnL %**: 0.4609907587718759
- **Trade count**: 152

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.004250051990161274
- **PnL %**: 0.5998429967483272
- **Trade count**: 69

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1222 <= 0; recent worst stress -1000.0000 < -10.0
- **Objective score**: -0.12222574916807377
- **PnL %**: 0.6983317787448186
- **Trade count**: 18

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: 0.0329220001302237
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0209, 0.0177 |
| sell_spread_base | 0.0367, 0.0263 |
| stop_loss | 0.0325, 0.0333 |
| take_profit | 0.0329, 0.0329 |
| executor_refresh_time | 0.0045, 0.0315 |
| cooldown_time | 0.0329, 0.0329 |
| total_amount_quote | 0.0328, 0.0340 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.40142688091073003
- **Max CV**: 0.906959779230363
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1415 | 2.520785474281091 | 4.256805191460716 | 3.5498571750060206 |
| buy_spread_ratio | 0.0651 | 1.2026907388680905 | 1.4626509023697019 | 1.3196295130236855 |
| sell_spread_base | 0.8400 | 0.26158173202069845 | 3.2566360026434866 | 1.219053718241934 |
| sell_spread_ratio | 0.1307 | 1.8100501387115342 | 2.730144801088631 | 2.3140426629234323 |
| buy_side_weight | 0.1283 | 0.4239470851981909 | 0.6353593433085643 | 0.5342879006501253 |
| amount_skew | 0.3279 | 1.0956635040216047 | 3.3312554499369025 | 2.006929831079053 |
| stop_loss | 0.9070 | 0.013435572176647918 | 0.2475440933347957 | 0.10274903558040518 |
| take_profit | 0.4063 | 0.026742748345212987 | 0.10679829583408781 | 0.06329262510705351 |
| executor_refresh_time | 0.5126 | 747.0 | 8139.0 | 4854.7 |
| cooldown_time | 0.6653 | 164.0 | 2696.0 | 1405.1 |
| total_amount_quote | 0.2910 | 439.37550261084994 | 977.973128722704 | 714.1484562652329 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.0
- **supports_post_only**: True
- **connector**: mexc
- **fill_participation_rate**: 0.1
- **latency_bars**: 1
- **slippage_bps**: 5.0
- **touch_through**: False
- **maker_fill_probability**: 1.0
- **refresh_close_mode**: market_close

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
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.0013141766674305835 | PASS |
| recent_pnl | >= 0 | 0.4609907587718759 | PASS |
| recent_trades | >= 5 | 152 | PASS |
| worst_stress | > -10 | -0.09160389822451469 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.02053551652368256 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.09160389822451469 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | PASS | score=0.0013141766674305835, pnl=0.4609907587718759, trades=152, reason= |
| recent_14d_info | PASS | informational only; score=0.004250051990161274, pnl=0.5998429967483272, trades=69, reason= |
| recent_7d_info | FAIL | informational only; score=-0.12222574916807377, pnl=0.6983317787448186, trades=18, reason=recent objective score -0.1222 <= 0; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.40142688091073003 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51954 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1222 <= 0; recent worst stress -1000.0000 < -10.0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51954
- **Pre-release bars**: 43921
- **Dev bars**: 35137
- **Holdout bars**: 8784
- **Recent 28d bars**: 8033
- **Recent window start**: 1773315900

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T12:50:17.697142+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 13132
