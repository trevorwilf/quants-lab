# PMM Dynamic Optimization Report: mexc_TON-USDT_5m_sweep_v1

Generated: 2026-04-09 09:28:59 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T09:28:59.478529+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 3520 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: TON-USDT
- **interval**: 5m
- **n_candles**: 51918
- **dataset_hash**: d525a7188e323aaeb0ef3cd70826267a0fb8de3b30ad3557013a051f744a74ba
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 982.779393476181
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.968613258356157 |
| buy_n_levels | 8 |
| buy_side_weight | 0.6156545554048326 |
| buy_spread_base | 1.6138880670912699 |
| buy_spread_ratio | 2.4753211973584026 |
| cooldown_time | 1398 |
| executor_refresh_time | 5781 |
| macd_fast | 18 |
| macd_signal | 23 |
| macd_slow | 20 |
| natr_length | 31 |
| sell_n_levels | 8 |
| sell_spread_base | 5.284746100539176 |
| sell_spread_ratio | 1.3634575348456806 |
| stop_loss | 0.01512947167371503 |
| take_profit | 0.005239140910087 |
| time_limit | 36732 |
| total_amount_quote | 982.779393476181 |
| trailing_stop_activation | 0.08087440828304254 |
| trailing_stop_delta | 0.044186870764835795 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 982.779393476181 |
| Selected | 982.779393476181 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.2985
- **Net PnL (quote)**: -2.9341
- **Sharpe Ratio**: -0.2177
- **Max Drawdown %**: 2.0064
- **Profit Factor**: 0.9476917324862301
- **Trade Count**: 889
- **Total Fees (quote)**: 5.8257
- **Maker Fees**: 5.1214
- **Taker Fees**: 0.7043
- **Fee Drag %**: 0.5928
- **TP Min-Notional Failures**: 3153 :warning:
  > 3153 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0284
- **PnL Component**: -0.0030
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0150
- **Fee Drag Component**: -0.0030
- **Inventory Component**: -0.0073
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0038**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.12 | -2.48 | 0.29 | 97 | -0.0055 | n/a |
| 1 | 0.04 | 1.72 | 0.10 | 84 | -0.0025 | n/a |
| 2 | -0.01 | -0.43 | 0.12 | 63 | -0.0031 | n/a |
| 3 | -0.01 | -0.52 | 0.13 | 98 | -0.0032 | n/a |
| 4 | -0.69 | -1.39 | 2.29 | 98 | -0.0265 | n/a |
| 5 | -0.16 | -2.42 | 0.33 | 102 | -0.0064 | n/a |
| 6 | 0.06 | 2.37 | 0.08 | 91 | -0.0021 | n/a |
| 7 | -0.14 | -3.89 | 0.27 | 85 | -0.0056 | n/a |
| 8 | 0.02 | 1.16 | 0.08 | 64 | -0.0025 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0845)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.59 | -0.45 | 2.02 | -0.0330 |
| fees_2x | -0.89 | -0.69 | 2.05 | -0.0377 |
| latency_plus1 | -0.50 | -0.38 | 2.01 | -0.0305 |
| latency_plus2 | -0.63 | -0.48 | 2.01 | -0.0317 |
| latency_plus3 | -0.67 | -0.51 | 2.01 | -0.0320 |
| low_liquidity | -0.30 | -0.22 | 2.01 | -0.0284 |
| very_low_liquidity | -0.30 | -0.22 | 2.01 | -0.0284 |
| high_slippage | -0.48 | -0.36 | 2.02 | -0.0303 |
| extreme_slippage | -0.84 | -0.65 | 2.05 | -0.0342 |
| combined_adverse | -0.98 | -0.76 | 2.09 | -0.0374 |
| spread_widen_10bps | -1.10 | -0.84 | 2.14 | -0.0375 |
| spread_widen_25bps | -3.06 | -1.94 | 4.07 | -0.0737 |
| thin_book | -2.50 | -3.12 | 2.61 | -0.0543 |
| very_thin_book | -2.31 | -4.77 | 2.36 | -0.0461 |
| entry_spread_stress | -1.59 | -1.03 | 2.61 | -0.0459 |
| combined_market_deterioration | -2.73 | -2.51 | 2.87 | -0.0608 |
| severe_adverse | -4.07 | -9.25 | 4.23 | -0.0845 |

