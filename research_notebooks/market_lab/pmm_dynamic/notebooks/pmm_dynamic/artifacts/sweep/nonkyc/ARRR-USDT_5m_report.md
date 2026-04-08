# PMM Dynamic Optimization Report: nonkyc_ARRR-USDT_5m_sweep_v1

Generated: 2026-04-08 19:23:12 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T19:23:12.441371+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 13954 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-USDT
- **interval**: 5m
- **n_candles**: 51913
- **dataset_hash**: 95ff3fca6fd948f29340b6bf2a37fee77700cd5b9fcf08ba8305238dab91941c
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 93.00531929967465
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.2232831095191283 |
| buy_n_levels | 5 |
| buy_side_weight | 0.6782374103903513 |
| buy_spread_base | 3.0848308994829003 |
| buy_spread_ratio | 1.2363689912376832 |
| cooldown_time | 209 |
| executor_refresh_time | 1052 |
| macd_fast | 27 |
| macd_signal | 25 |
| macd_slow | 29 |
| natr_length | 40 |
| sell_n_levels | 8 |
| sell_spread_base | 1.6136847268639039 |
| sell_spread_ratio | 1.981252565822449 |
| stop_loss | 0.08571924090527214 |
| take_profit | 0.009497727444693828 |
| time_limit | 6017 |
| total_amount_quote | 93.00531929967465 |
| trailing_stop_activation | 0.0012000720364657366 |
| trailing_stop_delta | 0.0012382544525439453 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 93.00531929967465 |
| Selected | 93.00531929967465 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 260.1377
- **Net PnL (quote)**: 241.9419
- **Sharpe Ratio**: 8.9460
- **Max Drawdown %**: 9.9402
- **Profit Factor**: 3.72708100359261
- **Trade Count**: 2015
- **Total Fees (quote)**: 58.6117
- **Maker Fees**: 19.7360
- **Taker Fees**: 38.8757
- **Fee Drag %**: 63.0197
- **TP Min-Notional Failures**: 6 :warning:
  > 6 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.8719
