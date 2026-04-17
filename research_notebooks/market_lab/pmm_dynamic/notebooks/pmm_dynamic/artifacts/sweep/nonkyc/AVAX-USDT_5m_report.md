# PMM Dynamic Optimization Report: nonkyc_AVAX-USDT_5m_sweep_v1

Generated: 2026-04-09 16:18:42 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T16:18:42.555094+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 4771 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: AVAX-USDT
- **interval**: 5m
- **n_candles**: 52002
- **dataset_hash**: e82871fb03fdfb9008c09a1d3a015c143c57d7560d8c27b5c3dc3f3788cdd206
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 951.9442594310352
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.8548277577950514 |
| buy_n_levels | 10 |
| buy_side_weight | 0.4361664889149661 |
| buy_spread_base | 2.9312108841610756 |
| buy_spread_ratio | 2.382023897984594 |
| cooldown_time | 4591 |
| executor_refresh_time | 13072 |
| macd_fast | 42 |
| macd_signal | 18 |
| macd_slow | 51 |
| natr_length | 41 |
| sell_n_levels | 7 |
| sell_spread_base | 5.09044021785415 |
| sell_spread_ratio | 1.803450749290863 |
| stop_loss | 0.01528496508198849 |
| take_profit | 0.005651201356669517 |
| time_limit | 160497 |
| total_amount_quote | 951.9442594310352 |
| trailing_stop_activation | 0.01411940958403917 |
| trailing_stop_delta | 0.028317324231706898 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 951.9442594310352 |
| Selected | 951.9442594310352 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -3.4578
- **Net PnL (quote)**: -32.9161
- **Sharpe Ratio**: -10.2728
- **Max Drawdown %**: 3.4978
- **Profit Factor**: 0.3409484311678615
- **Trade Count**: 865
- **Total Fees (quote)**: 17.6625
- **Maker Fees**: 12.4806
- **Taker Fees**: 5.1820
- **Fee Drag %**: 1.8554
- **TP Min-Notional Failures**: 4371 :warning:
  > 4371 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0764
- **PnL Component**: -0.0352
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0262
- **Fee Drag Component**: -0.0093
- **Inventory Component**: -0.0056
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0247**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.49 | -15.89 | 0.56 | 63 | -0.0157 | n/a |
| 1 | -0.56 | -15.63 | 0.59 | 62 | -0.0192 | n/a |
| 2 | -0.16 | -7.70 | 0.17 | 48 | -0.0546 | n/a |
| 3 | -0.21 | -6.46 | 0.26 | 54 | -0.0064 | n/a |
| 4 | -1.14 | -11.65 | 1.15 | 67 | -0.0268 | n/a |
| 5 | -0.23 | -6.94 | 0.26 | 74 | -0.0070 | n/a |
| 6 | -0.44 | -8.01 | 0.50 | 102 | -0.0188 | n/a |
| 7 | -0.22 | -7.77 | 0.28 | 65 | -0.0067 | n/a |
| 8 | -1.30 | -11.98 | 1.42 | 69 | -0.0919 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1263)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -4.39 | -12.74 | 4.42 | -0.0976 |
| fees_2x | -5.31 | -14.99 | 5.35 | -0.1190 |
| latency_plus1 | -3.46 | -10.28 | 3.50 | -0.0764 |
| latency_plus2 | -3.45 | -10.25 | 3.49 | -0.0761 |
| latency_plus3 | -3.47 | -10.24 | 3.51 | -0.0765 |
| low_liquidity | -4.27 | -8.11 | 4.35 | -0.0939 |
| very_low_liquidity | -4.03 | -7.88 | 4.09 | -0.0886 |
| high_slippage | -3.59 | -10.56 | 3.63 | -0.0788 |
| extreme_slippage | -3.87 | -11.11 | 3.91 | -0.0837 |
| combined_adverse | -5.45 | -10.12 | 5.50 | -0.1201 |
| spread_widen_10bps | -4.60 | -8.05 | 4.74 | -0.1007 |
| spread_widen_25bps | -4.59 | -10.94 | 4.61 | -0.0970 |
| thin_book | -4.65 | -8.13 | 4.70 | -0.0988 |
| very_thin_book | -4.03 | -7.45 | 4.05 | -0.0825 |
| entry_spread_stress | -4.83 | -10.14 | 4.90 | -0.1043 |
| combined_market_deterioration | -5.50 | -8.74 | 5.55 | -0.1203 |
| severe_adverse | -6.04 | -16.18 | 6.05 | -0.1263 |

