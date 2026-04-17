# PMM Dynamic Optimization Report: mexc_HYPE-USDT_5m_sweep_v1

Generated: 2026-04-09 04:46:34 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T04:46:34.321579+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 11997 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: HYPE-USDT
- **interval**: 5m
- **n_candles**: 51872
- **dataset_hash**: b5abd867ceffcc5a347fbf25aeff763223a83e29231f3fe52439725cf26cf8ed
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 437.2428702023989
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.739961533426624 |
| buy_n_levels | 8 |
| buy_side_weight | 0.7131297801052783 |
| buy_spread_base | 3.608195607375753 |
| buy_spread_ratio | 1.27577704651881 |
| cooldown_time | 227 |
| executor_refresh_time | 1964 |
| macd_fast | 38 |
| macd_signal | 27 |
| macd_slow | 43 |
| natr_length | 33 |
| sell_n_levels | 10 |
| sell_spread_base | 2.252410305227546 |
| sell_spread_ratio | 2.0870589578824723 |
| stop_loss | 0.20563647201400886 |
| take_profit | 0.009925767869351794 |
| time_limit | 131879 |
| total_amount_quote | 437.2428702023989 |
| trailing_stop_activation | 0.0021460183953709226 |
| trailing_stop_delta | 0.0013170411920051717 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 437.2428702023989 |
| Selected | 437.2428702023989 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 32.2871
- **Net PnL (quote)**: 141.1732
- **Sharpe Ratio**: 4.2352
- **Max Drawdown %**: 7.5681
- **Profit Factor**: 4.062557295526657
- **Trade Count**: 1539
- **Total Fees (quote)**: 15.1811
- **Maker Fees**: 7.5801
- **Taker Fees**: 7.6011
- **Fee Drag %**: 3.4720

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1531
- **PnL Component**: 0.2798
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0568
- **Fee Drag Component**: -0.0174
- **Inventory Component**: -0.0515
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.0059**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 4.68 | 14.11 | 0.16 | 57 | 0.0432 | n/a |
| 1 | 3.59 | 13.83 | 0.52 | 73 | 0.0291 | n/a |
| 2 | -1.21 | -7.35 | 1.40 | 51 | -0.0241 | n/a |
| 3 | 5.12 | 9.54 | 0.35 | 66 | 0.0452 | n/a |
| 4 | 0.54 | 1.23 | 2.00 | 69 | -0.0116 | n/a |
| 5 | 3.45 | 10.43 | 1.09 | 56 | 0.0243 | n/a |
| 6 | 1.58 | 6.16 | 0.99 | 75 | 0.0059 | n/a |
| 7 | 2.56 | 6.06 | 1.27 | 73 | 0.0136 | n/a |
| 8 | 0.67 | 2.92 | 0.56 | 61 | 0.0010 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0870)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 30.51 | 4.02 | 7.61 | 0.1304 |
| fees_2x | 28.74 | 3.81 | 7.66 | 0.1075 |
| latency_plus1 | 32.12 | 4.24 | 7.48 | 0.1524 |
| latency_plus2 | 29.20 | 3.92 | 7.51 | 0.1277 |
| latency_plus3 | 24.49 | 3.25 | 7.61 | 0.0908 |
| low_liquidity | 32.28 | 4.23 | 7.57 | 0.1530 |
| very_low_liquidity | 32.27 | 4.23 | 7.57 | 0.1530 |
| high_slippage | 27.85 | 3.70 | 7.66 | 0.1177 |
| extreme_slippage | 19.03 | 2.61 | 7.85 | 0.0425 |
| combined_adverse | 25.98 | 3.50 | 7.61 | 0.0937 |
| spread_widen_10bps | 30.89 | 3.79 | 8.56 | 0.1288 |
| spread_widen_25bps | 24.23 | 3.36 | 5.26 | 0.0974 |
| thin_book | 3.78 | 0.81 | 7.52 | -0.0703 |
| very_thin_book | 4.07 | 1.48 | 3.20 | 0.0005 |
| entry_spread_stress | 27.46 | 3.28 | 8.54 | 0.0705 |
| combined_market_deterioration | 9.10 | 1.34 | 9.64 | -0.0502 |
| severe_adverse | 1.57 | 0.39 | 5.73 | -0.0870 |

