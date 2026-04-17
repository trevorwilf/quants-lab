# PMM Dynamic Optimization Report: nonkyc_SAL-USDT_5m_sweep_v1

Generated: 2026-04-10 00:16:36 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-10T00:16:36.585403+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 1714 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: SAL-USDT
- **interval**: 5m
- **n_candles**: 52112
- **dataset_hash**: f911a4fc39a10a4def876458714fef690dad7e667d9a814c1ae50c45f8ba9577
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 807.9452237390358
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.4955786173652426 |
| buy_n_levels | 7 |
| buy_side_weight | 0.3983983161671061 |
| buy_spread_base | 1.9420346202461294 |
| buy_spread_ratio | 2.506586892512774 |
| cooldown_time | 1411 |
| executor_refresh_time | 11222 |
| macd_fast | 20 |
| macd_signal | 5 |
| macd_slow | 88 |
| natr_length | 28 |
| sell_n_levels | 7 |
| sell_spread_base | 1.7731413089833283 |
| sell_spread_ratio | 2.8933217206248742 |
| stop_loss | 0.1808186733651551 |
| take_profit | 0.006390350457005845 |
| time_limit | 111935 |
| total_amount_quote | 807.9452237390358 |
| trailing_stop_activation | 0.009465046402001187 |
| trailing_stop_delta | 0.0011236119600285862 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 807.9452237390358 |
| Selected | 807.9452237390358 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 20.9221
- **Net PnL (quote)**: 169.0392
- **Sharpe Ratio**: 4.3462
- **Max Drawdown %**: 3.4178
- **Profit Factor**: 2.4279293197855187
- **Trade Count**: 1952
- **Total Fees (quote)**: 44.3477
- **Maker Fees**: 19.2733
- **Taker Fees**: 25.0744
- **Fee Drag %**: 5.4889
- **TP Min-Notional Failures**: 661 :warning:
  > 661 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1192
- **PnL Component**: 0.1900
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0256
- **Fee Drag Component**: -0.0274
- **Inventory Component**: -0.0170
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0142**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.21 | 1.50 | 0.34 | 114 | -0.0080 | n/a |
| 1 | -0.07 | -1.39 | 0.27 | 51 | -0.0051 | n/a |
| 2 | -1.42 | -7.83 | 1.42 | 151 | -0.0646 | n/a |
| 3 | 0.03 | 0.50 | 0.30 | 94 | -0.0048 | n/a |
| 4 | -0.33 | -3.65 | 0.57 | 114 | -0.0164 | n/a |
| 5 | -0.12 | -1.43 | 0.42 | 98 | -0.0112 | n/a |
| 6 | -1.24 | -11.36 | 1.29 | 126 | -0.0297 | n/a |
| 7 | -0.24 | -3.70 | 0.43 | 98 | -0.0129 | n/a |
| 8 | 1.31 | 4.35 | 0.51 | 121 | 0.0052 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0260)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 18.18 | 3.81 | 3.77 | 0.0796 |
| fees_2x | 15.43 | 3.27 | 4.14 | 0.0395 |
| latency_plus1 | 21.81 | 4.46 | 3.37 | 0.1273 |
| latency_plus2 | 20.54 | 4.42 | 2.84 | 0.1227 |
| latency_plus3 | 20.23 | 4.36 | 2.77 | 0.1209 |
| low_liquidity | 14.40 | 3.27 | 3.48 | 0.0658 |
| very_low_liquidity | 20.85 | 4.81 | 3.09 | 0.1293 |
| high_slippage | 20.15 | 4.20 | 3.51 | 0.1120 |
| extreme_slippage | 18.59 | 3.90 | 3.70 | 0.0975 |
| combined_adverse | 12.89 | 3.16 | 3.33 | 0.0441 |
| spread_widen_10bps | 19.07 | 3.95 | 3.81 | 0.1006 |
| spread_widen_25bps | 18.35 | 3.77 | 3.33 | 0.0985 |
| thin_book | 15.93 | 3.54 | 3.25 | 0.0854 |
| very_thin_book | 6.87 | 2.32 | 3.80 | 0.0145 |
| entry_spread_stress | 20.53 | 4.12 | 3.82 | 0.1122 |
| combined_market_deterioration | 7.72 | 1.67 | 5.97 | -0.0248 |
| severe_adverse | 6.22 | 1.86 | 5.00 | -0.0260 |

