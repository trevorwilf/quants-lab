# PMM Dynamic Optimization Report: mexc_ICP-USDT_5m_sweep_v1

Generated: 2026-04-09 05:15:08 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T05:15:08.384872+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 12013 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ICP-USDT
- **interval**: 5m
- **n_candles**: 51871
- **dataset_hash**: 792b0477e8426b0d04f31f513bf1d0e347750909d98121811d3ab700cc079962
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 849.1438319189832
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.2784143203401563 |
| buy_n_levels | 9 |
| buy_side_weight | 0.760264102353754 |
| buy_spread_base | 3.2465572310641004 |
| buy_spread_ratio | 1.2694372134570497 |
| cooldown_time | 595 |
| executor_refresh_time | 1969 |
| macd_fast | 31 |
| macd_signal | 24 |
| macd_slow | 52 |
| natr_length | 26 |
| sell_n_levels | 4 |
| sell_spread_base | 5.7697423154292204 |
| sell_spread_ratio | 2.3651902227993578 |
| stop_loss | 0.03211773960596171 |
| take_profit | 0.06774288317182593 |
| time_limit | 91458 |
| total_amount_quote | 849.1438319189832 |
| trailing_stop_activation | 0.012738721123321858 |
| trailing_stop_delta | 0.0017254669677932999 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 849.1438319189832 |
| Selected | 849.1438319189832 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 17.5914
- **Net PnL (quote)**: 149.3760
- **Sharpe Ratio**: 4.0174
- **Max Drawdown %**: 3.4248
- **Profit Factor**: 2.006636117403224
- **Trade Count**: 737
- **Total Fees (quote)**: 7.8756
- **Maker Fees**: 3.9222
- **Taker Fees**: 3.9534
- **Fee Drag %**: 0.9275

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1158
- **PnL Component**: 0.1620
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0257
- **Fee Drag Component**: -0.0046
- **Inventory Component**: -0.0156
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0029**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -2.36 | -8.16 | 3.01 | 93 | -0.0483 | n/a |
| 1 | 0.84 | 3.34 | 0.57 | 92 | 0.0033 | n/a |
| 2 | 0.15 | 5.55 | 0.08 | 50 | 0.0007 | n/a |
| 3 | 0.58 | 8.99 | 0.10 | 74 | 0.0048 | n/a |
| 4 | 9.16 | 7.73 | 0.23 | 70 | 0.0853 | n/a |
| 5 | 1.96 | 6.35 | 0.79 | 105 | 0.0078 | n/a |
| 6 | -1.63 | -5.40 | 2.50 | 67 | -0.0357 | n/a |
| 7 | 0.06 | 0.91 | 0.32 | 52 | -0.0020 | n/a |
| 8 | -0.99 | -3.96 | 1.81 | 56 | -0.0388 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0687)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 17.08 | 3.92 | 3.50 | 0.1085 |
| fees_2x | 16.59 | 3.82 | 3.58 | 0.1013 |
| latency_plus1 | 9.20 | 3.26 | 3.42 | 0.0421 |
| latency_plus2 | 6.50 | 2.37 | 3.97 | 0.0127 |
| latency_plus3 | 4.04 | 1.50 | 4.90 | -0.0183 |
| low_liquidity | 17.56 | 4.01 | 3.42 | 0.1155 |
| very_low_liquidity | 17.46 | 3.99 | 3.42 | 0.1146 |
| high_slippage | 16.34 | 3.78 | 3.62 | 0.1035 |
| extreme_slippage | 13.86 | 3.30 | 4.02 | 0.0787 |
| combined_adverse | 7.64 | 2.73 | 3.70 | 0.0232 |
| spread_widen_10bps | 13.54 | 3.09 | 3.53 | 0.0798 |
| spread_widen_25bps | 5.23 | 1.22 | 9.09 | -0.0499 |
| thin_book | 1.12 | 0.46 | 4.27 | -0.0399 |
| very_thin_book | -1.21 | -0.92 | 3.14 | -0.0426 |
| entry_spread_stress | 14.61 | 3.39 | 3.53 | 0.0890 |
| combined_market_deterioration | 4.73 | 1.28 | 8.65 | -0.0465 |
| severe_adverse | -1.67 | -0.89 | 4.56 | -0.0687 |

