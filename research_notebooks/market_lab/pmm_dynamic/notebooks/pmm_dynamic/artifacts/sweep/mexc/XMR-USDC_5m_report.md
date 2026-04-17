# PMM Dynamic Optimization Report: mexc_XMR-USDC_5m_sweep_v1

Generated: 2026-04-09 12:23:09 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T12:23:09.275038+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 11655 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XMR-USDC
- **interval**: 5m
- **n_candles**: 51915
- **dataset_hash**: cb5c9a31b74468086bed6e91d62b5ea529dcb8c22331128ba80282929be8df0a
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 999.8202841725578
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.703502847438733 |
| buy_n_levels | 5 |
| buy_side_weight | 0.660811367342335 |
| buy_spread_base | 3.6207362561970924 |
| buy_spread_ratio | 1.42707679654801 |
| cooldown_time | 167 |
| executor_refresh_time | 4464 |
| macd_fast | 18 |
| macd_signal | 27 |
| macd_slow | 20 |
| natr_length | 19 |
| sell_n_levels | 3 |
| sell_spread_base | 0.5485229401315903 |
| sell_spread_ratio | 1.368081811214159 |
| stop_loss | 0.11550059129417775 |
| take_profit | 0.030058815054922992 |
| time_limit | 164488 |
| total_amount_quote | 999.8202841725578 |
| trailing_stop_activation | 0.019185374568438746 |
| trailing_stop_delta | 0.001469587609583419 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 999.8202841725578 |
| Selected | 999.8202841725578 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 231.2754
- **Net PnL (quote)**: 2312.3382
- **Sharpe Ratio**: 4.7638
- **Max Drawdown %**: 37.1462
- **Profit Factor**: 1.4973317160268127
- **Trade Count**: 4795
- **Total Fees (quote)**: 143.2419
- **Maker Fees**: 72.2498
- **Taker Fees**: 70.9921
- **Fee Drag %**: 14.3268
- **TP Min-Notional Failures**: 9 :warning:
  > 9 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.5915
- **PnL Component**: 1.1978
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.2786
- **Fee Drag Component**: -0.0716
- **Inventory Component**: -0.2496
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0102**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.56 | 3.19 | 0.42 | 68 | -0.0006 | n/a |
| 1 | -0.69 | -2.81 | 2.00 | 101 | -0.0409 | n/a |
| 2 | 1.06 | 4.65 | 0.79 | 111 | -0.0045 | n/a |
| 3 | 1.13 | 4.33 | 0.60 | 85 | 0.0036 | n/a |
| 4 | 3.38 | 7.77 | 0.93 | 109 | 0.0226 | n/a |
| 5 | -0.27 | -1.62 | 0.86 | 97 | -0.0122 | n/a |
| 6 | -1.38 | -7.05 | 1.91 | 100 | -0.0400 | n/a |
| 7 | 1.37 | 7.80 | 0.48 | 102 | 0.0069 | n/a |
| 8 | -2.20 | -10.03 | 2.49 | 138 | -0.0811 | n/a |

## Stress Test Results

Worst Scenario: **very_thin_book** (score: -0.4237)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 221.75 | 4.65 | 36.73 | 0.5313 |
| fees_2x | 220.39 | 4.64 | 37.48 | 0.4851 |
| latency_plus1 | 219.04 | 4.61 | 36.69 | 0.5584 |
| latency_plus2 | 220.85 | 4.54 | 37.85 | 0.5543 |
| latency_plus3 | 206.26 | 4.37 | 37.58 | 0.5131 |
| low_liquidity | 228.47 | 4.69 | 37.13 | 0.5839 |
| very_low_liquidity | 199.53 | 4.34 | 36.31 | 0.4993 |
| high_slippage | 216.87 | 4.59 | 36.70 | 0.5505 |
| extreme_slippage | 199.08 | 4.33 | 36.93 | 0.4920 |
| combined_adverse | 225.41 | 4.62 | 37.88 | 0.5344 |
| spread_widen_10bps | 277.96 | 4.99 | 39.96 | 0.6951 |
| spread_widen_25bps | 234.97 | 4.70 | 36.93 | 0.6014 |
| thin_book | 122.91 | 3.47 | 36.91 | 0.2212 |
| very_thin_book | 14.56 | 0.93 | 37.61 | -0.4237 |
| entry_spread_stress | 255.57 | 4.84 | 37.52 | 0.6549 |
| combined_market_deterioration | 103.74 | 3.15 | 34.46 | 0.1186 |
| severe_adverse | 43.06 | 1.80 | 33.61 | -0.2187 |

