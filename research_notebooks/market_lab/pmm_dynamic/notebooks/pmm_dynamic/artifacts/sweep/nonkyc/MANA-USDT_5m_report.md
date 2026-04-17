# PMM Dynamic Optimization Report: nonkyc_MANA-USDT_5m_sweep_v1

Generated: 2026-04-09 22:04:41 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T22:04:41.712244+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 2053 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: MANA-USDT
- **interval**: 5m
- **n_candles**: 16792
- **dataset_hash**: 6a61caf8e7906344a5aa72253ecf0202206ebd72913b56acdd3ea45141ec97f8
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 945.2432954467955
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.2754388340603313 |
| buy_n_levels | 10 |
| buy_side_weight | 0.26880200762663575 |
| buy_spread_base | 0.8809423996141874 |
| buy_spread_ratio | 2.4735472118857382 |
| cooldown_time | 6097 |
| executor_refresh_time | 8912 |
| macd_fast | 31 |
| macd_signal | 21 |
| macd_slow | 57 |
| natr_length | 29 |
| sell_n_levels | 5 |
| sell_spread_base | 5.543428473181261 |
| sell_spread_ratio | 1.3356716715100894 |
| stop_loss | 0.1675819918584697 |
| take_profit | 0.007014680179554702 |
| time_limit | 116916 |
| total_amount_quote | 945.2432954467955 |
| trailing_stop_activation | 0.004349114500441708 |
| trailing_stop_delta | 0.025167094760358447 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 945.2432954467955 |
| Selected | 945.2432954467955 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.8234
- **Net PnL (quote)**: -7.7831
- **Sharpe Ratio**: -2.2415
- **Max Drawdown %**: 1.4111
- **Profit Factor**: 0.7967029476148458
- **Trade Count**: 386
- **Total Fees (quote)**: 9.8446
- **Maker Fees**: 8.3608
- **Taker Fees**: 1.4838
- **Fee Drag %**: 1.0415
- **TP Min-Notional Failures**: 3834 :warning:
  > 3834 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0527
- **PnL Component**: -0.0083
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0106
- **Fee Drag Component**: -0.0052
- **Inventory Component**: -0.0282
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0639**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.37 | -12.34 | 0.56 | 68 | -0.0214 | n/a |
| 1 | -0.23 | -12.23 | 0.26 | 60 | -0.0158 | n/a |
| 2 | -0.01 | -0.89 | 0.12 | 60 | -0.0124 | n/a |
| 3 | -0.33 | -16.26 | 0.36 | 75 | -0.1470 | n/a |
| 4 | -0.14 | -10.22 | 0.20 | 52 | -0.0157 | n/a |
| 5 | -0.08 | -8.81 | 0.16 | 55 | -0.0353 | n/a |
| 6 | -0.63 | -18.54 | 0.75 | 57 | -0.0254 | n/a |
| 7 | -0.68 | -12.88 | 0.71 | 43 | -0.1093 | n/a |
| 8 | -0.15 | -18.86 | 0.20 | 54 | -0.0605 | n/a |
| 9 | 0.02 | 1.77 | 0.07 | 35 | -0.0654 | n/a |
| 10 | -0.13 | -17.62 | 0.15 | 43 | -0.1743 | n/a |
| 11 | -0.09 | -13.53 | 0.12 | 29 | -0.1629 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1156)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.34 | -3.67 | 1.72 | -0.0630 |
| fees_2x | -1.86 | -5.09 | 2.10 | -0.0739 |
| latency_plus1 | -0.82 | -2.17 | 1.41 | -0.0529 |
| latency_plus2 | -0.87 | -2.23 | 1.50 | -0.0554 |
| latency_plus3 | -0.89 | -2.29 | 1.51 | -0.0556 |
| low_liquidity | -1.55 | -3.62 | 1.88 | -0.0737 |
| very_low_liquidity | -1.67 | -3.87 | 2.33 | -0.0800 |
| high_slippage | -0.86 | -2.35 | 1.44 | -0.0533 |
| extreme_slippage | -0.94 | -2.56 | 1.49 | -0.0545 |
| combined_adverse | -2.25 | -5.19 | 2.42 | -0.0883 |
| spread_widen_10bps | -1.78 | -3.45 | 2.19 | -0.0878 |
| spread_widen_25bps | -1.45 | -2.94 | 1.89 | -0.0772 |
| thin_book | -1.28 | -2.89 | 2.06 | -0.0739 |
| very_thin_book | -1.00 | -2.53 | 1.75 | -0.0624 |
| entry_spread_stress | -1.65 | -3.31 | 2.08 | -0.0842 |
| combined_market_deterioration | -2.18 | -4.34 | 2.59 | -0.0987 |
| severe_adverse | -3.16 | -5.78 | 3.47 | -0.1156 |

