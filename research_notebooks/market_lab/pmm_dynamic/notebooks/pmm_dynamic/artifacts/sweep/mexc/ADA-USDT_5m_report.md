# PMM Dynamic Optimization Report: mexc_ADA-USDT_5m_sweep_v1

Generated: 2026-04-09 00:28:46 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T00:28:46.493659+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 4831 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ADA-USDT
- **interval**: 5m
- **n_candles**: 51792
- **dataset_hash**: 95d5bf327f246a6e803127b2a837eaa18ef16d6f2ee0a7f2c45cbce9ab40670b
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 903.7017254136916
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.8871029528122043 |
| buy_n_levels | 9 |
| buy_side_weight | 0.6761908622148359 |
| buy_spread_base | 1.1562422786305762 |
| buy_spread_ratio | 1.814630901670465 |
| cooldown_time | 6571 |
| executor_refresh_time | 6021 |
| macd_fast | 24 |
| macd_signal | 5 |
| macd_slow | 26 |
| natr_length | 30 |
| sell_n_levels | 9 |
| sell_spread_base | 0.29793228541737365 |
| sell_spread_ratio | 1.3171259023187203 |
| stop_loss | 0.015517729455018024 |
| take_profit | 0.03347184766007595 |
| time_limit | 138549 |
| total_amount_quote | 903.7017254136916 |
| trailing_stop_activation | 0.00012018942168543433 |
| trailing_stop_delta | 0.001059315541647032 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 903.7017254136916 |
| Selected | 903.7017254136916 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3.7813
- **Net PnL (quote)**: 34.1714
- **Sharpe Ratio**: 4.9548
- **Max Drawdown %**: 0.3859
- **Profit Factor**: 2.2963619418994488
- **Trade Count**: 753
- **Total Fees (quote)**: 5.0770
- **Maker Fees**: 2.5346
- **Taker Fees**: 2.5424
- **Fee Drag %**: 0.5618

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0314
- **PnL Component**: 0.0371
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0029
- **Fee Drag Component**: -0.0028
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0007**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.27 | -6.06 | 0.41 | 68 | -0.0065 | n/a |
| 1 | 0.37 | 7.78 | 0.10 | 71 | 0.0027 | n/a |
| 2 | 0.29 | 8.36 | 0.01 | 64 | 0.0025 | n/a |
| 3 | 0.07 | 6.84 | 0.04 | 73 | 0.0002 | n/a |
| 4 | 1.11 | 5.59 | 0.22 | 72 | 0.0090 | n/a |
| 5 | 0.59 | 6.55 | 0.16 | 72 | 0.0044 | n/a |
| 6 | 0.14 | 5.63 | 0.08 | 62 | 0.0006 | n/a |
| 7 | 0.06 | 3.92 | 0.06 | 43 | -0.0461 | n/a |
| 8 | -0.06 | -2.24 | 0.17 | 53 | -0.0020 | n/a |

## Stress Test Results

