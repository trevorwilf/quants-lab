# PMM Dynamic Optimization Report: nonkyc_DOGE-USDT_5m_sweep_v1

Generated: 2026-03-29 08:15:46 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T08:15:46.225915+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 7247 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: DOGE-USDT
- **interval**: 5m
- **n_candles**: 51843
- **dataset_hash**: 16ba8682bd47266965875ba081f8ca1b0e7cff2e85d4110f4cf36e2d3396b5e3
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 961.4498216316956
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.803800192714752 |
| buy_n_levels | 7 |
| buy_side_weight | 0.20548817307005304 |
| buy_spread_base | 3.2271381314014715 |
| buy_spread_ratio | 2.2559345518664786 |
| cooldown_time | 447 |
| executor_refresh_time | 4007 |
| macd_fast | 23 |
| macd_signal | 20 |
| macd_slow | 25 |
| natr_length | 47 |
| sell_n_levels | 9 |
| sell_spread_base | 5.337437947834534 |
| sell_spread_ratio | 1.4368828039872719 |
| stop_loss | 0.01242585420612838 |
| take_profit | 0.006066016458271146 |
| time_limit | 49136 |
| total_amount_quote | 961.4498216316956 |
| trailing_stop_activation | 0.0016875679813453306 |
| trailing_stop_delta | 0.026603825686539295 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 961.4498216316956 |
| Selected | 961.4498216316956 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.8551
- **Net PnL (quote)**: -17.8354
- **Sharpe Ratio**: -0.5361
- **Max Drawdown %**: 4.0999
- **Profit Factor**: 0.37611201912663617
- **Trade Count**: 649
- **Total Fees (quote)**: 10.8588
- **Maker Fees**: 7.1014
- **Taker Fees**: 3.7574
- **Fee Drag %**: 1.1294

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0573
- **PnL Component**: -0.0187
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0307
- **Fee Drag Component**: -0.0056
- **Inventory Component**: -0.0021
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0071**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.23 | -10.32 | 0.27 | 71 | -0.0065 | n/a |
| 1 | -0.19 | -9.49 | 0.22 | 76 | -0.0057 | n/a |
| 2 | -0.15 | -8.46 | 0.19 | 75 | -0.0065 | n/a |
| 3 | -0.14 | -6.54 | 0.20 | 97 | -0.0067 | n/a |
| 4 | -0.19 | -4.08 | 0.28 | 78 | -0.0077 | n/a |
| 5 | -0.35 | -14.46 | 0.40 | 117 | -0.0111 | n/a |
| 6 | -0.15 | -11.91 | 0.16 | 69 | -0.0048 | n/a |
| 7 | -0.24 | -10.71 | 0.26 | 92 | -0.0066 | n/a |
| 8 | -0.06 | -6.51 | 0.07 | 32 | -0.0748 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0861)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.42 | -0.72 | 4.14 | -0.0662 |
| fees_2x | -2.98 | -0.90 | 4.19 | -0.0752 |
| latency_plus1 | -1.88 | -0.54 | 4.10 | -0.0575 |
| latency_plus2 | -1.97 | -0.57 | 4.10 | -0.0584 |
| latency_plus3 | -2.00 | -0.58 | 4.10 | -0.0586 |
| low_liquidity | -2.00 | -0.58 | 4.10 | -0.0579 |
| very_low_liquidity | -2.13 | -0.68 | 3.93 | -0.0579 |
| high_slippage | -1.95 | -0.57 | 4.11 | -0.0583 |
| extreme_slippage | -2.15 | -0.63 | 4.12 | -0.0604 |
| combined_adverse | -2.67 | -0.80 | 4.15 | -0.0684 |
| spread_widen_10bps | -2.19 | -0.61 | 4.33 | -0.0630 |
| spread_widen_25bps | -2.63 | -0.76 | 4.26 | -0.0687 |
| thin_book | -1.64 | -0.58 | 3.38 | -0.0475 |
| very_thin_book | 0.15 | 0.33 | 0.72 | -0.0074 |
| entry_spread_stress | -2.38 | -0.68 | 4.26 | -0.0659 |
| combined_market_deterioration | -2.47 | -1.41 | 2.73 | -0.0560 |
| severe_adverse | -1.57 | -3.13 | 2.38 | -0.0861 |

## Holdout Validation

- **Holdout bars**: 8763
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0036)
- **Trend**: ranging (efficiency: 0.0128)
- **Best holdout score**: -0.0089 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0717 | -0.0116 | -0.48 | 0.48 | 193 |
| 1 | -0.0059 | -0.0103 | -0.40 | 0.42 | 169 |
| 2 | -0.0060 | -0.0156 | -0.64 | 0.71 | 154 |
| 3 | -0.0061 | -0.0089 | -0.33 | 0.33 | 181 |
| 4 | -0.0063 | -0.0091 | -0.32 | 0.39 | 137 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51843
- **Expected rows**: 51881
- **Missing rows**: 38
- **Forward-fill count**: 67
- **Forward-fill fraction**: 0.0012923634820515787
- **Longest gap (seconds)**: 8100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0048 <= 0; recent PnL -0.1370% < 0
- **Objective score**: -0.00483326066299265
- **PnL %**: -0.1370091997474257
- **Trade count**: 87

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.06743539194631296
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0563, -0.0780 |
| sell_spread_base | -0.0660, -0.0676 |
| stop_loss | -0.0702, -0.0690 |
| take_profit | -0.0683, -0.0694 |
| executor_refresh_time | -0.0612, -0.0693 |
| cooldown_time | -0.0674, -0.0674 |
| total_amount_quote | -0.0681, -0.0666 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.23841629222647057
- **Max CV**: 0.7933953761724782
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0865 | 3.2271381314014715 | 4.17815750464396 | 3.6411419555626665 |
| buy_spread_ratio | 0.1182 | 1.7370910074515835 | 2.4231161585207492 | 2.1122421864021157 |
| sell_spread_base | 0.2901 | 2.4162702247605545 | 5.622354723223128 | 4.173354744244946 |
| sell_spread_ratio | 0.1229 | 1.2957195071663856 | 1.8880057612938281 | 1.5621031218055152 |
| buy_side_weight | 0.1037 | 0.20548817307005304 | 0.27092772848458047 | 0.22677536855380734 |
| amount_skew | 0.1298 | 2.0489865754028327 | 2.9836714057566223 | 2.5664370305116395 |
| stop_loss | 0.2081 | 0.010099655583882153 | 0.018079402616012968 | 0.013081681927180889 |
| take_profit | 0.1928 | 0.005005215353237593 | 0.008823854603253325 | 0.006057211163093922 |
| executor_refresh_time | 0.4876 | 2221.0 | 9530.0 | 5550.9 |
| cooldown_time | 0.7934 | 232.0 | 2632.0 | 931.8 |
| total_amount_quote | 0.0895 | 763.9602413105833 | 994.4405676148002 | 910.8868999835883 |

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
| recent_objective | > 0 | -0.00483326066299265 | FAIL |
| recent_pnl | >= 0 | -0.1370091997474257 | FAIL |
| recent_trades | >= 5 | 87 | PASS |
| worst_stress | > -10 | -0.08611513987403402 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.011589501579337722 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.08611513987403402 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.00483326066299265, pnl=-0.1370091997474257, trades=87, reason=recent objective score -0.0048 <= 0; recent PnL -0.1370% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.23841629222647057 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51843 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0048 <= 0; recent PnL -0.1370% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35053
- **Holdout bars**: 8763
- **Recent 28d bars**: 8027

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T08:15:46.225915+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 7247