## Holdout Validation

- **Holdout bars**: 8765
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0043)
- **Trend**: ranging (efficiency: 0.0081)
- **Best holdout score**: 0.0208 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0330 | 0.0208 | 3.48 | 1.26 | 145 |
| 1 | 0.0244 | -0.1181 | 3.78 | 3.78 | 1762 |
| 2 | 0.0231 | -0.2499 | 8.23 | 10.83 | 671 |
| 3 | 0.0229 | -0.1799 | 16.57 | 9.51 | 2093 |
| 4 | 0.0204 | -0.1687 | 9.65 | 6.69 | 1934 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51872
- **Expected rows**: 51890
- **Missing rows**: 18
- **Forward-fill count**: 234
- **Forward-fill fraction**: 0.004511104256631709
- **Longest gap (seconds)**: 4500

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0052 <= 0
- **Objective score**: -0.005232801065642117
- **PnL %**: 0.7846297246149438
- **Trade count**: 152

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0205 <= 0; recent PnL -0.7177% < 0
- **Objective score**: -0.020536960912034836
- **PnL %**: -0.7177248434289665
- **Trade count**: 97

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0853 <= 0; recent PnL -0.6027% < 0
- **Objective score**: -0.08526730296870237
- **PnL %**: -0.6027401677094214
- **Trade count**: 33

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.02780109171882017
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.1830, 0.0493 |
| sell_spread_base | 0.1580, 0.1642 |
| stop_loss | 0.0323, 0.0270 |
| take_profit | 0.0278, 0.0278 |
| executor_refresh_time | 0.1042, 0.1534 |
| cooldown_time | 0.0278, 0.0278 |
| total_amount_quote | 0.0281, 0.0264 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.40935106149320555
- **Max CV**: 0.976642204030612
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss
- **Scattered params**: take_profit, executor_refresh_time, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2542 | 1.5349803434887477 | 3.2662800128289167 | 2.2670014736171176 |
| buy_spread_ratio | 0.1525 | 1.3100063485571756 | 2.0822491610097416 | 1.5251257210494482 |
| sell_spread_base | 0.4945 | 0.21870073077204225 | 0.871784678725624 | 0.39746491358416114 |
| sell_spread_ratio | 0.1743 | 1.585283950946648 | 2.702524117086186 | 2.151923169802939 |
| buy_side_weight | 0.1265 | 0.5501383100926731 | 0.7793793280959758 | 0.6830726562925111 |
| amount_skew | 0.0728 | 3.210872184694107 | 3.9426549899463543 | 3.6056398340985027 |
| stop_loss | 0.4630 | 0.04948253355538373 | 0.23536801212875055 | 0.10990429245280671 |
| take_profit | 0.5169 | 0.0051438100618610965 | 0.017954659270794985 | 0.008785384674775689 |
| executor_refresh_time | 0.9766 | 322.0 | 5982.0 | 1730.4 |
| cooldown_time | 0.6899 | 69.0 | 1291.0 | 573.7 |
| total_amount_quote | 0.5815 | 68.24312486989359 | 789.9531829244427 | 449.87953229742214 |

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
- holdout_passed: PASS
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
| recent_objective | > 0 | -0.005232801065642117 | FAIL |
| recent_pnl | >= 0 | 0.7846297246149438 | PASS |
| recent_trades | >= 5 | 152 | PASS |
| worst_stress | > -10 | -0.08702107558640321 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0208 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.08702107558640321 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.005232801065642117, pnl=0.7846297246149438, trades=152, reason=recent objective score -0.0052 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.020536960912034836, pnl=-0.7177248434289665, trades=97, reason=recent objective score -0.0205 <= 0; recent PnL -0.7177% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.08526730296870237, pnl=-0.6027401677094214, trades=33, reason=recent objective score -0.0853 <= 0; recent PnL -0.6027% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.40935106149320555 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51872 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0052 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0205 <= 0; recent PnL -0.7177% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0853 <= 0; recent PnL -0.6027% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51872
- **Pre-release bars**: 43825
- **Dev bars**: 35060
- **Holdout bars**: 8765
- **Recent 28d bars**: 8047
- **Recent window start**: 1773287100

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T04:46:34.321579+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 11997
