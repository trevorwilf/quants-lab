# PMM Dynamic Optimization Report: nonkyc_SAL-USDT_5m_retest_20260408

Generated: 2026-04-08 12:15:38 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T12:15:38.086980+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 11943 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: SAL-USDT
- **interval**: 5m
- **n_candles**: 51902
- **dataset_hash**: 5c7697af50eec9cab952453add0ee40863e464477e2032367e78b414e3075409
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 906.3492924620635
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.3066244956928954 |
| buy_n_levels | 10 |
| buy_side_weight | 0.2968453198860069 |
| buy_spread_base | 3.964093792687932 |
| buy_spread_ratio | 1.7507561884579654 |
| cooldown_time | 3936 |
| executor_refresh_time | 10205 |
| macd_fast | 41 |
| macd_signal | 14 |
| macd_slow | 45 |
| natr_length | 30 |
| sell_n_levels | 7 |
| sell_spread_base | 4.941118512178045 |
| sell_spread_ratio | 2.912586136375291 |
| stop_loss | 0.22346770679297653 |
| take_profit | 0.14199691732768444 |
| time_limit | 114069 |
| total_amount_quote | 906.3492924620635 |
| trailing_stop_activation | 0.023423679428314276 |
| trailing_stop_delta | 0.0011623898975065957 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 906.3492924620635 |
| Selected | 906.3492924620635 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 31.5291
- **Net PnL (quote)**: 285.7636
- **Sharpe Ratio**: 5.5749
- **Max Drawdown %**: 3.5783
- **Profit Factor**: 3.958978997390162
- **Trade Count**: 1000
- **Total Fees (quote)**: 30.2300
- **Maker Fees**: 10.0495
- **Taker Fees**: 20.1805
- **Fee Drag %**: 3.3354

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.2162
- **PnL Component**: 0.2741
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0268
- **Fee Drag Component**: -0.0167
- **Inventory Component**: -0.0138
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0100**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.31 | 2.56 | 0.30 | 57 | -0.0015 | n/a |
| 1 | 0.01 | 0.30 | 0.20 | 22 | -0.1725 | n/a |
| 2 | 1.26 | 3.11 | 2.02 | 71 | -0.0052 | n/a |
| 3 | 0.21 | 1.60 | 0.41 | 64 | -0.0035 | n/a |
| 4 | 1.62 | 5.12 | 0.90 | 74 | 0.0043 | n/a |
| 5 | 0.28 | 4.48 | 0.27 | 55 | -0.0014 | n/a |
| 6 | -0.25 | -3.09 | 0.71 | 60 | -0.0262 | n/a |
| 7 | -0.32 | -4.77 | 0.56 | 59 | -0.0406 | n/a |
| 8 | 0.38 | 1.39 | 0.78 | 71 | -0.0471 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 0.0634)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 29.86 | 5.32 | 3.59 | 0.1948 |
| fees_2x | 28.19 | 5.07 | 3.61 | 0.1732 |
| latency_plus1 | 30.46 | 5.21 | 3.58 | 0.2081 |
| latency_plus2 | 30.32 | 5.20 | 3.58 | 0.2071 |
| latency_plus3 | 30.84 | 5.33 | 3.58 | 0.2113 |
| low_liquidity | 26.49 | 5.20 | 2.64 | 0.1864 |
| very_low_liquidity | 16.18 | 3.77 | 3.98 | 0.0969 |
| high_slippage | 30.97 | 5.49 | 3.58 | 0.2119 |
| extreme_slippage | 29.86 | 5.33 | 3.58 | 0.2032 |
| combined_adverse | 24.20 | 4.81 | 2.71 | 0.1601 |
| spread_widen_10bps | 30.45 | 5.34 | 3.59 | 0.2064 |
| spread_widen_25bps | 31.32 | 5.49 | 3.62 | 0.2126 |
| thin_book | 21.63 | 4.54 | 3.08 | 0.1482 |
| very_thin_book | 13.53 | 3.76 | 2.71 | 0.0886 |
| entry_spread_stress | 32.19 | 5.59 | 3.60 | 0.2194 |
| combined_market_deterioration | 22.99 | 4.78 | 2.79 | 0.1494 |
| severe_adverse | 12.32 | 2.96 | 2.42 | 0.0634 |

