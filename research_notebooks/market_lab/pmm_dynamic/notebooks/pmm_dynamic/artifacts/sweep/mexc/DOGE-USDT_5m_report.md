# PMM Dynamic Optimization Report: mexc_DOGE-USDT_5m_sweep_v1

Generated: 2026-04-09 03:01:26 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T03:01:26.360118+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 4301 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOGE-USDT
- **interval**: 5m
- **n_candles**: 51871
- **dataset_hash**: 18ef6b0e2b6192cd94275f611899ba76b151793fb34885bdf967f2cd197c8796
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 857.6301225416319
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.9394944469255084 |
| buy_n_levels | 4 |
| buy_side_weight | 0.24052587576725803 |
| buy_spread_base | 2.288134367982081 |
| buy_spread_ratio | 2.4934480033919115 |
| cooldown_time | 4546 |
| executor_refresh_time | 11434 |
| macd_fast | 25 |
| macd_signal | 5 |
| macd_slow | 27 |
| natr_length | 25 |
| sell_n_levels | 6 |
| sell_spread_base | 4.586167346198922 |
| sell_spread_ratio | 1.8027460306888825 |
| stop_loss | 0.013553679939316929 |
| take_profit | 0.005273329031698073 |
| time_limit | 112097 |
| total_amount_quote | 857.6301225416319 |
| trailing_stop_activation | 0.09509570294180325 |
| trailing_stop_delta | 0.003940379671700113 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 857.6301225416319 |
| Selected | 857.6301225416319 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.7165
- **Net PnL (quote)**: -14.7215
- **Sharpe Ratio**: -3.4690
- **Max Drawdown %**: 1.7602
- **Profit Factor**: 0.620434566202333
- **Trade Count**: 918
- **Total Fees (quote)**: 2.9942
- **Maker Fees**: 2.4702
- **Taker Fees**: 0.5241
- **Fee Drag %**: 0.3491
- **TP Min-Notional Failures**: 7933 :warning:
  > 7933 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0385
- **PnL Component**: -0.0173
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0132
- **Fee Drag Component**: -0.0017
- **Inventory Component**: -0.0062
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0060**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.31 | -8.76 | 0.39 | 76 | -0.0109 | n/a |
| 1 | -0.02 | -0.82 | 0.16 | 77 | -0.0032 | n/a |
| 2 | -0.19 | -6.48 | 0.32 | 67 | -0.0062 | n/a |
| 3 | -0.05 | -3.15 | 0.09 | 73 | -0.0030 | n/a |
| 4 | -0.47 | -3.56 | 0.69 | 94 | -0.0149 | n/a |
| 5 | -0.04 | -1.07 | 0.13 | 91 | -0.0032 | n/a |
| 6 | -0.15 | -5.14 | 0.22 | 81 | -0.0050 | n/a |
| 7 | -0.00 | -0.10 | 0.07 | 80 | -0.0023 | n/a |
| 8 | -0.16 | -7.33 | 0.20 | 83 | -0.0079 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0808)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.89 | -3.82 | 1.93 | -0.0424 |
| fees_2x | -2.07 | -4.16 | 2.11 | -0.0464 |
| latency_plus1 | -1.72 | -3.48 | 1.76 | -0.0385 |
| latency_plus2 | -1.70 | -3.58 | 1.74 | -0.0368 |
| latency_plus3 | -1.80 | -3.77 | 1.84 | -0.0399 |
| low_liquidity | -1.72 | -3.47 | 1.76 | -0.0385 |
| very_low_liquidity | -1.72 | -3.47 | 1.76 | -0.0385 |
| high_slippage | -1.87 | -3.78 | 1.91 | -0.0412 |
| extreme_slippage | -2.17 | -4.39 | 2.22 | -0.0466 |
| combined_adverse | -2.05 | -4.13 | 2.09 | -0.0452 |
| spread_widen_10bps | -2.05 | -3.93 | 2.17 | -0.0455 |
| spread_widen_25bps | -2.84 | -5.65 | 2.94 | -0.0591 |
| thin_book | -1.84 | -3.97 | 1.93 | -0.0393 |
| very_thin_book | -2.31 | -6.19 | 2.37 | -0.0454 |
| entry_spread_stress | -2.50 | -4.44 | 2.58 | -0.0543 |
| combined_market_deterioration | -3.43 | -6.17 | 3.63 | -0.0726 |
| severe_adverse | -4.11 | -10.78 | 4.15 | -0.0808 |

