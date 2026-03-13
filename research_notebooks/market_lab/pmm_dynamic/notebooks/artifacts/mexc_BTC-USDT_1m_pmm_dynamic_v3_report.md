# PMM Dynamic Optimization Report: mexc_BTC-USDT_1m_pmm_dynamic_v3

Generated: 2026-03-07 05:04:44 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BTC-USDT
- **interval**: 1m
- **n_candles**: 48885
- **dataset_hash**: 2b7e0ceee9978061dbdffa0c69349d9a905814410f04eee58d2ecfb177dddde0
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.6781071215712258 |
| buy_n_levels | 6 |
| buy_side_weight | 0.271682898373902 |
| buy_spread_base | 5.41654883336513 |
| buy_spread_ratio | 2.81517229926326 |
| cooldown_time | 987.7051760923193 |
| executor_refresh_time | 2527.3953982193825 |
| macd_fast | 9 |
| macd_signal | 16 |
| macd_slow | 59 |
| natr_length | 28 |
| sell_n_levels | 9 |
| sell_spread_base | 0.3898801956228725 |
| sell_spread_ratio | 2.4723676530214074 |
| stop_loss | 0.1350123813763261 |
| take_profit | 0.027959343622899244 |
| time_limit | 147121 |
| total_amount_quote | 645.0707258402645 |
| trailing_stop_activation | 0.018459095474939985 |
| trailing_stop_delta | 0.001680444629975627 |

## Best Metrics

- **PnL %**: 1.0911
- **Net PnL (quote)**: 7.0382
- **Sharpe Ratio**: 2.2955
- **Max Drawdown %**: 1.6125
- **Profit Factor**: 1.0649802708106506
- **Trade Count**: 800
- **Total Fees (quote)**: 2.9251
- **Maker Fees**: 1.4787
- **Taker Fees**: 1.4464
- **Fee Drag %**: 0.4535

## Objective Decomposition

- **Raw Score**: 1.5006
- **PnL Component**: 1.0911
- **Sharpe Component**: 1.1477
- **Drawdown Component**: -0.4838
- **Fee Drag Component**: -0.0907
- **Inventory Component**: -0.1598
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **2.5282**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 0.19 | 20.83 | 0.03 | 44 | 2.5425 |
| 1 | 0.48 | 15.45 | 0.20 | 106 | 2.8023 |
| 2 | 0.06 | 9.62 | 0.06 | 90 | 2.5093 |
| 3 | 0.18 | 5.75 | 0.18 | 99 | 2.5138 |
| 4 | 0.31 | 8.62 | 0.55 | 88 | 2.5568 |

## Stress Test Results

Worst Scenario: **extreme_slippage** (score: -2.0556)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 0.87 | 1.83 | 1.68 | 0.9734 |
| fees_2x | 0.64 | 1.36 | 1.75 | 0.4461 |
| latency_plus1 | 0.71 | 1.44 | 1.69 | 0.6508 |
| latency_plus2 | 0.70 | 1.38 | 1.77 | 0.5829 |
| latency_plus3 | 1.24 | 2.56 | 1.68 | 1.7506 |
| low_liquidity | 1.09 | 2.30 | 1.61 | 1.5006 |
| very_low_liquidity | 1.09 | 2.30 | 1.61 | 1.5006 |
| high_slippage | 0.53 | 1.14 | 1.78 | 0.3135 |
| extreme_slippage | -0.58 | -1.17 | 2.13 | -2.0556 |
| combined_adverse | -0.07 | -0.10 | 1.92 | -1.0106 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: **FAIL**
- yaml_validates: PASS
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
