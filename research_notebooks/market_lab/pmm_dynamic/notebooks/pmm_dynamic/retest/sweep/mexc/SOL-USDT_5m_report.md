# PMM Dynamic Optimization Report: mexc_SOL-USDT_5m_retest_20260408

Generated: 2026-04-08 10:16:58 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T10:16:58.196623+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 11994 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SOL-USDT
- **interval**: 5m
- **n_candles**: 51843
- **dataset_hash**: 9b493adb212ca8c0c1c6e569762f5410a33737216dab788e7ba153e09d8e0892
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 699.0820445795559
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.924364727128833 |
| buy_n_levels | 8 |
| buy_side_weight | 0.3788387624159054 |
| buy_spread_base | 2.2513602984190713 |
| buy_spread_ratio | 2.7867000155322517 |
| cooldown_time | 3363 |
| executor_refresh_time | 10963 |
| macd_fast | 18 |
| macd_signal | 21 |
| macd_slow | 20 |
| natr_length | 20 |
| sell_n_levels | 4 |
| sell_spread_base | 3.7039078072683296 |
| sell_spread_ratio | 2.3425417048145256 |
| stop_loss | 0.013260023395268205 |
| take_profit | 0.005241226968465564 |
| time_limit | 111213 |
| total_amount_quote | 699.0820445795559 |
| trailing_stop_activation | 0.005789198012309517 |
| trailing_stop_delta | 0.0016259103083000185 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 699.0820445795559 |
| Selected | 699.0820445795559 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.7215
- **Net PnL (quote)**: -12.0345
- **Sharpe Ratio**: -2.5106
- **Max Drawdown %**: 2.3749
- **Profit Factor**: 0.9666898657720346
- **Trade Count**: 1150
- **Total Fees (quote)**: 4.3465
- **Maker Fees**: 2.6073
- **Taker Fees**: 1.7392
- **Fee Drag %**: 0.6217

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0527
- **PnL Component**: -0.0174
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0178
- **Fee Drag Component**: -0.0031
- **Inventory Component**: -0.0142
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0071**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.14 | -3.51 | 0.26 | 69 | -0.0060 | n/a |
| 1 | -0.06 | -1.51 | 0.23 | 78 | -0.0051 | n/a |
| 2 | -0.04 | -1.88 | 0.12 | 66 | -0.0039 | n/a |
| 3 | 0.07 | 3.76 | 0.06 | 71 | -0.0025 | n/a |
| 4 | -0.13 | -1.95 | 0.45 | 85 | -0.0218 | n/a |
| 5 | 0.36 | 4.72 | 0.20 | 94 | -0.0008 | n/a |
| 6 | -0.18 | -5.52 | 0.34 | 73 | -0.0072 | n/a |
| 7 | -0.18 | -5.60 | 0.23 | 72 | -0.0062 | n/a |
| 8 | -0.43 | -10.70 | 0.49 | 80 | -0.0417 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1445)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.03 | -2.96 | 2.64 | -0.0595 |
| fees_2x | -2.34 | -3.42 | 2.92 | -0.0663 |
| latency_plus1 | -1.68 | -2.45 | 2.31 | -0.0517 |
| latency_plus2 | -1.77 | -2.58 | 2.39 | -0.0532 |
| latency_plus3 | -1.84 | -2.68 | 2.49 | -0.0544 |
| low_liquidity | -1.72 | -2.51 | 2.37 | -0.0527 |
| very_low_liquidity | -1.72 | -2.51 | 2.37 | -0.0527 |
| high_slippage | -2.34 | -3.42 | 2.92 | -0.0632 |
| extreme_slippage | -3.59 | -5.24 | 4.07 | -0.0848 |
| combined_adverse | -2.60 | -3.81 | 3.13 | -0.0689 |
| spread_widen_10bps | -2.87 | -3.98 | 3.32 | -0.0713 |
| spread_widen_25bps | -4.05 | -6.08 | 4.40 | -0.0921 |
| thin_book | -4.72 | -6.45 | 5.31 | -0.1026 |
| very_thin_book | -3.63 | -6.92 | 4.04 | -0.0776 |
| entry_spread_stress | -3.78 | -5.42 | 4.25 | -0.0874 |
| combined_market_deterioration | -4.31 | -5.85 | 4.81 | -0.0960 |
| severe_adverse | -7.01 | -10.59 | 7.44 | -0.1445 |

