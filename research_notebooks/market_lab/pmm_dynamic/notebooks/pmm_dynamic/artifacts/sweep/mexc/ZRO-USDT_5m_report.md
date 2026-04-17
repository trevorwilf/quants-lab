# PMM Dynamic Optimization Report: mexc_ZRO-USDT_5m_sweep_v1

Generated: 2026-04-09 13:42:39 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T13:42:39.963899+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 12917 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ZRO-USDT
- **interval**: 5m
- **n_candles**: 52058
- **dataset_hash**: bac8fead9e50a402e22936dce95b7993cdee227ae5914c1d5c4a14a37c1b5a39
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 998.1671151773196
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.3907995783535165 |
| buy_n_levels | 6 |
| buy_side_weight | 0.38477797836154487 |
| buy_spread_base | 2.4725050929561236 |
| buy_spread_ratio | 1.4147442602581162 |
| cooldown_time | 2895 |
| executor_refresh_time | 2969 |
| macd_fast | 13 |
| macd_signal | 7 |
| macd_slow | 64 |
| natr_length | 48 |
| sell_n_levels | 4 |
| sell_spread_base | 2.4745221026642756 |
| sell_spread_ratio | 2.308515504380465 |
| stop_loss | 0.1214124710710024 |
| take_profit | 0.01641587753088281 |
| time_limit | 165701 |
| total_amount_quote | 998.1671151773196 |
| trailing_stop_activation | 0.00983508997842871 |
| trailing_stop_delta | 0.0010007731990058493 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 998.1671151773196 |
| Selected | 998.1671151773196 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 26.3594
- **Net PnL (quote)**: 263.1109
- **Sharpe Ratio**: 3.6935
- **Max Drawdown %**: 6.1761
- **Profit Factor**: 2.160094630009624
- **Trade Count**: 1254
- **Total Fees (quote)**: 15.7738
- **Maker Fees**: 7.8765
- **Taker Fees**: 7.8973
- **Fee Drag %**: 1.5803

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0834
- **PnL Component**: 0.2340
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0463
- **Fee Drag Component**: -0.0079
- **Inventory Component**: -0.0950
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0157**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.06 | -0.22 | 1.31 | 73 | -0.0186 | n/a |
| 1 | 0.86 | 3.58 | 0.83 | 93 | -0.0063 | n/a |
| 2 | -0.28 | -2.00 | 0.57 | 58 | -0.0128 | n/a |
| 3 | 1.49 | 8.60 | 0.59 | 109 | 0.0014 | n/a |
| 4 | 3.43 | 6.91 | 1.19 | 115 | 0.0160 | n/a |
| 5 | 1.43 | 3.13 | 3.57 | 120 | -0.0214 | n/a |
| 6 | 0.77 | 2.78 | 1.22 | 117 | -0.0106 | n/a |
| 7 | 0.59 | 2.16 | 1.34 | 115 | -0.0130 | n/a |
| 8 | 1.27 | 6.13 | 0.56 | 117 | -0.0144 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0700)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 25.57 | 3.59 | 6.22 | 0.0727 |
| fees_2x | 24.78 | 3.48 | 6.27 | 0.0618 |
| latency_plus1 | 26.81 | 3.72 | 6.17 | 0.0868 |
| latency_plus2 | 25.88 | 3.79 | 6.42 | 0.0786 |
| latency_plus3 | 25.17 | 3.60 | 6.50 | 0.0739 |
| low_liquidity | 26.14 | 3.67 | 6.19 | 0.0812 |
| very_low_liquidity | 24.85 | 3.47 | 6.25 | 0.0706 |
| high_slippage | 24.38 | 3.43 | 6.28 | 0.0662 |
| extreme_slippage | 20.42 | 2.89 | 6.51 | 0.0304 |
| combined_adverse | 23.92 | 3.33 | 6.33 | 0.0573 |
| spread_widen_10bps | 28.13 | 3.94 | 6.18 | 0.0961 |
| spread_widen_25bps | 19.24 | 2.51 | 7.84 | -0.0008 |
| thin_book | 12.25 | 2.02 | 6.88 | -0.0464 |
| very_thin_book | 10.68 | 3.59 | 3.74 | 0.0392 |
| entry_spread_stress | 22.87 | 3.01 | 6.44 | 0.0450 |
| combined_market_deterioration | 19.17 | 3.33 | 5.18 | 0.0346 |
| severe_adverse | 7.66 | 1.51 | 5.01 | -0.0700 |

