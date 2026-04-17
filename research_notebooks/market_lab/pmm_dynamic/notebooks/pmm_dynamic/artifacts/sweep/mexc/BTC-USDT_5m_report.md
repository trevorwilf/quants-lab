# PMM Dynamic Optimization Report: mexc_BTC-USDT_5m_sweep_v1

Generated: 2026-04-09 02:36:05 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T02:36:05.950471+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 12167 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 51844
- **dataset_hash**: 53595cd86a0b11bdef76cc7c03326bf24f7b861e952d98346ff97ff19d053f9f
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 997.5947816570425
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.0835866917291925 |
| buy_n_levels | 5 |
| buy_side_weight | 0.25639162599723914 |
| buy_spread_base | 2.964771860889494 |
| buy_spread_ratio | 2.5578751043270476 |
| cooldown_time | 4415 |
| executor_refresh_time | 12072 |
| macd_fast | 14 |
| macd_signal | 30 |
| macd_slow | 57 |
| natr_length | 41 |
| sell_n_levels | 9 |
| sell_spread_base | 2.319095213392774 |
| sell_spread_ratio | 2.2827334994924673 |
| stop_loss | 0.03087521613619568 |
| take_profit | 0.006575952077553121 |
| time_limit | 165088 |
| total_amount_quote | 997.5947816570425 |
| trailing_stop_activation | 0.022484179758705466 |
| trailing_stop_delta | 0.005122242840185867 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 997.5947816570425 |
| Selected | 997.5947816570425 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -6.3664
- **Net PnL (quote)**: -63.5113
- **Sharpe Ratio**: -4.3449
- **Max Drawdown %**: 7.7443
- **Profit Factor**: 0.7713823955467745
- **Trade Count**: 1003
- **Total Fees (quote)**: 6.2758
- **Maker Fees**: 5.5381
- **Taker Fees**: 0.7377
- **Fee Drag %**: 0.6291
- **TP Min-Notional Failures**: 1686 :warning:
  > 1686 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1665
- **PnL Component**: -0.0658
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0581
- **Fee Drag Component**: -0.0031
- **Inventory Component**: -0.0391
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0115**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.14 | -6.69 | 0.26 | 62 | -0.0093 | n/a |
| 1 | -0.11 | -3.71 | 0.19 | 64 | -0.0085 | n/a |
| 2 | 0.02 | 1.37 | 0.06 | 59 | -0.0061 | n/a |
| 3 | 0.03 | 3.53 | 0.02 | 61 | -0.0089 | n/a |
| 4 | -0.33 | -7.94 | 0.37 | 69 | -0.0388 | n/a |
| 5 | -0.06 | -2.68 | 0.09 | 62 | -0.0029 | n/a |
| 6 | -0.21 | -6.47 | 0.28 | 64 | -0.0200 | n/a |
| 7 | -0.10 | -3.71 | 0.16 | 57 | -0.0038 | n/a |
| 8 | -0.17 | -6.45 | 0.21 | 68 | -0.0311 | n/a |

## Stress Test Results

Worst Scenario: **spread_widen_25bps** (score: -0.2867)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -6.68 | -4.56 | 8.03 | -0.1736 |
| fees_2x | -7.00 | -4.77 | 8.32 | -0.1808 |
| latency_plus1 | -6.39 | -4.36 | 7.76 | -0.1668 |
| latency_plus2 | -6.38 | -4.37 | 7.75 | -0.1667 |
| latency_plus3 | -5.85 | -4.16 | 7.01 | -0.1552 |
| low_liquidity | -6.37 | -4.34 | 7.74 | -0.1665 |
| very_low_liquidity | -6.37 | -4.34 | 7.74 | -0.1665 |
| high_slippage | -6.55 | -4.47 | 7.91 | -0.1698 |
| extreme_slippage | -6.92 | -4.71 | 8.25 | -0.1764 |
| combined_adverse | -6.89 | -4.69 | 8.21 | -0.1773 |
| spread_widen_10bps | -6.77 | -4.28 | 8.31 | -0.1798 |
| spread_widen_25bps | -11.42 | -5.35 | 13.48 | -0.2867 |
| thin_book | -6.75 | -5.71 | 7.56 | -0.1632 |
| very_thin_book | -6.75 | -6.25 | 7.33 | -0.1550 |
| entry_spread_stress | -8.88 | -4.29 | 11.06 | -0.2387 |
| combined_market_deterioration | -8.00 | -5.43 | 9.41 | -0.2003 |
| severe_adverse | -11.00 | -6.65 | 12.18 | -0.2586 |

