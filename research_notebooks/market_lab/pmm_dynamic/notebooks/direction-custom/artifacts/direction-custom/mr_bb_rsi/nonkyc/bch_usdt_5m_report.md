# PMM Dynamic Optimization Report: nonkyc_BCH-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 12:35:53 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T12:35:53.351131+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 8307 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BCH-USDT
- **interval**: 5m
- **n_candles**: 51899
- **dataset_hash**: 012941938b5817d1eb30a23fae4ec69df74ed60ddd8d56773ed7dc8f2cf176e7
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 877.8718915230883
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 22 |
| bb_length | 26 |
| bb_std | 1.2290596201958972 |
| bbp_entry_threshold | 0.13175062079185118 |
| cooldown_time | 6687 |
| max_atr_pct_for_entry | 0.006748199816305095 |
| min_volume_quantile | 0.3867387274736685 |
| rsi_entry_threshold | 38.85538790097843 |
| rsi_length | 12 |
| stop_loss | 0.04289002414540453 |
| take_profit | 0.00512139406823476 |
| take_profit_order_type | LIMIT |
| time_limit | 274959 |
| total_amount_quote | 877.8718915230883 |
| trailing_stop_activation | 0.031758871290921524 |
| trailing_stop_delta | 0.011521503440665333 |
| trend_ema_length | 105 |
| use_trend_filter | False |
| volume_filter_window | 304 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 877.8718915230883 |
| Selected | 877.8718915230883 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -4.0196
- **Net PnL (quote)**: -35.2873
- **Sharpe Ratio**: -1.8643
- **Max Drawdown %**: 4.6085
- **Profit Factor**: 0.13294869217908004
- **Trade Count**: 48
- **Total Fees (quote)**: 6.2215
- **Maker Fees**: 4.5401
- **Taker Fees**: 1.6814
- **Fee Drag %**: 0.7087
- **TP Min-Notional Failures**: 39 :warning:
  > 39 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0873
- **PnL Component**: -0.0410
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0346
- **Fee Drag Component**: -0.0035
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0080
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2355**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.87 | -4.27 | 2.91 | 27 | -0.1396 | n/a |
| 1 | -3.66 | -8.99 | 4.42 | 36 | -0.2882 | n/a |
| 2 | -1.10 | -6.03 | 1.15 | 2 | -1000.0000 | n/a |
| 3 | -1.53 | -3.90 | 2.48 | 29 | -0.2222 | n/a |
| 4 | -1.43 | -6.19 | 2.17 | 48 | -0.0930 | n/a |
| 5 | -1.85 | -5.85 | 2.61 | 3 | -1000.0000 | n/a |
| 6 | -4.08 | -8.81 | 4.36 | 23 | -0.1880 | n/a |
| 7 | -1.07 | -8.05 | 1.19 | 21 | -0.3485 | n/a |
| 8 | -1.57 | -6.40 | 2.35 | 100 | -0.0439 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -4.37 | -2.03 | 4.77 | -0.0940 |
| fees_2x | -4.73 | -2.19 | 4.93 | -0.1006 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -4.00 | -1.94 | 4.61 | -0.0792 |
| very_low_liquidity | -4.00 | -2.06 | 4.61 | -0.0788 |
| high_slippage | -4.07 | -1.88 | 4.66 | -0.0881 |
| extreme_slippage | -4.16 | -1.92 | 4.75 | -0.0899 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -4.02 | -1.86 | 4.61 | -0.0873 |
| spread_widen_25bps | -4.03 | -1.82 | 4.61 | -0.0914 |
| thin_book | -4.59 | -3.46 | 4.63 | -0.3788 |
| very_thin_book | -4.77 | -2.39 | 6.44 | -0.1066 |
| entry_spread_stress | -4.02 | -1.82 | 4.61 | -0.0914 |
| combined_market_deterioration | -4.82 | -3.51 | 4.85 | -0.4250 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0024)
- **Trend**: ranging (efficiency: 0.0159)
- **Best holdout score**: -0.1169 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0436 | -0.1169 | -1.71 | 2.77 | 31 |
| 1 | -0.0533 | -1000.0000 | -1.55 | 2.31 | 3 |
| 2 | -0.0596 | -0.3329 | -1.46 | 2.31 | 4 |
| 3 | -0.0605 | -0.2246 | -1.68 | 2.60 | 10 |
| 4 | -0.0621 | -1000.0000 | -1.33 | 2.05 | 3 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51899
- **Expected rows**: 51899
- **Missing rows**: 0
- **Forward-fill count**: 450
- **Forward-fill fraction**: 0.008670687296479702
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0360 <= 0; recent PnL -1.7534% < 0
- **Objective score**: -0.036003050007101405
- **PnL %**: -1.753400391337533
- **Trade count**: 58

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1931 <= 0; recent PnL -1.4000% < 0
- **Objective score**: -0.193134386820076
- **PnL %**: -1.3999873153820563
- **Trade count**: 75

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2930 <= 0; recent PnL -2.8599% < 0
- **Objective score**: -0.2929895168971731
- **PnL %**: -2.8598617937520805
- **Trade count**: 110

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.08692977914658268
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0869, -0.0869 |
| bb_std | -0.0869, -0.0869 |
| bbp_entry_threshold | -0.0869, -0.0869 |
| rsi_length | -0.0869, -0.0870 |
| rsi_entry_threshold | -0.0789, -0.0869 |
| trend_ema_length | -0.0869, -0.0869 |
| max_atr_pct_for_entry | -0.0869, -0.0869 |
| volume_filter_window | -0.0869, -0.0869 |
| min_volume_quantile | -0.0869, -0.0869 |
| stop_loss | -0.0946, -0.0793 |
| take_profit | -0.0858, -0.0880 |
| cooldown_time | -0.0869, -0.0869 |
| total_amount_quote | -0.0789, -0.1109 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4291665983388723
- **Max CV**: 0.7196328120993434
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3758 | 0.019536712695748096 | 0.06361941594560416 | 0.03752444198017389 |
| take_profit | 0.7196 | 0.005189265228006389 | 0.02572000482032313 | 0.00868406654019231 |
| cooldown_time | 0.5451 | 3137.0 | 15255.0 | 6535.9 |
| total_amount_quote | 0.0761 | 777.517620122268 | 999.329155370399 | 904.9115469608975 |

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
| recent_objective | > 0 | -0.036003050007101405 | FAIL |
| recent_pnl | >= 0 | -1.753400391337533 | FAIL |
| recent_trades | >= 5 | 58 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.11694613239291071 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.036003050007101405, pnl=-1.753400391337533, trades=58, reason=recent objective score -0.0360 <= 0; recent PnL -1.7534% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.193134386820076, pnl=-1.3999873153820563, trades=75, reason=recent objective score -0.1931 <= 0; recent PnL -1.4000% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.2929895168971731, pnl=-2.8598617937520805, trades=110, reason=recent objective score -0.2930 <= 0; recent PnL -2.8599% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4291665983388723 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51899 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0360 <= 0; recent PnL -1.7534% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1931 <= 0; recent PnL -1.4000% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2930 <= 0; recent PnL -2.8599% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51899
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8065
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T12:35:53.351131+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 8307
- **validation_status**: validated_fail
