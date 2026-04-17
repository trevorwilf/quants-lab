# PMM Dynamic Optimization Report: nonkyc_XMR-USDT_5m_sweep_v1

Generated: 2026-04-10 02:30:47 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-10T02:30:47.914281+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 10148 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 52153
- **dataset_hash**: 0df11cfd5195702bf7ea1f93cf5d612732bacf95372311e2398f2b47907d80c1
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 993.7207457656558
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.9796396875891866 |
| buy_n_levels | 8 |
| buy_side_weight | 0.23845172113603497 |
| buy_spread_base | 2.1575019671793942 |
| buy_spread_ratio | 2.7250145027756405 |
| cooldown_time | 753 |
| executor_refresh_time | 12146 |
| macd_fast | 43 |
| macd_signal | 12 |
| macd_slow | 71 |
| natr_length | 36 |
| sell_n_levels | 6 |
| sell_spread_base | 2.844476068204559 |
| sell_spread_ratio | 1.2974715576413063 |
| stop_loss | 0.11541361803502559 |
| take_profit | 0.006775491194266324 |
| time_limit | 34542 |
| total_amount_quote | 993.7207457656558 |
| trailing_stop_activation | 0.01020639091607309 |
| trailing_stop_delta | 0.00189946794039931 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 993.7207457656558 |
| Selected | 993.7207457656558 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 8.5623
- **Net PnL (quote)**: 85.0853
- **Sharpe Ratio**: 3.1517
- **Max Drawdown %**: 3.7637
- **Profit Factor**: 2.814087930307339
- **Trade Count**: 1372
- **Total Fees (quote)**: 36.6640
- **Maker Fees**: 23.3961
- **Taker Fees**: 13.2678
- **Fee Drag %**: 3.6896
- **TP Min-Notional Failures**: 160 :warning:
  > 160 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0202
- **PnL Component**: 0.0822
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0282
- **Fee Drag Component**: -0.0184
- **Inventory Component**: -0.0149
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0020**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.10 | 5.21 | 0.06 | 56 | -0.0015 | n/a |
| 1 | 0.40 | 7.67 | 0.07 | 55 | 0.0012 | n/a |
| 2 | 0.08 | 7.56 | 0.05 | 63 | -0.0017 | n/a |
| 3 | 0.82 | 4.00 | 0.31 | 59 | 0.0035 | n/a |
| 4 | -0.21 | -7.09 | 0.38 | 76 | -0.0074 | n/a |
| 5 | 0.17 | 6.44 | 0.07 | 67 | -0.0011 | n/a |
| 6 | 0.06 | 1.69 | 0.19 | 71 | -0.0032 | n/a |
| 7 | 0.06 | 5.03 | 0.07 | 53 | -0.0020 | n/a |
| 8 | 0.05 | 3.51 | 0.05 | 67 | -0.0019 | n/a |

## Stress Test Results

Worst Scenario: **combined_market_deterioration** (score: -0.0594)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 6.72 | 2.50 | 4.24 | -0.0099 |
| fees_2x | 4.87 | 1.84 | 4.72 | -0.0404 |
| latency_plus1 | 8.33 | 3.07 | 3.78 | 0.0181 |
| latency_plus2 | 6.87 | 2.87 | 1.81 | 0.0330 |
| latency_plus3 | 8.82 | 2.92 | 4.73 | 0.0082 |
| low_liquidity | 8.29 | 3.06 | 3.77 | 0.0178 |
| very_low_liquidity | 6.18 | 3.16 | 3.79 | -0.0016 |
| high_slippage | 8.23 | 3.03 | 3.86 | 0.0164 |
| extreme_slippage | 7.56 | 2.79 | 4.04 | 0.0087 |
| combined_adverse | 5.78 | 2.16 | 4.36 | -0.0192 |
| spread_widen_10bps | 8.40 | 2.79 | 4.89 | 0.0028 |
| spread_widen_25bps | 9.73 | 2.68 | 5.33 | 0.0085 |
| thin_book | 4.71 | 1.79 | 4.94 | -0.0245 |
| very_thin_book | -0.56 | -1.20 | 1.84 | -0.0296 |
| entry_spread_stress | 7.49 | 2.60 | 5.34 | -0.0087 |
| combined_market_deterioration | 3.85 | 1.15 | 6.37 | -0.0594 |
| severe_adverse | 0.40 | 0.22 | 3.09 | -0.0428 |

