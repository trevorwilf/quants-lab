# PMM Dynamic Optimization Report: nonkyc_ENA-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:28:53 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:28:53.935855+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 345 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ENA-USDT
- **interval**: 5m+4h
- **n_candles**: 55243
- **dataset_hash**: 9d86515c9456d22b248641958a0c019c7e57ca2c859a5f650471718bd707d1ce
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 984.7313231208709
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 70741 |
| min_volume_quantile | 0.023879861380555024 |
| regime_adx_length | 15 |
| regime_adx_threshold | 17.720481767314197 |
| regime_ema_fast | 52 |
| regime_ema_slow | 53 |
| stop_loss | 0.025780111676895083 |
| take_profit | 0.09168558950697082 |
| take_profit_order_type | MARKET |
| time_limit | 257919 |
| total_amount_quote | 984.7313231208709 |
| trailing_stop_activation | 0.006392270262381744 |
| trailing_stop_delta | 0.01386054690708954 |
| volume_filter_window | 206 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 984.7313231208709 |
| Selected | 984.7313231208709 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.3781
- **Net PnL (quote)**: -13.5710
- **Sharpe Ratio**: -0.7272
- **Max Drawdown %**: 1.9010
- **Profit Factor**: 0.2633477986352865
- **Trade Count**: 102
- **Total Fees (quote)**: 15.4524
- **Maker Fees**: 5.6014
- **Taker Fees**: 9.8511
- **Fee Drag %**: 1.5692

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0361
- **PnL Component**: -0.0139
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0143
- **Fee Drag Component**: -0.0078
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0884**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.45 | -2.62 | 1.65 | 46 | -0.0467 | n/a |
| 1 | -2.82 | -4.85 | 3.04 | 15 | -0.3046 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | -1.67 | -7.87 | 2.61 | 76 | -0.0397 | n/a |
| 4 | -2.92 | -15.42 | 2.92 | 15 | -0.3678 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | -2.77 | -5.91 | 3.31 | 171 | -0.0926 | n/a |
| 8 | -1.43 | -6.86 | 1.81 | 188 | -0.0541 | n/a |
| 9 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.16 | -1.14 | 2.43 | -0.0726 |
| fees_2x | -1.18 | -0.63 | 2.85 | -0.1674 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -3.44 | -4.10 | 3.71 | -0.0674 |
| very_low_liquidity | -1.68 | -2.67 | 1.82 | -0.0966 |
| high_slippage | -1.63 | -0.86 | 2.03 | -0.0423 |
| extreme_slippage | -2.13 | -1.12 | 2.45 | -0.0687 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.74 | -1.29 | 3.02 | -0.0584 |
| spread_widen_25bps | -2.71 | -1.27 | 3.10 | -0.0586 |
| thin_book | -1.71 | -2.40 | 1.86 | -0.2881 |
| very_thin_book | -2.27 | -3.05 | 2.37 | -0.4330 |
| entry_spread_stress | -2.51 | -1.18 | 2.95 | -0.0555 |
| combined_market_deterioration | -3.05 | -4.06 | 3.24 | -0.2038 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 9439
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0032)
- **Trend**: ranging (efficiency: 0.0100)
- **Best holdout score**: -0.0299 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0180 | -0.0616 | -2.77 | 3.31 | 171 |
| 1 | -0.0525 | -0.2130 | -3.25 | 3.30 | 12 |
| 2 | -0.0707 | -0.0299 | -1.16 | 1.80 | 67 |
| 3 | -0.0954 | -0.0580 | -2.78 | 3.33 | 69 |
| 4 | -0.0962 | -0.4608 | -3.56 | 3.79 | 15 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 55243
- **Expected rows**: 55263
- **Missing rows**: 20
- **Forward-fill count**: 140
- **Forward-fill fraction**: 0.002534257734011549
- **Longest gap (seconds)**: 6300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3866 <= 0; recent PnL -2.4069% < 0
- **Objective score**: -0.3866288651928669
- **PnL %**: -2.4068851913596623
- **Trade count**: 22

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3868 <= 0; recent PnL -2.4069% < 0
- **Objective score**: -0.386754619621574
- **PnL %**: -2.4068851913596623
- **Trade count**: 22

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3136 <= 0; recent PnL -1.9367% < 0
- **Objective score**: -0.3135976723527416
- **PnL %**: -1.9366573661727373
- **Trade count**: 25

## Sensitivity Analysis

- **Sensitivity penalty**: 0.4444444444444444
- **Baseline score**: -0.034920393675412706
- **Sign flips**: 0
- **Collapse count**: 8
- **Perturbations**: 20
- **Rejected**: 2

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -1000.0000, -0.0599 |
| regime_ema_slow | -0.0805, -1000.0000 |
| regime_adx_length | -0.1881, -0.0571 |
| regime_adx_threshold | -0.1881, -0.0571 |
| volume_filter_window | -0.0349, -0.0349 |
| min_volume_quantile | -0.0349, -0.0349 |
| stop_loss | -0.0367, -0.0512 |
| take_profit | -0.0349, -0.0349 |
| cooldown_time | -0.0979, -0.0538 |
| total_amount_quote | -0.0411, -0.0501 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.34145202764507715
- **Max CV**: 0.5917216895140351
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2651 | 0.020169888751515194 | 0.042760629555660366 | 0.026819638845235205 |
| take_profit | 0.5917 | 0.01337719018301386 | 0.09168558950697082 | 0.04919824864063286 |
| cooldown_time | 0.3214 | 30714.0 | 86064.0 | 61571.0 |
| total_amount_quote | 0.1876 | 552.0292867610037 | 984.7313231208709 | 782.3599421002265 |

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
| recent_objective | > 0 | -0.3866288651928669 | FAIL |
| recent_pnl | >= 0 | -2.4068851913596623 | FAIL |
| recent_trades | >= 5 | 22 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.4444444444444444 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.061649383911557845 |
| walkforward | PASS | 10 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.4444444444444444 |
| recent_28d | FAIL | score=-0.3866288651928669, pnl=-2.4068851913596623, trades=22, reason=recent objective score -0.3866 <= 0; recent PnL -2.4069% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.386754619621574, pnl=-2.4068851913596623, trades=22, reason=recent objective score -0.3868 <= 0; recent PnL -2.4069% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.3135976723527416, pnl=-1.9366573661727373, trades=25, reason=recent objective score -0.3136 <= 0; recent PnL -1.9367% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.34145202764507715 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 55243 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3866 <= 0; recent PnL -2.4069% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3868 <= 0; recent PnL -2.4069% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.3136 <= 0; recent PnL -1.9367% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 55243
- **Pre-release bars**: 47198
- **Dev bars**: 37759
- **Holdout bars**: 9439
- **Recent 28d bars**: 8045
- **Recent window start**: 1774096800

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:28:53.935855+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 345
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
