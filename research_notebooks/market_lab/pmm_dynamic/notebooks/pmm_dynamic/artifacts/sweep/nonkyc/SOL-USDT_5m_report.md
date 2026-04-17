# PMM Dynamic Optimization Report: nonkyc_SOL-USDT_5m_sweep_v1

Generated: 2026-04-10 01:05:03 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-10T01:05:03.887430+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 13176 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: SOL-USDT
- **interval**: 5m
- **n_candles**: 52112
- **dataset_hash**: 18c7148ed93d79b295602caca8272758fb6940738dc6e78f9ee013480c33f770
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 868.6075651709208
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.783567525247121 |
| buy_n_levels | 5 |
| buy_side_weight | 0.29600144075606916 |
| buy_spread_base | 1.9012733243440856 |
| buy_spread_ratio | 2.741008409832201 |
| cooldown_time | 4284 |
| executor_refresh_time | 10851 |
| macd_fast | 12 |
| macd_signal | 21 |
| macd_slow | 75 |
| natr_length | 50 |
| sell_n_levels | 7 |
| sell_spread_base | 2.6049978435827352 |
| sell_spread_ratio | 2.1024752636279884 |
| stop_loss | 0.020689624651090865 |
| take_profit | 0.0051750998753367725 |
| time_limit | 92771 |
| total_amount_quote | 868.6075651709208 |
| trailing_stop_activation | 0.03437624758279144 |
| trailing_stop_delta | 0.01014304206168601 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 868.6075651709208 |
| Selected | 868.6075651709208 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -9.4467
- **Net PnL (quote)**: -82.0546
- **Sharpe Ratio**: -7.2096
- **Max Drawdown %**: 10.4772
- **Profit Factor**: 0.49218521579367913
- **Trade Count**: 1311
- **Total Fees (quote)**: 48.1225
- **Maker Fees**: 39.0023
- **Taker Fees**: 9.1202
- **Fee Drag %**: 5.5402
- **TP Min-Notional Failures**: 2458 :warning:
  > 2458 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.2296
- **PnL Component**: -0.0992
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0786
- **Fee Drag Component**: -0.0277
- **Inventory Component**: -0.0238
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0166**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.31 | -4.93 | 0.47 | 79 | -0.0143 | n/a |
| 1 | -0.57 | -13.08 | 0.59 | 86 | -0.0142 | n/a |
| 2 | -0.20 | -6.87 | 0.26 | 89 | -0.0139 | n/a |
| 3 | -0.11 | -4.47 | 0.16 | 85 | -0.0099 | n/a |
| 4 | -1.05 | -14.44 | 1.11 | 101 | -0.0467 | n/a |
| 5 | -0.52 | -7.05 | 0.71 | 102 | -0.0151 | n/a |
| 6 | -0.74 | -15.10 | 0.76 | 89 | -0.0214 | n/a |
| 7 | -0.21 | -7.92 | 0.22 | 86 | -0.0094 | n/a |
| 8 | -0.67 | -14.86 | 0.69 | 96 | -0.0221 | n/a |

## Stress Test Results

Worst Scenario: **combined_market_deterioration** (score: -0.3934)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -12.22 | -9.23 | 13.13 | -0.2950 |
| fees_2x | -14.99 | -11.19 | 15.79 | -0.3615 |
| latency_plus1 | -9.53 | -7.33 | 10.56 | -0.2308 |
| latency_plus2 | -9.84 | -7.39 | 10.91 | -0.2376 |
| latency_plus3 | -10.00 | -7.76 | 11.01 | -0.2390 |
| low_liquidity | -9.45 | -7.21 | 10.48 | -0.2296 |
| very_low_liquidity | -9.65 | -7.25 | 10.74 | -0.2331 |
| high_slippage | -9.71 | -7.39 | 10.73 | -0.2344 |
| extreme_slippage | -10.23 | -7.76 | 11.24 | -0.2442 |
| combined_adverse | -12.52 | -9.50 | 13.42 | -0.3001 |
| spread_widen_10bps | -10.33 | -8.43 | 11.27 | -0.2433 |
| spread_widen_25bps | -13.56 | -8.74 | 14.43 | -0.3149 |
| thin_book | -12.20 | -8.47 | 13.06 | -0.2784 |
| very_thin_book | -11.12 | -12.61 | 11.24 | -0.2355 |
| entry_spread_stress | -10.87 | -8.91 | 11.83 | -0.2540 |
| combined_market_deterioration | -17.21 | -10.75 | 17.99 | -0.3934 |
| severe_adverse | -17.04 | -15.74 | 17.42 | -0.3795 |

