# PMM Dynamic Optimization Report: mexc_SOL-USDT_5m_sweep_v1

Generated: 2026-04-09 08:38:08 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T08:38:08.675308+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 13605 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SOL-USDT
- **interval**: 5m
- **n_candles**: 51915
- **dataset_hash**: 8305c54687f47d1658390fd24ebe1efc91233cf7a18f32be6d10cc0acd0ae4bc
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 983.539112761031
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.7158977405603766 |
| buy_n_levels | 6 |
| buy_side_weight | 0.5156739098992936 |
| buy_spread_base | 2.487507455402475 |
| buy_spread_ratio | 2.541464333611893 |
| cooldown_time | 4080 |
| executor_refresh_time | 9109 |
| macd_fast | 39 |
| macd_signal | 13 |
| macd_slow | 42 |
| natr_length | 28 |
| sell_n_levels | 6 |
| sell_spread_base | 5.919589008971566 |
| sell_spread_ratio | 2.5635402730358225 |
| stop_loss | 0.010955347480838228 |
| take_profit | 0.0050291927187995165 |
| time_limit | 90699 |
| total_amount_quote | 983.539112761031 |
| trailing_stop_activation | 0.06612583384291722 |
| trailing_stop_delta | 0.04296845776069813 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 983.539112761031 |
| Selected | 983.539112761031 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.1703
- **Net PnL (quote)**: -21.3458
- **Sharpe Ratio**: -5.6954
- **Max Drawdown %**: 2.2942
- **Profit Factor**: 0.5731730205005576
- **Trade Count**: 2140
- **Total Fees (quote)**: 3.7178
- **Maker Fees**: 2.9710
- **Taker Fees**: 0.7468
- **Fee Drag %**: 0.3780
- **TP Min-Notional Failures**: 2687 :warning:
  > 2687 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0479
- **PnL Component**: -0.0219
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0172
- **Fee Drag Component**: -0.0019
- **Inventory Component**: -0.0068
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0071**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.17 | -6.89 | 0.25 | 73 | -0.0056 | n/a |
| 1 | -0.17 | -5.52 | 0.27 | 73 | -0.0057 | n/a |
| 2 | 0.02 | 0.91 | 0.09 | 71 | -0.0023 | n/a |
| 3 | -0.01 | -0.81 | 0.06 | 72 | -0.0025 | n/a |
| 4 | -0.79 | -8.12 | 0.82 | 78 | -0.0228 | n/a |
| 5 | -0.37 | -7.73 | 0.51 | 82 | -0.0834 | n/a |
| 6 | -0.01 | -0.14 | 0.25 | 74 | -0.0041 | n/a |
| 7 | 0.01 | 0.24 | 0.16 | 77 | -0.0031 | n/a |
| 8 | -0.39 | -10.20 | 0.43 | 85 | -0.0092 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0745)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.36 | -6.17 | 2.45 | -0.0520 |
| fees_2x | -2.55 | -6.63 | 2.61 | -0.0560 |
| latency_plus1 | -2.18 | -5.72 | 2.29 | -0.0480 |
| latency_plus2 | -2.24 | -5.91 | 2.35 | -0.0490 |
| latency_plus3 | -2.27 | -5.99 | 2.38 | -0.0495 |
| low_liquidity | -2.17 | -5.70 | 2.29 | -0.0479 |
| very_low_liquidity | -2.17 | -5.70 | 2.29 | -0.0479 |
| high_slippage | -2.36 | -6.10 | 2.47 | -0.0511 |
| extreme_slippage | -2.74 | -6.86 | 2.81 | -0.0576 |
| combined_adverse | -2.56 | -6.59 | 2.63 | -0.0553 |
| spread_widen_10bps | -2.29 | -6.45 | 2.33 | -0.0491 |
| spread_widen_25bps | -2.66 | -7.51 | 2.70 | -0.0558 |
| thin_book | -2.47 | -7.33 | 2.48 | -0.0518 |
| very_thin_book | -2.72 | -6.63 | 2.72 | -0.0524 |
| entry_spread_stress | -2.82 | -7.63 | 2.89 | -0.0590 |
| combined_market_deterioration | -3.39 | -7.47 | 3.59 | -0.0728 |
| severe_adverse | -3.65 | -7.61 | 3.69 | -0.0745 |