- **PnL Component**: 1.2813
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0746
- **Fee Drag Component**: -0.3151
- **Inventory Component**: -0.0187
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.0516**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 29.64 | 17.16 | 2.86 | 99 | 0.2101 | n/a |
| 1 | 19.27 | 17.34 | 1.86 | 80 | 0.1421 | n/a |
| 2 | 6.47 | 9.67 | 0.81 | 38 | 0.0008 | n/a |
| 3 | 17.91 | 7.17 | 5.46 | 80 | 0.1006 | n/a |
| 4 | 28.54 | 17.27 | 3.14 | 112 | 0.1986 | n/a |
| 5 | 12.95 | 14.87 | 1.50 | 101 | 0.0851 | n/a |
| 6 | 2.07 | 5.94 | 1.35 | 54 | -0.0024 | n/a |
| 7 | 2.56 | 3.55 | 1.72 | 50 | -0.0087 | n/a |
| 8 | 14.93 | 12.28 | 1.15 | 89 | 0.1117 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.2228)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 228.57 | 8.17 | 10.68 | 0.6160 |
| fees_2x | 197.00 | 7.34 | 11.46 | 0.3506 |
| latency_plus1 | 207.38 | 7.27 | 10.50 | 0.6825 |
| latency_plus2 | 145.63 | 5.04 | 12.30 | 0.4121 |
| latency_plus3 | 51.64 | 2.20 | 22.73 | -0.0841 |
| low_liquidity | 187.18 | 8.16 | 12.45 | 0.6884 |
| very_low_liquidity | 158.84 | 7.84 | 13.80 | 0.5406 |
| high_slippage | 249.67 | 8.70 | 10.15 | 0.8406 |
| extreme_slippage | 228.75 | 8.19 | 10.57 | 0.7751 |
| combined_adverse | 127.65 | 5.94 | 13.24 | 0.2497 |
| spread_widen_10bps | 252.46 | 8.71 | 10.23 | 0.8465 |
| spread_widen_25bps | 232.18 | 8.10 | 10.36 | 0.7876 |
| thin_book | 94.43 | 6.52 | 8.06 | 0.4113 |
| very_thin_book | 22.68 | 2.79 | 8.05 | 0.0483 |
| entry_spread_stress | 246.72 | 8.51 | 10.38 | 0.8297 |
| combined_market_deterioration | 79.37 | 4.46 | 10.23 | 0.1385 |
| severe_adverse | -2.01 | -0.18 | 11.25 | -0.2228 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0076)
- **Trend**: ranging (efficiency: 0.0064)
- **Best holdout score**: 0.3751 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.3246 | 0.0561 | 10.43 | 1.60 | 128 |
| 1 | 0.1759 | -0.3852 | 19.65 | 6.61 | 1019 |
| 2 | 0.1715 | 0.0584 | 14.21 | 2.03 | 206 |
| 3 | 0.1628 | -0.3989 | 15.93 | 7.70 | 2227 |
| 4 | 0.1604 | 0.3751 | 141.13 | 6.43 | 587 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51913
- **Expected rows**: 51913
- **Missing rows**: 0
- **Forward-fill count**: 583
- **Forward-fill fraction**: 0.011230327663591009
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.19103865849439644
- **PnL %**: 28.856232057013358
- **Trade count**: 192

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.12292934610562843
- **PnL %**: 18.345938073390858
- **Trade count**: 106

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.03435195897134513
- **PnL %**: 6.527772114875878
- **Trade count**: 53

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.8889736293479253
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.8418, 0.6680 |
| sell_spread_base | 0.8502, 0.7384 |
| stop_loss | 0.8899, 0.8789 |
| take_profit | 0.8905, 0.8878 |
| executor_refresh_time | 0.8890, 0.8890 |
| cooldown_time | 0.8890, 0.8890 |
| total_amount_quote | 0.8676, 0.8961 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.41223425381595064
- **Max CV**: 1.2351693994965456
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit
- **Scattered params**: sell_spread_base, executor_refresh_time, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2043 | 1.7323842881609726 | 3.3813684828949135 | 2.392798568689398 |
| buy_spread_ratio | 0.1395 | 1.2286397186879314 | 1.8594916502726733 | 1.5357808904953925 |
| sell_spread_base | 0.6291 | 0.2589274048405534 | 1.171763489210274 | 0.5342574197620846 |
| sell_spread_ratio | 0.1814 | 1.4812038018270246 | 2.8925515780416893 | 2.4929891931466694 |
| buy_side_weight | 0.0847 | 0.5926896072903436 | 0.7955854588106138 | 0.7309492674212771 |
| amount_skew | 0.1712 | 1.8026466079058285 | 3.686846267146111 | 2.9780558333136957 |
| stop_loss | 0.2550 | 0.1035927193110655 | 0.2099007153448422 | 0.15883432425396043 |
| take_profit | 0.3372 | 0.005048934121307463 | 0.01565874920235022 | 0.010604857255246151 |
| executor_refresh_time | 0.6204 | 336.0 | 2333.0 | 1048.1 |
| cooldown_time | 1.2352 | 103.0 | 1527.0 | 345.7 |
| total_amount_quote | 0.6766 | 27.592858148635727 | 181.31539617620342 | 77.09098337013363 |

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
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: PASS
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.19103865849439644 | PASS |
| recent_pnl | >= 0 | 28.856232057013358 | PASS |
| recent_trades | >= 5 | 192 | PASS |
| worst_stress | > -10 | -0.22275906476821936 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=0.05607350598011213 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.22275906476821936 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.19103865849439644, pnl=28.856232057013358, trades=192, reason= |
| recent_14d_info | PASS | informational only; score=0.12292934610562843, pnl=18.345938073390858, trades=106, reason= |
| recent_7d_info | PASS | informational only; score=0.03435195897134513, pnl=6.527772114875878, trades=53, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.41223425381595064 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51913 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | PASS | recent_7d_info | — | — |  |
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
- **run_timestamp**: 2026-04-08T19:23:12.441371+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 13954