## Holdout Validation

- **Holdout bars**: 8759
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0034)
- **Trend**: ranging (efficiency: 0.0007)
- **Best holdout score**: -0.0043 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0986 | -0.0112 | -0.42 | 0.52 | 169 |
| 1 | -0.0030 | -0.0043 | -0.13 | 0.14 | 136 |
| 2 | -0.0033 | -0.0130 | -0.48 | 0.50 | 189 |
| 3 | -0.0034 | -0.0511 | -0.09 | 1.96 | 360 |
| 4 | -0.0039 | -0.0320 | -1.09 | 1.27 | 551 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51843
- **Expected rows**: 51862
- **Missing rows**: 19
- **Forward-fill count**: 308
- **Forward-fill fraction**: 0.005941014215998302
- **Longest gap (seconds)**: 5100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0177 <= 0; recent PnL -0.5584% < 0
- **Objective score**: -0.017687909155196083
- **PnL %**: -0.5584034461021786
- **Trade count**: 155

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0103 <= 0; recent PnL -0.1307% < 0
- **Objective score**: -0.010275670063940836
- **PnL %**: -0.13073866575700765
- **Trade count**: 83

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0724 <= 0; recent PnL -0.0535% < 0
- **Objective score**: -0.07244765406311679
- **PnL %**: -0.05346687253885032
- **Trade count**: 34

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: -0.07524860011722494
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1434, -0.0867 |
| sell_spread_base | -0.1153, -0.0872 |
| stop_loss | -0.0755, -0.0761 |
| take_profit | -0.0873, -0.0392 |
| executor_refresh_time | -0.0716, -0.0909 |
| cooldown_time | -0.0794, -0.0640 |
| total_amount_quote | -0.0738, -0.0724 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3050044126519604
- **Max CV**: 0.6682473677801014
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1744 | 1.7407500516056165 | 3.153149193812948 | 2.647087528787125 |
| buy_spread_ratio | 0.0895 | 2.225046874887852 | 2.945079965680473 | 2.545120912088455 |
| sell_spread_base | 0.5856 | 0.3314003374733954 | 1.5996616807237043 | 0.7604710402466263 |
| sell_spread_ratio | 0.2578 | 1.4971979568332043 | 2.9478613634381565 | 2.120466078190619 |
| buy_side_weight | 0.1947 | 0.20344000882337293 | 0.36828312725248685 | 0.256363407611101 |
| amount_skew | 0.0839 | 2.403099053236213 | 3.188367616835107 | 2.753312342895131 |
| stop_loss | 0.6682 | 0.010204752222437023 | 0.04982185983646343 | 0.01747609839426188 |
| take_profit | 0.5653 | 0.005075866568184471 | 0.02204108096643664 | 0.010048239147858054 |
| executor_refresh_time | 0.4327 | 2765.0 | 11819.0 | 8220.9 |
| cooldown_time | 0.2329 | 2142.0 | 5360.0 | 4135.2 |
| total_amount_quote | 0.0700 | 771.2911504641156 | 989.1073640392913 | 936.1549360121219 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

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

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.017687909155196083 | FAIL |
| recent_pnl | >= 0 | -0.5584034461021786 | FAIL |
| recent_trades | >= 5 | 155 | PASS |
| worst_stress | > -10 | -0.14445663600081185 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.011202549480789381 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.14445663600081185 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.017687909155196083, pnl=-0.5584034461021786, trades=155, reason=recent objective score -0.0177 <= 0; recent PnL -0.5584% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.010275670063940836, pnl=-0.13073866575700765, trades=83, reason=recent objective score -0.0103 <= 0; recent PnL -0.1307% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.07244765406311679, pnl=-0.05346687253885032, trades=34, reason=recent objective score -0.0724 <= 0; recent PnL -0.0535% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3050044126519604 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51843 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0177 <= 0; recent PnL -0.5584% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0103 <= 0; recent PnL -0.1307% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0724 <= 0; recent PnL -0.0535% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51843
- **Pre-release bars**: 43797
- **Dev bars**: 35038
- **Holdout bars**: 8759
- **Recent 28d bars**: 8046
- **Recent window start**: 1773213900

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T10:16:58.196623+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 11994
