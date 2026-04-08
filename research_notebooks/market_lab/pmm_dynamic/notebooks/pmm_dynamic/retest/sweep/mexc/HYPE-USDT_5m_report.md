# PMM Dynamic Optimization Report: mexc_HYPE-USDT_5m_retest_20260408

Generated: 2026-04-08 08:57:44 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T08:57:44.300573+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 8817 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: HYPE-USDT
- **interval**: 5m
- **n_candles**: 51839
- **dataset_hash**: 4a600f4dd8bdeb2248da6a544b69a608eee32a341939f9c09db4d1d11bef6795
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 491.4518308522199
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.4909057161621848 |
| buy_n_levels | 3 |
| buy_side_weight | 0.6440429964097669 |
| buy_spread_base | 3.4551382041261514 |
| buy_spread_ratio | 1.3290992279846248 |
| cooldown_time | 1312 |
| executor_refresh_time | 1449 |
| macd_fast | 15 |
| macd_signal | 28 |
| macd_slow | 44 |
| natr_length | 36 |
| sell_n_levels | 9 |
| sell_spread_base | 5.483156833059431 |
| sell_spread_ratio | 2.489459895393302 |
| stop_loss | 0.03555303437459667 |
| take_profit | 0.007421131279307484 |
| time_limit | 122057 |
| total_amount_quote | 491.4518308522199 |
| trailing_stop_activation | 0.0007495200739717768 |
| trailing_stop_delta | 0.001057715303863337 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 491.4518308522199 |
| Selected | 491.4518308522199 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 27.5376
- **Net PnL (quote)**: 135.3338
- **Sharpe Ratio**: 7.3524
- **Max Drawdown %**: 1.8956
- **Profit Factor**: 2.480858344394571
- **Trade Count**: 576
- **Total Fees (quote)**: 19.9161
- **Maker Fees**: 9.9425
- **Taker Fees**: 9.9736
- **Fee Drag %**: 4.0525

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1802
- **PnL Component**: 0.2432
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0142
- **Fee Drag Component**: -0.0203
- **Inventory Component**: -0.0282
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.0068**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 2.22 | 8.88 | 0.62 | 55 | 0.0152 | n/a |
| 1 | 3.17 | 10.14 | 1.06 | 75 | 0.0202 | n/a |
| 2 | 0.96 | 4.83 | 1.01 | 62 | -0.0005 | n/a |
| 3 | 5.01 | 9.44 | 0.62 | 73 | 0.0415 | n/a |
| 4 | 0.14 | 0.41 | 2.11 | 79 | -0.0176 | n/a |
| 5 | 6.40 | 22.48 | 0.33 | 46 | 0.0420 | n/a |
| 6 | 2.30 | 12.32 | 0.74 | 78 | 0.0142 | n/a |
| 7 | 2.28 | 5.73 | 1.49 | 65 | 0.0088 | n/a |
| 8 | 0.52 | 2.57 | 0.68 | 66 | -0.0026 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.2751)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 25.51 | 6.83 | 1.95 | 0.1532 |
| fees_2x | 23.48 | 6.31 | 2.00 | 0.1260 |
| latency_plus1 | 25.43 | 6.70 | 2.40 | 0.1592 |
| latency_plus2 | 22.84 | 5.75 | 3.02 | 0.1337 |
| latency_plus3 | 13.29 | 3.60 | 4.25 | 0.0427 |
| low_liquidity | 27.54 | 7.35 | 1.90 | 0.1802 |
| very_low_liquidity | 28.05 | 7.47 | 1.89 | 0.1843 |
| high_slippage | 22.45 | 6.05 | 2.03 | 0.1375 |
| extreme_slippage | 12.28 | 3.38 | 2.95 | 0.0417 |
| combined_adverse | 18.21 | 4.86 | 2.64 | 0.0864 |
| spread_widen_10bps | 22.31 | 5.99 | 2.05 | 0.1356 |
| spread_widen_25bps | 9.78 | 2.35 | 8.04 | -0.0217 |
| thin_book | 5.16 | 1.75 | 3.71 | 0.0114 |
| very_thin_book | -2.47 | -1.49 | 3.52 | -0.0560 |
| entry_spread_stress | 18.39 | 4.79 | 3.32 | 0.0922 |
| combined_market_deterioration | 2.36 | 0.75 | 4.79 | -0.0693 |
| severe_adverse | -10.44 | -3.37 | 12.65 | -0.2751 |

