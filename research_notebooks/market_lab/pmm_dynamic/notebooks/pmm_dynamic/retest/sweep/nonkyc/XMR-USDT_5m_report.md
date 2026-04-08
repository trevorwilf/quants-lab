# PMM Dynamic Optimization Report: nonkyc_XMR-USDT_5m_retest_20260408

Generated: 2026-04-08 12:54:52 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T12:54:52.738265+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 11810 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 51912
- **dataset_hash**: 6826ed1619d18824eb6160e08cd9d36111d0daa6eb842fbb06a3c46d5a46b234
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 638.8268251399502
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.0693233389469494 |
| buy_n_levels | 7 |
| buy_side_weight | 0.2713469741263099 |
| buy_spread_base | 2.022972136490778 |
| buy_spread_ratio | 1.9209317534516595 |
| cooldown_time | 2935 |
| executor_refresh_time | 4338 |
| macd_fast | 32 |
| macd_signal | 12 |
| macd_slow | 65 |
| natr_length | 35 |
| sell_n_levels | 10 |
| sell_spread_base | 5.807651996655439 |
| sell_spread_ratio | 2.110788514604412 |
| stop_loss | 0.04451049320916281 |
| take_profit | 0.00936259087266018 |
| time_limit | 26608 |
| total_amount_quote | 638.8268251399502 |
| trailing_stop_activation | 0.01207014608530825 |
| trailing_stop_delta | 0.0012468780640568886 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 638.8268251399502 |
| Selected | 638.8268251399502 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 4.6552
- **Net PnL (quote)**: 29.7389
- **Sharpe Ratio**: 2.8801
- **Max Drawdown %**: 1.5543
- **Profit Factor**: 1.5862912873175097
- **Trade Count**: 1013
- **Total Fees (quote)**: 19.6893
- **Maker Fees**: 10.7917
- **Taker Fees**: 8.8976
- **Fee Drag %**: 3.0821

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0106
- **PnL Component**: 0.0455
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0117
- **Fee Drag Component**: -0.0154
- **Inventory Component**: -0.0077
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0034**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.41 | 11.31 | 0.11 | 110 | -0.0002 | n/a |
| 1 | 0.43 | 6.25 | 0.08 | 87 | 0.0004 | n/a |
| 2 | 0.04 | 1.23 | 0.15 | 130 | -0.0409 | n/a |
| 3 | 0.98 | 5.90 | 0.12 | 121 | 0.0029 | n/a |
| 4 | -0.96 | -13.89 | 1.00 | 139 | -0.0259 | n/a |
| 5 | 0.44 | 9.38 | 0.11 | 130 | -0.0025 | n/a |
| 6 | -0.49 | -11.16 | 0.54 | 135 | -0.0941 | n/a |
| 7 | 0.33 | 12.71 | 0.08 | 111 | -0.0008 | n/a |
| 8 | 0.20 | 6.40 | 0.11 | 111 | -0.0022 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3.11 | 1.95 | 1.66 | -0.0128 |
| fees_2x | 1.57 | 1.00 | 1.81 | -0.0368 |
| latency_plus1 | 4.08 | 2.37 | 2.55 | -0.0061 |
| latency_plus2 | 4.26 | 2.64 | 1.57 | 0.0069 |
| latency_plus3 | 3.60 | 2.09 | 2.55 | -0.0108 |
| low_liquidity | 4.40 | 2.74 | 1.55 | 0.0083 |
| very_low_liquidity | 4.21 | 2.63 | 1.55 | 0.0065 |
| high_slippage | 4.31 | 2.67 | 1.58 | 0.0071 |
| extreme_slippage | 3.61 | 2.24 | 1.63 | -0.0000 |
| combined_adverse | 1.89 | 1.12 | 3.05 | -0.0388 |
| spread_widen_10bps | 3.55 | 1.97 | 3.56 | -0.0214 |
| spread_widen_25bps | 3.39 | 1.61 | 5.22 | -0.0408 |
| thin_book | -1.96 | -1.85 | 3.50 | -0.0677 |
| very_thin_book | -2.45 | -3.21 | 2.67 | -0.0577 |
| entry_spread_stress | 3.75 | 1.90 | 4.56 | -0.0296 |
| combined_market_deterioration | 0.03 | 0.04 | 3.30 | -0.0550 |
| severe_adverse | -4.03 | -4.64 | 4.21 | -0.1000 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0042)
- **Trend**: ranging (efficiency: 0.0048)
- **Best holdout score**: -0.0183 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0447 | -0.0183 | -0.22 | 0.58 | 274 |
| 1 | 0.0008 | -0.0478 | -0.22 | 0.58 | 322 |
| 2 | 0.0006 | -0.0966 | -0.61 | 1.06 | 210 |
| 3 | 0.0003 | -0.1247 | -0.36 | 0.96 | 206 |
| 4 | 0.0001 | -0.0933 | -0.95 | 1.50 | 534 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51912
- **Expected rows**: 51912
- **Missing rows**: 0
- **Forward-fill count**: 236
- **Forward-fill fraction**: 0.004546155031591925
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0032 <= 0
- **Objective score**: -0.0032475085935448293
- **PnL %**: 0.21780249669778579
- **Trade count**: 205

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0192 <= 0
- **Objective score**: -0.019168729729076434
- **PnL %**: 0.05430021400315817
- **Trade count**: 108

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1261 <= 0; recent PnL -0.0960% < 0
- **Objective score**: -0.1261023858768197
- **PnL %**: -0.09601987078921008
- **Trade count**: 55

