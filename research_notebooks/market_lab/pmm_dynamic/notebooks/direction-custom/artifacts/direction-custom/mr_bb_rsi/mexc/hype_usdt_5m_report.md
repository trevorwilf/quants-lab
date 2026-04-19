# PMM Dynamic Optimization Report: mexc_HYPE-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 09:06:36 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T09:06:36.207197+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 2419 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: HYPE-USDT
- **interval**: 5m
- **n_candles**: 51694
- **dataset_hash**: 7dbd8e7a0a53c78a623e8f975bade6416b546c9f12cbce3963371dfc9ceb852d
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 771.6504008216178
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 24 |
| bb_length | 92 |
| bb_std | 1.0556537908953212 |
| bbp_entry_threshold | 0.17270351999115424 |
| cooldown_time | 51510 |
| max_atr_pct_for_entry | 0.05946802985997853 |
| min_volume_quantile | 0.45566314224603044 |
| rsi_entry_threshold | 42.066991037610315 |
| rsi_length | 24 |
| stop_loss | 0.07605335614516304 |
| take_profit | 0.005662104662883562 |
| take_profit_order_type | MARKET |
| time_limit | 126589 |
| total_amount_quote | 771.6504008216178 |
| trailing_stop_activation | 0.0006056136468189841 |
| trailing_stop_delta | 0.01708789164772373 |
| trend_ema_length | 78 |
| use_trend_filter | False |
| volume_filter_window | 189 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 771.6504008216178 |
| Selected | 771.6504008216178 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 35.6223
- **Net PnL (quote)**: 274.8799
- **Sharpe Ratio**: 3.8762
- **Max Drawdown %**: 6.7949
- **Profit Factor**: 43.12231137871344
- **Trade Count**: 153
- **Total Fees (quote)**: 45.1284
- **Maker Fees**: 22.5322
- **Taker Fees**: 22.5962
- **Fee Drag %**: 5.8483

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.2235
- **PnL Component**: 0.3047
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0510
- **Fee Drag Component**: -0.0292
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1324**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 4.83 | 7.03 | 1.62 | 18 | -0.0969 | n/a |
| 1 | 3.01 | 4.02 | 2.42 | 21 | -0.1089 | n/a |
| 2 | 1.90 | 3.95 | 2.05 | 20 | -0.1206 | n/a |
| 3 | 2.48 | 3.03 | 3.60 | 19 | -0.1307 | n/a |
| 4 | 6.89 | 6.18 | 2.10 | 15 | -0.0930 | n/a |
| 5 | 1.56 | 2.30 | 2.37 | 29 | -0.3365 | n/a |
| 6 | -3.59 | -4.71 | 7.18 | 6 | -0.2685 | n/a |
| 7 | 3.11 | 6.61 | 2.11 | 18 | -0.1168 | n/a |
| 8 | -1.38 | -1.55 | 4.38 | 10 | -0.4570 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 32.70 | 3.58 | 6.83 | 0.1868 |
| fees_2x | 29.77 | 3.29 | 6.86 | 0.1496 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 35.86 | 3.90 | 6.78 | 0.2039 |
| very_low_liquidity | 33.86 | 3.71 | 6.84 | 0.1028 |
| high_slippage | 28.30 | 3.16 | 6.85 | 0.1675 |
| extreme_slippage | 13.65 | 1.64 | 7.02 | 0.0363 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 25.53 | 2.84 | 7.38 | 0.1416 |
| spread_widen_25bps | -2.04 | -0.47 | 7.29 | -0.1913 |
| thin_book | 7.62 | 1.17 | 9.74 | -0.0188 |
| very_thin_book | -4.55 | -1.03 | 7.46 | -0.2302 |
| entry_spread_stress | 12.54 | 1.32 | 13.20 | -0.2432 |
| combined_market_deterioration | 12.60 | 1.49 | 7.10 | -0.1811 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0042)
- **Trend**: ranging (efficiency: 0.0173)
- **Best holdout score**: -0.0436 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.8883 | -0.2078 | -3.80 | 7.19 | 22 |
| 1 | -0.0904 | -0.1995 | -3.14 | 5.26 | 19 |
| 2 | -0.0914 | -0.2635 | -5.11 | 5.52 | 8 |
| 3 | -0.0929 | -0.2095 | -2.63 | 3.39 | 12 |
| 4 | -0.0996 | -0.0436 | 5.80 | 1.88 | 30 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51694
- **Expected rows**: 51911
- **Missing rows**: 217
- **Forward-fill count**: 274
- **Forward-fill fraction**: 0.005300421712384416
- **Longest gap (seconds)**: 26700

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3002 <= 0
- **Objective score**: -0.3001538658301986
- **PnL %**: 0.7415550840032824
- **Trade count**: 47

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3830 <= 0
- **Objective score**: -0.38295427834627466
- **PnL %**: 0.8949378623353086
- **Trade count**: 21

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4216 <= 0
- **Objective score**: -0.42158673551358133
- **PnL %**: 0.28861038299853453
- **Trade count**: 11

## Sensitivity Analysis

- **Sensitivity penalty**: 0.19230769230769232
- **Baseline score**: -0.07798106016925684
- **Sign flips**: 0
- **Collapse count**: 5
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0729, -0.0292 |
| bb_std | -0.0617, -0.1290 |
| bbp_entry_threshold | -0.0777, -0.0743 |
| rsi_length | -0.0971, -0.1039 |
| rsi_entry_threshold | -0.0908, -0.1356 |
| trend_ema_length | -0.0780, -0.0780 |
| max_atr_pct_for_entry | -0.0780, -0.0780 |
| volume_filter_window | -0.0293, -0.0706 |
| min_volume_quantile | -0.0246, -0.0846 |
| stop_loss | -0.0888, -0.1900 |
| take_profit | -0.0780, -0.0780 |
| cooldown_time | -0.2373, -0.1712 |
| total_amount_quote | -0.0771, -0.0770 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2731056191535134
- **Max CV**: 0.38146567459013186
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3815 | 0.015677371806860983 | 0.06459043344076727 | 0.041064356542156684 |
| take_profit | 0.2449 | 0.005203366338164563 | 0.010184434329306487 | 0.007166740096612842 |
| cooldown_time | 0.2286 | 28087.0 | 48154.0 | 37398.4 |
| total_amount_quote | 0.2375 | 429.3404876528119 | 999.1606066264018 | 811.0589817971899 |

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
| recent_objective | > 0 | -0.3001538658301986 | FAIL |
| recent_pnl | >= 0 | 0.7415550840032824 | PASS |
| recent_trades | >= 5 | 47 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.19230769230769232 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.20778838546568262 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.19230769230769232 |
| recent_28d | FAIL | score=-0.3001538658301986, pnl=0.7415550840032824, trades=47, reason=recent objective score -0.3002 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.38295427834627466, pnl=0.8949378623353086, trades=21, reason=recent objective score -0.3830 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.42158673551358133, pnl=0.28861038299853453, trades=11, reason=recent objective score -0.4216 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2731056191535134 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51694 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3002 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3830 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.4216 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51694
- **Pre-release bars**: 43846
- **Dev bars**: 35077
- **Holdout bars**: 8769
- **Recent 28d bars**: 7848
- **Recent window start**: 1774078200

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T09:06:36.207197+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 2419
- **validation_status**: validated_fail
