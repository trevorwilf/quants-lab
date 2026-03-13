# PMM Dynamic Optimization Report: mexc_XMR-USDT_5m_sweep_mexc_v2

Generated: 2026-03-09 12:02:39 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 53672
- **dataset_hash**: 97c857e17619bcec9b184d877506f67906db30ba22368b48b57682ac8d2bb639
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.7007234989166617 |
| buy_n_levels | 3 |
| buy_side_weight | 0.5192463532200713 |
| buy_spread_base | 0.25747253079876586 |
| buy_spread_ratio | 1.5987366391163031 |
| cooldown_time | 341.7849222712134 |
| executor_refresh_time | 1559.7018418098796 |
| macd_fast | 27 |
| macd_signal | 29 |
| macd_slow | 80 |
| natr_length | 9 |
| sell_n_levels | 6 |
| sell_spread_base | 0.6516685804313838 |
| sell_spread_ratio | 1.2628373321701798 |
| stop_loss | 0.19365668801919939 |
| take_profit | 0.07831641645285256 |
| time_limit | 164356 |
| total_amount_quote | 149.26156457884147 |
| trailing_stop_activation | 0.04846204251340265 |
| trailing_stop_delta | 0.0013886904676032883 |

## Best Metrics

- **PnL %**: 1352.6244
- **Net PnL (quote)**: 2018.9483
- **Sharpe Ratio**: 7.7357
- **Max Drawdown %**: 31.5040
- **Profit Factor**: 1.0747626860115966
- **Trade Count**: 25644
- **Total Fees (quote)**: 224.4200
- **Maker Fees**: 116.8590
- **Taker Fees**: 107.5610
- **Fee Drag %**: 150.3535

## Objective Decomposition

- **Raw Score**: 1310.1721
- **PnL Component**: 1352.6244
- **Sharpe Component**: 2.5000
- **Drawdown Component**: -9.4512
- **Fee Drag Component**: -30.0707
- **Inventory Component**: -5.2743
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **97.5804**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 98.66 | 23.92 | 7.56 | 1567 | 90.9986 |
| 1 | 244.34 | 24.74 | 11.91 | 1761 | 235.2462 |
| 2 | 159.09 | 23.91 | 13.54 | 1745 | 150.1425 |
| 3 | 106.15 | 25.62 | 7.04 | 1714 | 99.0544 |
| 4 | 94.60 | 23.46 | 6.07 | 1693 | 87.7857 |
| 5 | 6.66 | 3.74 | 8.73 | 1688 | -1.4472 |
| 6 | 267.07 | 24.17 | 19.15 | 1745 | 256.1108 |
| 7 | 136.27 | 17.94 | 13.32 | 1705 | 127.2847 |
| 8 | 181.40 | 24.85 | 18.94 | 1634 | 170.4590 |
| 9 | 96.24 | 25.03 | 9.29 | 1857 | 88.6593 |

## Stress Test Results

Worst Scenario: **latency_plus3** (score: 842.0151)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 1253.58 | 7.31 | 31.31 | 1196.4539 |
| fees_2x | 1175.27 | 7.36 | 31.85 | 1103.6183 |
| latency_plus1 | 1232.17 | 7.54 | 30.63 | 1191.5673 |
| latency_plus2 | 1037.22 | 6.87 | 30.59 | 999.0883 |
| latency_plus3 | 876.79 | 6.49 | 27.99 | 842.0151 |
| low_liquidity | 1254.70 | 7.44 | 32.47 | 1212.1682 |
| very_low_liquidity | 1263.54 | 7.39 | 30.24 | 1222.3140 |
| high_slippage | 1154.07 | 7.29 | 30.48 | 1112.5705 |
| extreme_slippage | 1000.17 | 6.82 | 30.11 | 959.5849 |
| combined_adverse | 1076.70 | 6.94 | 26.09 | 1024.6916 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
