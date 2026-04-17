# PMM Dynamic Optimization Report: nonkyc_BTC-USDT_5m_sweep_v1

Generated: 2026-04-09 17:59:38 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T17:59:38.205035+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 13598 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 52003
- **dataset_hash**: 3153adaa238a128f66c85b9c907b42e7d956043f7ef7ca450fd4c4807f9a0fb7
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 984.5540951200568
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.499023182456151 |
| buy_n_levels | 6 |
| buy_side_weight | 0.25988054353678425 |
| buy_spread_base | 2.4044744416297346 |
| buy_spread_ratio | 2.6878347950921575 |
| cooldown_time | 4613 |
| executor_refresh_time | 13668 |
| macd_fast | 38 |
| macd_signal | 7 |
| macd_slow | 75 |
| natr_length | 48 |
| sell_n_levels | 6 |
| sell_spread_base | 5.94174295575616 |
| sell_spread_ratio | 2.9706567015868166 |
| stop_loss | 0.02655999022616672 |
| take_profit | 0.005029240539818734 |
| time_limit | 17188 |
| total_amount_quote | 984.5540951200568 |
| trailing_stop_activation | 0.06910403650501246 |
| trailing_stop_delta | 0.0031504873652882692 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 984.5540951200568 |
| Selected | 984.5540951200568 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.3057
- **Net PnL (quote)**: -3.0097
- **Sharpe Ratio**: -0.3068
- **Max Drawdown %**: 1.6440
- **Profit Factor**: 0.9093811245766795
- **Trade Count**: 543
- **Total Fees (quote)**: 18.3836
- **Maker Fees**: 13.6539
- **Taker Fees**: 4.7297
- **Fee Drag %**: 1.8672
- **TP Min-Notional Failures**: 1556 :warning:
  > 1556 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0335
- **PnL Component**: -0.0031
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0123
- **Fee Drag Component**: -0.0093
- **Inventory Component**: -0.0087
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0114**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.09 | -3.18 | 0.23 | 53 | -0.0061 | n/a |
| 1 | -0.35 | -11.79 | 0.39 | 58 | -0.0139 | n/a |
| 2 | -0.14 | -9.91 | 0.18 | 52 | -0.0156 | n/a |
| 3 | -0.07 | -2.87 | 0.13 | 59 | -0.0052 | n/a |
| 4 | -0.36 | -9.80 | 0.40 | 69 | -0.0169 | n/a |
| 5 | -0.30 | -9.72 | 0.31 | 71 | -0.0093 | n/a |
| 6 | -0.43 | -10.65 | 0.43 | 68 | -0.0153 | n/a |
| 7 | -0.11 | -5.81 | 0.13 | 56 | -0.0056 | n/a |
| 8 | -0.20 | -4.95 | 0.28 | 64 | -0.0078 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1211)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.24 | -1.30 | 2.42 | -0.0534 |
| fees_2x | -2.17 | -2.31 | 3.21 | -0.0735 |
| latency_plus1 | -0.32 | -0.32 | 1.65 | -0.0314 |
| latency_plus2 | -0.45 | -0.46 | 1.78 | -0.0338 |
| latency_plus3 | -0.53 | -0.54 | 1.81 | -0.0372 |
| low_liquidity | -0.31 | -0.31 | 1.64 | -0.0335 |
| very_low_liquidity | -0.30 | -0.30 | 1.64 | -0.0334 |
| high_slippage | -0.43 | -0.43 | 1.75 | -0.0355 |
| extreme_slippage | -0.67 | -0.68 | 1.96 | -0.0394 |
| combined_adverse | -1.38 | -1.44 | 2.53 | -0.0534 |
| spread_widen_10bps | -1.59 | -1.62 | 2.82 | -0.0562 |
| spread_widen_25bps | -1.89 | -1.90 | 3.16 | -0.0616 |
| thin_book | -2.44 | -9.25 | 2.51 | -0.0601 |
| very_thin_book | -2.26 | -10.50 | 2.30 | -0.0525 |
| entry_spread_stress | -1.67 | -1.70 | 2.84 | -0.0571 |
| combined_market_deterioration | -3.56 | -12.92 | 3.61 | -0.0851 |
| severe_adverse | -5.46 | -17.04 | 5.53 | -0.1211 |