## Holdout Validation

- **Holdout bars**: 8776
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0030)
- **Trend**: ranging (efficiency: 0.0020)
- **Best holdout score**: 0.0113 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0565 | -0.0051 | -0.05 | 0.29 | 189 |
| 1 | -0.0004 | -0.0036 | 0.43 | 0.57 | 188 |
| 2 | -0.0010 | 0.0113 | 1.82 | 0.41 | 288 |
| 3 | -0.0013 | -0.0017 | 0.50 | 0.11 | 165 |
| 4 | -0.0016 | -0.0225 | -0.34 | 0.83 | 411 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51918
- **Expected rows**: 51947
- **Missing rows**: 29
- **Forward-fill count**: 158
- **Forward-fill fraction**: 0.0030432605262144152
- **Longest gap (seconds)**: 6900

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0009 <= 0
- **Objective score**: -0.0009162162277897878
- **PnL %**: 0.17549847461194024
- **Trade count**: 140

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0021 <= 0
- **Objective score**: -0.002109394642324673
- **PnL %**: 0.04484676765566333
- **Trade count**: 76

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0783 <= 0
- **Objective score**: -0.07834413846821185
- **PnL %**: 0.004037305571441721
- **Trade count**: 31

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.03455063234290349
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0506, -0.0361 |
| sell_spread_base | -0.0487, -0.0382 |
| stop_loss | -0.0409, -0.0314 |
| take_profit | -0.0368, -0.0280 |
| executor_refresh_time | -0.0477, -0.0563 |
| cooldown_time | -0.0478, -0.0346 |
| total_amount_quote | -0.0337, -0.0337 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3872301022044438
- **Max CV**: 0.737784021763392
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1868 | 1.5887659737672535 | 2.9923121474692884 | 2.213875794705669 |
| buy_spread_ratio | 0.1492 | 1.4045984259343156 | 2.1373457566976044 | 1.7833759217142522 |
| sell_spread_base | 0.5464 | 0.4664590852934496 | 2.0083402706726665 | 0.9974558122523399 |
| sell_spread_ratio | 0.2216 | 1.4081853932737494 | 2.915247698648076 | 2.396946389817446 |
| buy_side_weight | 0.2434 | 0.289427685802542 | 0.7145641613118354 | 0.5360439488646701 |
| amount_skew | 0.1657 | 2.1271806883221918 | 3.9926965143642317 | 3.387467368546781 |
| stop_loss | 0.6803 | 0.011940751557090406 | 0.054085216372195266 | 0.02247038807461596 |
| take_profit | 0.6872 | 0.005056988465545818 | 0.033205285630609434 | 0.014519570634539907 |
| executor_refresh_time | 0.4763 | 755.0 | 12143.0 | 7376.2 |
| cooldown_time | 0.7378 | 89.0 | 2468.0 | 1044.8 |
| total_amount_quote | 0.1649 | 561.1260869606087 | 972.4349773999377 | 829.0316765054228 |

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
- walkforward_positive_majority: **FAIL**
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.0009162162277897878 | FAIL |
| recent_pnl | >= 0 | 0.17549847461194024 | PASS |
| recent_trades | >= 5 | 140 | PASS |
| worst_stress | > -10 | -0.08450230676263285 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.005061256412180902 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.08450230676263285 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.0009162162277897878, pnl=0.17549847461194024, trades=140, reason=recent objective score -0.0009 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.002109394642324673, pnl=0.04484676765566333, trades=76, reason=recent objective score -0.0021 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.07834413846821185, pnl=0.004037305571441721, trades=31, reason=recent objective score -0.0783 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3872301022044438 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51918 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0009 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0021 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0783 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51918
- **Pre-release bars**: 43882
- **Dev bars**: 35106
- **Holdout bars**: 8776
- **Recent 28d bars**: 8036
- **Recent window start**: 1773304200

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T09:28:59.478529+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 3520
