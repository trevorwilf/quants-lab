# PMM Dynamic Optimization Report: mexc_BNB-USDT_5m_sweep_mexc_v2

Generated: 2026-03-09 04:15:56 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BNB-USDT
- **interval**: 5m
- **n_candles**: 52055
- **dataset_hash**: 46b73fbd6434c11929de9b25359eb5d0259f3909bf5beab2103604303398be17
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.5900587609350425 |
| buy_n_levels | 6 |
| buy_side_weight | 0.5580657491810783 |
| buy_spread_base | 5.231344635131261 |
| buy_spread_ratio | 2.1897728058795636 |
| cooldown_time | 6201.070126630017 |
| executor_refresh_time | 3422.6078808441125 |
| macd_fast | 22 |
| macd_signal | 16 |
| macd_slow | 51 |
| natr_length | 19 |
| sell_n_levels | 9 |
| sell_spread_base | 5.18648882362567 |
| sell_spread_ratio | 2.8271679704615127 |
| stop_loss | 0.09096392019468098 |
| take_profit | 0.08903515108738597 |
| time_limit | 27917 |
| total_amount_quote | 896.8074530152488 |
| trailing_stop_activation | 0.04840280589416272 |
| trailing_stop_delta | 0.04387151767543093 |

## Best Metrics

- **PnL %**: 5.4157
- **Net PnL (quote)**: 48.5683
- **Sharpe Ratio**: 0.8016
- **Max Drawdown %**: 3.4563
- **Profit Factor**: 1.8105191318398879
- **Trade Count**: 577
- **Total Fees (quote)**: 3.0047
- **Maker Fees**: 1.5029
- **Taker Fees**: 1.5018
- **Fee Drag %**: 0.3350

## Objective Decomposition

- **Raw Score**: 4.4758
- **PnL Component**: 5.4157
- **Sharpe Component**: 0.4008
- **Drawdown Component**: -1.0369
- **Fee Drag Component**: -0.0670
- **Inventory Component**: -0.2312
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.7107**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | -0.42 | -4.52 | 0.80 | 38 | -2.0715 |
| 1 | 0.20 | 3.76 | 0.21 | 34 | 1.5805 |
| 2 | -0.38 | -3.40 | 0.84 | 43 | -1.9668 |
| 3 | 0.15 | 4.74 | 0.09 | 36 | 2.1141 |
| 4 | 0.18 | 2.78 | 0.29 | 48 | 1.2445 |
| 5 | 0.10 | 5.59 | 0.05 | 30 | 2.0948 |
| 6 | 0.72 | 4.56 | 0.40 | 36 | 2.3120 |
| 7 | -1.08 | -7.44 | 1.42 | 50 | -2.7418 |
| 8 | -0.10 | -1.31 | 0.47 | 35 | -1.3213 |

## Stress Test Results

Worst Scenario: **extreme_slippage** (score: 3.1286)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 5.25 | 0.78 | 3.46 | 4.2611 |
| fees_2x | 5.08 | 0.76 | 3.47 | 4.0463 |
| latency_plus1 | 5.37 | 0.80 | 3.46 | 4.4309 |
| latency_plus2 | 5.38 | 0.80 | 3.46 | 4.4376 |
| latency_plus3 | 4.61 | 0.70 | 3.41 | 3.6333 |
| low_liquidity | 5.42 | 0.80 | 3.46 | 4.4758 |
| very_low_liquidity | 5.42 | 0.80 | 3.46 | 4.4758 |
| high_slippage | 5.00 | 0.75 | 3.47 | 4.0270 |
| extreme_slippage | 4.16 | 0.64 | 3.48 | 3.1286 |
| combined_adverse | 4.79 | 0.72 | 3.47 | 3.7699 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
