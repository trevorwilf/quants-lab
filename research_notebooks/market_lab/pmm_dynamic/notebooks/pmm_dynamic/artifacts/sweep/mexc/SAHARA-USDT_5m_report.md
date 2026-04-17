# PMM Dynamic Optimization Report: mexc_SAHARA-USDT_5m_sweep_v1

Generated: 2026-04-09 07:53:15 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T07:53:15.532284+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 3589 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SAHARA-USDT
- **interval**: 5m
- **n_candles**: 51914
- **dataset_hash**: fb2d94232811f5e4037dfca2af06f0d616a14458487c6bc6f1a110231ff53400
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 953.6875968881299
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.3804873969901557 |
| buy_n_levels | 10 |
| buy_side_weight | 0.26636134834328085 |
| buy_spread_base | 0.22129853279346973 |
| buy_spread_ratio | 1.2173519715031134 |
| cooldown_time | 2114 |
| executor_refresh_time | 2610 |
| macd_fast | 30 |
| macd_signal | 18 |
| macd_slow | 95 |
| natr_length | 39 |
| sell_n_levels | 10 |
| sell_spread_base | 2.6038070540620013 |
| sell_spread_ratio | 1.2204248957357735 |
| stop_loss | 0.019847488305716247 |
| take_profit | 0.008669217490430578 |
| time_limit | 71441 |
| total_amount_quote | 953.6875968881299 |
| trailing_stop_activation | 0.08613881877773767 |
| trailing_stop_delta | 0.0038944375224766407 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 953.6875968881299 |
| Selected | 953.6875968881299 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 7.2681
- **Net PnL (quote)**: 69.3148
- **Sharpe Ratio**: 2.5162
- **Max Drawdown %**: 2.9115
- **Profit Factor**: 2.5196486321302736
- **Trade Count**: 601
- **Total Fees (quote)**: 5.5517
- **Maker Fees**: 4.7813
- **Taker Fees**: 0.7704
- **Fee Drag %**: 0.5821
- **TP Min-Notional Failures**: 820 :warning:
  > 820 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0337
- **PnL Component**: 0.0702
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0218
- **Fee Drag Component**: -0.0029
- **Inventory Component**: -0.0114
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2201**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 9.09 | 11.82 | 0.76 | 239 | 0.0798 | n/a |
| 1 | 0.03 | 0.27 | 0.56 | 54 | -0.0042 | n/a |
| 2 | -0.55 | -6.85 | 0.55 | 9 | -0.3906 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | -1.52 | -10.74 | 1.58 | 33 | -0.3047 | n/a |
| 6 | 0.38 | 1.87 | 0.61 | 17 | -0.1329 | n/a |
| 7 | -1.66 | -8.56 | 2.07 | 74 | -0.1571 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **very_thin_book** (score: -0.0558)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 6.98 | 2.42 | 2.96 | 0.0292 |
| fees_2x | 6.69 | 2.32 | 3.00 | 0.0247 |
| latency_plus1 | 7.41 | 2.63 | 2.91 | 0.0361 |
| latency_plus2 | 6.93 | 2.54 | 2.71 | 0.0368 |
| latency_plus3 | 2.04 | 0.93 | 3.38 | -0.0104 |
| low_liquidity | 7.50 | 2.60 | 2.88 | 0.0351 |
| very_low_liquidity | 7.73 | 2.75 | 2.56 | 0.0416 |
| high_slippage | 7.07 | 2.45 | 2.97 | 0.0314 |
| extreme_slippage | 6.66 | 2.31 | 3.09 | 0.0267 |
| combined_adverse | 5.86 | 2.03 | 3.37 | 0.0154 |
| spread_widen_10bps | 9.08 | 3.15 | 2.51 | 0.0527 |
| spread_widen_25bps | 8.28 | 2.83 | 3.14 | 0.0405 |
| thin_book | -0.77 | -0.23 | 3.11 | -0.0365 |
| very_thin_book | -2.23 | -0.70 | 4.06 | -0.0558 |
| entry_spread_stress | 9.05 | 3.12 | 2.53 | 0.0523 |
| combined_market_deterioration | 6.88 | 2.56 | 2.22 | 0.0421 |
| severe_adverse | -2.13 | -0.60 | 3.04 | -0.0512 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0067)
- **Trend**: ranging (efficiency: 0.0109)
- **Best holdout score**: 0.0773 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0110 | -0.0334 | -1.52 | 2.33 | 97 |
| 1 | -0.0063 | -0.1121 | 3.38 | 1.54 | 100 |
| 2 | -0.0067 | -0.0312 | 3.87 | 1.47 | 95 |
| 3 | -0.0133 | 0.0250 | 3.18 | 0.78 | 101 |
| 4 | -0.0147 | 0.0773 | 15.13 | 7.02 | 100 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51914
- **Expected rows**: 51914
- **Missing rows**: 0
- **Forward-fill count**: 178
- **Forward-fill fraction**: 0.003428747544015102
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1619 <= 0
- **Objective score**: -0.16185378625748087
- **PnL %**: 0.22021380785524453
- **Trade count**: 9

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.011772226349818778
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0234, 0.0095 |
| sell_spread_base | 0.0185, 0.0109 |
| stop_loss | 0.0087, 0.0206 |
| take_profit | 0.0167, 0.0157 |
| executor_refresh_time | 0.0370, 0.0070 |
| cooldown_time | 0.0118, 0.0468 |
| total_amount_quote | 0.0149, 0.0148 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4088932781811078
- **Max CV**: 0.8331815171261513
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1053 | 0.20207810504580945 | 0.27279195084038166 | 0.2242820951949867 |
| buy_spread_ratio | 0.0416 | 1.2069891481086215 | 1.3838254346305605 | 1.2677738038370014 |
| sell_spread_base | 0.8332 | 0.33647567860794775 | 5.643785020155674 | 1.8167926438524262 |
| sell_spread_ratio | 0.2414 | 1.3742237738028937 | 2.9070234145975498 | 1.896556954256495 |
| buy_side_weight | 0.4349 | 0.21182831777830996 | 0.6714594378507939 | 0.32272525040593353 |
| amount_skew | 0.1530 | 1.009485078321442 | 1.614583246656652 | 1.1985319935748353 |
| stop_loss | 0.6651 | 0.012676668138913664 | 0.07150936505264384 | 0.034004624139478246 |
| take_profit | 0.7041 | 0.009283283154132897 | 0.06781489074178643 | 0.02463979751044267 |
| executor_refresh_time | 0.6113 | 382.0 | 3550.0 | 1983.2 |
| cooldown_time | 0.5230 | 270.0 | 1666.0 | 991.7 |
| total_amount_quote | 0.1851 | 532.820442792852 | 983.7483667873447 | 808.4730918153435 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.0
- **supports_post_only**: True
- **connector**: mexc
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
| recent_objective | > 0 | -0.16185378625748087 | FAIL |
| recent_pnl | >= 0 | 0.22021380785524453 | PASS |
| recent_trades | >= 5 | 9 | PASS |
| worst_stress | > -10 | -0.05576647136693168 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.03335756076911175 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_thin_book score=-0.05576647136693168 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.16185378625748087, pnl=0.22021380785524453, trades=9, reason=recent objective score -0.1619 <= 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4088932781811078 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51914 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1619 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51914
- **Pre-release bars**: 43849
- **Dev bars**: 35080
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065
- **Recent window start**: 1773294300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T07:53:15.532284+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 3589
