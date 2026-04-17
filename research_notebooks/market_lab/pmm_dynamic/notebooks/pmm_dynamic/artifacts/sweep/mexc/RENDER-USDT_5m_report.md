# PMM Dynamic Optimization Report: mexc_RENDER-USDT_5m_sweep_v1

Generated: 2026-04-09 07:21:05 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T07:21:05.157008+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 10042 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: RENDER-USDT
- **interval**: 5m
- **n_candles**: 51914
- **dataset_hash**: cca75370ab5845da22b204fac659e02a42cd30cb7fd56cd35c10114fc164bc14
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 722.6807619790027
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.1736073218323155 |
| buy_n_levels | 7 |
| buy_side_weight | 0.41941419206493336 |
| buy_spread_base | 2.041519835133199 |
| buy_spread_ratio | 2.0712764786468663 |
| cooldown_time | 535 |
| executor_refresh_time | 1292 |
| macd_fast | 28 |
| macd_signal | 20 |
| macd_slow | 98 |
| natr_length | 33 |
| sell_n_levels | 9 |
| sell_spread_base | 2.761973931915439 |
| sell_spread_ratio | 2.0641477275985776 |
| stop_loss | 0.020501707799076157 |
| take_profit | 0.056108163913717014 |
| time_limit | 141678 |
| total_amount_quote | 722.6807619790027 |
| trailing_stop_activation | 0.0021125354845790583 |
| trailing_stop_delta | 0.0011791211091379836 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 722.6807619790027 |
| Selected | 722.6807619790027 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 4.1881
- **Net PnL (quote)**: 30.2665
- **Sharpe Ratio**: 4.7294
- **Max Drawdown %**: 0.4528
- **Profit Factor**: 2.2085782449586957
- **Trade Count**: 910
- **Total Fees (quote)**: 3.6674
- **Maker Fees**: 1.8303
- **Taker Fees**: 1.8371
- **Fee Drag %**: 0.5075

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0328
- **PnL Component**: 0.0410
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0034
- **Fee Drag Component**: -0.0025
- **Inventory Component**: -0.0022
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0004**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.11 | 2.77 | 0.24 | 86 | -0.0010 | n/a |
| 1 | 0.10 | 6.69 | 0.07 | 74 | 0.0003 | n/a |
| 2 | 0.16 | 12.67 | 0.02 | 52 | 0.0014 | n/a |
| 3 | 0.06 | 2.92 | 0.11 | 88 | -0.0004 | n/a |
| 4 | 1.17 | 6.14 | 0.03 | 111 | 0.0110 | n/a |
| 5 | 0.53 | 9.54 | 0.16 | 94 | 0.0039 | n/a |
| 6 | 0.54 | 11.27 | 0.08 | 113 | 0.0044 | n/a |
| 7 | -0.05 | -2.76 | 0.13 | 82 | -0.0017 | n/a |
| 8 | 0.17 | 2.02 | 0.34 | 108 | -0.0012 | n/a |

## Stress Test Results

