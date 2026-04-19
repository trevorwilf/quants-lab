# PMM Dynamic Optimization Report: nonkyc_NKYC-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 14:42:41 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T14:42:41.687934+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 5689 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: NKYC-USDT
- **interval**: 5m
- **n_candles**: 51878
- **dataset_hash**: f6bc756d2fa03e076bd757a31447c2705a471bf5ab90c48f7492d4f30ba19f26
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 979.578548879453
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 22 |
| bb_length | 147 |
| bb_std | 2.2771849344791626 |
| bbp_entry_threshold | 0.14372737162552973 |
| cooldown_time | 22464 |
| max_atr_pct_for_entry | 0.04622861584509432 |
| min_volume_quantile | 0.009643801133912592 |
| rsi_entry_threshold | 44.23147014809132 |
| rsi_length | 12 |
| stop_loss | 0.02796172801115416 |
| take_profit | 0.008488689896368092 |
| take_profit_order_type | LIMIT |
| time_limit | 314151 |
| total_amount_quote | 979.578548879453 |
| trailing_stop_activation | 0.02569740315710059 |
| trailing_stop_delta | 0.0032971322151970793 |
| trend_ema_length | 307 |
| use_trend_filter | True |
| volume_filter_window | 185 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 979.578548879453 |
| Selected | 979.578548879453 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 8.5845
- **Net PnL (quote)**: 84.0916
- **Sharpe Ratio**: 2.7765
- **Max Drawdown %**: 2.5456
- **Profit Factor**: 177.9889220354982
- **Trade Count**: 290
- **Total Fees (quote)**: 28.2721
- **Maker Fees**: 28.2322
- **Taker Fees**: 0.0399
- **Fee Drag %**: 2.8861
- **TP Min-Notional Failures**: 742 :warning:
  > 742 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0472
- **PnL Component**: 0.0824
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0191
- **Fee Drag Component**: -0.0144
- **Inventory Component**: -0.0013
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1052**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 1.25 | 3.24 | 1.23 | 42 | -0.0313 | n/a |
| 1 | -0.02 | -0.36 | 0.15 | 8 | -0.5311 | n/a |
| 2 | -0.05 | -0.16 | 1.12 | 35 | -0.0718 | n/a |
| 3 | 1.27 | 5.18 | 1.09 | 55 | 0.0010 | n/a |
| 4 | 1.32 | 3.97 | 1.64 | 51 | -0.0051 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.64 | 2.02 | 1.08 | 23 | -0.1109 | n/a |
| 8 | -2.62 | -12.44 | 2.62 | 35 | -0.3634 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 7.14 | 2.33 | 2.58 | 0.0263 |
| fees_2x | 5.70 | 1.88 | 2.62 | 0.0052 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 2.87 | 1.05 | 3.45 | -0.0652 |
| very_low_liquidity | -2.09 | -1.89 | 2.47 | -0.3199 |
| high_slippage | 8.58 | 2.78 | 2.55 | 0.0471 |
| extreme_slippage | 8.58 | 2.78 | 2.55 | 0.0471 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 8.59 | 2.74 | 2.58 | 0.0466 |
| spread_widen_25bps | 8.58 | 2.67 | 2.62 | 0.0448 |
| thin_book | -2.05 | -1.86 | 2.49 | -0.3907 |
| very_thin_book | 0.21 | 1.06 | 0.14 | -0.1672 |
| entry_spread_stress | 8.58 | 2.70 | 2.59 | 0.0450 |
| combined_market_deterioration | 1.83 | 0.82 | 3.30 | -0.0227 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0024)
- **Trend**: ranging (efficiency: 0.0014)
- **Best holdout score**: -0.0506 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9764 | -0.1108 | 0.64 | 1.08 | 23 |
| 1 | -0.0398 | -0.5339 | -1.97 | 2.21 | 12 |
| 2 | -0.0408 | -0.0506 | 1.38 | 1.63 | 39 |
| 3 | -0.0427 | -0.4932 | -1.50 | 1.76 | 7 |
| 4 | -0.0428 | -0.5667 | -2.02 | 2.02 | 5 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51878
- **Expected rows**: 51899
- **Missing rows**: 21
- **Forward-fill count**: 55
- **Forward-fill fraction**: 0.001060179652261074
- **Longest gap (seconds)**: 6600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3424 <= 0; recent PnL -2.6163% < 0
- **Objective score**: -0.34243703090868965
- **PnL %**: -2.6162901883018335
- **Trade count**: 35

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4259 <= 0; recent PnL -1.7109% < 0
- **Objective score**: -0.42593482218633244
- **PnL %**: -1.7109350763930231
- **Trade count**: 19

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07692307692307693
- **Baseline score**: -0.18706330211590283
- **Sign flips**: 2
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | 0.0303, -0.1010 |
| bb_std | -0.0401, -0.1684 |
| bbp_entry_threshold | -0.1805, -0.2085 |
| rsi_length | -0.1871, -0.1871 |
| rsi_entry_threshold | -0.2117, -0.0631 |
| trend_ema_length | -0.1752, 0.0344 |
| max_atr_pct_for_entry | -0.1871, -0.1871 |
| volume_filter_window | -0.1871, -0.1871 |
| min_volume_quantile | -0.1871, -0.1871 |
| stop_loss | -0.1871, -0.1870 |
| take_profit | -0.1714, -0.2030 |
| cooldown_time | -0.1871, -0.1871 |
| total_amount_quote | -0.1927, -0.1863 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.12355863006776018
- **Max CV**: 0.25750048644482554
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.0626 | 0.016045384635846382 | 0.019048529861003284 | 0.01725358188575727 |
| take_profit | 0.1277 | 0.005058355276671314 | 0.007188370597352984 | 0.005701862393240567 |
| cooldown_time | 0.2575 | 26995.0 | 63666.0 | 41345.7 |
| total_amount_quote | 0.0465 | 850.0912589511962 | 974.2248336044112 | 904.3401333333984 |

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
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.34243703090868965 | FAIL |
| recent_pnl | >= 0 | -2.6162901883018335 | FAIL |
| recent_trades | >= 5 | 35 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.07692307692307693 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.11081090891333864 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.07692307692307693 |
| recent_28d | FAIL | score=-0.34243703090868965, pnl=-2.6162901883018335, trades=35, reason=recent objective score -0.3424 <= 0; recent PnL -2.6163% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.42593482218633244, pnl=-1.7109350763930231, trades=19, reason=recent objective score -0.4259 <= 0; recent PnL -1.7109% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.12355863006776018 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51878 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3424 <= 0; recent PnL -2.6163% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.4259 <= 0; recent PnL -1.7109% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51878
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8044
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T14:42:41.687934+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 5689
- **validation_status**: validated_fail
