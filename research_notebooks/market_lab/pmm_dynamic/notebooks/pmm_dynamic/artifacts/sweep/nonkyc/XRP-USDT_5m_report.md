# PMM Dynamic Optimization Report: nonkyc_XRP-USDT_5m_sweep_v1

Generated: 2026-04-10 03:20:33 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-10T03:20:33.577535+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 11860 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: XRP-USDT
- **interval**: 5m
- **n_candles**: 52156
- **dataset_hash**: bd4e5e3686dcf21661f3646aa129c1bc4c33f1d8229162d1349303d2ed7ecd8a
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 612.0793397971073
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.119664801099997 |
| buy_n_levels | 10 |
| buy_side_weight | 0.3943879382307825 |
| buy_spread_base | 2.6429291517892097 |
| buy_spread_ratio | 2.5294587664204284 |
| cooldown_time | 4416 |
| executor_refresh_time | 12441 |
| macd_fast | 46 |
| macd_signal | 27 |
| macd_slow | 76 |
| natr_length | 40 |
| sell_n_levels | 8 |
| sell_spread_base | 4.992290287169464 |
| sell_spread_ratio | 1.9958935558128499 |
| stop_loss | 0.022952349449744405 |
| take_profit | 0.005843445370455029 |
| time_limit | 41156 |
| total_amount_quote | 612.0793397971073 |
| trailing_stop_activation | 0.057542710914739816 |
| trailing_stop_delta | 0.022643026568301458 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 612.0793397971073 |
| Selected | 612.0793397971073 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -6.9278
- **Net PnL (quote)**: -42.4039
- **Sharpe Ratio**: -6.0320
- **Max Drawdown %**: 7.7248
- **Profit Factor**: 0.3939611568004325
- **Trade Count**: 782
- **Total Fees (quote)**: 19.3591
- **Maker Fees**: 14.5260
- **Taker Fees**: 4.8331
- **Fee Drag %**: 3.1628
- **TP Min-Notional Failures**: 4471 :warning:
  > 4471 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1689
- **PnL Component**: -0.0718
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0579
- **Fee Drag Component**: -0.0158
- **Inventory Component**: -0.0231
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0312**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.38 | -9.69 | 0.42 | 73 | -0.0155 | n/a |
| 1 | -0.35 | -5.08 | 0.47 | 67 | -0.0160 | n/a |
| 2 | -0.32 | -10.30 | 0.37 | 61 | -0.0630 | n/a |
| 3 | -0.43 | -10.63 | 0.51 | 68 | -0.0445 | n/a |
| 4 | -1.42 | -12.44 | 1.44 | 77 | -0.0728 | n/a |
| 5 | -0.46 | -6.37 | 0.55 | 72 | -0.0125 | n/a |
| 6 | -0.69 | -16.15 | 0.69 | 75 | -0.0230 | n/a |
| 7 | -0.14 | -5.88 | 0.22 | 71 | -0.0066 | n/a |
| 8 | -0.51 | -9.64 | 0.54 | 70 | -0.0438 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.2535)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -8.51 | -7.33 | 9.25 | -0.2056 |
| fees_2x | -10.09 | -8.58 | 10.77 | -0.2427 |
| latency_plus1 | -6.94 | -6.04 | 7.73 | -0.1691 |
| latency_plus2 | -6.00 | -7.49 | 6.23 | -0.1391 |
| latency_plus3 | -6.75 | -7.88 | 7.05 | -0.1551 |
| low_liquidity | -6.93 | -6.03 | 7.72 | -0.1689 |
| very_low_liquidity | -6.25 | -7.27 | 6.55 | -0.1461 |
| high_slippage | -7.13 | -6.18 | 7.92 | -0.1725 |
| extreme_slippage | -7.52 | -6.48 | 8.30 | -0.1797 |
| combined_adverse | -8.71 | -7.48 | 9.45 | -0.2094 |
| spread_widen_10bps | -7.30 | -7.06 | 7.95 | -0.1728 |
| spread_widen_25bps | -7.49 | -7.97 | 8.15 | -0.1711 |
| thin_book | -5.20 | -7.18 | 5.36 | -0.1202 |
| very_thin_book | -7.08 | -10.36 | 7.09 | -0.1498 |
| entry_spread_stress | -7.97 | -8.01 | 8.63 | -0.1804 |
| combined_market_deterioration | -10.52 | -10.60 | 10.72 | -0.2335 |
| severe_adverse | -11.55 | -12.21 | 11.87 | -0.2535 |

