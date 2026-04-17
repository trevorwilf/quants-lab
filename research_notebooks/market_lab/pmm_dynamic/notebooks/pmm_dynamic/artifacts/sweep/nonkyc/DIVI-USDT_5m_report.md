# PMM Dynamic Optimization Report: nonkyc_DIVI-USDT_5m_sweep_v1

Generated: 2026-04-09 18:24:13 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T18:24:13.299237+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 5643 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: DIVI-USDT
- **interval**: 5m
- **n_candles**: 44968
- **dataset_hash**: 3e7c994eba0b925227d52f7fe021f50cb01af29b7b1a4f6906251892a00c12cf
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 590.163843791653
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.5648221224332155 |
| buy_n_levels | 5 |
| buy_side_weight | 0.5318698089688166 |
| buy_spread_base | 3.020923150338695 |
| buy_spread_ratio | 1.640314050363264 |
| cooldown_time | 6506 |
| executor_refresh_time | 2277 |
| macd_fast | 31 |
| macd_signal | 12 |
| macd_slow | 36 |
| natr_length | 40 |
| sell_n_levels | 5 |
| sell_spread_base | 0.48040792623563283 |
| sell_spread_ratio | 1.2489534381034653 |
| stop_loss | 0.1627580030119564 |
| take_profit | 0.034335992475013295 |
| time_limit | 85146 |
| total_amount_quote | 590.163843791653 |
| trailing_stop_activation | 0.007323763232736681 |
| trailing_stop_delta | 0.001355360379206248 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 590.163843791653 |
| Selected | 590.163843791653 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 17.9518
- **Net PnL (quote)**: 105.9448
- **Sharpe Ratio**: 1.6967
- **Max Drawdown %**: 10.8526
- **Profit Factor**: 1.6499223662715434
- **Trade Count**: 732
- **Total Fees (quote)**: 21.1211
- **Maker Fees**: 7.5140
- **Taker Fees**: 13.6071
- **Fee Drag %**: 3.5788

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0206
- **PnL Component**: 0.1651
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0814
- **Fee Drag Component**: -0.0179
- **Inventory Component**: -0.0443
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1108**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -9.05 | -14.27 | 9.59 | 61 | -0.2593 | n/a |
| 1 | -0.42 | -1.91 | 1.05 | 48 | -0.0214 | n/a |
| 2 | 2.35 | 2.81 | 3.02 | 86 | -0.0023 | n/a |
| 3 | 2.12 | 1.67 | 4.45 | 69 | -0.0175 | n/a |
| 4 | -0.35 | -6.26 | 0.35 | 10 | -0.3945 | n/a |
| 5 | -0.19 | -1.38 | 0.75 | 28 | -0.0964 | n/a |
| 6 | -0.32 | -0.61 | 1.83 | 90 | -0.0579 | n/a |
| 7 | -10.52 | -6.82 | 14.84 | 204 | -0.3599 | n/a |

## Stress Test Results

Worst Scenario: **combined_market_deterioration** (score: -0.1394)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 16.16 | 1.56 | 11.16 | -0.0063 |
| fees_2x | 14.37 | 1.41 | 11.48 | -0.0334 |
| latency_plus1 | 16.64 | 1.56 | 11.36 | 0.0013 |
| latency_plus2 | 14.09 | 1.39 | 11.88 | -0.0219 |
| latency_plus3 | 13.07 | 1.30 | 12.72 | -0.0381 |
| low_liquidity | 11.93 | 1.30 | 9.42 | -0.0373 |
| very_low_liquidity | 1.85 | 0.38 | 10.76 | -0.1245 |
| high_slippage | 17.38 | 1.65 | 10.95 | 0.0149 |
| extreme_slippage | 16.22 | 1.57 | 11.14 | 0.0034 |
| combined_adverse | 9.73 | 1.10 | 9.80 | -0.0691 |
| spread_widen_10bps | 9.07 | 0.98 | 12.18 | -0.0751 |
| spread_widen_25bps | 6.75 | 0.74 | 12.89 | -0.1087 |
| thin_book | 13.09 | 1.36 | 11.14 | -0.0380 |
| very_thin_book | -4.00 | -0.77 | 7.99 | -0.1371 |
| entry_spread_stress | 8.65 | 0.88 | 11.70 | -0.0812 |
| combined_market_deterioration | 6.34 | 0.72 | 13.95 | -0.1394 |
| severe_adverse | 0.82 | 0.24 | 9.92 | -0.1390 |

