# PMM Dynamic Optimization Report: mexc_ASTER-USDT_5m_sweep_v1

Generated: 2026-04-09 01:22:05 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T01:22:05.028154+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 3574 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ASTER-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 05c6178b72e49ad53a62ee1b6042ca0f8ad2adb74838ae4e259e4d3a32a7ecad
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 748.2271858974029
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.4091529222625763 |
| buy_n_levels | 6 |
| buy_side_weight | 0.384756223060396 |
| buy_spread_base | 2.8170299631252584 |
| buy_spread_ratio | 1.3678592243935264 |
| cooldown_time | 1680 |
| executor_refresh_time | 6584 |
| macd_fast | 8 |
| macd_signal | 10 |
| macd_slow | 60 |
| natr_length | 36 |
| sell_n_levels | 2 |
| sell_spread_base | 3.913763025729693 |
| sell_spread_ratio | 2.1970690278025304 |
| stop_loss | 0.019691678651177165 |
| take_profit | 0.010184119248646878 |
| time_limit | 59519 |
| total_amount_quote | 748.2271858974029 |
| trailing_stop_activation | 0.00040322409764751907 |
| trailing_stop_delta | 0.0013792541257811814 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 748.2271858974029 |
| Selected | 748.2271858974029 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 9.1981
- **Net PnL (quote)**: 68.8226
- **Sharpe Ratio**: 4.4346
- **Max Drawdown %**: 1.2283
- **Profit Factor**: 2.368213895600006
- **Trade Count**: 782
- **Total Fees (quote)**: 7.6999
- **Maker Fees**: 3.8423
- **Taker Fees**: 3.8576
- **Fee Drag %**: 1.0291

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0736
- **PnL Component**: 0.0880
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0092
- **Fee Drag Component**: -0.0051
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.0013**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.54 | -2.88 | 0.97 | 92 | -0.0135 | n/a |
| 1 | 0.83 | 6.20 | 0.38 | 99 | 0.0045 | n/a |
| 2 | 0.51 | 6.46 | 0.08 | 59 | 0.0041 | n/a |
| 3 | 0.71 | 6.03 | 0.34 | 72 | 0.0039 | n/a |
| 4 | 1.08 | 9.54 | 0.13 | 71 | 0.0093 | n/a |
| 5 | 2.42 | 6.89 | 0.66 | 77 | 0.0185 | n/a |
| 6 | -0.54 | -3.63 | 0.83 | 71 | -0.0120 | n/a |
| 7 | 0.49 | 8.64 | 0.07 | 55 | 0.0020 | n/a |
| 8 | 0.21 | 1.36 | 0.79 | 73 | -0.0044 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1557)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 8.68 | 4.20 | 1.29 | 0.0658 |
| fees_2x | 8.17 | 3.96 | 1.35 | 0.0581 |
| latency_plus1 | 9.21 | 4.44 | 1.23 | 0.0737 |
| latency_plus2 | 9.07 | 4.37 | 1.23 | 0.0724 |
| latency_plus3 | 9.41 | 4.64 | 0.99 | 0.0774 |
| low_liquidity | 9.20 | 4.43 | 1.23 | 0.0736 |
| very_low_liquidity | 9.20 | 4.43 | 1.23 | 0.0736 |
| high_slippage | 7.91 | 3.86 | 1.37 | 0.0607 |
| extreme_slippage | 5.33 | 2.67 | 1.65 | 0.0328 |
| combined_adverse | 7.40 | 3.63 | 1.42 | 0.0530 |
| spread_widen_10bps | 6.95 | 3.37 | 1.44 | 0.0512 |
| spread_widen_25bps | 5.04 | 2.49 | 1.59 | 0.0320 |
| thin_book | -0.16 | -0.08 | 3.18 | -0.0292 |
| very_thin_book | -2.74 | -2.28 | 3.89 | -0.0634 |
| entry_spread_stress | 6.09 | 2.94 | 1.62 | 0.0417 |
| combined_market_deterioration | -0.51 | -0.27 | 3.95 | -0.0454 |
| severe_adverse | -6.20 | -3.17 | 9.05 | -0.1557 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0035)
- **Trend**: ranging (efficiency: 0.0083)
- **Best holdout score**: 0.0102 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0411 | -0.0060 | 0.09 | 0.83 | 133 |
| 1 | 0.0092 | 0.0081 | 2.82 | 1.29 | 322 |
| 2 | 0.0090 | -0.0045 | 1.85 | 1.14 | 256 |
| 3 | 0.0089 | 0.0102 | 3.29 | 1.29 | 464 |
| 4 | 0.0082 | 0.0099 | 2.17 | 1.11 | 131 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 57
- **Forward-fill fraction**: 0.0010995158272409868
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.0007519320985173781
- **PnL %**: 0.755450101049241
- **Trade count**: 115

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.007489392438005379
- **PnL %**: 0.8049463672435052
- **Trade count**: 50

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1322 <= 0
- **Objective score**: -0.13223354615631389
- **PnL %**: 0.39561588216892274
- **Trade count**: 16

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: 0.08028147278122104
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0548, 0.0745 |
| sell_spread_base | 0.0803, 0.0798 |
| stop_loss | 0.0743, 0.0615 |
| take_profit | 0.0803, 0.0803 |
| executor_refresh_time | 0.0680, 0.0538 |
| cooldown_time | 0.0581, 0.0803 |
| total_amount_quote | 0.0787, 0.0036 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3213942287655716
- **Max CV**: 0.6174166674346546
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: stop_loss, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2557 | 1.5017469767345841 | 3.621285544402634 | 2.605669561664864 |
| buy_spread_ratio | 0.1229 | 1.2277478769431684 | 1.783213549572857 | 1.3965206257032052 |
| sell_spread_base | 0.4007 | 0.2211784979275064 | 0.6542606267603432 | 0.42962635181609227 |
| sell_spread_ratio | 0.1929 | 1.7090076667902712 | 2.927664191583241 | 2.21033566232741 |
| buy_side_weight | 0.0974 | 0.5375712018816218 | 0.7368729980454054 | 0.6496431364627904 |
| amount_skew | 0.2645 | 1.557994288894232 | 3.51716892549556 | 2.417912921453489 |
| stop_loss | 0.5481 | 0.02859452213108557 | 0.22202134435762486 | 0.12275324541364704 |
| take_profit | 0.3857 | 0.019726932591403904 | 0.12923469957276434 | 0.08841650718558751 |
| executor_refresh_time | 0.3968 | 2171.0 | 12683.0 | 7505.4 |
| cooldown_time | 0.6174 | 248.0 | 6302.0 | 3126.4 |
| total_amount_quote | 0.2533 | 372.4760312783574 | 992.0982099383168 | 725.7319415453769 |

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
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 0.0007519320985173781 | PASS |
| recent_pnl | >= 0 | 0.755450101049241 | PASS |
| recent_trades | >= 5 | 115 | PASS |
| worst_stress | > -10 | -0.15572722607294606 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.0059718982338136046 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.15572722607294606 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | PASS | score=0.0007519320985173781, pnl=0.755450101049241, trades=115, reason= |
| recent_14d_info | PASS | informational only; score=0.007489392438005379, pnl=0.8049463672435052, trades=50, reason= |
| recent_7d_info | FAIL | informational only; score=-0.13223354615631389, pnl=0.39561588216892274, trades=16, reason=recent objective score -0.1322 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3213942287655716 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| recent_14d_info | true | PASS | recent_14d_info | — | — |  |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1322 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
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
- **run_timestamp**: 2026-04-09T01:22:05.028154+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 3574
