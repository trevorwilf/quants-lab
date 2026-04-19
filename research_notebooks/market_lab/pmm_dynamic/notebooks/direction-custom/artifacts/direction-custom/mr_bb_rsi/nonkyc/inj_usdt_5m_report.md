# PMM Dynamic Optimization Report: nonkyc_INJ-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 14:07:41 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T14:07:41.892027+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 567 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: INJ-USDT
- **interval**: 5m
- **n_candles**: 51864
- **dataset_hash**: c6da32d8d996c89190b3c767153dbd57a1c1971aeac2226680e148b48c98b603
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 818.4381067945666
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 20 |
| bb_length | 167 |
| bb_std | 1.0207484890119505 |
| bbp_entry_threshold | 0.15278203360229314 |
| cooldown_time | 55304 |
| max_atr_pct_for_entry | 0.018971397589368257 |
| min_volume_quantile | 0.2081849239483995 |
| rsi_entry_threshold | 31.689287689226077 |
| rsi_length | 21 |
| stop_loss | 0.01762333673385864 |
| take_profit | 0.029777235401594368 |
| take_profit_order_type | MARKET |
| time_limit | 70183 |
| total_amount_quote | 818.4381067945666 |
| trailing_stop_activation | 0.004395030331522496 |
| trailing_stop_delta | 0.015869294728630724 |
| trend_ema_length | 379 |
| use_trend_filter | True |
| volume_filter_window | 547 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 818.4381067945666 |
| Selected | 818.4381067945666 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0662
- **Net PnL (quote)**: -8.7266
- **Sharpe Ratio**: -0.3692
- **Max Drawdown %**: 2.7213
- **Profit Factor**: 0.796874938334596
- **Trade Count**: 250
- **Total Fees (quote)**: 29.7326
- **Maker Fees**: 10.6075
- **Taker Fees**: 19.1251
- **Fee Drag %**: 3.6328

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0495
- **PnL Component**: -0.0107
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0204
- **Fee Drag Component**: -0.0182
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0894**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.03 | -0.01 | 2.07 | 37 | -0.0721 | n/a |
| 1 | 0.16 | 2.03 | 0.41 | 54 | -0.0030 | n/a |
| 2 | 1.09 | 2.22 | 0.89 | 70 | -0.0100 | n/a |
| 3 | -1.91 | -9.27 | 2.11 | 53 | -0.0602 | n/a |
| 4 | -1.92 | -7.84 | 2.16 | 104 | -0.0605 | n/a |
| 5 | -2.02 | -17.91 | 2.03 | 29 | -0.3285 | n/a |
| 6 | -1.04 | -3.56 | 1.37 | 157 | -0.0949 | n/a |
| 7 | -1.97 | -10.34 | 2.14 | 156 | -0.1066 | n/a |
| 8 | -1.09 | -2.60 | 1.83 | 67 | -0.3184 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.09 | -3.12 | 1.13 | -0.2529 |
| fees_2x | -1.25 | -3.42 | 1.25 | -0.2701 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.52 | -2.78 | 1.56 | -0.2467 |
| very_low_liquidity | -1.82 | -4.80 | 1.83 | -0.2080 |
| high_slippage | -1.10 | -2.30 | 1.54 | -0.2220 |
| extreme_slippage | -1.09 | -3.07 | 1.14 | -0.2441 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.12 | -2.69 | 2.21 | -0.4103 |
| spread_widen_25bps | -2.12 | -2.73 | 2.18 | -0.4100 |
| thin_book | -1.72 | -4.76 | 1.72 | -0.3832 |
| very_thin_book | -1.85 | -1.92 | 2.52 | -0.5793 |
| entry_spread_stress | -2.12 | -2.70 | 2.20 | -0.4102 |
| combined_market_deterioration | -2.32 | -3.41 | 2.33 | -0.4120 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0020)
- **Trend**: ranging (efficiency: 0.0030)
- **Best holdout score**: -0.0265 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0247 | -0.1891 | -1.14 | 2.85 | 336 |
| 1 | -0.0201 | -0.3692 | -2.25 | 2.34 | 11 |
| 2 | -0.0205 | -0.0450 | -1.56 | 2.61 | 117 |
| 3 | -0.0206 | -0.0265 | -0.52 | 1.54 | 99 |
| 4 | -0.0207 | -0.2273 | -1.62 | 1.97 | 36 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51864
- **Expected rows**: 51899
- **Missing rows**: 35
- **Forward-fill count**: 2496
- **Forward-fill fraction**: 0.04812586765386395
- **Longest gap (seconds)**: 2400

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0343 <= 0; recent PnL -1.0068% < 0
- **Objective score**: -0.03434949737206958
- **PnL %**: -1.0067670762352714
- **Trade count**: 118

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2000 <= 0; recent PnL -2.1080% < 0
- **Objective score**: -0.200022338755809
- **PnL %**: -2.1080054907686465
- **Trade count**: 28

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2584 <= 0
- **Objective score**: -0.25842344404924034
- **PnL %**: 0.10397478175485257
- **Trade count**: 114

## Sensitivity Analysis

- **Sensitivity penalty**: 0.3076923076923077
- **Baseline score**: -0.08301988431590472
- **Sign flips**: 0
- **Collapse count**: 8
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0833, -0.4014 |
| bb_std | -0.0798, -0.4014 |
| bbp_entry_threshold | -0.4014, -0.0830 |
| rsi_length | -0.0611, -0.2104 |
| rsi_entry_threshold | -0.2104, -0.2329 |
| trend_ema_length | -0.1152, -0.0877 |
| max_atr_pct_for_entry | -0.0830, -0.0830 |
| volume_filter_window | -0.0830, -0.0830 |
| min_volume_quantile | -0.0830, -0.0836 |
| stop_loss | -0.1976, -0.0730 |
| take_profit | -0.0830, -0.0830 |
| cooldown_time | -0.0830, -0.0830 |
| total_amount_quote | -0.2322, -0.0805 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.20479897939366423
- **Max CV**: 0.35958575890447
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2400 | 0.039248063510737924 | 0.07954088973857773 | 0.05616576014266926 |
| take_profit | 0.1639 | 0.005262159772443734 | 0.008323856147732454 | 0.006820969506486996 |
| cooldown_time | 0.3596 | 2593.0 | 29592.0 | 18894.0 |
| total_amount_quote | 0.0556 | 825.0230438627096 | 976.1334836067126 | 923.2341335401509 |

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
| recent_objective | > 0 | -0.03434949737206958 | FAIL |
| recent_pnl | >= 0 | -1.0067670762352714 | FAIL |
| recent_trades | >= 5 | 118 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.3076923076923077 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1891382022944769 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.3076923076923077 |
| recent_28d | FAIL | score=-0.03434949737206958, pnl=-1.0067670762352714, trades=118, reason=recent objective score -0.0343 <= 0; recent PnL -1.0068% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.200022338755809, pnl=-2.1080054907686465, trades=28, reason=recent objective score -0.2000 <= 0; recent PnL -2.1080% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.25842344404924034, pnl=0.10397478175485257, trades=114, reason=recent objective score -0.2584 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.20479897939366423 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51864 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0343 <= 0; recent PnL -1.0068% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2000 <= 0; recent PnL -2.1080% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2584 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51864
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8030
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T14:07:41.892027+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 567
- **validation_status**: validated_fail
