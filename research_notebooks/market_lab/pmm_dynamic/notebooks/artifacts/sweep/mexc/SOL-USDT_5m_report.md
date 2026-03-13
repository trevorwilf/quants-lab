# PMM Dynamic Optimization Report: mexc_SOL-USDT_5m_sweep_mexc_v2

Generated: 2026-03-09 09:55:10 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SOL-USDT
- **interval**: 5m
- **n_candles**: 53669
- **dataset_hash**: bed78f33321b584f61e9d943f0d3b93177a3adddc733ad25b2a1574908adaf87
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.6289756576766843 |
| buy_n_levels | 10 |
| buy_side_weight | 0.5261413976083937 |
| buy_spread_base | 0.8430489645971962 |
| buy_spread_ratio | 1.6045480946599249 |
| cooldown_time | 1651.9732840467555 |
| executor_refresh_time | 1661.6261617490572 |
| macd_fast | 32 |
| macd_signal | 24 |
| macd_slow | 45 |
| natr_length | 18 |
| sell_n_levels | 10 |
| sell_spread_base | 0.4568635896201377 |
| sell_spread_ratio | 1.9435522044345344 |
| stop_loss | 0.2487872891911428 |
| take_profit | 0.13481925609842887 |
| time_limit | 146874 |
| total_amount_quote | 149.7958626374804 |
| trailing_stop_activation | 0.027246737291406406 |
| trailing_stop_delta | 0.0012369605126629386 |

## Best Metrics

- **PnL %**: 543.7903
- **Net PnL (quote)**: 814.5753
- **Sharpe Ratio**: 6.8744
- **Max Drawdown %**: 32.4790
- **Profit Factor**: 1.056928012210736
- **Trade Count**: 9570
- **Total Fees (quote)**: 118.3006
- **Maker Fees**: 63.4938
- **Taker Fees**: 54.8068
- **Fee Drag %**: 78.9745

## Objective Decomposition

- **Raw Score**: 516.1809
- **PnL Component**: 543.7903
- **Sharpe Component**: 2.5000
- **Drawdown Component**: -9.7437
- **Fee Drag Component**: -15.7949
- **Inventory Component**: -4.4545
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **34.2105**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 85.20 | 28.29 | 6.57 | 704 | 80.1573 |
| 1 | 35.98 | 11.05 | 10.42 | 666 | 29.5507 |
| 2 | 64.06 | 17.44 | 8.47 | 649 | 58.9662 |
| 3 | 93.12 | 19.91 | 6.54 | 681 | 88.5694 |
| 4 | 77.76 | 18.40 | 3.63 | 718 | 73.6374 |
| 5 | 37.78 | 23.14 | 2.88 | 684 | 33.6022 |
| 6 | 30.52 | 15.67 | 6.41 | 667 | 25.3427 |
| 7 | 26.14 | 8.49 | 12.39 | 648 | 18.8824 |
| 8 | 41.71 | 11.00 | 18.99 | 656 | 33.2550 |
| 9 | 114.69 | 30.71 | 8.22 | 663 | 109.8937 |

## Stress Test Results

Worst Scenario: **latency_plus3** (score: 334.9282)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 531.58 | 6.76 | 33.40 | 495.9883 |
| fees_2x | 515.64 | 6.70 | 30.24 | 473.3585 |
| latency_plus1 | 503.19 | 6.56 | 33.37 | 476.1416 |
| latency_plus2 | 446.52 | 6.27 | 33.30 | 420.4630 |
| latency_plus3 | 360.45 | 5.59 | 35.15 | 334.9282 |
| low_liquidity | 543.79 | 6.87 | 32.48 | 516.1809 |
| very_low_liquidity | 543.79 | 6.87 | 32.48 | 516.1809 |
| high_slippage | 476.03 | 6.38 | 33.15 | 448.4767 |
| extreme_slippage | 392.44 | 5.80 | 31.12 | 365.8535 |
| combined_adverse | 431.18 | 6.05 | 34.58 | 396.8725 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