## Holdout Validation

- **Holdout bars**: 8757
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0043)
- **Trend**: ranging (efficiency: 0.0037)
- **Best holdout score**: 0.0287 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0475 | 0.0287 | 4.62 | 1.46 | 148 |
| 1 | 0.0247 | -0.0727 | 4.68 | 2.29 | 747 |
| 2 | 0.0231 | -0.1897 | 1.65 | 5.72 | 245 |
| 3 | 0.0212 | -0.1060 | 7.42 | 4.41 | 222 |
| 4 | 0.0203 | 0.0113 | 8.00 | 1.23 | 429 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51839
- **Expected rows**: 51852
- **Missing rows**: 13
- **Forward-fill count**: 224
- **Forward-fill fraction**: 0.004321071008314204
- **Longest gap (seconds)**: 3300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.0003656306789277518
- **PnL %**: 1.0965043546067659
- **Trade count**: 139

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0044 <= 0
- **Objective score**: -0.004361030996690569
- **PnL %**: 0.3599831811615139
- **Trade count**: 84

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0825 <= 0
- **Objective score**: -0.08251332620920573
- **PnL %**: 0.33152881190004263
- **Trade count**: 30

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.19518703701639464
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.2063, 0.2627 |
| sell_spread_base | 0.1975, 0.1964 |
| stop_loss | 0.1719, 0.2060 |
| take_profit | 0.1952, 0.1952 |
| executor_refresh_time | 0.2125, 0.1952 |
| cooldown_time | 0.1952, 0.1163 |
| total_amount_quote | 0.1952, 0.1967 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.37072913634413757
- **Max CV**: 0.7409144195290657
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss
- **Scattered params**: take_profit, executor_refresh_time, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1272 | 2.5939275552009247 | 3.9090039944254 | 3.2782540435889445 |
| buy_spread_ratio | 0.1087 | 1.213497671643632 | 1.6311560751099663 | 1.3651961437612925 |
| sell_spread_base | 0.4655 | 0.8948796942562807 | 4.138555853082733 | 2.502495034553017 |
| sell_spread_ratio | 0.1644 | 1.5813148678959281 | 2.610676879154791 | 2.0627230026709986 |
| buy_side_weight | 0.0912 | 0.5834137936104531 | 0.7829123008307758 | 0.7296987299412299 |
| amount_skew | 0.2401 | 1.7331940346564738 | 3.41835785407834 | 2.507486553978244 |
| stop_loss | 0.3826 | 0.05890121632231181 | 0.2104901834053154 | 0.12982428797026396 |
| take_profit | 0.5754 | 0.011001377124318212 | 0.12236828580411939 | 0.05735394809292654 |
| executor_refresh_time | 0.5579 | 580.0 | 6507.0 | 3322.2 |
| cooldown_time | 0.7409 | 146.0 | 2881.0 | 1068.2 |
| total_amount_quote | 0.6240 | 91.01514734764713 | 558.4199611738259 | 263.0331457529423 |

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
- holdout_passed: PASS
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.0003656306789277518 | PASS |
| recent_pnl | >= 0 | 1.0965043546067659 | PASS |
| recent_trades | >= 5 | 139 | PASS |
| worst_stress | > -10 | -0.27514753594023134 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0287 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.27514753594023134 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.0003656306789277518, pnl=1.0965043546067659, trades=139, reason= |
| recent_14d_info | FAIL | informational only; score=-0.004361030996690569, pnl=0.3599831811615139, trades=84, reason=recent objective score -0.0044 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.08251332620920573, pnl=0.33152881190004263, trades=30, reason=recent objective score -0.0825 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.37072913634413757 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51839 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0044 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0825 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51839
- **Pre-release bars**: 43787
- **Dev bars**: 35030
- **Holdout bars**: 8757
- **Recent 28d bars**: 8052
- **Recent window start**: 1773212400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T08:57:44.300573+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 8817
