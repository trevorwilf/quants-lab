# PMM Dynamic Optimization Report: nonkyc_NKYC-USDT_5m_sweep_v1

Generated: 2026-03-29 10:39:38 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T10:39:38.769349+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 8077 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: NKYC-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: c1847b2a1674046f16c645178e93aa44055e4cd11371b64b703dde27ad007bd3
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 797.8247447627315
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.584575116000297 |
| buy_n_levels | 7 |
| buy_side_weight | 0.21924345522622635 |
| buy_spread_base | 4.972530260996043 |
| buy_spread_ratio | 2.7700682177910796 |
| cooldown_time | 1867 |
| executor_refresh_time | 3190 |
| macd_fast | 35 |
| macd_signal | 26 |
| macd_slow | 37 |
| natr_length | 34 |
| sell_n_levels | 9 |
| sell_spread_base | 3.067814320070889 |
| sell_spread_ratio | 2.0127218493149757 |
| stop_loss | 0.01347324282088651 |
| take_profit | 0.00622970922262936 |
| time_limit | 124240 |
| total_amount_quote | 797.8247447627315 |
| trailing_stop_activation | 0.053548165294403254 |
| trailing_stop_delta | 0.0011852281051909887 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 797.8247447627315 |
| Selected | 797.8247447627315 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -4.0576
- **Net PnL (quote)**: -32.3724
- **Sharpe Ratio**: -8.0931
- **Max Drawdown %**: 4.0876
- **Profit Factor**: 0.3912865036021307
- **Trade Count**: 707
- **Total Fees (quote)**: 16.6723
- **Maker Fees**: 11.2289
- **Taker Fees**: 5.4434
- **Fee Drag %**: 2.0897

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0922
- **PnL Component**: -0.0414
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0307
- **Fee Drag Component**: -0.0104
- **Inventory Component**: -0.0095
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0167**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.29 | -7.41 | 0.43 | 77 | -0.0107 | n/a |
| 1 | -0.24 | -6.55 | 0.32 | 72 | -0.0122 | n/a |
| 2 | -0.22 | -8.12 | 0.27 | 36 | -0.0672 | n/a |
| 3 | -0.23 | -7.00 | 0.33 | 76 | -0.0153 | n/a |
| 4 | -0.42 | -12.17 | 0.44 | 59 | -0.0148 | n/a |
| 5 | -0.61 | -13.26 | 0.67 | 75 | -0.0187 | n/a |
| 6 | -0.70 | -9.70 | 0.75 | 114 | -0.0207 | n/a |
| 7 | -0.37 | -10.40 | 0.44 | 81 | -0.0144 | n/a |
| 8 | -0.05 | -1.14 | 0.18 | 84 | -0.0092 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.1404)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -5.10 | -10.10 | 5.13 | -0.1162 |
| fees_2x | -6.15 | -12.06 | 6.16 | -0.1404 |
| latency_plus1 | -4.07 | -8.12 | 4.10 | -0.0924 |
| latency_plus2 | -4.01 | -8.03 | 4.03 | -0.0911 |
| latency_plus3 | -4.12 | -8.17 | 4.14 | -0.0930 |
| low_liquidity | -4.27 | -8.42 | 4.30 | -0.0960 |
| very_low_liquidity | -4.20 | -8.47 | 4.21 | -0.0942 |
| high_slippage | -4.23 | -8.42 | 4.26 | -0.0952 |
| extreme_slippage | -4.57 | -9.05 | 4.60 | -0.1014 |
| combined_adverse | -5.49 | -10.70 | 5.51 | -0.1232 |
| spread_widen_10bps | -5.09 | -8.95 | 5.11 | -0.1128 |
| spread_widen_25bps | -5.19 | -9.21 | 5.21 | -0.1142 |
| thin_book | -3.18 | -9.32 | 3.19 | -0.0697 |
| very_thin_book | -1.03 | -6.78 | 1.04 | -0.0240 |
| entry_spread_stress | -5.48 | -8.53 | 5.51 | -0.1245 |
| combined_market_deterioration | -5.69 | -13.38 | 5.71 | -0.1243 |
| severe_adverse | -4.83 | -13.82 | 4.84 | -0.1036 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0034)
- **Trend**: ranging (efficiency: 0.0178)
- **Best holdout score**: -0.0070 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1163 | -0.0236 | -0.79 | 0.84 | 189 |
| 1 | -0.0088 | -0.0297 | -1.15 | 1.34 | 453 |
| 2 | -0.0090 | -0.0942 | -4.23 | 5.96 | 210 |
| 3 | -0.0094 | -0.0070 | 2.62 | 2.86 | 309 |
| 4 | -0.0095 | -0.0496 | -1.30 | 3.10 | 292 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 54
- **Forward-fill fraction**: 0.0010416465731756717
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0192 <= 0; recent PnL -0.5891% < 0
- **Objective score**: -0.01924905899033148
- **PnL %**: -0.5891341156543084
- **Trade count**: 156

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.1349458392408981
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1291, -0.1496 |
| sell_spread_base | -0.1201, -0.1641 |
| stop_loss | -0.1085, -0.1278 |
| take_profit | -0.1405, -0.1494 |
| executor_refresh_time | -0.1260, -0.1276 |
| cooldown_time | -0.1349, -0.1590 |
| total_amount_quote | -0.1325, -0.1372 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.330406700764818
- **Max CV**: 0.8144667968268196
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0618 | 4.825596246787146 | 5.951669937961925 | 5.413173523930283 |
| buy_spread_ratio | 0.0868 | 1.5096848576624393 | 2.0540419241019974 | 1.853325186107595 |
| sell_spread_base | 0.5314 | 0.23022646673716682 | 0.9131732451838197 | 0.4096975875028602 |
| sell_spread_ratio | 0.1990 | 1.2163587948263757 | 2.4072351346518785 | 1.8214533323458113 |
| buy_side_weight | 0.1947 | 0.20746952111463401 | 0.3760032255135526 | 0.27839868021566605 |
| amount_skew | 0.1428 | 2.0183660497124443 | 3.3402831047883526 | 2.7227644879155357 |
| stop_loss | 0.4653 | 0.03107733612564893 | 0.23367108537367295 | 0.14148335914899116 |
| take_profit | 0.5509 | 0.005870845032476312 | 0.02718074573721531 | 0.012442899978658842 |
| executor_refresh_time | 0.4051 | 323.0 | 1405.0 | 887.9 |
| cooldown_time | 0.8145 | 62.0 | 1114.0 | 486.3 |
| total_amount_quote | 0.1823 | 550.0003592568322 | 993.0105513881747 | 810.3547680612 |

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
| recent_objective | > 0 | -0.01924905899033148 | FAIL |
| recent_pnl | >= 0 | -0.5891341156543084 | FAIL |
| recent_trades | >= 5 | 156 | PASS |
| worst_stress | > -10 | -0.14038400196151873 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.023638625550711174 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.14038400196151873 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.01924905899033148, pnl=-0.5891341156543084, trades=156, reason=recent objective score -0.0192 <= 0; recent PnL -0.5891% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.330406700764818 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0192 <= 0; recent PnL -0.5891% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T10:39:38.769349+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 8077
