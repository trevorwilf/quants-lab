# PMM Dynamic Optimization Report: nonkyc_ZEC-XMR_5m_mr_bb_rsi_v1

Generated: 2026-04-18 16:51:25 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T16:51:25.713487+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 5845 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ZEC-XMR
- **interval**: 5m
- **n_candles**: 51868
- **dataset_hash**: 98335ac301dc843ce558eae7ed2e337fb9b6eef1850eba02e6f69ee78cb4f8ff
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 53.51922356600312
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 18 |
| bb_length | 134 |
| bb_std | 2.3026974384836 |
| bbp_entry_threshold | 0.12712062597643453 |
| cooldown_time | 10297 |
| max_atr_pct_for_entry | 0.09565295822796592 |
| min_volume_quantile | 0.41033839940442884 |
| rsi_entry_threshold | 47.8327339861248 |
| rsi_length | 11 |
| stop_loss | 0.030237366636380415 |
| take_profit | 0.05007839951738497 |
| take_profit_order_type | MARKET |
| time_limit | 298960 |
| total_amount_quote | 53.51922356600312 |
| trailing_stop_activation | 0.027896745701824075 |
| trailing_stop_delta | 0.0015341838488604582 |
| trend_ema_length | 212 |
| use_trend_filter | True |
| volume_filter_window | 504 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 53.51922356600312 |
| Selected | 53.51922356600312 |

> **WARNING**: Selected quote is within 5% of search minimum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 0.3100
- **Net PnL (quote)**: 0.1659
- **Sharpe Ratio**: 2.0178
- **Max Drawdown %**: 0.1025
- **Profit Factor**: 7.001577656758145
- **Trade Count**: 801
- **Total Fees (quote)**: 0.0154
- **Maker Fees**: 0.0053
- **Taker Fees**: 0.0101
- **Fee Drag %**: 0.0288

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0022
- **PnL Component**: 0.0031
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0008
- **Fee Drag Component**: -0.0001
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0046**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.07 | 6.30 | 0.01 | 97 | 0.0005 | n/a |
| 1 | 0.02 | 0.86 | 0.04 | 222 | -0.0028 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.11 | 3.67 | 0.03 | 183 | 0.0009 | n/a |
| 5 | -0.05 | -42.78 | 0.05 | 134 | -0.2709 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | -0.05 | -0.83 | 0.33 | 998 | -0.0812 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 0.30 | 1.94 | 0.10 | 0.0020 |
| fees_2x | 0.28 | 1.85 | 0.10 | 0.0017 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 0.16 | 2.02 | 0.05 | 0.0011 |
| very_low_liquidity | 0.08 | 2.02 | 0.03 | 0.0005 |
| high_slippage | 0.31 | 1.99 | 0.10 | 0.0021 |
| extreme_slippage | 0.30 | 1.94 | 0.10 | 0.0020 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 0.23 | 1.56 | 0.10 | 0.0014 |
| spread_widen_25bps | 0.22 | 1.50 | 0.10 | 0.0013 |
| thin_book | 0.04 | 1.94 | 0.01 | 0.0003 |
| very_thin_book | 0.00 | 0.93 | 0.00 | -0.1560 |
| entry_spread_stress | 0.23 | 1.55 | 0.10 | 0.0014 |
| combined_market_deterioration | 0.09 | 1.47 | 0.05 | 0.0005 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0075)
- **Trend**: ranging (efficiency: 0.0066)
- **Best holdout score**: -0.1760 (rank #3)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9989 | -1000.0000 | 0.00 | 0.00 | 0 |
| 1 | 0.0008 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | 0.0005 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | 0.0004 | -0.1760 | 0.00 | 0.00 | 6 |
| 4 | 0.0004 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51868
- **Expected rows**: 51899
- **Missing rows**: 31
- **Forward-fill count**: 1743
- **Forward-fill fraction**: 0.0336045345877998
- **Longest gap (seconds)**: 5100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0767 <= 0; recent PnL -0.0478% < 0
- **Objective score**: -0.07673218138539772
- **PnL %**: -0.047849641027778514
- **Trade count**: 998

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.3076923076923077
- **Baseline score**: -0.0004897419885787086
- **Sign flips**: 0
- **Collapse count**: 8
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0006, -0.3327 |
| bb_std | -0.0008, -0.2790 |
| bbp_entry_threshold | -0.0003, -0.0005 |
| rsi_length | -0.0005, -0.0005 |
| rsi_entry_threshold | -0.0005, -0.0012 |
| trend_ema_length | -0.1521, -0.0806 |
| max_atr_pct_for_entry | -0.0005, -0.0005 |
| volume_filter_window | -0.0005, -0.0005 |
| min_volume_quantile | -0.0005, -0.0005 |
| stop_loss | -0.0009, -0.1149 |
| take_profit | -0.0005, -0.0005 |
| cooldown_time | -0.0005, -0.0005 |
| total_amount_quote | -0.0004, -0.0005 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3693651043465887
- **Max CV**: 0.554200985045593
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2783 | 0.015988195348578454 | 0.036330389356637606 | 0.02470628399734873 |
| take_profit | 0.4069 | 0.011070035098222646 | 0.05007839951738497 | 0.030415741843441268 |
| cooldown_time | 0.5542 | 3572.0 | 31194.0 | 17713.0 |
| total_amount_quote | 0.2380 | 29.932226387793186 | 56.289023621370646 | 42.85712822198792 |

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
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
| recent_objective | > 0 | -0.07673218138539772 | FAIL |
| recent_pnl | >= 0 | -0.047849641027778514 | FAIL |
| recent_trades | >= 5 | 998 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.3076923076923077 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.3076923076923077 |
| recent_28d | FAIL | score=-0.07673218138539772, pnl=-0.047849641027778514, trades=998, reason=recent objective score -0.0767 <= 0; recent PnL -0.0478% < 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3693651043465887 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51868 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0767 <= 0; recent PnL -0.0478% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51868
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8034
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T16:51:25.713487+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 5845
- **validation_status**: validated_fail