## Holdout Validation

- **Holdout bars**: 8767
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0082)
- **Trend**: ranging (efficiency: 0.0009)
- **Best holdout score**: -0.0039 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.1398 | -0.0156 | -0.26 | 0.97 | 142 |
| 1 | -0.0034 | -0.0323 | -0.95 | 1.76 | 401 |
| 2 | -0.0039 | -0.0840 | -3.45 | 4.04 | 857 |
| 3 | -0.0040 | -0.0039 | 0.97 | 0.61 | 226 |
| 4 | -0.0043 | -0.0129 | -0.43 | 0.57 | 477 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51902
- **Expected rows**: 51902
- **Missing rows**: 0
- **Forward-fill count**: 1047
- **Forward-fill fraction**: 0.02017263303918924
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0407 <= 0
- **Objective score**: -0.0407085661941549
- **PnL %**: 0.674537639462595
- **Trade count**: 140

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0430 <= 0
- **Objective score**: -0.04302123786642479
- **PnL %**: 0.34937324304544765
- **Trade count**: 72

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0714 <= 0; recent PnL -0.1277% < 0
- **Objective score**: -0.07141841263987284
- **PnL %**: -0.12766650002263266
- **Trade count**: 50

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.287140060186569
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.2223, 0.3010 |
| sell_spread_base | 0.2575, 0.2722 |
| stop_loss | 0.2995, 0.2842 |
| take_profit | 0.2871, 0.2871 |
| executor_refresh_time | 0.2461, 0.2548 |
| cooldown_time | 0.2511, 0.2551 |
| total_amount_quote | 0.2527, 0.4699 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4442957466206217
- **Max CV**: 1.0672146351976433
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2386 | 2.011226268830744 | 3.964093792687932 | 2.8268549123497078 |
| buy_spread_ratio | 0.1849 | 1.7430446302749938 | 2.8126157611376432 | 2.20631401764017 |
| sell_spread_base | 1.0069 | 0.23469394686620126 | 5.627548639602696 | 2.185755470979477 |
| sell_spread_ratio | 0.2918 | 1.258991379533139 | 2.9666725336120368 | 2.2022679488776715 |
| buy_side_weight | 0.1417 | 0.2336447196923146 | 0.341072059248739 | 0.27910532855961223 |
| amount_skew | 0.1687 | 2.1541527334319843 | 3.3066244956928954 | 2.629111063403353 |
| stop_loss | 1.0672 | 0.014521632122597165 | 0.24418851101076047 | 0.08836771653916001 |
| take_profit | 0.9994 | 0.005078544642737518 | 0.14199691732768444 | 0.04228452624119064 |
| executor_refresh_time | 0.2730 | 3576.0 | 14155.0 | 11441.3 |
| cooldown_time | 0.4579 | 293.0 | 5610.0 | 3565.9 |
| total_amount_quote | 0.0570 | 848.6695061317673 | 999.6791952915659 | 919.6214007892702 |

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
| recent_objective | > 0 | -0.0407085661941549 | FAIL |
| recent_pnl | >= 0 | 0.674537639462595 | PASS |
| recent_trades | >= 5 | 140 | PASS |
| worst_stress | > -10 | 0.06344207406124436 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.015574785461320118 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=0.06344207406124436 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.0407085661941549, pnl=0.674537639462595, trades=140, reason=recent objective score -0.0407 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.04302123786642479, pnl=0.34937324304544765, trades=72, reason=recent objective score -0.0430 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.07141841263987284, pnl=-0.12766650002263266, trades=50, reason=recent objective score -0.0714 <= 0; recent PnL -0.1277% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4442957466206217 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51902 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0407 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0430 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0714 <= 0; recent PnL -0.1277% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51902
- **Pre-release bars**: 43837
- **Dev bars**: 35070
- **Holdout bars**: 8767
- **Recent 28d bars**: 8065
- **Recent window start**: 1773226500

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T12:15:38.086980+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 11943
