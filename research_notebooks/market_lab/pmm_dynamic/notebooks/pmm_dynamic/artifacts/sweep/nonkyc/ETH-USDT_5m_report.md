# PMM Dynamic Optimization Report: nonkyc_ETH-USDT_5m_sweep_v1

Generated: 2026-04-09 20:26:43 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T20:26:43.587329+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 5286 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ETH-USDT
- **interval**: 5m
- **n_candles**: 52059
- **dataset_hash**: 400fe160581937d69ef718cf1ca7afe7a5088188350d5a932fb02360b30b3937
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 989.1382768625779
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.1627467861139404 |
| buy_n_levels | 7 |
| buy_side_weight | 0.2139558993369628 |
| buy_spread_base | 4.154332314441614 |
| buy_spread_ratio | 1.7210047541111817 |
| cooldown_time | 4520 |
| executor_refresh_time | 10024 |
| macd_fast | 28 |
| macd_signal | 20 |
| macd_slow | 42 |
| natr_length | 30 |
| sell_n_levels | 8 |
| sell_spread_base | 3.004372619323075 |
| sell_spread_ratio | 1.7378642214827122 |
| stop_loss | 0.11183801325021386 |
| take_profit | 0.005352884373011188 |
| time_limit | 133995 |
| total_amount_quote | 989.1382768625779 |
| trailing_stop_activation | 0.05838468499335697 |
| trailing_stop_delta | 0.0010642481918677125 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 989.1382768625779 |
| Selected | 989.1382768625779 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -4.0524
- **Net PnL (quote)**: -40.0834
- **Sharpe Ratio**: -3.0505
- **Max Drawdown %**: 4.8146
- **Profit Factor**: 0.615315726091308
- **Trade Count**: 925
- **Total Fees (quote)**: 22.4478
- **Maker Fees**: 19.7350
- **Taker Fees**: 2.7129
- **Fee Drag %**: 2.2694
- **TP Min-Notional Failures**: 3346 :warning:
  > 3346 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1155
- **PnL Component**: -0.0414
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0361
- **Fee Drag Component**: -0.0113
- **Inventory Component**: -0.0264
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0098**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.29 | 1.89 | 0.54 | 61 | -0.0034 | n/a |
| 1 | -0.30 | -5.89 | 0.35 | 55 | -0.0079 | n/a |
| 2 | -0.01 | -0.76 | 0.09 | 55 | -0.0043 | n/a |
| 3 | -0.00 | -0.00 | 0.13 | 53 | -0.0066 | n/a |
| 4 | -0.61 | -14.66 | 0.66 | 69 | -0.0840 | n/a |
| 5 | -0.17 | -2.93 | 0.39 | 63 | -0.0084 | n/a |
| 6 | -0.32 | -8.31 | 0.34 | 61 | -0.0080 | n/a |
| 7 | -0.11 | -4.33 | 0.16 | 37 | -0.0561 | n/a |
| 8 | -0.39 | -4.59 | 0.55 | 46 | -0.0260 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.2330)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -5.19 | -3.91 | 5.86 | -0.1412 |
| fees_2x | -6.32 | -4.76 | 6.93 | -0.1672 |
| latency_plus1 | -4.06 | -3.06 | 4.83 | -0.1157 |
| latency_plus2 | -4.08 | -3.07 | 4.84 | -0.1158 |
| latency_plus3 | -4.07 | -3.07 | 4.83 | -0.1157 |
| low_liquidity | -4.07 | -3.06 | 4.83 | -0.1158 |
| very_low_liquidity | -4.07 | -3.06 | 4.84 | -0.1160 |
| high_slippage | -4.12 | -3.10 | 4.88 | -0.1167 |
| extreme_slippage | -4.26 | -3.20 | 5.01 | -0.1192 |
| combined_adverse | -5.28 | -3.97 | 5.95 | -0.1428 |
| spread_widen_10bps | -4.74 | -3.32 | 5.39 | -0.1282 |
| spread_widen_25bps | -6.40 | -3.58 | 7.40 | -0.1678 |
| thin_book | -4.97 | -4.25 | 5.34 | -0.1231 |
| very_thin_book | -5.38 | -4.32 | 5.48 | -0.1295 |
| entry_spread_stress | -6.97 | -3.59 | 8.04 | -0.1829 |
| combined_market_deterioration | -7.61 | -4.97 | 8.09 | -0.1927 |
| severe_adverse | -9.72 | -5.86 | 10.12 | -0.2330 |

## Holdout Validation

