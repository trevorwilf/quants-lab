# PMM Dynamic Optimization Report: mexc_ETH-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 08:48:06 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T08:48:06.020631+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 8229 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ETH-USDT
- **interval**: 5m
- **n_candles**: 51667
- **dataset_hash**: e0a01f8aa3000c07ade818eb591589ba0ccc31a09c59b0ae0f6a798d38b4c2a9
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 524.2877056804203
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 27 |
| bb_length | 65 |
| bb_std | 1.008295273777009 |
| bbp_entry_threshold | 0.23421053470024364 |
| cooldown_time | 83716 |
| max_atr_pct_for_entry | 0.017057265188214314 |
| min_volume_quantile | 0.023865111773221412 |
| rsi_entry_threshold | 42.46472899915389 |
| rsi_length | 23 |
| stop_loss | 0.0459671668612341 |
| take_profit | 0.04252100359301771 |
| take_profit_order_type | LIMIT |
| time_limit | 11540 |
| total_amount_quote | 524.2877056804203 |
| trailing_stop_activation | 0.00016428880952066644 |
| trailing_stop_delta | 0.009231136535528638 |
| trend_ema_length | 369 |
| use_trend_filter | False |
| volume_filter_window | 306 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 524.2877056804203 |
| Selected | 524.2877056804203 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 7.7335
- **Net PnL (quote)**: 40.5456
- **Sharpe Ratio**: 2.1394
- **Max Drawdown %**: 2.2178
- **Profit Factor**: 2.385090342302981
- **Trade Count**: 114
- **Total Fees (quote)**: 21.8173
- **Maker Fees**: 10.9024
- **Taker Fees**: 10.9149
- **Fee Drag %**: 4.1613

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0368
- **PnL Component**: 0.0745
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0166
- **Fee Drag Component**: -0.0208
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1671**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.43 | -3.17 | 3.03 | 7 | -0.2369 | n/a |
| 1 | 1.06 | 2.43 | 2.04 | 12 | -0.1594 | n/a |
| 2 | 1.38 | 6.94 | 0.50 | 13 | -0.1405 | n/a |
| 3 | 0.69 | 2.54 | 1.08 | 13 | -0.1518 | n/a |
| 4 | 2.45 | 4.41 | 1.91 | 13 | -0.1407 | n/a |
| 5 | -1.21 | -2.02 | 3.27 | 3 | -1000.0000 | n/a |
| 6 | 0.44 | 1.58 | 0.93 | 12 | -0.1572 | n/a |
| 7 | -1.49 | -5.33 | 1.85 | 12 | -0.2249 | n/a |
| 8 | -4.02 | -9.65 | 4.13 | 12 | -0.2345 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 5.69 | 1.59 | 2.29 | 0.0068 |
| fees_2x | 3.60 | 1.03 | 2.44 | -0.0248 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 7.73 | 2.14 | 2.22 | 0.0368 |
| very_low_liquidity | 7.73 | 2.14 | 2.22 | 0.0368 |
| high_slippage | -1.04 | -1.01 | 1.77 | -0.1234 |
| extreme_slippage | -1.16 | -2.56 | 1.16 | -0.3859 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.44 | -1.79 | 1.45 | -0.2140 |
| spread_widen_25bps | -1.32 | -1.10 | 1.59 | -0.1965 |
| thin_book | -1.18 | -1.59 | 1.50 | -0.1961 |
| very_thin_book | -1.43 | -2.18 | 1.43 | -1000.0000 |
| entry_spread_stress | -1.28 | -1.44 | 1.45 | -0.2243 |
| combined_market_deterioration | -1.49 | -1.96 | 1.68 | -0.2012 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8760
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0027)
- **Trend**: ranging (efficiency: 0.0084)
- **Best holdout score**: 0.0352 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9816 | -0.1478 | -1.55 | 2.36 | 22 |
| 1 | -0.1120 | -0.1609 | -2.35 | 2.42 | 21 |
| 2 | -0.1210 | 0.0352 | 6.25 | 1.89 | 55 |
| 3 | -0.1228 | -0.2410 | -1.06 | 1.84 | 6 |
| 4 | -0.1309 | -0.2320 | -3.42 | 4.21 | 9 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51667
- **Expected rows**: 51867
- **Missing rows**: 200
- **Forward-fill count**: 359
- **Forward-fill fraction**: 0.006948342268759556
- **Longest gap (seconds)**: 8700

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2184 <= 0; recent PnL -4.0007% < 0
- **Objective score**: -0.21844985530768565
- **PnL %**: -4.000656621697499
- **Trade count**: 15

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2001 <= 0; recent PnL -1.9133% < 0
- **Objective score**: -0.2001112046916462
- **PnL %**: -1.9133135870530074
- **Trade count**: 10

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1656 <= 0
- **Objective score**: -0.1656471259683948
- **PnL %**: 0.2279608289409115
- **Trade count**: 9

## Sensitivity Analysis

- **Sensitivity penalty**: 0.11538461538461539
- **Baseline score**: -0.08321728589925428
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0803, -0.0814 |
| bb_std | -0.0778, -0.0821 |
| bbp_entry_threshold | -0.0821, -0.0778 |
| rsi_length | -0.2172, -0.0779 |
| rsi_entry_threshold | -0.1017, -0.2146 |
| trend_ema_length | -0.0832, -0.0800 |
| max_atr_pct_for_entry | -0.0832, -0.0832 |
| volume_filter_window | -0.0832, -0.0832 |
| min_volume_quantile | -0.0832, -0.0832 |
| stop_loss | -0.0832, -0.0832 |
| take_profit | -0.0832, -0.0832 |
| cooldown_time | -0.1868, -0.1137 |
| total_amount_quote | -0.0832, -0.0832 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.498069770401964
- **Max CV**: 0.7811952293211335
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2654 | 0.036700728163316224 | 0.07758367191345962 | 0.05954120531681878 |
| take_profit | 0.5588 | 0.006065453065592188 | 0.04198872279472756 | 0.024106021591151886 |
| cooldown_time | 0.7812 | 6713.0 | 65055.0 | 22210.8 |
| total_amount_quote | 0.3869 | 130.681953076362 | 995.1718837179394 | 664.4190934827408 |

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
| recent_objective | > 0 | -0.21844985530768565 | FAIL |
| recent_pnl | >= 0 | -4.000656621697499 | FAIL |
| recent_trades | >= 5 | 15 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.11538461538461539 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1477739039822337 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.11538461538461539 |
| recent_28d | FAIL | score=-0.21844985530768565, pnl=-4.000656621697499, trades=15, reason=recent objective score -0.2184 <= 0; recent PnL -4.0007% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.2001112046916462, pnl=-1.9133135870530074, trades=10, reason=recent objective score -0.2001 <= 0; recent PnL -1.9133% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.1656471259683948, pnl=0.2279608289409115, trades=9, reason=recent objective score -0.1656 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.498069770401964 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51667 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2184 <= 0; recent PnL -4.0007% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2001 <= 0; recent PnL -1.9133% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1656 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51667
- **Pre-release bars**: 43802
- **Dev bars**: 35042
- **Holdout bars**: 8760
- **Recent 28d bars**: 7865
- **Recent window start**: 1774078200

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T08:48:06.020631+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 8229
- **validation_status**: validated_fail
