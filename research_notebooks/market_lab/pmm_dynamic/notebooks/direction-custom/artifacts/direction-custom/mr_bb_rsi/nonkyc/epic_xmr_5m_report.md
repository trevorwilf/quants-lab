# PMM Dynamic Optimization Report: nonkyc_EPIC-XMR_5m_mr_bb_rsi_v1

Generated: 2026-04-18 13:49:11 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T13:49:11.824091+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 6722 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: EPIC-XMR
- **interval**: 5m
- **n_candles**: 38431
- **dataset_hash**: 22a5d815b51461d23403948aa9bf9317c4f2e1e1eda5ba346689122454d6e1da
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 25.26502726028607
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 26 |
| bb_length | 177 |
| bb_std | 2.543228558167963 |
| bbp_entry_threshold | 0.09748623289396138 |
| cooldown_time | 78079 |
| max_atr_pct_for_entry | 0.015369077456932011 |
| min_volume_quantile | 0.02356516394623534 |
| rsi_entry_threshold | 39.42476360288157 |
| rsi_length | 13 |
| stop_loss | 0.02810311662906756 |
| take_profit | 0.05814494442845459 |
| take_profit_order_type | LIMIT |
| time_limit | 112122 |
| total_amount_quote | 25.26502726028607 |
| trailing_stop_activation | 0.037155819988339396 |
| trailing_stop_delta | 0.0018776035088695065 |
| trend_ema_length | 291 |
| use_trend_filter | False |
| volume_filter_window | 519 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 25.26502726028607 |
| Selected | 25.26502726028607 |

> **WARNING**: Selected quote is within 5% of search minimum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 1.1811
- **Net PnL (quote)**: 0.2984
- **Sharpe Ratio**: 1.5148
- **Max Drawdown %**: 0.5901
- **Profit Factor**: 5.614193978583013
- **Trade Count**: 361
- **Total Fees (quote)**: 0.0361
- **Maker Fees**: 0.0127
- **Taker Fees**: 0.0234
- **Fee Drag %**: 0.1429

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0065
- **PnL Component**: 0.0117
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0044
- **Fee Drag Component**: -0.0007
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1101**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.66 | 4.39 | 0.14 | 82 | 0.0054 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | -0.00 | -0.02 | 0.08 | 36 | -0.0716 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | -0.34 | -2.31 | 0.44 | 181 | -0.2645 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 1.11 | 1.43 | 0.62 | 0.0053 |
| fees_2x | 1.04 | 1.34 | 0.64 | 0.0040 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 0.59 | 1.51 | 0.30 | 0.0033 |
| very_low_liquidity | 0.30 | 1.51 | 0.15 | 0.0016 |
| high_slippage | 1.16 | 1.49 | 0.59 | 0.0063 |
| extreme_slippage | 1.11 | 1.43 | 0.60 | 0.0057 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 1.16 | 1.49 | 0.60 | 0.0062 |
| spread_widen_25bps | 1.14 | 1.46 | 0.62 | 0.0058 |
| thin_book | 0.40 | 1.61 | 0.20 | 0.0023 |
| very_thin_book | 0.00 | 0.00 | 0.00 | -1000.0000 |
| entry_spread_stress | 1.15 | 1.48 | 0.61 | 0.0061 |
| combined_market_deterioration | 0.54 | 1.39 | 0.32 | 0.0024 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 6077
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0071)
- **Trend**: ranging (efficiency: 0.0018)
- **Best holdout score**: -0.0560 (rank #1)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9967 | -0.0664 | -0.00 | 0.08 | 36 |
| 1 | 0.0058 | -0.0560 | 0.01 | 0.01 | 36 |
| 2 | 0.0057 | -0.0953 | -0.00 | 0.01 | 36 |
| 3 | 0.0055 | -0.0802 | -0.00 | 0.01 | 36 |
| 4 | 0.0054 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 38431
- **Expected rows**: 38452
- **Missing rows**: 21
- **Forward-fill count**: 861
- **Forward-fill fraction**: 0.022403788608154875
- **Longest gap (seconds)**: 1500

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3531 <= 0; recent PnL -3.1622% < 0
- **Objective score**: -0.35311630214243245
- **PnL %**: -3.162194361877847
- **Trade count**: 832

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3720 <= 0; recent PnL -3.1622% < 0
- **Objective score**: -0.3720339019671039
- **PnL %**: -3.162194361877847
- **Trade count**: 832

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4037 <= 0; recent PnL -3.1622% < 0
- **Objective score**: -0.40374783186397933
- **PnL %**: -3.162194361877847
- **Trade count**: 832

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.22276236255652287
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.2882, -0.2945 |
| bb_std | -0.2804, -0.2424 |
| bbp_entry_threshold | -0.2424, -0.2804 |
| rsi_length | -0.2882, -0.2228 |
| rsi_entry_threshold | -0.2228, -0.2804 |
| trend_ema_length | -0.2228, -0.2228 |
| max_atr_pct_for_entry | -0.2228, -0.2228 |
| volume_filter_window | -0.2228, -0.2228 |
| min_volume_quantile | -0.2228, -0.2228 |
| stop_loss | -0.2326, -0.2445 |
| take_profit | -0.2228, -0.2228 |
| cooldown_time | -0.2228, -0.2228 |
| total_amount_quote | -0.2341, -0.2055 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.37375408898501905
- **Max CV**: 0.761550695187054
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3249 | 0.01947058040785159 | 0.05028700113825908 | 0.03502071605558582 |
| take_profit | 0.7616 | 0.007000318350508588 | 0.05814494442845459 | 0.024329481240759055 |
| cooldown_time | 0.3273 | 21444.0 | 78079.0 | 51325.3 |
| total_amount_quote | 0.0813 | 25.25452556599203 | 31.944388541452298 | 26.93102352880401 |

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
| recent_objective | > 0 | -0.35311630214243245 | FAIL |
| recent_pnl | >= 0 | -3.162194361877847 | FAIL |
| recent_trades | >= 5 | 832 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.0663768300415864 |
| walkforward | PASS | 6 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.35311630214243245, pnl=-3.162194361877847, trades=832, reason=recent objective score -0.3531 <= 0; recent PnL -3.1622% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.3720339019671039, pnl=-3.162194361877847, trades=832, reason=recent objective score -0.3720 <= 0; recent PnL -3.1622% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.40374783186397933, pnl=-3.162194361877847, trades=832, reason=recent objective score -0.4037 <= 0; recent PnL -3.1622% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.37375408898501905 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 38431 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3531 <= 0; recent PnL -3.1622% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3720 <= 0; recent PnL -3.1622% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.4037 <= 0; recent PnL -3.1622% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 38431
- **Pre-release bars**: 30387
- **Dev bars**: 24310
- **Holdout bars**: 6077
- **Recent 28d bars**: 8044
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T13:49:11.824091+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 6722
- **validation_status**: validated_fail
