# PMM Dynamic Optimization Report: nonkyc_ARRR-USDT_5m_sweep_v1

Generated: 2026-04-09 15:26:04 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T15:26:04.917562+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 9075 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-USDT
- **interval**: 5m
- **n_candles**: 52002
- **dataset_hash**: 2811c32a13e4ccff9c869470400eeb994c6e7a710ab08eaead8c4606ecb0a1b3
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 29.41324707569261
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.734867306538544 |
| buy_n_levels | 2 |
| buy_side_weight | 0.7674103270261686 |
| buy_spread_base | 3.516845549675473 |
| buy_spread_ratio | 1.5953890291754278 |
| cooldown_time | 67 |
| executor_refresh_time | 1267 |
| macd_fast | 49 |
| macd_signal | 27 |
| macd_slow | 79 |
| natr_length | 45 |
| sell_n_levels | 8 |
| sell_spread_base | 1.863700106798433 |
| sell_spread_ratio | 2.380216744114731 |
| stop_loss | 0.11921272384020044 |
| take_profit | 0.016968632246993753 |
| time_limit | 30767 |
| total_amount_quote | 29.41324707569261 |
| trailing_stop_activation | 0.004990510792508677 |
| trailing_stop_delta | 0.001862355458775609 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 29.41324707569261 |
| Selected | 29.41324707569261 |

> **WARNING**: Selected quote is within 5% of search minimum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 288.2159
- **Net PnL (quote)**: 84.7736
- **Sharpe Ratio**: 6.9864
- **Max Drawdown %**: 9.9422
- **Profit Factor**: 3.2031893716488
- **Trade Count**: 1007
- **Total Fees (quote)**: 22.6035
- **Maker Fees**: 7.9278
- **Taker Fees**: 14.6757
- **Fee Drag %**: 76.8479

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.8510
- **PnL Component**: 1.3564
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0746
- **Fee Drag Component**: -0.3842
- **Inventory Component**: -0.0444
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.0632**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 21.95 | 10.40 | 6.52 | 49 | 0.1231 | n/a |
| 1 | 17.66 | 18.00 | 1.04 | 36 | 0.0832 | n/a |
| 2 | 3.28 | 7.54 | 0.75 | 15 | -0.1197 | n/a |
| 3 | 19.99 | 8.16 | 5.14 | 49 | 0.1145 | n/a |
| 4 | 25.89 | 14.75 | 2.46 | 44 | 0.1674 | n/a |
| 5 | 15.30 | 17.76 | 0.79 | 55 | 0.1131 | n/a |
| 6 | 0.74 | 2.89 | 1.16 | 25 | -0.1111 | n/a |
| 7 | 3.74 | 4.16 | 1.89 | 31 | -0.0889 | n/a |
| 8 | 12.97 | 10.81 | 2.43 | 40 | 0.0475 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0319)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 249.66 | 6.32 | 10.65 | 0.5454 |
| fees_2x | 210.16 | 5.64 | 11.47 | 0.2386 |
| latency_plus1 | 223.84 | 5.83 | 10.39 | 0.6815 |
| latency_plus2 | 190.03 | 5.16 | 10.40 | 0.5919 |
| latency_plus3 | 123.26 | 3.57 | 18.03 | 0.3252 |
| low_liquidity | 310.47 | 7.75 | 12.95 | 0.8341 |
| very_low_liquidity | 276.69 | 7.55 | 13.98 | 0.7747 |
| high_slippage | 275.74 | 6.78 | 10.15 | 0.8156 |
| extreme_slippage | 249.27 | 6.39 | 10.58 | 0.7456 |
| combined_adverse | 193.42 | 5.51 | 11.13 | 0.3994 |
| spread_widen_10bps | 273.39 | 6.78 | 10.28 | 0.8144 |
| spread_widen_25bps | 263.41 | 6.59 | 10.56 | 0.7860 |
| thin_book | 57.62 | 2.92 | 14.41 | 0.1351 |
| very_thin_book | 24.41 | 2.21 | 10.52 | 0.0990 |
| entry_spread_stress | 270.85 | 6.73 | 10.38 | 0.8080 |
| combined_market_deterioration | 103.10 | 3.70 | 19.44 | 0.0545 |
| severe_adverse | 22.13 | 2.16 | 16.84 | -0.0319 |

