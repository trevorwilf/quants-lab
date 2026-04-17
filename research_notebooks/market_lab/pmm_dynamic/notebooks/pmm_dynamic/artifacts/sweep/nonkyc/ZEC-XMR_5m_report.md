# PMM Dynamic Optimization Report: nonkyc_ZEC-XMR_5m_sweep_v1

Generated: 2026-04-10 04:28:48 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-10T04:28:48.491767+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 14653 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ZEC-XMR
- **interval**: 5m
- **n_candles**: 52165
- **dataset_hash**: 892b6916836f61cfc65773488f3860c485b54f316b03459fb5c513277849db66
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 736.7684441595574
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.0173533022117187 |
| buy_n_levels | 7 |
| buy_side_weight | 0.2822729999095362 |
| buy_spread_base | 0.6540359624034991 |
| buy_spread_ratio | 1.3709558744636445 |
| cooldown_time | 252 |
| executor_refresh_time | 5436 |
| macd_fast | 18 |
| macd_signal | 15 |
| macd_slow | 71 |
| natr_length | 12 |
| sell_n_levels | 7 |
| sell_spread_base | 3.5657500872446564 |
| sell_spread_ratio | 1.2342768322980822 |
| stop_loss | 0.23937525090437597 |
| take_profit | 0.01814375078263392 |
| time_limit | 93445 |
| total_amount_quote | 736.7684441595574 |
| trailing_stop_activation | 0.005211177111754795 |
| trailing_stop_delta | 0.0018017400972094142 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 736.7684441595574 |
| Selected | 736.7684441595574 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.4847
- **Net PnL (quote)**: -3.5715
- **Sharpe Ratio**: -7.7886
- **Max Drawdown %**: 0.4866
- **Profit Factor**: 0.23011277513495737
- **Trade Count**: 18827
- **Total Fees (quote)**: 0.3709
- **Maker Fees**: 0.1341
- **Taker Fees**: 0.2368
- **Fee Drag %**: 0.0503
- **TP Min-Notional Failures**: 45 :warning:
  > 45 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0092
- **PnL Component**: -0.0049
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0036
- **Fee Drag Component**: -0.0003
- **Inventory Component**: -0.0005
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0519**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.05 | -42.52 | 0.05 | 1890 | -0.1129 | n/a |
| 1 | -0.03 | -16.75 | 0.03 | 1822 | -0.0241 | n/a |
| 2 | -0.03 | -15.63 | 0.03 | 1910 | -0.0644 | n/a |
| 3 | -0.04 | -26.19 | 0.04 | 2233 | -0.0386 | n/a |
| 4 | -0.01 | -9.05 | 0.01 | 1695 | -0.0058 | n/a |
| 5 | -0.02 | -13.12 | 0.02 | 2146 | -0.0512 | n/a |
| 6 | -0.02 | -24.24 | 0.02 | 1883 | -0.0004 | n/a |
| 7 | -0.01 | -21.28 | 0.01 | 1717 | -0.0003 | n/a |
| 8 | -0.02 | -15.51 | 0.02 | 2035 | -0.0653 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.0215)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.51 | -8.21 | 0.51 | -0.0125 |
| fees_2x | -0.54 | -8.63 | 0.54 | -0.0215 |
| latency_plus1 | -0.49 | -7.82 | 0.49 | -0.0092 |
| latency_plus2 | -0.48 | -7.84 | 0.49 | -0.0092 |
| latency_plus3 | -0.47 | -7.70 | 0.47 | -0.0089 |
| low_liquidity | -0.24 | -7.80 | 0.24 | -0.0046 |
| very_low_liquidity | -0.12 | -7.80 | 0.12 | -0.0023 |
| high_slippage | -0.49 | -7.93 | 0.49 | -0.0094 |
| extreme_slippage | -0.51 | -8.20 | 0.51 | -0.0122 |
| combined_adverse | -0.26 | -8.38 | 0.26 | -0.0102 |
| spread_widen_10bps | -0.50 | -7.75 | 0.50 | -0.0094 |
| spread_widen_25bps | -0.52 | -7.97 | 0.52 | -0.0099 |
| thin_book | -0.09 | -5.43 | 0.10 | -0.0019 |
| very_thin_book | -0.03 | -4.47 | 0.04 | -0.0007 |
| entry_spread_stress | -0.50 | -7.89 | 0.51 | -0.0096 |
| combined_market_deterioration | -0.17 | -5.73 | 0.17 | -0.0067 |
| severe_adverse | -0.09 | -6.77 | 0.09 | -0.0148 |