Worst Scenario: **combined_market_deterioration** (score: -0.0804)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3.50 | 4.61 | 0.40 | 0.0272 |
| fees_2x | 3.22 | 4.26 | 0.42 | 0.0229 |
| latency_plus1 | 3.80 | 4.98 | 0.39 | 0.0316 |
| latency_plus2 | 3.70 | 4.79 | 0.38 | 0.0306 |
| latency_plus3 | 3.45 | 4.52 | 0.39 | 0.0282 |
| low_liquidity | 3.78 | 4.95 | 0.39 | 0.0314 |
| very_low_liquidity | 3.78 | 4.95 | 0.39 | 0.0314 |
| high_slippage | 3.08 | 4.08 | 0.43 | 0.0216 |
| extreme_slippage | 1.67 | 2.25 | 0.53 | -0.0161 |
| combined_adverse | 2.81 | 3.74 | 0.44 | 0.0123 |
| spread_widen_10bps | 3.15 | 4.15 | 0.45 | 0.0248 |
| spread_widen_25bps | 0.79 | 1.05 | 1.23 | -0.0106 |
| thin_book | -1.39 | -2.53 | 1.96 | -0.0390 |
| very_thin_book | -3.20 | -7.00 | 3.24 | -0.0584 |
| entry_spread_stress | 2.34 | 3.09 | 0.71 | 0.0111 |
| combined_market_deterioration | -2.60 | -5.15 | 2.84 | -0.0804 |
| severe_adverse | -3.63 | -10.37 | 3.63 | -0.0680 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0034)
- **Trend**: ranging (efficiency: 0.0000)
- **Best holdout score**: 0.0174 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0245 | 0.0015 | 0.25 | 0.08 | 114 |
| 1 | 0.0037 | 0.0018 | 0.51 | 0.35 | 131 |
| 2 | 0.0025 | 0.0088 | 1.27 | 0.30 | 230 |
| 3 | 0.0014 | 0.0174 | 2.19 | 0.35 | 160 |
| 4 | 0.0014 | 0.0015 | 0.25 | 0.08 | 114 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51792
- **Expected rows**: 51841
- **Missing rows**: 49
- **Forward-fill count**: 33
- **Forward-fill fraction**: 0.0006371640407784986
- **Longest gap (seconds)**: 15000

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0019 <= 0; recent PnL -0.0420% < 0
- **Objective score**: -0.0019382837430937138
- **PnL %**: -0.04198078929077354
- **Trade count**: 91

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0514 <= 0
- **Objective score**: -0.051405397682232186
- **PnL %**: 0.08221743774871058
- **Trade count**: 37

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1277 <= 0
- **Objective score**: -0.12771256184563012
- **PnL %**: 0.044455196063225254
- **Trade count**: 18

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.03146287480832359
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0231, 0.0199 |
| sell_spread_base | 0.0315, 0.0315 |
| stop_loss | 0.0288, 0.0298 |
| take_profit | 0.0315, 0.0315 |
| executor_refresh_time | 0.0220, 0.0230 |
| cooldown_time | 0.0252, 0.0291 |
| total_amount_quote | 0.0314, 0.0315 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4024817217754064
- **Max CV**: 1.3102668014207157
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2744 | 0.5442140919227456 | 1.2740686080716837 | 0.9680504023558256 |
| buy_spread_ratio | 0.2210 | 1.3876503065537211 | 2.8961278332513025 | 2.000775694078853 |
| sell_spread_base | 1.3103 | 0.20464087801336123 | 3.569109505092095 | 0.7700975448267988 |
| sell_spread_ratio | 0.1901 | 1.3171259023187203 | 2.799314166382277 | 2.315214024360042 |
| buy_side_weight | 0.2208 | 0.2810607730156222 | 0.7867828648369435 | 0.6685865153477248 |
| amount_skew | 0.2793 | 1.58256336557389 | 3.6456331324147175 | 2.25888652310826 |
| stop_loss | 0.5853 | 0.0124327572788816 | 0.0512341709064963 | 0.02233647695634181 |
| take_profit | 0.6924 | 0.00532135486543005 | 0.03347184766007595 | 0.013531126352928177 |
| executor_refresh_time | 0.2274 | 6021.0 | 13991.0 | 10619.1 |
| cooldown_time | 0.3197 | 1782.0 | 7046.0 | 5652.1 |
| total_amount_quote | 0.1068 | 680.4878664655138 | 960.8410370113749 | 860.7585917772449 |

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
| recent_objective | > 0 | -0.0019382837430937138 | FAIL |
| recent_pnl | >= 0 | -0.04198078929077354 | FAIL |
| recent_trades | >= 5 | 91 | PASS |
| worst_stress | > -10 | -0.0803887930791393 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0015 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=combined_market_deterioration score=-0.0803887930791393 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.0019382837430937138, pnl=-0.04198078929077354, trades=91, reason=recent objective score -0.0019 <= 0; recent PnL -0.0420% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.051405397682232186, pnl=0.08221743774871058, trades=37, reason=recent objective score -0.0514 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.12771256184563012, pnl=0.044455196063225254, trades=18, reason=recent objective score -0.1277 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4024817217754064 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51792 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0019 <= 0; recent PnL -0.0420% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0514 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1277 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51792
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8016
- **Recent window start**: 1773272700

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T00:28:46.493659+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 4831
