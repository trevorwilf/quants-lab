# PMM Dynamic Optimization Report: nonkyc_BNB-USDT_5m_sweep_v1

Generated: 2026-04-08 21:25:38 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T21:25:38.154941+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 2592 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BNB-USDT
- **interval**: 5m
- **n_candles**: 51856
- **dataset_hash**: 9f4ee1d812b396bfeb641289b79972e4944fc28fc6f8326d268a6ac4ad8d0bf4
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 989.0594862968766
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.765210921322553 |
| buy_n_levels | 6 |
| buy_side_weight | 0.5365711475495665 |
| buy_spread_base | 4.949135925317727 |
| buy_spread_ratio | 1.6286743401205872 |
| cooldown_time | 2247 |
| executor_refresh_time | 11233 |
| macd_fast | 14 |
| macd_signal | 21 |
| macd_slow | 43 |
| natr_length | 30 |
| sell_n_levels | 5 |
| sell_spread_base | 5.037314578821677 |
| sell_spread_ratio | 2.094971960248943 |
| stop_loss | 0.014521491712690723 |
| take_profit | 0.005266375138811751 |
| time_limit | 140710 |
| total_amount_quote | 989.0594862968766 |
| trailing_stop_activation | 0.0994626005072366 |
| trailing_stop_delta | 0.004263627841893789 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 989.0594862968766 |
| Selected | 989.0594862968766 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -7.8320
- **Net PnL (quote)**: -77.4631
- **Sharpe Ratio**: -3.6368
- **Max Drawdown %**: 7.9398
- **Profit Factor**: 0.2157127982197413
- **Trade Count**: 624
- **Total Fees (quote)**: 26.9891
- **Maker Fees**: 17.0241
- **Taker Fees**: 9.9650
- **Fee Drag %**: 2.7288
- **TP Min-Notional Failures**: 6525 :warning:
  > 6525 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1665
- **PnL Component**: -0.0816
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0595
- **Fee Drag Component**: -0.0136
- **Inventory Component**: -0.0116
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0678**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.60 | -7.53 | 0.86 | 48 | -0.0234 | n/a |
| 1 | -0.48 | -5.78 | 0.66 | 46 | -0.0560 | n/a |
| 2 | -0.26 | -7.04 | 0.31 | 46 | -0.1330 | n/a |
| 3 | -0.02 | -2.08 | 0.04 | 45 | -0.0487 | n/a |
| 4 | -1.37 | -8.21 | 1.47 | 60 | -0.0677 | n/a |
| 5 | -0.17 | -5.34 | 0.19 | 74 | -0.0087 | n/a |
| 6 | -0.37 | -4.64 | 0.57 | 57 | -0.0796 | n/a |
| 7 | -0.06 | -4.86 | 0.06 | 41 | -0.0390 | n/a |
| 8 | -0.62 | -6.00 | 0.86 | 34 | -0.1113 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.2306)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -9.20 | -4.26 | 9.28 | -0.1985 |
| fees_2x | -10.56 | -4.88 | 10.62 | -0.2306 |
| latency_plus1 | -7.83 | -3.64 | 7.94 | -0.1665 |
| latency_plus2 | -7.83 | -3.64 | 7.94 | -0.1665 |
| latency_plus3 | -7.87 | -3.65 | 7.97 | -0.1672 |
| low_liquidity | -7.83 | -3.64 | 7.94 | -0.1665 |
| very_low_liquidity | -7.83 | -3.87 | 7.94 | -0.1665 |
| high_slippage | -8.08 | -3.76 | 8.19 | -0.1712 |
| extreme_slippage | -8.59 | -3.99 | 8.69 | -0.1804 |
| combined_adverse | -9.45 | -4.38 | 9.53 | -0.2031 |
| spread_widen_10bps | -7.68 | -3.54 | 7.77 | -0.1624 |
| spread_widen_25bps | -9.36 | -4.24 | 9.59 | -0.1981 |
| thin_book | -7.70 | -3.86 | 7.77 | -0.1602 |
| very_thin_book | -6.33 | -4.60 | 6.46 | -0.1320 |
| entry_spread_stress | -8.54 | -3.85 | 8.79 | -0.1867 |
| combined_market_deterioration | -9.32 | -4.21 | 9.44 | -0.1971 |
| severe_adverse | -10.62 | -5.26 | 10.63 | -0.2250 |

