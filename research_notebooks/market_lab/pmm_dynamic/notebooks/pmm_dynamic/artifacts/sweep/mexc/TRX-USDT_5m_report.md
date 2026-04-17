# PMM Dynamic Optimization Report: mexc_TRX-USDT_5m_sweep_v1

Generated: 2026-04-09 09:56:06 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T09:56:06.812346+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 5374 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: TRX-USDT
- **interval**: 5m
- **n_candles**: 51914
- **dataset_hash**: afcd92a5b4c4af19790bfc7681670a098fc46510aa251cac630eff01648458e0
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 929.0998470032486
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.9643055761839285 |
| buy_n_levels | 5 |
| buy_side_weight | 0.4504331365826163 |
| buy_spread_base | 0.6582628251597031 |
| buy_spread_ratio | 1.5119276402858242 |
| cooldown_time | 2289 |
| executor_refresh_time | 1047 |
| macd_fast | 38 |
| macd_signal | 23 |
| macd_slow | 94 |
| natr_length | 31 |
| sell_n_levels | 6 |
| sell_spread_base | 1.1445450705552949 |
| sell_spread_ratio | 2.6329383450549733 |
| stop_loss | 0.022622983854290287 |
| take_profit | 0.005736050647430558 |
| time_limit | 161305 |
| total_amount_quote | 929.0998470032486 |
| trailing_stop_activation | 0.00017621407276935397 |
| trailing_stop_delta | 0.011339773558633092 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 929.0998470032486 |
| Selected | 929.0998470032486 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.4239
- **Net PnL (quote)**: -22.5205
- **Sharpe Ratio**: -1.5719
- **Max Drawdown %**: 3.7617
- **Profit Factor**: 0.7835910004340844
- **Trade Count**: 505
- **Total Fees (quote)**: 8.8281
- **Maker Fees**: 7.0767
- **Taker Fees**: 1.7514
- **Fee Drag %**: 0.9502
- **TP Min-Notional Failures**: 38 :warning:
  > 38 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1839
