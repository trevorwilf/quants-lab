# PMM Dynamic Optimization Report: nonkyc_ARRR-XMR_5m_sweep_v1

Generated: 2026-04-09 15:53:56 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T15:53:56.453052+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 5127 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-XMR
- **interval**: 5m
- **n_candles**: 52002
- **dataset_hash**: 83ecfc1cec5ca7e0470a5152727739829c646514c565a90bc5ab6600de83cbd1
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 845.3895338817255
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.9342239310623925 |
| buy_n_levels | 6 |
| buy_side_weight | 0.5437849606507733 |
| buy_spread_base | 4.591035691818173 |
| buy_spread_ratio | 1.2859409076348565 |
| cooldown_time | 97 |
| executor_refresh_time | 8718 |
| macd_fast | 22 |
| macd_signal | 16 |
| macd_slow | 99 |
| natr_length | 38 |
| sell_n_levels | 4 |
| sell_spread_base | 0.7441448900964734 |
| sell_spread_ratio | 2.6062297925918445 |
| stop_loss | 0.21102955802249254 |
| take_profit | 0.014623279036827171 |
| time_limit | 152689 |
| total_amount_quote | 845.3895338817255 |
| trailing_stop_activation | 0.041013155407421224 |
| trailing_stop_delta | 0.013945777653079293 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 845.3895338817255 |
| Selected | 845.3895338817255 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.0158
- **Net PnL (quote)**: -0.1333
- **Sharpe Ratio**: -0.2847
- **Max Drawdown %**: 0.1133
- **Profit Factor**: 0.8910473980593693
- **Trade Count**: 1467
- **Total Fees (quote)**: 0.1148
- **Maker Fees**: 0.0403
- **Taker Fees**: 0.0745
- **Fee Drag %**: 0.0136
- **TP Min-Notional Failures**: 37835 :warning:
  > 37835 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0014
- **PnL Component**: -0.0002
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0009
- **Fee Drag Component**: -0.0001
- **Inventory Component**: -0.0003
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0004**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 1.28 | 0.01 | 151 | -0.0000 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | -0.01 | -7.34 | 0.02 | 149 | -0.0003 | n/a |
| 4 | -0.00 | -2.53 | 0.00 | 81 | -0.0000 | n/a |
| 5 | -0.00 | -2.72 | 0.00 | 110 | -0.3025 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | -0.00 | -0.24 | 0.00 | 24 | -0.3936 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.0016)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.02 | -0.41 | 0.11 | -0.0015 |
| fees_2x | -0.03 | -0.53 | 0.12 | -0.0016 |
| latency_plus1 | -0.02 | -0.28 | 0.11 | -0.0014 |
| latency_plus2 | -0.02 | -0.29 | 0.11 | -0.0014 |
| latency_plus3 | -0.02 | -0.29 | 0.11 | -0.0014 |
| low_liquidity | -0.01 | -0.29 | 0.06 | -0.0007 |
| very_low_liquidity | -0.00 | -0.29 | 0.03 | -0.0004 |
| high_slippage | -0.02 | -0.32 | 0.11 | -0.0014 |
| extreme_slippage | -0.02 | -0.40 | 0.11 | -0.0015 |
| combined_adverse | -0.01 | -0.45 | 0.06 | -0.0008 |
| spread_widen_10bps | -0.02 | -0.31 | 0.11 | -0.0014 |
| spread_widen_25bps | -0.02 | -0.36 | 0.11 | -0.0014 |
| thin_book | 0.01 | 0.44 | 0.03 | -0.0002 |
| very_thin_book | 0.01 | 0.41 | 0.03 | -0.0002 |
| entry_spread_stress | -0.02 | -0.33 | 0.11 | -0.0014 |
| combined_market_deterioration | -0.00 | -0.14 | 0.04 | -0.0005 |
| severe_adverse | 0.00 | 0.17 | 0.03 | -0.0003 |

