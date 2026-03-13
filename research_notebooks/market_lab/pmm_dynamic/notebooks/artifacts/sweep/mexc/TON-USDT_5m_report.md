# PMM Dynamic Optimization Report: mexc_TON-USDT_5m_sweep_mexc_v2

Generated: 2026-03-09 10:52:01 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: TON-USDT
- **interval**: 5m
- **n_candles**: 52051
- **dataset_hash**: e421232cd21a05a7207f4f841bf41cf00fe3be4cb707a9b1811db8587a61e5c3
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.1815927804340132 |
| buy_n_levels | 2 |
| buy_side_weight | 0.5149634040817561 |
| buy_spread_base | 0.5397090239576179 |
| buy_spread_ratio | 1.5161492122092068 |
| cooldown_time | 206.3884546200436 |
| executor_refresh_time | 987.0884074172759 |
| macd_fast | 43 |
| macd_signal | 20 |
| macd_slow | 96 |
| natr_length | 22 |
| sell_n_levels | 5 |
| sell_spread_base | 0.9358541804337777 |
| sell_spread_ratio | 1.7898913122623088 |
| stop_loss | 0.19096129712918566 |
| take_profit | 0.0858907626889277 |
| time_limit | 166203 |
| total_amount_quote | 57.01318228091297 |
| trailing_stop_activation | 0.017123240688776364 |
| trailing_stop_delta | 0.0011267706913253468 |

## Best Metrics

- **PnL %**: 900.3865
- **Net PnL (quote)**: 513.3390
- **Sharpe Ratio**: 8.0231
- **Max Drawdown %**: 16.7357
- **Profit Factor**: 1.2294293500913254
- **Trade Count**: 18800
- **Total Fees (quote)**: 57.4013
- **Maker Fees**: 30.4153
- **Taker Fees**: 26.9860
- **Fee Drag %**: 100.6808

## Objective Decomposition

- **Raw Score**: 873.2204
- **PnL Component**: 900.3865
- **Sharpe Component**: 2.5000
- **Drawdown Component**: -5.0207
- **Fee Drag Component**: -20.1362
- **Inventory Component**: -4.3998
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **70.5185**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 99.61 | 26.39 | 8.46 | 1163 | 93.8240 |
| 1 | 87.64 | 21.36 | 6.93 | 1156 | 81.4723 |
| 2 | 122.90 | 28.27 | 7.48 | 1191 | 117.5802 |
| 3 | 86.66 | 30.75 | 4.55 | 1144 | 82.9988 |
| 4 | 62.36 | 27.50 | 3.25 | 1038 | 59.5647 |
| 5 | 70.42 | 27.31 | 5.84 | 1200 | 65.7363 |
| 6 | 55.73 | 22.70 | 8.21 | 1204 | 50.9020 |
| 7 | 123.14 | 24.92 | 15.30 | 1126 | 115.9477 |
| 8 | 50.16 | 19.54 | 3.50 | 1157 | 46.8992 |

## Stress Test Results

Worst Scenario: **latency_plus3** (score: 503.9053)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 871.03 | 8.08 | 16.74 | 833.8971 |
| fees_2x | 829.64 | 7.74 | 16.51 | 782.7868 |
| latency_plus1 | 824.04 | 7.21 | 17.45 | 797.8570 |
| latency_plus2 | 708.72 | 5.03 | 17.42 | 684.4793 |
| latency_plus3 | 525.31 | 5.79 | 18.19 | 503.9053 |
| low_liquidity | 900.62 | 8.02 | 16.74 | 873.4513 |
| very_low_liquidity | 900.98 | 8.03 | 16.74 | 873.8005 |
| high_slippage | 825.46 | 7.64 | 16.77 | 798.4745 |
| extreme_slippage | 689.00 | 6.34 | 16.70 | 662.5644 |
| combined_adverse | 738.59 | 5.81 | 17.47 | 703.2259 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