## Holdout Validation

- **Holdout bars**: 8760
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0022)
- **Trend**: ranging (efficiency: 0.0005)
- **Best holdout score**: -0.0130 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.2266 | -0.0130 | -0.36 | 0.43 | 133 |
| 1 | -0.0076 | -0.0259 | -0.43 | 0.86 | 248 |
| 2 | -0.0076 | -0.0348 | -0.94 | 1.14 | 410 |
| 3 | -0.0077 | -0.0399 | -1.31 | 1.33 | 441 |
| 4 | -0.0080 | -0.0569 | -0.86 | 1.54 | 551 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51844
- **Expected rows**: 51866
- **Missing rows**: 22
- **Forward-fill count**: 530
- **Forward-fill fraction**: 0.010222976622174215
- **Longest gap (seconds)**: 2700

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0095 <= 0; recent PnL -0.1235% < 0
- **Objective score**: -0.00947444042627691
- **PnL %**: -0.12345678703211346
- **Trade count**: 121

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0250 <= 0; recent PnL -0.0219% < 0
- **Objective score**: -0.025042775934742252
- **PnL %**: -0.021910287098883513
- **Trade count**: 60

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1056 <= 0
- **Objective score**: -0.10557292306973552
- **PnL %**: 0.003303002185583334
- **Trade count**: 24

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.18017400872163747
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.4242, -0.2494 |
| sell_spread_base | -0.1570, -0.1931 |
| stop_loss | -0.2235, -0.2057 |
| take_profit | -0.1551, -0.1609 |
| executor_refresh_time | -0.1922, -0.1649 |
| cooldown_time | -0.2274, -0.2432 |
| total_amount_quote | -0.1635, -0.1961 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.291193730242215
- **Max CV**: 0.7963583524592249
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1768 | 2.0364192702823405 | 4.165438311063939 | 3.223584903827491 |
| buy_spread_ratio | 0.1388 | 1.7718685062564994 | 2.878146784284153 | 2.346882509160354 |
| sell_spread_base | 0.7964 | 0.23878839766201415 | 2.319095213392774 | 0.8227574964114691 |
| sell_spread_ratio | 0.2392 | 1.205889657293519 | 2.618276102407358 | 1.876395251375892 |
| buy_side_weight | 0.2381 | 0.20898313281985187 | 0.3813951338449447 | 0.2560803692687324 |
| amount_skew | 0.1350 | 2.367407229180811 | 3.5652630131677077 | 2.7823275793891877 |
| stop_loss | 0.3522 | 0.011400962552074513 | 0.03087521613619568 | 0.01951054903349148 |
| take_profit | 0.2905 | 0.005276648584226054 | 0.011149759118322224 | 0.007296775692487436 |
| executor_refresh_time | 0.3340 | 3444.0 | 13496.0 | 9928.7 |
| cooldown_time | 0.3737 | 1288.0 | 6859.0 | 4876.4 |
| total_amount_quote | 0.1286 | 672.2047203542879 | 997.5947816570425 | 886.8181944187949 |

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
| recent_objective | > 0 | -0.00947444042627691 | FAIL |
| recent_pnl | >= 0 | -0.12345678703211346 | FAIL |
| recent_trades | >= 5 | 121 | PASS |
| worst_stress | > -10 | -0.28665327952247527 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.013014685629952187 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=spread_widen_25bps score=-0.28665327952247527 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.00947444042627691, pnl=-0.12345678703211346, trades=121, reason=recent objective score -0.0095 <= 0; recent PnL -0.1235% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.025042775934742252, pnl=-0.021910287098883513, trades=60, reason=recent objective score -0.0250 <= 0; recent PnL -0.0219% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.10557292306973552, pnl=0.003303002185583334, trades=24, reason=recent objective score -0.1056 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.291193730242215 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51844 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0095 <= 0; recent PnL -0.1235% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0250 <= 0; recent PnL -0.0219% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1056 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51844
- **Pre-release bars**: 43801
- **Dev bars**: 35041
- **Holdout bars**: 8760
- **Recent 28d bars**: 8043
- **Recent window start**: 1773280200

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T02:36:05.950471+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 12167