## Holdout Validation

- **Holdout bars**: 8787
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0075)
- **Trend**: ranging (efficiency: 0.0097)
- **Best holdout score**: -1000.0000 (rank #-1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0015 | -1000.0000 | 0.00 | 0.00 | 0 |
| 1 | 0.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | 0.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | 0.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 4 | -0.0000 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52002
- **Expected rows**: 52002
- **Missing rows**: 0
- **Forward-fill count**: 513
- **Forward-fill fraction**: 0.009865005192107996
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3936 <= 0; recent PnL -0.0000% < 0; recent worst stress -1000.0000 < -10.0
- **Objective score**: -0.39360556513570316
- **PnL %**: -2.670420500373837e-05
- **Trade count**: 24

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3936 <= 0; recent PnL -0.0000% < 0; recent worst stress -1000.0000 < -10.0
- **Objective score**: -0.39360559234723036
- **PnL %**: -2.670420500373837e-05
- **Trade count**: 24

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: -0.0012567582302454813
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0013, -0.0054 |
| sell_spread_base | -0.0013, -0.0013 |
| stop_loss | -0.0014, -0.0013 |
| take_profit | -0.0013, -0.0013 |
| executor_refresh_time | -0.0042, -0.0009 |
| cooldown_time | -0.0013, -0.0013 |
| total_amount_quote | -0.0011, -0.0014 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.39757084146064287
- **Max CV**: 1.0083532029931126
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1119 | 4.464557790565018 | 5.90934017143139 | 5.204154580333652 |
| buy_spread_ratio | 0.1321 | 1.4586918373297737 | 2.266847318074261 | 1.8748180815053501 |
| sell_spread_base | 1.0084 | 0.2256475306322356 | 3.7911922938136753 | 1.0668411115607712 |
| sell_spread_ratio | 0.2072 | 1.2359341625914035 | 2.33480580546042 | 1.603636717650442 |
| buy_side_weight | 0.3830 | 0.23766952309781847 | 0.7898596920265267 | 0.5528238182434119 |
| amount_skew | 0.4631 | 1.0119394559164385 | 3.5332963446435057 | 1.914808585670104 |
| stop_loss | 0.3426 | 0.07014793078069172 | 0.1915038576676091 | 0.1172740079875515 |
| take_profit | 0.5174 | 0.022730232236462852 | 0.12783679912494939 | 0.07331557655224633 |
| executor_refresh_time | 0.4226 | 1214.0 | 3788.0 | 2161.2 |
| cooldown_time | 0.3459 | 1707.0 | 6235.0 | 3988.9 |
| total_amount_quote | 0.4392 | 212.61062507866652 | 964.2530369048851 | 661.7576042664334 |

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
| recent_objective | > 0 | -0.39360556513570316 | FAIL |
| recent_pnl | >= 0 | -2.670420500373837e-05 | FAIL |
| recent_trades | >= 5 | 24 | PASS |
| worst_stress | > -10 | -0.0016284926860399935 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.0016284926860399935 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.39360556513570316, pnl=-2.670420500373837e-05, trades=24, reason=recent objective score -0.3936 <= 0; recent PnL -0.0000% < 0; recent worst stress -1000.0000 < -10.0 |
| recent_14d_info | FAIL | informational only; score=-0.39360559234723036, pnl=-2.670420500373837e-05, trades=24, reason=recent objective score -0.3936 <= 0; recent PnL -0.0000% < 0; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.39757084146064287 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52002 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3936 <= 0; recent PnL -0.0000% < 0; recent worst stress -1000.0000 < -10.0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3936 <= 0; recent PnL -0.0000% < 0; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52002
- **Pre-release bars**: 43937
- **Dev bars**: 35150
- **Holdout bars**: 8787
- **Recent 28d bars**: 8065
- **Recent window start**: 1773321300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T15:53:56.453052+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 5127
