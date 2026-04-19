# PMM Dynamic Optimization Report: nonkyc_EPIC-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:29:22 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:29:22.809970+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 229 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: EPIC-USDT
- **interval**: 5m+4h
- **n_candles**: 38455
- **dataset_hash**: 16ac93ef6787b0c1cf7bb37b4d8a146903cac03374a7142c8fb5d2a6656247e0
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 190.42057846313782
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 66599 |
| min_volume_quantile | 0.07573007452563985 |
| regime_adx_length | 12 |
| regime_adx_threshold | 32.71278097492353 |
| regime_ema_fast | 73 |
| regime_ema_slow | 291 |
| stop_loss | 0.020480069346704172 |
| take_profit | 0.03630659723787422 |
| take_profit_order_type | MARKET |
| time_limit | 286713 |
| total_amount_quote | 190.42057846313782 |
| trailing_stop_activation | 0.011805877746705034 |
| trailing_stop_delta | 0.024992332668393895 |
| volume_filter_window | 519 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 190.42057846313782 |
| Selected | 190.42057846313782 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 34.0260
- **Net PnL (quote)**: 64.7925
- **Sharpe Ratio**: 3.2606
- **Max Drawdown %**: 6.0073
- **Profit Factor**: 4.747487775776664
- **Trade Count**: 336
- **Total Fees (quote)**: 11.9326
- **Maker Fees**: 4.1507
- **Taker Fees**: 7.7819
- **Fee Drag %**: 6.2664

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1729
- **PnL Component**: 0.2929
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0451
- **Fee Drag Component**: -0.0313
- **Inventory Component**: -0.0421
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.3800**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | 16.45 | 5.96 | 1.54 | 133 | -0.1080 | n/a |
| 2 | 15.18 | 4.63 | 6.82 | 225 | -0.1469 | n/a |
| 3 | -2.40 | -5.58 | 2.58 | 19 | -0.5062 | n/a |
| 4 | -1.04 | -0.50 | 2.01 | 36 | -0.4447 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 30.89 | 3.00 | 6.77 | 0.1275 |
| fees_2x | 27.76 | 2.74 | 7.56 | 0.0814 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -2.30 | -0.56 | 4.67 | -0.1270 |
| very_low_liquidity | -1.09 | -1.32 | 2.44 | -0.0338 |
| high_slippage | 33.01 | 3.18 | 6.25 | 0.1633 |
| extreme_slippage | 30.97 | 3.02 | 6.74 | 0.1440 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 27.32 | 2.59 | 6.62 | 0.0614 |
| spread_widen_25bps | -1.07 | -0.71 | 2.43 | -0.0813 |
| thin_book | -1.26 | -0.83 | 2.91 | -0.0715 |
| very_thin_book | -2.13 | -1.61 | 2.42 | -0.3183 |
| entry_spread_stress | 24.11 | 2.38 | 6.72 | 0.1331 |
| combined_market_deterioration | 4.31 | 0.67 | 12.62 | -0.1354 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 6078
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0083)
- **Trend**: ranging (efficiency: 0.0006)
- **Best holdout score**: -0.3761 (rank #2)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9135 | -0.3898 | -2.42 | 2.65 | 19 |
| 1 | 0.0495 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | 0.0484 | -0.3761 | -2.54 | 4.87 | 30 |
| 3 | 0.0329 | -0.4739 | -9.70 | 10.02 | 299 |
| 4 | 0.0311 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 38455
- **Expected rows**: 38455
- **Missing rows**: 0
- **Forward-fill count**: 291
- **Forward-fill fraction**: 0.007567286438694578
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0764 <= 0; recent PnL -3.1732% < 0
- **Objective score**: -0.07644495727601122
- **PnL %**: -3.173189041639779
- **Trade count**: 70

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

- **Sensitivity penalty**: 0.6
- **Baseline score**: -0.02834797154766247
- **Sign flips**: 0
- **Collapse count**: 12
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.5050, -0.3651 |
| regime_ema_slow | -0.4233, -0.3784 |
| regime_adx_length | -0.4352, -0.2120 |
| regime_adx_threshold | -0.1934, -0.2588 |
| volume_filter_window | -0.0283, -0.0283 |
| min_volume_quantile | -0.1767, -0.0281 |
| stop_loss | -0.0524, -0.1391 |
| take_profit | -0.0283, -0.0283 |
| cooldown_time | -0.0332, -0.2105 |
| total_amount_quote | -0.0293, -0.0278 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.37183169239791625
- **Max CV**: 0.48489872153111385
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4849 | 0.020008873291095793 | 0.09118303747099242 | 0.047727400748531205 |
| take_profit | 0.4460 | 0.024881977393571293 | 0.0975800446531221 | 0.05750544045884472 |
| cooldown_time | 0.1093 | 60268.0 | 83736.0 | 69275.8 |
| total_amount_quote | 0.4471 | 134.62495167931866 | 826.2198261401468 | 527.441137022011 |

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
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.07644495727601122 | FAIL |
| recent_pnl | >= 0 | -3.173189041639779 | FAIL |
| recent_trades | >= 5 | 70 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.6 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.38975489079111103 |
| walkforward | PASS | 6 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=0.6 |
| recent_28d | FAIL | score=-0.07644495727601122, pnl=-3.173189041639779, trades=70, reason=recent objective score -0.0764 <= 0; recent PnL -3.1732% < 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.37183169239791625 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 38455 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0764 <= 0; recent PnL -3.1732% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 38455
- **Pre-release bars**: 30390
- **Dev bars**: 24312
- **Holdout bars**: 6078
- **Recent 28d bars**: 8065
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:29:22.809970+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 229
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
