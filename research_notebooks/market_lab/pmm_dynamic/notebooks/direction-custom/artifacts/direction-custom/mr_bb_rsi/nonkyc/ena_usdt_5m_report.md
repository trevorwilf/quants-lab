# PMM Dynamic Optimization Report: nonkyc_ENA-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 13:31:54 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T13:31:54.020616+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 3740 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ENA-USDT
- **interval**: 5m
- **n_candles**: 51888
- **dataset_hash**: a332d5ffcd1d2748688a3cdaffe6b7955b3582de8ff2e954e7a3c9e90bbd0829
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 996.0998627138341
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 25 |
| bb_length | 172 |
| bb_std | 2.322972596073552 |
| bbp_entry_threshold | 0.08566363600741358 |
| cooldown_time | 71389 |
| max_atr_pct_for_entry | 0.010143668182208536 |
| min_volume_quantile | 0.4107734294975057 |
| rsi_entry_threshold | 42.6606164115105 |
| rsi_length | 30 |
| stop_loss | 0.015490822421377589 |
| take_profit | 0.005688110864422249 |
| take_profit_order_type | LIMIT |
| time_limit | 84149 |
| total_amount_quote | 996.0998627138341 |
| trailing_stop_activation | 0.008454344875358975 |
| trailing_stop_delta | 0.0005163342161086236 |
| trend_ema_length | 175 |
| use_trend_filter | False |
| volume_filter_window | 410 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 996.0998627138341 |
| Selected | 996.0998627138341 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0052
- **Net PnL (quote)**: -10.0124
- **Sharpe Ratio**: -0.7923
- **Max Drawdown %**: 2.0256
- **Profit Factor**: 0.47019503462222123
- **Trade Count**: 56
- **Total Fees (quote)**: 8.2665
- **Maker Fees**: 5.5697
- **Taker Fees**: 2.6968
- **Fee Drag %**: 0.8299

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0295
- **PnL Component**: -0.0101
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0152
- **Fee Drag Component**: -0.0041
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2787**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.35 | -7.68 | 1.72 | 39 | -0.2353 | n/a |
| 1 | -1.66 | -11.34 | 1.76 | 53 | -0.2301 | n/a |
| 2 | -1.77 | -15.85 | 1.80 | 33 | -0.2584 | n/a |
| 3 | -2.46 | -9.22 | 2.73 | 32 | -0.2642 | n/a |
| 4 | -1.90 | -12.74 | 1.91 | 20 | -0.2649 | n/a |
| 5 | -1.91 | -17.42 | 1.93 | 29 | -0.3552 | n/a |
| 6 | -1.79 | -14.63 | 1.85 | 24 | -0.2904 | n/a |
| 7 | -1.85 | -9.76 | 2.12 | 88 | -0.1844 | n/a |
| 8 | -1.90 | -11.62 | 1.91 | 30 | -0.2985 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.42 | -1.12 | 2.13 | -0.0366 |
| fees_2x | -1.84 | -1.44 | 2.27 | -0.0439 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.14 | -1.24 | 1.95 | -0.0301 |
| very_low_liquidity | -1.61 | -2.04 | 2.03 | -0.0354 |
| high_slippage | -1.07 | -0.84 | 2.07 | -0.0305 |
| extreme_slippage | -1.21 | -0.94 | 2.17 | -0.0326 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.05 | -0.83 | 1.98 | -0.0294 |
| spread_widen_25bps | -1.05 | -0.83 | 1.91 | -0.0289 |
| thin_book | -1.94 | -2.09 | 2.43 | -0.1609 |
| very_thin_book | -1.87 | -3.35 | 2.05 | -0.5294 |
| entry_spread_stress | -1.05 | -0.83 | 1.96 | -0.0293 |
| combined_market_deterioration | -2.83 | -1.56 | 2.97 | -0.1641 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8768
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0033)
- **Trend**: ranging (efficiency: 0.0076)
- **Best holdout score**: -0.2589 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0147 | -0.2589 | -1.90 | 1.93 | 63 |
| 1 | -0.0321 | -0.4106 | -1.92 | 1.92 | 21 |
| 2 | -0.0322 | -0.4163 | -1.90 | 1.97 | 18 |
| 3 | -0.0322 | -0.3190 | -2.64 | 2.84 | 32 |
| 4 | -0.0327 | -0.3644 | -1.92 | 2.13 | 19 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51888
- **Expected rows**: 51908
- **Missing rows**: 20
- **Forward-fill count**: 102
- **Forward-fill fraction**: 0.00196577243293247
- **Longest gap (seconds)**: 6300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1704 <= 0; recent PnL -1.7489% < 0
- **Objective score**: -0.17041468775046767
- **PnL %**: -1.7488681005798188
- **Trade count**: 16

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1843 <= 0; recent PnL -1.8989% < 0
- **Objective score**: -0.1843449389969252
- **PnL %**: -1.8988644503425511
- **Trade count**: 74

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3904 <= 0; recent PnL -1.8987% < 0
- **Objective score**: -0.3904435279026427
- **PnL %**: -1.8987032340613244
- **Trade count**: 71

## Sensitivity Analysis

- **Sensitivity penalty**: 0.038461538461538464
- **Baseline score**: -0.06401825169752294
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0441, -0.0442 |
| bb_std | -0.0416, -0.1401 |
| bbp_entry_threshold | -0.0631, -0.0874 |
| rsi_length | -0.0640, -0.0640 |
| rsi_entry_threshold | -0.0640, -0.0640 |
| trend_ema_length | -0.0640, -0.0640 |
| max_atr_pct_for_entry | -0.0640, -0.0640 |
| volume_filter_window | -0.0640, -0.0640 |
| min_volume_quantile | -0.0640, -0.0640 |
| stop_loss | -0.0318, -0.0585 |
| take_profit | -0.0628, -0.0303 |
| cooldown_time | -0.0640, -0.0640 |
| total_amount_quote | -0.0640, -0.0639 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2002639567723986
- **Max CV**: 0.37544479722044327
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3754 | 0.015069789685026903 | 0.0371638772298011 | 0.018042177835018783 |
| take_profit | 0.2845 | 0.005688110864422249 | 0.011520738600456543 | 0.007876566612763775 |
| cooldown_time | 0.0949 | 58096.0 | 80399.0 | 67119.0 |
| total_amount_quote | 0.0462 | 851.225834668801 | 998.2511287100049 | 954.4501388575967 |

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
| recent_objective | > 0 | -0.17041468775046767 | FAIL |
| recent_pnl | >= 0 | -1.7488681005798188 | FAIL |
| recent_trades | >= 5 | 16 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.038461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.2588546925453806 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.038461538461538464 |
| recent_28d | FAIL | score=-0.17041468775046767, pnl=-1.7488681005798188, trades=16, reason=recent objective score -0.1704 <= 0; recent PnL -1.7489% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.1843449389969252, pnl=-1.8988644503425511, trades=74, reason=recent objective score -0.1843 <= 0; recent PnL -1.8989% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.3904435279026427, pnl=-1.8987032340613244, trades=71, reason=recent objective score -0.3904 <= 0; recent PnL -1.8987% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2002639567723986 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51888 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1704 <= 0; recent PnL -1.7489% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1843 <= 0; recent PnL -1.8989% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.3904 <= 0; recent PnL -1.8987% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51888
- **Pre-release bars**: 43843
- **Dev bars**: 35075
- **Holdout bars**: 8768
- **Recent 28d bars**: 8045
- **Recent window start**: 1774096800

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T13:31:54.020616+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 3740
- **validation_status**: validated_fail