## Holdout Validation

- **Holdout bars**: 8773
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0033)
- **Trend**: ranging (efficiency: 0.0017)
- **Best holdout score**: -0.0049 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0612 | -0.0049 | -0.07 | 0.25 | 159 |
| 1 | -0.0028 | -0.0171 | -0.54 | 0.63 | 398 |
| 2 | -0.0033 | -0.0167 | -0.42 | 0.53 | 273 |
| 3 | -0.0036 | -0.0148 | -0.31 | 0.48 | 162 |
| 4 | -0.0037 | -0.0142 | -0.36 | 0.41 | 203 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51915
- **Expected rows**: 51934
- **Missing rows**: 19
- **Forward-fill count**: 319
- **Forward-fill fraction**: 0.006144659539632091
- **Longest gap (seconds)**: 6000

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0108 <= 0; recent PnL -0.4619% < 0
- **Objective score**: -0.010832835538560253
- **PnL %**: -0.4619124834311875
- **Trade count**: 164

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0093 <= 0; recent PnL -0.1257% < 0
- **Objective score**: -0.009311765451919002
- **PnL %**: -0.1256594683053255
- **Trade count**: 84

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0646 <= 0; recent PnL -0.0900% < 0
- **Objective score**: -0.06456832572471101
- **PnL %**: -0.08997076745692524
- **Trade count**: 36

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.06334290838002014
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0434, -0.0615 |
| sell_spread_base | -0.0528, -0.0581 |
| stop_loss | -0.0590, -0.0553 |
| take_profit | -0.0632, -0.0496 |
| executor_refresh_time | -0.0537, -0.0780 |
| cooldown_time | -0.0573, -0.0643 |
| total_amount_quote | -0.0576, -0.0588 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.27018548855102376
- **Max CV**: 0.8120320233708798
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1214 | 2.275711570399848 | 3.3896198926686267 | 2.7823505018988826 |
| buy_spread_ratio | 0.0740 | 2.1431100890330734 | 2.7000794669374955 | 2.451575536273441 |
| sell_spread_base | 0.8120 | 0.26917293945636767 | 4.7590033414062916 | 2.0219545221056983 |
| sell_spread_ratio | 0.2051 | 1.426788499970874 | 2.640132658772613 | 1.908725416272708 |
| buy_side_weight | 0.3245 | 0.22198946348812892 | 0.6457121638376817 | 0.4540772497974951 |
| amount_skew | 0.1386 | 2.569077396165923 | 3.9232985761900747 | 3.336105711557802 |
| stop_loss | 0.2694 | 0.010251808228669205 | 0.02125943062264369 | 0.013473658540630234 |
| take_profit | 0.1575 | 0.005048877140102311 | 0.008068017289925032 | 0.005755089727720274 |
| executor_refresh_time | 0.4165 | 2072.0 | 12100.0 | 7629.2 |
| cooldown_time | 0.3470 | 1477.0 | 5582.0 | 3838.8 |
| total_amount_quote | 0.1059 | 736.2685195527039 | 996.9530119218123 | 850.2596222171821 |

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
| recent_objective | > 0 | -0.010832835538560253 | FAIL |
| recent_pnl | >= 0 | -0.4619124834311875 | FAIL |
| recent_trades | >= 5 | 164 | PASS |
| worst_stress | > -10 | -0.07453159738022389 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.004863501790314354 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.07453159738022389 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.010832835538560253, pnl=-0.4619124834311875, trades=164, reason=recent objective score -0.0108 <= 0; recent PnL -0.4619% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.009311765451919002, pnl=-0.1256594683053255, trades=84, reason=recent objective score -0.0093 <= 0; recent PnL -0.1257% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.06456832572471101, pnl=-0.08997076745692524, trades=36, reason=recent objective score -0.0646 <= 0; recent PnL -0.0900% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.27018548855102376 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51915 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0108 <= 0; recent PnL -0.4619% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0093 <= 0; recent PnL -0.1257% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0646 <= 0; recent PnL -0.0900% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51915
- **Pre-release bars**: 43869
- **Dev bars**: 35096
- **Holdout bars**: 8773
- **Recent 28d bars**: 8046
- **Recent window start**: 1773300300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T08:38:08.675308+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 13605
