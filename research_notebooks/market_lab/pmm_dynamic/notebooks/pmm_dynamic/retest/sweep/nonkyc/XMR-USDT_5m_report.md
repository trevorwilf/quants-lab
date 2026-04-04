# PMM Dynamic Optimization Report: nonkyc_XMR-USDT_5m_retest_20260403

Generated: 2026-04-04 07:35:29 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-04T07:35:29.288207+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 6569 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 51866
- **dataset_hash**: 68011971b0afa3e110a999a50d82b76337f10c10bb695f60acd8d3e3c4f4a5dd
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 820.4681578237688
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.1404272660346053 |
| buy_n_levels | 9 |
| buy_side_weight | 0.3262400512795466 |
| buy_spread_base | 2.6575351013432544 |
| buy_spread_ratio | 2.553554601623629 |
| cooldown_time | 1287 |
| executor_refresh_time | 1242 |
| macd_fast | 20 |
| macd_signal | 28 |
| macd_slow | 66 |
| natr_length | 42 |
| sell_n_levels | 2 |
| sell_spread_base | 4.698515053319818 |
| sell_spread_ratio | 2.671065549422046 |
| stop_loss | 0.010224035831805547 |
| take_profit | 0.010053965586034946 |
| time_limit | 123959 |
| total_amount_quote | 820.4681578237688 |
| trailing_stop_activation | 0.018105637274177466 |
| trailing_stop_delta | 0.001717205209272019 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 820.4681578237688 |
| Selected | 820.4681578237688 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 7.5131
- **Net PnL (quote)**: 61.6426
- **Sharpe Ratio**: 2.2303
- **Max Drawdown %**: 1.1657
- **Profit Factor**: 3.924943613293632
- **Trade Count**: 641
- **Total Fees (quote)**: 11.7758
- **Maker Fees**: 7.0063
- **Taker Fees**: 4.7695
- **Fee Drag %**: 1.4353

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0512
- **PnL Component**: 0.0724
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0087
- **Fee Drag Component**: -0.0072
- **Inventory Component**: -0.0052
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0033**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.08 | -3.17 | 0.22 | 52 | -0.0049 | n/a |
| 1 | 0.64 | 8.48 | 0.05 | 63 | 0.0034 | n/a |
| 2 | 0.01 | 0.78 | 0.05 | 55 | -0.0026 | n/a |
| 3 | 1.47 | 6.89 | 0.06 | 83 | 0.0095 | n/a |
| 4 | 0.04 | 0.76 | 0.20 | 93 | -0.0041 | n/a |
| 5 | 0.01 | 0.77 | 0.08 | 68 | -0.0020 | n/a |
| 6 | -0.07 | -4.78 | 0.09 | 60 | -0.0038 | n/a |
| 7 | 0.05 | 3.21 | 0.07 | 62 | -0.0025 | n/a |
| 8 | 0.22 | 6.44 | 0.10 | 56 | -0.0049 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0173)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 6.80 | 2.03 | 1.33 | 0.0397 |
| fees_2x | 6.08 | 1.83 | 1.49 | 0.0281 |
| latency_plus1 | 7.34 | 2.18 | 1.13 | 0.0501 |
| latency_plus2 | 7.19 | 2.15 | 0.57 | 0.0551 |
| latency_plus3 | 5.57 | 1.71 | 1.22 | 0.0334 |
| low_liquidity | 7.19 | 2.14 | 1.17 | 0.0482 |
| very_low_liquidity | 4.22 | 2.44 | 0.61 | 0.0272 |
| high_slippage | 7.37 | 2.19 | 1.20 | 0.0496 |
| extreme_slippage | 7.08 | 2.11 | 1.27 | 0.0464 |
| combined_adverse | 6.18 | 1.86 | 1.32 | 0.0344 |
| spread_widen_10bps | 6.92 | 2.06 | 1.28 | 0.0445 |
| spread_widen_25bps | 6.68 | 2.02 | 0.67 | 0.0489 |
| thin_book | 1.15 | 1.60 | 0.39 | 0.0031 |
| very_thin_book | -0.26 | -1.16 | 0.31 | -0.0062 |
| entry_spread_stress | 6.74 | 2.02 | 1.31 | 0.0426 |
| combined_market_deterioration | 4.92 | 1.55 | 0.54 | 0.0345 |
| severe_adverse | -0.75 | -2.80 | 0.81 | -0.0173 |

## Holdout Validation

- **Holdout bars**: 8772
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0046)
- **Trend**: ranging (efficiency: 0.0046)
- **Best holdout score**: -0.0051 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0169 | -0.0059 | -0.13 | 0.19 | 135 |
| 1 | -0.0028 | -0.0222 | -0.34 | 0.39 | 197 |
| 2 | -0.0028 | -0.0192 | -0.17 | 0.26 | 384 |
| 3 | -0.0028 | -0.0059 | -0.13 | 0.19 | 135 |
| 4 | -0.0029 | -0.0051 | -0.13 | 0.16 | 126 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51866
- **Expected rows**: 51925
- **Missing rows**: 59
- **Forward-fill count**: 231
- **Forward-fill fraction**: 0.004453784753017391
- **Longest gap (seconds)**: 18000

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0053 <= 0
- **Objective score**: -0.005297396302516227
- **PnL %**: 0.30632090604654777
- **Trade count**: 128

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.045007684341100404
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0609, 0.0395 |
| sell_spread_base | 0.0510, 0.0410 |
| stop_loss | 0.0547, 0.0517 |
| take_profit | 0.0433, 0.0483 |
| executor_refresh_time | 0.0450, 0.0579 |
| cooldown_time | 0.0450, 0.0562 |
| total_amount_quote | 0.0524, 0.0453 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.34086388550724894
- **Max CV**: 0.8480282173809884
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, total_amount_quote
- **Scattered params**: executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0995 | 2.018360724973581 | 2.800717562594257 | 2.417175482699161 |
| buy_spread_ratio | 0.1199 | 1.951040869337922 | 2.7858193569921506 | 2.41275462126451 |
| sell_spread_base | 0.4665 | 0.7873209092103571 | 5.202605174558726 | 3.0824408629110938 |
| sell_spread_ratio | 0.2790 | 1.205917687054585 | 2.671065549422046 | 1.6410536583523432 |
| buy_side_weight | 0.2592 | 0.20465185545712988 | 0.4367069055792279 | 0.2767770178142018 |
| amount_skew | 0.1725 | 1.853388759253038 | 3.547664021907545 | 2.880521461576358 |
| stop_loss | 0.2225 | 0.010224035831805547 | 0.02155780821799612 | 0.013628930426005137 |
| take_profit | 0.3778 | 0.005110702857858025 | 0.013804817732824538 | 0.007215714442108133 |
| executor_refresh_time | 0.8480 | 898.0 | 12590.0 | 4864.4 |
| cooldown_time | 0.8226 | 107.0 | 4250.0 | 1895.5 |
| total_amount_quote | 0.0821 | 785.5994445912188 | 975.7358649434801 | 896.8554928138963 |

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
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.005297396302516227 | FAIL |
| recent_pnl | >= 0 | 0.30632090604654777 | PASS |
| recent_trades | >= 5 | 128 | PASS |
| worst_stress | > -10 | -0.017305541936123808 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.005858128235743443 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.017305541936123808 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.005297396302516227, pnl=0.30632090604654777, trades=128, reason=recent objective score -0.0053 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.34086388550724894 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51866 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0053 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35088
- **Holdout bars**: 8772
- **Recent 28d bars**: 8006

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-04T07:35:29.288207+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 6569
