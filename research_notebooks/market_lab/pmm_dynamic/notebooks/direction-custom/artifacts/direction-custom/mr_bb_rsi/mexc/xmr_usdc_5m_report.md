# PMM Dynamic Optimization Report: mexc_XMR-USDC_5m_mr_bb_rsi_v1

Generated: 2026-04-18 11:03:32 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T11:03:32.553740+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 5362 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XMR-USDC
- **interval**: 5m
- **n_candles**: 51840
- **dataset_hash**: a55228863ee652ee4763474a7c6d06b682bce2a31ea9cbaa18e6a9feeb7a9374
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 753.8464218192621
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 26 |
| bb_length | 128 |
| bb_std | 1.612269617047286 |
| bbp_entry_threshold | 0.30226551224964077 |
| cooldown_time | 11028 |
| max_atr_pct_for_entry | 0.006598011470304272 |
| min_volume_quantile | 0.2159989417252822 |
| rsi_entry_threshold | 44.94294827051437 |
| rsi_length | 10 |
| stop_loss | 0.05467570352832127 |
| take_profit | 0.0351467645878066 |
| take_profit_order_type | MARKET |
| time_limit | 169404 |
| total_amount_quote | 753.8464218192621 |
| trailing_stop_activation | 0.0003505100543079846 |
| trailing_stop_delta | 0.008957322739394286 |
| trend_ema_length | 390 |
| use_trend_filter | True |
| volume_filter_window | 392 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 753.8464218192621 |
| Selected | 753.8464218192621 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 10.7258
- **Net PnL (quote)**: 80.8560
- **Sharpe Ratio**: 2.2670
- **Max Drawdown %**: 3.3513
- **Profit Factor**: 13.621323065106822
- **Trade Count**: 242
- **Total Fees (quote)**: 20.9984
- **Maker Fees**: 10.4890
- **Taker Fees**: 10.5094
- **Fee Drag %**: 2.7855

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0623
- **PnL Component**: 0.1019
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0251
- **Fee Drag Component**: -0.0139
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1445**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.31 | -4.64 | 2.03 | 26 | -0.1489 | n/a |
| 1 | 2.47 | 7.43 | 0.76 | 54 | 0.0161 | n/a |
| 2 | -0.10 | -0.13 | 2.08 | 52 | -0.0195 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | -1.96 | -3.44 | 3.52 | 4 | -0.2312 | n/a |
| 5 | 1.14 | 3.08 | 1.33 | 23 | -0.1080 | n/a |
| 6 | 0.25 | 0.46 | 2.83 | 35 | -0.0811 | n/a |
| 7 | -1.14 | -2.07 | 1.98 | 28 | -0.1163 | n/a |
| 8 | -2.03 | -8.16 | 2.32 | 26 | -0.2753 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 9.33 | 1.98 | 3.39 | 0.0424 |
| fees_2x | 7.94 | 1.70 | 3.43 | 0.0223 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 8.54 | 1.65 | 3.45 | 0.0141 |
| very_low_liquidity | 5.43 | 1.04 | 4.76 | -0.0952 |
| high_slippage | 7.24 | 1.57 | 3.45 | 0.0296 |
| extreme_slippage | 0.11 | 0.10 | 4.94 | -0.0885 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 10.23 | 1.96 | 3.47 | 0.0567 |
| spread_widen_25bps | 2.04 | 0.43 | 5.60 | -0.2135 |
| thin_book | -3.54 | -0.97 | 5.44 | -0.0809 |
| very_thin_book | -3.72 | -0.83 | 4.86 | -0.1130 |
| entry_spread_stress | 8.96 | 1.72 | 3.51 | 0.0449 |
| combined_market_deterioration | -2.64 | -0.65 | 5.54 | -0.0868 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0028)
- **Trend**: ranging (efficiency: 0.0032)
- **Best holdout score**: -0.0263 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9688 | -0.0263 | -0.08 | 2.83 | 71 |
| 1 | -0.0100 | -0.2002 | -1.39 | 1.80 | 7 |
| 2 | -0.0128 | -1000.0000 | -1.29 | 1.31 | 2 |
| 3 | -0.0131 | -1000.0000 | -1.19 | 1.54 | 2 |
| 4 | -0.0142 | -0.2001 | -1.63 | 2.48 | 9 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51840
- **Expected rows**: 51841
- **Missing rows**: 1
- **Forward-fill count**: 159
- **Forward-fill fraction**: 0.0030671296296296297
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0281 <= 0; recent PnL -0.3543% < 0
- **Objective score**: -0.0281415625704181
- **PnL %**: -0.35433624908000366
- **Trade count**: 151

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0087 <= 0
- **Objective score**: -0.008712659858205907
- **PnL %**: 0.6208945797675989
- **Trade count**: 48

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1473 <= 0
- **Objective score**: -0.14733936952081528
- **PnL %**: 0.0917500839888373
- **Trade count**: 18

## Sensitivity Analysis

- **Sensitivity penalty**: 0.7692307692307693
- **Baseline score**: 0.05193848309521391
- **Sign flips**: 9
- **Collapse count**: 11
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | 0.0318, -0.3103 |
| bb_std | -0.1816, -0.0232 |
| bbp_entry_threshold | -0.1489, -0.0634 |
| rsi_length | 0.0572, 0.0502 |
| rsi_entry_threshold | -0.0795, 0.0435 |
| trend_ema_length | -0.2918, -0.1196 |
| max_atr_pct_for_entry | 0.0674, 0.0100 |
| volume_filter_window | 0.0516, 0.0522 |
| min_volume_quantile | 0.0540, 0.0436 |
| stop_loss | 0.0514, 0.0525 |
| take_profit | 0.0519, 0.0519 |
| cooldown_time | -0.0153, 0.0240 |
| total_amount_quote | 0.0359, 0.0302 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.33465116277292134
- **Max CV**: 0.4650198959150922
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3546 | 0.022000740730504353 | 0.07620880355518414 | 0.055289338365401286 |
| take_profit | 0.4650 | 0.013597120293232238 | 0.0560951892874374 | 0.028235782294528815 |
| cooldown_time | 0.4388 | 3309.0 | 11028.0 | 5821.6 |
| total_amount_quote | 0.0802 | 753.8464218192621 | 986.0000306979424 | 933.6985008745745 |

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
- walkforward_positive_majority: **FAIL**
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
| recent_objective | > 0 | -0.0281415625704181 | FAIL |
| recent_pnl | >= 0 | -0.35433624908000366 | FAIL |
| recent_trades | >= 5 | 151 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.7692307692307693 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.026287708524044943 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=0.7692307692307693 |
| recent_28d | FAIL | score=-0.0281415625704181, pnl=-0.35433624908000366, trades=151, reason=recent objective score -0.0281 <= 0; recent PnL -0.3543% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.008712659858205907, pnl=0.6208945797675989, trades=48, reason=recent objective score -0.0087 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.14733936952081528, pnl=0.0917500839888373, trades=18, reason=recent objective score -0.1473 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.33465116277292134 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51840 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0281 <= 0; recent PnL -0.3543% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0087 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1473 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51840
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8064
- **Recent window start**: 1774012500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T11:03:32.553740+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 5362
- **validation_status**: validated_fail
