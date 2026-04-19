# PMM Dynamic Optimization Report: mexc_ATOM-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 08:02:16 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T08:02:16.928639+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 2745 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ATOM-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 7f09c9187f8f3354dafc182b6ebca9b15901cb6b1214f047b365777798f88c78
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 986.4495431219294
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 17 |
| bb_length | 88 |
| bb_std | 1.3494926333090422 |
| bbp_entry_threshold | 0.37905248093814126 |
| cooldown_time | 40553 |
| max_atr_pct_for_entry | 0.015936049465665268 |
| min_volume_quantile | 0.17412463099306177 |
| rsi_entry_threshold | 43.43648681760477 |
| rsi_length | 12 |
| stop_loss | 0.019859690183296752 |
| take_profit | 0.022596840128787567 |
| take_profit_order_type | MARKET |
| time_limit | 324797 |
| total_amount_quote | 986.4495431219294 |
| trailing_stop_activation | 0.0011777176881972652 |
| trailing_stop_delta | 0.01242350386251664 |
| trend_ema_length | 341 |
| use_trend_filter | False |
| volume_filter_window | 163 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 986.4495431219294 |
| Selected | 986.4495431219294 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.7373
- **Net PnL (quote)**: -17.1378
- **Sharpe Ratio**: -1.0589
- **Max Drawdown %**: 2.6589
- **Profit Factor**: 0.5564406658369803
- **Trade Count**: 82
- **Total Fees (quote)**: 8.2844
- **Maker Fees**: 4.1431
- **Taker Fees**: 4.1413
- **Fee Drag %**: 0.8398

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0417
- **PnL Component**: -0.0175
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0199
- **Fee Drag Component**: -0.0042
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2422**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -2.07 | -12.62 | 2.07 | 4 | -0.5246 | n/a |
| 1 | -1.76 | -4.78 | 2.07 | 8 | -0.2022 | n/a |
| 2 | -1.84 | -7.55 | 1.86 | 7 | -0.4387 | n/a |
| 3 | -1.83 | -4.43 | 2.07 | 15 | -0.1753 | n/a |
| 4 | 1.68 | 2.20 | 2.15 | 63 | -0.0398 | n/a |
| 5 | -2.07 | -12.13 | 2.09 | 6 | -0.4724 | n/a |
| 6 | -2.07 | -6.63 | 2.07 | 2 | -1000.0000 | n/a |
| 7 | -1.43 | -4.32 | 1.59 | 26 | -0.1240 | n/a |
| 8 | -1.69 | -6.19 | 2.07 | 23 | -0.1418 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.09 | -1.32 | 1.81 | -0.0522 |
| fees_2x | -1.33 | -1.61 | 1.84 | -0.0584 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -2.37 | -2.35 | 3.07 | -0.0497 |
| very_low_liquidity | -1.90 | -1.91 | 1.96 | -0.0359 |
| high_slippage | -1.45 | -1.78 | 1.87 | -0.0630 |
| extreme_slippage | -2.80 | -3.39 | 2.87 | -0.1263 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.86 | -1.16 | 2.78 | -0.0439 |
| spread_widen_25bps | -2.00 | -2.17 | 2.08 | -0.1922 |
| thin_book | -2.10 | -3.16 | 2.24 | -0.2074 |
| very_thin_book | -1.27 | -3.02 | 1.38 | -0.3476 |
| entry_spread_stress | -1.07 | -1.05 | 1.80 | -0.0507 |
| combined_market_deterioration | -2.64 | -3.75 | 2.72 | -0.1937 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0031)
- **Trend**: ranging (efficiency: 0.0174)
- **Best holdout score**: 0.0157 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0209 | -0.1348 | -2.67 | 3.91 | 31 |
| 1 | 0.0001 | -0.2033 | -3.49 | 5.47 | 19 |
| 2 | -0.0031 | 0.0157 | 4.26 | 2.31 | 73 |
| 3 | -0.0065 | -0.2084 | -2.33 | 3.56 | 11 |
| 4 | -0.0175 | 0.0020 | 2.63 | 2.09 | 62 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 11
- **Forward-fill fraction**: 0.00021218726490615535
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0892 <= 0; recent PnL -1.5787% < 0
- **Objective score**: -0.08919471150690245
- **PnL %**: -1.5787465289389413
- **Trade count**: 36

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2611 <= 0; recent PnL -1.6059% < 0
- **Objective score**: -0.2611301701881724
- **PnL %**: -1.605891207829176
- **Trade count**: 14

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2872 <= 0
- **Objective score**: -0.28716312707486535
- **PnL %**: 0.6136120284579262
- **Trade count**: 26

## Sensitivity Analysis

- **Sensitivity penalty**: 0.38461538461538464
- **Baseline score**: -0.04171158465104224
- **Sign flips**: 0
- **Collapse count**: 10
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1173, -0.0756 |
| bb_std | -0.1240, -0.0618 |
| bbp_entry_threshold | -0.0294, -0.1173 |
| rsi_length | -0.0412, -0.1244 |
| rsi_entry_threshold | -0.1306, -0.0976 |
| trend_ema_length | -0.0429, -0.3978 |
| max_atr_pct_for_entry | -0.0417, -0.0417 |
| volume_filter_window | -0.0417, -0.0417 |
| min_volume_quantile | -0.0417, -0.0417 |
| stop_loss | -0.0513, -0.0356 |
| take_profit | -0.0417, -0.0417 |
| cooldown_time | -0.0534, -0.0786 |
| total_amount_quote | -0.0557, -0.1831 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.32308762807686786
- **Max CV**: 0.5600829886413422
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2028 | 0.03234651397063959 | 0.0753443688318802 | 0.06152343908438061 |
| take_profit | 0.3815 | 0.005415845028872986 | 0.012123148533875363 | 0.008034644327749271 |
| cooldown_time | 0.5601 | 4956.0 | 29052.0 | 14738.4 |
| total_amount_quote | 0.1479 | 621.5306049814188 | 963.4138706496959 | 818.2122056781387 |

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
| recent_objective | > 0 | -0.08919471150690245 | FAIL |
| recent_pnl | >= 0 | -1.5787465289389413 | FAIL |
| recent_trades | >= 5 | 36 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.38461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1347665750607646 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.38461538461538464 |
| recent_28d | FAIL | score=-0.08919471150690245, pnl=-1.5787465289389413, trades=36, reason=recent objective score -0.0892 <= 0; recent PnL -1.5787% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.2611301701881724, pnl=-1.605891207829176, trades=14, reason=recent objective score -0.2611 <= 0; recent PnL -1.6059% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.28716312707486535, pnl=0.6136120284579262, trades=26, reason=recent objective score -0.2872 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.32308762807686786 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0892 <= 0; recent PnL -1.5787% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2611 <= 0; recent PnL -1.6059% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2872 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51841
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065
- **Recent window start**: 1774011900

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T08:02:16.928639+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 2745
- **validation_status**: validated_fail
