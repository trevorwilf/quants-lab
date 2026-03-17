# PMM Dynamic Optimization Report: nonkyc_BTC-USDT_5m_sweep_nonkyc_v2

Generated: 2026-03-17 06:35:16 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 56286
- **dataset_hash**: 338eeb950bc0b53870ec68b5ae96433a7641fae4b349a01c39b58aaf9ac1748d
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.6858957532827386 |
| buy_n_levels | 9 |
| buy_side_weight | 0.5670280330000257 |
| buy_spread_base | 5.804896374107554 |
| buy_spread_ratio | 1.8191933097715562 |
| cooldown_time | 5872.107444864935 |
| executor_refresh_time | 10017.642085055526 |
| macd_fast | 12 |
| macd_signal | 22 |
| macd_slow | 46 |
| natr_length | 40 |
| sell_n_levels | 2 |
| sell_spread_base | 2.8020365580596436 |
| sell_spread_ratio | 1.6710025729382119 |
| stop_loss | 0.1725304594667152 |
| take_profit | 0.023223156984013626 |
| time_limit | 170250 |
| total_amount_quote | 990.9345203855235 |
| trailing_stop_activation | 0.037793294627287796 |
| trailing_stop_delta | 0.001290547779282734 |

## Best Metrics

- **PnL %**: 98.9412
- **Net PnL (quote)**: 980.4429
- **Sharpe Ratio**: 1.3614
- **Max Drawdown %**: 2.2970
- **Profit Factor**: 6.118928478596054
- **Trade Count**: 486
- **Total Fees (quote)**: 45.5983
- **Maker Fees**: 26.6203
- **Taker Fees**: 18.9779
- **Fee Drag %**: 4.6015

## Objective Decomposition

- **Raw Score**: 97.8571
- **PnL Component**: 98.9412
- **Sharpe Component**: 0.6807
- **Drawdown Component**: -0.6891
- **Fee Drag Component**: -0.9203
- **Inventory Component**: -0.1499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.6432**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.02 | 0.69 | 0.17 | 26 | -0.2264 | n/a |
| 1 | 94.38 | 5.12 | 0.07 | 33 | 96.4096 | n/a |
| 2 | -0.22 | -3.91 | 0.42 | 32 | -1.7890 | n/a |
| 3 | -0.01 | -0.51 | 0.12 | 24 | -0.8744 | n/a |
| 4 | 0.08 | 2.32 | 0.13 | 30 | 0.7110 | n/a |
| 5 | -0.00 | -0.08 | 0.04 | 24 | -0.6114 | n/a |
| 6 | 0.00 | 0.08 | 0.09 | 33 | -0.3836 | n/a |
| 7 | -0.03 | -0.22 | 0.58 | 43 | -0.6915 | n/a |
| 8 | 0.12 | 1.82 | 0.45 | 44 | 0.6492 | n/a |
| 9 | 0.12 | 1.73 | 0.27 | 35 | 0.4785 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: 92.0157)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 96.64 | 1.34 | 2.74 | 94.9533 |
| fees_2x | 94.34 | 1.33 | 3.30 | 92.0157 |
| latency_plus1 | 97.93 | 1.36 | 2.30 | 96.9179 |
| latency_plus2 | 98.29 | 1.36 | 2.42 | 97.1481 |
| latency_plus3 | 98.08 | 1.36 | 2.43 | 96.9633 |
| low_liquidity | 99.93 | 1.35 | 2.85 | 98.5118 |
| very_low_liquidity | 99.82 | 1.35 | 2.93 | 98.3669 |
| high_slippage | 98.46 | 1.36 | 2.36 | 97.3580 |
| extreme_slippage | 97.50 | 1.35 | 2.52 | 96.3456 |
| combined_adverse | 95.36 | 1.34 | 2.88 | 93.7374 |

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: **FAIL**

> **WARNING**: One or more stop-ship checks FAILED.