- **Holdout bars**: 8798
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0029)
- **Trend**: ranging (efficiency: 0.0005)
- **Best holdout score**: -0.0115 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1743 | -0.0115 | -0.48 | 0.52 | 110 |
| 1 | -0.0067 | -0.0753 | -2.76 | 2.81 | 307 |
| 2 | -0.0070 | -0.0552 | -2.04 | 2.26 | 522 |
| 3 | -0.0072 | -0.0347 | -0.87 | 0.96 | 415 |
| 4 | -0.0077 | -0.1222 | -4.76 | 4.86 | 502 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52059
- **Expected rows**: 52059
- **Missing rows**: 0
- **Forward-fill count**: 128
- **Forward-fill fraction**: 0.002458748727405444
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0105 <= 0; recent PnL -0.3940% < 0
- **Objective score**: -0.010483441862973253
- **PnL %**: -0.3940316276188475
- **Trade count**: 83

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0626 <= 0; recent PnL -0.0324% < 0
- **Objective score**: -0.06257221016576564
- **PnL %**: -0.03244627561406302
- **Trade count**: 35

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1339 <= 0; recent PnL -0.0041% < 0
- **Objective score**: -0.13389900692743642
- **PnL %**: -0.004095636209373584
- **Trade count**: 17

## Sensitivity Analysis

- **Sensitivity penalty**: 0.2857142857142857
- **Baseline score**: -0.13489902474126556
- **Sign flips**: 0
- **Collapse count**: 4
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1574, -0.2099 |
| sell_spread_base | -0.2040, -0.1626 |
| stop_loss | -0.1358, -0.1276 |
| take_profit | -0.1525, -0.1356 |
| executor_refresh_time | -0.1720, -0.1662 |
| cooldown_time | -0.1691, -0.2082 |
| total_amount_quote | -0.1329, -0.2713 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.34111431614334176
- **Max CV**: 1.0632128334330462
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1251 | 3.732668256329068 | 5.363989579911244 | 4.419775863511552 |
| buy_spread_ratio | 0.2128 | 1.3244885892119564 | 2.285777440061884 | 1.7150453177662068 |
| sell_spread_base | 0.9002 | 0.2636052579980151 | 3.004372619323075 | 1.0969144634273205 |
| sell_spread_ratio | 0.2854 | 1.280625888405883 | 2.969860297162446 | 1.83004088915937 |
| buy_side_weight | 0.1554 | 0.20225863242697872 | 0.3168994369785696 | 0.26115938229412733 |
| amount_skew | 0.2412 | 1.4008250631047188 | 3.015313736955953 | 2.0608869807287937 |
| stop_loss | 1.0632 | 0.010987687344060706 | 0.1322568668169823 | 0.04671289864733247 |
| take_profit | 0.1050 | 0.0052149323293411666 | 0.007214708112215267 | 0.005585476296519171 |
| executor_refresh_time | 0.3851 | 4092.0 | 13806.0 | 9094.2 |
| cooldown_time | 0.2415 | 2650.0 | 6156.0 | 4775.6 |
| total_amount_quote | 0.0373 | 898.7944847365177 | 997.3509741307013 | 946.9264093988835 |

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
| recent_objective | > 0 | -0.010483441862973253 | FAIL |
| recent_pnl | >= 0 | -0.3940316276188475 | FAIL |
| recent_trades | >= 5 | 83 | PASS |
| worst_stress | > -10 | -0.23300265617107546 | PASS |
| sensitivity_penalty | < 0.50 | 0.2857142857142857 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.011468530665736436 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.23300265617107546 |
| sensitivity | PASS | penalty=0.2857142857142857 |
| recent_28d | FAIL | score=-0.010483441862973253, pnl=-0.3940316276188475, trades=83, reason=recent objective score -0.0105 <= 0; recent PnL -0.3940% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.06257221016576564, pnl=-0.03244627561406302, trades=35, reason=recent objective score -0.0626 <= 0; recent PnL -0.0324% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.13389900692743642, pnl=-0.004095636209373584, trades=17, reason=recent objective score -0.1339 <= 0; recent PnL -0.0041% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.34111431614334176 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52059 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0105 <= 0; recent PnL -0.3940% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0626 <= 0; recent PnL -0.0324% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1339 <= 0; recent PnL -0.0041% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52059
- **Pre-release bars**: 43994
- **Dev bars**: 35196
- **Holdout bars**: 8798
- **Recent 28d bars**: 8065
- **Recent window start**: 1773338400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T20:26:43.587329+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 5286