## Holdout Validation

- **Holdout bars**: 8809
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0081)
- **Trend**: ranging (efficiency: 0.0025)
- **Best holdout score**: -0.0271 (rank #0)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0466 | -0.0271 | -1.03 | 1.17 | 231 |
| 1 | -0.0052 | -0.0417 | -1.04 | 2.56 | 252 |
| 2 | -0.0052 | -0.0422 | 0.14 | 2.50 | 571 |
| 3 | -0.0054 | -0.0595 | -2.72 | 2.86 | 461 |
| 4 | -0.0054 | -0.0410 | -0.64 | 2.54 | 275 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52112
- **Expected rows**: 52112
- **Missing rows**: 0
- **Forward-fill count**: 1055
- **Forward-fill fraction**: 0.02024485723058029
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.015974716550189012
- **PnL %**: 2.5291257680622623
- **Trade count**: 220

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.0029611484265792587
- **PnL %**: 1.0279301653308262
- **Trade count**: 107

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1442 <= 0; recent PnL -0.7500% < 0
- **Objective score**: -0.14419420510284398
- **PnL %**: -0.7500374671526971
- **Trade count**: 56

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.1245579399915617
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.1440, 0.1809 |
| sell_spread_base | 0.1495, 0.1289 |
| stop_loss | 0.1560, 0.1263 |
| take_profit | 0.1281, 0.1028 |
| executor_refresh_time | 0.0933, 0.1462 |
| cooldown_time | 0.1520, 0.1246 |
| total_amount_quote | 0.1126, 0.3138 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3405120595486145
- **Max CV**: 0.8417808638108671
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1619 | 2.1832106296272995 | 3.6946234149536283 | 3.124678498185216 |
| buy_spread_ratio | 0.0885 | 1.8639732960391333 | 2.6420868267111732 | 2.324639414818045 |
| sell_spread_base | 0.6605 | 0.218987585810333 | 5.15636226510681 | 2.2995696212880192 |
| sell_spread_ratio | 0.2217 | 1.2350382760811338 | 2.614322460150408 | 2.0709089349204772 |
| buy_side_weight | 0.2668 | 0.2026974641653119 | 0.4087876901179694 | 0.2848732658612536 |
| amount_skew | 0.1246 | 2.580074651300327 | 3.718698771711274 | 2.9893032540023916 |
| stop_loss | 0.5948 | 0.04160091625052718 | 0.23224740700199512 | 0.12667870353896504 |
| take_profit | 0.8418 | 0.0053971422504680575 | 0.04751041097594182 | 0.01726930176478967 |
| executor_refresh_time | 0.2059 | 5037.0 | 9994.0 | 7771.0 |
| cooldown_time | 0.5061 | 1760.0 | 7183.0 | 3879.7 |
| total_amount_quote | 0.0731 | 764.6710620651073 | 993.476795299556 | 915.530408449308 |

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
- holdout_no_collapse: **FAIL**
- sensitivity_stable: PASS
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.015974716550189012 | PASS |
| recent_pnl | >= 0 | 2.5291257680622623 | PASS |
| recent_trades | >= 5 | 220 | PASS |
| worst_stress | > -10 | -0.025986160924142736 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.027098700247309454 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.025986160924142736 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.015974716550189012, pnl=2.5291257680622623, trades=220, reason= |
| recent_14d_info | PASS | informational only; score=0.0029611484265792587, pnl=1.0279301653308262, trades=107, reason= |
| recent_7d_info | FAIL | informational only; score=-0.14419420510284398, pnl=-0.7500374671526971, trades=56, reason=recent objective score -0.1442 <= 0; recent PnL -0.7500% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3405120595486145 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52112 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1442 <= 0; recent PnL -0.7500% < 0 |
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
- **run_timestamp**: 2026-04-10T00:16:36.585403+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 1714
