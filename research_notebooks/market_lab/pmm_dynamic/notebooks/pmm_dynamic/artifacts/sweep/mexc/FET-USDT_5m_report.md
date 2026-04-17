# PMM Dynamic Optimization Report: mexc_FET-USDT_5m_sweep_v1

Generated: 2026-04-09 04:18:57 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T04:18:57.999868+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 4424 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: FET-USDT
- **interval**: 5m
- **n_candles**: 51871
- **dataset_hash**: 9f82068a74cf65c799bf846e023beeb382af2e536b6fbeeddca7751547ca2578
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 948.1792084287199
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.49832651894593 |
| buy_n_levels | 6 |
| buy_side_weight | 0.3208048541611766 |
| buy_spread_base | 0.7355627815144067 |
| buy_spread_ratio | 1.635005156171989 |
| cooldown_time | 6935 |
| executor_refresh_time | 5353 |
| macd_fast | 43 |
| macd_signal | 15 |
| macd_slow | 74 |
| natr_length | 31 |
| sell_n_levels | 6 |
| sell_spread_base | 2.0824360844413925 |
| sell_spread_ratio | 1.2388459629702966 |
| stop_loss | 0.018835801217970988 |
| take_profit | 0.06661087369119309 |
| time_limit | 86651 |
| total_amount_quote | 948.1792084287199 |
| trailing_stop_activation | 0.0036540080562502777 |
| trailing_stop_delta | 0.0011062600668601463 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 948.1792084287199 |
| Selected | 948.1792084287199 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 4.5448
- **Net PnL (quote)**: 43.0933
- **Sharpe Ratio**: 1.7962
- **Max Drawdown %**: 2.9739
- **Profit Factor**: 1.276921403642453
- **Trade Count**: 1464
- **Total Fees (quote)**: 18.0243
- **Maker Fees**: 9.0065
- **Taker Fees**: 9.0179
- **Fee Drag %**: 1.9009

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0079
- **PnL Component**: 0.0444
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0223
- **Fee Drag Component**: -0.0095
- **Inventory Component**: -0.0045
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0053**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.62 | -4.86 | 2.33 | 90 | -0.0362 | n/a |
| 1 | 1.00 | 4.61 | 0.96 | 101 | 0.0002 | n/a |
| 2 | 0.32 | 3.81 | 0.29 | 48 | -0.0074 | n/a |
| 3 | 0.94 | 3.90 | 1.16 | 87 | -0.0017 | n/a |
| 4 | 1.37 | 11.57 | 0.15 | 72 | 0.0118 | n/a |
| 5 | -0.71 | -2.53 | 2.13 | 70 | -0.0242 | n/a |
| 6 | 0.97 | 7.23 | 0.40 | 69 | 0.0059 | n/a |
| 7 | 0.96 | 6.69 | 0.27 | 46 | -0.0089 | n/a |
| 8 | 1.10 | 6.01 | 1.03 | 107 | 0.0020 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.3326)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3.59 | 1.43 | 3.03 | -0.0065 |
| fees_2x | 2.64 | 1.06 | 3.10 | -0.0209 |
| latency_plus1 | 3.79 | 1.51 | 2.99 | 0.0006 |
| latency_plus2 | 3.20 | 1.29 | 3.11 | -0.0059 |
| latency_plus3 | 4.11 | 1.68 | 3.03 | 0.0035 |
| low_liquidity | 4.60 | 1.81 | 2.97 | 0.0083 |
| very_low_liquidity | 3.49 | 1.40 | 3.18 | -0.0039 |
| high_slippage | 2.17 | 0.88 | 3.22 | -0.0170 |
| extreme_slippage | -2.59 | -0.98 | 5.27 | -0.0801 |
| combined_adverse | 0.68 | 0.30 | 3.29 | -0.0369 |
| spread_widen_10bps | -0.19 | -0.03 | 4.71 | -0.0513 |
| spread_widen_25bps | -7.15 | -2.23 | 7.66 | -0.1607 |
| thin_book | -6.18 | -2.67 | 7.57 | -0.1346 |
| very_thin_book | -7.08 | -2.06 | 8.72 | -0.1488 |
| entry_spread_stress | -2.11 | -0.75 | 5.32 | -0.0755 |
| combined_market_deterioration | -5.68 | -2.23 | 7.29 | -0.1358 |
| severe_adverse | -16.78 | -6.73 | 17.19 | -0.3326 |

## Holdout Validation