## Holdout Validation

- **Holdout bars**: 1750
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0025)
- **Trend**: ranging (efficiency: 0.0085)
- **Best holdout score**: -0.0187 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0842 | -0.0856 | -0.23 | 0.27 | 86 |
| 1 | -0.0079 | -0.0267 | 0.17 | 0.27 | 135 |
| 2 | -0.0080 | -0.0187 | -0.20 | 0.22 | 142 |
| 3 | -0.0089 | -0.0405 | -0.31 | 0.64 | 180 |
| 4 | -0.0094 | -0.0371 | -0.27 | 0.36 | 89 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 16792
- **Expected rows**: 16818
- **Missing rows**: 26
- **Forward-fill count**: 79
- **Forward-fill fraction**: 0.004704621248213435
- **Longest gap (seconds)**: 8100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0759 <= 0; recent PnL -1.9814% < 0
- **Objective score**: -0.07591998205868139
- **PnL %**: -1.9814049898390331
- **Trade count**: 309

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0270 <= 0; recent PnL -0.2765% < 0
- **Objective score**: -0.02700482941703984
- **PnL %**: -0.2764622129890086
- **Trade count**: 130

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0480 <= 0; recent PnL -0.1491% < 0
- **Objective score**: -0.048017384676925914
- **PnL %**: -0.14914299815275564
- **Trade count**: 61

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.11371990163399714
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0940, -0.1135 |
| sell_spread_base | -0.1030, -0.1291 |
| stop_loss | -0.1137, -0.1137 |
| take_profit | -0.1217, -0.1054 |
| executor_refresh_time | -0.1115, -0.1101 |
| cooldown_time | -0.0998, -0.1054 |
| total_amount_quote | -0.1176, -0.2302 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.41782009850539514
- **Max CV**: 1.2426858056718755
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3131 | 0.8690984276603474 | 2.082680351763081 | 1.3355165492464887 |
| buy_spread_ratio | 0.1546 | 1.7699549424905288 | 2.935909254478648 | 2.3507723104145937 |
| sell_spread_base | 1.1175 | 0.24174083106246883 | 5.212731943414683 | 1.6796450381167403 |
| sell_spread_ratio | 0.2306 | 1.3280643269182495 | 2.6013693241027966 | 1.7890113003706012 |
| buy_side_weight | 0.3339 | 0.2171699346525288 | 0.5886224661031884 | 0.4002567725644184 |
| amount_skew | 0.1352 | 2.0270195916939584 | 2.995065190815017 | 2.523894359161641 |
| stop_loss | 1.2427 | 0.012696841421341101 | 0.21950658346000082 | 0.0639648843935435 |
| take_profit | 0.1377 | 0.0051520811959978405 | 0.007252508770627735 | 0.005855920549968782 |
| executor_refresh_time | 0.5653 | 795.0 | 10520.0 | 5420.5 |
| cooldown_time | 0.2866 | 2015.0 | 5737.0 | 4206.0 |
| total_amount_quote | 0.0789 | 784.1039407143678 | 997.3366052376666 | 937.023943931977 |

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
| recent_objective | > 0 | -0.07591998205868139 | FAIL |
| recent_pnl | >= 0 | -1.9814049898390331 | FAIL |
| recent_trades | >= 5 | 309 | PASS |
| worst_stress | > -10 | -0.11563438113071567 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.08555250241079852 |
| walkforward | PASS | 12 folds |
| stress | PASS | worst=severe_adverse score=-0.11563438113071567 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.07591998205868139, pnl=-1.9814049898390331, trades=309, reason=recent objective score -0.0759 <= 0; recent PnL -1.9814% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.02700482941703984, pnl=-0.2764622129890086, trades=130, reason=recent objective score -0.0270 <= 0; recent PnL -0.2765% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.048017384676925914, pnl=-0.14914299815275564, trades=61, reason=recent objective score -0.0480 <= 0; recent PnL -0.1491% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.41782009850539514 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 16792 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0759 <= 0; recent PnL -1.9814% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0270 <= 0; recent PnL -0.2765% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0480 <= 0; recent PnL -0.1491% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 16792
- **Pre-release bars**: 8753
- **Dev bars**: 7003
- **Holdout bars**: 1750
- **Recent 28d bars**: 8039
- **Recent window start**: 1773346800

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T22:04:41.712244+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 2053
