# PMM Dynamic Optimization Report: nonkyc_BDX-USDT_5m_sweep_v1

Generated: 2026-04-09 17:10:19 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T17:10:19.960812+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 3288 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BDX-USDT
- **interval**: 5m
- **n_candles**: 52002
- **dataset_hash**: 8a1e4bdd3ed24a0a6fc0ac7812e4f853254e8f65637e894ef53028de57317d8e
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 777.3593078955984
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.8729923610111148 |
| buy_n_levels | 5 |
| buy_side_weight | 0.7787296725839953 |
| buy_spread_base | 3.839622549181243 |
| buy_spread_ratio | 1.882355880940274 |
| cooldown_time | 7083 |
| executor_refresh_time | 3119 |
| macd_fast | 21 |
| macd_signal | 7 |
| macd_slow | 77 |
| natr_length | 39 |
| sell_n_levels | 3 |
| sell_spread_base | 1.603295089924476 |
| sell_spread_ratio | 1.973330525005486 |
| stop_loss | 0.175016232951813 |
| take_profit | 0.005875808737430669 |
| time_limit | 76595 |
| total_amount_quote | 777.3593078955984 |
| trailing_stop_activation | 0.008308515290431761 |
| trailing_stop_delta | 0.001927431002484069 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 777.3593078955984 |
| Selected | 777.3593078955984 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 0.2971
- **Net PnL (quote)**: 2.3099
- **Sharpe Ratio**: 0.1696
- **Max Drawdown %**: 4.5111
- **Profit Factor**: 1.0213604782691683
- **Trade Count**: 2645
- **Total Fees (quote)**: 43.7952
- **Maker Fees**: 27.3300
- **Taker Fees**: 16.4652
- **Fee Drag %**: 5.6338
- **TP Min-Notional Failures**: 6884 :warning:
  > 6884 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1063
- **PnL Component**: 0.0030
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0338
- **Fee Drag Component**: -0.0282
- **Inventory Component**: -0.0469
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0498**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.27 | -11.42 | 0.27 | 74 | -0.1799 | n/a |
| 1 | 0.04 | 3.09 | 0.03 | 37 | -0.0540 | n/a |
| 2 | 0.04 | 1.88 | 0.07 | 64 | -0.0027 | n/a |
| 3 | -0.27 | -7.52 | 0.36 | 143 | -0.0341 | n/a |
| 4 | -0.24 | -2.80 | 0.46 | 135 | -0.0384 | n/a |
| 5 | 0.08 | 2.44 | 0.11 | 71 | -0.0027 | n/a |
| 6 | 0.00 | 0.09 | 0.07 | 160 | -0.0091 | n/a |
| 7 | -0.04 | -0.21 | 0.37 | 152 | -0.0787 | n/a |
| 8 | 0.89 | 3.20 | 0.54 | 144 | 0.0020 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.2167)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.52 | -1.13 | 5.47 | -0.1572 |
| fees_2x | -5.34 | -2.41 | 7.45 | -0.2167 |
| latency_plus1 | 0.28 | 0.16 | 4.47 | -0.1057 |
| latency_plus2 | 0.63 | 0.28 | 5.37 | -0.1193 |
| latency_plus3 | 0.32 | 0.16 | 5.34 | -0.1217 |
| low_liquidity | -1.90 | -0.76 | 5.77 | -0.1414 |
| very_low_liquidity | -1.90 | -0.96 | 4.57 | -0.1218 |
| high_slippage | -0.23 | -0.08 | 4.67 | -0.1131 |
| extreme_slippage | -1.29 | -0.56 | 4.99 | -0.1266 |
| combined_adverse | -5.33 | -2.15 | 7.94 | -0.2078 |
| spread_widen_10bps | -0.69 | -0.29 | 4.58 | -0.1172 |
| spread_widen_25bps | -2.09 | -0.69 | 6.69 | -0.1659 |
| thin_book | -0.72 | -0.35 | 4.67 | -0.1055 |
| very_thin_book | -1.19 | -1.10 | 2.63 | -0.0668 |
| entry_spread_stress | -1.99 | -0.62 | 6.78 | -0.1694 |
| combined_market_deterioration | -3.75 | -1.63 | 6.50 | -0.1731 |
| severe_adverse | -6.21 | -3.97 | 7.56 | -0.1894 |

