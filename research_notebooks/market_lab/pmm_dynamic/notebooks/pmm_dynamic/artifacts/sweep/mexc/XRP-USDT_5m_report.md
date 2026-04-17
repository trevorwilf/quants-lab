# PMM Dynamic Optimization Report: mexc_XRP-USDT_5m_sweep_v1

Generated: 2026-04-09 13:15:56 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T13:15:56.989119+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 14188 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XRP-USDT
- **interval**: 5m
- **n_candles**: 51937
- **dataset_hash**: 59b89bb2cf09f50c142fc6b56c410a4bec80a1762e258d75e7b75726334e74c7
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 993.652959503227
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.272887260417568 |
| buy_n_levels | 7 |
| buy_side_weight | 0.26121522583416906 |
| buy_spread_base | 2.501251750257364 |
| buy_spread_ratio | 2.6669321547682525 |
| cooldown_time | 2441 |
| executor_refresh_time | 7943 |
| macd_fast | 19 |
| macd_signal | 25 |
| macd_slow | 42 |
| natr_length | 17 |
| sell_n_levels | 6 |
| sell_spread_base | 4.062160436141993 |
| sell_spread_ratio | 2.39221641789703 |
| stop_loss | 0.015183561307951765 |
| take_profit | 0.005101343069590253 |
| time_limit | 24497 |
| total_amount_quote | 993.652959503227 |
| trailing_stop_activation | 0.03257349921817145 |
| trailing_stop_delta | 0.027308017092941794 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 993.652959503227 |
| Selected | 993.652959503227 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0860
- **Net PnL (quote)**: -10.7907
- **Sharpe Ratio**: -3.3925
- **Max Drawdown %**: 1.5101
- **Profit Factor**: 0.7762889241259705
- **Trade Count**: 920
- **Total Fees (quote)**: 2.2930
- **Maker Fees**: 1.9345
- **Taker Fees**: 0.3585
- **Fee Drag %**: 0.2308
- **TP Min-Notional Failures**: 3411 :warning:
  > 3411 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0293
- **PnL Component**: -0.0109
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0113
- **Fee Drag Component**: -0.0012
- **Inventory Component**: -0.0058
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0139**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.09 | -6.88 | 0.14 | 58 | -0.0033 | n/a |
| 1 | -0.02 | -1.40 | 0.05 | 46 | -0.0179 | n/a |
| 2 | -0.02 | -1.57 | 0.05 | 40 | -0.0432 | n/a |
| 3 | -0.02 | -1.60 | 0.05 | 52 | -0.0019 | n/a |
| 4 | -0.18 | -6.94 | 0.20 | 53 | -0.0098 | n/a |
| 5 | -0.10 | -8.01 | 0.12 | 64 | -0.0034 | n/a |
| 6 | 0.03 | 1.95 | 0.08 | 51 | -0.0017 | n/a |
| 7 | -0.00 | -0.46 | 0.04 | 35 | -0.0617 | n/a |
| 8 | -0.11 | -4.41 | 0.19 | 44 | -0.0279 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.0343)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.20 | -3.75 | 1.61 | -0.0318 |
| fees_2x | -1.32 | -4.11 | 1.71 | -0.0343 |
| latency_plus1 | -0.82 | -3.87 | 1.08 | -0.0209 |
| latency_plus2 | -0.82 | -3.88 | 1.08 | -0.0210 |
| latency_plus3 | -0.86 | -4.08 | 1.11 | -0.0215 |
| low_liquidity | -1.09 | -3.39 | 1.51 | -0.0293 |
| very_low_liquidity | -1.09 | -3.39 | 1.51 | -0.0293 |
| high_slippage | -1.18 | -3.67 | 1.59 | -0.0308 |
| extreme_slippage | -1.36 | -4.21 | 1.76 | -0.0339 |
| combined_adverse | -0.99 | -4.65 | 1.23 | -0.0242 |
| spread_widen_10bps | -0.86 | -5.01 | 0.94 | -0.0192 |
| spread_widen_25bps | -1.34 | -5.57 | 1.57 | -0.0306 |
| thin_book | -0.97 | -5.94 | 1.05 | -0.0209 |
| very_thin_book | -1.04 | -8.82 | 1.05 | -0.0201 |
| entry_spread_stress | -1.34 | -4.16 | 1.69 | -0.0333 |
| combined_market_deterioration | -1.48 | -6.06 | 1.69 | -0.0329 |
| severe_adverse | -1.63 | -10.77 | 1.63 | -0.0311 |