## Holdout Validation

- **Holdout bars**: 8809
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0030)
- **Trend**: ranging (efficiency: 0.0012)
- **Best holdout score**: -0.0094 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.3115 | -0.0234 | -0.72 | 0.80 | 193 |
| 1 | -0.0100 | -0.0716 | -1.92 | 2.51 | 403 |
| 2 | -0.0107 | -0.0580 | -1.23 | 1.60 | 328 |
| 3 | -0.0107 | -0.0265 | -1.03 | 1.07 | 208 |
| 4 | -0.0107 | -0.0094 | -0.33 | 0.37 | 4778 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52112
- **Expected rows**: 52112
- **Missing rows**: 0
- **Forward-fill count**: 123
- **Forward-fill fraction**: 0.0023603008903899294
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0239 <= 0; recent PnL -0.8297% < 0
- **Objective score**: -0.023864245667986745
- **PnL %**: -0.8296627885726703
- **Trade count**: 175

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0065 <= 0; recent PnL -0.1520% < 0
- **Objective score**: -0.0064502531110978666
- **PnL %**: -0.15201072381130612
- **Trade count**: 76

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0590 <= 0
- **Objective score**: -0.058970463710574704
- **PnL %**: 0.02545042150172013
- **Trade count**: 36

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.29193416186232884
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.2746, -0.3775 |
| sell_spread_base | -0.2600, -0.2176 |
| stop_loss | -0.2950, -0.3001 |
| take_profit | -0.3588, -0.2889 |
| executor_refresh_time | -0.3011, -0.3607 |
| cooldown_time | -0.2999, -0.2877 |
| total_amount_quote | -0.2948, -0.2983 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2863426481389585
- **Max CV**: 1.0895178731475286
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1066 | 2.2352141652542232 | 2.964294722304065 | 2.6027204090686538 |
| buy_spread_ratio | 0.0458 | 2.3341750130181764 | 2.660200559065992 | 2.498197806961542 |
| sell_spread_base | 0.8657 | 0.20092462442107822 | 2.2762914673496075 | 0.7083717949978281 |
| sell_spread_ratio | 0.2337 | 1.4102599484266887 | 2.802344768544995 | 1.858281574645695 |
| buy_side_weight | 0.1673 | 0.21684016581000728 | 0.3432552054538283 | 0.26973876646249983 |
| amount_skew | 0.0958 | 2.5958654405365786 | 3.504535537243963 | 2.9546574010488884 |
| stop_loss | 1.0895 | 0.010114115394696201 | 0.14327416758309489 | 0.047610037778263836 |
| take_profit | 0.0409 | 0.005113201829389105 | 0.005804398496244338 | 0.005507820313277264 |
| executor_refresh_time | 0.1367 | 9630.0 | 14264.0 | 12657.3 |
| cooldown_time | 0.2427 | 3022.0 | 6275.0 | 4966.2 |
| total_amount_quote | 0.1250 | 672.4925581916423 | 963.0511432577348 | 857.2363279017976 |

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
| recent_objective | > 0 | -0.023864245667986745 | FAIL |
| recent_pnl | >= 0 | -0.8296627885726703 | FAIL |
| recent_trades | >= 5 | 175 | PASS |
| worst_stress | > -10 | -0.39335375052838684 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.02340013153901477 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=combined_market_deterioration score=-0.39335375052838684 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.023864245667986745, pnl=-0.8296627885726703, trades=175, reason=recent objective score -0.0239 <= 0; recent PnL -0.8297% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.0064502531110978666, pnl=-0.15201072381130612, trades=76, reason=recent objective score -0.0065 <= 0; recent PnL -0.1520% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.058970463710574704, pnl=0.02545042150172013, trades=36, reason=recent objective score -0.0590 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2863426481389585 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52112 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0239 <= 0; recent PnL -0.8297% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0065 <= 0; recent PnL -0.1520% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0590 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52112
- **Pre-release bars**: 44047
- **Dev bars**: 35238
- **Holdout bars**: 8809
- **Recent 28d bars**: 8065
- **Recent window start**: 1773354300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-10T01:05:03.887430+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 13176
