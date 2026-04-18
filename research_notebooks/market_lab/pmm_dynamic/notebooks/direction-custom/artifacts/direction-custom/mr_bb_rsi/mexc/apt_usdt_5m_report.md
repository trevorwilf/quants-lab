# PMM Dynamic Optimization Report: mexc_APT-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-17 21:33:33 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-17T21:33:33.106654+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 466 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: APT-USDT
- **interval**: 5m
- **n_candles**: 51795
- **dataset_hash**: acbc5d2caba0ec4b40a5a284b3289ef7ca58dc78e0c687ae23e7b752ac14bc98
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 799.6790147780679
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 15 |
| bb_length | 93 |
| bb_std | 2.8768721587771324 |
| bbp_entry_threshold | 0.3667294641540456 |
| cooldown_time | 29129 |
| max_atr_pct_for_entry | 0.04777410193406458 |
| min_volume_quantile | 0.47294359020888865 |
| rsi_entry_threshold | 48.128824832340186 |
| rsi_length | 25 |
| stop_loss | 0.02762788846311005 |
| take_profit | 0.00751050369544075 |
| take_profit_order_type | LIMIT |
| time_limit | 78107 |
| total_amount_quote | 799.6790147780679 |
| trailing_stop_activation | 0.0005330771008937784 |
| trailing_stop_delta | 0.009652918950762184 |
| trend_ema_length | 55 |
| use_trend_filter | False |
| volume_filter_window | 97 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 799.6790147780679 |
| Selected | 799.6790147780679 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.4804
- **Net PnL (quote)**: -19.8349
- **Sharpe Ratio**: -1.3921
- **Max Drawdown %**: 5.0750
- **Profit Factor**: 0.5830070839032481
- **Trade Count**: 38
- **Total Fees (quote)**: 8.6343
- **Maker Fees**: 4.3183
- **Taker Fees**: 4.3160
- **Fee Drag %**: 1.0797

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1167
- **PnL Component**: -0.0251
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0381
- **Fee Drag Component**: -0.0054
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0480
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -3.02 | -1.70 | 5.20 | -0.1219 |
| fees_2x | -1.13 | -0.79 | 2.95 | -0.1138 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -3.22 | -1.79 | 5.07 | -0.0758 |
| very_low_liquidity | -2.22 | -3.47 | 2.64 | -0.1909 |
| high_slippage | -1.37 | -0.98 | 3.01 | -0.1142 |
| extreme_slippage | -1.08 | -1.51 | 1.30 | -0.2081 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.05 | -0.66 | 2.80 | -0.1354 |
| spread_widen_25bps | -1.27 | -3.09 | 1.67 | -0.2059 |
| thin_book | -1.65 | -1.55 | 2.85 | -0.1996 |
| very_thin_book | -2.69 | -2.34 | 2.85 | -0.2332 |
| entry_spread_stress | -1.35 | -3.34 | 1.69 | -0.2029 |
| combined_market_deterioration | -1.51 | -3.67 | 1.75 | -0.2090 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0036)
- **Trend**: ranging (efficiency: 0.0047)
- **Best holdout score**: -0.0374 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0583 | -0.1843 | -1.54 | 1.59 | 11 |
| 1 | -0.0846 | -0.1843 | -1.54 | 1.59 | 11 |
| 2 | -0.1196 | -0.0374 | 2.50 | 2.76 | 41 |
| 3 | -0.1254 | -0.2849 | -3.00 | 3.04 | 6 |
| 4 | -0.1277 | -0.2849 | -3.00 | 3.04 | 6 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51795
- **Expected rows**: 51841
- **Missing rows**: 46
- **Forward-fill count**: 58
- **Forward-fill fraction**: 0.001119799208417801
- **Longest gap (seconds)**: 8100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0535 <= 0
- **Objective score**: -0.053546735839130624
- **PnL %**: 3.942221495778051
- **Trade count**: 32

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1317 <= 0
- **Objective score**: -0.1317082964930461
- **PnL %**: 0.6387959530864139
- **Trade count**: 17

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2227 <= 0; recent PnL -2.7932% < 0
- **Objective score**: -0.22270133610062956
- **PnL %**: -2.7932202958989443
- **Trade count**: 7

## Sensitivity Analysis

- **Sensitivity penalty**: 0.125
- **Baseline score**: -0.11662699722334935
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | -0.1264, -0.0517 |
| take_profit | -0.1166, -0.1166 |
| cooldown_time | -0.2081, -0.0955 |
| total_amount_quote | -0.1130, -0.0763 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4848814717429352
- **Max CV**: 0.6766591791254801
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3963 | 0.018038744812412952 | 0.06728868640857513 | 0.04016237614063313 |
| take_profit | 0.5368 | 0.006209053394094213 | 0.03134299562903997 | 0.014017707388430504 |
| cooldown_time | 0.6767 | 644.0 | 82222.0 | 44106.5 |
| total_amount_quote | 0.3297 | 242.8934583230324 | 985.6862455661015 | 717.0260580277485 |

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
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.053546735839130624 | FAIL |
| recent_pnl | >= 0 | 3.942221495778051 | PASS |
| recent_trades | >= 5 | 32 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.125 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1842684753873223 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.125 |
| recent_28d | FAIL | score=-0.053546735839130624, pnl=3.942221495778051, trades=32, reason=recent objective score -0.0535 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.1317082964930461, pnl=0.6387959530864139, trades=17, reason=recent objective score -0.1317 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.22270133610062956, pnl=-2.7932202958989443, trades=7, reason=recent objective score -0.2227 <= 0; recent PnL -2.7932% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4848814717429352 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51795 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0535 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1317 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2227 <= 0; recent PnL -2.7932% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | false | NOT_RUN | — | — | — | not executed |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51795
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8019
- **Recent window start**: 1774025700

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-17T21:33:33.106654+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 466
