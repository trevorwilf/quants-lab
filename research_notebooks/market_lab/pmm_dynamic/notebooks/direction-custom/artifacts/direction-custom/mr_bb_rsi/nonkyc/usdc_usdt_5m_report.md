# PMM Dynamic Optimization Report: nonkyc_USDC-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 16:00:40 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T16:00:40.652646+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 4030 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: USDC-USDT
- **interval**: 5m
- **n_candles**: 51866
- **dataset_hash**: fe387b58123f50854f82894d73bf181425255ef3518884d825a26a0f1a9deb0e
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 864.7308490428675
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 7 |
| bb_length | 171 |
| bb_std | 2.961682811921052 |
| bbp_entry_threshold | 0.21776774234862195 |
| cooldown_time | 29548 |
| max_atr_pct_for_entry | 0.05933247654380962 |
| min_volume_quantile | 0.14017647030238092 |
| rsi_entry_threshold | 35.90923080272591 |
| rsi_length | 16 |
| stop_loss | 0.037873084893955015 |
| take_profit | 0.009923564709770818 |
| take_profit_order_type | MARKET |
| time_limit | 264728 |
| total_amount_quote | 864.7308490428675 |
| trailing_stop_activation | 0.0018189177076090213 |
| trailing_stop_delta | 0.01763626899775079 |
| trend_ema_length | 127 |
| use_trend_filter | False |
| volume_filter_window | 311 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 864.7308490428675 |
| Selected | 864.7308490428675 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.1367
- **Net PnL (quote)**: -9.8297
- **Sharpe Ratio**: -5.7139
- **Max Drawdown %**: 1.1367
- **Profit Factor**: 0.09124761061318602
- **Trade Count**: 96
- **Total Fees (quote)**: 21.3564
- **Maker Fees**: 7.4977
- **Taker Fees**: 13.8587
- **Fee Drag %**: 2.4697

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0338
- **PnL Component**: -0.0114
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0085
- **Fee Drag Component**: -0.0123
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1329**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.72 | -11.77 | 0.75 | 254 | -0.0560 | n/a |
| 1 | -0.78 | -8.70 | 0.97 | 186 | -0.0377 | n/a |
| 2 | -1.09 | -9.91 | 1.18 | 57 | -0.0678 | n/a |
| 3 | -1.04 | -7.02 | 1.04 | 42 | -0.1087 | n/a |
| 4 | -1.08 | -8.44 | 1.09 | 36 | -0.0977 | n/a |
| 5 | -1.04 | -11.77 | 1.07 | 32 | -0.2758 | n/a |
| 6 | -1.21 | -9.11 | 1.29 | 17 | -0.2600 | n/a |
| 7 | -1.10 | -13.78 | 1.10 | 33 | -0.2538 | n/a |
| 8 | -1.13 | -10.02 | 1.29 | 38 | -0.1073 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.14 | -5.68 | 1.14 | -0.3564 |
| fees_2x | -1.42 | -5.37 | 1.42 | -0.4093 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.06 | -5.98 | 1.06 | -0.0812 |
| very_low_liquidity | -1.06 | -7.34 | 1.06 | -0.0956 |
| high_slippage | -1.01 | -5.11 | 1.01 | -0.2981 |
| extreme_slippage | -1.12 | -5.28 | 1.12 | -0.3573 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.15 | -3.23 | 1.18 | -0.1530 |
| spread_widen_25bps | -1.03 | -2.93 | 1.03 | -0.1514 |
| thin_book | -1.11 | -4.19 | 1.15 | -0.0611 |
| very_thin_book | -1.00 | -2.95 | 1.08 | -0.0398 |
| entry_spread_stress | -1.00 | -2.91 | 1.02 | -0.1432 |
| combined_market_deterioration | -1.10 | -4.10 | 1.10 | -0.2864 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8771
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0014)
- **Trend**: ranging (efficiency: 0.0001)
- **Best holdout score**: -0.0491 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0169 | -0.0981 | -1.16 | 1.16 | 46 |
| 1 | -0.0245 | -0.0565 | 1.05 | 0.26 | 42 |
| 2 | -0.0281 | -0.3140 | 0.60 | 0.40 | 41 |
| 3 | -0.0302 | -0.0491 | 0.26 | 0.80 | 65 |
| 4 | -0.0307 | -0.2955 | -0.41 | 0.50 | 48 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51866
- **Expected rows**: 51921
- **Missing rows**: 55
- **Forward-fill count**: 478
- **Forward-fill fraction**: 0.009216056761655034
- **Longest gap (seconds)**: 10200

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0788 <= 0; recent PnL -1.0036% < 0
- **Objective score**: -0.07883997514792529
- **PnL %**: -1.0036142049173147
- **Trade count**: 39

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1354 <= 0; recent PnL -1.1064% < 0
- **Objective score**: -0.1354026585957886
- **PnL %**: -1.106383865845781
- **Trade count**: 37

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2120 <= 0; recent PnL -0.9695% < 0
- **Objective score**: -0.21203019288334152
- **PnL %**: -0.96951826932355
- **Trade count**: 25

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.031109770110693033
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0311, -0.0311 |
| bb_std | -0.0311, -0.0311 |
| bbp_entry_threshold | -0.0311, -0.0311 |
| rsi_length | -0.0341, -0.0311 |
| rsi_entry_threshold | -0.0354, -0.0362 |
| trend_ema_length | -0.0311, -0.0311 |
| max_atr_pct_for_entry | -0.0311, -0.0311 |
| volume_filter_window | -0.0311, -0.0311 |
| min_volume_quantile | -0.0311, -0.0311 |
| stop_loss | -0.0311, -0.0311 |
| take_profit | -0.0311, -0.0311 |
| cooldown_time | -0.0309, -0.0311 |
| total_amount_quote | -0.0312, -0.0313 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.40672273507305406
- **Max CV**: 0.5756810607905174
- **Clustered params**: take_profit, total_amount_quote
- **Scattered params**: stop_loss, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.5757 | 0.01609265628313178 | 0.07175236281797417 | 0.0362827288765736 |
| take_profit | 0.3668 | 0.012214765993030195 | 0.05569340309306036 | 0.03477732458852144 |
| cooldown_time | 0.5684 | 9345.0 | 70894.0 | 39576.2 |
| total_amount_quote | 0.1160 | 634.4264143040638 | 983.3483361616022 | 878.5148739388202 |

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
| recent_objective | > 0 | -0.07883997514792529 | FAIL |
| recent_pnl | >= 0 | -1.0036142049173147 | FAIL |
| recent_trades | >= 5 | 39 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.0981426838499734 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.07883997514792529, pnl=-1.0036142049173147, trades=39, reason=recent objective score -0.0788 <= 0; recent PnL -1.0036% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.1354026585957886, pnl=-1.106383865845781, trades=37, reason=recent objective score -0.1354 <= 0; recent PnL -1.1064% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.21203019288334152, pnl=-0.96951826932355, trades=25, reason=recent objective score -0.2120 <= 0; recent PnL -0.9695% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.40672273507305406 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51866 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0788 <= 0; recent PnL -1.0036% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1354 <= 0; recent PnL -1.1064% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2120 <= 0; recent PnL -0.9695% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51866
- **Pre-release bars**: 43856
- **Dev bars**: 35085
- **Holdout bars**: 8771
- **Recent 28d bars**: 8010
- **Recent window start**: 1774100700

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T16:00:40.652646+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 4030
- **validation_status**: validated_fail
