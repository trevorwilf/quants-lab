# PMM Dynamic Optimization Report: nonkyc_ADA-USDT_5m_sweep_v1

Generated: 2026-04-09 14:34:54 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T14:34:54.668079+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 7385 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ADA-USDT
- **interval**: 5m
- **n_candles**: 52002
- **dataset_hash**: e5ad3c9fbf4683813c4bdf712eb880bd1a88d0936a3b3b1e7dcb6e690dd124c5
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 994.6250112078291
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.7386088124954098 |
| buy_n_levels | 6 |
| buy_side_weight | 0.38193343618229575 |
| buy_spread_base | 4.107635385897596 |
| buy_spread_ratio | 2.2638353212826634 |
| cooldown_time | 7130 |
| executor_refresh_time | 7985 |
| macd_fast | 46 |
| macd_signal | 24 |
| macd_slow | 82 |
| natr_length | 42 |
| sell_n_levels | 6 |
| sell_spread_base | 4.864324992503616 |
| sell_spread_ratio | 1.5095984038964905 |
| stop_loss | 0.05748959553433896 |
| take_profit | 0.0051571997765796854 |
| time_limit | 164978 |
| total_amount_quote | 994.6250112078291 |
| trailing_stop_activation | 0.08504371160738548 |
| trailing_stop_delta | 0.009214279966863385 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 994.6250112078291 |
| Selected | 994.6250112078291 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -5.2683
- **Net PnL (quote)**: -52.3994
- **Sharpe Ratio**: -5.6906
- **Max Drawdown %**: 5.6807
- **Profit Factor**: 0.570002094314068
- **Trade Count**: 1206
- **Total Fees (quote)**: 16.7437
- **Maker Fees**: 12.3159
- **Taker Fees**: 4.4278
- **Fee Drag %**: 1.6834
- **TP Min-Notional Failures**: 188512 :warning:
  > 188512 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1201
- **PnL Component**: -0.0541
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0426
- **Fee Drag Component**: -0.0084
- **Inventory Component**: -0.0147
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0257**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.51 | -10.69 | 0.56 | 79 | -0.0184 | n/a |
| 1 | -0.15 | -6.92 | 0.20 | 76 | -0.0184 | n/a |
| 2 | -0.29 | -8.85 | 0.31 | 84 | -0.0573 | n/a |
| 3 | -0.05 | -3.08 | 0.09 | 73 | -0.0039 | n/a |
| 4 | -0.65 | -6.90 | 0.72 | 100 | -0.0151 | n/a |
| 5 | -0.15 | -5.81 | 0.18 | 76 | -0.0049 | n/a |
| 6 | -0.26 | -6.30 | 0.28 | 123 | -0.0521 | n/a |
| 7 | -0.16 | -11.09 | 0.16 | 93 | -0.0770 | n/a |
| 8 | -0.41 | -10.23 | 0.44 | 106 | -0.0822 | n/a |

## Stress Test Results

Worst Scenario: **very_low_liquidity** (score: -0.2445)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -6.11 | -6.56 | 6.48 | -0.1393 |
| fees_2x | -6.95 | -7.42 | 7.29 | -0.1677 |
| latency_plus1 | -5.27 | -5.69 | 5.68 | -0.1201 |
| latency_plus2 | -5.29 | -5.71 | 5.69 | -0.1200 |
| latency_plus3 | -6.40 | -6.87 | 6.75 | -0.1401 |
| low_liquidity | -7.17 | -6.08 | 7.78 | -0.1691 |
| very_low_liquidity | -9.93 | -6.14 | 10.55 | -0.2445 |
| high_slippage | -5.38 | -5.80 | 5.79 | -0.1221 |
| extreme_slippage | -5.60 | -6.02 | 6.00 | -0.1260 |
| combined_adverse | -8.81 | -7.14 | 9.38 | -0.2168 |
| spread_widen_10bps | -6.20 | -7.30 | 6.50 | -0.1336 |
| spread_widen_25bps | -5.97 | -6.08 | 6.37 | -0.1332 |
| thin_book | -7.45 | -6.95 | 7.91 | -0.1610 |
| very_thin_book | -5.95 | -8.30 | 6.38 | -0.1363 |
| entry_spread_stress | -6.60 | -7.33 | 6.93 | -0.1426 |
| combined_market_deterioration | -6.74 | -7.44 | 7.13 | -0.1495 |
| severe_adverse | -9.57 | -9.40 | 9.93 | -0.2255 |

