# PMM Dynamic Optimization Report: nonkyc_BDX-USDT_5m_sweep_v1

Generated: 2026-04-08 21:00:32 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T21:00:32.609704+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 881 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BDX-USDT
- **interval**: 5m
- **n_candles**: 51913
- **dataset_hash**: ce5bee2db3208814f0902c3613eb35c3aa5b003a4090bd792f4680695fa998e8
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 573.6150838116591
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.7635812415905594 |
| buy_n_levels | 5 |
| buy_side_weight | 0.3340126525301652 |
| buy_spread_base | 3.5692376707660185 |
| buy_spread_ratio | 2.9431598677056905 |
| cooldown_time | 7110 |
| executor_refresh_time | 8028 |
| macd_fast | 25 |
| macd_signal | 9 |
| macd_slow | 27 |
| natr_length | 13 |
| sell_n_levels | 5 |
| sell_spread_base | 2.8925661136280607 |
| sell_spread_ratio | 2.285125016317505 |
| stop_loss | 0.034270490187892064 |
| take_profit | 0.005229471666789432 |
| time_limit | 51271 |
| total_amount_quote | 573.6150838116591 |
| trailing_stop_activation | 0.02001468551824742 |
| trailing_stop_delta | 0.022520121215225643 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 573.6150838116591 |
| Selected | 573.6150838116591 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.6692
- **Net PnL (quote)**: -15.3110
- **Sharpe Ratio**: -2.4546
- **Max Drawdown %**: 3.0737
- **Profit Factor**: 0.5631390324378861
- **Trade Count**: 1284
- **Total Fees (quote)**: 16.4211
- **Maker Fees**: 11.3512
- **Taker Fees**: 5.0698
- **Fee Drag %**: 2.8627
- **TP Min-Notional Failures**: 56510 :warning:
  > 56510 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0938
