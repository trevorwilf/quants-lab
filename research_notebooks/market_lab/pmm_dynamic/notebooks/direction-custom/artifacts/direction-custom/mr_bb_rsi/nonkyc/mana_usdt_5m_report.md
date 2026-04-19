# PMM Dynamic Optimization Report: nonkyc_MANA-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 14:33:12 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T14:33:12.197454+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 87 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: MANA-USDT
- **interval**: 5m
- **n_candles**: 19276
- **dataset_hash**: b201a09e1f3ebde103a13a0abc9f973f24d8617933d0278696baa6f1a8310e25
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 664.5920730923958
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 25 |
| bb_length | 20 |
| bb_std | 2.1082880245662965 |
| bbp_entry_threshold | 0.3228513117628403 |
| cooldown_time | 36244 |
| max_atr_pct_for_entry | 0.055412049703922966 |
| min_volume_quantile | 0.551773966889899 |
| rsi_entry_threshold | 31.169053582278295 |
| rsi_length | 30 |
| stop_loss | 0.028167807461274928 |
| take_profit | 0.00587347380061132 |
| take_profit_order_type | MARKET |
| time_limit | 28074 |
| total_amount_quote | 664.5920730923958 |
| trailing_stop_activation | 0.03395441365873483 |
| trailing_stop_delta | 0.015967144159177465 |
| trend_ema_length | 72 |
| use_trend_filter | False |
| volume_filter_window | 403 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 664.5920730923958 |
| Selected | 664.5920730923958 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.6444
- **Net PnL (quote)**: -10.9283
- **Sharpe Ratio**: -2.2206
- **Max Drawdown %**: 2.3557
- **Profit Factor**: 0.24232338015978758
- **Trade Count**: 93
- **Total Fees (quote)**: 7.0947
- **Maker Fees**: 2.5776
- **Taker Fees**: 4.5171
- **Fee Drag %**: 1.0675

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0399
- **PnL Component**: -0.0166
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0177
- **Fee Drag Component**: -0.0053
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.4128**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | 0.23 | 0.96 | 1.40 | 9 | -0.1744 | n/a |
| 2 | 0.44 | 2.64 | 0.62 | 39 | -0.0477 | n/a |
| 3 | -2.82 | -13.09 | 2.82 | 32 | -0.3711 | n/a |
| 4 | -1.93 | -9.47 | 2.05 | 61 | -0.4018 | n/a |
| 5 | -1.86 | -11.58 | 1.86 | 10 | -0.4545 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.18 | -2.95 | 2.51 | -0.0492 |
| fees_2x | -2.72 | -3.69 | 2.91 | -0.0857 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.46 | -2.27 | 2.31 | -0.0367 |
| very_low_liquidity | -1.95 | -4.20 | 2.37 | -0.0414 |
| high_slippage | -1.81 | -2.45 | 2.40 | -0.0420 |
| extreme_slippage | -2.15 | -2.92 | 2.50 | -0.0462 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.69 | -2.28 | 2.39 | -0.0407 |
| spread_widen_25bps | -1.77 | -2.37 | 2.46 | -0.0419 |
| thin_book | -1.18 | -3.58 | 1.54 | -0.3020 |
| very_thin_book | -1.94 | -6.70 | 2.04 | -0.3209 |
| entry_spread_stress | -1.72 | -2.31 | 2.41 | -0.0410 |
| combined_market_deterioration | -1.71 | -4.16 | 1.97 | -0.0398 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 2246
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0025)
- **Trend**: ranging (efficiency: 0.0262)
- **Best holdout score**: -0.0608 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0199 | -0.0608 | 0.21 | 1.40 | 38 |
| 1 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -1000.0000 | -1000.0000 | -0.34 | 1.58 | 1 |
| 4 | -1000.0000 | -0.2325 | -4.25 | 4.55 | 18 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 19276
- **Expected rows**: 19297
- **Missing rows**: 21
- **Forward-fill count**: 84
- **Forward-fill fraction**: 0.004357750570657813
- **Longest gap (seconds)**: 6600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2062 <= 0; recent PnL -3.2884% < 0
- **Objective score**: -0.20624081435779384
- **PnL %**: -3.288427914675738
- **Trade count**: 44

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3200 <= 0; recent PnL -1.9977% < 0
- **Objective score**: -0.31995258128295545
- **PnL %**: -1.9977474394600052
- **Trade count**: 45

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4607 <= 0; recent PnL -1.8595% < 0
- **Objective score**: -0.460695474153667
- **PnL %**: -1.8595188709040755
- **Trade count**: 10

## Sensitivity Analysis

- **Sensitivity penalty**: 0.11538461538461539
- **Baseline score**: -0.03895602502304134
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0390, -0.0390 |
| bb_std | -0.0390, -0.0390 |
| bbp_entry_threshold | -0.0390, -0.0390 |
| rsi_length | -0.0397, -0.1700 |
| rsi_entry_threshold | -0.3760, -0.2687 |
| trend_ema_length | -0.0390, -0.0390 |
| max_atr_pct_for_entry | -0.0390, -0.0390 |
| volume_filter_window | -0.0390, -0.0390 |
| min_volume_quantile | -0.0334, -0.0390 |
| stop_loss | -0.0390, -0.0390 |
| take_profit | -0.0374, -0.0404 |
| cooldown_time | -0.0390, -0.0390 |
| total_amount_quote | -0.0380, -0.0398 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5465690930453482
- **Max CV**: 0.7035440873964931
- **Clustered params**: stop_loss
- **Scattered params**: take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4511 | 0.015846488196553956 | 0.06760341855737632 | 0.039039962794188164 |
| take_profit | 0.5016 | 0.005570740712340032 | 0.025877575042778093 | 0.014127329229890708 |
| cooldown_time | 0.7035 | 1319.0 | 81404.0 | 45223.8 |
| total_amount_quote | 0.5300 | 27.846360259215086 | 973.6975036774652 | 581.5399116555404 |

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
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.20624081435779384 | FAIL |
| recent_pnl | >= 0 | -3.288427914675738 | FAIL |
| recent_trades | >= 5 | 44 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.11538461538461539 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.060755021900682146 |
| walkforward | PASS | 6 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.11538461538461539 |
| recent_28d | FAIL | score=-0.20624081435779384, pnl=-3.288427914675738, trades=44, reason=recent objective score -0.2062 <= 0; recent PnL -3.2884% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.31995258128295545, pnl=-1.9977474394600052, trades=45, reason=recent objective score -0.3200 <= 0; recent PnL -1.9977% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.460695474153667, pnl=-1.8595188709040755, trades=10, reason=recent objective score -0.4607 <= 0; recent PnL -1.8595% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5465690930453482 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 19276 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2062 <= 0; recent PnL -3.2884% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3200 <= 0; recent PnL -1.9977% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.4607 <= 0; recent PnL -1.8595% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 19276
- **Pre-release bars**: 11232
- **Dev bars**: 8986
- **Holdout bars**: 2246
- **Recent 28d bars**: 8044
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T14:33:12.197454+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 87
- **validation_status**: validated_fail