- **Holdout bars**: 8763
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0035)
- **Trend**: ranging (efficiency: 0.0006)
- **Best holdout score**: 0.0106 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1624 | 0.0064 | 1.63 | 1.13 | 114 |
| 1 | 0.0177 | -0.1035 | 1.92 | 2.08 | 188 |
| 2 | 0.0174 | -0.0139 | 0.41 | 1.98 | 83 |
| 3 | 0.0153 | 0.0106 | 2.13 | 0.90 | 202 |
| 4 | 0.0141 | -0.1529 | 0.83 | 2.60 | 193 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51871
- **Expected rows**: 51882
- **Missing rows**: 11
- **Forward-fill count**: 11
- **Forward-fill fraction**: 0.00021206454473597964
- **Longest gap (seconds)**: 3300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0193 <= 0
- **Objective score**: -0.01926344527429652
- **PnL %**: 0.3693694191648618
- **Trade count**: 207

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0321 <= 0; recent PnL -0.9678% < 0
- **Objective score**: -0.0321072853904952
- **PnL %**: -0.967768230540723
- **Trade count**: 96

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0720 <= 0; recent PnL -0.3263% < 0
- **Objective score**: -0.07199176954922332
- **PnL %**: -0.3263283200264553
- **Trade count**: 36

## Sensitivity Analysis

- **Sensitivity penalty**: 0.7142857142857143
- **Baseline score**: 0.015444898142992847
- **Sign flips**: 5
- **Collapse count**: 5
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0136, 0.0388 |
| sell_spread_base | 0.0119, -0.0326 |
| stop_loss | 0.0095, -0.0022 |
| take_profit | 0.0154, 0.0154 |
| executor_refresh_time | 0.0163, -0.0656 |
| cooldown_time | -0.0338, 0.0142 |
| total_amount_quote | 0.0154, -0.0173 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.34210750981604926
- **Max CV**: 0.8952389395854712
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3470 | 0.2671625107491862 | 1.1080666405695743 | 0.6600282040172201 |
| buy_spread_ratio | 0.1732 | 1.2027686116819534 | 1.9741674271447822 | 1.440312356643301 |
| sell_spread_base | 0.4899 | 0.8180356683775983 | 4.315305583429915 | 2.286985555267764 |
| sell_spread_ratio | 0.2325 | 1.2013345038112442 | 2.3563519964464703 | 1.6964837727997004 |
| buy_side_weight | 0.2518 | 0.30722042249265125 | 0.7192668328389027 | 0.5039297714011518 |
| amount_skew | 0.1983 | 2.1519175723822 | 3.775883893218312 | 2.8711440596580617 |
| stop_loss | 0.3872 | 0.031343215892935476 | 0.10091970517328525 | 0.05590345607043153 |
| take_profit | 0.8952 | 0.006735465038749431 | 0.07120504827936648 | 0.03003450224220634 |
| executor_refresh_time | 0.2265 | 6832.0 | 12931.0 | 10105.4 |
| cooldown_time | 0.2459 | 3505.0 | 7085.0 | 5590.4 |
| total_amount_quote | 0.3156 | 215.77380007271125 | 667.9604548792561 | 485.29842757013995 |

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
- holdout_passed: PASS
- holdout_no_collapse: PASS
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.01926344527429652 | FAIL |
| recent_pnl | >= 0 | 0.3693694191648618 | PASS |
| recent_trades | >= 5 | 207 | PASS |
| worst_stress | > -10 | -0.33261831427680616 | PASS |
| sensitivity_penalty | < 0.50 | 0.7142857142857143 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0064 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.33261831427680616 |
| sensitivity | FAIL | penalty=0.7142857142857143 |
| recent_28d | FAIL | score=-0.01926344527429652, pnl=0.3693694191648618, trades=207, reason=recent objective score -0.0193 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.0321072853904952, pnl=-0.967768230540723, trades=96, reason=recent objective score -0.0321 <= 0; recent PnL -0.9678% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.07199176954922332, pnl=-0.3263283200264553, trades=36, reason=recent objective score -0.0720 <= 0; recent PnL -0.3263% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.34210750981604926 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51871 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0193 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0321 <= 0; recent PnL -0.9678% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0720 <= 0; recent PnL -0.3263% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51871
- **Pre-release bars**: 43817
- **Dev bars**: 35054
- **Holdout bars**: 8763
- **Recent 28d bars**: 8054
- **Recent window start**: 1773284700

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T04:18:57.999868+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 4424