- **PnL Component**: -0.0271
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0231
- **Fee Drag Component**: -0.0143
- **Inventory Component**: -0.0291
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0259**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.51 | -14.69 | 0.54 | 88 | -0.1725 | n/a |
| 1 | 0.08 | 4.08 | 0.05 | 49 | -0.0087 | n/a |
| 2 | -0.09 | -5.47 | 0.15 | 55 | -0.0236 | n/a |
| 3 | -0.50 | -13.54 | 0.50 | 89 | -0.0818 | n/a |
| 4 | -0.31 | -4.42 | 0.44 | 131 | -0.0232 | n/a |
| 5 | -0.19 | -6.35 | 0.22 | 67 | -0.0272 | n/a |
| 6 | -0.00 | -0.14 | 0.16 | 196 | -0.0144 | n/a |
| 7 | -0.51 | -5.33 | 0.55 | 123 | -0.0178 | n/a |
| 8 | -0.26 | -1.37 | 0.80 | 49 | -0.0183 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1842)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -4.10 | -3.77 | 4.38 | -0.1259 |
| fees_2x | -5.53 | -5.07 | 5.71 | -0.1585 |
| latency_plus1 | -2.67 | -2.46 | 3.07 | -0.0937 |
| latency_plus2 | -2.76 | -2.53 | 3.17 | -0.0955 |
| latency_plus3 | -2.72 | -2.51 | 3.10 | -0.0938 |
| low_liquidity | -3.22 | -2.61 | 3.36 | -0.1031 |
| very_low_liquidity | -4.29 | -2.39 | 4.96 | -0.1689 |
| high_slippage | -2.89 | -2.66 | 3.28 | -0.0976 |
| extreme_slippage | -3.33 | -3.06 | 3.68 | -0.1053 |
| combined_adverse | -5.56 | -4.52 | 5.61 | -0.1782 |
| spread_widen_10bps | -3.52 | -2.99 | 3.94 | -0.1093 |
| spread_widen_25bps | -4.51 | -3.98 | 4.95 | -0.1287 |
| thin_book | -2.55 | -2.84 | 2.83 | -0.0836 |
| very_thin_book | -2.11 | -3.14 | 2.34 | -0.0617 |
| entry_spread_stress | -3.94 | -3.23 | 4.35 | -0.1192 |
| combined_market_deterioration | -4.99 | -5.25 | 5.12 | -0.1344 |
| severe_adverse | -6.34 | -6.11 | 6.46 | -0.1842 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0014)
- **Trend**: ranging (efficiency: 0.0000)
- **Best holdout score**: -0.0186 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1390 | -0.0186 | -0.51 | 0.52 | 317 |
| 1 | -0.0164 | -0.0444 | -0.33 | 0.65 | 770 |
| 2 | -0.0182 | -0.0295 | -0.55 | 0.71 | 372 |
| 3 | -0.0195 | -0.0285 | -0.36 | 0.49 | 467 |
| 4 | -0.0198 | -0.0554 | 0.73 | 1.61 | 763 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51913
- **Expected rows**: 51913
- **Missing rows**: 0
- **Forward-fill count**: 1638
- **Forward-fill fraction**: 0.03155279024521796
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0172 <= 0; recent PnL -0.3134% < 0
- **Objective score**: -0.017215942994099186
- **PnL %**: -0.3134030419818631
- **Trade count**: 106

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1176 <= 0; recent PnL -0.0676% < 0
- **Objective score**: -0.11761267773916642
- **PnL %**: -0.06759484204235941
- **Trade count**: 45

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1481 <= 0
- **Objective score**: -0.1481350258860278
- **PnL %**: 0.006948072891371548
- **Trade count**: 19

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.10063142731654676
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0914, -0.1299 |
| sell_spread_base | -0.1021, -0.1163 |
| stop_loss | -0.1050, -0.1146 |
| take_profit | -0.1028, -0.1108 |
| executor_refresh_time | -0.1033, -0.1166 |
| cooldown_time | -0.1132, -0.1296 |
| total_amount_quote | -0.0982, -0.1869 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.34213609547313334
- **Max CV**: 0.9854945685582432
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1549 | 3.2680833460169305 | 5.22124584197334 | 4.1262319413627315 |
| buy_spread_ratio | 0.1532 | 1.799312620312809 | 2.843104955025491 | 2.2488636979126766 |
| sell_spread_base | 0.8043 | 0.3071777407969453 | 3.713843656410452 | 1.277715458404627 |
| sell_spread_ratio | 0.2226 | 1.3719612119883935 | 2.818609427076329 | 2.1429415982465754 |
| buy_side_weight | 0.3069 | 0.2442238288005329 | 0.6285527168457029 | 0.46485179641599517 |
| amount_skew | 0.2213 | 1.9954452332268453 | 3.8924306927673236 | 3.056399637543702 |
| stop_loss | 0.5823 | 0.014948058715966344 | 0.1753468466831226 | 0.0918360676645567 |
| take_profit | 0.0879 | 0.005142842712515719 | 0.0066838930747298774 | 0.00586470997784924 |
| executor_refresh_time | 0.9855 | 517.0 | 11540.0 | 3695.3 |
| cooldown_time | 0.1069 | 4704.0 | 6794.0 | 6049.0 |
| total_amount_quote | 0.1378 | 587.8949349475953 | 955.6845020182075 | 821.4835409436113 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

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

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.017215942994099186 | FAIL |
| recent_pnl | >= 0 | -0.3134030419818631 | FAIL |
| recent_trades | >= 5 | 106 | PASS |
| worst_stress | > -10 | -0.18419404968914457 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.018576578996279274 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.18419404968914457 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.017215942994099186, pnl=-0.3134030419818631, trades=106, reason=recent objective score -0.0172 <= 0; recent PnL -0.3134% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.11761267773916642, pnl=-0.06759484204235941, trades=45, reason=recent objective score -0.1176 <= 0; recent PnL -0.0676% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.1481350258860278, pnl=0.006948072891371548, trades=19, reason=recent objective score -0.1481 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.34213609547313334 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51913 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0172 <= 0; recent PnL -0.3134% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1176 <= 0; recent PnL -0.0676% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1481 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51913
- **Pre-release bars**: 43848
- **Dev bars**: 35079
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065
- **Recent window start**: 1773251100

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T21:00:32.609704+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 881