Worst Scenario: **spread_widen_25bps** (score: -0.0307)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3.93 | 4.46 | 0.47 | 0.0290 |
| fees_2x | 3.68 | 4.19 | 0.48 | 0.0252 |
| latency_plus1 | 2.34 | 3.28 | 0.71 | 0.0130 |
| latency_plus2 | 2.20 | 2.91 | 0.67 | 0.0121 |
| latency_plus3 | 1.34 | 1.99 | 0.59 | 0.0043 |
| low_liquidity | 4.19 | 4.73 | 0.45 | 0.0328 |
| very_low_liquidity | 4.14 | 4.67 | 0.45 | 0.0323 |
| high_slippage | 3.55 | 4.05 | 0.49 | 0.0264 |
| extreme_slippage | 2.28 | 2.65 | 0.57 | 0.0135 |
| combined_adverse | 1.49 | 2.11 | 0.87 | 0.0023 |
| spread_widen_10bps | 1.48 | 1.60 | 1.76 | -0.0080 |
| spread_widen_25bps | -0.20 | -0.19 | 2.48 | -0.0307 |
| thin_book | -0.15 | -0.49 | 0.76 | -0.0108 |
| very_thin_book | -0.17 | -1.23 | 0.30 | -0.0044 |
| entry_spread_stress | 1.04 | 1.12 | 1.98 | -0.0144 |
| combined_market_deterioration | -0.80 | -1.67 | 1.75 | -0.0263 |
| severe_adverse | -1.29 | -5.87 | 1.32 | -0.0288 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0042)
- **Trend**: ranging (efficiency: 0.0061)
- **Best holdout score**: 0.0378 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0011 | 0.0050 | 0.61 | 0.08 | 203 |
| 1 | 0.0096 | 0.0378 | 5.37 | 1.29 | 208 |
| 2 | 0.0075 | -0.0343 | -0.42 | 2.16 | 488 |
| 3 | 0.0065 | -0.0646 | -2.24 | 3.38 | 1397 |
| 4 | 0.0056 | -0.0573 | 1.90 | 3.73 | 662 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51914
- **Expected rows**: 51914
- **Missing rows**: 0
- **Forward-fill count**: 37
- **Forward-fill fraction**: 0.0007127171861154987
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0016 <= 0
- **Objective score**: -0.0015925237549841145
- **PnL %**: 0.20330365112950466
- **Trade count**: 215

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.0007980164021460253
- **PnL %**: 0.1769450204408246
- **Trade count**: 112

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.00024436515517702127
- **PnL %**: 0.04627976617433382
- **Trade count**: 55

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: 0.040625632283715636
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0240, 0.0495 |
| sell_spread_base | 0.0405, 0.0163 |
| stop_loss | 0.0412, 0.0405 |
| take_profit | 0.0406, 0.0406 |
| executor_refresh_time | 0.0406, 0.0382 |
| cooldown_time | 0.0406, 0.0406 |
| total_amount_quote | 0.0426, 0.0413 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.40602383397013564
- **Max CV**: 0.7819587636678946
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit
- **Scattered params**: sell_spread_base, executor_refresh_time, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1965 | 1.7361578710748904 | 3.22444727724895 | 2.4244817441961137 |
| buy_spread_ratio | 0.0847 | 1.2014464385493773 | 1.559611642733596 | 1.313652037587709 |
| sell_spread_base | 0.6665 | 0.21561181324176798 | 1.7792440853396463 | 0.7414458464395903 |
| sell_spread_ratio | 0.3121 | 1.3304835200331668 | 2.994705860494017 | 2.172962824612815 |
| buy_side_weight | 0.2812 | 0.28907816173282386 | 0.7523422563090773 | 0.5208280214032428 |
| amount_skew | 0.3162 | 1.1867773185903197 | 3.1379592484973013 | 1.9534252257866052 |
| stop_loss | 0.1537 | 0.014339058719581558 | 0.022401378129105715 | 0.01888223103274788 |
| take_profit | 0.4592 | 0.03302415337465787 | 0.14425630931261227 | 0.08786243519112205 |
| executor_refresh_time | 0.5892 | 594.0 | 6643.0 | 3429.6 |
| cooldown_time | 0.6251 | 169.0 | 2031.0 | 1041.6 |
| total_amount_quote | 0.7820 | 85.54889553337564 | 818.2478352517796 | 266.25733607309087 |

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
- holdout_passed: PASS
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
| recent_objective | > 0 | -0.0015925237549841145 | FAIL |
| recent_pnl | >= 0 | 0.20330365112950466 | PASS |
| recent_trades | >= 5 | 215 | PASS |
| worst_stress | > -10 | -0.030715754839510334 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0050 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=spread_widen_25bps score=-0.030715754839510334 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.0015925237549841145, pnl=0.20330365112950466, trades=215, reason=recent objective score -0.0016 <= 0 |
| recent_14d_info | PASS | informational only; score=0.0007980164021460253, pnl=0.1769450204408246, trades=112, reason= |
| recent_7d_info | PASS | informational only; score=0.00024436515517702127, pnl=0.04627976617433382, trades=55, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.40602383397013564 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51914 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0016 <= 0 |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | PASS | recent_7d_info | — | — |  |
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
- **run_timestamp**: 2026-04-09T07:21:05.157008+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 10042
