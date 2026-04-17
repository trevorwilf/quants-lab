# PMM Dynamic Optimization Report: nonkyc_POL-USDT_5m_sweep_v1

Generated: 2026-04-09 23:31:19 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T23:31:19.834609+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 11138 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: POL-USDT
- **interval**: 5m
- **n_candles**: 52112
- **dataset_hash**: a3e865dc1ac1c8be3eda59e7b4ec76605187cf69ddd7768027e5fdbf676e9d2b
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 936.9801629471617
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.0435602000497 |
| buy_n_levels | 6 |
| buy_side_weight | 0.257902384878872 |
| buy_spread_base | 3.022376237010973 |
| buy_spread_ratio | 2.2806741106228134 |
| cooldown_time | 5626 |
| executor_refresh_time | 13738 |
| macd_fast | 28 |
| macd_signal | 11 |
| macd_slow | 61 |
| natr_length | 24 |
| sell_n_levels | 10 |
| sell_spread_base | 5.69793516916606 |
| sell_spread_ratio | 1.6765004728428432 |
| stop_loss | 0.023002515066573647 |
| take_profit | 0.005237888148176431 |
| time_limit | 14847 |
| total_amount_quote | 936.9801629471617 |
| trailing_stop_activation | 0.0664182058858205 |
| trailing_stop_delta | 0.012884536007082713 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 936.9801629471617 |
| Selected | 936.9801629471617 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.5649
- **Net PnL (quote)**: -14.6626
- **Sharpe Ratio**: -5.6309
- **Max Drawdown %**: 1.5734
- **Profit Factor**: 0.4731172048339819
- **Trade Count**: 596
- **Total Fees (quote)**: 13.2961
- **Maker Fees**: 10.3870
- **Taker Fees**: 2.9091
- **Fee Drag %**: 1.4190
- **TP Min-Notional Failures**: 8287 :warning:
  > 8287 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0380
- **PnL Component**: -0.0158
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0118
- **Fee Drag Component**: -0.0071
- **Inventory Component**: -0.0033
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0090**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.19 | -6.53 | 0.27 | 63 | -0.0062 | n/a |
| 1 | -0.29 | -10.03 | 0.29 | 50 | -0.0073 | n/a |
| 2 | -0.08 | -7.18 | 0.10 | 47 | -0.0155 | n/a |
| 3 | -0.10 | -5.28 | 0.16 | 52 | -0.0043 | n/a |
| 4 | -0.26 | -5.03 | 0.40 | 86 | -0.0084 | n/a |
| 5 | -0.25 | -6.58 | 0.28 | 82 | -0.0071 | n/a |
| 6 | -0.19 | -6.53 | 0.27 | 90 | -0.0096 | n/a |
| 7 | -0.14 | -7.30 | 0.18 | 74 | -0.0083 | n/a |
| 8 | -0.48 | -8.01 | 0.49 | 78 | -0.0827 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1088)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.27 | -8.05 | 2.28 | -0.0541 |
| fees_2x | -2.98 | -10.34 | 2.99 | -0.0702 |
| latency_plus1 | -1.57 | -5.65 | 1.58 | -0.0380 |
| latency_plus2 | -1.57 | -5.64 | 1.58 | -0.0380 |
| latency_plus3 | -1.58 | -5.67 | 1.58 | -0.0382 |
| low_liquidity | -2.53 | -6.68 | 2.55 | -0.0572 |
| very_low_liquidity | -2.77 | -5.93 | 2.79 | -0.0727 |
| high_slippage | -1.64 | -5.89 | 1.65 | -0.0393 |
| extreme_slippage | -1.80 | -6.40 | 1.80 | -0.0421 |
| combined_adverse | -3.41 | -8.89 | 3.42 | -0.0767 |
| spread_widen_10bps | -1.98 | -5.75 | 2.05 | -0.0457 |
| spread_widen_25bps | -3.16 | -8.08 | 3.18 | -0.0675 |
| thin_book | -2.93 | -7.91 | 2.93 | -0.0609 |
| very_thin_book | -2.76 | -10.17 | 2.77 | -0.0552 |
| entry_spread_stress | -2.70 | -6.33 | 2.77 | -0.0598 |
| combined_market_deterioration | -3.31 | -11.09 | 3.31 | -0.0711 |
| severe_adverse | -4.56 | -13.74 | 4.56 | -0.1088 |

