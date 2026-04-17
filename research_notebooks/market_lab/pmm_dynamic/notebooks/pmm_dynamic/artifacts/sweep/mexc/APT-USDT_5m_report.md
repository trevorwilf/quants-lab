# PMM Dynamic Optimization Report: mexc_APT-USDT_5m_sweep_v1

Generated: 2026-04-09 00:56:07 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T00:56:07.186350+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 10471 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: APT-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 6de4f147e163bf08aa42061b1f703bd4d6c1a91fc9f9386a03b757e4b2680689
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 917.532617693142
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.1645180873622047 |
| buy_n_levels | 4 |
| buy_side_weight | 0.4173558875354981 |
| buy_spread_base | 1.8358901312904046 |
| buy_spread_ratio | 2.6794322498998686 |
| cooldown_time | 1666 |
| executor_refresh_time | 1518 |
| macd_fast | 5 |
| macd_signal | 27 |
| macd_slow | 68 |
| natr_length | 14 |
| sell_n_levels | 10 |
| sell_spread_base | 3.6926921842913645 |
| sell_spread_ratio | 1.635263386330629 |
| stop_loss | 0.013000824107883968 |
| take_profit | 0.03984485982921788 |
| time_limit | 139228 |
| total_amount_quote | 917.532617693142 |
| trailing_stop_activation | 0.003367041611017434 |
| trailing_stop_delta | 0.0010863600894002407 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 917.532617693142 |
| Selected | 917.532617693142 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 1.1149
- **Net PnL (quote)**: 10.2292
- **Sharpe Ratio**: 2.7913
- **Max Drawdown %**: 0.5978
- **Profit Factor**: 1.2954966145058768
- **Trade Count**: 1018
- **Total Fees (quote)**: 4.6439
- **Maker Fees**: 2.3205
- **Taker Fees**: 2.3234
- **Fee Drag %**: 0.5061

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0018
- **PnL Component**: 0.0111
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0045
- **Fee Drag Component**: -0.0025
- **Inventory Component**: -0.0023
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0043**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.01 | -0.34 | 0.10 | 114 | -0.0034 | n/a |
| 1 | 0.03 | 1.49 | 0.08 | 80 | -0.0028 | n/a |
| 2 | 0.01 | 0.86 | 0.05 | 66 | -0.0027 | n/a |
| 3 | -0.03 | -1.77 | 0.09 | 109 | -0.0036 | n/a |
| 4 | -0.39 | -5.57 | 0.58 | 94 | -0.0109 | n/a |
| 5 | 0.38 | 8.47 | 0.14 | 102 | 0.0001 | n/a |
| 6 | -0.07 | -1.78 | 0.24 | 106 | -0.0051 | n/a |
| 7 | 0.17 | 5.83 | 0.06 | 77 | -0.0013 | n/a |
| 8 | -0.14 | -3.42 | 0.29 | 73 | -0.0061 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0539)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 0.86 | 2.16 | 0.61 | -0.0021 |
| fees_2x | 0.61 | 1.53 | 0.62 | -0.0059 |
| latency_plus1 | 0.83 | 2.08 | 0.61 | -0.0011 |
| latency_plus2 | 0.50 | 1.29 | 0.67 | -0.0045 |
| latency_plus3 | 0.25 | 0.64 | 0.75 | -0.0078 |
| low_liquidity | 1.11 | 2.79 | 0.60 | 0.0018 |
| very_low_liquidity | 1.11 | 2.79 | 0.60 | 0.0018 |
| high_slippage | 0.48 | 1.22 | 0.63 | -0.0047 |
| extreme_slippage | -0.78 | -2.00 | 1.35 | -0.0228 |
| combined_adverse | -0.02 | -0.05 | 0.86 | -0.0126 |
| spread_widen_10bps | -0.18 | -0.31 | 1.07 | -0.0175 |
| spread_widen_25bps | -0.98 | -1.73 | 1.72 | -0.0276 |
| thin_book | -0.78 | -2.08 | 1.20 | -0.0208 |
| very_thin_book | -0.51 | -3.03 | 0.71 | -0.0112 |
| entry_spread_stress | -0.18 | -0.40 | 1.03 | -0.0153 |
| combined_market_deterioration | -1.55 | -3.48 | 1.92 | -0.0354 |
| severe_adverse | -2.73 | -7.95 | 2.87 | -0.0539 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0037)
- **Trend**: ranging (efficiency: 0.0045)
- **Best holdout score**: -0.0015 (rank #4)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0261 | -0.0030 | 0.16 | 0.24 | 198 |
| 1 | 0.0010 | -0.0176 | -0.40 | 1.63 | 191 |
| 2 | 0.0008 | -0.0135 | 0.59 | 0.94 | 333 |
| 3 | 0.0005 | -0.0146 | -0.15 | 1.06 | 740 |
| 4 | 0.0004 | -0.0015 | 1.38 | 0.58 | 334 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 40
- **Forward-fill fraction**: 0.0007715900542042013
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0055 <= 0; recent PnL -0.0679% < 0
- **Objective score**: -0.005526893545872099
- **PnL %**: -0.0679039573346477
- **Trade count**: 133

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0020 <= 0
- **Objective score**: -0.0020015751389320944
- **PnL %**: 0.10666428677884876
- **Trade count**: 64

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0944 <= 0
- **Objective score**: -0.09435199041300675
- **PnL %**: 0.021071293994143533
- **Trade count**: 27

## Sensitivity Analysis

- **Sensitivity penalty**: 0.6428571428571429
- **Baseline score**: -0.00042062045855318806
- **Sign flips**: 1
- **Collapse count**: 8
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0054, -0.0046 |
| sell_spread_base | -0.0002, -0.0025 |
| stop_loss | -0.0022, 0.0005 |
| take_profit | -0.0004, -0.0004 |
| executor_refresh_time | -0.0004, -0.0143 |
| cooldown_time | -0.0045, -0.0102 |
| total_amount_quote | -0.0009, -0.0003 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5179739460566792
- **Max CV**: 1.2954809369187898
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2905 | 0.8245200792413475 | 2.7691482788634074 | 2.0081578595220364 |
| buy_spread_ratio | 0.2429 | 1.465002490685508 | 2.8037180264680264 | 1.9630737889526966 |
| sell_spread_base | 0.8166 | 0.2036319211816367 | 3.621025186661554 | 1.512890101239258 |
| sell_spread_ratio | 0.1251 | 1.9199482328705768 | 2.872823131679079 | 2.4351619919933802 |
| buy_side_weight | 0.2185 | 0.2923682830884573 | 0.7511514802941057 | 0.5708480424985789 |
| amount_skew | 0.3035 | 1.4372650417034185 | 3.970783798668447 | 2.906258485478996 |
| stop_loss | 1.2955 | 0.011941787074782856 | 0.1953885856344273 | 0.043430715870749335 |
| take_profit | 0.6742 | 0.006501692553407818 | 0.05592662065141185 | 0.02305412387093809 |
| executor_refresh_time | 0.8433 | 757.0 | 14253.0 | 5777.5 |
| cooldown_time | 0.7799 | 384.0 | 3122.0 | 1322.2 |
| total_amount_quote | 0.1078 | 636.5550829070982 | 941.817543918333 | 822.4308309085585 |

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
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.005526893545872099 | FAIL |
| recent_pnl | >= 0 | -0.0679039573346477 | FAIL |
| recent_trades | >= 5 | 133 | PASS |
| worst_stress | > -10 | -0.053911451047634604 | PASS |
| sensitivity_penalty | < 0.50 | 0.6428571428571429 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.0030203100649815397 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.053911451047634604 |
| sensitivity | FAIL | penalty=0.6428571428571429 |
| recent_28d | FAIL | score=-0.005526893545872099, pnl=-0.0679039573346477, trades=133, reason=recent objective score -0.0055 <= 0; recent PnL -0.0679% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.0020015751389320944, pnl=0.10666428677884876, trades=64, reason=recent objective score -0.0020 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.09435199041300675, pnl=0.021071293994143533, trades=27, reason=recent objective score -0.0944 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5179739460566792 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0055 <= 0; recent PnL -0.0679% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0020 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0944 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51841
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065
- **Recent window start**: 1773272700

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T00:56:07.186350+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 10471