## Holdout Validation

- **Holdout bars**: 8786
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0030)
- **Trend**: ranging (efficiency: 0.0025)
- **Best holdout score**: -0.0015 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0318 | -0.0015 | 0.06 | 0.09 | 98 |
| 1 | -0.0029 | -0.0164 | -0.36 | 0.51 | 416 |
| 2 | -0.0030 | -0.0103 | -0.37 | 0.45 | 141 |
| 3 | -0.0033 | -0.0055 | -0.20 | 0.25 | 112 |
| 4 | -0.0035 | -0.0252 | -0.23 | 0.74 | 390 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51937
- **Expected rows**: 51995
- **Missing rows**: 58
- **Forward-fill count**: 660
- **Forward-fill fraction**: 0.012707703563933227
- **Longest gap (seconds)**: 6600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0040 <= 0; recent PnL -0.1007% < 0
- **Objective score**: -0.003954784731751482
- **PnL %**: -0.1006517784902776
- **Trade count**: 88

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0216 <= 0
- **Objective score**: -0.021649950046716857
- **PnL %**: 0.010693506690859647
- **Trade count**: 45

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1256 <= 0; recent PnL -0.0055% < 0
- **Objective score**: -0.12559549811358986
- **PnL %**: -0.0054751920849085475
- **Trade count**: 19

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: -0.03601399847329597
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0697, -0.0443 |
| sell_spread_base | -0.0151, -0.0436 |
| stop_loss | -0.0203, -0.0095 |
| take_profit | -0.0327, -0.0147 |
| executor_refresh_time | -0.0294, -0.0095 |
| cooldown_time | -0.0360, -0.0183 |
| total_amount_quote | -0.0346, -0.0752 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.30448183270312434
- **Max CV**: 0.7976394057764516
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1297 | 1.7227252128187485 | 2.4685888302251064 | 2.120776066510773 |
| buy_spread_ratio | 0.1123 | 2.063336936489606 | 2.9609025923046786 | 2.550910967041337 |
| sell_spread_base | 0.7976 | 0.23027329029400748 | 4.139956148351211 | 1.9214664625845657 |
| sell_spread_ratio | 0.1637 | 1.828248576332077 | 2.8702661158536076 | 2.481867714650251 |
| buy_side_weight | 0.2896 | 0.20429922084270097 | 0.489488113481302 | 0.293719845121304 |
| amount_skew | 0.1760 | 2.1332122067212445 | 3.809930745709634 | 3.000958720973686 |
| stop_loss | 0.4181 | 0.010068640899864058 | 0.029488203946941956 | 0.014432587875973613 |
| take_profit | 0.1501 | 0.005220537969454127 | 0.0075334985654098375 | 0.00617563850991586 |
| executor_refresh_time | 0.4728 | 2422.0 | 12722.0 | 6652.0 |
| cooldown_time | 0.5217 | 456.0 | 5986.0 | 3264.8 |
| total_amount_quote | 0.1176 | 623.1545775164891 | 987.206162878635 | 910.9638548227373 |

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
| recent_objective | > 0 | -0.003954784731751482 | FAIL |
| recent_pnl | >= 0 | -0.1006517784902776 | FAIL |
| recent_trades | >= 5 | 88 | PASS |
| worst_stress | > -10 | -0.034270332982775945 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.001549270962161224 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.034270332982775945 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.003954784731751482, pnl=-0.1006517784902776, trades=88, reason=recent objective score -0.0040 <= 0; recent PnL -0.1007% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.021649950046716857, pnl=0.010693506690859647, trades=45, reason=recent objective score -0.0216 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.12559549811358986, pnl=-0.0054751920849085475, trades=19, reason=recent objective score -0.1256 <= 0; recent PnL -0.0055% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.30448183270312434 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51937 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0040 <= 0; recent PnL -0.1007% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0216 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1256 <= 0; recent PnL -0.0055% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51937
- **Pre-release bars**: 43930
- **Dev bars**: 35144
- **Holdout bars**: 8786
- **Recent 28d bars**: 8007
- **Recent window start**: 1773318600

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T13:15:56.989119+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 14188
