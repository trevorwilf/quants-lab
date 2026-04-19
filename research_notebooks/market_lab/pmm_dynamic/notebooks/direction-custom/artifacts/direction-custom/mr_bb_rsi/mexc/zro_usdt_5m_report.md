# PMM Dynamic Optimization Report: mexc_ZRO-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 11:31:14 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T11:31:14.582625+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 4064 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ZRO-USDT
- **interval**: 5m
- **n_candles**: 51839
- **dataset_hash**: e6b96a34cd9dea2b727d66d2912e65e39845e424f840d33dd4cf69de016e50b3
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 919.3338696905028
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 19 |
| bb_length | 118 |
| bb_std | 1.3366741686933592 |
| bbp_entry_threshold | 0.18563864692841556 |
| cooldown_time | 49466 |
| max_atr_pct_for_entry | 0.07136783417887238 |
| min_volume_quantile | 0.4693707277152288 |
| rsi_entry_threshold | 41.69589635999955 |
| rsi_length | 20 |
| stop_loss | 0.040601867985530476 |
| take_profit | 0.007315458020536383 |
| take_profit_order_type | MARKET |
| time_limit | 299337 |
| total_amount_quote | 919.3338696905028 |
| trailing_stop_activation | 0.00023915517414617663 |
| trailing_stop_delta | 0.01726623064954676 |
| trend_ema_length | 358 |
| use_trend_filter | False |
| volume_filter_window | 278 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 919.3338696905028 |
| Selected | 919.3338696905028 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 24.6847
- **Net PnL (quote)**: 226.9350
- **Sharpe Ratio**: 3.2687
- **Max Drawdown %**: 6.4850
- **Profit Factor**: 2.696169097290503
- **Trade Count**: 473
- **Total Fees (quote)**: 40.9035
- **Maker Fees**: 20.4250
- **Taker Fees**: 20.4785
- **Fee Drag %**: 4.4493

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1490
- **PnL Component**: 0.2206
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0486
- **Fee Drag Component**: -0.0222
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1033**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 2.07 | 5.26 | 1.40 | 50 | 0.0075 | n/a |
| 1 | 3.94 | 5.32 | 1.41 | 96 | 0.0248 | n/a |
| 2 | 1.36 | 2.08 | 2.68 | 73 | -0.2596 | n/a |
| 3 | 5.87 | 6.26 | 1.84 | 66 | 0.0399 | n/a |
| 4 | -3.13 | -7.21 | 4.11 | 15 | -0.2039 | n/a |
| 5 | -4.15 | -6.58 | 4.15 | 2 | -1000.0000 | n/a |
| 6 | 2.40 | 2.54 | 2.71 | 27 | -0.0926 | n/a |
| 7 | 2.88 | 7.77 | 1.30 | 43 | -0.0254 | n/a |
| 8 | -1.46 | -2.59 | 3.12 | 22 | -0.1523 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 22.46 | 2.99 | 6.56 | 0.1193 |
| fees_2x | -1.07 | -0.39 | 4.06 | -0.0617 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.45 | -2.95 | 1.87 | -0.1651 |
| very_low_liquidity | -2.70 | -3.47 | 3.01 | -0.1103 |
| high_slippage | -1.18 | -0.43 | 4.07 | -0.0607 |
| extreme_slippage | -2.28 | -0.88 | 4.24 | -0.0732 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 25.84 | 3.60 | 4.82 | 0.1709 |
| spread_widen_25bps | 18.64 | 2.47 | 5.67 | 0.0799 |
| thin_book | -3.57 | -1.91 | 4.12 | -0.2320 |
| very_thin_book | -4.05 | -2.18 | 4.14 | -0.5137 |
| entry_spread_stress | 24.69 | 3.31 | 5.42 | 0.1572 |
| combined_market_deterioration | -3.85 | -2.05 | 4.21 | -0.2281 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0054)
- **Trend**: ranging (efficiency: 0.0113)
- **Best holdout score**: 0.0493 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9255 | -0.1647 | -1.01 | 1.75 | 15 |
| 1 | 0.0196 | 0.0493 | 9.60 | 3.58 | 48 |
| 2 | 0.0171 | -0.1239 | -0.78 | 5.17 | 32 |
| 3 | 0.0147 | -0.2168 | -2.11 | 2.48 | 6 |
| 4 | 0.0143 | -0.2193 | -2.14 | 2.78 | 6 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51839
- **Expected rows**: 51841
- **Missing rows**: 2
- **Forward-fill count**: 56
- **Forward-fill fraction**: 0.001080267752078551
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1050 <= 0; recent PnL -1.4272% < 0
- **Objective score**: -0.10497480879492052
- **PnL %**: -1.4271710692103152
- **Trade count**: 34

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4061 <= 0; recent PnL -3.9767% < 0
- **Objective score**: -0.4060762697664403
- **PnL %**: -3.976723086466949
- **Trade count**: 30

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.5000 <= 0; recent PnL -3.7536% < 0
- **Objective score**: -0.500031263016618
- **PnL %**: -3.7535590543930764
- **Trade count**: 5