## Holdout Validation

- **Holdout bars**: 8761
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0041)
- **Trend**: ranging (efficiency: 0.0043)
- **Best holdout score**: 0.0158 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0235 | -0.0430 | -2.19 | 2.67 | 126 |
| 1 | 0.0105 | 0.0158 | 2.19 | 0.55 | 173 |
| 2 | 0.0070 | -0.0085 | 1.24 | 0.51 | 298 |
| 3 | 0.0062 | 0.0142 | 2.07 | 0.34 | 133 |
| 4 | 0.0058 | -0.0605 | 1.17 | 2.28 | 209 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51871
- **Expected rows**: 51871
- **Missing rows**: 0
- **Forward-fill count**: 160
- **Forward-fill fraction**: 0.003084575196159704
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0131 <= 0
- **Objective score**: -0.01310397711554781
- **PnL %**: 0.2538901285503317
- **Trade count**: 107

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.005098755742531103
- **PnL %**: 1.2602956792073199
- **Trade count**: 62

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1385 <= 0
- **Objective score**: -0.13850909484525215
- **PnL %**: 0.03274015748776682
- **Trade count**: 17

## Sensitivity Analysis

- **Sensitivity penalty**: 0.35714285714285715
- **Baseline score**: 0.07785427092058406
- **Sign flips**: 2
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0206, 0.0448 |
| sell_spread_base | 0.1040, 0.0393 |
| stop_loss | 0.0696, 0.1349 |
| take_profit | 0.0779, 0.0779 |
| executor_refresh_time | -0.0076, 0.0894 |
| cooldown_time | -0.0167, 0.0779 |
| total_amount_quote | 0.0794, 0.0790 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.47176870404016785
- **Max CV**: 1.2710982042496786
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1080 | 2.0886086130280304 | 3.005934012344975 | 2.6562315622929544 |
| buy_spread_ratio | 0.1731 | 1.213594371997738 | 1.8343427246639918 | 1.435735033753199 |
| sell_spread_base | 0.6058 | 0.7023170066682689 | 5.141948167574937 | 2.7175275358414064 |
| sell_spread_ratio | 0.2119 | 1.3938715713394743 | 2.8628459537473794 | 2.224562040672871 |
| buy_side_weight | 0.0775 | 0.594224955067848 | 0.7982782637315691 | 0.7356288174282384 |
| amount_skew | 0.2514 | 1.088655907892726 | 2.387318271993615 | 1.8193623302088366 |
| stop_loss | 1.0121 | 0.010576904495434912 | 0.1509278839829098 | 0.05146517031741148 |
| take_profit | 0.4387 | 0.014705415067704458 | 0.0598697892227239 | 0.03545683527611444 |
| executor_refresh_time | 0.6495 | 303.0 | 3060.0 | 1481.2 |
| cooldown_time | 1.2711 | 112.0 | 3530.0 | 783.4 |
| total_amount_quote | 0.3903 | 219.29315476542868 | 947.2219187797562 | 609.0776521583687 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.0
- **supports_post_only**: True
- **connector**: mexc
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
- holdout_no_collapse: **FAIL**
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.01310397711554781 | FAIL |
| recent_pnl | >= 0 | 0.2538901285503317 | PASS |
| recent_trades | >= 5 | 107 | PASS |
| worst_stress | > -10 | -0.06873698374414422 | PASS |
| sensitivity_penalty | < 0.50 | 0.35714285714285715 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.04296733155700416 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.06873698374414422 |
| sensitivity | PASS | penalty=0.35714285714285715 |
| recent_28d | FAIL | score=-0.01310397711554781, pnl=0.2538901285503317, trades=107, reason=recent objective score -0.0131 <= 0 |
| recent_14d_info | PASS | informational only; score=0.005098755742531103, pnl=1.2602956792073199, trades=62, reason= |
| recent_7d_info | FAIL | informational only; score=-0.13850909484525215, pnl=0.03274015748776682, trades=17, reason=recent objective score -0.1385 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.47176870404016785 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51871 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0131 <= 0 |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1385 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51871
- **Pre-release bars**: 43806
- **Dev bars**: 35045
- **Holdout bars**: 8761
- **Recent 28d bars**: 8065
- **Recent window start**: 1773281400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T05:15:08.384872+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 12013
