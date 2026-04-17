# PMM Dynamic Optimization Report: nonkyc_NKYC-USDT_5m_sweep_v1

Generated: 2026-04-09 22:32:38 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T22:32:38.935578+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 5182 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: NKYC-USDT
- **interval**: 5m
- **n_candles**: 52059
- **dataset_hash**: 6a01a21894e1a374df873999d46ae2363a14a821bb0f91fcbddaf0a25addb112
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 736.080862479191
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.4288079149738326 |
| buy_n_levels | 10 |
| buy_side_weight | 0.2504757989316152 |
| buy_spread_base | 4.255890399834412 |
| buy_spread_ratio | 1.4273552068594213 |
| cooldown_time | 7071 |
| executor_refresh_time | 7058 |
| macd_fast | 14 |
| macd_signal | 26 |
| macd_slow | 64 |
| natr_length | 31 |
| sell_n_levels | 2 |
| sell_spread_base | 5.418139774550164 |
| sell_spread_ratio | 1.2126081981845886 |
| stop_loss | 0.01473867692166903 |
| take_profit | 0.005010646644858754 |
| time_limit | 19569 |
| total_amount_quote | 736.080862479191 |
| trailing_stop_activation | 0.09903631711380184 |
| trailing_stop_delta | 0.006803016580718891 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 736.080862479191 |
| Selected | 736.080862479191 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -4.5648
- **Net PnL (quote)**: -33.6005
- **Sharpe Ratio**: -11.1884
- **Max Drawdown %**: 4.5657
- **Profit Factor**: 0.3134791680853489
- **Trade Count**: 885
- **Total Fees (quote)**: 20.2164
- **Maker Fees**: 14.2606
- **Taker Fees**: 5.9558
- **Fee Drag %**: 2.7465
- **TP Min-Notional Failures**: 1969 :warning:
  > 1969 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1023
- **PnL Component**: -0.0467
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0342
- **Fee Drag Component**: -0.0137
- **Inventory Component**: -0.0076
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0173**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.48 | -9.97 | 0.55 | 76 | -0.0163 | n/a |
| 1 | -0.58 | -10.78 | 0.65 | 69 | -0.0183 | n/a |
| 2 | -0.15 | -4.66 | 0.22 | 63 | -0.0117 | n/a |
| 3 | 0.01 | 0.42 | 0.12 | 68 | -0.0078 | n/a |
| 4 | -0.89 | -15.89 | 0.94 | 102 | -0.0426 | n/a |
| 5 | -0.87 | -15.67 | 0.89 | 102 | -0.0236 | n/a |
| 6 | -0.43 | -5.42 | 0.48 | 84 | -0.0154 | n/a |
| 7 | -0.18 | -5.42 | 0.19 | 72 | -0.0103 | n/a |
| 8 | -0.44 | -7.89 | 0.60 | 58 | -0.0127 | n/a |

## Stress Test Results

Worst Scenario: **very_thin_book** (score: -0.2133)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -5.94 | -14.01 | 5.94 | -0.1341 |
| fees_2x | -7.31 | -16.56 | 7.31 | -0.1661 |
| latency_plus1 | -4.56 | -11.19 | 4.57 | -0.1023 |
| latency_plus2 | -4.62 | -11.27 | 4.62 | -0.1043 |
| latency_plus3 | -4.58 | -11.24 | 4.58 | -0.1027 |
| low_liquidity | -4.84 | -11.58 | 4.84 | -0.1083 |
| very_low_liquidity | -5.53 | -13.06 | 5.53 | -0.1218 |
| high_slippage | -4.77 | -11.55 | 4.77 | -0.1060 |
| extreme_slippage | -5.17 | -12.24 | 5.17 | -0.1133 |
| combined_adverse | -6.47 | -14.76 | 6.47 | -0.1449 |
| spread_widen_10bps | -5.56 | -12.17 | 5.56 | -0.1230 |
| spread_widen_25bps | -6.48 | -15.04 | 6.50 | -0.1398 |
| thin_book | -6.14 | -14.84 | 6.14 | -0.1294 |
| very_thin_book | -5.94 | -13.61 | 5.95 | -0.2133 |
| entry_spread_stress | -5.60 | -13.48 | 5.63 | -0.1225 |
| combined_market_deterioration | -8.12 | -18.55 | 8.12 | -0.1733 |
| severe_adverse | -10.12 | -23.25 | 10.12 | -0.2130 |

