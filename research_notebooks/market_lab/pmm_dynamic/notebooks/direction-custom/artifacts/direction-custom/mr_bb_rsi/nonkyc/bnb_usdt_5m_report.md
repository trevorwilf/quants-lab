# PMM Dynamic Optimization Report: nonkyc_BNB-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 12:54:44 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T12:54:44.922384+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 6448 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BNB-USDT
- **interval**: 5m
- **n_candles**: 51899
- **dataset_hash**: 4732531bcd7456473578271ee825ebabc7063234fcf62c53310f33ef95ae7bdf
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 947.5017220607683
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 18 |
| bb_length | 32 |
| bb_std | 1.714935802227128 |
| bbp_entry_threshold | 0.29477185921370586 |
| cooldown_time | 13014 |
| max_atr_pct_for_entry | 0.02059449399259802 |
| min_volume_quantile | 0.08494725567729436 |
| rsi_entry_threshold | 42.8604434977566 |
| rsi_length | 28 |
| stop_loss | 0.045091314162094075 |
| take_profit | 0.007101424479800696 |
| take_profit_order_type | LIMIT |
| time_limit | 126652 |
| total_amount_quote | 947.5017220607683 |
| trailing_stop_activation | 0.005174090676145417 |
| trailing_stop_delta | 0.002464088016735508 |
| trend_ema_length | 141 |
| use_trend_filter | True |
| volume_filter_window | 357 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 947.5017220607683 |
| Selected | 947.5017220607683 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2.5180
- **Net PnL (quote)**: 23.8580
- **Sharpe Ratio**: 0.8439
- **Max Drawdown %**: 2.6177
- **Profit Factor**: 14.08441037230424
- **Trade Count**: 41
- **Total Fees (quote)**: 39.8965
- **Maker Fees**: 15.1493
- **Taker Fees**: 24.7472
- **Fee Drag %**: 4.2107

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0522
- **PnL Component**: 0.0249
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0196
- **Fee Drag Component**: -0.0211
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0360
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.73 | -4.46 | 2.63 | 11 | -0.1983 | n/a |
| 1 | 0.06 | 0.82 | 0.31 | 4 | -0.1873 | n/a |
| 2 | -1.36 | -7.07 | 1.79 | 8 | -0.4745 | n/a |
| 3 | -0.84 | -4.16 | 0.92 | 3 | -1000.0000 | n/a |
| 4 | -0.06 | -0.30 | 0.90 | 3 | -1000.0000 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | -0.39 | -1.39 | 1.35 | 6 | -0.3025 | n/a |
| 7 | -0.04 | -0.24 | 0.41 | 2 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 0.41 | 0.18 | 2.95 | -0.1379 |
| fees_2x | -1.08 | -0.33 | 3.75 | -0.3179 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 2.65 | 0.86 | 2.87 | -0.0167 |
| very_low_liquidity | 2.63 | 0.83 | 3.01 | -0.0177 |
| high_slippage | 1.87 | 0.64 | 2.73 | -0.0594 |
| extreme_slippage | 0.56 | 0.23 | 2.95 | -0.1242 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.08 | -0.49 | 3.09 | -1000.0000 |
| spread_widen_25bps | -1.23 | -0.56 | 3.09 | -1000.0000 |
| thin_book | 1.32 | 0.61 | 2.03 | -0.1336 |
| very_thin_book | -0.04 | -0.04 | 1.00 | -0.1912 |
| entry_spread_stress | -1.13 | -0.51 | 3.09 | -1000.0000 |
| combined_market_deterioration | -1.30 | -0.61 | 3.09 | -1000.0000 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0018)
- **Trend**: ranging (efficiency: 0.0063)
- **Best holdout score**: -0.1685 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0261 | -0.2246 | -0.43 | 1.35 | 8 |
| 1 | -0.1771 | -0.2148 | -1.75 | 2.91 | 8 |
| 2 | -0.1797 | -0.2002 | -1.12 | 1.98 | 13 |
| 3 | -0.1820 | -0.1795 | 1.22 | 2.07 | 8 |
| 4 | -0.1821 | -0.1685 | 1.84 | 2.07 | 10 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51899
- **Expected rows**: 51899
- **Missing rows**: 0
- **Forward-fill count**: 176
- **Forward-fill fraction**: 0.003391202142623172
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

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

- **Sensitivity penalty**: 0.23076923076923078
- **Baseline score**: -0.0291684367642193
- **Sign flips**: 0
- **Collapse count**: 6
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0292, -0.0292 |
| bb_std | -0.0292, -0.0292 |
| bbp_entry_threshold | -0.0292, -0.0292 |
| rsi_length | -0.1321, -0.1572 |
| rsi_entry_threshold | -0.3403, -1000.0000 |
| trend_ema_length | -0.2091, -0.0547 |
| max_atr_pct_for_entry | -0.0292, -0.0292 |
| volume_filter_window | -0.0292, -0.0093 |
| min_volume_quantile | -0.0292, -0.0093 |
| stop_loss | -0.0292, -0.0292 |
| take_profit | -0.0323, -0.0236 |
| cooldown_time | -0.0251, -0.0292 |
| total_amount_quote | -0.0134, -0.0377 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5057727379218142
- **Max CV**: 0.6928588489757019
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4292 | 0.019110194325594344 | 0.07499192939075085 | 0.046674546200906414 |
| take_profit | 0.6929 | 0.005353882828068168 | 0.025395094214195658 | 0.008773346049242658 |
| cooldown_time | 0.6883 | 3202.0 | 75339.0 | 34835.1 |
| total_amount_quote | 0.2127 | 488.60079385168046 | 984.0767319570783 | 786.2309533433636 |

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
- walkforward_robust: **FAIL**
- walkforward_positive_majority: **FAIL**
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | 0.0 | PASS |
| recent_trades | >= 5 | 0 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.23076923076923078 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.2246344726237258 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.23076923076923078 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5057727379218142 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51899 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51899
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8065
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T12:54:44.922384+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 6448
- **validation_status**: validated_fail
