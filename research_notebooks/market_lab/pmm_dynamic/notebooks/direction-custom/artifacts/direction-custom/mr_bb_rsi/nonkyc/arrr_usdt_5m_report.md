# PMM Dynamic Optimization Report: nonkyc_ARRR-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 12:08:05 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T12:08:05.711248+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 2601 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-USDT
- **interval**: 5m
- **n_candles**: 51897
- **dataset_hash**: 9e18c250ad69f09d4b67a8cc801311c5bd1a56fab6d1c6b137afa85a70bc889d
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 911.2349618908909
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 22 |
| bb_length | 150 |
| bb_std | 2.8914362360048242 |
| bbp_entry_threshold | 0.18661451200995055 |
| cooldown_time | 77567 |
| max_atr_pct_for_entry | 0.010642999537232203 |
| min_volume_quantile | 0.4449190396906866 |
| rsi_entry_threshold | 38.48307453536121 |
| rsi_length | 8 |
| stop_loss | 0.05846317175048089 |
| take_profit | 0.005218425927631816 |
| take_profit_order_type | MARKET |
| time_limit | 27750 |
| total_amount_quote | 911.2349618908909 |
| trailing_stop_activation | 0.0004667650436896739 |
| trailing_stop_delta | 0.01327548057910831 |
| trend_ema_length | 208 |
| use_trend_filter | False |
| volume_filter_window | 76 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 911.2349618908909 |
| Selected | 911.2349618908909 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0442
- **Net PnL (quote)**: -9.5153
- **Sharpe Ratio**: -1.0024
- **Max Drawdown %**: 1.2407
- **Profit Factor**: 0.19810129349072225
- **Trade Count**: 117
- **Total Fees (quote)**: 5.6047
- **Maker Fees**: 1.9676
- **Taker Fees**: 3.6371
- **Fee Drag %**: 0.6151

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0229
- **PnL Component**: -0.0105
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0093
- **Fee Drag Component**: -0.0031
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0396**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 2.15 | 4.68 | 1.04 | 68 | 0.0024 | n/a |
| 1 | 1.67 | 9.63 | 0.61 | 57 | 0.0027 | n/a |
| 2 | -4.58 | -5.70 | 5.08 | 44 | -0.1183 | n/a |
| 3 | -6.21 | -8.44 | 6.80 | 7 | -0.5670 | n/a |
| 4 | 5.76 | 6.93 | 2.00 | 76 | 0.0299 | n/a |
| 5 | -1.83 | -2.99 | 2.29 | 29 | -0.1840 | n/a |
| 6 | -1.52 | -1.24 | 2.76 | 96 | -0.0805 | n/a |
| 7 | 4.28 | 3.21 | 3.55 | 104 | -0.0165 | n/a |
| 8 | 2.63 | 13.35 | 0.28 | 61 | 0.0131 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.15 | -1.12 | 1.20 | -0.0229 |
| fees_2x | -1.30 | -1.29 | 1.31 | -0.0459 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -3.13 | -2.06 | 3.29 | -0.1907 |
| very_low_liquidity | -4.66 | -4.87 | 4.70 | -0.3563 |
| high_slippage | -1.05 | -1.01 | 1.18 | -0.0209 |
| extreme_slippage | -1.15 | -1.13 | 1.20 | -0.0221 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.05 | -1.01 | 1.18 | -0.0210 |
| spread_widen_25bps | -1.12 | -1.08 | 1.20 | -0.0219 |
| thin_book | -4.49 | -3.88 | 4.49 | -0.3142 |
| very_thin_book | -4.91 | -4.26 | 4.94 | -0.5165 |
| entry_spread_stress | -1.07 | -1.03 | 1.19 | -0.0213 |
| combined_market_deterioration | -3.46 | -2.19 | 3.51 | -0.1999 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0074)
- **Trend**: ranging (efficiency: 0.0048)
- **Best holdout score**: 0.0112 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0115 | -0.1122 | 3.61 | 3.85 | 228 |
| 1 | 0.0262 | -0.1817 | -4.04 | 4.21 | 26 |
| 2 | 0.0255 | -0.1865 | -2.21 | 2.38 | 17 |
| 3 | 0.0104 | 0.0112 | 8.12 | 3.45 | 110 |
| 4 | 0.0102 | 0.0023 | 4.44 | 2.08 | 64 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51897
- **Expected rows**: 51899
- **Missing rows**: 2
- **Forward-fill count**: 593
- **Forward-fill fraction**: 0.011426479372603425
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.020820392430490487
- **PnL %**: 5.084779829363682
- **Trade count**: 125

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.0015407107535820933
- **PnL %**: 1.9425888751055713
- **Trade count**: 62

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0874 <= 0
- **Objective score**: -0.08740679376792886
- **PnL %**: 1.0507709717126188
- **Trade count**: 27

## Sensitivity Analysis

- **Sensitivity penalty**: 0.34615384615384615
- **Baseline score**: -0.02259195010907921
- **Sign flips**: 0
- **Collapse count**: 9
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1383, -0.3526 |
| bb_std | -0.1383, -0.3596 |
| bbp_entry_threshold | -0.0226, -0.1401 |
| rsi_length | -0.1405, -0.0226 |
| rsi_entry_threshold | -0.2480, -0.1405 |
| trend_ema_length | -0.0226, -0.0226 |
| max_atr_pct_for_entry | -0.0226, -0.0226 |
| volume_filter_window | -0.0226, -0.0226 |
| min_volume_quantile | -0.0226, -0.0226 |
| stop_loss | -0.0226, -0.0207 |
| take_profit | -0.0226, -0.0226 |
| cooldown_time | -0.0226, -0.0226 |
| total_amount_quote | -0.0265, -0.0536 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.46899868878328677
- **Max CV**: 0.7321113907694998
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.1128 | 0.05578932788520953 | 0.07886113237108879 | 0.06725679877449352 |
| take_profit | 0.7321 | 0.007786967637822188 | 0.059358260586679916 | 0.02567772422971324 |
| cooldown_time | 0.5978 | 8332.0 | 86014.0 | 55081.0 |
| total_amount_quote | 0.4333 | 159.29827268097597 | 951.3466272241495 | 593.5304707668843 |

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
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.020820392430490487 | PASS |
| recent_pnl | >= 0 | 5.084779829363682 | PASS |
| recent_trades | >= 5 | 125 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.34615384615384615 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.11223799866540562 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.34615384615384615 |
| recent_28d | PASS | score=0.020820392430490487, pnl=5.084779829363682, trades=125, reason= |
| recent_14d_info | PASS | informational only; score=0.0015407107535820933, pnl=1.9425888751055713, trades=62, reason= |
| recent_7d_info | FAIL | informational only; score=-0.08740679376792886, pnl=1.0507709717126188, trades=27, reason=recent objective score -0.0874 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.46899868878328677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51897 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0874 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51897
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8063
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T12:08:05.711248+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 2601
- **validation_status**: validated_fail