## Holdout Validation

- **Holdout bars**: 8798
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0028)
- **Trend**: ranging (efficiency: 0.0006)
- **Best holdout score**: 0.0049 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1578 | -0.0238 | -0.83 | 0.86 | 169 |
| 1 | -0.0120 | -0.0704 | -1.75 | 2.70 | 574 |
| 2 | -0.0125 | 0.0049 | 4.33 | 1.68 | 306 |
| 3 | -0.0128 | -0.0151 | 1.25 | 1.35 | 304 |
| 4 | -0.0128 | -0.0528 | -1.93 | 1.98 | 357 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52059
- **Expected rows**: 52059
- **Missing rows**: 0
- **Forward-fill count**: 55
- **Forward-fill fraction**: 0.0010564935938070267
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0131 <= 0; recent PnL -0.4462% < 0
- **Objective score**: -0.013062814860643403
- **PnL %**: -0.44617949399343765
- **Trade count**: 78

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1201 <= 0
- **Objective score**: -0.1201458548856728
- **PnL %**: 0.048983757174624075
- **Trade count**: 20

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1761 <= 0
- **Objective score**: -0.1760714241134183
- **PnL %**: 0.005723802454670277
- **Trade count**: 6

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.12078339282943071
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1217, -0.1350 |
| sell_spread_base | -0.1238, -0.1352 |
| stop_loss | -0.1201, -0.1224 |
| take_profit | -0.1405, -0.1296 |
| executor_refresh_time | -0.1563, -0.1409 |
| cooldown_time | -0.1467, -0.1288 |
| total_amount_quote | -0.1227, -0.1212 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2092425902943285
- **Max CV**: 0.6887618649010462
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0741 | 4.4436352580415 | 5.364943019341553 | 4.9194460743548625 |
| buy_spread_ratio | 0.0645 | 1.2298096962445644 | 1.484961702434104 | 1.3449551728274587 |
| sell_spread_base | 0.6888 | 0.5821926460469022 | 5.895326003601989 | 2.38146104555386 |
| sell_spread_ratio | 0.1758 | 1.2027723863873048 | 1.9201883338103167 | 1.5826617798998344 |
| buy_side_weight | 0.2929 | 0.2015827926872171 | 0.42391870621848854 | 0.28521060693699185 |
| amount_skew | 0.1732 | 1.2333937065230711 | 2.0389240093021437 | 1.4059569823899827 |
| stop_loss | 0.2643 | 0.010140865073377508 | 0.021289238127798957 | 0.014682328970917475 |
| take_profit | 0.1057 | 0.005077930041225823 | 0.006730002313069076 | 0.005744666213869879 |
| executor_refresh_time | 0.2170 | 6868.0 | 14155.0 | 11127.1 |
| cooldown_time | 0.0710 | 5546.0 | 7032.0 | 6594.4 |
| total_amount_quote | 0.1745 | 642.2641355339056 | 990.0039182350433 | 778.9439449706919 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
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
| recent_objective | > 0 | -0.013062814860643403 | FAIL |
| recent_pnl | >= 0 | -0.44617949399343765 | FAIL |
| recent_trades | >= 5 | 78 | PASS |
| worst_stress | > -10 | -0.2133209008380813 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.023813639136942177 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_thin_book score=-0.2133209008380813 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.013062814860643403, pnl=-0.44617949399343765, trades=78, reason=recent objective score -0.0131 <= 0; recent PnL -0.4462% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.1201458548856728, pnl=0.048983757174624075, trades=20, reason=recent objective score -0.1201 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.1760714241134183, pnl=0.005723802454670277, trades=6, reason=recent objective score -0.1761 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2092425902943285 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52059 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0131 <= 0; recent PnL -0.4462% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1201 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1761 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52059
- **Pre-release bars**: 43994
- **Dev bars**: 35196
- **Holdout bars**: 8798
- **Recent 28d bars**: 8065
- **Recent window start**: 1773338400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T22:32:38.935578+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 5182
