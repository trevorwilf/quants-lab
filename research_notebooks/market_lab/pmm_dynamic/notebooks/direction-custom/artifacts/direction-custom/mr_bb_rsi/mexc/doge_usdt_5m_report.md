# PMM Dynamic Optimization Report: mexc_DOGE-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 08:29:45 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T08:29:45.724551+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 1733 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOGE-USDT
- **interval**: 5m
- **n_candles**: 51785
- **dataset_hash**: 072b6d494891ac30e93af2480acab45c04139ebd0f8af4fcc471ff05a0b6a256
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 802.5810404108879
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 9 |
| bb_length | 83 |
| bb_std | 1.2088668240184375 |
| bbp_entry_threshold | 0.24576199504000543 |
| cooldown_time | 35828 |
| max_atr_pct_for_entry | 0.04044118229787417 |
| min_volume_quantile | 0.014163967962805148 |
| rsi_entry_threshold | 47.13367150947796 |
| rsi_length | 13 |
| stop_loss | 0.019118368977519142 |
| take_profit | 0.006391934524792641 |
| take_profit_order_type | LIMIT |
| time_limit | 15137 |
| total_amount_quote | 802.5810404108879 |
| trailing_stop_activation | 6.184948246368543e-05 |
| trailing_stop_delta | 0.016333802105217593 |
| trend_ema_length | 192 |
| use_trend_filter | True |
| volume_filter_window | 495 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 802.5810404108879 |
| Selected | 802.5810404108879 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3.8974
- **Net PnL (quote)**: 31.2799
- **Sharpe Ratio**: 2.2376
- **Max Drawdown %**: 1.9598
- **Profit Factor**: 2.204358703660262
- **Trade Count**: 67
- **Total Fees (quote)**: 21.1968
- **Maker Fees**: 10.5932
- **Taker Fees**: 10.6037
- **Fee Drag %**: 2.6411

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0102
- **PnL Component**: 0.0382
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0147
- **Fee Drag Component**: -0.0132
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1750**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.70 | 5.38 | 0.25 | 9 | -0.1605 | n/a |
| 1 | -0.37 | -1.76 | 1.06 | 13 | -0.1614 | n/a |
| 2 | 0.30 | 2.41 | 0.63 | 7 | -0.1749 | n/a |
| 3 | 0.07 | 0.35 | 0.76 | 9 | -0.1701 | n/a |
| 4 | 0.45 | 4.58 | 0.35 | 10 | -0.1593 | n/a |
| 5 | 0.22 | 0.68 | 1.49 | 10 | -0.1710 | n/a |
| 6 | -1.50 | -5.08 | 2.07 | 5 | -0.2116 | n/a |
| 7 | 0.11 | 0.58 | 0.69 | 12 | -0.1580 | n/a |
| 8 | 0.33 | 3.65 | 0.36 | 10 | -0.1952 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2.57 | 1.49 | 1.99 | -0.0094 |
| fees_2x | 1.25 | 0.74 | 2.01 | -0.0368 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 3.86 | 2.22 | 1.96 | 0.0099 |
| very_low_liquidity | 3.85 | 2.21 | 1.96 | 0.0098 |
| high_slippage | 0.58 | 0.37 | 2.03 | -0.0235 |
| extreme_slippage | -2.94 | -3.25 | 3.03 | -0.0981 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 1.31 | 0.66 | 2.23 | -0.0169 |
| spread_widen_25bps | 1.68 | 0.62 | 3.52 | -0.0231 |
| thin_book | -1.00 | -1.08 | 1.98 | -0.1480 |
| very_thin_book | -1.93 | -3.11 | 2.00 | -0.1958 |
| entry_spread_stress | -1.27 | -1.48 | 2.01 | -0.1157 |
| combined_market_deterioration | -2.06 | -1.70 | 2.11 | -0.1293 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0031)
- **Trend**: ranging (efficiency: 0.0060)
- **Best holdout score**: -0.1775 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9949 | -0.1775 | -1.99 | 2.08 | 15 |
| 1 | -0.1232 | -0.2004 | -1.52 | 2.03 | 8 |
| 2 | -0.1302 | -0.1977 | -1.69 | 2.46 | 10 |
| 3 | -0.1322 | -0.1971 | -1.88 | 5.26 | 16 |
| 4 | -0.1329 | -0.1818 | -1.08 | 1.67 | 11 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51785
- **Expected rows**: 51841
- **Missing rows**: 56
- **Forward-fill count**: 111
- **Forward-fill fraction**: 0.00214347784107367
- **Longest gap (seconds)**: 8100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1302 <= 0; recent PnL -2.3463% < 0
- **Objective score**: -0.13022695913448684
- **PnL %**: -2.346263552921
- **Trade count**: 30

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2601 <= 0; recent PnL -1.8315% < 0
- **Objective score**: -0.26011922048537517
- **PnL %**: -1.831473825200721
- **Trade count**: 10

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2225 <= 0; recent PnL -1.7899% < 0
- **Objective score**: -0.2225499452896505
- **PnL %**: -1.7899439796806793
- **Trade count**: 8

## Sensitivity Analysis

- **Sensitivity penalty**: 0.15384615384615385
- **Baseline score**: -0.05189289601708718
- **Sign flips**: 0
- **Collapse count**: 4
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -1000.0000, -0.0587 |
| bb_std | -0.0672, -0.0805 |
| bbp_entry_threshold | -0.0805, -0.0676 |
| rsi_length | -0.0519, -0.0513 |
| rsi_entry_threshold | -0.0496, -0.0553 |
| trend_ema_length | -0.0683, -0.0385 |
| max_atr_pct_for_entry | -0.0519, -0.0519 |
| volume_filter_window | -0.0519, -0.0519 |
| min_volume_quantile | -0.0519, -0.0519 |
| stop_loss | -0.0572, -0.0673 |
| take_profit | -0.0519, -0.0519 |
| cooldown_time | -0.0600, -0.2031 |
| total_amount_quote | -0.0520, -0.0519 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3915892760154355
- **Max CV**: 0.604392836209143
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3432 | 0.015353809348862558 | 0.040439701268110445 | 0.026148054574548264 |
| take_profit | 0.4415 | 0.006202678443889007 | 0.02529896939365258 | 0.014079611790666838 |
| cooldown_time | 0.6044 | 4023.0 | 77842.0 | 40380.1 |
| total_amount_quote | 0.1773 | 472.68974941331146 | 989.1915999783772 | 832.3498239611854 |

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
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.13022695913448684 | FAIL |
| recent_pnl | >= 0 | -2.346263552921 | FAIL |
| recent_trades | >= 5 | 30 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.15384615384615385 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1775354479431341 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.15384615384615385 |
| recent_28d | FAIL | score=-0.13022695913448684, pnl=-2.346263552921, trades=30, reason=recent objective score -0.1302 <= 0; recent PnL -2.3463% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.26011922048537517, pnl=-1.831473825200721, trades=10, reason=recent objective score -0.2601 <= 0; recent PnL -1.8315% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.2225499452896505, pnl=-1.7899439796806793, trades=8, reason=recent objective score -0.2225 <= 0; recent PnL -1.7899% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3915892760154355 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51785 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1302 <= 0; recent PnL -2.3463% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2601 <= 0; recent PnL -1.8315% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2225 <= 0; recent PnL -1.7899% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51785
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8009
- **Recent window start**: 1774029600

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T08:29:45.724551+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 1733
- **validation_status**: validated_fail
