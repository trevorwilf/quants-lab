# PMM Dynamic Optimization Report: mexc_ICP-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:06:19 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:06:19.275253+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 31 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ICP-USDT
- **interval**: 5m+4h
- **n_candles**: 103803
- **dataset_hash**: 96978b54428d8355d5bf2176e25291b014292b991d19a561325057e02dbd135d
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 401.2232084792803
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 4930 |
| min_volume_quantile | 0.2875690061575766 |
| regime_adx_length | 13 |
| regime_adx_threshold | 30.769829871522848 |
| regime_ema_fast | 61 |
| regime_ema_slow | 99 |
| stop_loss | 0.03328893532294333 |
| take_profit | 0.03015178502578876 |
| take_profit_order_type | MARKET |
| time_limit | 256786 |
| total_amount_quote | 401.2232084792803 |
| trailing_stop_activation | 0.03545598748663139 |
| trailing_stop_delta | 0.014277585046205854 |
| volume_filter_window | 74 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 401.2232084792803 |
| Selected | 401.2232084792803 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 36.9681
- **Net PnL (quote)**: 148.3245
- **Sharpe Ratio**: 1.7056
- **Max Drawdown %**: 10.8768
- **Profit Factor**: 1.3731106347827173
- **Trade Count**: 77
- **Total Fees (quote)**: 12.0688
- **Maker Fees**: 6.0183
- **Taker Fees**: 6.0504
- **Fee Drag %**: 3.0080

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.2173
- **PnL Component**: 0.3146
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0816
- **Fee Drag Component**: -0.0150
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 9 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 10 | -1.00 | -0.77 | 4.97 | 5 | -0.2288 | n/a |
| 11 | -3.42 | -3.96 | 4.27 | 2 | -1000.0000 | n/a |
| 12 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | -1.61 | -4.12 | 2.30 | 3 | -1000.0000 | n/a |
| 16 | 2.89 | 1.33 | 15.63 | 71 | -0.3896 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | -1.25 | -2.15 | 2.75 | 4 | -0.4083 | n/a |
| 20 | -3.98 | -10.70 | 3.98 | 7 | -0.2945 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 35.46 | 1.64 | 10.99 | 0.1978 |
| fees_2x | 33.96 | 1.58 | 11.11 | 0.1782 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 36.97 | 1.71 | 10.88 | 0.2173 |
| very_low_liquidity | 36.97 | 1.71 | 10.88 | 0.2173 |
| high_slippage | 33.20 | 1.55 | 11.15 | 0.1873 |
| extreme_slippage | 25.65 | 1.24 | 12.07 | 0.1221 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 36.59 | 1.68 | 10.81 | 0.2150 |
| spread_widen_25bps | -3.42 | -0.80 | 5.82 | -1000.0000 |
| thin_book | -3.42 | -1.15 | 4.02 | -1000.0000 |
| very_thin_book | -3.42 | -1.05 | 4.83 | -1000.0000 |
| entry_spread_stress | -3.42 | -0.80 | 5.86 | -1000.0000 |
| combined_market_deterioration | -1.53 | -0.04 | 9.70 | -0.2215 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19160
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0045)
- **Trend**: ranging (efficiency: 0.0053)
- **Best holdout score**: -0.2498 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.8914 | -0.4606 | -2.39 | 17.71 | 90 |
| 1 | -1000.0000 | -0.2498 | -2.99 | 4.69 | 5 |
| 2 | -1000.0000 | -0.3388 | -3.01 | 7.49 | 4 |
| 3 | -1000.0000 | -1000.0000 | -2.99 | 4.79 | 3 |
| 4 | -1000.0000 | -1000.0000 | -2.04 | 2.80 | 3 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103803
- **Expected rows**: 103868
- **Missing rows**: 65
- **Forward-fill count**: 214
- **Forward-fill fraction**: 0.0020615974490139975
- **Longest gap (seconds)**: 19800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2944 <= 0; recent PnL -3.9823% < 0
- **Objective score**: -0.2943571458300307
- **PnL %**: -3.9822876034414167
- **Trade count**: 7

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2764 <= 0; recent PnL -2.3753% < 0
- **Objective score**: -0.2764132502449498
- **PnL %**: -2.3753352468162294
- **Trade count**: 10

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 1.15
- **Baseline score**: 0.08538453281112732
- **Sign flips**: 11
- **Collapse count**: 12
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -1000.0000, -1000.0000 |
| regime_ema_slow | -1000.0000, -1000.0000 |
| regime_adx_length | 0.0398, -0.2216 |
| regime_adx_threshold | 0.1894, -0.3075 |
| volume_filter_window | 0.0769, 0.0854 |
| min_volume_quantile | 0.1260, 0.0997 |
| stop_loss | -0.2507, -0.2407 |
| take_profit | -1000.0000, 0.1059 |
| cooldown_time | -0.2805, -0.2703 |
| total_amount_quote | 0.0854, 0.0854 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5755714253901677
- **Max CV**: 0.7234175758948191
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4708 | 0.022961564713937427 | 0.0825158425491216 | 0.04414834791047861 |
| take_profit | 0.6187 | 0.01645477416780652 | 0.07948998901397729 | 0.037266436929498895 |
| cooldown_time | 0.7234 | 4806.0 | 83356.0 | 36402.3 |
| total_amount_quote | 0.4893 | 142.22499629651378 | 670.0304205910417 | 380.94402331641834 |

## Execution Realism Assumptions

- **taker_probability**: 0.0
- **supports_post_only**: True
- **connector**: mexc
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
- walkforward_robust: **FAIL**
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.2943571458300307 | FAIL |
| recent_pnl | >= 0 | -3.9822876034414167 | FAIL |
| recent_trades | >= 5 | 7 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 1.15 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.4606102512321665 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=1.15 |
| recent_28d | FAIL | score=-0.2943571458300307, pnl=-3.9822876034414167, trades=7, reason=recent objective score -0.2944 <= 0; recent PnL -3.9823% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.2764132502449498, pnl=-2.3753352468162294, trades=10, reason=recent objective score -0.2764 <= 0; recent PnL -2.3753% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5755714253901677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103803 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2944 <= 0; recent PnL -3.9823% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2764 <= 0; recent PnL -2.3753% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103803
- **Pre-release bars**: 95803
- **Dev bars**: 76643
- **Holdout bars**: 19160
- **Recent 28d bars**: 8000
- **Recent window start**: 1774032000

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:06:19.275253+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 31
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