## Holdout Validation

- **Holdout bars**: 8787
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0074)
- **Trend**: ranging (efficiency: 0.0084)
- **Best holdout score**: 0.0581 (rank #0)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.4095 | 0.0581 | 10.08 | 1.42 | 64 |
| 1 | 0.2012 | 0.0162 | 30.32 | 3.44 | 264 |
| 2 | 0.1855 | 0.0126 | 33.45 | 6.37 | 115 |
| 3 | 0.1823 | -0.2109 | 16.92 | 7.60 | 375 |
| 4 | 0.1737 | -0.0551 | 17.49 | 5.86 | 219 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52002
- **Expected rows**: 52002
- **Missing rows**: 0
- **Forward-fill count**: 588
- **Forward-fill fraction**: 0.011307257413176416
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.17021595503519169
- **PnL %**: 25.522005127019504
- **Trade count**: 90

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.08751576832170593
- **PnL %**: 13.570916681347567
- **Trade count**: 48

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0895 <= 0
- **Objective score**: -0.08948503457595057
- **PnL %**: 2.8522782703798732
- **Trade count**: 27

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.8965776873660958
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.8844, 0.8015 |
| sell_spread_base | 0.9044, 0.8281 |
| stop_loss | 0.8989, 0.9665 |
| take_profit | 0.8972, 0.8973 |
| executor_refresh_time | 0.8966, 0.9425 |
| cooldown_time | 0.8966, 0.8966 |
| total_amount_quote | 0.8738, 0.8800 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3587983462769253
- **Max CV**: 0.7469017457573079
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1339 | 1.8882759288405009 | 3.179075302110556 | 2.7046809853975224 |
| buy_spread_ratio | 0.1105 | 1.2226158719064553 | 1.7398696038722319 | 1.3723361558343705 |
| sell_spread_base | 0.5233 | 0.4832803025177382 | 4.123092666660443 | 1.9732016103752603 |
| sell_spread_ratio | 0.1007 | 2.041458422591559 | 2.845874810249554 | 2.448568412299987 |
| buy_side_weight | 0.0546 | 0.6650630379789237 | 0.7980157621491447 | 0.7290622600934952 |
| amount_skew | 0.2361 | 1.1987521326894501 | 3.372824556964421 | 2.750059296953272 |
| stop_loss | 0.3293 | 0.06769143291282236 | 0.23774752695879953 | 0.15735166956320096 |
| take_profit | 0.7469 | 0.01320159852682059 | 0.10845042904005514 | 0.035509294835622096 |
| executor_refresh_time | 0.7012 | 323.0 | 2130.0 | 819.3 |
| cooldown_time | 0.6787 | 244.0 | 1185.0 | 476.1 |
| total_amount_quote | 0.3315 | 28.886326764274266 | 82.70263404356541 | 58.83195566130712 |

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
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.17021595503519169 | PASS |
| recent_pnl | >= 0 | 25.522005127019504 | PASS |
| recent_trades | >= 5 | 90 | PASS |
| worst_stress | > -10 | -0.031940549858817495 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=0.058124003261021975 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.031940549858817495 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.17021595503519169, pnl=25.522005127019504, trades=90, reason= |
| recent_14d_info | PASS | informational only; score=0.08751576832170593, pnl=13.570916681347567, trades=48, reason= |
| recent_7d_info | FAIL | informational only; score=-0.08948503457595057, pnl=2.8522782703798732, trades=27, reason=recent objective score -0.0895 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3587983462769253 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52002 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0895 <= 0 |
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
- **run_timestamp**: 2026-04-09T15:26:04.917562+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 9075
