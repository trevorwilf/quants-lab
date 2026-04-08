# PMM Dynamic Optimization Report: nonkyc_BCH-USDT_5m_sweep_v1

Generated: 2026-04-08 20:34:04 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T20:34:04.745151+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 6747 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BCH-USDT
- **interval**: 5m
- **n_candles**: 51913
- **dataset_hash**: 358d33a9f0da15d5ddf52eb71c3779887fde573ee5633ef459f78f917c4d46bc
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 958.0894035417915
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.970492765911618 |
| buy_n_levels | 10 |
| buy_side_weight | 0.25444472811833535 |
| buy_spread_base | 2.625639228771732 |
| buy_spread_ratio | 2.5199883635297855 |
| cooldown_time | 826 |
| executor_refresh_time | 13588 |
| macd_fast | 28 |
| macd_signal | 6 |
| macd_slow | 52 |
| natr_length | 43 |
| sell_n_levels | 6 |
| sell_spread_base | 3.5409823918735404 |
| sell_spread_ratio | 1.7850605433878695 |
| stop_loss | 0.03423737393793685 |
| take_profit | 0.005125509103819814 |
| time_limit | 99462 |
| total_amount_quote | 958.0894035417915 |
| trailing_stop_activation | 0.053664851025789925 |
| trailing_stop_delta | 0.006227721050632863 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 958.0894035417915 |
| Selected | 958.0894035417915 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -6.7773
- **Net PnL (quote)**: -64.9322
- **Sharpe Ratio**: -7.0721
- **Max Drawdown %**: 7.3222
- **Profit Factor**: 0.28883391862649604
- **Trade Count**: 1100
- **Total Fees (quote)**: 23.9524
- **Maker Fees**: 18.8677
- **Taker Fees**: 5.0847
- **Fee Drag %**: 2.5000
- **TP Min-Notional Failures**: 6895 :warning:
  > 6895 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1548
