# PMM Dynamic Optimization Report: nonkyc_EPIC-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 13:40:18 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T13:40:18.150266+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 8617 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: EPIC-USDT
- **interval**: 5m
- **n_candles**: 38455
- **dataset_hash**: c39a12d01035d17fcb13e67df3d4ccc001c48d7521a99ba10105830b33675fc9
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 632.535284778647
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 7 |
| bb_length | 57 |
| bb_std | 1.154520560937423 |
| bbp_entry_threshold | 0.09918290817586128 |
| cooldown_time | 22490 |
| max_atr_pct_for_entry | 0.006875657887650163 |
| min_volume_quantile | 0.36005041119501907 |
| rsi_entry_threshold | 39.0399074080474 |
| rsi_length | 9 |
| stop_loss | 0.07902196682925268 |
| take_profit | 0.03329322996092721 |
| take_profit_order_type | MARKET |
| time_limit | 251530 |
| total_amount_quote | 632.535284778647 |
| trailing_stop_activation | 0.03610086122353218 |
| trailing_stop_delta | 0.0028400215247334853 |
| trend_ema_length | 280 |
| use_trend_filter | True |
| volume_filter_window | 249 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 632.535284778647 |
| Selected | 632.535284778647 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 27.3958
- **Net PnL (quote)**: 173.2883
- **Sharpe Ratio**: 2.7514
- **Max Drawdown %**: 6.8448
- **Profit Factor**: 4.32323010287877
- **Trade Count**: 353
- **Total Fees (quote)**: 14.1074
- **Maker Fees**: 4.8785
- **Taker Fees**: 9.2289
- **Fee Drag %**: 2.2303

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1783
- **PnL Component**: 0.2421
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0513
- **Fee Drag Component**: -0.0112
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0853**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 4.41 | 4.56 | 1.26 | 57 | 0.0317 | n/a |
| 1 | 5.75 | 6.54 | 0.88 | 52 | 0.0474 | n/a |
| 2 | -3.89 | -2.09 | 7.96 | 103 | -0.1913 | n/a |
| 3 | -5.11 | -4.22 | 5.62 | 47 | -0.4425 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 0.60 | 0.74 | 2.74 | 44 | -0.0410 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 26.28 | 2.67 | 6.84 | 0.1639 |
| fees_2x | 25.16 | 2.58 | 6.84 | 0.1495 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 19.93 | 2.30 | 6.83 | 0.1070 |
| very_low_liquidity | 3.09 | 0.61 | 7.95 | -0.0640 |
| high_slippage | 27.03 | 2.73 | 6.84 | 0.1755 |
| extreme_slippage | 26.30 | 2.68 | 6.84 | 0.1697 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 27.09 | 2.72 | 6.84 | 0.1759 |
| spread_widen_25bps | 26.63 | 2.68 | 6.84 | 0.1723 |
| thin_book | -1.81 | -0.46 | 7.76 | -0.1266 |
| very_thin_book | -4.76 | -3.33 | 8.12 | -0.2310 |
| entry_spread_stress | 26.94 | 2.71 | 6.84 | 0.1747 |
| combined_market_deterioration | 18.28 | 2.14 | 6.82 | 0.0752 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 6078
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0083)
- **Trend**: ranging (efficiency: 0.0006)
- **Best holdout score**: -0.4420 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9108 | -0.4420 | -5.11 | 5.62 | 47 |
| 1 | 0.0445 | -0.5316 | -5.03 | 5.70 | 19 |
| 2 | 0.0428 | -0.5174 | -3.65 | 4.53 | 20 |
| 3 | 0.0393 | -0.5390 | -4.83 | 5.70 | 20 |
| 4 | 0.0387 | -0.5413 | -4.94 | 5.81 | 20 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 38455
- **Expected rows**: 38455
- **Missing rows**: 0
- **Forward-fill count**: 291
- **Forward-fill fraction**: 0.007567286438694578
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0453 <= 0; recent PnL -1.3272% < 0
- **Objective score**: -0.045323677689312565
- **PnL %**: -1.327194604480266
- **Trade count**: 85

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1456 <= 0; recent PnL -1.3272% < 0
- **Objective score**: -0.14559274146764656
- **PnL %**: -1.327194604480266
- **Trade count**: 85

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4876 <= 0; recent PnL -1.8755% < 0
- **Objective score**: -0.4875897579712792
- **PnL %**: -1.8754652670676224
- **Trade count**: 40

## Sensitivity Analysis

- **Sensitivity penalty**: 0.2692307692307692
- **Baseline score**: -0.03766071352622344
- **Sign flips**: 0
- **Collapse count**: 7
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0353, -0.0377 |
| bb_std | -0.0377, -0.0375 |
| bbp_entry_threshold | -0.0377, -0.0377 |
| rsi_length | -0.0377, -0.0699 |
| rsi_entry_threshold | -0.4443, -0.0564 |
| trend_ema_length | -0.1273, -0.0719 |
| max_atr_pct_for_entry | -0.0084, -0.0891 |
| volume_filter_window | -0.0377, -0.0377 |
| min_volume_quantile | -0.0373, -0.0377 |
| stop_loss | -0.0494, -0.4615 |
| take_profit | -0.1726, -0.0440 |
| cooldown_time | -0.0377, -0.0377 |
| total_amount_quote | -0.0351, -0.0408 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3613587068212934
- **Max CV**: 0.5714535648842989
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4362 | 0.01881579266214395 | 0.07833742270483392 | 0.04299214590043128 |
| take_profit | 0.2926 | 0.022032571685855578 | 0.05923607533522345 | 0.044196040069644796 |
| cooldown_time | 0.5715 | 11860.0 | 72284.0 | 40238.4 |
| total_amount_quote | 0.1452 | 635.1608270174368 | 955.5698367946361 | 765.4544823312997 |

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
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
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.045323677689312565 | FAIL |
| recent_pnl | >= 0 | -1.327194604480266 | FAIL |
| recent_trades | >= 5 | 85 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.2692307692307692 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.4420242534028243 |
| walkforward | PASS | 6 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.2692307692307692 |
| recent_28d | FAIL | score=-0.045323677689312565, pnl=-1.327194604480266, trades=85, reason=recent objective score -0.0453 <= 0; recent PnL -1.3272% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.14559274146764656, pnl=-1.327194604480266, trades=85, reason=recent objective score -0.1456 <= 0; recent PnL -1.3272% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.4875897579712792, pnl=-1.8754652670676224, trades=40, reason=recent objective score -0.4876 <= 0; recent PnL -1.8755% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3613587068212934 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 38455 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0453 <= 0; recent PnL -1.3272% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1456 <= 0; recent PnL -1.3272% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.4876 <= 0; recent PnL -1.8755% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 38455
- **Pre-release bars**: 30390
- **Dev bars**: 24312
- **Holdout bars**: 6078
- **Recent 28d bars**: 8065
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T13:40:18.150266+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 8617
- **validation_status**: validated_fail