## Holdout Validation

- **Holdout bars**: 8817
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0041)
- **Trend**: ranging (efficiency: 0.0042)
- **Best holdout score**: -0.0051 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0196 | -0.0051 | -0.02 | 0.24 | 143 |
| 1 | 0.0001 | -0.0446 | 0.03 | 0.92 | 387 |
| 2 | -0.0003 | -0.0170 | 0.05 | 0.40 | 397 |
| 3 | -0.0004 | -0.1247 | -1.03 | 1.39 | 678 |
| 4 | -0.0005 | -0.0703 | -0.05 | 0.29 | 488 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52153
- **Expected rows**: 52153
- **Missing rows**: 0
- **Forward-fill count**: 236
- **Forward-fill fraction**: 0.004525147163154565
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0030 <= 0
- **Objective score**: -0.00303262212943537
- **PnL %**: 0.04185120989748439
- **Trade count**: 117

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0026 <= 0
- **Objective score**: -0.0026125522290997355
- **PnL %**: 0.014021953029024165
- **Trade count**: 61

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0781 <= 0
- **Objective score**: -0.07805465245796199
- **PnL %**: 0.026365163441262822
- **Trade count**: 31

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: 0.0280524812503089
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0494, 0.0186 |
| sell_spread_base | 0.0086, 0.0357 |
| stop_loss | 0.0263, 0.0286 |
| take_profit | 0.0245, 0.0373 |
| executor_refresh_time | 0.0251, 0.0403 |
| cooldown_time | 0.0281, 0.0281 |
| total_amount_quote | 0.0241, 0.0281 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.28139851481878414
- **Max CV**: 0.8075647759738426
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2192 | 1.2508996456120423 | 2.5610265847437437 | 2.1207050774371154 |
| buy_spread_ratio | 0.1442 | 1.70255714143207 | 2.7953809147368474 | 2.2451740924770567 |
| sell_spread_base | 0.8076 | 0.3470724308297845 | 2.922832107182718 | 1.2634108505800676 |
| sell_spread_ratio | 0.1653 | 1.2123486483680805 | 1.8242508182849395 | 1.4483826752834095 |
| buy_side_weight | 0.2986 | 0.2025274181678502 | 0.45673352244021104 | 0.29649490226441433 |
| amount_skew | 0.2316 | 1.9586108369402018 | 3.9845262795798417 | 2.983488900003927 |
| stop_loss | 0.3116 | 0.07260321657609112 | 0.21006157456142863 | 0.12691598852210473 |
| take_profit | 0.3015 | 0.0050367262059099775 | 0.011877796729845517 | 0.0070917782021014935 |
| executor_refresh_time | 0.0852 | 9935.0 | 12997.0 | 11086.8 |
| cooldown_time | 0.4452 | 1533.0 | 5721.0 | 3549.2 |
| total_amount_quote | 0.0855 | 717.1689558061184 | 989.8232533769207 | 878.3151417187644 |

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
- walkforward_positive_majority: PASS
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
| recent_objective | > 0 | -0.00303262212943537 | FAIL |
| recent_pnl | >= 0 | 0.04185120989748439 | PASS |
| recent_trades | >= 5 | 117 | PASS |
| worst_stress | > -10 | -0.05941112805280999 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.005101478609910559 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=combined_market_deterioration score=-0.05941112805280999 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.00303262212943537, pnl=0.04185120989748439, trades=117, reason=recent objective score -0.0030 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.0026125522290997355, pnl=0.014021953029024165, trades=61, reason=recent objective score -0.0026 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.07805465245796199, pnl=0.026365163441262822, trades=31, reason=recent objective score -0.0781 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.28139851481878414 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52153 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0030 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0026 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0781 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52153
- **Pre-release bars**: 44088
- **Dev bars**: 35271
- **Holdout bars**: 8817
- **Recent 28d bars**: 8065
- **Recent window start**: 1773366600

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-10T02:30:47.914281+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 10148