- **PnL Component**: -0.0702
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0549
- **Fee Drag Component**: -0.0125
- **Inventory Component**: -0.0170
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0157**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.23 | -14.13 | 0.24 | 62 | -0.0065 | n/a |
| 1 | -0.35 | -10.60 | 0.41 | 66 | -0.0123 | n/a |
| 2 | -0.17 | -10.78 | 0.19 | 66 | -0.1111 | n/a |
| 3 | -0.16 | -7.83 | 0.19 | 62 | -0.0054 | n/a |
| 4 | -1.20 | -14.74 | 1.25 | 79 | -0.0869 | n/a |
| 5 | -0.36 | -9.95 | 0.42 | 81 | -0.0095 | n/a |
| 6 | -0.61 | -11.57 | 0.65 | 77 | -0.0186 | n/a |
| 7 | -0.07 | -1.02 | 0.24 | 69 | -0.0051 | n/a |
| 8 | -1.07 | -8.22 | 1.08 | 73 | -0.0592 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.2272)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -8.03 | -8.30 | 8.54 | -0.1839 |
| fees_2x | -9.28 | -9.51 | 9.76 | -0.2131 |
| latency_plus1 | -6.79 | -7.08 | 7.33 | -0.1550 |
| latency_plus2 | -6.85 | -7.15 | 7.40 | -0.1561 |
| latency_plus3 | -7.86 | -7.73 | 8.55 | -0.1762 |
| low_liquidity | -6.27 | -5.22 | 7.05 | -0.1536 |
| very_low_liquidity | -6.34 | -6.99 | 6.75 | -0.1461 |
| high_slippage | -6.91 | -7.19 | 7.45 | -0.1573 |
| extreme_slippage | -7.18 | -7.42 | 7.72 | -0.1621 |
| combined_adverse | -7.79 | -6.44 | 8.53 | -0.1881 |
| spread_widen_10bps | -7.14 | -6.74 | 7.75 | -0.1639 |
| spread_widen_25bps | -8.68 | -8.16 | 9.41 | -0.1941 |
| thin_book | -7.23 | -7.34 | 7.72 | -0.1601 |
| very_thin_book | -6.78 | -7.87 | 7.05 | -0.1449 |
| entry_spread_stress | -7.59 | -8.07 | 8.24 | -0.1700 |
| combined_market_deterioration | -8.38 | -9.11 | 8.74 | -0.1880 |
| severe_adverse | -10.26 | -9.68 | 10.88 | -0.2272 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0025)
- **Trend**: ranging (efficiency: 0.0102)
- **Best holdout score**: -0.0186 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1910 | -0.0186 | -0.82 | 0.87 | 163 |
| 1 | -0.0072 | -0.0257 | -0.92 | 1.01 | 203 |
| 2 | -0.0073 | -0.1202 | -3.20 | 4.31 | 402 |
| 3 | -0.0078 | -0.1801 | -5.90 | 6.55 | 454 |
| 4 | -0.0080 | -0.0824 | -2.75 | 3.00 | 386 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51913
- **Expected rows**: 51913
- **Missing rows**: 0
- **Forward-fill count**: 468
- **Forward-fill fraction**: 0.009015082927205131
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0382 <= 0; recent PnL -1.0650% < 0
- **Objective score**: -0.03816339357421329
- **PnL %**: -1.0649602364888777
- **Trade count**: 116

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0459 <= 0; recent PnL -0.1960% < 0
- **Objective score**: -0.04589254946048295
- **PnL %**: -0.19601191910570528
- **Trade count**: 40

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1311 <= 0; recent PnL -0.0608% < 0
- **Objective score**: -0.13110923563654275
- **PnL %**: -0.06075676583587921
- **Trade count**: 18

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.20420473519644633
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1715, -0.2119 |
| sell_spread_base | -0.1988, -0.1872 |
| stop_loss | -0.2080, -0.1897 |
| take_profit | -0.1978, -0.1998 |
| executor_refresh_time | -0.1767, -0.1993 |
| cooldown_time | -0.2074, -0.2042 |
| total_amount_quote | -0.2041, -0.2277 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.27887740035552977
- **Max CV**: 0.8121912531859111
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1377 | 2.1076846630234596 | 3.2284443713272517 | 2.7363841848639487 |
| buy_spread_ratio | 0.0748 | 2.147912667266236 | 2.8063529335539 | 2.4614301560997407 |
| sell_spread_base | 0.8122 | 0.5246927363319085 | 5.821586192257559 | 2.4237712380065948 |
| sell_spread_ratio | 0.1383 | 1.3712784707723276 | 2.088611705027325 | 1.6796499198129318 |
| buy_side_weight | 0.2537 | 0.22410105028045102 | 0.5059394524606423 | 0.3316738941589211 |
| amount_skew | 0.1129 | 2.680458032598168 | 3.8660688835626065 | 3.1982794201015894 |
| stop_loss | 0.7270 | 0.011442704707892548 | 0.106034673928546 | 0.04752812833708471 |
| take_profit | 0.0499 | 0.005025955321694206 | 0.005767440822457233 | 0.0053482151597617055 |
| executor_refresh_time | 0.1206 | 8816.0 | 14360.0 | 13136.4 |
| cooldown_time | 0.5444 | 371.0 | 5205.0 | 2854.0 |
| total_amount_quote | 0.0960 | 763.9007336635159 | 994.7849169182564 | 881.8427238219841 |

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
- walkforward_positive_majority: **FAIL**
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.03816339357421329 | FAIL |
| recent_pnl | >= 0 | -1.0649602364888777 | FAIL |
| recent_trades | >= 5 | 116 | PASS |
| worst_stress | > -10 | -0.22719385129880793 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.01855353102893875 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.22719385129880793 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.03816339357421329, pnl=-1.0649602364888777, trades=116, reason=recent objective score -0.0382 <= 0; recent PnL -1.0650% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.04589254946048295, pnl=-0.19601191910570528, trades=40, reason=recent objective score -0.0459 <= 0; recent PnL -0.1960% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.13110923563654275, pnl=-0.06075676583587921, trades=18, reason=recent objective score -0.1311 <= 0; recent PnL -0.0608% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.27887740035552977 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51913 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0382 <= 0; recent PnL -1.0650% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0459 <= 0; recent PnL -0.1960% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1311 <= 0; recent PnL -0.0608% < 0 |
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
- **run_timestamp**: 2026-04-08T20:34:04.745151+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 6747
