# PMM Dynamic Optimization Report: mexc_ATOM-USDT_5m_sweep_v1

Generated: 2026-03-28 07:50:12 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T07:50:12.873649+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 7083 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ATOM-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 2e1ebb140701e8c2d063a861b0f88534e1883013de5e713b1d17b10f8fe3164d
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 982.3077599125742
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.936785927965344 |
| buy_n_levels | 7 |
| buy_side_weight | 0.37765772779933054 |
| buy_spread_base | 1.6440967190857814 |
| buy_spread_ratio | 2.6222441141492494 |
| cooldown_time | 5473 |
| executor_refresh_time | 10575 |
| macd_fast | 5 |
| macd_signal | 18 |
| macd_slow | 75 |
| natr_length | 37 |
| sell_n_levels | 9 |
| sell_spread_base | 4.296889232740751 |
| sell_spread_ratio | 2.267667665673481 |
| stop_loss | 0.012272317873964066 |
| take_profit | 0.045439951138138486 |
| time_limit | 36139 |
| total_amount_quote | 982.3077599125742 |
| trailing_stop_activation | 0.0026547019680846573 |
| trailing_stop_delta | 0.0012187704108621972 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 982.3077599125742 |
| Selected | 982.3077599125742 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.0822
- **Net PnL (quote)**: -0.8076
- **Sharpe Ratio**: -0.1503
- **Max Drawdown %**: 1.1669
- **Profit Factor**: 0.9802370537284385
- **Trade Count**: 706
- **Total Fees (quote)**: 5.6657
- **Maker Fees**: 2.8324
- **Taker Fees**: 2.8334
- **Fee Drag %**: 0.5768

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0150
- **PnL Component**: -0.0008
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0088
- **Fee Drag Component**: -0.0029
- **Inventory Component**: -0.0025
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0051**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.18 | -2.96 | 0.51 | 93 | -0.0086 | n/a |
| 1 | -0.12 | -2.90 | 0.27 | 76 | -0.0086 | n/a |
| 2 | 0.11 | 4.89 | 0.10 | 73 | -0.0024 | n/a |
| 3 | -0.04 | -2.34 | 0.15 | 51 | -0.0042 | n/a |
| 4 | 0.63 | 6.19 | 0.10 | 70 | 0.0027 | n/a |
| 5 | 0.07 | 1.54 | 0.27 | 103 | -0.0043 | n/a |
| 6 | -0.09 | -3.33 | 0.21 | 299 | -0.0052 | n/a |
| 7 | 0.11 | 4.36 | 0.12 | 83 | -0.0026 | n/a |
| 8 | 0.13 | 9.43 | 0.03 | 67 | -0.0016 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1190)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.37 | -0.71 | 1.29 | -0.0203 |
| fees_2x | -0.66 | -1.26 | 1.44 | -0.0258 |
| latency_plus1 | -0.09 | -0.16 | 1.17 | -0.0151 |
| latency_plus2 | -0.08 | -0.14 | 1.18 | -0.0150 |
| latency_plus3 | -0.26 | -0.50 | 1.36 | -0.0183 |
| low_liquidity | -0.08 | -0.15 | 1.17 | -0.0150 |
| very_low_liquidity | -0.90 | -1.83 | 1.16 | -0.0283 |
| high_slippage | -0.80 | -1.54 | 1.55 | -0.0252 |
| extreme_slippage | -2.25 | -4.28 | 2.68 | -0.0551 |
| combined_adverse | -1.10 | -2.10 | 1.78 | -0.0313 |
| spread_widen_10bps | -1.12 | -2.27 | 1.24 | -0.0310 |
| spread_widen_25bps | -2.18 | -4.58 | 2.23 | -0.0467 |
| thin_book | -1.97 | -0.52 | 4.74 | -0.0629 |
| very_thin_book | -3.43 | -1.00 | 4.36 | -0.0719 |
| entry_spread_stress | -1.51 | -2.83 | 1.88 | -0.0374 |
| combined_market_deterioration | -2.95 | -0.49 | 7.07 | -0.0896 |
| severe_adverse | -5.59 | -9.73 | 5.61 | -0.1190 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0039)
- **Trend**: ranging (efficiency: 0.0112)
- **Best holdout score**: 0.0016 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0670 | -0.0034 | 0.16 | 0.24 | 399 |
| 1 | 0.0006 | 0.0016 | 0.88 | 0.36 | 162 |
| 2 | -0.0002 | 0.0004 | 0.22 | 0.14 | 162 |
| 3 | -0.0003 | 0.0001 | 0.40 | 0.15 | 204 |
| 4 | -0.0004 | -0.0009 | 0.05 | 0.11 | 171 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 2
- **Forward-fill fraction**: 3.8579502710210066e-05
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0098 <= 0; recent PnL -0.0293% < 0
- **Objective score**: -0.009829333538611824
- **PnL %**: -0.029346967710157774
- **Trade count**: 192

## Sensitivity Analysis

- **Sensitivity penalty**: 0.35714285714285715
- **Baseline score**: -0.016601239295850556
- **Sign flips**: 0
- **Collapse count**: 5
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0956, -0.0147 |
| sell_spread_base | -0.0170, -0.0189 |
| stop_loss | -0.0124, -0.0305 |
| take_profit | -0.0166, -0.0166 |
| executor_refresh_time | -0.0398, -0.0166 |
| cooldown_time | -0.0134, -0.0189 |
| total_amount_quote | -0.0459, -0.0444 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.34653074899579617
- **Max CV**: 0.7716782485108443
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: stop_loss, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2648 | 1.2748723566437272 | 2.9048395170673076 | 1.824819161908954 |
| buy_spread_ratio | 0.1777 | 1.6745427525078873 | 2.915189480995654 | 2.4430440034178185 |
| sell_spread_base | 0.4874 | 1.5541051928552465 | 5.883381716594586 | 3.11511141642409 |
| sell_spread_ratio | 0.2506 | 1.3920652824367408 | 2.849707821615223 | 2.174232742576175 |
| buy_side_weight | 0.3112 | 0.2194127643577578 | 0.5505507892019178 | 0.37138179487987005 |
| amount_skew | 0.1928 | 1.8187959061835306 | 3.8482004819062543 | 3.2986004725960547 |
| stop_loss | 0.5715 | 0.01048926798850648 | 0.04311376541247773 | 0.01965865026459282 |
| take_profit | 0.7717 | 0.0050658218738922015 | 0.06750848551506332 | 0.029972720471384662 |
| executor_refresh_time | 0.3337 | 2895.0 | 13387.0 | 9077.2 |
| cooldown_time | 0.2518 | 3478.0 | 6935.0 | 5053.4 |
| total_amount_quote | 0.1987 | 553.9700038661704 | 974.6184665234364 | 775.1383117131089 |

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
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.009829333538611824 | FAIL |
| recent_pnl | >= 0 | -0.029346967710157774 | FAIL |
| recent_trades | >= 5 | 192 | PASS |
| worst_stress | > -10 | -0.1189635129870554 | PASS |
| sensitivity_penalty | < 0.50 | 0.35714285714285715 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.0033960212701299166 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.1189635129870554 |
| sensitivity | PASS | penalty=0.35714285714285715 |
| recent_28d | FAIL | score=-0.009829333538611824, pnl=-0.029346967710157774, trades=192, reason=recent objective score -0.0098 <= 0; recent PnL -0.0293% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.34653074899579617 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0098 <= 0; recent PnL -0.0293% < 0 |
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
- **run_timestamp**: 2026-03-28T07:50:12.873649+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 7083
