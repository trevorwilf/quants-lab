# PMM Dynamic Optimization Report: nonkyc_BCH-USDT_5m_sweep_v1

Generated: 2026-04-09 16:43:16 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T16:43:16.202964+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 9487 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BCH-USDT
- **interval**: 5m
- **n_candles**: 52002
- **dataset_hash**: 0b2b89df2ff02eb31a346d288281d73823dea4ba26ab092fec2880934c152606
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 996.2141851998555
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.3580718696304634 |
| buy_n_levels | 10 |
| buy_side_weight | 0.29328348411219785 |
| buy_spread_base | 3.7857203591484283 |
| buy_spread_ratio | 1.866079311314807 |
| cooldown_time | 6652 |
| executor_refresh_time | 6321 |
| macd_fast | 12 |
| macd_signal | 20 |
| macd_slow | 70 |
| natr_length | 28 |
| sell_n_levels | 2 |
| sell_spread_base | 5.804645302964218 |
| sell_spread_ratio | 2.5410664797264766 |
| stop_loss | 0.011900696648861361 |
| take_profit | 0.005698600517168604 |
| time_limit | 145952 |
| total_amount_quote | 996.2141851998555 |
| trailing_stop_activation | 0.06285023758933957 |
| trailing_stop_delta | 0.002729480048858176 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 996.2141851998555 |
| Selected | 996.2141851998555 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.1810
- **Net PnL (quote)**: -21.7270
- **Sharpe Ratio**: -8.7159
- **Max Drawdown %**: 2.1835
- **Profit Factor**: 0.3757715241049758
- **Trade Count**: 1044
- **Total Fees (quote)**: 14.6579
- **Maker Fees**: 10.1917
- **Taker Fees**: 4.4662
- **Fee Drag %**: 1.4714
- **TP Min-Notional Failures**: 4102 :warning:
  > 4102 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0505
- **PnL Component**: -0.0221
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0164
- **Fee Drag Component**: -0.0074
- **Inventory Component**: -0.0046
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0190**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.13 | -8.92 | 0.14 | 52 | -0.0044 | n/a |
| 1 | -0.21 | -5.99 | 0.42 | 61 | -0.0095 | n/a |
| 2 | -0.08 | -6.12 | 0.10 | 52 | -0.0246 | n/a |
| 3 | -0.22 | -10.68 | 0.24 | 49 | -0.0617 | n/a |
| 4 | -0.79 | -16.98 | 0.82 | 72 | -0.0606 | n/a |
| 5 | -0.21 | -12.73 | 0.22 | 64 | -0.0060 | n/a |
| 6 | -0.52 | -13.63 | 0.55 | 70 | -0.0137 | n/a |
| 7 | -0.04 | -1.49 | 0.10 | 57 | -0.0032 | n/a |
| 8 | -0.54 | -4.32 | 0.59 | 78 | -0.1098 | n/a |

## Stress Test Results

Worst Scenario: **very_thin_book** (score: -0.1987)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.92 | -11.09 | 2.92 | -0.0672 |
| fees_2x | -3.65 | -13.15 | 3.65 | -0.0840 |
| latency_plus1 | -2.18 | -8.70 | 2.18 | -0.0499 |
| latency_plus2 | -2.20 | -8.78 | 2.21 | -0.0504 |
| latency_plus3 | -2.20 | -8.74 | 2.20 | -0.0509 |
| low_liquidity | -2.49 | -9.12 | 2.50 | -0.0564 |
| very_low_liquidity | -2.59 | -8.95 | 2.60 | -0.0855 |
| high_slippage | -2.29 | -9.00 | 2.30 | -0.0525 |
| extreme_slippage | -2.52 | -9.51 | 2.52 | -0.0564 |
| combined_adverse | -3.39 | -11.67 | 3.39 | -0.0801 |
| spread_widen_10bps | -2.57 | -8.61 | 2.60 | -0.0597 |
| spread_widen_25bps | -3.10 | -11.05 | 3.11 | -0.0674 |
| thin_book | -3.64 | -11.00 | 3.64 | -0.0757 |
| very_thin_book | -2.50 | -7.63 | 2.62 | -0.1987 |
| entry_spread_stress | -2.81 | -10.02 | 2.81 | -0.0619 |
| combined_market_deterioration | -4.50 | -9.26 | 4.90 | -0.1036 |
| severe_adverse | -5.85 | -15.86 | 5.88 | -0.1226 |