## Holdout Validation

- **Holdout bars**: 8758
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0019)
- **Trend**: ranging (efficiency: 0.0032)
- **Best holdout score**: -0.0224 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1986 | -0.0224 | -1.05 | 1.09 | 108 |
| 1 | -0.0218 | -0.1890 | -3.66 | 4.96 | 365 |
| 2 | -0.0229 | -0.1172 | -1.05 | 2.27 | 293 |
| 3 | -0.0230 | -0.0346 | -0.81 | 1.04 | 198 |
| 4 | -0.0262 | -0.1406 | -3.70 | 4.27 | 432 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51856
- **Expected rows**: 51856
- **Missing rows**: 0
- **Forward-fill count**: 252
- **Forward-fill fraction**: 0.004859611231101512
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0550 <= 0; recent PnL -0.5718% < 0
- **Objective score**: -0.05499944255897547
- **PnL %**: -0.5717763295948902
- **Trade count**: 56

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2711 <= 0; recent PnL -0.0814% < 0
- **Objective score**: -0.27107630069895866
- **PnL %**: -0.08138909651785904
- **Trade count**: 22

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2670 <= 0; recent PnL -0.0258% < 0
- **Objective score**: -0.2670364904290218
- **PnL %**: -0.025766296983549212
- **Trade count**: 13

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.2117934633515429
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1534, -0.2107 |
| sell_spread_base | -0.2366, -0.1836 |
| stop_loss | -0.2095, -0.1855 |
| take_profit | -0.1997, -0.1810 |
| executor_refresh_time | -0.1724, -0.1956 |
| cooldown_time | -0.1736, -0.1859 |
| total_amount_quote | -0.2104, -0.2120 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.35911410589329984
- **Max CV**: 1.379862164761088
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1080 | 4.186909261123127 | 5.794001868747356 | 4.840444249292521 |
| buy_spread_ratio | 0.0992 | 1.2075055877550256 | 1.562999264685919 | 1.3544360797134907 |
| sell_spread_base | 1.3799 | 0.23100364661223405 | 5.719943448081946 | 1.346453997754443 |
| sell_spread_ratio | 0.2278 | 1.200432287653868 | 2.229247141402718 | 1.5990700440607877 |
| buy_side_weight | 0.2359 | 0.20157093108520108 | 0.38327295773211456 | 0.2756483741625178 |
| amount_skew | 0.1505 | 1.267885915917157 | 2.0509699922220137 | 1.5879863425631209 |
| stop_loss | 0.8934 | 0.01356921906592475 | 0.2361356645846726 | 0.07479136817661348 |
| take_profit | 0.0952 | 0.00501386390617119 | 0.006480269604424157 | 0.005461718441959036 |
| executor_refresh_time | 0.4533 | 902.0 | 12305.0 | 8269.7 |
| cooldown_time | 0.1740 | 4293.0 | 7178.0 | 6164.5 |
| total_amount_quote | 0.1332 | 625.513143172549 | 989.419272383385 | 869.7761420953811 |

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
| recent_objective | > 0 | -0.05499944255897547 | FAIL |
| recent_pnl | >= 0 | -0.5717763295948902 | FAIL |
| recent_trades | >= 5 | 56 | PASS |
| worst_stress | > -10 | -0.23064185228081138 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.02236157933208827 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.23064185228081138 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.05499944255897547, pnl=-0.5717763295948902, trades=56, reason=recent objective score -0.0550 <= 0; recent PnL -0.5718% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.27107630069895866, pnl=-0.08138909651785904, trades=22, reason=recent objective score -0.2711 <= 0; recent PnL -0.0814% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.2670364904290218, pnl=-0.025766296983549212, trades=13, reason=recent objective score -0.2670 <= 0; recent PnL -0.0258% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.35911410589329984 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51856 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0550 <= 0; recent PnL -0.5718% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2711 <= 0; recent PnL -0.0814% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2670 <= 0; recent PnL -0.0258% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51856
- **Pre-release bars**: 43791
- **Dev bars**: 35033
- **Holdout bars**: 8758
- **Recent 28d bars**: 8065
- **Recent window start**: 1773251100

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T21:25:38.154941+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 2592