## Holdout Validation

- **Holdout bars**: 8818
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0026)
- **Trend**: ranging (efficiency: 0.0003)
- **Best holdout score**: -0.0229 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.2112 | -0.0229 | -0.72 | 0.77 | 154 |
| 1 | -0.0141 | -0.0374 | -1.03 | 1.28 | 314 |
| 2 | -0.0144 | -0.1067 | -3.81 | 3.87 | 349 |
| 3 | -0.0146 | -0.0619 | -1.81 | 2.15 | 432 |
| 4 | -0.0147 | -0.0748 | -3.11 | 3.21 | 548 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52156
- **Expected rows**: 52156
- **Missing rows**: 0
- **Forward-fill count**: 171
- **Forward-fill fraction**: 0.0032786256614771073
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0218 <= 0; recent PnL -0.5203% < 0
- **Objective score**: -0.021791494074507693
- **PnL %**: -0.5203446113350562
- **Trade count**: 108

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0718 <= 0; recent PnL -0.0490% < 0
- **Objective score**: -0.0718432551980956
- **PnL %**: -0.049032671641335845
- **Trade count**: 33

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1944 <= 0; recent PnL -0.0225% < 0
- **Objective score**: -0.19440910900128397
- **PnL %**: -0.022500082705051903
- **Trade count**: 14

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.21652177078881674
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1668, -0.2334 |
| sell_spread_base | -0.1938, -0.1807 |
| stop_loss | -0.2236, -0.2109 |
| take_profit | -0.2225, -0.1665 |
| executor_refresh_time | -0.1595, -0.1798 |
| cooldown_time | -0.1886, -0.2371 |
| total_amount_quote | -0.2242, -0.4983 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.33566161342476525
- **Max CV**: 1.3594039434923137
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2031 | 1.8478671205154744 | 3.306597977070459 | 2.5952779669906483 |
| buy_spread_ratio | 0.0532 | 2.43508368645307 | 2.90242663013455 | 2.616917172919435 |
| sell_spread_base | 0.6779 | 0.3103439329777103 | 2.059048509891632 | 0.9642455257316342 |
| sell_spread_ratio | 0.1288 | 1.2268254750099168 | 1.767750960062366 | 1.4247076602001607 |
| buy_side_weight | 0.3217 | 0.20496252575945687 | 0.43023695430833536 | 0.2897331415256449 |
| amount_skew | 0.1615 | 2.5252491744463077 | 3.7599447019563255 | 3.1480015839873596 |
| stop_loss | 1.3594 | 0.011316700388665253 | 0.2377349160020221 | 0.05418932834765502 |
| take_profit | 0.0457 | 0.005005826324404967 | 0.005630808881461506 | 0.005266821888804831 |
| executor_refresh_time | 0.3787 | 3175.0 | 14356.0 | 11516.4 |
| cooldown_time | 0.2373 | 3516.0 | 7126.0 | 5406.7 |
| total_amount_quote | 0.1248 | 700.4120374584827 | 984.317250383561 | 839.4221992073396 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
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
- walkforward_positive_majority: **FAIL**
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.021791494074507693 | FAIL |
| recent_pnl | >= 0 | -0.5203446113350562 | FAIL |
| recent_trades | >= 5 | 108 | PASS |
| worst_stress | > -10 | -0.2534682264514337 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.022881265159965806 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.2534682264514337 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.021791494074507693, pnl=-0.5203446113350562, trades=108, reason=recent objective score -0.0218 <= 0; recent PnL -0.5203% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.0718432551980956, pnl=-0.049032671641335845, trades=33, reason=recent objective score -0.0718 <= 0; recent PnL -0.0490% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.19440910900128397, pnl=-0.022500082705051903, trades=14, reason=recent objective score -0.1944 <= 0; recent PnL -0.0225% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.33566161342476525 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52156 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0218 <= 0; recent PnL -0.5203% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0718 <= 0; recent PnL -0.0490% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1944 <= 0; recent PnL -0.0225% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52156
- **Pre-release bars**: 44091
- **Dev bars**: 35273
- **Holdout bars**: 8818
- **Recent 28d bars**: 8065
- **Recent window start**: 1773367500

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-10T03:20:33.577535+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 11860
