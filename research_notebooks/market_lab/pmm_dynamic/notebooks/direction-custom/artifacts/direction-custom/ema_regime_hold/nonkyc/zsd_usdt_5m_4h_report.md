# PMM Dynamic Optimization Report: nonkyc_ZSD-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:43:11 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:43:11.605015+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 138 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ZSD-USDT
- **interval**: 5m+4h
- **n_candles**: 57366
- **dataset_hash**: c11d921e28e1eace04c70259bf3e748a1ed86df6848d18c9b220e5cf44134089
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 154.86060755086032
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 84690 |
| min_volume_quantile | 0.07622214526520113 |
| regime_adx_length | 11 |
| regime_adx_threshold | 23.334509081464862 |
| regime_ema_fast | 49 |
| regime_ema_slow | 232 |
| stop_loss | 0.05796348636565926 |
| take_profit | 0.038370993862595834 |
| take_profit_order_type | MARKET |
| time_limit | 420552 |
| total_amount_quote | 154.86060755086032 |
| trailing_stop_activation | 0.0014176212332046706 |
| trailing_stop_delta | 0.016142128716636776 |
| volume_filter_window | 380 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 154.86060755086032 |
| Selected | 154.86060755086032 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 7.2314
- **Net PnL (quote)**: 11.1986
- **Sharpe Ratio**: 1.4436
- **Max Drawdown %**: 2.8397
- **Profit Factor**: 5.172524477671482
- **Trade Count**: 1148
- **Total Fees (quote)**: 9.1330
- **Maker Fees**: 3.1939
- **Taker Fees**: 5.9391
- **Fee Drag %**: 5.8976

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0186
- **PnL Component**: 0.0698
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0213
- **Fee Drag Component**: -0.0295
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1371**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.12 | -0.24 | 0.92 | 120 | -0.0115 | n/a |
| 1 | 2.08 | 4.80 | 1.05 | 319 | -0.0015 | n/a |
| 2 | 0.18 | 10.78 | 0.02 | 70 | 0.0001 | n/a |
| 3 | 2.20 | 1.69 | 2.89 | 365 | -0.1692 | n/a |
| 4 | 0.76 | 2.40 | 1.16 | 163 | -0.0071 | n/a |
| 5 | 2.50 | 4.20 | 1.07 | 182 | 0.0060 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | -3.66 | -3.13 | 3.74 | 124 | -0.3818 | n/a |
| 8 | -3.20 | -1.76 | 3.69 | 439 | -0.3730 | n/a |
| 9 | 0.13 | 0.26 | 1.43 | 598 | -0.2770 | n/a |
| 10 | -0.92 | -0.42 | 3.04 | 610 | -0.4116 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 4.28 | 0.89 | 3.11 | -0.0309 |
| fees_2x | 1.29 | 0.31 | 3.97 | -0.1222 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 4.84 | 1.60 | 2.59 | 0.0028 |
| very_low_liquidity | 4.95 | 1.07 | 2.04 | -0.0011 |
| high_slippage | 6.27 | 1.27 | 2.92 | 0.0091 |
| extreme_slippage | 4.36 | 0.91 | 3.08 | -0.0140 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 6.70 | 0.90 | 3.89 | 0.0061 |
| spread_widen_25bps | 5.89 | 0.73 | 4.51 | -0.0082 |
| thin_book | 8.03 | 1.26 | 3.35 | -0.0043 |
| very_thin_book | -5.57 | -0.73 | 7.67 | -0.1888 |
| entry_spread_stress | 6.31 | 0.85 | 3.92 | 0.0022 |
| combined_market_deterioration | 1.96 | 0.53 | 3.62 | -0.0468 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 9865
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0057)
- **Trend**: ranging (efficiency: 0.0014)
- **Best holdout score**: -0.0455 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9907 | -0.1490 | -3.66 | 3.74 | 124 |
| 1 | -0.0143 | -0.4928 | -2.66 | 2.68 | 241 |
| 2 | -0.0166 | -0.3327 | -3.03 | 3.10 | 129 |
| 3 | -0.0238 | -0.0455 | -1.42 | 1.50 | 231 |
| 4 | -0.0293 | -0.0828 | 0.05 | 0.78 | 125 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 57366
- **Expected rows**: 57393
- **Missing rows**: 27
- **Forward-fill count**: 1139
- **Forward-fill fraction**: 0.01985496635637834
- **Longest gap (seconds)**: 6600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3441 <= 0; recent PnL -1.3452% < 0
- **Objective score**: -0.3440738119084114
- **PnL %**: -1.3451617669797011
- **Trade count**: 834

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4247 <= 0; recent PnL -1.0516% < 0
- **Objective score**: -0.4247230167203142
- **PnL %**: -1.0515923772487354
- **Trade count**: 383

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1970 <= 0; recent PnL -0.4583% < 0
- **Objective score**: -0.19702574829974367
- **PnL %**: -0.45828851751531785
- **Trade count**: 298

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.3388673868973533
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.1934, -0.3363 |
| regime_ema_slow | -0.3639, -0.1850 |
| regime_adx_length | -0.2538, -0.2461 |
| regime_adx_threshold | -0.3342, -0.3873 |
| volume_filter_window | -0.3389, -0.3389 |
| min_volume_quantile | -0.3389, -0.3389 |
| stop_loss | -0.3492, -0.3507 |
| take_profit | -0.3389, -0.3389 |
| cooldown_time | -0.1029, -0.2443 |
| total_amount_quote | -0.3246, -0.3287 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.40358171044561214
- **Max CV**: 0.6270263268003116
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3630 | 0.021615581794270276 | 0.06538928178194768 | 0.04001997760858274 |
| take_profit | 0.6270 | 0.0144136978928963 | 0.09012226534626168 | 0.03635085048673381 |
| cooldown_time | 0.1761 | 41514.0 | 85216.0 | 73082.4 |
| total_amount_quote | 0.4482 | 104.0127073157656 | 494.1360970877191 | 275.49252850975597 |

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
- **fill_participation_rate**: 0.1
- **latency_bars**: 1
- **slippage_bps**: 5.0
- **refresh_close_mode**: market_close

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: **FAIL**
- yaml_validates: **FAIL**
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
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
| recent_objective | > 0 | -0.3440738119084114 | FAIL |
| recent_pnl | >= 0 | -1.3451617669797011 | FAIL |
| recent_trades | >= 5 | 834 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.14901720551279315 |
| walkforward | PASS | 11 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.3440738119084114, pnl=-1.3451617669797011, trades=834, reason=recent objective score -0.3441 <= 0; recent PnL -1.3452% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.4247230167203142, pnl=-1.0515923772487354, trades=383, reason=recent objective score -0.4247 <= 0; recent PnL -1.0516% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.19702574829974367, pnl=-0.45828851751531785, trades=298, reason=recent objective score -0.1970 <= 0; recent PnL -0.4583% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.40358171044561214 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 57366 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3441 <= 0; recent PnL -1.3452% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.4247 <= 0; recent PnL -1.0516% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1970 <= 0; recent PnL -0.4583% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 57366
- **Pre-release bars**: 49328
- **Dev bars**: 39463
- **Holdout bars**: 9865
- **Recent 28d bars**: 8038
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:43:11.605015+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 138
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
