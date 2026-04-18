# PMM Dynamic Optimization Report: mexc_ATOM-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 06:19:52 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T06:19:52.808612+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 306 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ATOM-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 7f09c9187f8f3354dafc182b6ebca9b15901cb6b1214f047b365777798f88c78
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 809.8640340556015
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 13 |
| bb_length | 75 |
| bb_std | 1.058248283532468 |
| bbp_entry_threshold | 0.0814351044464695 |
| cooldown_time | 20348 |
| max_atr_pct_for_entry | 0.024036217751014763 |
| min_volume_quantile | 0.0362487968597657 |
| rsi_entry_threshold | 46.16179603855479 |
| rsi_length | 11 |
| stop_loss | 0.036441320840609345 |
| take_profit | 0.05391648727763326 |
| take_profit_order_type | LIMIT |
| time_limit | 310905 |
| total_amount_quote | 809.8640340556015 |
| trailing_stop_activation | 0.0003593490403289523 |
| trailing_stop_delta | 0.01380147483956555 |
| trend_ema_length | 253 |
| use_trend_filter | False |
| volume_filter_window | 524 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 809.8640340556015 |
| Selected | 809.8640340556015 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.5103
- **Net PnL (quote)**: -12.2314
- **Sharpe Ratio**: -0.8481
- **Max Drawdown %**: 3.6549
- **Profit Factor**: 0.6192563895736942
- **Trade Count**: 65
- **Total Fees (quote)**: 7.4498
- **Maker Fees**: 3.7254
- **Taker Fees**: 3.7244
- **Fee Drag %**: 0.9199

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0473
- **PnL Component**: -0.0152
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0274
- **Fee Drag Component**: -0.0046
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0730**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 1.89 | 4.14 | 0.91 | 64 | 0.0080 | n/a |
| 1 | 1.37 | 2.68 | 1.43 | 64 | -0.0005 | n/a |
| 2 | 1.43 | 4.18 | 1.58 | 62 | -0.0140 | n/a |
| 3 | -1.72 | -4.65 | 2.12 | 8 | -0.2024 | n/a |
| 4 | 4.73 | 4.53 | 3.23 | 63 | -0.0460 | n/a |
| 5 | -2.07 | -6.30 | 2.26 | 7 | -0.2110 | n/a |
| 6 | 3.29 | 5.44 | 2.18 | 88 | 0.0102 | n/a |
| 7 | 0.46 | 2.00 | 1.01 | 33 | -0.0733 | n/a |
| 8 | -1.04 | -3.26 | 2.09 | 16 | -0.1636 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.99 | -1.14 | 3.72 | -0.0544 |
| fees_2x | -2.85 | -1.65 | 3.81 | -0.0660 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.45 | -0.83 | 3.68 | -0.0465 |
| very_low_liquidity | -2.11 | -1.21 | 3.56 | -0.0509 |
| high_slippage | -2.94 | -1.90 | 3.84 | -0.0632 |
| extreme_slippage | -1.05 | -2.52 | 1.11 | -0.1854 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.09 | -1.12 | 3.74 | -0.0535 |
| spread_widen_25bps | -3.85 | -1.32 | 5.61 | -0.0860 |
| thin_book | -2.84 | -1.16 | 3.72 | -0.1668 |
| very_thin_book | -2.93 | -1.60 | 3.09 | -0.2694 |
| entry_spread_stress | -1.80 | -0.72 | 3.72 | -0.0505 |
| combined_market_deterioration | -3.77 | -2.45 | 3.85 | -0.1095 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0031)
- **Trend**: ranging (efficiency: 0.0174)
- **Best holdout score**: -0.0934 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0237 | -1000.0000 | -3.65 | 3.75 | 3 |
| 1 | -0.0168 | -0.1979 | -3.73 | 4.53 | 19 |
| 2 | -0.0463 | -0.0934 | 0.60 | 4.07 | 34 |
| 3 | -0.0489 | -1000.0000 | -1.87 | 1.93 | 2 |
| 4 | -0.0501 | -0.2130 | -1.93 | 2.70 | 7 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 11
- **Forward-fill fraction**: 0.00021218726490615535
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0694 <= 0; recent PnL -1.0134% < 0
- **Objective score**: -0.06943397697206961
- **PnL %**: -1.0133619458647392
- **Trade count**: 40

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.007687910360498627
- **PnL %**: 1.4492248067162519
- **Trade count**: 89

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.0021078885254003765
- **PnL %**: 0.7670004632224567
- **Trade count**: 50

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.33232318255166704
- **Max CV**: 0.536080950151979
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2427 | 0.02675530228483605 | 0.06054670969048219 | 0.040106089922547786 |
| take_profit | 0.5361 | 0.009783019854616628 | 0.05391648727763326 | 0.025705457403287467 |
| cooldown_time | 0.4006 | 6384.0 | 28680.0 | 17102.1 |
| total_amount_quote | 0.1499 | 556.436230786458 | 990.2679068101544 | 866.9158807194551 |

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
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.06943397697206961 | FAIL |
| recent_pnl | >= 0 | -1.0133619458647392 | FAIL |
| recent_trades | >= 5 | 40 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | SKIPPED |  |
| recent_28d | FAIL | score=-0.06943397697206961, pnl=-1.0133619458647392, trades=40, reason=recent objective score -0.0694 <= 0; recent PnL -1.0134% < 0 |
| recent_14d_info | PASS | informational only; score=0.007687910360498627, pnl=1.4492248067162519, trades=89, reason= |
| recent_7d_info | PASS | informational only; score=0.0021078885254003765, pnl=0.7670004632224567, trades=50, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.33232318255166704 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0694 <= 0; recent PnL -1.0134% < 0 |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | PASS | recent_7d_info | — | — |  |
| sensitivity | false | NOT_RUN | — | — | — | not executed |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51841
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065
- **Recent window start**: 1774011900

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T06:19:52.808612+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 306
- **validation_status**: validated_fail
