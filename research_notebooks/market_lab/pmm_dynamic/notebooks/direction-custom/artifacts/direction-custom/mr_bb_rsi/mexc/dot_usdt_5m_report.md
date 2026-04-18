# PMM Dynamic Optimization Report: mexc_DOT-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 00:57:12 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T00:57:12.697423+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 241 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOT-USDT
- **interval**: 5m
- **n_candles**: 51840
- **dataset_hash**: 2173295c56f9aa70680f9a8eb443783f49032da25853a92073d2cb50df19fa58
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 940.4137537771207
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 29 |
| bb_length | 147 |
| bb_std | 1.0543758681014679 |
| bbp_entry_threshold | 0.31082347700605295 |
| cooldown_time | 20820 |
| max_atr_pct_for_entry | 0.036455275882386486 |
| min_volume_quantile | 0.46582020014489106 |
| rsi_entry_threshold | 47.97820679679746 |
| rsi_length | 21 |
| stop_loss | 0.0552002594081184 |
| take_profit | 0.03860210213555218 |
| take_profit_order_type | MARKET |
| time_limit | 278318 |
| total_amount_quote | 940.4137537771207 |
| trailing_stop_activation | 0.004197090610400099 |
| trailing_stop_delta | 0.017564694150927245 |
| trend_ema_length | 299 |
| use_trend_filter | True |
| volume_filter_window | 259 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 940.4137537771207 |
| Selected | 940.4137537771207 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 10.0546
- **Net PnL (quote)**: 94.5549
- **Sharpe Ratio**: 3.0918
- **Max Drawdown %**: 2.8652
- **Profit Factor**: inf
- **Trade Count**: 54
- **Total Fees (quote)**: 12.8111
- **Maker Fees**: 6.3948
- **Taker Fees**: 6.4163
- **Fee Drag %**: 1.3623

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0672
- **PnL Component**: 0.0958
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0215
- **Fee Drag Component**: -0.0068
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 9.37 | 2.89 | 2.87 | 0.0576 |
| fees_2x | 8.69 | 2.69 | 2.87 | 0.0479 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 10.25 | 3.14 | 2.87 | 0.0690 |
| very_low_liquidity | 9.90 | 2.98 | 2.87 | 0.0661 |
| high_slippage | 8.35 | 2.59 | 2.87 | 0.0515 |
| extreme_slippage | 4.94 | 1.56 | 2.89 | 0.0194 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 9.45 | 2.59 | 3.37 | 0.0578 |
| spread_widen_25bps | 8.85 | 2.23 | 3.39 | 0.0520 |
| thin_book | 3.79 | 1.65 | 2.88 | -0.0837 |
| very_thin_book | 1.27 | 0.50 | 4.36 | -0.1854 |
| entry_spread_stress | 9.18 | 2.47 | 3.38 | 0.0553 |
| combined_market_deterioration | 5.89 | 1.86 | 3.43 | -0.0124 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0041)
- **Trend**: ranging (efficiency: 0.0066)
- **Best holdout score**: -0.2106 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9664 | -0.2106 | -3.11 | 5.42 | 16 |
| 1 | -0.1328 | -0.2308 | -1.53 | 4.57 | 5 |
| 2 | -0.1469 | -0.2215 | -1.39 | 4.57 | 7 |
| 3 | -0.1584 | -1000.0000 | -2.17 | 2.45 | 1 |
| 4 | -0.1592 | -1000.0000 | -1.55 | 2.45 | 3 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51840
- **Expected rows**: 51841
- **Missing rows**: 1
- **Forward-fill count**: 22
- **Forward-fill fraction**: 0.0004243827160493827
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.5287% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.5287207079560376
- **Trade count**: 2

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3843 <= 0; recent PnL -0.2629% < 0
- **Objective score**: -0.3842522151301897
- **PnL %**: -0.2628763895773907
- **Trade count**: 22

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -1.6270% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -1.6270493478764345
- **Trade count**: 1

## Sensitivity Analysis

- **Sensitivity penalty**: 0.125
- **Baseline score**: -0.13894720505679942
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | -0.3134, -0.1106 |
| take_profit | -0.1389, -0.1389 |
| cooldown_time | -0.1444, -0.1402 |
| total_amount_quote | -0.1381, -0.1399 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5594501455600582
- **Max CV**: 0.8865288292552298
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4561 | 0.015058279985254375 | 0.07358027902708066 | 0.04049418063935048 |
| take_profit | 0.8865 | 0.005096252700470045 | 0.042140707589686334 | 0.012745890268701338 |
| cooldown_time | 0.5871 | 1535.0 | 34222.0 | 15226.3 |
| total_amount_quote | 0.3080 | 154.37664795505378 | 852.6826330857941 | 662.928019337958 |

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
- walkforward_positive_majority: **FAIL**
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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | -2.5287207079560376 | FAIL |
| recent_trades | >= 5 | 2 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.125 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.21062724874500055 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.125 |
| recent_28d | FAIL | score=-1000.0, pnl=-2.5287207079560376, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -2.5287% < 0; recent trades 2 < 5 |
| recent_14d_info | FAIL | informational only; score=-0.3842522151301897, pnl=-0.2628763895773907, trades=22, reason=recent objective score -0.3843 <= 0; recent PnL -0.2629% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-1.6270493478764345, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -1.6270% < 0; recent trades 1 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5594501455600582 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51840 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.5287% < 0; recent trades 2 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3843 <= 0; recent PnL -0.2629% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -1.6270% < 0; recent trades 1 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | false | NOT_RUN | — | — | — | not executed |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51840
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8064
- **Recent window start**: 1774012200

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T00:57:12.697423+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 241
