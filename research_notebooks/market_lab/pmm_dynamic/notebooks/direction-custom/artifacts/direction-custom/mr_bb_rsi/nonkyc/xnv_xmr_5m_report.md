# PMM Dynamic Optimization Report: nonkyc_XNV-XMR_5m_mr_bb_rsi_v1

Generated: 2026-04-18 16:19:00 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T16:19:00.250699+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 64 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: XNV-XMR
- **interval**: 5m
- **n_candles**: 22398
- **dataset_hash**: b8551765a4bad1e07e0d6e4875a2a8e796193fcdd2099c9b25d963b997609186
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 482.43614973461814
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 28 |
| bb_length | 92 |
| bb_std | 2.589058462779366 |
| bbp_entry_threshold | 0.36259350863916107 |
| cooldown_time | 2019 |
| max_atr_pct_for_entry | 0.06733034139037168 |
| min_volume_quantile | 6.435391184218542e-05 |
| rsi_entry_threshold | 49.67591022134317 |
| rsi_length | 13 |
| stop_loss | 0.025375802829028172 |
| take_profit | 0.059305716043395275 |
| take_profit_order_type | MARKET |
| time_limit | 54504 |
| total_amount_quote | 482.43614973461814 |
| trailing_stop_activation | 0.002781186646172924 |
| trailing_stop_delta | 0.01410946877192541 |
| trend_ema_length | 174 |
| use_trend_filter | True |
| volume_filter_window | 553 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 482.43614973461814 |
| Selected | 482.43614973461814 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.0433
- **Net PnL (quote)**: -0.2090
- **Sharpe Ratio**: -43.4539
- **Max Drawdown %**: 0.0435
- **Profit Factor**: 0.001268208855282366
- **Trade Count**: 683
- **Total Fees (quote)**: 0.0229
- **Maker Fees**: 0.0082
- **Taker Fees**: 0.0147
- **Fee Drag %**: 0.0047

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.2826
- **PnL Component**: -0.0004
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0003
- **Fee Drag Component**: -0.0000
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
| 6 | -0.00 | -0.28 | 0.00 | 100 | -0.0033 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.05 | -44.97 | 0.05 | -0.2820 |
| fees_2x | -0.05 | -46.40 | 0.05 | -0.2815 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -0.02 | -43.45 | 0.02 | -0.2822 |
| very_low_liquidity | -0.01 | -43.45 | 0.01 | -0.2820 |
| high_slippage | -0.04 | -44.00 | 0.04 | -0.2825 |
| extreme_slippage | -0.05 | -45.07 | 0.05 | -0.2824 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -0.04 | -43.34 | 0.04 | -0.2825 |
| spread_widen_25bps | -0.04 | -43.18 | 0.04 | -0.2824 |
| thin_book | -0.00 | -3.36 | 0.00 | -1000.0000 |
| very_thin_book | 0.00 | 0.00 | 0.00 | -1000.0000 |
| entry_spread_stress | -0.04 | -43.29 | 0.04 | -0.2825 |
| combined_market_deterioration | -0.02 | -20.39 | 0.02 | -0.2824 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 2873
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0085)
- **Trend**: ranging (efficiency: 0.0162)
- **Best holdout score**: -1000.0000 (rank #-1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.1413 | -1000.0000 | 0.00 | 0.00 | 0 |
| 1 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 4 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 22398
- **Expected rows**: 22433
- **Missing rows**: 35
- **Forward-fill count**: 229
- **Forward-fill fraction**: 0.010224127154210198
- **Longest gap (seconds)**: 6600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0033 <= 0; recent PnL -0.0000% < 0
- **Objective score**: -0.003334694824649135
- **PnL %**: -3.616596852829568e-05
- **Trade count**: 100

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0033 <= 0; recent PnL -0.0000% < 0
- **Objective score**: -0.0033347671190763835
- **PnL %**: -3.616596852829568e-05
- **Trade count**: 100

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.038461538461538464
- **Baseline score**: -0.27481283537011547
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.2747, -0.0000 |
| bb_std | -0.2748, -0.2830 |
| bbp_entry_threshold | -1000.0000, -0.2830 |
| rsi_length | -0.2748, -0.2748 |
| rsi_entry_threshold | -0.2748, -0.2831 |
| trend_ema_length | -0.2748, -0.2748 |
| max_atr_pct_for_entry | -0.2748, -0.2748 |
| volume_filter_window | -0.2748, -0.2748 |
| min_volume_quantile | -0.2748, -0.2748 |
| stop_loss | -0.2752, -0.2744 |
| take_profit | -0.2748, -0.2748 |
| cooldown_time | -0.2748, -0.2748 |
| total_amount_quote | -0.2747, -0.2749 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5465690930453482
- **Max CV**: 0.7035440873964931
- **Clustered params**: stop_loss
- **Scattered params**: take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4511 | 0.015846488196553956 | 0.06760341855737632 | 0.03903996279418816 |
| take_profit | 0.5016 | 0.005570740712340032 | 0.025877575042778093 | 0.014127329229890708 |
| cooldown_time | 0.7035 | 1319.0 | 81404.0 | 45223.8 |
| total_amount_quote | 0.5300 | 27.846360259215086 | 973.6975036774652 | 581.5399116555404 |

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
- walkforward_robust: **FAIL**
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.003334694824649135 | FAIL |
| recent_pnl | >= 0 | -3.616596852829568e-05 | FAIL |
| recent_trades | >= 5 | 100 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.038461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 7 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.038461538461538464 |
| recent_28d | FAIL | score=-0.003334694824649135, pnl=-3.616596852829568e-05, trades=100, reason=recent objective score -0.0033 <= 0; recent PnL -0.0000% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.0033347671190763835, pnl=-3.616596852829568e-05, trades=100, reason=recent objective score -0.0033 <= 0; recent PnL -0.0000% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5465690930453482 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 22398 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0033 <= 0; recent PnL -0.0000% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0033 <= 0; recent PnL -0.0000% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 22398
- **Pre-release bars**: 14368
- **Dev bars**: 11495
- **Holdout bars**: 2873
- **Recent 28d bars**: 8030
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T16:19:00.250699+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 64
- **validation_status**: validated_fail
