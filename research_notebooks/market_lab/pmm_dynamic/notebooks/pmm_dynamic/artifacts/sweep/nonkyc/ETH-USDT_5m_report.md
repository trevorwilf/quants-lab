# PMM Dynamic Optimization Report: nonkyc_ETH-USDT_5m_sweep_v1

Generated: 2026-03-29 09:59:59 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T09:59:59.277274+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 1750 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ETH-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 05179aef5a600187bc16ea0496be54fb97a5eab0255cac76d8dd7357f138b71b
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 806.5761619879117
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.1993109159914566 |
| buy_n_levels | 9 |
| buy_side_weight | 0.3411452378190374 |
| buy_spread_base | 4.041821999735279 |
| buy_spread_ratio | 1.7276731855179026 |
| cooldown_time | 107 |
| executor_refresh_time | 2067 |
| macd_fast | 28 |
| macd_signal | 29 |
| macd_slow | 30 |
| natr_length | 44 |
| sell_n_levels | 7 |
| sell_spread_base | 5.837183508441587 |
| sell_spread_ratio | 2.4152630879688775 |
| stop_loss | 0.017069942683737294 |
| take_profit | 0.0061864987504326755 |
| time_limit | 93058 |
| total_amount_quote | 806.5761619879117 |
| trailing_stop_activation | 0.04707623615004579 |
| trailing_stop_delta | 0.0015008112610647832 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 806.5761619879117 |
| Selected | 806.5761619879117 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 0.5938
- **Net PnL (quote)**: 4.7894
- **Sharpe Ratio**: 0.3505
- **Max Drawdown %**: 1.7433
- **Profit Factor**: 1.1850275464906066
- **Trade Count**: 525
- **Total Fees (quote)**: 14.7333
- **Maker Fees**: 10.4967
- **Taker Fees**: 4.2366
- **Fee Drag %**: 1.8266

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0256
- **PnL Component**: 0.0059
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0131
- **Fee Drag Component**: -0.0091
- **Inventory Component**: -0.0092
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0174**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.21 | -11.65 | 0.24 | 42 | -0.0382 | n/a |
| 1 | 1.12 | 2.44 | 0.77 | 62 | -0.0058 | n/a |
| 2 | -0.39 | -9.61 | 0.50 | 61 | -0.0145 | n/a |
| 3 | 0.25 | 6.79 | 0.15 | 69 | -0.0091 | n/a |
| 4 | -0.11 | -2.78 | 0.27 | 81 | -0.0135 | n/a |
| 5 | -0.72 | -7.65 | 0.79 | 86 | -0.0228 | n/a |
| 6 | -0.16 | -7.45 | 0.17 | 52 | -0.0053 | n/a |
| 7 | -0.30 | -4.94 | 0.56 | 80 | -0.0107 | n/a |
| 8 | -0.09 | -5.60 | 0.14 | 22 | -0.1200 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus3** (score: -0.0665)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.32 | -0.15 | 2.26 | -0.0432 |
| fees_2x | -1.23 | -0.65 | 2.78 | -0.0609 |
| latency_plus1 | 0.57 | 0.33 | 1.75 | -0.0247 |
| latency_plus2 | -0.61 | -0.38 | 1.80 | -0.0363 |
| latency_plus3 | -2.56 | -4.24 | 3.20 | -0.0665 |
| low_liquidity | 0.59 | 0.35 | 1.74 | -0.0256 |
| very_low_liquidity | 0.59 | 0.35 | 1.74 | -0.0256 |
| high_slippage | 0.46 | 0.28 | 1.81 | -0.0274 |
| extreme_slippage | 0.20 | 0.14 | 1.94 | -0.0310 |
| combined_adverse | -0.47 | -0.23 | 2.33 | -0.0438 |
| spread_widen_10bps | 0.22 | 0.15 | 1.93 | -0.0305 |
| spread_widen_25bps | -0.44 | -0.21 | 2.32 | -0.0429 |
| thin_book | -2.05 | -3.68 | 2.59 | -0.0532 |
| very_thin_book | -0.80 | -1.17 | 1.47 | -0.0229 |
| entry_spread_stress | -0.08 | -0.02 | 2.00 | -0.0341 |
| combined_market_deterioration | -2.02 | -1.97 | 3.03 | -0.0581 |
| severe_adverse | -2.06 | -2.98 | 2.74 | -0.0497 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0035)
- **Trend**: ranging (efficiency: 0.0227)
- **Best holdout score**: -0.0102 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0460 | -0.0184 | -0.77 | 0.80 | 160 |
| 1 | -0.0071 | -0.0102 | -0.35 | 0.41 | 116 |
| 2 | -0.0072 | -0.0229 | -0.85 | 0.89 | 288 |
| 3 | -0.0076 | -0.0131 | -0.54 | 0.54 | 137 |
| 4 | -0.0086 | -0.0103 | -0.39 | 0.39 | 150 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 128
- **Forward-fill fraction**: 0.0024690881734534442
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0165 <= 0; recent PnL -0.3753% < 0
- **Objective score**: -0.016517389574079874
- **PnL %**: -0.3752657384698328
- **Trade count**: 77

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.0579050974943116
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0421, -0.0617 |
| sell_spread_base | -0.0514, -0.0682 |
| stop_loss | -0.0740, -0.0578 |
| take_profit | -0.0570, -0.0786 |
| executor_refresh_time | -0.0877, -0.0579 |
| cooldown_time | -0.0579, -0.0579 |
| total_amount_quote | -0.0579, -0.0580 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.271789812371088
- **Max CV**: 0.6480968301403347
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, total_amount_quote
- **Scattered params**: executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1056 | 3.4214047812930763 | 4.94333558989277 | 3.96103449667389 |
| buy_spread_ratio | 0.1401 | 1.7084125636354217 | 2.802526368745336 | 2.164308851272027 |
| sell_spread_base | 0.4264 | 1.252823679343914 | 4.981022798223769 | 3.4042311372405885 |
| sell_spread_ratio | 0.1596 | 1.3853049170733123 | 2.4575662737291 | 1.9519840799457264 |
| buy_side_weight | 0.2920 | 0.20375633748200664 | 0.44949244999136306 | 0.3031901434160868 |
| amount_skew | 0.1869 | 2.1463534721946367 | 3.864933554221616 | 3.0994953173002657 |
| stop_loss | 0.2245 | 0.01006700093920046 | 0.018495704379068934 | 0.012008297951105843 |
| take_profit | 0.1698 | 0.005032302454428335 | 0.008300779667424004 | 0.006085261081704718 |
| executor_refresh_time | 0.5627 | 2484.0 | 12797.0 | 6985.1 |
| cooldown_time | 0.6481 | 76.0 | 7181.0 | 3451.5 |
| total_amount_quote | 0.0741 | 804.5437207575245 | 995.4486194814892 | 930.6636219332055 |

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
| recent_objective | > 0 | -0.016517389574079874 | FAIL |
| recent_pnl | >= 0 | -0.3752657384698328 | FAIL |
| recent_trades | >= 5 | 77 | PASS |
| worst_stress | > -10 | -0.06652606442485703 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.01841971674122859 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus3 score=-0.06652606442485703 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.016517389574079874, pnl=-0.3752657384698328, trades=77, reason=recent objective score -0.0165 <= 0; recent PnL -0.3753% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.271789812371088 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0165 <= 0; recent PnL -0.3753% < 0 |
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
- **run_timestamp**: 2026-03-29T09:59:59.277274+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 1750