## Holdout Validation

- **Holdout bars**: 8789
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0024)
- **Trend**: ranging (efficiency: 0.0003)
- **Best holdout score**: -0.0153 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0773 | -0.0153 | -0.55 | 0.62 | 139 |
| 1 | -0.0056 | -0.0760 | -2.47 | 2.56 | 363 |
| 2 | -0.0072 | -0.0820 | -2.82 | 2.84 | 272 |
| 3 | -0.0076 | -0.1212 | -1.83 | 2.87 | 465 |
| 4 | -0.0078 | -0.0215 | -0.55 | 0.61 | 144 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52003
- **Expected rows**: 52012
- **Missing rows**: 9
- **Forward-fill count**: 276
- **Forward-fill fraction**: 0.005307386112339673
- **Longest gap (seconds)**: 3000

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0066 <= 0; recent PnL -0.0759% < 0
- **Objective score**: -0.006577823862619041
- **PnL %**: -0.07585503502898204
- **Trade count**: 124

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0053 <= 0; recent PnL -0.0748% < 0
- **Objective score**: -0.005259852917853166
- **PnL %**: -0.07476699977566721
- **Trade count**: 63

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2526 <= 0; recent PnL -0.0387% < 0
- **Objective score**: -0.25260947562000274
- **PnL %**: -0.03871387191159572
- **Trade count**: 23

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: -0.04843445929347789
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1506, -0.0730 |
| sell_spread_base | -0.0507, -0.0592 |
| stop_loss | -0.0470, -0.0462 |
| take_profit | -0.0673, -0.0535 |
| executor_refresh_time | -0.0419, -0.0519 |
| cooldown_time | -0.0561, -0.0464 |
| total_amount_quote | -0.0479, -0.0484 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.23444995954193415
- **Max CV**: 0.7693622900688664
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1183 | 1.9811731755603919 | 2.870594513637613 | 2.4568770154872674 |
| buy_spread_ratio | 0.0950 | 2.1225093101300025 | 2.8833330768347265 | 2.577877850106713 |
| sell_spread_base | 0.7694 | 0.5869814975809642 | 5.94174295575616 | 2.828061644949171 |
| sell_spread_ratio | 0.3025 | 1.209063322251569 | 2.9706567015868166 | 1.9880601837920864 |
| buy_side_weight | 0.3361 | 0.22935049301394084 | 0.590666554601758 | 0.4054621228637537 |
| amount_skew | 0.1780 | 2.499023182456151 | 3.924245167031301 | 3.2554107547312867 |
| stop_loss | 0.3064 | 0.010262469042059208 | 0.029363782764513333 | 0.018474509940365667 |
| take_profit | 0.0545 | 0.005029240539818734 | 0.005972908763013285 | 0.005400964127518147 |
| executor_refresh_time | 0.1187 | 10015.0 | 14393.0 | 12213.0 |
| cooldown_time | 0.2031 | 4201.0 | 7161.0 | 5676.5 |
| total_amount_quote | 0.0970 | 777.111581603977 | 994.6398317435142 | 900.9915148686365 |

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
| recent_objective | > 0 | -0.006577823862619041 | FAIL |
| recent_pnl | >= 0 | -0.07585503502898204 | FAIL |
| recent_trades | >= 5 | 124 | PASS |
| worst_stress | > -10 | -0.12109503817257757 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.015268179636811471 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.12109503817257757 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.006577823862619041, pnl=-0.07585503502898204, trades=124, reason=recent objective score -0.0066 <= 0; recent PnL -0.0759% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.005259852917853166, pnl=-0.07476699977566721, trades=63, reason=recent objective score -0.0053 <= 0; recent PnL -0.0748% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.25260947562000274, pnl=-0.03871387191159572, trades=23, reason=recent objective score -0.2526 <= 0; recent PnL -0.0387% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.23444995954193415 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52003 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0066 <= 0; recent PnL -0.0759% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0053 <= 0; recent PnL -0.0748% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2526 <= 0; recent PnL -0.0387% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52003
- **Pre-release bars**: 43947
- **Dev bars**: 35158
- **Holdout bars**: 8789
- **Recent 28d bars**: 8056
- **Recent window start**: 1773324300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T17:59:38.205035+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 13598
