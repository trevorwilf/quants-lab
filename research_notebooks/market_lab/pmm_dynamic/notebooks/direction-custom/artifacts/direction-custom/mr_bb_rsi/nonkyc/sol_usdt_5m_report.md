# PMM Dynamic Optimization Report: nonkyc_SOL-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 15:42:05 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T15:42:05.780656+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 2031 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: SOL-USDT
- **interval**: 5m
- **n_candles**: 51879
- **dataset_hash**: 5ff756b126cd986df7e573f2a7541541250e8380b6497eef5f839a9932517670
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 180.67390934818786
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 15 |
| bb_length | 96 |
| bb_std | 1.0295637901875994 |
| bbp_entry_threshold | 0.16195814236205686 |
| cooldown_time | 58177 |
| max_atr_pct_for_entry | 0.022039605580865745 |
| min_volume_quantile | 0.5713116950247239 |
| rsi_entry_threshold | 30.300443491138147 |
| rsi_length | 22 |
| stop_loss | 0.028797146420872652 |
| take_profit | 0.005769392544614937 |
| take_profit_order_type | LIMIT |
| time_limit | 135152 |
| total_amount_quote | 180.67390934818786 |
| trailing_stop_activation | 0.024314061434160535 |
| trailing_stop_delta | 0.009884874172207582 |
| trend_ema_length | 80 |
| use_trend_filter | False |
| volume_filter_window | 465 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 180.67390934818786 |
| Selected | 180.67390934818786 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0615
- **Net PnL (quote)**: -1.9179
- **Sharpe Ratio**: -0.4429
- **Max Drawdown %**: 3.6582
- **Profit Factor**: 0.6702799720760749
- **Trade Count**: 8
- **Total Fees (quote)**: 2.8851
- **Maker Fees**: 2.5343
- **Taker Fees**: 0.3508
- **Fee Drag %**: 1.5968
- **TP Min-Notional Failures**: 4 :warning:
  > 4 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.2142
- **PnL Component**: -0.0107
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0274
- **Fee Drag Component**: -0.0080
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1680
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1850**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -2.57 | -4.98 | 3.40 | 4 | -0.2404 | n/a |
| 1 | 2.15 | 4.24 | 2.07 | 7 | -0.1732 | n/a |
| 2 | 3.01 | 7.89 | 0.92 | 9 | -0.1498 | n/a |
| 3 | -2.84 | -7.90 | 3.21 | 2 | -1000.0000 | n/a |
| 4 | 3.28 | 5.10 | 1.63 | 10 | -0.1499 | n/a |
| 5 | -2.84 | -5.38 | 3.47 | 3 | -1000.0000 | n/a |
| 6 | -3.22 | -11.76 | 3.22 | 2 | -1000.0000 | n/a |
| 7 | -3.28 | -6.92 | 3.66 | 5 | -0.4966 | n/a |
| 8 | -3.22 | -7.71 | 3.23 | 2 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.86 | -0.80 | 3.97 | -0.2287 |
| fees_2x | -2.66 | -1.14 | 4.28 | -0.2432 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.06 | -0.44 | 3.66 | -0.2142 |
| very_low_liquidity | -1.19 | -0.23 | 7.06 | -0.1817 |
| high_slippage | -1.11 | -0.46 | 3.71 | -0.2151 |
| extreme_slippage | -1.21 | -0.51 | 3.80 | -0.2168 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.06 | -0.44 | 3.61 | -0.2139 |
| spread_widen_25bps | -1.06 | -0.40 | 3.54 | -0.2134 |
| thin_book | -2.47 | -1.38 | 3.22 | -0.2366 |
| very_thin_book | -2.84 | -1.28 | 3.46 | -1000.0000 |
| entry_spread_stress | -1.06 | -0.44 | 3.59 | -0.2138 |
| combined_market_deterioration | -2.74 | -1.34 | 4.26 | -0.2473 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8767
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0028)
- **Trend**: ranging (efficiency: 0.0071)
- **Best holdout score**: -0.2298 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.1071 | -0.2298 | -2.09 | 3.20 | 5 |
| 1 | -0.1515 | -1000.0000 | -2.07 | 2.86 | 2 |
| 2 | -0.1525 | -0.2462 | -3.50 | 4.07 | 6 |
| 3 | -0.1526 | -1000.0000 | -4.15 | 5.19 | 2 |
| 4 | -0.1532 | -1000.0000 | -3.02 | 4.57 | 1 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51879
- **Expected rows**: 51901
- **Missing rows**: 22
- **Forward-fill count**: 109
- **Forward-fill fraction**: 0.00210104281115673
- **Longest gap (seconds)**: 6600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2304 <= 0; recent PnL -2.0950% < 0
- **Objective score**: -0.23041827819860944
- **PnL %**: -2.0949830520553285
- **Trade count**: 5

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.6049% < 0; recent trades 3 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.6049076572360215
- **Trade count**: 3

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.0889% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.0889194039780103
- **Trade count**: 1

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.2627189697873634
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.2627, -0.2627 |
| bb_std | -0.2627, -0.2627 |
| bbp_entry_threshold | -0.2627, -0.2627 |
| rsi_length | -0.2291, -0.2527 |
| rsi_entry_threshold | -0.2038, -0.2365 |
| trend_ema_length | -0.2627, -0.2627 |
| max_atr_pct_for_entry | -0.2627, -0.2627 |
| volume_filter_window | -0.2627, -0.2627 |
| min_volume_quantile | -0.2627, -0.2627 |
| stop_loss | -0.2176, -0.2455 |
| take_profit | -0.2582, -0.2171 |
| cooldown_time | -0.1837, -0.2531 |
| total_amount_quote | -0.2628, -0.2627 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.24464716376810935
- **Max CV**: 0.4181886333862579
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4182 | 0.017314038178867 | 0.07941392990506625 | 0.05071709554215213 |
| take_profit | 0.2538 | 0.005123187168711366 | 0.011874428222820275 | 0.009911187093228867 |
| cooldown_time | 0.1125 | 57129.0 | 84742.0 | 74770.2 |
| total_amount_quote | 0.1941 | 536.5931854616521 | 983.5830283543534 | 818.5946279165739 |

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
| recent_objective | > 0 | -0.23041827819860944 | FAIL |
| recent_pnl | >= 0 | -2.0949830520553285 | FAIL |
| recent_trades | >= 5 | 5 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.22977269287556915 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.23041827819860944, pnl=-2.0949830520553285, trades=5, reason=recent objective score -0.2304 <= 0; recent PnL -2.0950% < 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=-2.6049076572360215, trades=3, reason=recent objective score -1000.0000 <= 0; recent PnL -2.6049% < 0; recent trades 3 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-2.0889194039780103, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -2.0889% < 0; recent trades 1 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.24464716376810935 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51879 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2304 <= 0; recent PnL -2.0950% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.6049% < 0; recent trades 3 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.0889% < 0; recent trades 1 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51879
- **Pre-release bars**: 43836
- **Dev bars**: 35069
- **Holdout bars**: 8767
- **Recent 28d bars**: 8043
- **Recent window start**: 1774091100

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T15:42:05.780656+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 2031
- **validation_status**: validated_fail