## Holdout Validation

- **Holdout bars**: 8820
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0075)
- **Trend**: ranging (efficiency: 0.0053)
- **Best holdout score**: -0.0004 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0153 | -0.0007 | -0.03 | 0.03 | 4089 |
| 1 | -0.0223 | -0.0011 | -0.01 | 0.04 | 3986 |
| 2 | -0.0225 | -0.0004 | 0.00 | 0.01 | 4204 |
| 3 | -0.0243 | -0.0006 | -0.02 | 0.03 | 4760 |
| 4 | -0.0258 | -0.1967 | -0.70 | 0.71 | 7920 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52165
- **Expected rows**: 52165
- **Missing rows**: 0
- **Forward-fill count**: 1806
- **Forward-fill fraction**: 0.03462091440621106
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0528 <= 0; recent PnL -0.0303% < 0
- **Objective score**: -0.05284217935990348
- **PnL %**: -0.030255591926711893
- **Trade count**: 4098

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0617 <= 0; recent PnL -0.0120% < 0
- **Objective score**: -0.06173175789278265
- **PnL %**: -0.011994637225131012
- **Trade count**: 2124

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0321 <= 0; recent PnL -0.0045% < 0
- **Objective score**: -0.03207144266435241
- **PnL %**: -0.004499446648799096
- **Trade count**: 1029

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.008945682806714548
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0090, -0.0091 |
| sell_spread_base | -0.0089, -0.0089 |
| stop_loss | -0.0091, -0.0078 |
| take_profit | -0.0089, -0.0089 |
| executor_refresh_time | -0.0091, -0.0089 |
| cooldown_time | -0.0089, -0.0089 |
| total_amount_quote | -0.0081, -0.0099 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.44182686705753205
- **Max CV**: 0.9024510945669972
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3550 | 0.26624824419484416 | 1.041027106671341 | 0.6087581707461246 |
| buy_spread_ratio | 0.1996 | 1.325492684882753 | 2.32385106158407 | 1.7535695685893207 |
| sell_spread_base | 0.9025 | 0.22277068934972794 | 2.515847061708216 | 0.7697578556709336 |
| sell_spread_ratio | 0.1193 | 1.2004246459336867 | 1.636392388747835 | 1.4192687501624535 |
| buy_side_weight | 0.4543 | 0.214820163312153 | 0.7297903283938623 | 0.4399133205201948 |
| amount_skew | 0.4029 | 1.1141746339272154 | 3.9092214279601705 | 2.499464346054057 |
| stop_loss | 0.2967 | 0.09622387988718703 | 0.24075655717169908 | 0.16857533772932187 |
| take_profit | 0.7346 | 0.0076567912969988695 | 0.0763860176941409 | 0.031657339379506946 |
| executor_refresh_time | 0.5243 | 503.0 | 4090.0 | 2412.2 |
| cooldown_time | 0.4763 | 83.0 | 548.0 | 355.6 |
| total_amount_quote | 0.3947 | 268.36599317768616 | 930.4599205303878 | 546.429293539725 |

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
| recent_objective | > 0 | -0.05284217935990348 | FAIL |
| recent_pnl | >= 0 | -0.030255591926711893 | FAIL |
| recent_trades | >= 5 | 4098 | PASS |
| worst_stress | > -10 | -0.021458615818226973 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.0006550163048975727 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.021458615818226973 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.05284217935990348, pnl=-0.030255591926711893, trades=4098, reason=recent objective score -0.0528 <= 0; recent PnL -0.0303% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.06173175789278265, pnl=-0.011994637225131012, trades=2124, reason=recent objective score -0.0617 <= 0; recent PnL -0.0120% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.03207144266435241, pnl=-0.004499446648799096, trades=1029, reason=recent objective score -0.0321 <= 0; recent PnL -0.0045% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.44182686705753205 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52165 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0528 <= 0; recent PnL -0.0303% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0617 <= 0; recent PnL -0.0120% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0321 <= 0; recent PnL -0.0045% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52165
- **Pre-release bars**: 44100
- **Dev bars**: 35280
- **Holdout bars**: 8820
- **Recent 28d bars**: 8065
- **Recent window start**: 1773370200

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-10T04:28:48.491767+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 14653
