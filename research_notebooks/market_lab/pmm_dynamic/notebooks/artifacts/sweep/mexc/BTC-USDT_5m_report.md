# PMM Dynamic Optimization Report: mexc_BTC-USDT_5m_sweep_mexc_v2

Generated: 2026-03-09 05:02:24 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 53616
- **dataset_hash**: 3ef73f56914fe6bc08a192c1b14e09e4f0e4caf356e34fa8e5e116ca185239e0
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.8048273282922183 |
| buy_n_levels | 8 |
| buy_side_weight | 0.7165670385384207 |
| buy_spread_base | 5.009918648830945 |
| buy_spread_ratio | 2.525620673579426 |
| cooldown_time | 2326.045400883134 |
| executor_refresh_time | 6350.5812437228415 |
| macd_fast | 40 |
| macd_signal | 28 |
| macd_slow | 85 |
| natr_length | 33 |
| sell_n_levels | 3 |
| sell_spread_base | 0.5494242688693719 |
| sell_spread_ratio | 1.7328935116214923 |
| stop_loss | 0.13436167981572847 |
| take_profit | 0.12975663794574682 |
| time_limit | 164132 |
| total_amount_quote | 347.885184113805 |
| trailing_stop_activation | 0.015495588895661461 |
| trailing_stop_delta | 0.001770460561183007 |

## Best Metrics

- **PnL %**: 6.3979
- **Net PnL (quote)**: 22.2575
- **Sharpe Ratio**: 1.8224
- **Max Drawdown %**: 3.0544
- **Profit Factor**: 1.4289643297840862
- **Trade Count**: 1249
- **Total Fees (quote)**: 6.6736
- **Maker Fees**: 3.3619
- **Taker Fees**: 3.3118
- **Fee Drag %**: 1.9183

## Objective Decomposition

- **Raw Score**: 5.7445
- **PnL Component**: 6.3979
- **Sharpe Component**: 0.9112
- **Drawdown Component**: -0.9163
- **Fee Drag Component**: -0.3837
- **Inventory Component**: -0.2536
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **2.2009**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 0.84 | 9.98 | 0.23 | 78 | 3.1941 |
| 1 | 0.37 | 4.06 | 0.51 | 72 | 2.1473 |
| 2 | 0.09 | 0.94 | 0.66 | 79 | 0.2544 |
| 3 | 0.85 | 10.57 | 0.29 | 61 | 3.1985 |
| 4 | 0.41 | 4.51 | 0.49 | 67 | 2.4264 |
| 5 | 0.22 | 8.31 | 0.07 | 72 | 2.6391 |
| 6 | 0.12 | 1.46 | 0.53 | 72 | 0.5706 |
| 7 | -0.06 | -0.20 | 1.03 | 105 | -0.7456 |
| 8 | 1.07 | 12.11 | 0.48 | 61 | 3.3660 |
| 9 | 0.65 | 4.68 | 0.51 | 82 | 2.6852 |

## Stress Test Results

Worst Scenario: **extreme_slippage** (score: -3.0856)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 5.44 | 1.55 | 3.29 | 4.3859 |
| fees_2x | 4.45 | 1.28 | 3.56 | 2.9848 |
| latency_plus1 | 4.80 | 1.34 | 3.44 | 3.7793 |
| latency_plus2 | 2.18 | 0.59 | 5.17 | 0.2140 |
| latency_plus3 | 3.30 | 1.02 | 4.20 | 1.9848 |
| low_liquidity | 6.40 | 1.82 | 3.05 | 5.7445 |
| very_low_liquidity | 6.40 | 1.82 | 3.05 | 5.7445 |
| high_slippage | 3.99 | 1.15 | 3.68 | 2.8055 |
| extreme_slippage | -0.77 | -0.18 | 5.23 | -3.0856 |
| combined_adverse | 1.44 | 0.43 | 4.33 | -0.5049 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
