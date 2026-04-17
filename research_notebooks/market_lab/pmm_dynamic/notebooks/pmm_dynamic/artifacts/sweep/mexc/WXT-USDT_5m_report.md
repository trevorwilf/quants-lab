# PMM Dynamic Optimization Report: mexc_WXT-USDT_5m_sweep_v1

Generated: 2026-04-09 11:30:32 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T11:30:32.196686+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 11517 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: WXT-USDT
- **interval**: 5m
- **n_candles**: 51914
- **dataset_hash**: 8371952d74cacafcb025e17a45672fa7448c504f4906efad7cb2c7bb9624f02b
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 544.6167126440893
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.3620583396578654 |
| buy_n_levels | 10 |
| buy_side_weight | 0.7656336483508299 |
| buy_spread_base | 0.4811801572836414 |
| buy_spread_ratio | 1.2158480802540415 |
| cooldown_time | 4650 |
| executor_refresh_time | 1473 |
| macd_fast | 23 |
| macd_signal | 18 |
| macd_slow | 25 |
| natr_length | 16 |
| sell_n_levels | 9 |
| sell_spread_base | 4.428518665984581 |
| sell_spread_ratio | 2.4593301748511918 |
| stop_loss | 0.017628204524247796 |
| take_profit | 0.05942575626676328 |
| time_limit | 47370 |
| total_amount_quote | 544.6167126440893 |
| trailing_stop_activation | 0.02223153502986184 |
| trailing_stop_delta | 0.006070478730483843 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 544.6167126440893 |
| Selected | 544.6167126440893 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 4.9281
- **Net PnL (quote)**: 26.8390
- **Sharpe Ratio**: 2.3905
- **Max Drawdown %**: 1.7991
- **Profit Factor**: 2.2229592500218653
- **Trade Count**: 193
- **Total Fees (quote)**: 1.7708
- **Maker Fees**: 0.8825
- **Taker Fees**: 0.8882
- **Fee Drag %**: 0.3251

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0328
- **PnL Component**: 0.0481
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0135
- **Fee Drag Component**: -0.0016
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0979**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.05 | -2.10 | 0.15 | 5 | -0.4549 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 1.17 | 4.50 | 0.85 | 78 | -0.0098 | n/a |
| 4 | -1.01 | -7.28 | 1.49 | 37 | -0.0739 | n/a |
| 5 | 0.34 | 1.51 | 1.03 | 77 | -0.0675 | n/a |
| 6 | -1.92 | -7.07 | 2.74 | 130 | -0.1071 | n/a |
| 7 | 0.24 | 1.49 | 0.73 | 88 | -0.0260 | n/a |
| 8 | -0.35 | -3.16 | 0.52 | 10 | -0.3781 | n/a |

## Stress Test Results

