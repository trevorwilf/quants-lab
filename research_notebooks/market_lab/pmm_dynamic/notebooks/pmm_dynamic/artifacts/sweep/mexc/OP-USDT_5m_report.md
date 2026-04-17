# PMM Dynamic Optimization Report: mexc_OP-USDT_5m_sweep_v1

Generated: 2026-04-09 06:11:01 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T06:11:01.614705+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 1631 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: OP-USDT
- **interval**: 5m
- **n_candles**: 51871
- **dataset_hash**: 9b70e745f0b516bb63af92420bbedbf5e10021b302b45198ceb5fefcaa122b68
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 590.017116521971
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.007199086975323 |
| buy_n_levels | 8 |
| buy_side_weight | 0.47809699050463506 |
| buy_spread_base | 1.0695933927914516 |
| buy_spread_ratio | 1.9163809795940274 |
| cooldown_time | 5592 |
| executor_refresh_time | 12094 |
| macd_fast | 12 |
| macd_signal | 18 |
| macd_slow | 63 |
| natr_length | 50 |
| sell_n_levels | 5 |
| sell_spread_base | 0.4344967117406578 |
| sell_spread_ratio | 1.9217134090847383 |
| stop_loss | 0.010541759069125165 |
| take_profit | 0.042128420245953375 |
| time_limit | 39156 |
| total_amount_quote | 590.017116521971 |
| trailing_stop_activation | 0.0016071183212538474 |
| trailing_stop_delta | 0.0010411189788706722 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 590.017116521971 |
| Selected | 590.017116521971 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 7.1801
- **Net PnL (quote)**: 42.3635
- **Sharpe Ratio**: 4.9746
- **Max Drawdown %**: 0.8226
- **Profit Factor**: 2.092568304919071
- **Trade Count**: 670
- **Total Fees (quote)**: 6.5690
- **Maker Fees**: 3.2796
- **Taker Fees**: 3.2894
- **Fee Drag %**: 1.1134

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0575
- **PnL Component**: 0.0693
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0062
- **Fee Drag Component**: -0.0056
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0105**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.12 | -1.41 | 0.44 | 61 | -0.0051 | n/a |
| 1 | 0.73 | 6.91 | 0.31 | 65 | 0.0043 | n/a |
| 2 | 0.32 | 7.24 | 0.23 | 60 | 0.0011 | n/a |
| 3 | 0.40 | 7.64 | 0.17 | 60 | 0.0023 | n/a |
| 4 | -0.82 | -4.76 | 0.93 | 76 | -0.0159 | n/a |
| 5 | 2.37 | 7.23 | 0.36 | 49 | 0.0162 | n/a |
| 6 | 0.08 | 0.71 | 0.43 | 38 | -0.0508 | n/a |
| 7 | 1.12 | 7.89 | 0.03 | 30 | -0.0693 | n/a |
| 8 | -0.06 | -0.98 | 0.27 | 17 | -0.1348 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1825)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 6.62 | 4.60 | 0.86 | 0.0493 |
| fees_2x | 6.07 | 4.23 | 0.92 | 0.0408 |
| latency_plus1 | 7.16 | 4.96 | 0.82 | 0.0573 |
| latency_plus2 | 7.15 | 4.95 | 0.82 | 0.0573 |
| latency_plus3 | 7.00 | 4.85 | 0.82 | 0.0559 |
| low_liquidity | 7.18 | 4.97 | 0.82 | 0.0575 |
| very_low_liquidity | 7.12 | 4.94 | 0.82 | 0.0571 |
| high_slippage | 5.79 | 4.05 | 0.94 | 0.0435 |
| extreme_slippage | 3.00 | 2.14 | 1.49 | 0.0057 |
| combined_adverse | 5.21 | 3.66 | 1.01 | 0.0348 |
| spread_widen_10bps | 5.54 | 3.77 | 0.90 | 0.0415 |
| spread_widen_25bps | 4.24 | 2.86 | 0.93 | 0.0289 |
| thin_book | -1.49 | -1.10 | 2.94 | -0.0421 |
| very_thin_book | -5.89 | -3.50 | 6.35 | -0.1123 |
| entry_spread_stress | 5.24 | 3.54 | 0.91 | 0.0387 |
| combined_market_deterioration | -1.47 | -1.19 | 2.97 | -0.0451 |
| severe_adverse | -8.16 | -5.59 | 8.50 | -0.1825 |

