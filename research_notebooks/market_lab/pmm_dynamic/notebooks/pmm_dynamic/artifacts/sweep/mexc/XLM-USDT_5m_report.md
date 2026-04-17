# PMM Dynamic Optimization Report: mexc_XLM-USDT_5m_sweep_v1

Generated: 2026-04-09 11:57:02 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T11:57:02.251785+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 1430 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XLM-USDT
- **interval**: 5m
- **n_candles**: 51914
- **dataset_hash**: e70edc4e78a97d0583cb0a8b24b94948057cea51a2b8b4ae543b1b56c96fd7bd
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 734.592077061246
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.8878866298863972 |
| buy_n_levels | 10 |
| buy_side_weight | 0.7811402580602204 |
| buy_spread_base | 1.0238373014636928 |
| buy_spread_ratio | 1.572920471297722 |
| cooldown_time | 975 |
| executor_refresh_time | 1414 |
| macd_fast | 26 |
| macd_signal | 27 |
| macd_slow | 28 |
| natr_length | 29 |
| sell_n_levels | 4 |
| sell_spread_base | 2.545769044222338 |
| sell_spread_ratio | 2.9093282020680276 |
| stop_loss | 0.2438756020213273 |
| take_profit | 0.01928926424610302 |
| time_limit | 31226 |
| total_amount_quote | 734.592077061246 |
| trailing_stop_activation | 0.0017538281237189758 |
| trailing_stop_delta | 0.0010839072045955031 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 734.592077061246 |
| Selected | 734.592077061246 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 4.8810
- **Net PnL (quote)**: 35.8556
- **Sharpe Ratio**: 2.2295
- **Max Drawdown %**: 1.3715
- **Profit Factor**: 5.087023019536844
- **Trade Count**: 695
- **Total Fees (quote)**: 3.6537
- **Maker Fees**: 1.8240
- **Taker Fees**: 1.8297
- **Fee Drag %**: 0.4974

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0289
- **PnL Component**: 0.0477
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0103
- **Fee Drag Component**: -0.0025
- **Inventory Component**: -0.0059
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0012**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.10 | 4.14 | 0.08 | 59 | 0.0002 | n/a |
| 1 | 0.09 | 4.59 | 0.08 | 69 | 0.0001 | n/a |
| 2 | 3.09 | 5.19 | 0.04 | 44 | 0.0059 | n/a |
| 3 | 0.06 | 3.83 | 0.06 | 74 | -0.0001 | n/a |
| 4 | 0.41 | 1.06 | 1.15 | 49 | -0.0089 | n/a |
| 5 | 0.37 | 6.00 | 0.10 | 73 | 0.0026 | n/a |
| 6 | 0.08 | 3.01 | 0.13 | 48 | -0.0084 | n/a |
| 7 | 0.17 | 5.96 | 0.10 | 54 | 0.0008 | n/a |
| 8 | 0.46 | 5.80 | 0.06 | 21 | -0.1120 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0549)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 4.63 | 2.12 | 1.40 | 0.0250 |
| fees_2x | 4.38 | 2.01 | 1.43 | 0.0212 |
| latency_plus1 | 4.67 | 2.02 | 1.57 | 0.0252 |
| latency_plus2 | 4.27 | 1.71 | 2.03 | 0.0185 |
| latency_plus3 | 0.97 | 0.55 | 2.07 | -0.0138 |
| low_liquidity | 4.88 | 2.23 | 1.37 | 0.0289 |
| very_low_liquidity | 4.88 | 2.23 | 1.37 | 0.0289 |
| high_slippage | 4.26 | 1.95 | 1.43 | 0.0225 |
| extreme_slippage | 3.01 | 1.40 | 1.55 | 0.0033 |
| combined_adverse | 3.81 | 1.66 | 1.66 | 0.0151 |
| spread_widen_10bps | 4.85 | 2.13 | 1.43 | 0.0282 |
| spread_widen_25bps | 2.39 | 1.09 | 1.98 | -0.0038 |
| thin_book | -0.40 | -0.39 | 1.58 | -0.0235 |
| very_thin_book | -0.47 | -0.96 | 0.85 | -0.0139 |
| entry_spread_stress | 3.43 | 1.57 | 1.71 | 0.0105 |
| combined_market_deterioration | 1.67 | 0.94 | 1.20 | -0.0044 |
| severe_adverse | -1.85 | -1.86 | 2.70 | -0.0549 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0033)
- **Trend**: ranging (efficiency: 0.0020)
- **Best holdout score**: 0.0040 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0130 | 0.0017 | 0.30 | 0.13 | 110 |
| 1 | 0.0017 | -0.0008 | 0.34 | 0.32 | 103 |
| 2 | 0.0012 | -0.0307 | 0.85 | 1.05 | 250 |
| 3 | 0.0011 | -0.0257 | 1.99 | 1.11 | 305 |
| 4 | 0.0008 | 0.0040 | 0.94 | 0.63 | 94 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51914
- **Expected rows**: 51914
- **Missing rows**: 0
- **Forward-fill count**: 14
- **Forward-fill fraction**: 0.0002696767731247833
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0263 <= 0
- **Objective score**: -0.026303404472818703
- **PnL %**: 0.4358650161624425
- **Trade count**: 43

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1046 <= 0; recent PnL -0.0111% < 0
- **Objective score**: -0.10456875725528701
- **PnL %**: -0.011123818967413573
- **Trade count**: 24

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2818 <= 0; recent PnL -0.0148% < 0; recent worst stress -1000.0000 < -10.0
- **Objective score**: -0.28176845456853983
- **PnL %**: -0.014798753361973947
- **Trade count**: 6

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.033531443422074675
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0279, 0.0339 |
| sell_spread_base | 0.0338, 0.0315 |
| stop_loss | 0.0335, 0.0335 |
| take_profit | 0.0335, 0.0335 |
| executor_refresh_time | 0.0295, 0.0335 |
| cooldown_time | 0.0335, 0.0401 |
| total_amount_quote | 0.0335, 0.0335 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4995691786713124
- **Max CV**: 1.2140724295553955
- **Clustered params**: buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, total_amount_quote
- **Scattered params**: buy_spread_base, sell_spread_base, stop_loss, take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.5199 | 0.21856194556728423 | 1.4609369642279932 | 0.6998422339189241 |
| buy_spread_ratio | 0.1824 | 1.2770018728720953 | 2.1627117165688654 | 1.5935789103589122 |
| sell_spread_base | 0.9410 | 0.2034675868230819 | 2.1499775037925755 | 0.6426260237639374 |
| sell_spread_ratio | 0.2930 | 1.420269353712622 | 2.958179493906688 | 2.200343823997012 |
| buy_side_weight | 0.2891 | 0.25533254112538545 | 0.7411505232028274 | 0.5085273430486794 |
| amount_skew | 0.1785 | 1.4008511697900616 | 2.6078439893780097 | 1.8489421602089293 |
| stop_loss | 1.2141 | 0.016153213940544087 | 0.23785600446799363 | 0.06975327790187938 |
| take_profit | 0.8532 | 0.005700239110012253 | 0.09004825194089047 | 0.03382954914104985 |
| executor_refresh_time | 0.1708 | 8723.0 | 13351.0 | 11423.1 |
| cooldown_time | 0.6356 | 92.0 | 6435.0 | 3352.9 |
| total_amount_quote | 0.2178 | 577.61525171835 | 985.5462373204452 | 813.8372677768562 |

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
- walkforward_positive_majority: PASS
- holdout_passed: PASS
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
| recent_objective | > 0 | -0.026303404472818703 | FAIL |
| recent_pnl | >= 0 | 0.4358650161624425 | PASS |
| recent_trades | >= 5 | 43 | PASS |
| worst_stress | > -10 | -0.05490967378461272 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0017 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.05490967378461272 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.026303404472818703, pnl=0.4358650161624425, trades=43, reason=recent objective score -0.0263 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.10456875725528701, pnl=-0.011123818967413573, trades=24, reason=recent objective score -0.1046 <= 0; recent PnL -0.0111% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.28176845456853983, pnl=-0.014798753361973947, trades=6, reason=recent objective score -0.2818 <= 0; recent PnL -0.0148% < 0; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4995691786713124 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51914 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0263 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1046 <= 0; recent PnL -0.0111% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2818 <= 0; recent PnL -0.0148% < 0; recent worst stress -1000.0000 < -10.0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51914
- **Pre-release bars**: 43849
- **Dev bars**: 35080
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065
- **Recent window start**: 1773294300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T11:57:02.251785+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 1430