## Holdout Validation

- **Holdout bars**: 8787
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0030)
- **Trend**: ranging (efficiency: 0.0016)
- **Best holdout score**: -0.0409 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1823 | -0.0565 | -0.31 | 0.38 | 230 |
| 1 | -0.0123 | -0.0531 | -1.69 | 1.94 | 1338 |
| 2 | -0.0125 | -0.0542 | -1.12 | 1.54 | 830 |
| 3 | -0.0136 | -0.0409 | -1.25 | 1.33 | 913 |
| 4 | -0.0140 | -0.2350 | -6.32 | 6.35 | 1062 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52002
- **Expected rows**: 52002
- **Missing rows**: 0
- **Forward-fill count**: 251
- **Forward-fill fraction**: 0.0048267374331756475
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0173 <= 0; recent PnL -0.2504% < 0
- **Objective score**: -0.01726443902697672
- **PnL %**: -0.2504187578711388
- **Trade count**: 320

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0033 <= 0
- **Objective score**: -0.0033328075574946265
- **PnL %**: 0.1728337646666507
- **Trade count**: 210

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0078 <= 0
- **Objective score**: -0.007796421911860901
- **PnL %**: 0.35364022852273536
- **Trade count**: 195

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: -0.16677771010761458
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.4575, -0.1965 |
| sell_spread_base | -0.1645, -0.2000 |
| stop_loss | -0.2130, -0.1636 |
| take_profit | -0.1573, -0.1570 |
| executor_refresh_time | -0.2027, -0.2143 |
| cooldown_time | -0.1666, -0.1765 |
| total_amount_quote | -0.1813, -0.4847 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3076574000854253
- **Max CV**: 1.060985707211073
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1387 | 3.073063807052035 | 5.209855850432447 | 4.718027510131703 |
| buy_spread_ratio | 0.1703 | 1.7981056327913796 | 2.9503019934786003 | 2.321455819269048 |
| sell_spread_base | 1.0610 | 0.46057410245435093 | 4.14180300591671 | 1.0635986611076864 |
| sell_spread_ratio | 0.1296 | 1.2006303772517974 | 1.8498325655787462 | 1.4442983690244007 |
| buy_side_weight | 0.0736 | 0.20522086561583686 | 0.25408903286935186 | 0.2349600432343347 |
| amount_skew | 0.1990 | 2.082275950596288 | 3.9522070496875745 | 3.0095924012209916 |
| stop_loss | 0.5368 | 0.023059346579907165 | 0.2076261221668133 | 0.11807938043006923 |
| take_profit | 0.5341 | 0.005131072144532597 | 0.023124792702152872 | 0.013381121312883678 |
| executor_refresh_time | 0.2972 | 3945.0 | 14390.0 | 9812.0 |
| cooldown_time | 0.1496 | 4307.0 | 6629.0 | 5713.4 |
| total_amount_quote | 0.0943 | 739.2623669423848 | 985.4480251942853 | 902.8201701552365 |

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
| recent_objective | > 0 | -0.01726443902697672 | FAIL |
| recent_pnl | >= 0 | -0.2504187578711388 | FAIL |
| recent_trades | >= 5 | 320 | PASS |
| worst_stress | > -10 | -0.2445010853855239 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.056526543284214616 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_low_liquidity score=-0.2445010853855239 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.01726443902697672, pnl=-0.2504187578711388, trades=320, reason=recent objective score -0.0173 <= 0; recent PnL -0.2504% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.0033328075574946265, pnl=0.1728337646666507, trades=210, reason=recent objective score -0.0033 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.007796421911860901, pnl=0.35364022852273536, trades=195, reason=recent objective score -0.0078 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3076574000854253 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52002 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0173 <= 0; recent PnL -0.2504% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0033 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0078 <= 0 |
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
- **run_timestamp**: 2026-04-09T14:34:54.668079+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 7385
