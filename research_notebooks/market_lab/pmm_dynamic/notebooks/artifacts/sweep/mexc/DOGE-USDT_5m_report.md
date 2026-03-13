# PMM Dynamic Optimization Report: mexc_DOGE-USDT_5m_sweep_mexc_v2

Generated: 2026-03-09 06:04:08 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOGE-USDT
- **interval**: 5m
- **n_candles**: 53614
- **dataset_hash**: 61753d0d6ea0192ba817fde077321035f12487084d760bbf1e54889f05d8bef2
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.899357749595608 |
| buy_n_levels | 3 |
| buy_side_weight | 0.5028958570659012 |
| buy_spread_base | 0.5245864944590333 |
| buy_spread_ratio | 1.720303951861298 |
| cooldown_time | 823.6982385160281 |
| executor_refresh_time | 1987.102210119444 |
| macd_fast | 22 |
| macd_signal | 18 |
| macd_slow | 75 |
| natr_length | 23 |
| sell_n_levels | 3 |
| sell_spread_base | 1.323431740538668 |
| sell_spread_ratio | 1.2380108401596965 |
| stop_loss | 0.19839511854177744 |
| take_profit | 0.14811385446210756 |
| time_limit | 167300 |
| total_amount_quote | 187.1809810475968 |
| trailing_stop_activation | 0.028324457850353035 |
| trailing_stop_delta | 0.0010990995529943366 |

## Best Metrics

- **PnL %**: 769.2869
- **Net PnL (quote)**: 1439.9588
- **Sharpe Ratio**: 7.1212
- **Max Drawdown %**: 24.3441
- **Profit Factor**: 1.021879641664145
- **Trade Count**: 10594
- **Total Fees (quote)**: 170.8772
- **Maker Fees**: 91.9107
- **Taker Fees**: 78.9665
- **Fee Drag %**: 91.2898

## Objective Decomposition

- **Raw Score**: 740.7354
- **PnL Component**: 769.2869
- **Sharpe Component**: 2.5000
- **Drawdown Component**: -7.3032
- **Fee Drag Component**: -18.2580
- **Inventory Component**: -5.3604
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **64.9566**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 82.73 | 21.39 | 7.65 | 658 | 75.1939 |
| 1 | 56.18 | 14.88 | 9.85 | 669 | 48.7065 |
| 2 | 82.76 | 19.09 | 9.17 | 694 | 76.1830 |
| 3 | 78.10 | 23.47 | 10.14 | 700 | 70.7635 |
| 4 | 99.72 | 17.18 | 6.98 | 710 | 93.0003 |
| 5 | 102.78 | 15.17 | 7.34 | 658 | 96.2517 |
| 6 | 55.89 | 16.11 | 12.71 | 640 | 47.3978 |
| 7 | 82.85 | 18.02 | 10.43 | 668 | 74.4989 |
| 8 | 31.13 | 9.11 | 11.60 | 656 | 23.5699 |
| 9 | 117.77 | 25.31 | 8.07 | 596 | 110.8782 |

## Stress Test Results

Worst Scenario: **latency_plus3** (score: 535.5443)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 735.96 | 7.00 | 24.10 | 698.5355 |
| fees_2x | 695.68 | 6.82 | 24.76 | 649.2424 |
| latency_plus1 | 659.43 | 6.69 | 24.76 | 631.5424 |
| latency_plus2 | 639.25 | 6.63 | 28.60 | 610.8977 |
| latency_plus3 | 562.53 | 6.19 | 29.37 | 535.5443 |
| low_liquidity | 769.29 | 7.12 | 24.34 | 740.7354 |
| very_low_liquidity | 769.29 | 7.12 | 24.34 | 740.7354 |
| high_slippage | 704.67 | 6.88 | 24.81 | 676.1082 |
| extreme_slippage | 581.16 | 6.30 | 25.47 | 552.7076 |
| combined_adverse | 605.61 | 6.43 | 26.37 | 568.6124 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
