# PMM Dynamic Optimization Report: mexc_BTC-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 08:20:30 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T08:20:30.192139+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 8545 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 51649
- **dataset_hash**: a8be8eb451963ad683e759360e6addf98b84c562f7a16529c31dd0c062cd214f
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 962.0064929188572
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 25 |
| bb_length | 84 |
| bb_std | 1.7003748099329088 |
| bbp_entry_threshold | 0.3422770094882416 |
| cooldown_time | 6142 |
| max_atr_pct_for_entry | 0.014863381313889904 |
| min_volume_quantile | 0.253376361701596 |
| rsi_entry_threshold | 44.36244176758565 |
| rsi_length | 13 |
| stop_loss | 0.03972544017496369 |
| take_profit | 0.03655341452034966 |
| take_profit_order_type | LIMIT |
| time_limit | 230376 |
| total_amount_quote | 962.0064929188572 |
| trailing_stop_activation | 0.0002627960009158825 |
| trailing_stop_delta | 0.011443958595914896 |
| trend_ema_length | 299 |
| use_trend_filter | False |
| volume_filter_window | 396 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 962.0064929188572 |
| Selected | 962.0064929188572 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.4732
- **Net PnL (quote)**: -23.7927
- **Sharpe Ratio**: -0.7325
- **Max Drawdown %**: 3.9952
- **Profit Factor**: 0.47692337559743736
- **Trade Count**: 40
- **Total Fees (quote)**: 15.3829
- **Maker Fees**: 7.6923
- **Taker Fees**: 7.6906
- **Fee Drag %**: 1.5990

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1034
- **PnL Component**: -0.0250
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0300
- **Fee Drag Component**: -0.0080
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0400
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1801**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.10 | -3.73 | 2.36 | 13 | -0.1792 | n/a |
| 1 | -1.14 | -2.75 | 1.74 | 22 | -0.1401 | n/a |
| 2 | -1.14 | -7.57 | 1.14 | 6 | -0.2180 | n/a |
| 3 | -1.02 | -2.92 | 1.23 | 16 | -0.2130 | n/a |
| 4 | -1.31 | -3.27 | 2.04 | 17 | -0.1637 | n/a |
| 5 | -3.83 | -5.64 | 6.30 | 40 | -0.1351 | n/a |
| 6 | -2.11 | -7.34 | 2.27 | 11 | -0.1965 | n/a |
| 7 | -1.21 | -3.67 | 1.77 | 27 | -0.1211 | n/a |
| 8 | -1.65 | -4.01 | 2.30 | 54 | -0.0426 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -4.26 | -1.56 | 4.33 | -0.1695 |
| fees_2x | -4.63 | -1.22 | 4.64 | -0.1084 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -2.47 | -0.73 | 4.00 | -0.1034 |
| very_low_liquidity | -2.47 | -0.73 | 4.00 | -0.1034 |
| high_slippage | -1.04 | -0.34 | 3.96 | -0.0517 |
| extreme_slippage | -1.16 | -0.55 | 3.68 | -0.4346 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.36 | -0.68 | 4.09 | -0.1133 |
| spread_widen_25bps | -3.08 | -1.30 | 4.36 | -0.1812 |
| thin_book | -2.43 | -0.92 | 4.28 | -0.1737 |
| very_thin_book | 2.39 | 1.28 | 1.80 | -0.0266 |
| entry_spread_stress | -2.35 | -0.68 | 4.05 | -0.1167 |
| combined_market_deterioration | -4.05 | -2.33 | 4.61 | -0.2823 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0021)
- **Trend**: ranging (efficiency: 0.0068)
- **Best holdout score**: -0.1979 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0517 | -0.2351 | -1.14 | 1.20 | 4 |
| 1 | -0.1102 | -0.1979 | -2.28 | 2.32 | 17 |
| 2 | -0.1178 | -0.2445 | -4.59 | 4.97 | 12 |
| 3 | -0.1216 | -0.2493 | -4.12 | 4.68 | 9 |
| 4 | -0.1248 | -0.4003 | -1.12 | 1.46 | 6 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51649
- **Expected rows**: 51841
- **Missing rows**: 192
- **Forward-fill count**: 786
- **Forward-fill fraction**: 0.0152181068365312
- **Longest gap (seconds)**: 8100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0463 <= 0; recent PnL -1.9790% < 0
- **Objective score**: -0.04631702751647805
- **PnL %**: -1.97903228781936
- **Trade count**: 74

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1914 <= 0; recent PnL -1.6903% < 0
- **Objective score**: -0.19136694904850682
- **PnL %**: -1.6902982738248746
- **Trade count**: 10

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2286 <= 0; recent PnL -1.6453% < 0
- **Objective score**: -0.22862971558273937
- **PnL %**: -1.6453152437562693
- **Trade count**: 6

## Sensitivity Analysis

- **Sensitivity penalty**: 0.3076923076923077
- **Baseline score**: -0.10324735058268522
- **Sign flips**: 0
- **Collapse count**: 8
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1194, -1000.0000 |
| bb_std | -0.1754, -0.1140 |
| bbp_entry_threshold | -0.0877, -0.1035 |
| rsi_length | -0.1754, -0.0981 |
| rsi_entry_threshold | -0.1193, -0.1884 |
| trend_ema_length | -0.1068, -0.1433 |
| max_atr_pct_for_entry | -0.1032, -0.1032 |
| volume_filter_window | -0.1072, -0.1076 |
| min_volume_quantile | -0.1794, -0.1754 |
| stop_loss | -0.1103, -0.0962 |
| take_profit | -0.1032, -0.1032 |
| cooldown_time | -0.1308, -0.1887 |
| total_amount_quote | -0.1631, -0.0992 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.48467127001666677
- **Max CV**: 0.599989624191905
- **Clustered params**: take_profit, total_amount_quote
- **Scattered params**: stop_loss, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.6000 | 0.01536769423221319 | 0.07658676372385409 | 0.034349471936057904 |
| take_profit | 0.4509 | 0.006730729152973489 | 0.02421694760653317 | 0.013075359580519941 |
| cooldown_time | 0.5556 | 4665.0 | 18561.0 | 8750.8 |
| total_amount_quote | 0.3322 | 285.0356610449893 | 989.5608088674489 | 704.8964801018388 |

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
| recent_objective | > 0 | -0.04631702751647805 | FAIL |
| recent_pnl | >= 0 | -1.97903228781936 | FAIL |
| recent_trades | >= 5 | 74 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.3076923076923077 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.23513385183083998 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.3076923076923077 |
| recent_28d | FAIL | score=-0.04631702751647805, pnl=-1.97903228781936, trades=74, reason=recent objective score -0.0463 <= 0; recent PnL -1.9790% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.19136694904850682, pnl=-1.6902982738248746, trades=10, reason=recent objective score -0.1914 <= 0; recent PnL -1.6903% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.22862971558273937, pnl=-1.6453152437562693, trades=6, reason=recent objective score -0.2286 <= 0; recent PnL -1.6453% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.48467127001666677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51649 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0463 <= 0; recent PnL -1.9790% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1914 <= 0; recent PnL -1.6903% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2286 <= 0; recent PnL -1.6453% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51649
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 7873
- **Recent window start**: 1774074900

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T08:20:30.192139+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 8545
- **validation_status**: validated_fail
