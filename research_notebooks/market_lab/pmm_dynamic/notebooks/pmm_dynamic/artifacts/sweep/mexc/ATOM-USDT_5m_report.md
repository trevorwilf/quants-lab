# PMM Dynamic Optimization Report: mexc_ATOM-USDT_5m_sweep_v1

Generated: 2026-04-09 01:47:15 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T01:47:15.572909+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 9137 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ATOM-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 124df555c67d6fe5411a0aaf94eaf970cd4dfc0b3f1b180011ccd4c82f15b2a6
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 889.6055049108166
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.3358137889225565 |
| buy_n_levels | 7 |
| buy_side_weight | 0.32853479215187115 |
| buy_spread_base | 1.7897379542031489 |
| buy_spread_ratio | 2.649578290730202 |
| cooldown_time | 6188 |
| executor_refresh_time | 978 |
| macd_fast | 35 |
| macd_signal | 15 |
| macd_slow | 38 |
| natr_length | 12 |
| sell_n_levels | 5 |
| sell_spread_base | 5.211131901921867 |
| sell_spread_ratio | 1.237755361682299 |
| stop_loss | 0.014676718922841184 |
| take_profit | 0.005025056719011172 |
| time_limit | 33655 |
| total_amount_quote | 889.6055049108166 |
| trailing_stop_activation | 0.05810751490518119 |
| trailing_stop_delta | 0.0013657862788895086 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 889.6055049108166 |
| Selected | 889.6055049108166 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.3809
- **Net PnL (quote)**: -12.2844
- **Sharpe Ratio**: -2.6551
- **Max Drawdown %**: 1.6267
- **Profit Factor**: 0.8219034040307251
- **Trade Count**: 873
- **Total Fees (quote)**: 3.8674
- **Maker Fees**: 3.3461
- **Taker Fees**: 0.5213
- **Fee Drag %**: 0.4347
- **TP Min-Notional Failures**: 3045 :warning:
  > 3045 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0366
- **PnL Component**: -0.0139
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0122
- **Fee Drag Component**: -0.0022
- **Inventory Component**: -0.0083
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0032**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.04 | -1.21 | 0.18 | 83 | -0.0072 | n/a |
| 1 | 0.02 | 0.96 | 0.07 | 77 | -0.0021 | n/a |
| 2 | 0.02 | 1.39 | 0.06 | 56 | -0.0020 | n/a |
| 3 | -0.01 | -0.31 | 0.12 | 77 | -0.0027 | n/a |
| 4 | -0.48 | -7.29 | 0.62 | 92 | -0.0114 | n/a |
| 5 | -0.05 | -0.90 | 0.24 | 81 | -0.0076 | n/a |
| 6 | 0.05 | 2.36 | 0.07 | 83 | -0.0018 | n/a |
| 7 | 0.09 | 3.67 | 0.07 | 73 | -0.0014 | n/a |
| 8 | -0.07 | -3.23 | 0.16 | 64 | -0.0036 | n/a |

## Stress Test Results