## Holdout Validation

- **Holdout bars**: 8761
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0032)
- **Trend**: ranging (efficiency: 0.0016)
- **Best holdout score**: -0.0027 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0596 | -0.0040 | -0.01 | 0.25 | 175 |
| 1 | -0.0035 | -0.0110 | -0.17 | 0.26 | 242 |
| 2 | -0.0036 | -0.0027 | 0.02 | 0.12 | 170 |
| 3 | -0.0037 | -0.0211 | -0.35 | 0.85 | 314 |
| 4 | -0.0038 | -0.0500 | -1.54 | 2.15 | 379 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51871
- **Expected rows**: 51871
- **Missing rows**: 0
- **Forward-fill count**: 89
- **Forward-fill fraction**: 0.0017157949528638352
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0089 <= 0; recent PnL -0.1856% < 0
- **Objective score**: -0.008857120330578243
- **PnL %**: -0.185632995373319
- **Trade count**: 159

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0084 <= 0; recent PnL -0.0831% < 0
- **Objective score**: -0.008359033456789556
- **PnL %**: -0.08307937554338168
- **Trade count**: 83

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0589 <= 0; recent PnL -0.0242% < 0
- **Objective score**: -0.058912013701316275
- **PnL %**: -0.024156361386234632
- **Trade count**: 37

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: -0.0426490847391147
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0334, -0.0699 |
| sell_spread_base | -0.0432, -0.0621 |
| stop_loss | -0.0568, -0.0344 |
| take_profit | -0.0476, -0.0411 |
| executor_refresh_time | -0.0568, -0.0523 |
| cooldown_time | -0.0510, -0.0487 |
| total_amount_quote | -0.0658, -0.1280 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3183974197163207
- **Max CV**: 0.890049094178622
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0859 | 2.660531323584412 | 3.4401038069566314 | 3.01963835052421 |
| buy_spread_ratio | 0.0622 | 2.104904290099437 | 2.4939951799357654 | 2.3224509502529274 |
| sell_spread_base | 0.8900 | 0.21219941081322272 | 3.827166722733471 | 1.1834518896190602 |
| sell_spread_ratio | 0.3222 | 1.3758912281386193 | 2.949307820272511 | 1.7754945908756525 |
| buy_side_weight | 0.2425 | 0.20967990737573822 | 0.43913228853166425 | 0.2998700240543456 |
| amount_skew | 0.0842 | 2.774059978498929 | 3.4652194550466486 | 3.0304773151132633 |
| stop_loss | 0.6974 | 0.010131501017256383 | 0.05109655055021374 | 0.01751249595231095 |
| take_profit | 0.0870 | 0.005043099861959361 | 0.006637223019363921 | 0.0058346419327984745 |
| executor_refresh_time | 0.3799 | 2366.0 | 12166.0 | 7491.1 |
| cooldown_time | 0.4994 | 1593.0 | 7103.0 | 4213.9 |
| total_amount_quote | 0.1516 | 566.5547566668133 | 999.4827336280256 | 821.4980824043007 |

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
| recent_objective | > 0 | -0.008857120330578243 | FAIL |
| recent_pnl | >= 0 | -0.185632995373319 | FAIL |
| recent_trades | >= 5 | 159 | PASS |
| worst_stress | > -10 | -0.08077758218967616 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.004039375588599155 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.08077758218967616 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | FAIL | score=-0.008857120330578243, pnl=-0.185632995373319, trades=159, reason=recent objective score -0.0089 <= 0; recent PnL -0.1856% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.008359033456789556, pnl=-0.08307937554338168, trades=83, reason=recent objective score -0.0084 <= 0; recent PnL -0.0831% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.058912013701316275, pnl=-0.024156361386234632, trades=37, reason=recent objective score -0.0589 <= 0; recent PnL -0.0242% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3183974197163207 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51871 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0089 <= 0; recent PnL -0.1856% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0084 <= 0; recent PnL -0.0831% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0589 <= 0; recent PnL -0.0242% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51871
- **Pre-release bars**: 43806
- **Dev bars**: 35045
- **Holdout bars**: 8761
- **Recent 28d bars**: 8065
- **Recent window start**: 1773281400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T03:01:26.360118+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 4301
