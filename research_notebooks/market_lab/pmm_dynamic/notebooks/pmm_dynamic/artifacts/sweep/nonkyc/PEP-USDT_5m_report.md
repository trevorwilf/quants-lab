# PMM Dynamic Optimization Report: nonkyc_PEP-USDT_5m_sweep_v1

Generated: 2026-04-09 23:05:19 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T23:05:19.215745+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 10917 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: PEP-USDT
- **interval**: 5m
- **n_candles**: 52111
- **dataset_hash**: 9764286be81159d673232c0ace2d00b17126c3134b0636f4b3e5745a888c44c8
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 961.8438440241821
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.5751782189151993 |
| buy_n_levels | 10 |
| buy_side_weight | 0.21119537989729445 |
| buy_spread_base | 0.21723962195159877 |
| buy_spread_ratio | 1.364441103685098 |
| cooldown_time | 1538 |
| executor_refresh_time | 1085 |
| macd_fast | 20 |
| macd_signal | 11 |
| macd_slow | 22 |
| natr_length | 30 |
| sell_n_levels | 3 |
| sell_spread_base | 0.2009200182144958 |
| sell_spread_ratio | 1.3665339360782698 |
| stop_loss | 0.201649764420756 |
| take_profit | 0.019202522911256435 |
| time_limit | 167117 |
| total_amount_quote | 961.8438440241821 |
| trailing_stop_activation | 0.01584709208831658 |
| trailing_stop_delta | 0.0022661004690730153 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 961.8438440241821 |
| Selected | 961.8438440241821 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 8.3896
- **Net PnL (quote)**: 80.6948
- **Sharpe Ratio**: 1.6933
- **Max Drawdown %**: 5.0271
- **Profit Factor**: 1.728860580146161
- **Trade Count**: 572
- **Total Fees (quote)**: 20.5956
- **Maker Fees**: 7.2941
- **Taker Fees**: 13.3015
- **Fee Drag %**: 2.1413
- **TP Min-Notional Failures**: 10 :warning:
  > 10 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0216
- **PnL Component**: 0.0806
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0377
- **Fee Drag Component**: -0.0107
- **Inventory Component**: -0.0528
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0222**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.31 | 1.97 | 0.75 | 66 | -0.0038 | n/a |
| 1 | -0.04 | -0.67 | 0.21 | 52 | -0.0174 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.46 | 3.10 | 0.81 | 95 | -0.0031 | n/a |
| 4 | -0.52 | -2.72 | 1.21 | 86 | -0.0646 | n/a |
| 5 | -2.21 | -11.27 | 2.32 | 96 | -0.1515 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.82 | 4.08 | 0.73 | 376 | -0.0144 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **combined_adverse** (score: -0.0882)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 7.32 | 1.49 | 5.14 | -0.0379 |
| fees_2x | 6.25 | 1.29 | 5.26 | -0.0543 |
| latency_plus1 | 5.55 | 1.15 | 5.12 | -0.0493 |
| latency_plus2 | 5.76 | 1.30 | 4.88 | -0.0420 |
| latency_plus3 | 5.99 | 1.27 | 5.52 | -0.0464 |
| low_liquidity | 4.04 | 0.97 | 5.06 | -0.0585 |
| very_low_liquidity | 1.08 | 0.33 | 5.08 | -0.0854 |
| high_slippage | 8.04 | 1.63 | 5.06 | -0.0251 |
| extreme_slippage | 7.35 | 1.50 | 5.14 | -0.0322 |
| combined_adverse | 1.68 | 0.45 | 5.34 | -0.0882 |
| spread_widen_10bps | 9.15 | 1.81 | 5.04 | -0.0154 |
| spread_widen_25bps | 8.56 | 1.68 | 4.67 | -0.0180 |
| thin_book | 5.12 | 1.07 | 4.54 | -0.0488 |
| very_thin_book | 3.23 | 0.97 | 3.22 | -0.0323 |
| entry_spread_stress | 9.03 | 1.79 | 5.06 | -0.0166 |
| combined_market_deterioration | 4.29 | 0.85 | 5.95 | -0.0710 |
| severe_adverse | 1.88 | 0.55 | 3.84 | -0.0605 |

