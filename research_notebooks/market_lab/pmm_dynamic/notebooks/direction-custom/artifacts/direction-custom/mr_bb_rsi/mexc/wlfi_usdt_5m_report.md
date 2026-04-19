# PMM Dynamic Optimization Report: mexc_WLFI-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 10:45:11 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T10:45:11.873989+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 8859 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: WLFI-USDT
- **interval**: 5m
- **n_candles**: 51824
- **dataset_hash**: df0557bd6867d2f7ab204745216c66e32544f698daf20e88055f814d1fe9f6bc
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 838.2244239698673
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 8 |
| bb_length | 175 |
| bb_std | 1.9085823643667785 |
| bbp_entry_threshold | 0.15225182786343502 |
| cooldown_time | 80884 |
| max_atr_pct_for_entry | 0.0793273581311981 |
| min_volume_quantile | 0.5100528668986857 |
| rsi_entry_threshold | 49.93853020759562 |
| rsi_length | 29 |
| stop_loss | 0.04986959891157356 |
| take_profit | 0.016088778991431612 |
| take_profit_order_type | MARKET |
| time_limit | 158867 |
| total_amount_quote | 838.2244239698673 |
| trailing_stop_activation | 0.018369355286599158 |
| trailing_stop_delta | 0.0023774673319121114 |
| trend_ema_length | 243 |
| use_trend_filter | False |
| volume_filter_window | 547 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 838.2244239698673 |
| Selected | 838.2244239698673 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 32.8683
- **Net PnL (quote)**: 275.5105
- **Sharpe Ratio**: 5.6360
- **Max Drawdown %**: 3.0915
- **Profit Factor**: inf
- **Trade Count**: 23
- **Total Fees (quote)**: 6.4269
- **Maker Fees**: 3.1853
- **Taker Fees**: 3.2416
- **Fee Drag %**: 0.7667

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1487
- **PnL Component**: 0.2842
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0232
- **Fee Drag Component**: -0.0038
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1080
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.22 | -0.32 | 2.43 | 1 | -1000.0000 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 6.52 | 12.95 | 2.48 | 6 | -0.1325 | n/a |
| 3 | 7.58 | 7.52 | 1.89 | 5 | -0.3594 | n/a |
| 4 | 6.31 | 9.04 | 0.58 | 5 | -0.1241 | n/a |
| 5 | 3.60 | 5.86 | 1.18 | 3 | -1000.0000 | n/a |
| 6 | 1.85 | 6.34 | 0.90 | 2 | -1000.0000 | n/a |
| 7 | 3.15 | 6.79 | 1.89 | 3 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 32.48 | 5.58 | 3.10 | 0.1438 |
| fees_2x | 32.10 | 5.52 | 3.12 | 0.1389 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 32.87 | 5.65 | 3.09 | 0.1607 |
| very_low_liquidity | 32.83 | 5.65 | 3.09 | 0.2124 |
| high_slippage | 31.90 | 5.51 | 3.10 | 0.1413 |
| extreme_slippage | 29.97 | 5.25 | 3.11 | 0.1265 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 34.31 | 5.27 | 3.14 | 0.1590 |
| spread_widen_25bps | 27.28 | 4.14 | 5.15 | 0.0902 |
| thin_book | 18.47 | 4.44 | 2.32 | -0.0023 |
| very_thin_book | 6.09 | 2.39 | 2.40 | -0.1398 |
| entry_spread_stress | 27.55 | 4.20 | 5.13 | 0.0924 |
| combined_market_deterioration | -2.13 | -1.20 | 4.99 | -0.2439 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0037)
- **Trend**: ranging (efficiency: 0.0128)
- **Best holdout score**: -0.1268 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9257 | -0.1268 | 7.03 | 1.82 | 5 |
| 1 | -0.1327 | -1000.0000 | -2.54 | 4.55 | 2 |
| 2 | -0.1355 | -1000.0000 | -1.26 | 4.66 | 3 |
| 3 | -0.1355 | -0.1599 | 5.39 | 4.14 | 5 |
| 4 | -0.1368 | -0.1268 | 7.03 | 1.82 | 5 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51824
- **Expected rows**: 51841
- **Missing rows**: 17
- **Forward-fill count**: 265
- **Forward-fill fraction**: 0.005113460944736029
- **Longest gap (seconds)**: 5400

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -5.0735% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -5.073459517506637
- **Trade count**: 2

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -5.0735% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -5.073459517506637
- **Trade count**: 2

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.19230769230769232
- **Baseline score**: 0.17544291187200894
- **Sign flips**: 2
- **Collapse count**: 3
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | 0.0654, -0.2403 |
| bb_std | -0.2398, 0.1557 |
| bbp_entry_threshold | 0.1243, 0.0922 |
| rsi_length | 0.1754, 0.1754 |
| rsi_entry_threshold | 0.1754, 0.1754 |
| trend_ema_length | 0.1754, 0.1754 |
| max_atr_pct_for_entry | 0.1754, 0.1754 |
| volume_filter_window | 0.1754, 0.1984 |
| min_volume_quantile | 0.1944, 0.1754 |
| stop_loss | 0.1691, 0.1818 |
| take_profit | 0.1405, 0.2025 |
| cooldown_time | 0.1754, 0.1766 |
| total_amount_quote | 0.1754, 0.1714 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.38086434747838027
- **Max CV**: 0.5741868610714992
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2311 | 0.035151610775563724 | 0.07397533277974912 | 0.05234468934906894 |
| take_profit | 0.5742 | 0.005163599710602412 | 0.053658122669790184 | 0.026022084079719628 |
| cooldown_time | 0.5257 | 1530.0 | 80884.0 | 52448.7 |
| total_amount_quote | 0.1925 | 451.17125056249176 | 968.7911849571037 | 811.3929408335396 |

## Execution Realism Assumptions

- **taker_probability**: 0.0
- **supports_post_only**: True
- **connector**: mexc
- **fill_participation_rate**: 0.1
- **latency_bars**: 1
- **slippage_bps**: 5.0
- **refresh_close_mode**: market_close

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: **FAIL**
- yaml_validates: **FAIL**
- walkforward_robust: **FAIL**
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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | -5.073459517506637 | FAIL |
| recent_trades | >= 5 | 2 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.19230769230769232 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.12675787957676618 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.19230769230769232 |
| recent_28d | FAIL | score=-1000.0, pnl=-5.073459517506637, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -5.0735% < 0; recent trades 2 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=-5.073459517506637, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -5.0735% < 0; recent trades 2 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.38086434747838027 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51824 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -5.0735% < 0; recent trades 2 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -5.0735% < 0; recent trades 2 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51824
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8048
- **Recent window start**: 1774017900

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T10:45:11.873989+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 8859
- **validation_status**: validated_fail