## Holdout Validation

- **Holdout bars**: 8777
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0032)
- **Trend**: ranging (efficiency: 0.0046)
- **Best holdout score**: -0.0229 (rank #0)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0839 | -0.0229 | -0.43 | 1.95 | 219 |
| 1 | 0.0052 | -0.0570 | -1.01 | 1.40 | 1247 |
| 2 | 0.0031 | -0.0816 | 0.25 | 2.62 | 609 |
| 3 | 0.0029 | -0.0675 | 13.95 | 3.31 | 636 |
| 4 | 0.0029 | -0.0537 | -0.28 | 1.40 | 1410 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51915
- **Expected rows**: 51950
- **Missing rows**: 35
- **Forward-fill count**: 105
- **Forward-fill fraction**: 0.0020225368390638545
- **Longest gap (seconds)**: 10800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0703 <= 0; recent PnL -1.6809% < 0
- **Objective score**: -0.07033328788259435
- **PnL %**: -1.6808734426809382
- **Trade count**: 258

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0420 <= 0; recent PnL -0.4758% < 0
- **Objective score**: -0.041982589703785704
- **PnL %**: -0.47581347931023205
- **Trade count**: 139

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0235 <= 0
- **Objective score**: -0.023529539820947857
- **PnL %**: 0.4450270092903924
- **Trade count**: 45

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.6457941798733519
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.4426, 0.6917 |
| sell_spread_base | 0.6195, 0.5820 |
| stop_loss | 0.6546, 0.6186 |
| take_profit | 0.6458, 0.6458 |
| executor_refresh_time | 0.5338, 0.6713 |
| cooldown_time | 0.6458, 0.6458 |
| total_amount_quote | 0.6024, 0.6087 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.43191101725648706
- **Max CV**: 0.980966397808815
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1654 | 2.2425890272191182 | 4.208628069369298 | 3.513319438715352 |
| buy_spread_ratio | 0.0715 | 1.388952388985435 | 1.682248186283174 | 1.5014572852262895 |
| sell_spread_base | 0.7501 | 0.2087630261645145 | 1.4089341371246373 | 0.5081916095387496 |
| sell_spread_ratio | 0.1784 | 1.3054329166236895 | 2.184775079827637 | 1.7824986418934645 |
| buy_side_weight | 0.1507 | 0.5234045915025995 | 0.7861634553030864 | 0.6647536930456945 |
| amount_skew | 0.0974 | 2.9085476045014373 | 3.9564229731339786 | 3.6527839237732613 |
| stop_loss | 0.7165 | 0.015219467423612194 | 0.23479190090828178 | 0.09162806200283055 |
| take_profit | 0.8827 | 0.005001213565462887 | 0.1296752652398174 | 0.04768852945967769 |
| executor_refresh_time | 0.6596 | 1675.0 | 13847.0 | 6055.4 |
| cooldown_time | 0.9810 | 191.0 | 5876.0 | 2302.8 |
| total_amount_quote | 0.0978 | 654.0370407151162 | 946.51999479283 | 859.5349820282083 |

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
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.07033328788259435 | FAIL |
| recent_pnl | >= 0 | -1.6808734426809382 | FAIL |
| recent_trades | >= 5 | 258 | PASS |
| worst_stress | > -10 | -0.42374261770947574 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.022851506435382 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_thin_book score=-0.42374261770947574 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.07033328788259435, pnl=-1.6808734426809382, trades=258, reason=recent objective score -0.0703 <= 0; recent PnL -1.6809% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.041982589703785704, pnl=-0.47581347931023205, trades=139, reason=recent objective score -0.0420 <= 0; recent PnL -0.4758% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.023529539820947857, pnl=0.4450270092903924, trades=45, reason=recent objective score -0.0235 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.43191101725648706 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51915 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0703 <= 0; recent PnL -1.6809% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0420 <= 0; recent PnL -0.4758% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0235 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51915
- **Pre-release bars**: 43885
- **Dev bars**: 35108
- **Holdout bars**: 8777
- **Recent 28d bars**: 8030
- **Recent window start**: 1773305100

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T12:23:09.275038+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 11655
