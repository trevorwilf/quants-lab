# PMM Dynamic Optimization Report: nonkyc_AVAX-USDT_5m_sweep_v1

Generated: 2026-04-08 20:09:12 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T20:09:12.833071+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 2469 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: AVAX-USDT
- **interval**: 5m
- **n_candles**: 51913
- **dataset_hash**: 35fd41b2f9b28f54db431974ea0865e1fe3ef029c08a23c7227bd3ecc44ebd49
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 966.3435122341788
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.6254228619514457 |
| buy_n_levels | 9 |
| buy_side_weight | 0.228667753914056 |
| buy_spread_base | 2.530344381058068 |
| buy_spread_ratio | 2.6154848805139577 |
| cooldown_time | 7165 |
| executor_refresh_time | 10270 |
| macd_fast | 30 |
| macd_signal | 27 |
| macd_slow | 90 |
| natr_length | 40 |
| sell_n_levels | 3 |
| sell_spread_base | 5.806694088154753 |
| sell_spread_ratio | 2.2786691135890367 |
| stop_loss | 0.22398262977510142 |
| take_profit | 0.005128017842182228 |
| time_limit | 30943 |
| total_amount_quote | 966.3435122341788 |
| trailing_stop_activation | 0.04372500909702556 |
| trailing_stop_delta | 0.003749653085408872 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 966.3435122341788 |
| Selected | 966.3435122341788 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -3.3293
- **Net PnL (quote)**: -32.1722
- **Sharpe Ratio**: -5.9339
- **Max Drawdown %**: 3.5679
- **Profit Factor**: 0.40482133932729847
- **Trade Count**: 598
- **Total Fees (quote)**: 16.6914
- **Maker Fees**: 12.7988
- **Taker Fees**: 3.8926
- **Fee Drag %**: 1.7273
- **TP Min-Notional Failures**: 3902 :warning:
  > 3902 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0780
- **PnL Component**: -0.0339
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0268
- **Fee Drag Component**: -0.0086
- **Inventory Component**: -0.0086
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0307**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.38 | -11.60 | 0.43 | 59 | -0.0301 | n/a |
| 1 | -0.37 | -12.23 | 0.41 | 59 | -0.0436 | n/a |
| 2 | -0.12 | -6.03 | 0.14 | 53 | -0.0818 | n/a |
| 3 | -0.19 | -5.05 | 0.29 | 64 | -0.0122 | n/a |
| 4 | -0.66 | -11.67 | 0.73 | 69 | -0.0206 | n/a |
| 5 | -0.01 | -0.10 | 0.22 | 84 | -0.0082 | n/a |
| 6 | -0.66 | -12.97 | 0.69 | 102 | -0.0237 | n/a |
| 7 | -0.17 | -4.98 | 0.23 | 76 | -0.0097 | n/a |
| 8 | -1.04 | -11.57 | 1.06 | 71 | -0.1188 | n/a |

## Stress Test Results

