# PMM Dynamic Optimization Report: nonkyc_DOGE-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 13:22:27 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T13:22:27.236972+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 8944 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: DOGE-USDT
- **interval**: 5m
- **n_candles**: 51896
- **dataset_hash**: 11fc7d96ba8591283232ef91215bc8df6abfa6501bc930c59739740322d5ed1c
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 979.6039079991044
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 20 |
| bb_length | 149 |
| bb_std | 2.1145524424199977 |
| bbp_entry_threshold | 0.10703804625501132 |
| cooldown_time | 1564 |
| max_atr_pct_for_entry | 0.02670410987155396 |
| min_volume_quantile | 0.38627264707614706 |
| rsi_entry_threshold | 41.084350510692275 |
| rsi_length | 21 |
| stop_loss | 0.03529848535864519 |
| take_profit | 0.012447999111597129 |
| take_profit_order_type | LIMIT |
| time_limit | 162566 |
| total_amount_quote | 979.6039079991044 |
| trailing_stop_activation | 0.02515859710855699 |
| trailing_stop_delta | 0.001044615078260789 |
| trend_ema_length | 376 |
| use_trend_filter | True |
| volume_filter_window | 207 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 979.6039079991044 |
| Selected | 979.6039079991044 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3.6073
- **Net PnL (quote)**: 35.3372
- **Sharpe Ratio**: 0.9562
- **Max Drawdown %**: 3.6317
- **Profit Factor**: 1.780961714908249
- **Trade Count**: 453
- **Total Fees (quote)**: 17.7500
- **Maker Fees**: 12.8005
- **Taker Fees**: 4.9495
- **Fee Drag %**: 1.8120
- **TP Min-Notional Failures**: 2818 :warning:
  > 2818 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0211
- **PnL Component**: 0.0354
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0272
- **Fee Drag Component**: -0.0091
- **Inventory Component**: -0.0198
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.3712**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.68 | 3.14 | 0.71 | 117 | -0.0002 | n/a |
| 1 | -0.03 | -2.14 | 0.06 | 39 | -0.2556 | n/a |
| 2 | 0.95 | 4.99 | 0.34 | 95 | 0.0047 | n/a |
| 3 | 0.55 | 5.28 | 0.33 | 55 | 0.0024 | n/a |
| 4 | -0.11 | -1.49 | 0.31 | 11 | -0.4010 | n/a |
| 5 | -3.64 | -15.41 | 3.74 | 23 | -0.4012 | n/a |
| 6 | -0.25 | -1.92 | 0.54 | 16 | -0.4022 | n/a |
| 7 | -1.16 | -9.56 | 1.16 | 4 | -0.3401 | n/a |
| 8 | -1.72 | -12.69 | 1.76 | 14 | -0.3843 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2.70 | 0.74 | 3.82 | -0.0358 |
| fees_2x | 1.80 | 0.51 | 4.01 | -0.0506 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -0.50 | -0.11 | 4.07 | -0.0570 |
| very_low_liquidity | -2.65 | -1.07 | 5.09 | -0.0793 |
| high_slippage | 3.48 | 0.93 | 3.68 | -0.0226 |
| extreme_slippage | 3.23 | 0.87 | 3.77 | -0.0258 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 3.54 | 0.94 | 3.61 | -0.0216 |
| spread_widen_25bps | -3.59 | -2.10 | 3.86 | -0.2615 |
| thin_book | 0.44 | 0.53 | 1.26 | -0.0181 |
| very_thin_book | 0.18 | 1.23 | 0.17 | -0.1717 |
| entry_spread_stress | 3.51 | 0.93 | 3.61 | -0.0218 |
| combined_market_deterioration | -3.90 | -2.73 | 4.08 | -0.2820 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0032)
- **Trend**: ranging (efficiency: 0.0035)
- **Best holdout score**: -0.1175 (rank #2)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0105 | -0.2129 | -1.41 | 1.59 | 20 |
| 1 | 0.0001 | -1000.0000 | -1.16 | 1.16 | 3 |
| 2 | 0.0001 | -0.1175 | -1.95 | 1.95 | 51 |
| 3 | 0.0000 | -0.5107 | -1.12 | 1.15 | 11 |
| 4 | -0.0002 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51896
- **Expected rows**: 51896
- **Missing rows**: 0
- **Forward-fill count**: 72
- **Forward-fill fraction**: 0.0013873901649452752
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3842 <= 0; recent PnL -1.7221% < 0
- **Objective score**: -0.38421624561784373
- **PnL %**: -1.7221061961096586
- **Trade count**: 14

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2054 <= 0; recent PnL -1.0601% < 0
- **Objective score**: -0.20536163462309973
- **PnL %**: -1.0600668347739
- **Trade count**: 47

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3881 <= 0; recent PnL -0.7396% < 0
- **Objective score**: -0.3881163804779336
- **PnL %**: -0.7395657985655867
- **Trade count**: 21

## Sensitivity Analysis

- **Sensitivity penalty**: 0.19230769230769232
- **Baseline score**: -0.1497421453659564
- **Sign flips**: 0
- **Collapse count**: 5
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1181, -0.3746 |
| bb_std | -0.0911, -0.3182 |
| bbp_entry_threshold | -0.1420, -0.1504 |
| rsi_length | -0.0880, -0.1497 |
| rsi_entry_threshold | -0.3283, -0.0910 |
| trend_ema_length | -0.3029, -0.0474 |
| max_atr_pct_for_entry | -0.1497, -0.1497 |
| volume_filter_window | -0.1494, -0.1497 |
| min_volume_quantile | -0.1494, -0.1497 |
| stop_loss | -0.1685, -0.2542 |
| take_profit | -0.1452, -0.1539 |
| cooldown_time | -0.1497, -0.1130 |
| total_amount_quote | -0.1508, -0.1483 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3022852948110857
- **Max CV**: 0.5665997556455991
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3204 | 0.02279981126924449 | 0.06416224934200991 | 0.03859682787564701 |
| take_profit | 0.2559 | 0.005560242284233567 | 0.013091829878721508 | 0.009725229834367074 |
| cooldown_time | 0.5666 | 992.0 | 6850.0 | 3474.3 |
| total_amount_quote | 0.0663 | 817.6213081854421 | 995.4526816880799 | 902.5355308227494 |

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
| recent_objective | > 0 | -0.38421624561784373 | FAIL |
| recent_pnl | >= 0 | -1.7221061961096586 | FAIL |
| recent_trades | >= 5 | 14 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.19230769230769232 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.21288653792419854 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.19230769230769232 |
| recent_28d | FAIL | score=-0.38421624561784373, pnl=-1.7221061961096586, trades=14, reason=recent objective score -0.3842 <= 0; recent PnL -1.7221% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.20536163462309973, pnl=-1.0600668347739, trades=47, reason=recent objective score -0.2054 <= 0; recent PnL -1.0601% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.3881163804779336, pnl=-0.7395657985655867, trades=21, reason=recent objective score -0.3881 <= 0; recent PnL -0.7396% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3022852948110857 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51896 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3842 <= 0; recent PnL -1.7221% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2054 <= 0; recent PnL -1.0601% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.3881 <= 0; recent PnL -0.7396% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51896
- **Pre-release bars**: 43831
- **Dev bars**: 35065
- **Holdout bars**: 8766
- **Recent 28d bars**: 8065
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T13:22:27.236972+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 8944
- **validation_status**: validated_fail