## Holdout Validation

- **Holdout bars**: 8787
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0014)
- **Trend**: ranging (efficiency: 0.0009)
- **Best holdout score**: -0.0120 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1615 | -0.0156 | -0.07 | 0.39 | 325 |
| 1 | -0.0203 | -0.0120 | 0.28 | 0.42 | 284 |
| 2 | -0.0217 | -0.0246 | 0.14 | 0.70 | 603 |
| 3 | -0.0223 | -0.0325 | 0.55 | 0.93 | 864 |
| 4 | -0.0236 | -0.0145 | 0.43 | 0.35 | 502 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52002
- **Expected rows**: 52002
- **Missing rows**: 0
- **Forward-fill count**: 1639
- **Forward-fill fraction**: 0.03151801853774855
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.0010732639517713066
- **PnL %**: 0.8257455535236704
- **Trade count**: 179

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1118 <= 0; recent PnL -0.0562% < 0
- **Objective score**: -0.11183315501021382
- **PnL %**: -0.05617715294934478
- **Trade count**: 37

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1499 <= 0
- **Objective score**: -0.1499477114915886
- **PnL %**: 0.023635158237670328
- **Trade count**: 13

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: -0.08929705908751231
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1430, -0.1254 |
| sell_spread_base | -0.0790, -0.1170 |
| stop_loss | -0.0893, -0.0893 |
| take_profit | -0.1347, -0.1275 |
| executor_refresh_time | -0.0967, -0.1048 |
| cooldown_time | -0.0770, -0.1367 |
| total_amount_quote | -0.0864, -0.0947 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.38276606169231875
- **Max CV**: 1.033916357407096
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, cooldown_time, total_amount_quote
- **Scattered params**: stop_loss, take_profit, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1515 | 3.2584824126639584 | 5.091617298910973 | 3.9532188343881236 |
| buy_spread_ratio | 0.1477 | 1.403510304406239 | 2.45476810823016 | 2.0711670138074045 |
| sell_spread_base | 0.4310 | 0.20101046144498708 | 0.6131782072592514 | 0.31025795190888006 |
| sell_spread_ratio | 0.1941 | 1.347518010896044 | 2.3012036330734023 | 1.8357847096131625 |
| buy_side_weight | 0.3965 | 0.20412129161790932 | 0.6224715986918986 | 0.30181841737944304 |
| amount_skew | 0.3094 | 1.466808668749796 | 3.8832449381692578 | 2.7402141983621267 |
| stop_loss | 0.6779 | 0.015244258243307487 | 0.2206051424101858 | 0.11629484755340666 |
| take_profit | 1.0339 | 0.00501946299372854 | 0.03014068520424355 | 0.0076455070382336395 |
| executor_refresh_time | 0.7269 | 1769.0 | 12066.0 | 5315.1 |
| cooldown_time | 0.0798 | 5822.0 | 7185.0 | 6638.5 |
| total_amount_quote | 0.0617 | 823.0955316455045 | 984.8735941418008 | 920.0180411628498 |

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
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.0010732639517713066 | PASS |
| recent_pnl | >= 0 | 0.8257455535236704 | PASS |
| recent_trades | >= 5 | 179 | PASS |
| worst_stress | > -10 | -0.21670459904155137 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.01559913453193566 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.21670459904155137 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | PASS | score=0.0010732639517713066, pnl=0.8257455535236704, trades=179, reason= |
| recent_14d_info | FAIL | informational only; score=-0.11183315501021382, pnl=-0.05617715294934478, trades=37, reason=recent objective score -0.1118 <= 0; recent PnL -0.0562% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.1499477114915886, pnl=0.023635158237670328, trades=13, reason=recent objective score -0.1499 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.38276606169231875 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52002 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1118 <= 0; recent PnL -0.0562% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1499 <= 0 |
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
- **run_timestamp**: 2026-04-09T17:10:19.960812+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 3288
