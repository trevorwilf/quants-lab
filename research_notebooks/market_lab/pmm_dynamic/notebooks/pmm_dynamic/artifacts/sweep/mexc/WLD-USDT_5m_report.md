# PMM Dynamic Optimization Report: mexc_WLD-USDT_5m_sweep_v1

Generated: 2026-04-09 10:26:11 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T10:26:11.160002+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 9010 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: WLD-USDT
- **interval**: 5m
- **n_candles**: 51914
- **dataset_hash**: 51847ed6c5d6d3e4b49ac9c328cc3c3cdc8b2b5a41a1cd9df5f484fa180b7d03
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 906.612788050876
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.7903347889014003 |
| buy_n_levels | 8 |
| buy_side_weight | 0.6299837971289041 |
| buy_spread_base | 1.5058347511950398 |
| buy_spread_ratio | 1.686310927601007 |
| cooldown_time | 1721 |
| executor_refresh_time | 2515 |
| macd_fast | 32 |
| macd_signal | 7 |
| macd_slow | 34 |
| natr_length | 8 |
| sell_n_levels | 5 |
| sell_spread_base | 4.580922289088159 |
| sell_spread_ratio | 1.3825834052840564 |
| stop_loss | 0.010452603111831478 |
| take_profit | 0.040141172840486725 |
| time_limit | 56764 |
| total_amount_quote | 906.612788050876 |
| trailing_stop_activation | 0.003743043628697181 |
| trailing_stop_delta | 0.0011673423536758293 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 906.612788050876 |
| Selected | 906.612788050876 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2.6567
- **Net PnL (quote)**: 24.0864
- **Sharpe Ratio**: 2.0319
- **Max Drawdown %**: 1.9945
- **Profit Factor**: 1.6229607285433123
- **Trade Count**: 903
- **Total Fees (quote)**: 5.1319
- **Maker Fees**: 2.5630
- **Taker Fees**: 2.5689
- **Fee Drag %**: 0.5661

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0063
- **PnL Component**: 0.0262
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0150
- **Fee Drag Component**: -0.0028
- **Inventory Component**: -0.0021
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0004**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.20 | 5.07 | 0.18 | 90 | 0.0004 | n/a |
| 1 | 0.17 | 3.36 | 0.15 | 82 | 0.0002 | n/a |
| 2 | 0.05 | 1.91 | 0.11 | 65 | -0.0005 | n/a |
| 3 | 0.21 | 7.96 | 0.09 | 115 | -0.0010 | n/a |
| 4 | -0.12 | -0.24 | 1.97 | 85 | -0.0165 | n/a |
| 5 | 0.31 | 5.31 | 0.23 | 83 | 0.0010 | n/a |
| 6 | -0.13 | -1.83 | 0.33 | 75 | -0.0041 | n/a |
| 7 | 0.22 | 8.58 | 0.05 | 63 | 0.0017 | n/a |
| 8 | 0.42 | 6.71 | 0.06 | 51 | 0.0036 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0474)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2.37 | 1.82 | 2.02 | 0.0019 |
| fees_2x | 2.09 | 1.60 | 2.07 | -0.0026 |
| latency_plus1 | 2.16 | 1.67 | 2.00 | 0.0015 |
| latency_plus2 | 1.53 | 1.21 | 2.09 | -0.0054 |
| latency_plus3 | 1.40 | 1.07 | 2.06 | -0.0065 |
| low_liquidity | 2.66 | 2.03 | 1.99 | 0.0063 |
| very_low_liquidity | 2.66 | 2.03 | 1.99 | 0.0063 |
| high_slippage | 1.95 | 1.50 | 2.10 | -0.0014 |
| extreme_slippage | 0.53 | 0.43 | 2.50 | -0.0185 |
| combined_adverse | 1.18 | 0.93 | 2.22 | -0.0112 |
| spread_widen_10bps | 1.86 | 1.41 | 2.16 | -0.0027 |
| spread_widen_25bps | 0.67 | 0.51 | 2.24 | -0.0152 |
| thin_book | -0.59 | -1.21 | 1.09 | -0.0183 |
| very_thin_book | -0.31 | -0.67 | 0.55 | -0.0082 |
| entry_spread_stress | 1.56 | 1.18 | 2.08 | -0.0051 |
| combined_market_deterioration | -1.25 | -0.94 | 2.91 | -0.0402 |
| severe_adverse | -2.35 | -5.08 | 2.43 | -0.0474 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0036)
- **Trend**: ranging (efficiency: 0.0064)
- **Best holdout score**: 0.0103 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0206 | -0.0026 | 0.03 | 0.33 | 139 |
| 1 | 0.0028 | 0.0071 | 1.97 | 1.20 | 116 |
| 2 | 0.0025 | 0.0100 | 1.67 | 0.68 | 275 |
| 3 | 0.0022 | 0.0103 | 1.65 | 0.61 | 117 |
| 4 | 0.0019 | -0.0063 | 0.61 | 0.52 | 194 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51914
- **Expected rows**: 51914
- **Missing rows**: 0
- **Forward-fill count**: 17
- **Forward-fill fraction**: 0.000327464653080094
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.002894443891218405
- **PnL %**: 0.4212284843863455
- **Trade count**: 106

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0014 <= 0; recent PnL -0.0245% < 0
- **Objective score**: -0.001406553952960171
- **PnL %**: -0.02453187876247694
- **Trade count**: 54

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1082 <= 0
- **Objective score**: -0.10820435073636067
- **PnL %**: 0.013639131485830052
- **Trade count**: 23

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.00963756778093069
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0148, 0.0219 |
| sell_spread_base | 0.0096, 0.0096 |
| stop_loss | 0.0117, 0.0112 |
| take_profit | 0.0096, 0.0096 |
| executor_refresh_time | 0.0097, 0.0139 |
| cooldown_time | 0.0065, 0.0096 |
| total_amount_quote | 0.0096, 0.0096 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.45314960816901523
- **Max CV**: 0.8438662035258138
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2855 | 1.2069140037701396 | 3.1074396436371123 | 1.8425272373590018 |
| buy_spread_ratio | 0.1841 | 1.2138880356290946 | 2.0497634932976356 | 1.4883658609897434 |
| sell_spread_base | 0.8439 | 0.4510121444183272 | 4.768660608350798 | 1.6965666214685324 |
| sell_spread_ratio | 0.3038 | 1.2652481959212245 | 2.9848479100601923 | 2.203038365432582 |
| buy_side_weight | 0.2370 | 0.25743384851488094 | 0.6196357996577799 | 0.4871374675027774 |
| amount_skew | 0.3195 | 1.4072784582911124 | 3.330456703258097 | 2.3244204819167957 |
| stop_loss | 0.3510 | 0.013067464541883905 | 0.03600975754661518 | 0.022720564350803378 |
| take_profit | 0.8077 | 0.00534821603811095 | 0.050166403777726326 | 0.018733101443330367 |
| executor_refresh_time | 0.6012 | 771.0 | 12710.0 | 7202.7 |
| cooldown_time | 0.6096 | 78.0 | 5041.0 | 2752.4 |
| total_amount_quote | 0.4414 | 251.4501391203254 | 910.5946023499869 | 559.6525921903062 |

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
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.002894443891218405 | PASS |
| recent_pnl | >= 0 | 0.4212284843863455 | PASS |
| recent_trades | >= 5 | 106 | PASS |
| worst_stress | > -10 | -0.04740305720933188 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.0025692316898939136 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.04740305720933188 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.002894443891218405, pnl=0.4212284843863455, trades=106, reason= |
| recent_14d_info | FAIL | informational only; score=-0.001406553952960171, pnl=-0.02453187876247694, trades=54, reason=recent objective score -0.0014 <= 0; recent PnL -0.0245% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.10820435073636067, pnl=0.013639131485830052, trades=23, reason=recent objective score -0.1082 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.45314960816901523 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51914 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0014 <= 0; recent PnL -0.0245% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1082 <= 0 |
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
- **run_timestamp**: 2026-04-09T10:26:11.160002+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 9010
