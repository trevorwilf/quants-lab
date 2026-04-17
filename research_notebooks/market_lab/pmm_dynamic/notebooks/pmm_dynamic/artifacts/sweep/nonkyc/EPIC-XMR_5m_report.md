# PMM Dynamic Optimization Report: nonkyc_EPIC-XMR_5m_sweep_v1

Generated: 2026-04-09 20:00:51 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T20:00:51.779573+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 2109 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: EPIC-XMR
- **interval**: 5m
- **n_candles**: 35946
- **dataset_hash**: 7c47ff146b6a5fc775d1527f8e1dc22ae6dc3e8dfc79bc62bb55736c604579e1
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 173.81366124500164
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.7075564213596528 |
| buy_n_levels | 9 |
| buy_side_weight | 0.26711438943941185 |
| buy_spread_base | 4.521834046388758 |
| buy_spread_ratio | 2.1618762369315156 |
| cooldown_time | 2423 |
| executor_refresh_time | 10383 |
| macd_fast | 9 |
| macd_signal | 29 |
| macd_slow | 66 |
| natr_length | 19 |
| sell_n_levels | 3 |
| sell_spread_base | 0.5445408276472893 |
| sell_spread_ratio | 1.6786077053174413 |
| stop_loss | 0.1262591543093413 |
| take_profit | 0.07696316688512087 |
| time_limit | 93153 |
| total_amount_quote | 173.81366124500164 |
| trailing_stop_activation | 0.06706214517855624 |
| trailing_stop_delta | 0.0037243264878492675 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 173.81366124500164 |
| Selected | 173.81366124500164 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2.4599
- **Net PnL (quote)**: 4.2757
- **Sharpe Ratio**: 3.6644
- **Max Drawdown %**: 0.4749
- **Profit Factor**: 32.64688453417272
- **Trade Count**: 1541
- **Total Fees (quote)**: 0.1510
- **Maker Fees**: 0.0508
- **Taker Fees**: 0.1002
- **Fee Drag %**: 0.0869

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0172
- **PnL Component**: 0.0243
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0036
- **Fee Drag Component**: -0.0004
- **Inventory Component**: -0.0030
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0025**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.03 | 5.36 | 0.00 | 55 | 0.0003 | n/a |
| 1 | 0.05 | 6.86 | 0.01 | 61 | 0.0004 | n/a |
| 2 | -2.82 | -20.59 | 3.06 | 1689 | -0.3045 | n/a |
| 3 | 0.03 | 4.60 | 0.01 | 39 | -0.0438 | n/a |
| 4 | 0.04 | 1.21 | 0.07 | 229 | -0.0015 | n/a |

## Stress Test Results

Worst Scenario: **very_thin_book** (score: -0.0157)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2.42 | 3.62 | 0.48 | 0.0165 |
| fees_2x | 2.37 | 3.57 | 0.48 | 0.0159 |
| latency_plus1 | 2.46 | 3.66 | 0.47 | 0.0172 |
| latency_plus2 | 2.46 | 3.66 | 0.47 | 0.0172 |
| latency_plus3 | 2.46 | 3.66 | 0.47 | 0.0172 |
| low_liquidity | 1.22 | 3.60 | 0.24 | 0.0082 |
| very_low_liquidity | 0.61 | 3.60 | 0.12 | 0.0041 |
| high_slippage | 2.45 | 3.65 | 0.47 | 0.0171 |
| extreme_slippage | 2.42 | 3.63 | 0.48 | 0.0168 |
| combined_adverse | 1.19 | 3.53 | 0.24 | 0.0078 |
| spread_widen_10bps | 2.45 | 3.65 | 0.48 | 0.0171 |
| spread_widen_25bps | 2.25 | 3.47 | 0.48 | 0.0153 |
| thin_book | 0.39 | 3.61 | 0.10 | 0.0026 |
| very_thin_book | 0.06 | 2.20 | 0.02 | -0.0157 |
| entry_spread_stress | 2.26 | 3.49 | 0.48 | 0.0154 |
| combined_market_deterioration | 0.25 | 0.92 | 0.74 | -0.0048 |
| severe_adverse | 0.26 | 2.32 | 0.14 | 0.0010 |

## Holdout Validation