## Sensitivity Analysis

- **Sensitivity penalty**: 0.8461538461538461
- **Baseline score**: 0.13935917044287227
- **Sign flips**: 11
- **Collapse count**: 11
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1476, -0.0723 |
| bb_std | -0.1123, -0.0786 |
| bbp_entry_threshold | 0.1385, 0.1319 |
| rsi_length | 0.1627, 0.1584 |
| rsi_entry_threshold | -0.0957, -0.1408 |
| trend_ema_length | 0.1371, 0.1403 |
| max_atr_pct_for_entry | 0.1394, 0.1394 |
| volume_filter_window | 0.1221, 0.1430 |
| min_volume_quantile | -0.0739, -0.0738 |
| stop_loss | -0.0617, 0.1521 |
| take_profit | 0.1394, 0.1394 |
| cooldown_time | -0.1352, -0.1242 |
| total_amount_quote | 0.1134, 0.1589 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.43100143450477035
- **Max CV**: 0.700908742094674
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3698 | 0.019775413181974465 | 0.06321033828525244 | 0.037149152431868775 |
| take_profit | 0.3695 | 0.005304955513257459 | 0.05815496497156077 | 0.044852719444362865 |
| cooldown_time | 0.7009 | 7994.0 | 50641.0 | 19453.7 |
| total_amount_quote | 0.2838 | 379.39860026366506 | 953.1362753331516 | 693.8497502486656 |

## Execution Realism Assumptions

- **taker_probability**: 0.0
- **supports_post_only**: True
- **connector**: mexc
- **fill_participation_rate**: 0.1
- **latency_bars**: 1
- **slippage_bps**: 5.0
- **refresh_close_mode**: market_close

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: **FAIL**
- yaml_validates: **FAIL**
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.10497480879492052 | FAIL |
| recent_pnl | >= 0 | -1.4271710692103152 | FAIL |
| recent_trades | >= 5 | 34 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.8461538461538461 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1646656327641987 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=0.8461538461538461 |
| recent_28d | FAIL | score=-0.10497480879492052, pnl=-1.4271710692103152, trades=34, reason=recent objective score -0.1050 <= 0; recent PnL -1.4272% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.4060762697664403, pnl=-3.976723086466949, trades=30, reason=recent objective score -0.4061 <= 0; recent PnL -3.9767% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.500031263016618, pnl=-3.7535590543930764, trades=5, reason=recent objective score -0.5000 <= 0; recent PnL -3.7536% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.43100143450477035 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51839 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1050 <= 0; recent PnL -1.4272% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.4061 <= 0; recent PnL -3.9767% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.5000 <= 0; recent PnL -3.7536% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51839
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8063
- **Recent window start**: 1774012500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T11:31:14.582625+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 4064
- **validation_status**: validated_fail
