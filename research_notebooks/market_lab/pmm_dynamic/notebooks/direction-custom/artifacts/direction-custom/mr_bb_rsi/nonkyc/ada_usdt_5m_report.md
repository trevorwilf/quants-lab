# PMM Dynamic Optimization Report: nonkyc_ADA-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 11:49:55 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T11:49:55.442847+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 5010 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ADA-USDT
- **interval**: 5m
- **n_candles**: 51884
- **dataset_hash**: 513071d87930c15095ff2c49aac3c36715b4ee4bbf5b9f2bf42f5af00d3a46b6
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 344.6924171456902
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 13 |
| bb_length | 137 |
| bb_std | 2.5680062451678953 |
| bbp_entry_threshold | 0.181138970596776 |
| cooldown_time | 17687 |
| max_atr_pct_for_entry | 0.006593804810804476 |
| min_volume_quantile | 0.5473233377895271 |
| rsi_entry_threshold | 24.59795484387078 |
| rsi_length | 8 |
| stop_loss | 0.020679151032649397 |
| take_profit | 0.042416021430261276 |
| take_profit_order_type | MARKET |
| time_limit | 189119 |
| total_amount_quote | 344.6924171456902 |
| trailing_stop_activation | 0.03858565645861015 |
| trailing_stop_delta | 0.0002282413675281916 |
| trend_ema_length | 387 |
| use_trend_filter | True |
| volume_filter_window | 528 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 344.6924171456902 |
| Selected | 344.6924171456902 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 9.6174
- **Net PnL (quote)**: 33.1503
- **Sharpe Ratio**: 3.9821
- **Max Drawdown %**: 3.2316
- **Profit Factor**: 3.185645929861484
- **Trade Count**: 487
- **Total Fees (quote)**: 6.3304
- **Maker Fees**: 2.2677
- **Taker Fees**: 4.0627
- **Fee Drag %**: 1.8365

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0582
- **PnL Component**: 0.0918
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0242
- **Fee Drag Component**: -0.0092
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0464**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 3.55 | 8.49 | 1.37 | 114 | 0.0227 | n/a |
| 1 | 3.54 | 8.36 | 1.12 | 69 | 0.0244 | n/a |
| 2 | 0.95 | 2.71 | 1.19 | 109 | -0.0706 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | -2.42 | -22.92 | 2.45 | 92 | -0.2357 | n/a |
| 6 | -0.49 | -2.29 | 1.91 | 96 | -0.0228 | n/a |
| 7 | 0.74 | 1.66 | 1.13 | 64 | -0.0051 | n/a |
| 8 | -2.40 | -8.28 | 2.59 | 214 | -0.0774 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 8.70 | 3.61 | 3.46 | 0.0435 |
| fees_2x | 7.78 | 3.22 | 3.69 | 0.0287 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 4.01 | 2.79 | 3.92 | 0.0029 |
| very_low_liquidity | -0.42 | -0.47 | 4.37 | -0.1095 |
| high_slippage | 9.32 | 3.86 | 3.30 | 0.0550 |
| extreme_slippage | 8.73 | 3.62 | 3.44 | 0.0485 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 9.93 | 3.75 | 3.23 | 0.0610 |
| spread_widen_25bps | 11.20 | 4.14 | 3.19 | 0.0728 |
| thin_book | -0.75 | -1.34 | 2.38 | -0.1230 |
| very_thin_book | 0.44 | 2.74 | 0.15 | -0.1769 |
| entry_spread_stress | 9.82 | 3.71 | 3.23 | 0.0600 |
| combined_market_deterioration | -1.60 | -1.67 | 4.58 | -0.1140 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0028)
- **Trend**: ranging (efficiency: 0.0021)
- **Best holdout score**: -0.0145 (rank #4)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9709 | -0.0179 | 0.25 | 1.94 | 177 |
| 1 | 0.0229 | -0.2682 | -4.04 | 4.10 | 171 |
| 2 | 0.0225 | -0.1704 | -1.63 | 2.10 | 75 |
| 3 | 0.0219 | -0.1857 | -1.73 | 2.13 | 75 |
| 4 | 0.0218 | -0.0145 | 0.26 | 1.80 | 128 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51884
- **Expected rows**: 51899
- **Missing rows**: 15
- **Forward-fill count**: 233
- **Forward-fill fraction**: 0.004490787140544291
- **Longest gap (seconds)**: 4800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0456 <= 0; recent PnL -2.3971% < 0
- **Objective score**: -0.045564035103940886
- **PnL %**: -2.397099878223299
- **Trade count**: 214

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0796 <= 0; recent PnL -2.4145% < 0
- **Objective score**: -0.07955402340491863
- **PnL %**: -2.414544785867856
- **Trade count**: 74

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1242 <= 0
- **Objective score**: -0.12423165611237695
- **PnL %**: 0.21787743867492976
- **Trade count**: 21

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.13225732196009535
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1044, -0.1725 |
| bb_std | -0.1323, -0.1725 |
| bbp_entry_threshold | -0.1325, -0.1323 |
| rsi_length | -0.0640, -0.1305 |
| rsi_entry_threshold | -0.1305, -0.0690 |
| trend_ema_length | -0.1792, -0.0812 |
| max_atr_pct_for_entry | -0.1323, -0.1323 |
| volume_filter_window | -0.1158, -0.1264 |
| min_volume_quantile | -0.1129, -0.1895 |
| stop_loss | -0.1534, -0.1381 |
| take_profit | -0.1323, -0.1323 |
| cooldown_time | -0.1323, -0.1323 |
| total_amount_quote | -0.1342, -0.1205 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3522925944325163
- **Max CV**: 0.577699804935341
- **Clustered params**: take_profit, total_amount_quote
- **Scattered params**: stop_loss, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.5292 | 0.020141885648512107 | 0.07730775659912727 | 0.03614436671441102 |
| take_profit | 0.1689 | 0.03158387073197943 | 0.056655632472024875 | 0.04688230475912504 |
| cooldown_time | 0.5777 | 13797.0 | 60306.0 | 27161.1 |
| total_amount_quote | 0.1333 | 277.99275617456897 | 430.77619540054036 | 369.308160008585 |

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
| recent_objective | > 0 | -0.045564035103940886 | FAIL |
| recent_pnl | >= 0 | -2.397099878223299 | FAIL |
| recent_trades | >= 5 | 214 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.017880685576480062 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.045564035103940886, pnl=-2.397099878223299, trades=214, reason=recent objective score -0.0456 <= 0; recent PnL -2.3971% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.07955402340491863, pnl=-2.414544785867856, trades=74, reason=recent objective score -0.0796 <= 0; recent PnL -2.4145% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.12423165611237695, pnl=0.21787743867492976, trades=21, reason=recent objective score -0.1242 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3522925944325163 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51884 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0456 <= 0; recent PnL -2.3971% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0796 <= 0; recent PnL -2.4145% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1242 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51884
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8050
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T11:49:55.442847+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 5010
- **validation_status**: validated_fail
