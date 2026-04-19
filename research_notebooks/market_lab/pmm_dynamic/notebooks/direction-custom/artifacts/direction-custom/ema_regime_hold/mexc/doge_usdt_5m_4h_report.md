# PMM Dynamic Optimization Report: mexc_DOGE-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 16:59:41 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T16:59:41.123112+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 135 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOGE-USDT
- **interval**: 5m+4h
- **n_candles**: 103805
- **dataset_hash**: 6a68c118c72d45939ff1e9a2c1e89f812bceeb8b12872bdc0244a917f3983a80
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 658.4539845277197
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 62865 |
| min_volume_quantile | 0.32728070717900215 |
| regime_adx_length | 11 |
| regime_adx_threshold | 21.079440068864923 |
| regime_ema_fast | 23 |
| regime_ema_slow | 436 |
| stop_loss | 0.03569256291442189 |
| take_profit | 0.03176380592695306 |
| take_profit_order_type | LIMIT |
| time_limit | 77927 |
| total_amount_quote | 658.4539845277197 |
| trailing_stop_activation | 0.04914080026226679 |
| trailing_stop_delta | 0.022032408458346964 |
| volume_filter_window | 496 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 658.4539845277197 |
| Selected | 658.4539845277197 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 39.6416
- **Net PnL (quote)**: 261.0215
- **Sharpe Ratio**: 1.7918
- **Max Drawdown %**: 18.7552
- **Profit Factor**: 1.4237303865897326
- **Trade Count**: 77
- **Total Fees (quote)**: 20.3300
- **Maker Fees**: 15.5707
- **Taker Fees**: 4.7593
- **Fee Drag %**: 3.0875

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0494
- **PnL Component**: 0.3339
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1407
- **Fee Drag Component**: -0.0154
- **Inventory Component**: -0.2251
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | -1.03 | -1.02 | 5.10 | 5 | -0.4729 | n/a |
| 3 | -2.68 | -1.15 | 11.68 | 9 | -0.5866 | n/a |
| 4 | -3.66 | -9.49 | 4.46 | 1 | -1000.0000 | n/a |
| 5 | -3.66 | -8.57 | 3.66 | 1 | -1000.0000 | n/a |
| 6 | 11.54 | 11.97 | 1.55 | 4 | -0.3389 | n/a |
| 7 | -2.23 | -0.81 | 11.84 | 10 | -0.5274 | n/a |
| 8 | -3.66 | -7.54 | 3.66 | 1 | -1000.0000 | n/a |
| 9 | -3.66 | -6.37 | 4.25 | 2 | -1000.0000 | n/a |
| 10 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 11 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 12 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 16 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 20 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.80 | -0.01 | 16.77 | -0.4124 |
| fees_2x | -2.60 | -0.06 | 17.01 | -0.4276 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 39.64 | 1.79 | 18.76 | -0.0494 |
| very_low_liquidity | 39.64 | 1.79 | 18.76 | -0.0494 |
| high_slippage | -2.02 | -0.02 | 16.96 | -0.4121 |
| extreme_slippage | -4.06 | -0.16 | 17.81 | -0.4382 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 24.99 | 1.20 | 17.08 | -0.1499 |
| spread_widen_25bps | -2.09 | -0.26 | 10.82 | -0.2952 |
| thin_book | 25.28 | 1.25 | 13.21 | -0.1151 |
| very_thin_book | -1.94 | -0.14 | 10.37 | -0.2254 |
| entry_spread_stress | -3.06 | -0.10 | 17.37 | -0.2142 |
| combined_market_deterioration | 33.97 | 1.62 | 23.95 | -0.1234 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19159
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0032)
- **Trend**: ranging (efficiency: 0.0136)
- **Best holdout score**: -0.0820 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0247 | -1000.0000 | 0.00 | 0.00 | 0 |
| 1 | -0.2151 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | -0.2159 | -0.0820 | 1.18 | 1.01 | 30 |
| 3 | -0.2180 | -1000.0000 | -1.59 | 2.14 | 3 |
| 4 | -0.2285 | -1000.0000 | -1.49 | 1.49 | 1 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103805
- **Expected rows**: 103861
- **Missing rows**: 56
- **Forward-fill count**: 112
- **Forward-fill fraction**: 0.0010789461008621935
- **Longest gap (seconds)**: 8100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.5
- **Baseline score**: -0.036925434456303
- **Sign flips**: 0
- **Collapse count**: 10
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.0367, -0.0382 |
| regime_ema_slow | -0.0367, -0.0291 |
| regime_adx_length | -0.1716, -0.0123 |
| regime_adx_threshold | -0.0668, -0.2076 |
| volume_filter_window | -0.0369, -0.1392 |
| min_volume_quantile | -0.1332, -0.0378 |
| stop_loss | -0.2361, -0.3488 |
| take_profit | -0.0009, -0.1637 |
| cooldown_time | -0.2257, -0.2903 |
| total_amount_quote | -0.0369, -0.0370 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.48878818700855897
- **Max CV**: 1.0299904686816697
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2221 | 0.04257148156981983 | 0.09229426570386105 | 0.0735376009097641 |
| take_profit | 0.3769 | 0.024213483956957663 | 0.08481812157866227 | 0.04739531611759631 |
| cooldown_time | 1.0300 | 1524.0 | 58174.0 | 23461.0 |
| total_amount_quote | 0.3263 | 332.79010732101153 | 984.852186755636 | 730.4103963357833 |

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
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | 0.0 | PASS |
| recent_trades | >= 5 | 0 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.5 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=0.5 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.48878818700855897 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103805 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103805
- **Pre-release bars**: 95796
- **Dev bars**: 76637
- **Holdout bars**: 19159
- **Recent 28d bars**: 8009
- **Recent window start**: 1774029600

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T16:59:41.123112+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 135
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
