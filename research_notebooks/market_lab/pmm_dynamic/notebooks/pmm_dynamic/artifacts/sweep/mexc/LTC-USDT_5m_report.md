# PMM Dynamic Optimization Report: mexc_LTC-USDT_5m_sweep_v1

Generated: 2026-04-09 05:41:18 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T05:41:18.944640+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 4727 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: LTC-USDT
- **interval**: 5m
- **n_candles**: 51871
- **dataset_hash**: cf944fa068747eea58e1eb9f7f317d6b5e0411acf336d228310d1e3fa2a4b438
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 623.5987998361834
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.7245397984958446 |
| buy_n_levels | 6 |
| buy_side_weight | 0.27559479838106876 |
| buy_spread_base | 2.573739358252088 |
| buy_spread_ratio | 2.6420203358858747 |
| cooldown_time | 4883 |
| executor_refresh_time | 6932 |
| macd_fast | 23 |
| macd_signal | 24 |
| macd_slow | 52 |
| natr_length | 8 |
| sell_n_levels | 9 |
| sell_spread_base | 0.3087955759641368 |
| sell_spread_ratio | 2.0050574392514604 |
| stop_loss | 0.014212278568119248 |
| take_profit | 0.007026279909466579 |
| time_limit | 4645 |
| total_amount_quote | 623.5987998361834 |
| trailing_stop_activation | 0.06683382487455604 |
| trailing_stop_delta | 0.0010635255293261054 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 623.5987998361834 |
| Selected | 623.5987998361834 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.2761
- **Net PnL (quote)**: -7.9578
- **Sharpe Ratio**: -4.5990
- **Max Drawdown %**: 1.3893
- **Profit Factor**: 0.6737992203601981
- **Trade Count**: 634
- **Total Fees (quote)**: 2.2325
- **Maker Fees**: 1.5673
- **Taker Fees**: 0.6652
- **Fee Drag %**: 0.3580

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0273
- **PnL Component**: -0.0128
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0104
- **Fee Drag Component**: -0.0018
- **Inventory Component**: -0.0022
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0054**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.08 | -3.56 | 0.23 | 67 | -0.0050 | n/a |
| 1 | -0.21 | -6.23 | 0.23 | 68 | -0.0350 | n/a |
| 2 | -0.08 | -5.01 | 0.13 | 61 | -0.0042 | n/a |
| 3 | -0.04 | -1.59 | 0.21 | 71 | -0.0045 | n/a |
| 4 | -0.42 | -8.53 | 0.54 | 83 | -0.0250 | n/a |
| 5 | -0.27 | -7.85 | 0.35 | 82 | -0.0326 | n/a |
| 6 | -0.07 | -2.60 | 0.23 | 74 | -0.0049 | n/a |
| 7 | -0.06 | -2.54 | 0.15 | 65 | -0.0041 | n/a |
| 8 | -0.14 | -4.99 | 0.16 | 63 | -0.0461 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1537)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.46 | -5.23 | 1.55 | -0.0312 |
| fees_2x | -1.63 | -5.87 | 1.70 | -0.0351 |
| latency_plus1 | -0.81 | -2.81 | 0.93 | -0.0192 |
| latency_plus2 | -1.07 | -3.70 | 1.12 | -0.0232 |
| latency_plus3 | -1.22 | -4.48 | 1.33 | -0.0263 |
| low_liquidity | -1.28 | -4.60 | 1.39 | -0.0273 |
| very_low_liquidity | -1.28 | -4.60 | 1.39 | -0.0273 |
| high_slippage | -1.54 | -5.50 | 1.63 | -0.0319 |
| extreme_slippage | -2.08 | -7.23 | 2.14 | -0.0663 |
| combined_adverse | -1.25 | -4.29 | 1.32 | -0.0310 |
| spread_widen_10bps | -1.71 | -6.12 | 1.77 | -0.0346 |
| spread_widen_25bps | -2.33 | -8.07 | 2.36 | -0.0742 |
| thin_book | -1.51 | -4.61 | 1.54 | -0.0621 |
| very_thin_book | -1.72 | -5.69 | 1.74 | -0.0860 |
| entry_spread_stress | -1.89 | -6.81 | 1.94 | -0.0487 |
| combined_market_deterioration | -2.33 | -7.51 | 2.36 | -0.0810 |
| severe_adverse | -3.04 | -9.18 | 3.08 | -0.1537 |