## Holdout Validation

- **Holdout bars**: 8809
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0030)
- **Trend**: ranging (efficiency: 0.0035)
- **Best holdout score**: -0.0105 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0734 | -0.0105 | -0.30 | 0.35 | 167 |
| 1 | -0.0054 | -0.0179 | -0.64 | 0.67 | 164 |
| 2 | -0.0055 | -0.0471 | -1.99 | 2.16 | 542 |
| 3 | -0.0059 | -0.0282 | -0.89 | 1.05 | 372 |
| 4 | -0.0061 | -0.0295 | -0.92 | 1.11 | 394 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52112
- **Expected rows**: 52112
- **Missing rows**: 0
- **Forward-fill count**: 188
- **Forward-fill fraction**: 0.0036076143690512742
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0944 <= 0; recent PnL -0.8508% < 0
- **Objective score**: -0.09437095549313185
- **PnL %**: -0.8507557753377625
- **Trade count**: 135

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0878 <= 0; recent PnL -0.5703% < 0
- **Objective score**: -0.08779732997303097
- **PnL %**: -0.5702658861631553
- **Trade count**: 62

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1213 <= 0; recent PnL -0.2452% < 0
- **Objective score**: -0.12131641073384772
- **PnL %**: -0.2451876775836423
- **Trade count**: 31

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: -0.059046411576735784
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0681, -0.0857 |
| sell_spread_base | -0.0796, -0.0809 |
| stop_loss | -0.0692, -0.0951 |
| take_profit | -0.0709, -0.0917 |
| executor_refresh_time | -0.0779, -0.0655 |
| cooldown_time | -0.0672, -0.0744 |
| total_amount_quote | -0.0703, -0.0589 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2276920580439656
- **Max CV**: 0.4988265966968346
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1326 | 1.867792940913694 | 3.16269046675563 | 2.704911477069355 |
| buy_spread_ratio | 0.0634 | 2.18952288798883 | 2.7316490787595518 | 2.498467976804 |
| sell_spread_base | 0.4988 | 0.8625285452500482 | 4.694389598771338 | 2.5005966122122087 |
| sell_spread_ratio | 0.3247 | 1.2125880410229752 | 2.9308973810104195 | 1.8815890929280559 |
| buy_side_weight | 0.2207 | 0.20963205656432576 | 0.37535537953349796 | 0.24574120221582718 |
| amount_skew | 0.0762 | 2.6753413198291467 | 3.3103155997074465 | 2.908824930709307 |
| stop_loss | 0.4045 | 0.010005863067453283 | 0.03485252317281622 | 0.019881787698423668 |
| take_profit | 0.0813 | 0.005127076666384909 | 0.006433792004863848 | 0.005603476276833387 |
| executor_refresh_time | 0.1736 | 8966.0 | 14343.0 | 11923.1 |
| cooldown_time | 0.4302 | 889.0 | 6332.0 | 4456.2 |
| total_amount_quote | 0.0986 | 693.6414026359595 | 967.4717383567444 | 883.9665416303744 |

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
| recent_objective | > 0 | -0.09437095549313185 | FAIL |
| recent_pnl | >= 0 | -0.8507557753377625 | FAIL |
| recent_trades | >= 5 | 135 | PASS |
| worst_stress | > -10 | -0.10876303086006081 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.01052849265253119 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.10876303086006081 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.09437095549313185, pnl=-0.8507557753377625, trades=135, reason=recent objective score -0.0944 <= 0; recent PnL -0.8508% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.08779732997303097, pnl=-0.5702658861631553, trades=62, reason=recent objective score -0.0878 <= 0; recent PnL -0.5703% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.12131641073384772, pnl=-0.2451876775836423, trades=31, reason=recent objective score -0.1213 <= 0; recent PnL -0.2452% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2276920580439656 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52112 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0944 <= 0; recent PnL -0.8508% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0878 <= 0; recent PnL -0.5703% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1213 <= 0; recent PnL -0.2452% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52112
- **Pre-release bars**: 44047
- **Dev bars**: 35238
- **Holdout bars**: 8809
- **Recent 28d bars**: 8065
- **Recent window start**: 1773354300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T23:31:19.834609+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 11138