## Sensitivity Analysis

- **Sensitivity penalty**: 0.6428571428571429
- **Baseline score**: 0.019191545673598577
- **Sign flips**: 3
- **Collapse count**: 6
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0177, -0.0104 |
| sell_spread_base | 0.0134, 0.0071 |
| stop_loss | 0.0218, 0.0244 |
| take_profit | -0.0178, 0.0191 |
| executor_refresh_time | 0.0229, 0.0162 |
| cooldown_time | 0.0056, -0.0061 |
| total_amount_quote | 0.0155, 0.0009 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.44733950767007724
- **Max CV**: 1.023061179151375
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, amount_skew, take_profit, total_amount_quote
- **Scattered params**: sell_spread_base, buy_side_weight, stop_loss, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0856 | 2.064425017035983 | 2.6723827658810304 | 2.33889405106555 |
| buy_spread_ratio | 0.1945 | 1.4982899461012569 | 2.825523604289375 | 2.23243059912848 |
| sell_spread_base | 0.8688 | 0.422431425598825 | 5.791755077839602 | 2.081670713314415 |
| sell_spread_ratio | 0.1897 | 1.2422585077555501 | 2.263861498532576 | 1.7692013487153713 |
| buy_side_weight | 0.5146 | 0.2107340034175824 | 0.7893319461658035 | 0.3468017728258002 |
| amount_skew | 0.2206 | 1.9951625010217762 | 3.721474292193681 | 2.8951947448295146 |
| stop_loss | 0.6944 | 0.01276821892229501 | 0.23273387325922126 | 0.10920918362146348 |
| take_profit | 0.4421 | 0.00562804532713393 | 0.019077028979625005 | 0.012041068142064536 |
| executor_refresh_time | 1.0231 | 534.0 | 14260.0 | 4220.3 |
| cooldown_time | 0.5223 | 274.0 | 7121.0 | 4478.5 |
| total_amount_quote | 0.1650 | 601.8009563120829 | 959.2146271870438 | 792.9739620312099 |

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
- holdout_no_collapse: PASS
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.0032475085935448293 | FAIL |
| recent_pnl | >= 0 | 0.21780249669778579 | PASS |
| recent_trades | >= 5 | 205 | PASS |
| worst_stress | > -10 | -0.10002893489102117 | PASS |
| sensitivity_penalty | < 0.50 | 0.6428571428571429 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.018288649146953745 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.10002893489102117 |
| sensitivity | FAIL | penalty=0.6428571428571429 |
| recent_28d | FAIL | score=-0.0032475085935448293, pnl=0.21780249669778579, trades=205, reason=recent objective score -0.0032 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.019168729729076434, pnl=0.05430021400315817, trades=108, reason=recent objective score -0.0192 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.1261023858768197, pnl=-0.09601987078921008, trades=55, reason=recent objective score -0.1261 <= 0; recent PnL -0.0960% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.44733950767007724 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51912 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0032 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0192 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1261 <= 0; recent PnL -0.0960% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51912
- **Pre-release bars**: 43847
- **Dev bars**: 35078
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065
- **Recent window start**: 1773229500

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T12:54:52.738265+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 11810
