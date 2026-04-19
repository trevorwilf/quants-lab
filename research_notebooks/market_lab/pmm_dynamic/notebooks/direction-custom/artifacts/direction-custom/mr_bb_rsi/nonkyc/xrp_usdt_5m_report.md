# PMM Dynamic Optimization Report: nonkyc_XRP-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 16:28:57 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T16:28:57.140578+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 7269 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: XRP-USDT
- **interval**: 5m
- **n_candles**: 51878
- **dataset_hash**: c569951ea698d4dbdaa35e2e90a7652504c941f80a1d4e3018018bea1ee74328
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 421.6426059900675
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 14 |
| bb_length | 120 |
| bb_std | 1.5240018792883967 |
| bbp_entry_threshold | 0.10101262932439588 |
| cooldown_time | 58758 |
| max_atr_pct_for_entry | 0.016104812776039378 |
| min_volume_quantile | 0.11117825717578772 |
| rsi_entry_threshold | 44.55748060375053 |
| rsi_length | 7 |
| stop_loss | 0.020707872256001663 |
| take_profit | 0.00744103755149589 |
| take_profit_order_type | MARKET |
| time_limit | 109030 |
| total_amount_quote | 421.6426059900675 |
| trailing_stop_activation | 0.02976762564936391 |
| trailing_stop_delta | 0.018715484376319876 |
| trend_ema_length | 269 |
| use_trend_filter | True |
| volume_filter_window | 217 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 421.6426059900675 |
| Selected | 421.6426059900675 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.0232
- **Net PnL (quote)**: -8.5305
- **Sharpe Ratio**: -1.9467
- **Max Drawdown %**: 2.4063
- **Profit Factor**: 0.1624269243288367
- **Trade Count**: 4
- **Total Fees (quote)**: 2.5178
- **Maker Fees**: 0.8433
- **Taker Fees**: 1.6745
- **Fee Drag %**: 0.5971

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.2255
- **PnL Component**: -0.0204
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0180
- **Fee Drag Component**: -0.0030
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1840
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2470**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.58 | -2.23 | 1.06 | 4 | -0.5362 | n/a |
| 1 | 0.73 | 5.46 | 0.30 | 7 | -0.1703 | n/a |
| 2 | 1.57 | 6.04 | 0.57 | 6 | -0.1709 | n/a |
| 3 | -1.54 | -2.85 | 2.05 | 3 | -1000.0000 | n/a |
| 4 | -2.42 | -4.27 | 2.43 | 3 | -1000.0000 | n/a |
| 5 | -2.42 | -8.92 | 2.60 | 6 | -0.4348 | n/a |
| 6 | -1.63 | -3.56 | 2.68 | 5 | -0.2214 | n/a |
| 7 | -2.42 | -6.77 | 2.42 | 2 | -1000.0000 | n/a |
| 8 | -2.02 | -6.63 | 2.42 | 3 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.32 | -2.18 | 2.62 | -0.2317 |
| fees_2x | -2.62 | -2.39 | 2.87 | -0.2341 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -2.02 | -1.95 | 2.41 | -0.2095 |
| very_low_liquidity | -2.03 | -1.99 | 2.41 | -0.1896 |
| high_slippage | -2.12 | -2.02 | 2.47 | -0.2270 |
| extreme_slippage | -2.32 | -2.16 | 2.67 | -0.2305 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.02 | -1.95 | 2.41 | -0.2255 |
| spread_widen_25bps | -2.03 | -1.95 | 2.41 | -0.2256 |
| thin_book | -1.63 | -1.93 | 2.44 | -0.2233 |
| very_thin_book | -2.42 | -4.26 | 2.42 | -1000.0000 |
| entry_spread_stress | -2.02 | -1.95 | 2.41 | -0.2255 |
| combined_market_deterioration | -2.23 | -1.76 | 2.60 | -0.2249 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0023)
- **Trend**: ranging (efficiency: 0.0014)
- **Best holdout score**: -0.4345 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.1128 | -0.4345 | -2.42 | 2.60 | 6 |
| 1 | -0.1641 | -1000.0000 | -1.32 | 2.36 | 2 |
| 2 | -0.1651 | -1000.0000 | -1.08 | 2.14 | 3 |
| 3 | -0.1652 | -1000.0000 | -1.95 | 2.93 | 3 |
| 4 | -0.1660 | -1000.0000 | -1.08 | 2.04 | 3 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51878
- **Expected rows**: 51899
- **Missing rows**: 21
- **Forward-fill count**: 155
- **Forward-fill fraction**: 0.0029877790200084813
- **Longest gap (seconds)**: 6600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -1.9963% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -1.9963193065721114
- **Trade count**: 2

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.4155% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.4155123249338333
- **Trade count**: 2

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.5454 <= 0; recent PnL -2.0236% < 0; recent trades 4 < 5
- **Objective score**: -0.5454342144078075
- **PnL %**: -2.0235600406771783
- **Trade count**: 4

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.225500337434609
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.2160, -0.2190 |
| bb_std | -0.2255, -0.2215 |
| bbp_entry_threshold | -0.2215, -0.2255 |
| rsi_length | -0.2255, -0.2255 |
| rsi_entry_threshold | -0.2255, -0.2255 |
| trend_ema_length | -0.2255, -0.2255 |
| max_atr_pct_for_entry | -0.2255, -0.2255 |
| volume_filter_window | -0.2255, -0.2255 |
| min_volume_quantile | -0.2255, -0.2255 |
| stop_loss | -0.2292, -0.2219 |
| take_profit | -0.2247, -0.2266 |
| cooldown_time | -0.2255, -0.2149 |
| total_amount_quote | -0.2215, -0.2255 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.1506854434348351
- **Max CV**: 0.22389143102291933
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.1515 | 0.01709172111197645 | 0.027169212084405092 | 0.021282429814394762 |
| take_profit | 0.0578 | 0.011653581603021476 | 0.01359227077207531 | 0.012558743999691608 |
| cooldown_time | 0.2239 | 20490.0 | 43132.0 | 34003.7 |
| total_amount_quote | 0.1696 | 562.6769326276445 | 957.7686343523192 | 714.4626886354422 |

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
- runtime_sanity: **FAIL**
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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | -1.9963193065721114 | FAIL |
| recent_trades | >= 5 | 2 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.4345341728911239 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-1000.0, pnl=-1.9963193065721114, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -1.9963% < 0; recent trades 2 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=-2.4155123249338333, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -2.4155% < 0; recent trades 2 < 5 |
| recent_7d_info | FAIL | informational only; score=-0.5454342144078075, pnl=-2.0235600406771783, trades=4, reason=recent objective score -0.5454 <= 0; recent PnL -2.0236% < 0; recent trades 4 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.1506854434348351 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51878 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -1.9963% < 0; recent trades 2 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.4155% < 0; recent trades 2 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.5454 <= 0; recent PnL -2.0236% < 0; recent trades 4 < 5 |
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
- **run_timestamp**: 2026-04-18T16:28:57.140578+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 7269
- **validation_status**: validated_fail