## Holdout Validation

- **Holdout bars**: 8798
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0063)
- **Trend**: ranging (efficiency: 0.0044)
- **Best holdout score**: 0.0069 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0067 | -0.0681 | -2.21 | 4.72 | 256 |
| 1 | 0.0070 | -0.0221 | 3.29 | 2.43 | 456 |
| 2 | 0.0055 | -0.0289 | 3.41 | 3.99 | 418 |
| 3 | 0.0052 | 0.0069 | 1.59 | 0.90 | 139 |
| 4 | 0.0038 | 0.0008 | 6.27 | 1.86 | 295 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52058
- **Expected rows**: 52058
- **Missing rows**: 0
- **Forward-fill count**: 33
- **Forward-fill fraction**: 0.0006339083330131776
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.007087091199678601
- **PnL %**: 2.302357227407691
- **Trade count**: 238

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0016 <= 0
- **Objective score**: -0.0016120589147423535
- **PnL %**: 1.3415337934743956
- **Trade count**: 130

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0036 <= 0
- **Objective score**: -0.0035517629545690575
- **PnL %**: 0.8153661456678273
- **Trade count**: 57

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: 0.1407363685133935
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0490, 0.1107 |
| sell_spread_base | 0.0974, 0.0803 |
| stop_loss | 0.1295, 0.1405 |
| take_profit | 0.1407, 0.1407 |
| executor_refresh_time | 0.1045, 0.0578 |
| cooldown_time | 0.1486, 0.0416 |
| total_amount_quote | 0.1401, 0.1411 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4647042848111882
- **Max CV**: 0.8909175106299378
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1273 | 1.9804168096152077 | 3.052283057105131 | 2.5678934017017925 |
| buy_spread_ratio | 0.1370 | 1.2846961853811678 | 1.9804600930274374 | 1.5650952402921152 |
| sell_spread_base | 0.8711 | 0.23488574605079274 | 5.817429330964337 | 2.241639908700172 |
| sell_spread_ratio | 0.2100 | 1.339465580708639 | 2.7633715485652144 | 2.128394748278075 |
| buy_side_weight | 0.2861 | 0.2869384747729084 | 0.6312823269729839 | 0.44793644311813274 |
| amount_skew | 0.2164 | 1.8686565832284923 | 3.6130740508485792 | 2.628874721502587 |
| stop_loss | 0.8909 | 0.012013719029598073 | 0.2242448959139571 | 0.10478696378940829 |
| take_profit | 0.6083 | 0.010234994695572586 | 0.06966618828743944 | 0.029224673740685537 |
| executor_refresh_time | 0.7512 | 628.0 | 10476.0 | 4751.9 |
| cooldown_time | 0.5134 | 780.0 | 3618.0 | 2385.5 |
| total_amount_quote | 0.5000 | 124.7734729023245 | 995.7380159499323 | 693.6028980748102 |

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
| recent_objective | > 0 | 0.007087091199678601 | PASS |
| recent_pnl | >= 0 | 2.302357227407691 | PASS |
| recent_trades | >= 5 | 238 | PASS |
| worst_stress | > -10 | -0.07004023558109512 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.0680923139894434 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.07004023558109512 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | PASS | score=0.007087091199678601, pnl=2.302357227407691, trades=238, reason= |
| recent_14d_info | FAIL | informational only; score=-0.0016120589147423535, pnl=1.3415337934743956, trades=130, reason=recent objective score -0.0016 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.0035517629545690575, pnl=0.8153661456678273, trades=57, reason=recent objective score -0.0036 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4647042848111882 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52058 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0016 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0036 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52058
- **Pre-release bars**: 43993
- **Dev bars**: 35195
- **Holdout bars**: 8798
- **Recent 28d bars**: 8065
- **Recent window start**: 1773315900

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T13:42:39.963899+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 12917