## Holdout Validation

- **Holdout bars**: 8787
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0025)
- **Trend**: ranging (efficiency: 0.0108)
- **Best holdout score**: -0.0155 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1246 | -0.0155 | -0.58 | 0.61 | 132 |
| 1 | -0.0055 | -0.0203 | -0.80 | 0.80 | 259 |
| 2 | -0.0073 | -0.0537 | -1.52 | 1.93 | 330 |
| 3 | -0.0078 | -0.0707 | -2.51 | 2.72 | 341 |
| 4 | -0.0079 | -0.0362 | -1.30 | 1.40 | 215 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52002
- **Expected rows**: 52002
- **Missing rows**: 0
- **Forward-fill count**: 468
- **Forward-fill fraction**: 0.008999653859466944
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1084 <= 0; recent PnL -0.6989% < 0
- **Objective score**: -0.10840314780668206
- **PnL %**: -0.6989422791593165
- **Trade count**: 104

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2186 <= 0; recent PnL -0.1689% < 0
- **Objective score**: -0.2186217617571014
- **PnL %**: -0.16892455859189529
- **Trade count**: 20

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3173 <= 0; recent PnL -0.0765% < 0
- **Objective score**: -0.317337259092644
- **PnL %**: -0.07651695226690607
- **Trade count**: 8

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: -0.07646396519903834
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1956, -0.1340 |
| sell_spread_base | -0.0745, -0.0765 |
| stop_loss | -0.0860, -0.0700 |
| take_profit | -0.0823, -0.0882 |
| executor_refresh_time | -0.0786, -0.0908 |
| cooldown_time | -0.0916, -0.0833 |
| total_amount_quote | -0.0770, -0.1764 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.24681661853505776
- **Max CV**: 0.7702018937216576
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1761 | 2.2038899939844154 | 3.7857203591484283 | 3.16882680425245 |
| buy_spread_ratio | 0.1323 | 1.866079311314807 | 2.7300038103300057 | 2.2255865984951013 |
| sell_spread_base | 0.7702 | 0.5962122911741632 | 5.804645302964218 | 2.26289754716226 |
| sell_spread_ratio | 0.1733 | 1.5319264509863777 | 2.983055949903368 | 2.4183831386872807 |
| buy_side_weight | 0.2556 | 0.21034916664379152 | 0.43179324950157016 | 0.2968971358265972 |
| amount_skew | 0.1794 | 1.858638681619247 | 3.6575597392172403 | 2.759540454206747 |
| stop_loss | 0.2596 | 0.010342040982145865 | 0.02121496838345451 | 0.013738487030862603 |
| take_profit | 0.0403 | 0.005153860792295117 | 0.005881337759053662 | 0.005525013171494281 |
| executor_refresh_time | 0.2533 | 5818.0 | 11676.0 | 8958.4 |
| cooldown_time | 0.4222 | 1418.0 | 6652.0 | 4329.2 |
| total_amount_quote | 0.0525 | 848.435871694291 | 996.2141851998555 | 954.4846109632248 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
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
| recent_objective | > 0 | -0.10840314780668206 | FAIL |
| recent_pnl | >= 0 | -0.6989422791593165 | FAIL |
| recent_trades | >= 5 | 104 | PASS |
| worst_stress | > -10 | -0.19874758872173864 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.015497894167076854 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_thin_book score=-0.19874758872173864 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | FAIL | score=-0.10840314780668206, pnl=-0.6989422791593165, trades=104, reason=recent objective score -0.1084 <= 0; recent PnL -0.6989% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.2186217617571014, pnl=-0.16892455859189529, trades=20, reason=recent objective score -0.2186 <= 0; recent PnL -0.1689% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.317337259092644, pnl=-0.07651695226690607, trades=8, reason=recent objective score -0.3173 <= 0; recent PnL -0.0765% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.24681661853505776 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52002 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1084 <= 0; recent PnL -0.6989% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2186 <= 0; recent PnL -0.1689% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.3173 <= 0; recent PnL -0.0765% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52002
- **Pre-release bars**: 43937
- **Dev bars**: 35150
- **Holdout bars**: 8787
- **Recent 28d bars**: 8065
- **Recent window start**: 1773321300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T16:43:16.202964+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 9487