Worst Scenario: **combined_market_deterioration** (score: -0.0468)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.60 | -3.07 | 1.80 | -0.0413 |
| fees_2x | -1.82 | -3.49 | 1.98 | -0.0459 |
| latency_plus1 | -1.49 | -2.84 | 1.74 | -0.0386 |
| latency_plus2 | -1.19 | -2.29 | 1.40 | -0.0329 |
| latency_plus3 | -1.11 | -3.30 | 1.19 | -0.0250 |
| low_liquidity | -1.38 | -2.66 | 1.63 | -0.0366 |
| very_low_liquidity | -1.40 | -2.68 | 1.64 | -0.0369 |
| high_slippage | -1.53 | -2.92 | 1.75 | -0.0391 |
| extreme_slippage | -1.82 | -3.43 | 2.00 | -0.0439 |
| combined_adverse | -1.86 | -3.52 | 2.05 | -0.0458 |
| spread_widen_10bps | -1.15 | -3.32 | 1.21 | -0.0277 |
| spread_widen_25bps | -2.06 | -6.35 | 2.09 | -0.0435 |
| thin_book | -2.28 | -6.69 | 2.41 | -0.0455 |
| very_thin_book | -1.38 | -2.97 | 1.64 | -0.0284 |
| entry_spread_stress | -1.08 | -3.43 | 1.15 | -0.0267 |
| combined_market_deterioration | -2.17 | -5.39 | 2.28 | -0.0468 |
| severe_adverse | -2.00 | -6.07 | 2.06 | -0.0390 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0033)
- **Trend**: ranging (efficiency: 0.0026)
- **Best holdout score**: 0.0022 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0417 | -0.0023 | 0.06 | 0.12 | 166 |
| 1 | 0.0001 | -0.0096 | 0.17 | 0.27 | 763 |
| 2 | -0.0003 | -0.0024 | 0.13 | 0.09 | 264 |
| 3 | -0.0007 | 0.0022 | 0.31 | 0.06 | 128 |
| 4 | -0.0010 | -0.0488 | -1.30 | 1.78 | 650 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 8
- **Forward-fill fraction**: 0.00015431801084084027
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0033 <= 0; recent PnL -0.0232% < 0
- **Objective score**: -0.0033332241661498713
- **PnL %**: -0.023158936822614367
- **Trade count**: 113

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0067 <= 0; recent PnL -0.0371% < 0
- **Objective score**: -0.006714963326662402
- **PnL %**: -0.03710504542851656
- **Trade count**: 53

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1139 <= 0
- **Objective score**: -0.11394940036652187
- **PnL %**: 0.0010432823108554694
- **Trade count**: 22

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.04313354322772127
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0144, -0.0576 |
| sell_spread_base | -0.0209, -0.0347 |
| stop_loss | -0.0491, -0.0284 |
| take_profit | -0.0240, -0.0406 |
| executor_refresh_time | -0.0431, -0.0413 |
| cooldown_time | -0.0262, -0.0266 |
| total_amount_quote | -0.0429, -0.0205 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3931846582588143
- **Max CV**: 1.194206220427551
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1724 | 1.5514853226920495 | 2.694211123295951 | 2.1361252277341705 |
| buy_spread_ratio | 0.1413 | 1.770683935635478 | 2.749587841505715 | 2.1456778849024793 |
| sell_spread_base | 0.6595 | 0.2314256929556492 | 1.1014499069138648 | 0.5228266461089274 |
| sell_spread_ratio | 0.1644 | 1.2030903494351477 | 2.0523716152036093 | 1.6222208267030847 |
| buy_side_weight | 0.2292 | 0.26986867829791505 | 0.6402091635463047 | 0.5054621821282544 |
| amount_skew | 0.2556 | 1.9795547770534796 | 3.9891413969984586 | 3.061117625473864 |
| stop_loss | 0.2159 | 0.01024181739548714 | 0.01966278356612927 | 0.014263403917226724 |
| take_profit | 0.7451 | 0.005179376298831575 | 0.04036734883702889 | 0.014996055186646502 |
| executor_refresh_time | 0.4192 | 3251.0 | 14208.0 | 9365.9 |
| cooldown_time | 1.1942 | 80.0 | 4615.0 | 1281.9 |
| total_amount_quote | 0.1282 | 670.369223296088 | 979.6954594509165 | 840.4678401122785 |

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
| recent_objective | > 0 | -0.0033332241661498713 | FAIL |
| recent_pnl | >= 0 | -0.023158936822614367 | FAIL |
| recent_trades | >= 5 | 113 | PASS |
| worst_stress | > -10 | -0.04677927521458863 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.002301939235957424 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=combined_market_deterioration score=-0.04677927521458863 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.0033332241661498713, pnl=-0.023158936822614367, trades=113, reason=recent objective score -0.0033 <= 0; recent PnL -0.0232% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.006714963326662402, pnl=-0.03710504542851656, trades=53, reason=recent objective score -0.0067 <= 0; recent PnL -0.0371% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.11394940036652187, pnl=0.0010432823108554694, trades=22, reason=recent objective score -0.1139 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3931846582588143 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0033 <= 0; recent PnL -0.0232% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0067 <= 0; recent PnL -0.0371% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1139 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51841
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065
- **Recent window start**: 1773272700

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T01:47:15.572909+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 9137