## Holdout Validation

- **Holdout bars**: 8809
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0099)
- **Trend**: ranging (efficiency: 0.0144)
- **Best holdout score**: -0.0075 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0549 | -0.0343 | -0.86 | 2.26 | 400 |
| 1 | -0.0029 | -0.0075 | 0.87 | 0.71 | 362 |
| 2 | -0.0034 | -0.0264 | 1.84 | 1.58 | 428 |
| 3 | -0.0044 | -0.0297 | -1.18 | 1.33 | 441 |
| 4 | -0.0046 | -0.1371 | -3.68 | 6.02 | 366 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52111
- **Expected rows**: 52112
- **Missing rows**: 1
- **Forward-fill count**: 456
- **Forward-fill fraction**: 0.008750551706933276
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1983 <= 0; recent PnL -0.2738% < 0
- **Objective score**: -0.19827548578360094
- **PnL %**: -0.27380320378070255
- **Trade count**: 34

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: -0.06208981484450652
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0748, -0.0880 |
| sell_spread_base | -0.0639, -0.0622 |
| stop_loss | -0.0655, -0.0573 |
| take_profit | -0.0621, -0.0621 |
| executor_refresh_time | -0.0621, -0.0621 |
| cooldown_time | -0.0621, -0.0432 |
| total_amount_quote | -0.1428, -0.1449 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4404128744545739
- **Max CV**: 1.264729366465531
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, total_amount_quote
- **Scattered params**: stop_loss, take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1497 | 0.2185686402188853 | 0.36947923053562126 | 0.2752726883971667 |
| buy_spread_ratio | 0.0758 | 1.2046732638388418 | 1.5321900167825824 | 1.370537899887601 |
| sell_spread_base | 0.3346 | 0.20805150778135553 | 0.5448660316608838 | 0.3150920934151896 |
| sell_spread_ratio | 0.2341 | 1.2328032198175407 | 2.2822627600090057 | 1.635991257889738 |
| buy_side_weight | 0.3057 | 0.2094264901053302 | 0.49441474271015595 | 0.2857194399251523 |
| amount_skew | 0.1835 | 1.1990846752752813 | 2.1623585692803715 | 1.4447296198338908 |
| stop_loss | 0.6570 | 0.012430445762045555 | 0.18657084514140576 | 0.09635040797353905 |
| take_profit | 1.0175 | 0.005186035518897021 | 0.09392912645091164 | 0.028868218763840697 |
| executor_refresh_time | 0.5455 | 339.0 | 1497.0 | 812.4 |
| cooldown_time | 1.2647 | 79.0 | 3248.0 | 903.4 |
| total_amount_quote | 0.0763 | 813.0692605209119 | 989.6497980620228 | 904.2054697603837 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
- **fill_participation_rate**: 0.1
- **latency_bars**: 1
- **slippage_bps**: 5.0
- **touch_through**: False
- **maker_fill_probability**: 1.0
- **refresh_close_mode**: market_close

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: PASS
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
| recent_objective | > 0 | -0.19827548578360094 | FAIL |
| recent_pnl | >= 0 | -0.27380320378070255 | FAIL |
| recent_trades | >= 5 | 34 | PASS |
| worst_stress | > -10 | -0.0882076140181334 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.034256471727262046 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=combined_adverse score=-0.0882076140181334 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.19827548578360094, pnl=-0.27380320378070255, trades=34, reason=recent objective score -0.1983 <= 0; recent PnL -0.2738% < 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4404128744545739 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52111 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1983 <= 0; recent PnL -0.2738% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52111
- **Pre-release bars**: 44047
- **Dev bars**: 35238
- **Holdout bars**: 8809
- **Recent 28d bars**: 8064
- **Recent window start**: 1773354300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T23:05:19.215745+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 10917