Worst Scenario: **very_thin_book** (score: -0.0442)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 4.76 | 2.31 | 1.82 | 0.0302 |
| fees_2x | 4.60 | 2.24 | 1.85 | 0.0277 |
| latency_plus1 | 5.24 | 2.59 | 1.94 | 0.0348 |
| latency_plus2 | 5.23 | 2.59 | 1.94 | 0.0346 |
| latency_plus3 | 3.79 | 1.84 | 2.83 | 0.0144 |
| low_liquidity | 4.28 | 2.14 | 1.93 | 0.0257 |
| very_low_liquidity | 3.56 | 1.78 | 2.58 | 0.0136 |
| high_slippage | 4.52 | 2.20 | 1.88 | 0.0283 |
| extreme_slippage | 3.69 | 1.80 | 2.04 | 0.0192 |
| combined_adverse | 3.88 | 1.97 | 2.27 | 0.0187 |
| spread_widen_10bps | 5.01 | 2.37 | 1.84 | 0.0333 |
| spread_widen_25bps | 3.70 | 1.76 | 2.71 | 0.0141 |
| thin_book | 3.84 | 2.04 | 2.38 | 0.0182 |
| very_thin_book | -0.50 | -0.46 | 2.38 | -0.0442 |
| entry_spread_stress | 4.86 | 2.30 | 1.86 | 0.0316 |
| combined_market_deterioration | 3.78 | 1.80 | 2.39 | 0.0164 |
| severe_adverse | 1.56 | 0.93 | 2.55 | -0.0066 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0022)
- **Trend**: ranging (efficiency: 0.0006)
- **Best holdout score**: -0.1049 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0057 | -0.1049 | -1.95 | 3.28 | 231 |
| 1 | -0.0421 | -0.2282 | -4.36 | 6.39 | 318 |
| 2 | -0.0441 | -0.3238 | -5.34 | 6.97 | 245 |
| 3 | -0.0444 | -0.2144 | -0.29 | 4.16 | 273 |
| 4 | -0.0459 | -0.2868 | 0.37 | 6.33 | 238 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51914
- **Expected rows**: 51914
- **Missing rows**: 0
- **Forward-fill count**: 684
- **Forward-fill fraction**: 0.013175636629810842
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3781 <= 0; recent PnL -0.3520% < 0
- **Objective score**: -0.3780595863069399
- **PnL %**: -0.35198555039705093
- **Trade count**: 10

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3781 <= 0; recent PnL -0.3520% < 0
- **Objective score**: -0.37808396174570646
- **PnL %**: -0.35198555039705093
- **Trade count**: 10

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: -0.1304681269290008
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1167, -0.1591 |
| sell_spread_base | -0.1305, -0.1305 |
| stop_loss | -0.1429, -0.1835 |
| take_profit | -0.1305, -0.1305 |
| executor_refresh_time | -0.2580, -0.1305 |
| cooldown_time | -0.2723, -0.1999 |
| total_amount_quote | -0.1337, -0.1265 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.40774770889037426
- **Max CV**: 0.9570011138399136
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1981 | 0.20310775992141136 | 0.3387339564250696 | 0.2498239316674337 |
| buy_spread_ratio | 0.0339 | 1.2007187957329901 | 1.325800763020613 | 1.2503111481389158 |
| sell_spread_base | 0.6302 | 0.23042893722583394 | 3.576507948312127 | 1.8572191807043343 |
| sell_spread_ratio | 0.1667 | 1.4925172985608797 | 2.7713339621624145 | 2.3898390823309303 |
| buy_side_weight | 0.1462 | 0.46375278868988723 | 0.7938159417970918 | 0.6813239054599277 |
| amount_skew | 0.1305 | 1.1760833272332192 | 1.7268033217593906 | 1.395789487375874 |
| stop_loss | 0.9570 | 0.010051418168547422 | 0.18204215014495606 | 0.07366308444060547 |
| take_profit | 0.6607 | 0.005739980309586433 | 0.07881812222800001 | 0.036434094383410685 |
| executor_refresh_time | 0.4972 | 463.0 | 3342.0 | 1837.6 |
| cooldown_time | 0.7358 | 112.0 | 3279.0 | 1238.0 |
| total_amount_quote | 0.3288 | 269.19122777260947 | 994.4056790965025 | 734.3872570829648 |

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
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.3780595863069399 | FAIL |
| recent_pnl | >= 0 | -0.35198555039705093 | FAIL |
| recent_trades | >= 5 | 10 | PASS |
| worst_stress | > -10 | -0.044230779377474834 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.10491666674279695 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_thin_book score=-0.044230779377474834 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | FAIL | score=-0.3780595863069399, pnl=-0.35198555039705093, trades=10, reason=recent objective score -0.3781 <= 0; recent PnL -0.3520% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.37808396174570646, pnl=-0.35198555039705093, trades=10, reason=recent objective score -0.3781 <= 0; recent PnL -0.3520% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.40774770889037426 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51914 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3781 <= 0; recent PnL -0.3520% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3781 <= 0; recent PnL -0.3520% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51914
- **Pre-release bars**: 43849
- **Dev bars**: 35080
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065
- **Recent window start**: 1773294300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T11:30:32.196686+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 11517
