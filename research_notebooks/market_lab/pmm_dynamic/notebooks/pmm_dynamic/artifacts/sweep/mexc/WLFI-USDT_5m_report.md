# PMM Dynamic Optimization Report: mexc_WLFI-USDT_5m_sweep_v1

Generated: 2026-04-09 10:57:12 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T10:57:12.959737+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 3825 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: WLFI-USDT
- **interval**: 5m
- **n_candles**: 51921
- **dataset_hash**: 6d3a7bb6f3df12beccadcabf855c1a6d39c87f293cb7fa199f9bc3a2b26e7643
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 523.6617540805818
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.096105098065094 |
| buy_n_levels | 7 |
| buy_side_weight | 0.48260234688611214 |
| buy_spread_base | 1.1147437252498313 |
| buy_spread_ratio | 1.645159992315123 |
| cooldown_time | 1557 |
| executor_refresh_time | 960 |
| macd_fast | 41 |
| macd_signal | 23 |
| macd_slow | 56 |
| natr_length | 42 |
| sell_n_levels | 8 |
| sell_spread_base | 1.938103240513738 |
| sell_spread_ratio | 1.4096933585366114 |
| stop_loss | 0.021276582915608584 |
| take_profit | 0.005005061102131345 |
| time_limit | 76569 |
| total_amount_quote | 523.6617540805818 |
| trailing_stop_activation | 0.0409847389966078 |
| trailing_stop_delta | 0.0029956237629311833 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 523.6617540805818 |
| Selected | 523.6617540805818 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3.0103
- **Net PnL (quote)**: 15.7637
- **Sharpe Ratio**: 1.5782
- **Max Drawdown %**: 1.5522
- **Profit Factor**: 1.6455874660952685
- **Trade Count**: 575
- **Total Fees (quote)**: 2.9758
- **Maker Fees**: 2.5837
- **Taker Fees**: 0.3921
- **Fee Drag %**: 0.5683
- **TP Min-Notional Failures**: 2459 :warning:
  > 2459 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0068
- **PnL Component**: 0.0297
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0116
- **Fee Drag Component**: -0.0028
- **Inventory Component**: -0.0082
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0425**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.14 | 2.51 | 0.17 | 71 | -0.0003 | n/a |
| 1 | -0.04 | -1.14 | 0.15 | 42 | -0.0337 | n/a |
| 2 | 0.08 | 8.90 | 0.01 | 7 | -0.1713 | n/a |
| 3 | 0.87 | 8.99 | 0.11 | 56 | 0.0074 | n/a |
| 4 | 0.39 | 3.60 | 0.35 | 64 | 0.0008 | n/a |
| 5 | 0.99 | 2.59 | 1.07 | 78 | 0.0012 | n/a |
| 6 | 0.39 | 2.43 | 0.47 | 43 | -0.0280 | n/a |
| 7 | 0.06 | 4.06 | 0.03 | 23 | -0.1078 | n/a |
| 8 | 0.34 | 4.35 | 0.15 | 21 | -0.1140 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0530)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2.73 | 1.43 | 1.60 | 0.0023 |
| fees_2x | 2.44 | 1.29 | 1.64 | -0.0023 |
| latency_plus1 | 2.95 | 1.55 | 1.60 | 0.0060 |
| latency_plus2 | 2.31 | 1.21 | 1.49 | 0.0010 |
| latency_plus3 | 0.02 | 0.04 | 2.41 | -0.0266 |
| low_liquidity | 3.01 | 1.58 | 1.55 | 0.0068 |
| very_low_liquidity | 3.01 | 1.58 | 1.55 | 0.0068 |
| high_slippage | 2.82 | 1.49 | 1.57 | 0.0048 |
| extreme_slippage | 2.45 | 1.31 | 1.62 | 0.0008 |
| combined_adverse | 2.49 | 1.32 | 1.66 | -0.0004 |
| spread_widen_10bps | 3.03 | 1.59 | 1.60 | 0.0047 |
| spread_widen_25bps | 2.16 | 1.01 | 2.28 | -0.0096 |
| thin_book | -1.46 | -0.91 | 3.78 | -0.0521 |
| very_thin_book | 1.23 | 1.58 | 0.70 | 0.0027 |
| entry_spread_stress | 3.37 | 1.62 | 1.98 | 0.0048 |
| combined_market_deterioration | -0.93 | -0.54 | 3.66 | -0.0515 |
| severe_adverse | -1.66 | -1.07 | 4.06 | -0.0530 |

