# PMM Dynamic Optimization Report: mexc_APT-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 04:45:58 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T04:45:58.203156+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 466 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: APT-USDT
- **interval**: 5m
- **n_candles**: 51710
- **dataset_hash**: 881b421d384814a8ebbce420b111b9125a2fc18a2502ae258a3c4633f29f83ab
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 799.6790147780679
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 15 |
| bb_length | 93 |
| bb_std | 2.8768721587771324 |
| bbp_entry_threshold | 0.3667294641540456 |
| cooldown_time | 29129 |
| max_atr_pct_for_entry | 0.04777410193406458 |
| min_volume_quantile | 0.47294359020888865 |
| rsi_entry_threshold | 48.128824832340186 |
| rsi_length | 25 |
| stop_loss | 0.02762788846311005 |
| take_profit | 0.00751050369544075 |
| take_profit_order_type | LIMIT |
| time_limit | 78107 |
| total_amount_quote | 799.6790147780679 |
| trailing_stop_activation | 0.0005330771008937784 |
| trailing_stop_delta | 0.009652918950762184 |
| trend_ema_length | 55 |
| use_trend_filter | False |
| volume_filter_window | 97 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 799.6790147780679 |
| Selected | 799.6790147780679 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.6493
- **Net PnL (quote)**: -21.1856
- **Sharpe Ratio**: -1.4887
- **Max Drawdown %**: 5.0838
- **Profit Factor**: 0.5546121362923592
- **Trade Count**: 37
- **Total Fees (quote)**: 8.3141
- **Maker Fees**: 4.1583
- **Taker Fees**: 4.1558
- **Fee Drag %**: 1.0397

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1223
- **PnL Component**: -0.0268
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0381
- **Fee Drag Component**: -0.0052
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0520
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1391**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 5.67 | 10.02 | 1.50 | 35 | -0.0211 | n/a |
| 1 | -0.56 | -0.61 | 3.79 | 44 | -0.0625 | n/a |
| 2 | -1.96 | -3.25 | 2.93 | 7 | -0.2406 | n/a |
| 3 | -1.11 | -2.29 | 2.80 | 22 | -0.1484 | n/a |
| 4 | 7.66 | 9.59 | 1.47 | 30 | -0.0224 | n/a |
| 5 | -1.78 | -3.30 | 2.82 | 22 | -0.1553 | n/a |
| 6 | -2.85 | -8.23 | 2.85 | 2 | -1000.0000 | n/a |
| 7 | 4.52 | 4.24 | 2.20 | 22 | -0.0876 | n/a |
| 8 | 0.52 | 2.05 | 1.03 | 15 | -0.1443 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -3.17 | -1.79 | 5.21 | -0.1272 |
| fees_2x | -1.26 | -0.88 | 2.96 | -0.1148 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.10 | -0.75 | 2.80 | -0.0563 |
| very_low_liquidity | -2.36 | -3.70 | 2.64 | -0.2121 |
| high_slippage | -1.49 | -1.06 | 3.01 | -0.1119 |
| extreme_slippage | -1.10 | -1.54 | 1.30 | -0.2153 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.17 | -0.74 | 2.80 | -0.1404 |
| spread_widen_25bps | -1.52 | -3.83 | 1.67 | -0.2122 |
| thin_book | -1.65 | -2.55 | 2.05 | -0.2124 |
| very_thin_book | -2.27 | -1.00 | 4.99 | -0.1718 |
| entry_spread_stress | -1.45 | -3.60 | 1.69 | -0.2116 |
| combined_market_deterioration | -1.85 | -3.36 | 2.13 | -0.2249 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0036)
- **Trend**: ranging (efficiency: 0.0062)
- **Best holdout score**: -0.0033 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0611 | -0.0033 | 2.51 | 2.50 | 49 |
| 1 | -0.0739 | -0.1066 | -0.43 | 3.36 | 32 |
| 2 | -0.0846 | -0.0535 | 3.93 | 1.95 | 32 |
| 3 | -0.0992 | -1000.0000 | -1.45 | 3.00 | 2 |
| 4 | -0.1066 | -0.1718 | -1.41 | 2.54 | 16 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51710
- **Expected rows**: 51841
- **Missing rows**: 131
- **Forward-fill count**: 58
- **Forward-fill fraction**: 0.0011216399149100754
- **Longest gap (seconds)**: 25800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0484 <= 0
- **Objective score**: -0.048357514030486146
- **PnL %**: 4.085345069391309
- **Trade count**: 33

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1362 <= 0
- **Objective score**: -0.1362037439182955
- **PnL %**: 0.5674146980972625
- **Trade count**: 16

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2227 <= 0; recent PnL -2.7932% < 0
- **Objective score**: -0.22272709346531008
- **PnL %**: -2.7932202958989443
- **Trade count**: 7

## Sensitivity Analysis

- **Sensitivity penalty**: 0.038461538461538464
- **Baseline score**: -0.1222264665258491
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1224, -0.0741 |
| bb_std | -0.1452, -0.1249 |
| bbp_entry_threshold | -0.1040, -0.1604 |
| rsi_length | -0.1222, -0.1222 |
| rsi_entry_threshold | -0.1222, -0.1228 |
| trend_ema_length | -0.1222, -0.1222 |
| max_atr_pct_for_entry | -0.1222, -0.1222 |
| volume_filter_window | -0.1264, -0.1222 |
| min_volume_quantile | -0.0639, -0.1174 |
| stop_loss | -0.1280, -0.1125 |
| take_profit | -0.1222, -0.1222 |
| cooldown_time | -0.2137, -0.1012 |
| total_amount_quote | -0.1185, -0.0780 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5759643650051948
- **Max CV**: 0.9619749648075767
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4451 | 0.018038744812412952 | 0.0708241160790522 | 0.04044215117845707 |
| take_profit | 0.6990 | 0.005739002332439683 | 0.02770647449150117 | 0.011920898541010364 |
| cooldown_time | 0.9620 | 3100.0 | 59783.0 | 19175.8 |
| total_amount_quote | 0.1978 | 478.863363309123 | 990.8181219899975 | 804.2930982195674 |

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
| recent_objective | > 0 | -0.048357514030486146 | FAIL |
| recent_pnl | >= 0 | 4.085345069391309 | PASS |
| recent_trades | >= 5 | 33 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.038461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.003340454080636264 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.038461538461538464 |
| recent_28d | FAIL | score=-0.048357514030486146, pnl=4.085345069391309, trades=33, reason=recent objective score -0.0484 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.1362037439182955, pnl=0.5674146980972625, trades=16, reason=recent objective score -0.1362 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.22272709346531008, pnl=-2.7932202958989443, trades=7, reason=recent objective score -0.2227 <= 0; recent PnL -2.7932% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5759643650051948 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51710 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0484 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1362 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2227 <= 0; recent PnL -2.7932% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51710
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 7934
- **Recent window start**: 1774051500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T04:45:58.203156+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 466
- **validation_status**: validated_fail
