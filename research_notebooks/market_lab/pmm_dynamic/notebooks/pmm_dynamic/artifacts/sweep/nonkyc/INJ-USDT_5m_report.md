# PMM Dynamic Optimization Report: nonkyc_INJ-USDT_5m_sweep_v1

Generated: 2026-04-09 20:53:21 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T20:53:21.023149+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 9261 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: INJ-USDT
- **interval**: 5m
- **n_candles**: 52059
- **dataset_hash**: 87b2203fbd05d8a6084732a8348e531148a919268c5953fe4a3e5d0a4b49b886
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 974.1177151987167
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.894587464427536 |
| buy_n_levels | 6 |
| buy_side_weight | 0.5448899832337432 |
| buy_spread_base | 1.841720830084332 |
| buy_spread_ratio | 2.8529415222252945 |
| cooldown_time | 6967 |
| executor_refresh_time | 3580 |
| macd_fast | 36 |
| macd_signal | 19 |
| macd_slow | 67 |
| natr_length | 34 |
| sell_n_levels | 4 |
| sell_spread_base | 5.385378447676932 |
| sell_spread_ratio | 2.393462770566679 |
| stop_loss | 0.05559804417000102 |
| take_profit | 0.00569685930438815 |
| time_limit | 32904 |
| total_amount_quote | 974.1177151987167 |
| trailing_stop_activation | 0.08616395607332421 |
| trailing_stop_delta | 0.014175745355268875 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 974.1177151987167 |
| Selected | 974.1177151987167 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -23.3632
- **Net PnL (quote)**: -227.5852
- **Sharpe Ratio**: -10.2900
- **Max Drawdown %**: 24.0126
- **Profit Factor**: 0.18031757925510108
- **Trade Count**: 1278
- **Total Fees (quote)**: 46.8420
- **Maker Fees**: 31.4859
- **Taker Fees**: 15.3561
- **Fee Drag %**: 4.8087
- **TP Min-Notional Failures**: 50328 :warning:
  > 50328 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.5110
- **PnL Component**: -0.2661
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1801
- **Fee Drag Component**: -0.0240
- **Inventory Component**: -0.0402
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1099**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.28 | -14.66 | 1.29 | 82 | -0.0423 | n/a |
| 1 | -1.99 | -19.35 | 2.04 | 104 | -0.0493 | n/a |
| 2 | -1.25 | -20.60 | 1.28 | 156 | -0.0852 | n/a |
| 3 | -0.78 | -13.23 | 0.86 | 131 | -0.0366 | n/a |
| 4 | -2.76 | -9.94 | 3.44 | 183 | -0.0897 | n/a |
| 5 | -3.15 | -17.78 | 3.21 | 246 | -0.1457 | n/a |
| 6 | -1.86 | -18.88 | 1.98 | 227 | -0.0932 | n/a |
| 7 | -1.48 | -17.79 | 1.48 | 238 | -0.0944 | n/a |
| 8 | -6.15 | -21.58 | 6.15 | 340 | -0.2047 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.6384)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -25.76 | -11.24 | 26.27 | -0.5723 |
| fees_2x | -28.16 | -12.15 | 28.53 | -0.6384 |
| latency_plus1 | -23.46 | -10.47 | 23.79 | -0.5080 |
| latency_plus2 | -22.09 | -9.97 | 22.42 | -0.4747 |
| latency_plus3 | -23.83 | -10.32 | 24.16 | -0.5118 |
| low_liquidity | -22.74 | -10.44 | 23.17 | -0.4921 |
| very_low_liquidity | -23.59 | -10.87 | 23.70 | -0.5184 |
| high_slippage | -23.75 | -10.44 | 24.38 | -0.5189 |
| extreme_slippage | -24.54 | -10.73 | 25.14 | -0.5352 |
| combined_adverse | -25.66 | -11.63 | 25.90 | -0.5690 |
| spread_widen_10bps | -22.80 | -11.17 | 23.11 | -0.4945 |
| spread_widen_25bps | -24.31 | -9.88 | 24.91 | -0.5284 |
| thin_book | -21.26 | -10.76 | 21.76 | -0.4563 |
| very_thin_book | -18.14 | -10.14 | 18.36 | -0.3872 |
| entry_spread_stress | -23.19 | -11.30 | 23.46 | -0.4975 |
| combined_market_deterioration | -24.81 | -12.20 | 25.18 | -0.5437 |
| severe_adverse | -28.55 | -12.61 | 28.71 | -0.6365 |