- **PnL Component**: -0.0245
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0282
- **Fee Drag Component**: -0.0048
- **Inventory Component**: -0.1261
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0506**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.51 | -12.12 | 0.51 | 44 | -0.0582 | n/a |
| 1 | -0.24 | -3.87 | 0.44 | 57 | -0.0327 | n/a |
| 2 | -0.03 | -2.66 | 0.06 | 32 | -0.0730 | n/a |
| 3 | -0.53 | -9.76 | 0.65 | 32 | -0.1414 | n/a |
| 4 | -1.06 | -9.27 | 1.13 | 50 | -0.0443 | n/a |
| 5 | -0.20 | -9.33 | 0.21 | 15 | -0.1739 | n/a |
| 6 | -0.18 | -3.75 | 0.38 | 54 | -0.0317 | n/a |
| 7 | -0.34 | -7.50 | 0.42 | 48 | -0.0387 | n/a |
| 8 | -0.58 | -10.32 | 0.76 | 64 | -0.0384 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.2209)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.90 | -1.88 | 4.01 | -0.1934 |
| fees_2x | -3.37 | -2.19 | 4.25 | -0.2029 |
| latency_plus1 | -1.50 | -0.90 | 3.36 | -0.1708 |
| latency_plus2 | -1.03 | -0.61 | 2.67 | -0.1583 |
| latency_plus3 | -1.66 | -1.03 | 3.03 | -0.1617 |
| low_liquidity | -2.42 | -1.57 | 3.76 | -0.1839 |
| very_low_liquidity | -2.40 | -1.55 | 3.74 | -0.1835 |
| high_slippage | -2.90 | -1.87 | 4.08 | -0.1915 |
| extreme_slippage | -3.84 | -2.44 | 4.72 | -0.2066 |
| combined_adverse | -2.41 | -1.45 | 3.57 | -0.1849 |
| spread_widen_10bps | -3.13 | -1.91 | 3.97 | -0.1938 |
| spread_widen_25bps | -2.87 | -1.35 | 3.99 | -0.1917 |
| thin_book | -3.91 | -2.53 | 4.29 | -0.1990 |
| very_thin_book | -3.80 | -3.35 | 3.95 | -0.1758 |
| entry_spread_stress | -3.33 | -1.89 | 4.01 | -0.1964 |
| combined_market_deterioration | -4.56 | -2.75 | 5.06 | -0.2188 |
| severe_adverse | -5.10 | -3.01 | 5.50 | -0.2209 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0010)
- **Trend**: ranging (efficiency: 0.0101)
- **Best holdout score**: -0.0373 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.2024 | -0.0373 | -0.72 | 0.89 | 100 |
| 1 | -0.0441 | -0.2806 | -0.26 | 3.49 | 90 |
| 2 | -0.0442 | -0.2783 | -0.72 | 2.60 | 98 |
| 3 | -0.0442 | -0.1637 | 2.12 | 1.37 | 68 |
| 4 | -0.0443 | -0.2585 | 0.43 | 1.62 | 86 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51914
- **Expected rows**: 51914
- **Missing rows**: 0
- **Forward-fill count**: 30
- **Forward-fill fraction**: 0.0005778787995531071
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0446 <= 0; recent PnL -0.9411% < 0
- **Objective score**: -0.0446457515667145
- **PnL %**: -0.9410952530028762
- **Trade count**: 85

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0929 <= 0; recent PnL -0.4655% < 0
- **Objective score**: -0.09287822839366944
- **PnL %**: -0.465453398735331
- **Trade count**: 32

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.18463339925931535
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1578, -0.1648 |
| sell_spread_base | -0.1752, -0.2039 |
| stop_loss | -0.1867, -0.1822 |
| take_profit | -0.1708, -0.1889 |
| executor_refresh_time | -0.1846, -0.1846 |
| cooldown_time | -0.1631, -0.1469 |
| total_amount_quote | -0.1846, -0.1819 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3144920962952528
- **Max CV**: 0.6348281229888318
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3725 | 0.20853412788505024 | 0.664896662647845 | 0.4182575961680377 |
| buy_spread_ratio | 0.1157 | 1.4538260244314156 | 2.0242810559609867 | 1.6619249594741698 |
| sell_spread_base | 0.5656 | 1.1445450705552949 | 5.43241186504306 | 2.4527255922873255 |
| sell_spread_ratio | 0.1708 | 1.5627061959722555 | 2.966296879032616 | 2.5787409212328605 |
| buy_side_weight | 0.1342 | 0.42219539927936317 | 0.6017704055143922 | 0.5017855712133774 |
| amount_skew | 0.0193 | 3.7756701571013673 | 3.9923885503870777 | 3.894311454406156 |
| stop_loss | 0.5461 | 0.010567904452568994 | 0.060809498680675554 | 0.03331665594116751 |
| take_profit | 0.5717 | 0.005736050647430558 | 0.02750778938737232 | 0.012991033192140377 |
| executor_refresh_time | 0.6348 | 573.0 | 3835.0 | 1622.7 |
| cooldown_time | 0.2644 | 529.0 | 2364.0 | 2068.2 |
| total_amount_quote | 0.0643 | 812.6949143252115 | 999.001347921146 | 926.192398435636 |

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
| recent_objective | > 0 | -0.0446457515667145 | FAIL |
| recent_pnl | >= 0 | -0.9410952530028762 | FAIL |
| recent_trades | >= 5 | 85 | PASS |
| worst_stress | > -10 | -0.2208520184666365 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.03730419328127747 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.2208520184666365 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.0446457515667145, pnl=-0.9410952530028762, trades=85, reason=recent objective score -0.0446 <= 0; recent PnL -0.9411% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.09287822839366944, pnl=-0.465453398735331, trades=32, reason=recent objective score -0.0929 <= 0; recent PnL -0.4655% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3144920962952528 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51914 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0446 <= 0; recent PnL -0.9411% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0929 <= 0; recent PnL -0.4655% < 0 |
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
- **run_timestamp**: 2026-04-09T09:56:06.812346+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 5374
