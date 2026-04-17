# PMM Dynamic Optimization Report: nonkyc_LINK-USDT_5m_sweep_v1

Generated: 2026-04-09 21:19:09 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T21:19:09.351999+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 5659 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: LINK-USDT
- **interval**: 5m
- **n_candles**: 52057
- **dataset_hash**: eb78260009e21d37a0bb2824f16c2bdda587bcb94b2ef74e15d6efc276a2b886
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 849.0862745335717
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.768023060330083 |
| buy_n_levels | 10 |
| buy_side_weight | 0.2552578562228426 |
| buy_spread_base | 3.515287823750024 |
| buy_spread_ratio | 2.23270580806694 |
| cooldown_time | 5540 |
| executor_refresh_time | 8681 |
| macd_fast | 19 |
| macd_signal | 5 |
| macd_slow | 50 |
| natr_length | 20 |
| sell_n_levels | 7 |
| sell_spread_base | 4.800502857209187 |
| sell_spread_ratio | 2.7881982022982545 |
| stop_loss | 0.013204618406456821 |
| take_profit | 0.005797542964624695 |
| time_limit | 18642 |
| total_amount_quote | 849.0862745335717 |
| trailing_stop_activation | 0.05831417342996436 |
| trailing_stop_delta | 0.02857011108023868 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 849.0862745335717 |
| Selected | 849.0862745335717 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.6365
- **Net PnL (quote)**: -22.3861
- **Sharpe Ratio**: -8.5198
- **Max Drawdown %**: 2.6582
- **Profit Factor**: 0.36277465714798757
- **Trade Count**: 632
- **Total Fees (quote)**: 12.8614
- **Maker Fees**: 8.8197
- **Taker Fees**: 4.0417
- **Fee Drag %**: 1.5147
- **TP Min-Notional Failures**: 242 :warning:
  > 242 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0576
- **PnL Component**: -0.0267
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0199
- **Fee Drag Component**: -0.0076
- **Inventory Component**: -0.0033
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0181**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.07 | -3.08 | 0.17 | 43 | -0.0327 | n/a |
| 1 | -0.44 | -13.94 | 0.45 | 46 | -0.0267 | n/a |
| 2 | -0.13 | -7.80 | 0.15 | 34 | -0.1193 | n/a |
| 3 | 0.03 | 2.56 | 0.04 | 50 | -0.0026 | n/a |
| 4 | -0.38 | -5.80 | 0.41 | 54 | -0.0129 | n/a |
| 5 | -0.30 | -10.42 | 0.31 | 64 | -0.0084 | n/a |
| 6 | -0.31 | -9.78 | 0.35 | 83 | -0.0100 | n/a |
| 7 | -0.11 | -8.68 | 0.13 | 52 | -0.0048 | n/a |
| 8 | -1.26 | -13.09 | 1.26 | 57 | -0.0943 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0966)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -3.39 | -10.70 | 3.41 | -0.0748 |
| fees_2x | -4.15 | -12.71 | 4.16 | -0.0922 |
| latency_plus1 | -2.64 | -8.52 | 2.66 | -0.0576 |
| latency_plus2 | -2.64 | -8.52 | 2.66 | -0.0576 |
| latency_plus3 | -2.67 | -8.61 | 2.69 | -0.0582 |
| low_liquidity | -2.64 | -8.53 | 2.66 | -0.0577 |
| very_low_liquidity | -2.96 | -8.81 | 2.99 | -0.0635 |
| high_slippage | -2.76 | -8.82 | 2.77 | -0.0597 |
| extreme_slippage | -2.99 | -9.40 | 3.01 | -0.0639 |
| combined_adverse | -3.52 | -10.97 | 3.53 | -0.0771 |
| spread_widen_10bps | -2.95 | -9.22 | 3.00 | -0.0620 |
| spread_widen_25bps | -2.88 | -9.90 | 2.89 | -0.0605 |
| thin_book | -2.97 | -8.67 | 3.01 | -0.0609 |
| very_thin_book | -2.29 | -6.92 | 2.32 | -0.0882 |
| entry_spread_stress | -2.77 | -8.63 | 2.77 | -0.0583 |
| combined_market_deterioration | -4.06 | -10.64 | 4.13 | -0.0872 |
| severe_adverse | -4.44 | -13.69 | 4.46 | -0.0966 |