## Holdout Validation

- **Holdout bars**: 8761
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0027)
- **Trend**: ranging (efficiency: 0.0009)
- **Best holdout score**: -0.0040 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0905 | -0.0040 | 0.04 | 0.23 | 156 |
| 1 | -0.0023 | -0.0580 | 0.87 | 1.39 | 381 |
| 2 | -0.0024 | -0.0062 | -0.13 | 0.26 | 179 |
| 3 | -0.0029 | -0.0460 | -2.09 | 2.15 | 939 |
| 4 | -0.0030 | -0.0165 | -0.20 | 0.52 | 281 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51871
- **Expected rows**: 51871
- **Missing rows**: 0
- **Forward-fill count**: 36
- **Forward-fill fraction**: 0.0006940294191359334
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0381 <= 0; recent PnL -0.2365% < 0
- **Objective score**: -0.03808296037552707
- **PnL %**: -0.23653650199271797
- **Trade count**: 123

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0462 <= 0; recent PnL -0.1041% < 0
- **Objective score**: -0.04624244774639692
- **PnL %**: -0.10406857236325646
- **Trade count**: 66

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1568 <= 0; recent PnL -0.0408% < 0
- **Objective score**: -0.15682054133447965
- **PnL %**: -0.04084369395895524
- **Trade count**: 32

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: -0.03099492758333205
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0572, -0.0434 |
| sell_spread_base | -0.0310, -0.0310 |
| stop_loss | -0.0288, -0.0293 |
| take_profit | -0.0308, -0.0290 |
| executor_refresh_time | -0.0371, -0.0197 |
| cooldown_time | -0.0239, -0.2867 |
| total_amount_quote | -0.0310, -0.0739 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.34250062691582894
- **Max CV**: 0.7188355360775854
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1755 | 2.2644532390088483 | 4.08676201503588 | 3.058619954783393 |
| buy_spread_ratio | 0.1857 | 1.4665366724752917 | 2.625606537604998 | 2.186013156135066 |
| sell_spread_base | 0.7188 | 0.21674222854593514 | 2.2344012151109114 | 0.9397851722141907 |
| sell_spread_ratio | 0.2452 | 1.2926076419486483 | 2.7309438000845367 | 2.05416773660163 |
| buy_side_weight | 0.4172 | 0.21740702825858746 | 0.6413316892092851 | 0.38467325931872803 |
| amount_skew | 0.1993 | 2.119386193077405 | 3.974260473581811 | 2.9466942912753598 |
| stop_loss | 0.3872 | 0.010515657594426377 | 0.027824232778623205 | 0.01508064727846509 |
| take_profit | 0.3148 | 0.005010168219637247 | 0.011229339883773082 | 0.006998463078537899 |
| executor_refresh_time | 0.3148 | 2383.0 | 11423.0 | 8431.5 |
| cooldown_time | 0.5910 | 170.0 | 6911.0 | 4224.8 |
| total_amount_quote | 0.2179 | 440.2916068832143 | 988.2408459015961 | 810.9917248160411 |

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
| recent_objective | > 0 | -0.03808296037552707 | FAIL |
| recent_pnl | >= 0 | -0.23653650199271797 | FAIL |
| recent_trades | >= 5 | 123 | PASS |
| worst_stress | > -10 | -0.15367885755529348 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.003969946404047284 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.15367885755529348 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | FAIL | score=-0.03808296037552707, pnl=-0.23653650199271797, trades=123, reason=recent objective score -0.0381 <= 0; recent PnL -0.2365% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.04624244774639692, pnl=-0.10406857236325646, trades=66, reason=recent objective score -0.0462 <= 0; recent PnL -0.1041% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.15682054133447965, pnl=-0.04084369395895524, trades=32, reason=recent objective score -0.1568 <= 0; recent PnL -0.0408% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.34250062691582894 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51871 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0381 <= 0; recent PnL -0.2365% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0462 <= 0; recent PnL -0.1041% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1568 <= 0; recent PnL -0.0408% < 0 |
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
- **run_timestamp**: 2026-04-09T05:41:18.944640+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 4727