Worst Scenario: **spread_widen_25bps** (score: -0.1767)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -4.19 | -7.44 | 4.40 | -0.0976 |
| fees_2x | -5.06 | -8.93 | 5.26 | -0.1174 |
| latency_plus1 | -3.32 | -5.89 | 3.58 | -0.0780 |
| latency_plus2 | -3.46 | -6.09 | 3.69 | -0.0803 |
| latency_plus3 | -4.01 | -6.47 | 4.28 | -0.0915 |
| low_liquidity | -3.36 | -5.71 | 3.63 | -0.0797 |
| very_low_liquidity | -4.18 | -5.75 | 4.58 | -0.0995 |
| high_slippage | -3.43 | -6.11 | 3.66 | -0.0797 |
| extreme_slippage | -3.63 | -6.47 | 3.85 | -0.0833 |
| combined_adverse | -4.35 | -7.33 | 4.60 | -0.1017 |
| spread_widen_10bps | -4.93 | -6.32 | 5.27 | -0.1130 |
| spread_widen_25bps | -7.97 | -7.16 | 8.63 | -0.1767 |
| thin_book | -3.57 | -6.48 | 3.70 | -0.0798 |
| very_thin_book | -3.55 | -6.47 | 3.87 | -0.0783 |
| entry_spread_stress | -6.04 | -6.76 | 6.38 | -0.1354 |
| combined_market_deterioration | -5.59 | -8.85 | 5.74 | -0.1239 |
| severe_adverse | -7.28 | -9.78 | 7.61 | -0.1593 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0024)
- **Trend**: ranging (efficiency: 0.0049)
- **Best holdout score**: -0.0245 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1273 | -0.0245 | -0.81 | 0.88 | 194 |
| 1 | -0.0113 | -0.0884 | -2.18 | 2.89 | 560 |
| 2 | -0.0123 | -0.1244 | -3.75 | 3.86 | 575 |
| 3 | -0.0127 | -0.0623 | -2.05 | 2.13 | 454 |
| 4 | -0.0128 | -0.0418 | -0.82 | 1.22 | 267 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51913
- **Expected rows**: 51913
- **Missing rows**: 0
- **Forward-fill count**: 537
- **Forward-fill fraction**: 0.010344229769036657
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0920 <= 0; recent PnL -1.8406% < 0
- **Objective score**: -0.09195960021433291
- **PnL %**: -1.840622212998614
- **Trade count**: 147

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0725 <= 0; recent PnL -0.8544% < 0
- **Objective score**: -0.07252748212300188
- **PnL %**: -0.8543846128328443
- **Trade count**: 81

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0883 <= 0; recent PnL -0.6620% < 0
- **Objective score**: -0.0883200609481744
- **PnL %**: -0.6620479468510142
- **Trade count**: 41

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: -0.13507111919758583
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1948, -0.2395 |
| sell_spread_base | -0.1366, -0.2427 |
| stop_loss | -0.1351, -0.1351 |
| take_profit | -0.1985, -0.1890 |
| executor_refresh_time | -0.1858, -0.1729 |
| cooldown_time | -0.1822, -0.1754 |
| total_amount_quote | -0.1958, -0.1407 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2736584011630907
- **Max CV**: 1.0468863195285425
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1238 | 2.4711699251599213 | 3.4169631874326036 | 2.913919215968057 |
| buy_spread_ratio | 0.1159 | 1.9172890385519246 | 2.599346707752408 | 2.2728432107360077 |
| sell_spread_base | 0.5161 | 0.4604510973642527 | 4.592000261940294 | 2.4758927072706647 |
| sell_spread_ratio | 0.2667 | 1.4059581882802532 | 2.864518308960069 | 1.8884687394603543 |
| buy_side_weight | 0.2170 | 0.2070964575471449 | 0.36924947857127777 | 0.27067508882799046 |
| amount_skew | 0.1427 | 2.0599833488850705 | 3.2133505764420764 | 2.7058442571622043 |
| stop_loss | 1.0469 | 0.011005225443431323 | 0.1639027164032799 | 0.057821211284633564 |
| take_profit | 0.0900 | 0.0050087327925540945 | 0.006357262762778687 | 0.005513772208768236 |
| executor_refresh_time | 0.2171 | 7669.0 | 14248.0 | 11125.0 |
| cooldown_time | 0.1655 | 3861.0 | 6923.0 | 5875.6 |
| total_amount_quote | 0.1085 | 735.7006182360359 | 975.027058770271 | 869.1967870713482 |

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
| recent_objective | > 0 | -0.09195960021433291 | FAIL |
| recent_pnl | >= 0 | -1.840622212998614 | FAIL |
| recent_trades | >= 5 | 147 | PASS |
| worst_stress | > -10 | -0.17668782725015755 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.024548163197414145 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=spread_widen_25bps score=-0.17668782725015755 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.09195960021433291, pnl=-1.840622212998614, trades=147, reason=recent objective score -0.0920 <= 0; recent PnL -1.8406% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.07252748212300188, pnl=-0.8543846128328443, trades=81, reason=recent objective score -0.0725 <= 0; recent PnL -0.8544% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.0883200609481744, pnl=-0.6620479468510142, trades=41, reason=recent objective score -0.0883 <= 0; recent PnL -0.6620% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2736584011630907 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51913 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0920 <= 0; recent PnL -1.8406% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0725 <= 0; recent PnL -0.8544% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0883 <= 0; recent PnL -0.6620% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51913
- **Pre-release bars**: 43848
- **Dev bars**: 35079
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065
- **Recent window start**: 1773251100

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T20:09:12.833071+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 2469
