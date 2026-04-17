# PMM Dynamic Optimization Report: mexc_SUI-USDT_5m_sweep_v1

Generated: 2026-04-09 09:03:03 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T09:03:03.442480+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 12801 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SUI-USDT
- **interval**: 5m
- **n_candles**: 51916
- **dataset_hash**: 57c55562dfecf5f1952daabf3aa5ef4367c7d17017654e19dd5386465ffde185
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 859.7689390449555
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.8926605445572693 |
| buy_n_levels | 9 |
| buy_side_weight | 0.5523306648406546 |
| buy_spread_base | 1.9242449090565126 |
| buy_spread_ratio | 2.842949363473598 |
| cooldown_time | 3513 |
| executor_refresh_time | 4646 |
| macd_fast | 49 |
| macd_signal | 8 |
| macd_slow | 82 |
| natr_length | 45 |
| sell_n_levels | 6 |
| sell_spread_base | 4.528567247643197 |
| sell_spread_ratio | 1.493886086731313 |
| stop_loss | 0.023555777060776575 |
| take_profit | 0.011133884110109418 |
| time_limit | 45512 |
| total_amount_quote | 859.7689390449555 |
| trailing_stop_activation | 0.0028011216452431854 |
| trailing_stop_delta | 0.00134385512069689 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 859.7689390449555 |
| Selected | 859.7689390449555 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.0002
- **Net PnL (quote)**: -0.0014
- **Sharpe Ratio**: 0.0131
- **Max Drawdown %**: 1.9104
- **Profit Factor**: 0.9999648650516983
- **Trade Count**: 749
- **Total Fees (quote)**: 3.4008
- **Maker Fees**: 1.7000
- **Taker Fees**: 1.7008
- **Fee Drag %**: 0.3955

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0181
- **PnL Component**: -0.0000
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0143
- **Fee Drag Component**: -0.0020
- **Inventory Component**: -0.0017
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0047**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.27 | -5.21 | 0.42 | 81 | -0.0077 | n/a |
| 1 | -0.02 | -0.76 | 0.09 | 77 | -0.0028 | n/a |
| 2 | -0.05 | -3.40 | 0.10 | 56 | -0.0032 | n/a |
| 3 | 0.13 | 8.65 | 0.07 | 77 | -0.0011 | n/a |
| 4 | -1.24 | -4.55 | 1.54 | 79 | -0.0262 | n/a |
| 5 | 0.60 | 10.97 | 0.13 | 82 | 0.0030 | n/a |
| 6 | 0.26 | 11.01 | 0.06 | 79 | 0.0002 | n/a |
| 7 | 0.13 | 12.52 | 0.02 | 59 | 0.0010 | n/a |
| 8 | -0.36 | -7.93 | 0.39 | 58 | -0.0084 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0374)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.20 | -0.21 | 1.98 | -0.0216 |
| fees_2x | -0.40 | -0.43 | 2.04 | -0.0251 |
| latency_plus1 | -0.05 | -0.04 | 1.91 | -0.0185 |
| latency_plus2 | -0.69 | -0.71 | 2.23 | -0.0305 |
| latency_plus3 | 0.29 | 0.33 | 1.56 | -0.0152 |
| low_liquidity | -0.00 | 0.01 | 1.91 | -0.0181 |
| very_low_liquidity | -0.00 | 0.01 | 1.91 | -0.0181 |
| high_slippage | -0.49 | -0.55 | 2.07 | -0.0242 |
| extreme_slippage | -1.48 | -1.66 | 2.44 | -0.0370 |
| combined_adverse | -0.74 | -0.82 | 2.13 | -0.0282 |
| spread_widen_10bps | 0.21 | 0.25 | 1.73 | -0.0147 |
| spread_widen_25bps | -0.47 | -0.50 | 2.21 | -0.0251 |
| thin_book | 0.85 | 0.75 | 1.59 | -0.0068 |
| very_thin_book | 0.31 | 0.29 | 1.88 | -0.0138 |
| entry_spread_stress | -0.34 | -0.36 | 2.01 | -0.0223 |
| combined_market_deterioration | 0.73 | 0.64 | 1.14 | -0.0056 |
| severe_adverse | -1.38 | -1.17 | 2.50 | -0.0374 |