- **Holdout bars**: 5576
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0072)
- **Trend**: ranging (efficiency: 0.0217)
- **Best holdout score**: -0.1941 (rank #3)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0008 | -0.3323 | -3.03 | 3.08 | 1512 |
| 1 | 0.0043 | -0.3723 | -6.45 | 6.45 | 1414 |
| 2 | 0.0032 | -0.3371 | -2.32 | 2.35 | 1525 |
| 3 | 0.0020 | -0.1941 | -1.90 | 2.17 | 949 |
| 4 | 0.0018 | -0.2840 | -0.36 | 0.41 | 825 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 35946
- **Expected rows**: 35947
- **Missing rows**: 1
- **Forward-fill count**: 717
- **Forward-fill fraction**: 0.019946586546486397
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0003 <= 0; recent worst stress -1000.0000 < -10.0
- **Objective score**: -0.00025133202838854303
- **PnL %**: 0.03925563714080362
- **Trade count**: 235

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1760 <= 0; recent worst stress -1000.0000 < -10.0
- **Objective score**: -0.17596825269693592
- **PnL %**: 0.003570839915790679
- **Trade count**: 6

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1936 <= 0; recent worst stress -1000.0000 < -10.0
- **Objective score**: -0.19359099231335627
- **PnL %**: 0.002483446225700411
- **Trade count**: 5

## Sensitivity Analysis

- **Sensitivity penalty**: 0.35714285714285715
- **Baseline score**: -0.03326432491321161
- **Sign flips**: 1
- **Collapse count**: 4
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1563, -0.0719 |
| sell_spread_base | -0.0333, -0.0333 |
| stop_loss | -0.0375, -0.0352 |
| take_profit | -0.0333, -0.0333 |
| executor_refresh_time | -0.1926, 0.0084 |
| cooldown_time | -0.0333, -0.1160 |
| total_amount_quote | -0.0395, -0.0304 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4633928886498771
- **Max CV**: 0.9090627034229923
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, cooldown_time
- **Scattered params**: sell_spread_base, stop_loss, take_profit, executor_refresh_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0863 | 2.8463326507601066 | 3.8587050615450664 | 3.5714399164847412 |
| buy_spread_ratio | 0.3084 | 1.2033864734228743 | 2.970614572838253 | 1.9340667603507498 |
| sell_spread_base | 0.7004 | 0.29079948504380104 | 4.91764206204386 | 2.3802603143656476 |
| sell_spread_ratio | 0.1926 | 1.4735523181773182 | 2.901157678337651 | 2.34109183541229 |
| buy_side_weight | 0.1433 | 0.48014149361262415 | 0.7845224422297152 | 0.6496666519889487 |
| amount_skew | 0.2009 | 2.0143979387939646 | 3.712590031416015 | 2.8278841285262124 |
| stop_loss | 0.9091 | 0.018601700467257596 | 0.1933896331266498 | 0.06009688780201168 |
| take_profit | 0.7616 | 0.008819920857247691 | 0.0702507263495241 | 0.03189145739640196 |
| executor_refresh_time | 0.7742 | 1364.0 | 9156.0 | 3119.8 |
| cooldown_time | 0.4120 | 2179.0 | 6891.0 | 3896.9 |
| total_amount_quote | 0.6085 | 29.90789166645437 | 195.33984874182374 | 82.25700439614097 |

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
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.00025133202838854303 | FAIL |
| recent_pnl | >= 0 | 0.03925563714080362 | PASS |
| recent_trades | >= 5 | 235 | PASS |
| worst_stress | > -10 | -0.015653467475823437 | PASS |
| sensitivity_penalty | < 0.50 | 0.35714285714285715 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.332272602050361 |
| walkforward | PASS | 5 folds |
| stress | PASS | worst=very_thin_book score=-0.015653467475823437 |
| sensitivity | PASS | penalty=0.35714285714285715 |
| recent_28d | FAIL | score=-0.00025133202838854303, pnl=0.03925563714080362, trades=235, reason=recent objective score -0.0003 <= 0; recent worst stress -1000.0000 < -10.0 |
| recent_14d_info | FAIL | informational only; score=-0.17596825269693592, pnl=0.003570839915790679, trades=6, reason=recent objective score -0.1760 <= 0; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | FAIL | informational only; score=-0.19359099231335627, pnl=0.002483446225700411, trades=5, reason=recent objective score -0.1936 <= 0; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4633928886498771 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 35946 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0003 <= 0; recent worst stress -1000.0000 < -10.0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1760 <= 0; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1936 <= 0; recent worst stress -1000.0000 < -10.0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 35946
- **Pre-release bars**: 27882
- **Dev bars**: 22306
- **Holdout bars**: 5576
- **Recent 28d bars**: 8064
- **Recent window start**: 1773339000

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T20:00:51.779573+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 2109
