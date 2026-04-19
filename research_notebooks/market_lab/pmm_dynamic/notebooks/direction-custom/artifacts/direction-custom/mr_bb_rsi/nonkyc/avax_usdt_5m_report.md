# PMM Dynamic Optimization Report: nonkyc_AVAX-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 12:26:37 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T12:26:37.712075+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 6891 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: AVAX-USDT
- **interval**: 5m
- **n_candles**: 51896
- **dataset_hash**: 0a5d9ded710c29d2441a9c108c32640c7fb724b519f58390461942c1ebd1b584
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 994.8607691194926
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 16 |
| bb_length | 150 |
| bb_std | 2.2427243050533265 |
| bbp_entry_threshold | 0.16739575940226842 |
| cooldown_time | 69387 |
| max_atr_pct_for_entry | 0.03505383941527449 |
| min_volume_quantile | 0.3185910069669772 |
| rsi_entry_threshold | 48.60221212104563 |
| rsi_length | 24 |
| stop_loss | 0.018253908296728766 |
| take_profit | 0.005755884976615716 |
| take_profit_order_type | LIMIT |
| time_limit | 231046 |
| total_amount_quote | 994.8607691194926 |
| trailing_stop_activation | 0.0334722121760012 |
| trailing_stop_delta | 0.017630667372139024 |
| trend_ema_length | 87 |
| use_trend_filter | False |
| volume_filter_window | 421 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 994.8607691194926 |
| Selected | 994.8607691194926 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0009
- **Net PnL (quote)**: -9.9572
- **Sharpe Ratio**: -2.8740
- **Max Drawdown %**: 1.2659
- **Profit Factor**: 0.14091661121030535
- **Trade Count**: 10
- **Total Fees (quote)**: 2.6015
- **Maker Fees**: 1.5536
- **Taker Fees**: 1.0479
- **Fee Drag %**: 0.2615

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1809
- **PnL Component**: -0.0101
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0095
- **Fee Drag Component**: -0.0013
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1600
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2350**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.62 | -5.43 | 2.17 | 46 | -0.0559 | n/a |
| 1 | -1.81 | -4.08 | 2.23 | 14 | -0.1820 | n/a |
| 2 | -1.05 | -3.00 | 2.31 | 36 | -0.0886 | n/a |
| 3 | -1.84 | -4.44 | 2.21 | 13 | -0.1862 | n/a |
| 4 | -1.44 | -4.31 | 2.18 | 26 | -0.1308 | n/a |
| 5 | -2.18 | -13.21 | 2.18 | 36 | -0.3112 | n/a |
| 6 | -1.92 | -7.43 | 2.27 | 9 | -0.2036 | n/a |
| 7 | -1.83 | -4.32 | 2.56 | 12 | -0.4424 | n/a |
| 8 | -2.17 | -13.23 | 2.17 | 9 | -0.4254 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.13 | -3.12 | 1.32 | -0.1833 |
| fees_2x | -1.26 | -3.32 | 1.37 | -0.1856 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.59 | -3.66 | 1.77 | -0.4688 |
| very_low_liquidity | -1.88 | -4.42 | 1.97 | -0.3185 |
| high_slippage | -1.03 | -2.90 | 1.29 | -0.1813 |
| extreme_slippage | -1.08 | -2.93 | 1.34 | -0.1823 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.00 | -2.91 | 1.24 | -0.1807 |
| spread_widen_25bps | -1.00 | -2.92 | 1.20 | -0.1804 |
| thin_book | -2.20 | -4.22 | 2.22 | -0.4269 |
| very_thin_book | -1.80 | -1.20 | 2.81 | -0.2018 |
| entry_spread_stress | -1.00 | -2.89 | 1.23 | -0.1806 |
| combined_market_deterioration | -2.41 | -4.65 | 2.42 | -0.4612 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0023)
- **Trend**: ranging (efficiency: 0.0060)
- **Best holdout score**: -0.1293 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0904 | -0.1794 | -2.17 | 2.23 | 43 |
| 1 | -0.0744 | -0.3063 | -1.99 | 1.99 | 13 |
| 2 | -0.0752 | -0.3048 | -1.95 | 1.99 | 16 |
| 3 | -0.0759 | -0.1293 | -2.03 | 2.38 | 29 |
| 4 | -0.0837 | -0.2161 | -1.41 | 1.59 | 11 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51896
- **Expected rows**: 51899
- **Missing rows**: 3
- **Forward-fill count**: 548
- **Forward-fill fraction**: 0.010559580699861262
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3116 <= 0; recent PnL -2.1754% < 0
- **Objective score**: -0.3115548097730231
- **PnL %**: -2.175384592110249
- **Trade count**: 20

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1309 <= 0; recent PnL -1.7064% < 0
- **Objective score**: -0.130914144605077
- **PnL %**: -1.7063871143779232
- **Trade count**: 50

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3504 <= 0; recent PnL -2.4143% < 0
- **Objective score**: -0.35040704589245286
- **PnL %**: -2.414254431680919
- **Trade count**: 157

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.3800725519526724
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.3730, -0.1970 |
| bb_std | -0.4920, -0.2268 |
| bbp_entry_threshold | -0.3929, -0.3262 |
| rsi_length | -0.3801, -0.3801 |
| rsi_entry_threshold | -0.3801, -0.3262 |
| trend_ema_length | -0.3801, -0.3801 |
| max_atr_pct_for_entry | -0.3801, -0.3801 |
| volume_filter_window | -0.3801, -0.3801 |
| min_volume_quantile | -0.3801, -0.3801 |
| stop_loss | -0.1824, -0.3742 |
| take_profit | -0.3783, -0.1810 |
| cooldown_time | -0.2310, -0.3801 |
| total_amount_quote | -0.1786, -0.3760 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.22121254700449325
- **Max CV**: 0.5903375528975222
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.1220 | 0.015015119551004683 | 0.021594494243041978 | 0.01696933009726313 |
| take_profit | 0.5903 | 0.005003532512054107 | 0.017052849351686994 | 0.007968718100946926 |
| cooldown_time | 0.1324 | 43893.0 | 70142.0 | 62332.8 |
| total_amount_quote | 0.0401 | 884.2737185636062 | 993.5757120216541 | 944.7309621905728 |

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
| recent_objective | > 0 | -0.3115548097730231 | FAIL |
| recent_pnl | >= 0 | -2.175384592110249 | FAIL |
| recent_trades | >= 5 | 20 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.17944170501524231 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.3115548097730231, pnl=-2.175384592110249, trades=20, reason=recent objective score -0.3116 <= 0; recent PnL -2.1754% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.130914144605077, pnl=-1.7063871143779232, trades=50, reason=recent objective score -0.1309 <= 0; recent PnL -1.7064% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.35040704589245286, pnl=-2.414254431680919, trades=157, reason=recent objective score -0.3504 <= 0; recent PnL -2.4143% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.22121254700449325 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51896 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3116 <= 0; recent PnL -2.1754% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1309 <= 0; recent PnL -1.7064% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.3504 <= 0; recent PnL -2.4143% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51896
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8062
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T12:26:37.712075+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 6891
- **validation_status**: validated_fail