## Holdout Validation

- **Holdout bars**: 7381
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0060)
- **Trend**: ranging (efficiency: 0.0031)
- **Best holdout score**: 0.0063 (rank #1)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0594 | -0.0011 | 0.89 | 1.08 | 64 |
| 1 | 0.0252 | 0.0063 | 1.91 | 1.10 | 73 |
| 2 | 0.0235 | -0.0461 | 4.79 | 3.23 | 129 |
| 3 | 0.0183 | -0.0871 | 2.48 | 2.25 | 64 |
| 4 | 0.0141 | -0.1627 | 2.82 | 3.25 | 78 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 44968
- **Expected rows**: 44971
- **Missing rows**: 3
- **Forward-fill count**: 1406
- **Forward-fill fraction**: 0.0312666785269525
- **Longest gap (seconds)**: 900

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3602 <= 0; recent PnL -12.1711% < 0
- **Objective score**: -0.36017091962451575
- **PnL %**: -12.17110024025171
- **Trade count**: 278

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3248 <= 0; recent PnL -10.1042% < 0
- **Objective score**: -0.3247767650419524
- **PnL %**: -10.104157533063065
- **Trade count**: 211

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0682 <= 0; recent PnL -1.4666% < 0
- **Objective score**: -0.06824739817611791
- **PnL %**: -1.4666496747192685
- **Trade count**: 43

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: -0.1772076686442689
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1628, -0.2940 |
| sell_spread_base | -0.1822, -0.1939 |
| stop_loss | -0.1759, -0.4261 |
| take_profit | -0.1772, -0.1772 |
| executor_refresh_time | -0.2054, -0.1314 |
| cooldown_time | -0.2533, -0.1713 |
| total_amount_quote | -0.0816, -0.0761 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.33681178447038523
- **Max CV**: 1.1281323730815613
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1957 | 2.9922223458395565 | 5.770666783722954 | 4.559254935441979 |
| buy_spread_ratio | 0.0993 | 1.2036016542523804 | 1.6104012408912156 | 1.3592275456505618 |
| sell_spread_base | 0.7356 | 0.20576172344394322 | 1.5656413389354995 | 0.7035044170149437 |
| sell_spread_ratio | 0.1859 | 1.2588073199065657 | 2.1874012914374643 | 1.6812906159922705 |
| buy_side_weight | 0.1884 | 0.4475751600828681 | 0.7561051411059826 | 0.6167586316138643 |
| amount_skew | 0.1314 | 2.2873807091867118 | 3.800826867989148 | 3.253208847400341 |
| stop_loss | 0.2286 | 0.0775482702412103 | 0.21963272106223963 | 0.17218944761728944 |
| take_profit | 0.2534 | 0.0436869903612611 | 0.12710294116529902 | 0.09159346134063968 |
| executor_refresh_time | 1.1281 | 332.0 | 8204.0 | 2397.5 |
| cooldown_time | 0.3465 | 2213.0 | 7109.0 | 4905.7 |
| total_amount_quote | 0.2120 | 464.14273995035734 | 870.3394383083825 | 626.8323754654318 |

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
| recent_objective | > 0 | -0.36017091962451575 | FAIL |
| recent_pnl | >= 0 | -12.17110024025171 | FAIL |
| recent_trades | >= 5 | 278 | PASS |
| worst_stress | > -10 | -0.13944181238260095 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.0010747675761310714 |
| walkforward | PASS | 8 folds |
| stress | PASS | worst=combined_market_deterioration score=-0.13944181238260095 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.36017091962451575, pnl=-12.17110024025171, trades=278, reason=recent objective score -0.3602 <= 0; recent PnL -12.1711% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.3247767650419524, pnl=-10.104157533063065, trades=211, reason=recent objective score -0.3248 <= 0; recent PnL -10.1042% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.06824739817611791, pnl=-1.4666496747192685, trades=43, reason=recent objective score -0.0682 <= 0; recent PnL -1.4666% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.33681178447038523 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 44968 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3602 <= 0; recent PnL -12.1711% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3248 <= 0; recent PnL -10.1042% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0682 <= 0; recent PnL -1.4666% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 44968
- **Pre-release bars**: 36906
- **Dev bars**: 29525
- **Holdout bars**: 7381
- **Recent 28d bars**: 8062
- **Recent window start**: 1773337800

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T18:24:13.299237+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 5643