## Holdout Validation

- **Holdout bars**: 8775
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0037)
- **Trend**: ranging (efficiency: 0.0007)
- **Best holdout score**: 0.0008 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0277 | 0.0008 | 0.34 | 0.06 | 152 |
| 1 | -0.0021 | -0.0004 | 0.43 | 0.29 | 172 |
| 2 | -0.0022 | -0.0381 | -0.25 | 0.61 | 214 |
| 3 | -0.0022 | -0.0222 | -0.49 | 1.08 | 125 |
| 4 | -0.0022 | -0.0042 | -0.06 | 0.23 | 228 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51916
- **Expected rows**: 51943
- **Missing rows**: 27
- **Forward-fill count**: 48
- **Forward-fill fraction**: 0.0009245704599738038
- **Longest gap (seconds)**: 5700

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0081 <= 0; recent PnL -0.3147% < 0
- **Objective score**: -0.008130471062945812
- **PnL %**: -0.31470031469894383
- **Trade count**: 112

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0030 <= 0; recent PnL -0.0083% < 0
- **Objective score**: -0.003022799527745393
- **PnL %**: -0.008288366649964568
- **Trade count**: 55

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1150 <= 0; recent PnL -0.0571% < 0
- **Objective score**: -0.11500858967598147
- **PnL %**: -0.05709950854506871
- **Trade count**: 22

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.01766120125445867
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0115, -0.0138 |
| sell_spread_base | -0.0173, -0.0177 |
| stop_loss | -0.0185, -0.0128 |
| take_profit | -0.0177, -0.0177 |
| executor_refresh_time | -0.0179, -0.0188 |
| cooldown_time | -0.0201, -0.0109 |
| total_amount_quote | -0.0187, -0.0177 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4029908802355054
- **Max CV**: 1.4481554595763166
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1744 | 1.583651027382771 | 2.489523914434642 | 1.9539708781328318 |
| buy_spread_ratio | 0.1487 | 1.9003903579910113 | 2.9875223611825144 | 2.481292920272911 |
| sell_spread_base | 0.6194 | 0.4505190743782331 | 5.6436872549008195 | 3.3279188454802813 |
| sell_spread_ratio | 0.1319 | 1.5894196865243113 | 2.3553925791844716 | 1.880125558688792 |
| buy_side_weight | 0.3751 | 0.20643382150904593 | 0.6231971424538988 | 0.3855419978245594 |
| amount_skew | 0.1675 | 2.412445645995062 | 3.950517963969299 | 3.269491332665809 |
| stop_loss | 0.2801 | 0.010053977353042937 | 0.021981024148053283 | 0.013301772592704288 |
| take_profit | 1.4482 | 0.005284938109701073 | 0.10882752522107433 | 0.025518651353040635 |
| executor_refresh_time | 0.5362 | 950.0 | 13047.0 | 7970.8 |
| cooldown_time | 0.4670 | 198.0 | 5966.0 | 3648.5 |
| total_amount_quote | 0.0845 | 792.9798191281802 | 969.5504054983531 | 881.4431542840508 |

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
| recent_objective | > 0 | -0.008130471062945812 | FAIL |
| recent_pnl | >= 0 | -0.31470031469894383 | FAIL |
| recent_trades | >= 5 | 112 | PASS |
| worst_stress | > -10 | -0.037351363387681455 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0008 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.037351363387681455 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.008130471062945812, pnl=-0.31470031469894383, trades=112, reason=recent objective score -0.0081 <= 0; recent PnL -0.3147% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.003022799527745393, pnl=-0.008288366649964568, trades=55, reason=recent objective score -0.0030 <= 0; recent PnL -0.0083% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.11500858967598147, pnl=-0.05709950854506871, trades=22, reason=recent objective score -0.1150 <= 0; recent PnL -0.0571% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4029908802355054 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51916 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0081 <= 0; recent PnL -0.3147% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0030 <= 0; recent PnL -0.0083% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1150 <= 0; recent PnL -0.0571% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51916
- **Pre-release bars**: 43878
- **Dev bars**: 35103
- **Holdout bars**: 8775
- **Recent 28d bars**: 8038
- **Recent window start**: 1773303000

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T09:03:03.442480+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 12801