## Holdout Validation

- **Holdout bars**: 8768
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0044)
- **Trend**: ranging (efficiency: 0.0265)
- **Best holdout score**: 0.0160 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0625 | 0.0082 | 1.21 | 0.44 | 73 |
| 1 | 0.0103 | -0.0103 | 0.39 | 1.42 | 224 |
| 2 | 0.0086 | 0.0126 | 3.28 | 2.25 | 133 |
| 3 | 0.0085 | 0.0009 | 1.23 | 1.30 | 155 |
| 4 | 0.0076 | 0.0160 | 3.65 | 2.24 | 138 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51871
- **Expected rows**: 51905
- **Missing rows**: 34
- **Forward-fill count**: 16
- **Forward-fill fraction**: 0.0003084575196159704
- **Longest gap (seconds)**: 10200

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0692 <= 0
- **Objective score**: -0.06924652758175447
- **PnL %**: 0.17719033298214426
- **Trade count**: 33

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1221 <= 0
- **Objective score**: -0.12210586230747213
- **PnL %**: 0.3014752977614587
- **Trade count**: 19

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1726 <= 0
- **Objective score**: -0.17257762397207957
- **PnL %**: 0.01574858139173269
- **Trade count**: 7

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.07083320247269162
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0688, 0.0553 |
| sell_spread_base | 0.0708, 0.0708 |
| stop_loss | 0.0741, 0.0741 |
| take_profit | 0.0708, 0.0708 |
| executor_refresh_time | 0.0766, 0.0626 |
| cooldown_time | 0.0705, 0.0655 |
| total_amount_quote | 0.0708, 0.0708 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4118860015431419
- **Max CV**: 1.1116225500587655
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.4998 | 0.2203399318698249 | 1.476450538950233 | 0.8125602069569544 |
| buy_spread_ratio | 0.2457 | 1.246016041092474 | 2.5346052354584145 | 1.8036768789748705 |
| sell_spread_base | 0.4569 | 0.2275275509214595 | 1.0931577107729837 | 0.5396345268161941 |
| sell_spread_ratio | 0.0857 | 1.252750219217749 | 1.580552217108331 | 1.4148877026661517 |
| buy_side_weight | 0.1737 | 0.4594701716445743 | 0.7813637985363411 | 0.6549082368574279 |
| amount_skew | 0.3696 | 1.000268604453216 | 3.3228464286118795 | 2.4739204025232717 |
| stop_loss | 0.3939 | 0.011357270338814705 | 0.03052539383674947 | 0.017548198006470735 |
| take_profit | 1.1116 | 0.005083197807051879 | 0.09133240860882898 | 0.027754292915746114 |
| executor_refresh_time | 0.3896 | 1552.0 | 11159.0 | 7004.6 |
| cooldown_time | 0.4408 | 1742.0 | 6845.0 | 4311.6 |
| total_amount_quote | 0.3635 | 388.78047308527096 | 991.7702671064263 | 687.8337438994779 |

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
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.06924652758175447 | FAIL |
| recent_pnl | >= 0 | 0.17719033298214426 | PASS |
| recent_trades | >= 5 | 33 | PASS |
| worst_stress | > -10 | -0.18253514191112957 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0082 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.18253514191112957 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.06924652758175447, pnl=0.17719033298214426, trades=33, reason=recent objective score -0.0692 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.12210586230747213, pnl=0.3014752977614587, trades=19, reason=recent objective score -0.1221 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.17257762397207957, pnl=0.01574858139173269, trades=7, reason=recent objective score -0.1726 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4118860015431419 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51871 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0692 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1221 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1726 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51871
- **Pre-release bars**: 43840
- **Dev bars**: 35072
- **Holdout bars**: 8768
- **Recent 28d bars**: 8031
- **Recent window start**: 1773291600

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T06:11:01.614705+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 1631
