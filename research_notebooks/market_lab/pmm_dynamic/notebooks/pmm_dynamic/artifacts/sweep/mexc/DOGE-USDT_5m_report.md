# PMM Dynamic Optimization Report: mexc_DOGE-USDT_5m_sweep_v1

Generated: 2026-03-28 11:02:01 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T11:02:01.305004+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 5909 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOGE-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 706dbb336931f070fdf30cd13d19cb6ac5192c42b6d5b4d57949bbd0d86cdbbe
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 306.640085249094
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.539048559060434 |
| buy_n_levels | 5 |
| buy_side_weight | 0.43105031670017524 |
| buy_spread_base | 0.3407879830341016 |
| buy_spread_ratio | 1.4669672387215864 |
| cooldown_time | 70 |
| executor_refresh_time | 1180 |
| macd_fast | 31 |
| macd_signal | 6 |
| macd_slow | 52 |
| natr_length | 16 |
| sell_n_levels | 9 |
| sell_spread_base | 0.5535099997047158 |
| sell_spread_ratio | 1.2267478213901337 |
| stop_loss | 0.24510493952282125 |
| take_profit | 0.06071216734530744 |
| time_limit | 135240 |
| total_amount_quote | 306.640085249094 |
| trailing_stop_activation | 0.02426016391739547 |
| trailing_stop_delta | 0.0010572871793806911 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 306.640085249094 |
| Selected | 306.640085249094 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2426.2608
- **Net PnL (quote)**: 7439.8882
- **Sharpe Ratio**: 6.6957
- **Max Drawdown %**: 18.0250
- **Profit Factor**: 1.732117653404181
- **Trade Count**: 22676
- **Total Fees (quote)**: 419.0816
- **Maker Fees**: 212.4776
- **Taker Fees**: 206.6040
- **Fee Drag %**: 136.6689

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.1559
- **PnL Component**: 3.2293
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1352
- **Fee Drag Component**: -0.6833
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.7684**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 348.74 | 39.54 | 8.28 | 2239 | 1.1207 | n/a |
| 1 | 242.01 | 35.46 | 8.05 | 2168 | 0.8553 | n/a |
| 2 | 277.91 | 39.82 | 4.88 | 2161 | 0.9784 | n/a |
| 3 | 145.81 | 41.80 | 8.20 | 2132 | 0.5266 | n/a |
| 4 | 236.64 | 12.64 | 8.55 | 2205 | 0.8350 | n/a |
| 5 | 319.38 | 35.29 | 10.82 | 2296 | 1.0335 | n/a |
| 6 | 211.22 | 23.72 | 11.81 | 2192 | 0.7302 | n/a |
| 7 | 196.86 | 32.07 | 6.94 | 1962 | 0.7271 | n/a |
| 8 | 183.37 | 36.62 | 4.11 | 2012 | 0.7017 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.0902)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2384.87 | 5.17 | 18.44 | 1.7968 |
| fees_2x | 2330.00 | 5.50 | 18.75 | 1.4356 |
| latency_plus1 | 2163.68 | 7.05 | 17.98 | 2.1043 |
| latency_plus2 | 1846.77 | 6.59 | 18.70 | 2.0277 |
| latency_plus3 | 1458.58 | 6.38 | 17.32 | 1.9157 |
| low_liquidity | 2426.26 | 6.70 | 18.03 | 2.1559 |
| very_low_liquidity | 2415.63 | 6.69 | 18.03 | 2.1513 |
| high_slippage | 2314.35 | 6.51 | 18.45 | 2.1110 |
| extreme_slippage | 2131.29 | 4.99 | 18.88 | 2.0407 |
| combined_adverse | 2025.50 | 5.37 | 18.57 | 1.7326 |
| spread_widen_10bps | 2352.78 | 5.48 | 18.61 | 2.1173 |
| spread_widen_25bps | 2107.47 | 4.86 | 17.80 | 2.0291 |
| thin_book | 1478.54 | 7.47 | 17.84 | 1.9744 |
| very_thin_book | 626.58 | 5.36 | 18.40 | 1.4156 |
| entry_spread_stress | 2223.01 | 5.57 | 18.93 | 2.0704 |
| combined_market_deterioration | 1664.13 | 5.31 | 19.11 | 1.7155 |
| severe_adverse | 559.29 | 4.80 | 20.21 | 1.0902 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0037)
- **Trend**: ranging (efficiency: 0.0188)
- **Best holdout score**: 1.7450 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.6230 | 1.3419 | 542.47 | 16.53 | 4819 |
| 1 | 1.1894 | 1.7450 | 971.34 | 16.19 | 4418 |
| 2 | 1.1807 | 1.6136 | 783.82 | 15.59 | 4196 |
| 3 | 1.1729 | 1.6187 | 804.89 | 16.43 | 4596 |
| 4 | 1.1472 | 1.5951 | 792.31 | 14.57 | 4928 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 37
- **Forward-fill fraction**: 0.0007137208001388862
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.106576241034177
- **PnL %**: 363.3720511586375
- **Trade count**: 4127

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.6955839619202335
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.7078, 1.6789 |
| sell_spread_base | 1.6900, 1.6704 |
| stop_loss | 1.7056, 1.6950 |
| take_profit | 1.7000, 1.6898 |
| executor_refresh_time | 1.6604, 1.6956 |
| cooldown_time | 1.6956, 1.6956 |
| total_amount_quote | 1.6918, 1.6944 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.31042419573963365
- **Max CV**: 0.4822364834843739
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.4275 | 0.20468736671035506 | 0.667700962306922 | 0.3702586771713965 |
| buy_spread_ratio | 0.1627 | 1.2015349916478109 | 1.9116957941033583 | 1.4377850231506928 |
| sell_spread_base | 0.2280 | 0.20250823155891629 | 0.40766133278787053 | 0.2767260823089315 |
| sell_spread_ratio | 0.1695 | 1.238255833056348 | 2.0311474363201327 | 1.6622881636424105 |
| buy_side_weight | 0.1980 | 0.25474068268829586 | 0.5736940456045734 | 0.4543385855418922 |
| amount_skew | 0.1747 | 2.2523717138909474 | 3.8990962113501757 | 3.310215565976583 |
| stop_loss | 0.4133 | 0.03937332990682713 | 0.19728309051963316 | 0.12123829050982984 |
| take_profit | 0.4747 | 0.02407613346752033 | 0.14587318533963425 | 0.07323467008415203 |
| executor_refresh_time | 0.2627 | 353.0 | 799.0 | 502.3 |
| cooldown_time | 0.4822 | 67.0 | 244.0 | 129.7 |
| total_amount_quote | 0.4213 | 42.805226656448134 | 144.56047977793992 | 80.21501639803263 |

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
| recent_objective | > 0 | 1.106576241034177 | PASS |
| recent_pnl | >= 0 | 363.3720511586375 | PASS |
| recent_trades | >= 5 | 4127 | PASS |
| worst_stress | > -10 | 1.0901920073960008 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.3419 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.0901920073960008 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.106576241034177, pnl=363.3720511586375, trades=4127, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.31042419573963365 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
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
- **run_timestamp**: 2026-03-28T11:02:01.305004+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 5909