## Holdout Validation

- **Holdout bars**: 8787
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0024)
- **Trend**: ranging (efficiency: 0.0049)
- **Best holdout score**: -0.0214 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1013 | -0.0214 | -0.72 | 0.77 | 183 |
| 1 | -0.0104 | -0.1363 | -5.29 | 5.38 | 613 |
| 2 | -0.0117 | -0.0308 | -1.05 | 1.08 | 262 |
| 3 | -0.0127 | -0.0344 | -1.18 | 1.20 | 392 |
| 4 | -0.0131 | -0.0597 | -2.37 | 2.46 | 421 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52002
- **Expected rows**: 52002
- **Missing rows**: 0
- **Forward-fill count**: 539
- **Forward-fill fraction**: 0.010364985962078382
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0990 <= 0; recent PnL -2.3598% < 0
- **Objective score**: -0.09896672816053059
- **PnL %**: -2.3598413357247443
- **Trade count**: 137

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0820 <= 0; recent PnL -1.0934% < 0
- **Objective score**: -0.08201403085169759
- **PnL %**: -1.0934474711128654
- **Trade count**: 70

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1246 <= 0; recent PnL -0.8574% < 0
- **Objective score**: -0.12462212383793639
- **PnL %**: -0.8573716801324082
- **Trade count**: 33

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.1612344086079747
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1271, -0.2212 |
| sell_spread_base | -0.1764, -0.2031 |
| stop_loss | -0.1684, -0.1691 |
| take_profit | -0.1726, -0.1810 |
| executor_refresh_time | -0.1741, -0.1377 |
| cooldown_time | -0.1564, -0.1530 |
| total_amount_quote | -0.1573, -0.5124 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.26500421526200396
- **Max CV**: 0.7606642487971847
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1919 | 2.012385557226063 | 4.123563204414653 | 3.025081528596327 |
| buy_spread_ratio | 0.1709 | 1.6076342501434568 | 2.7605710582725953 | 2.1228395634395127 |
| sell_spread_base | 0.6502 | 0.5013582913263506 | 4.240212468320507 | 2.1395193423585286 |
| sell_spread_ratio | 0.1853 | 1.3681430797792475 | 2.3634961284762195 | 1.7522767883915822 |
| buy_side_weight | 0.2695 | 0.2182857824162869 | 0.45236242784014924 | 0.30403904537623644 |
| amount_skew | 0.1711 | 1.9396884840909396 | 3.3631777693758855 | 2.647044753373414 |
| stop_loss | 0.7607 | 0.011365196440790464 | 0.05885040273042225 | 0.021762360880503005 |
| take_profit | 0.0488 | 0.005016122398419816 | 0.005887741236563554 | 0.005246741406757712 |
| executor_refresh_time | 0.2409 | 6705.0 | 13788.0 | 10773.6 |
| cooldown_time | 0.1111 | 5390.0 | 7138.0 | 6364.0 |
| total_amount_quote | 0.1147 | 616.0829942863538 | 961.7183334964495 | 906.981342572685 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
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
| recent_objective | > 0 | -0.09896672816053059 | FAIL |
| recent_pnl | >= 0 | -2.3598413357247443 | FAIL |
| recent_trades | >= 5 | 137 | PASS |
| worst_stress | > -10 | -0.12632869202642472 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.021354571922121948 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.12632869202642472 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.09896672816053059, pnl=-2.3598413357247443, trades=137, reason=recent objective score -0.0990 <= 0; recent PnL -2.3598% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.08201403085169759, pnl=-1.0934474711128654, trades=70, reason=recent objective score -0.0820 <= 0; recent PnL -1.0934% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.12462212383793639, pnl=-0.8573716801324082, trades=33, reason=recent objective score -0.1246 <= 0; recent PnL -0.8574% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.26500421526200396 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52002 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0990 <= 0; recent PnL -2.3598% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0820 <= 0; recent PnL -1.0934% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1246 <= 0; recent PnL -0.8574% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52002
- **Pre-release bars**: 43937
- **Dev bars**: 35150
- **Holdout bars**: 8787
- **Recent 28d bars**: 8065
- **Recent window start**: 1773321300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T16:18:42.555094+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 4771