## Holdout Validation

- **Holdout bars**: 8779
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0043)
- **Trend**: ranging (efficiency: 0.0048)
- **Best holdout score**: 0.0629 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0231 | 0.0027 | 0.67 | 0.47 | 75 |
| 1 | 0.0084 | 0.0285 | 3.51 | 0.67 | 58 |
| 2 | 0.0081 | 0.0202 | 2.93 | 0.67 | 111 |
| 3 | 0.0077 | 0.0629 | 7.56 | 0.66 | 108 |
| 4 | 0.0068 | -0.0072 | 1.63 | 1.32 | 99 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51921
- **Expected rows**: 51964
- **Missing rows**: 43
- **Forward-fill count**: 46
- **Forward-fill fraction**: 0.0008859613643805011
- **Longest gap (seconds)**: 5400

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.0017348727373553492
- **PnL %**: 0.33681043927188214
- **Trade count**: 52

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0941 <= 0
- **Objective score**: -0.09407769698163711
- **PnL %**: 0.015218872127156566
- **Trade count**: 28

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1372 <= 0
- **Objective score**: -0.13724888227268933
- **PnL %**: 0.015468775968971985
- **Trade count**: 16

## Sensitivity Analysis

- **Sensitivity penalty**: 0.35714285714285715
- **Baseline score**: 0.014508170836137254
- **Sign flips**: 1
- **Collapse count**: 4
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0200, 0.0230 |
| sell_spread_base | 0.0179, 0.0061 |
| stop_loss | 0.0142, 0.0044 |
| take_profit | 0.0194, 0.0094 |
| executor_refresh_time | 0.0145, -0.0025 |
| cooldown_time | 0.0145, 0.0177 |
| total_amount_quote | 0.0019, 0.0144 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3370889800223237
- **Max CV**: 0.6995266798384034
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1999 | 0.9549583503313931 | 1.6951117639938882 | 1.3815958476665382 |
| buy_spread_ratio | 0.0820 | 1.2005930887888498 | 1.5184142526243642 | 1.2996222545501155 |
| sell_spread_base | 0.6247 | 0.4744871265895531 | 2.720123159536105 | 1.2924572853125282 |
| sell_spread_ratio | 0.1860 | 1.312399114258148 | 2.281585531310244 | 1.8617806547776268 |
| buy_side_weight | 0.0822 | 0.6133465470881035 | 0.7896301769269225 | 0.707709757810782 |
| amount_skew | 0.2191 | 2.052356863051024 | 3.833618822313725 | 3.1424738191427437 |
| stop_loss | 0.4505 | 0.010658873104453886 | 0.04177126750123954 | 0.023553081753486773 |
| take_profit | 0.6995 | 0.0060722300408878075 | 0.031175961025611567 | 0.012706501872241663 |
| executor_refresh_time | 0.6649 | 353.0 | 1734.0 | 642.9 |
| cooldown_time | 0.2059 | 1268.0 | 2279.0 | 1586.6 |
| total_amount_quote | 0.2933 | 283.50952101113563 | 928.9797037529959 | 657.567246894246 |

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
- sensitivity_stable: PASS
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.0017348727373553492 | PASS |
| recent_pnl | >= 0 | 0.33681043927188214 | PASS |
| recent_trades | >= 5 | 52 | PASS |
| worst_stress | > -10 | -0.053020546088972685 | PASS |
| sensitivity_penalty | < 0.50 | 0.35714285714285715 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0027 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.053020546088972685 |
| sensitivity | PASS | penalty=0.35714285714285715 |
| recent_28d | PASS | score=0.0017348727373553492, pnl=0.33681043927188214, trades=52, reason= |
| recent_14d_info | FAIL | informational only; score=-0.09407769698163711, pnl=0.015218872127156566, trades=28, reason=recent objective score -0.0941 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.13724888227268933, pnl=0.015468775968971985, trades=16, reason=recent objective score -0.1372 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3370889800223237 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51921 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0941 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1372 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51921
- **Pre-release bars**: 43899
- **Dev bars**: 35120
- **Holdout bars**: 8779
- **Recent 28d bars**: 8022
- **Recent window start**: 1773309300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T10:57:12.959737+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 3825