## Holdout Validation

- **Holdout bars**: 8799
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0021)
- **Trend**: ranging (efficiency: 0.0033)
- **Best holdout score**: -0.1329 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.5747 | -0.1329 | -3.71 | 3.71 | 513 |
| 1 | -0.0450 | -0.2659 | -10.33 | 10.43 | 1023 |
| 2 | -0.0462 | -0.5400 | -17.17 | 19.29 | 1174 |
| 3 | -0.0503 | -0.4157 | -11.96 | 12.86 | 992 |
| 4 | -0.0519 | -0.3906 | -9.83 | 14.96 | 945 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52059
- **Expected rows**: 52060
- **Missing rows**: 1
- **Forward-fill count**: 2309
- **Forward-fill fraction**: 0.044353521965462266
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2814 <= 0; recent PnL -8.7541% < 0
- **Objective score**: -0.28141334309788
- **PnL %**: -8.754083556200607
- **Trade count**: 765

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1891 <= 0; recent PnL -3.1484% < 0
- **Objective score**: -0.18906368493860998
- **PnL %**: -3.148394718158829
- **Trade count**: 486

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0686 <= 0; recent PnL -0.4826% < 0
- **Objective score**: -0.06860464838870989
- **PnL %**: -0.4826132520110617
- **Trade count**: 117

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.8672865710568775
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.7352, -0.8999 |
| sell_spread_base | -0.8535, -0.9435 |
| stop_loss | -0.8923, -0.8686 |
| take_profit | -0.8220, -0.8516 |
| executor_refresh_time | -0.8565, -0.8349 |
| cooldown_time | -0.8675, -0.9160 |
| total_amount_quote | -0.8419, -0.8824 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.18572577329002996
- **Max CV**: 0.4939093733324568
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0841 | 2.2227160558195735 | 2.9991918436436857 | 2.5196488178852725 |
| buy_spread_ratio | 0.0637 | 2.196510557774611 | 2.709384321538051 | 2.4413046950791832 |
| sell_spread_base | 0.4939 | 0.3356512797866402 | 1.560125587112724 | 0.7270417084316735 |
| sell_spread_ratio | 0.1314 | 1.2344992672455 | 1.8403460254087212 | 1.4088484159581143 |
| buy_side_weight | 0.1747 | 0.40389342423462826 | 0.7076470312842644 | 0.5444180354879702 |
| amount_skew | 0.0757 | 3.2203613057980274 | 3.9076716859263856 | 3.6274535787392588 |
| stop_loss | 0.3494 | 0.08516349832890471 | 0.2431957615501422 | 0.167559437400341 |
| take_profit | 0.1176 | 0.005227266204438726 | 0.007151753661430733 | 0.006022561099359309 |
| executor_refresh_time | 0.4153 | 1304.0 | 4323.0 | 2505.1 |
| cooldown_time | 0.0427 | 6241.0 | 7099.0 | 6779.8 |
| total_amount_quote | 0.0945 | 695.7982671470967 | 994.6470643994412 | 908.5331279918573 |

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
| recent_objective | > 0 | -0.28141334309788 | FAIL |
| recent_pnl | >= 0 | -8.754083556200607 | FAIL |
| recent_trades | >= 5 | 765 | PASS |
| worst_stress | > -10 | -0.6383748421247141 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.13290787820191813 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.6383748421247141 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.28141334309788, pnl=-8.754083556200607, trades=765, reason=recent objective score -0.2814 <= 0; recent PnL -8.7541% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.18906368493860998, pnl=-3.148394718158829, trades=486, reason=recent objective score -0.1891 <= 0; recent PnL -3.1484% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.06860464838870989, pnl=-0.4826132520110617, trades=117, reason=recent objective score -0.0686 <= 0; recent PnL -0.4826% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.18572577329002996 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52059 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2814 <= 0; recent PnL -8.7541% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1891 <= 0; recent PnL -3.1484% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0686 <= 0; recent PnL -0.4826% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52059
- **Pre-release bars**: 43995
- **Dev bars**: 35196
- **Holdout bars**: 8799
- **Recent 28d bars**: 8064
- **Recent window start**: 1773338400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T20:53:21.023149+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 9261