## Holdout Validation

- **Holdout bars**: 8798
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0026)
- **Trend**: ranging (efficiency: 0.0024)
- **Best holdout score**: -0.0120 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0771 | -0.0120 | -0.45 | 0.45 | 142 |
| 1 | -0.0060 | -0.0863 | -2.58 | 2.88 | 429 |
| 2 | -0.0060 | -0.0427 | -1.47 | 1.52 | 421 |
| 3 | -0.0064 | -0.0570 | -1.98 | 2.13 | 487 |
| 4 | -0.0066 | -0.1107 | -3.61 | 3.73 | 625 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52057
- **Expected rows**: 52059
- **Missing rows**: 2
- **Forward-fill count**: 536
- **Forward-fill fraction**: 0.010296405862804234
- **Longest gap (seconds)**: 900

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1179 <= 0; recent PnL -1.7382% < 0
- **Objective score**: -0.11788456192798992
- **PnL %**: -1.7381738179993964
- **Trade count**: 96

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1578 <= 0; recent PnL -0.5162% < 0
- **Objective score**: -0.15783711842911227
- **PnL %**: -0.5161688380658132
- **Trade count**: 39

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2541 <= 0; recent PnL -0.1790% < 0
- **Objective score**: -0.25411740312633163
- **PnL %**: -0.1790246043677997
- **Trade count**: 20

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.12406043921102397
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1076, -0.1285 |
| sell_spread_base | -0.1093, -0.1452 |
| stop_loss | -0.1264, -0.1238 |
| take_profit | -0.1178, -0.1237 |
| executor_refresh_time | -0.1238, -0.1436 |
| cooldown_time | -0.1144, -0.1225 |
| total_amount_quote | -0.1167, -0.1249 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.18504078280183853
- **Max CV**: 0.5950317247466659
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1236 | 2.1946947512646315 | 3.2745169561145784 | 2.744442326018052 |
| buy_spread_ratio | 0.1319 | 1.7361926029341954 | 2.7177183002358 | 2.307325230539417 |
| sell_spread_base | 0.5950 | 0.20744909052324328 | 0.8669174912396671 | 0.3868453722174486 |
| sell_spread_ratio | 0.1260 | 1.9914888546573573 | 2.994175265102116 | 2.510296067993445 |
| buy_side_weight | 0.1766 | 0.2004630022663089 | 0.3222174501347003 | 0.25654185428751275 |
| amount_skew | 0.1302 | 2.2855146151089416 | 3.5259109177493047 | 2.776764023760033 |
| stop_loss | 0.1719 | 0.011323089514787018 | 0.020370994922331593 | 0.016050964558519773 |
| take_profit | 0.1257 | 0.0050883329995685496 | 0.0072534078608892045 | 0.0058017059451945345 |
| executor_refresh_time | 0.1757 | 8630.0 | 13969.0 | 11027.0 |
| cooldown_time | 0.1880 | 3908.0 | 6728.0 | 5447.8 |
| total_amount_quote | 0.0909 | 757.1324685512915 | 984.0371954533848 | 904.9390230934911 |

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
| recent_objective | > 0 | -0.11788456192798992 | FAIL |
| recent_pnl | >= 0 | -1.7381738179993964 | FAIL |
| recent_trades | >= 5 | 96 | PASS |
| worst_stress | > -10 | -0.09657339012326265 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.011979782543026835 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.09657339012326265 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.11788456192798992, pnl=-1.7381738179993964, trades=96, reason=recent objective score -0.1179 <= 0; recent PnL -1.7382% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.15783711842911227, pnl=-0.5161688380658132, trades=39, reason=recent objective score -0.1578 <= 0; recent PnL -0.5162% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.25411740312633163, pnl=-0.1790246043677997, trades=20, reason=recent objective score -0.2541 <= 0; recent PnL -0.1790% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.18504078280183853 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52057 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1179 <= 0; recent PnL -1.7382% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1578 <= 0; recent PnL -0.5162% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2541 <= 0; recent PnL -0.1790% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52057
- **Pre-release bars**: 43994
- **Dev bars**: 35196
- **Holdout bars**: 8798
- **Recent 28d bars**: 8063
- **Recent window start**: 1773338400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T21:19:09.351999+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 5659
