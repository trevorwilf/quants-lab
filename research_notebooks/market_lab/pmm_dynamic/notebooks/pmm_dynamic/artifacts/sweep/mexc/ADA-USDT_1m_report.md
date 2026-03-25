# PMM Dynamic Optimization Report: mexc_ADA-USDT_1m_sweep_v1

Generated: 2026-03-25 23:16:53 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ADA-USDT
- **interval**: 1m
- **n_candles**: 45860
- **dataset_hash**: 79b35c7c459ee74c54759cd3e6ee7435b38f8e4ff69f57ee732fff66ab5974dc
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 651.8236744467301
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.0958002788105192 |
| buy_n_levels | 6 |
| buy_side_weight | 0.33107749747945514 |
| buy_spread_base | 0.30718186002475284 |
| buy_spread_ratio | 1.2611171347277308 |
| cooldown_time | 1043 |
| executor_refresh_time | 10805 |
| macd_fast | 14 |
| macd_signal | 15 |
| macd_slow | 66 |
| natr_length | 24 |
| sell_n_levels | 9 |
| sell_spread_base | 0.6023746730882366 |
| sell_spread_ratio | 1.4839294977342317 |
| stop_loss | 0.24131183419252877 |
| take_profit | 0.04845285607869934 |
| time_limit | 140427 |
| total_amount_quote | 651.8236744467301 |
| trailing_stop_activation | 0.05183036690129909 |
| trailing_stop_delta | 0.0014911028174549883 |

## Best Metrics

- **PnL %**: 24.7800
- **Net PnL (quote)**: 161.5220
- **Sharpe Ratio**: 5.6141
- **Max Drawdown %**: 10.5526
- **Profit Factor**: 1.281919076197897
- **Trade Count**: 322
- **Total Fees (quote)**: 9.5416
- **Maker Fees**: 5.7062
- **Taker Fees**: 3.8355
- **Fee Drag %**: 1.4638

## Objective Decomposition

- **Raw Score**: 19.4998
- **PnL Component**: 24.7800
- **Sharpe Component**: 2.5000
- **Drawdown Component**: -3.1658
- **Fee Drag Component**: -0.2928
- **Inventory Component**: -4.2781
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **3.8862**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 4.39 | 15.75 | 1.31 | 26 | 4.8624 | n/a |
| 1 | 6.66 | 13.14 | 2.79 | 39 | 4.9450 | n/a |
| 2 | 8.79 | 21.38 | 1.29 | 32 | 6.8149 | n/a |
| 3 | -5.64 | -11.16 | 8.32 | 28 | -14.5757 | n/a |
| 4 | 2.18 | 7.53 | 2.06 | 32 | 1.2798 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 8.9189)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 24.00 | 5.46 | 10.60 | 18.5514 |
| fees_2x | 23.24 | 5.31 | 10.65 | 17.6339 |
| latency_plus1 | 25.81 | 5.94 | 10.57 | 20.5642 |
| latency_plus2 | 23.65 | 5.10 | 8.65 | 18.0971 |
| latency_plus3 | 23.68 | 5.07 | 8.58 | 18.0742 |
| low_liquidity | 24.56 | 5.50 | 10.67 | 18.9593 |
| very_low_liquidity | 25.10 | 5.54 | 11.05 | 19.2989 |
| high_slippage | 23.25 | 5.32 | 10.70 | 17.9192 |
| extreme_slippage | 20.37 | 4.75 | 10.96 | 14.8204 |
| combined_adverse | 24.98 | 5.27 | 8.84 | 19.3524 |
| spread_widen_10bps | 23.14 | 5.28 | 10.63 | 17.8083 |
| spread_widen_25bps | 19.76 | 4.65 | 10.64 | 14.2165 |
| thin_book | 25.81 | 5.11 | 10.15 | 19.5304 |
| very_thin_book | 21.75 | 4.53 | 9.60 | 15.1153 |
| entry_spread_stress | 22.36 | 5.12 | 10.63 | 17.0222 |
| combined_market_deterioration | 18.55 | 4.09 | 9.09 | 12.3661 |
| severe_adverse | 16.18 | 3.47 | 10.82 | 8.9189 |

## Stop-Ship Checks

- dataset_audit: **FAIL**
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**

> **WARNING**: One or more stop-ship checks FAILED.
