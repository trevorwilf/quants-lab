# PMM Dynamic Optimization Report: mexc_XRP-USDT_5m_sweep_mexc_v2

Generated: 2026-03-09 12:46:37 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XRP-USDT
- **interval**: 5m
- **n_candles**: 52039
- **dataset_hash**: 032c0a600f8caa27dbb533d130ff54fba7160a6bd2f96fb138c5348daa591e1a
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.7356984341574355 |
| buy_n_levels | 6 |
| buy_side_weight | 0.7081246679284026 |
| buy_spread_base | 5.494878932357278 |
| buy_spread_ratio | 2.5933968058111385 |
| cooldown_time | 1759.2035011773442 |
| executor_refresh_time | 2790.556523768051 |
| macd_fast | 29 |
| macd_signal | 21 |
| macd_slow | 91 |
| natr_length | 35 |
| sell_n_levels | 9 |
| sell_spread_base | 0.8432619491644332 |
| sell_spread_ratio | 1.4637673397142057 |
| stop_loss | 0.10861185425476265 |
| take_profit | 0.14778626600016176 |
| time_limit | 168529 |
| total_amount_quote | 616.1388827035574 |
| trailing_stop_activation | 0.01662485918895673 |
| trailing_stop_delta | 0.0036591218582291223 |

## Best Metrics

- **PnL %**: 12.3992
- **Net PnL (quote)**: 76.3963
- **Sharpe Ratio**: 1.3516
- **Max Drawdown %**: 3.2665
- **Profit Factor**: 1.8447351644180354
- **Trade Count**: 780
- **Total Fees (quote)**: 4.8576
- **Maker Fees**: 2.4353
- **Taker Fees**: 2.4223
- **Fee Drag %**: 0.7884

## Objective Decomposition

- **Raw Score**: 11.8825
- **PnL Component**: 12.3992
- **Sharpe Component**: 0.6758
- **Drawdown Component**: -0.9800
- **Fee Drag Component**: -0.1577
- **Inventory Component**: -0.0503
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **1.9399**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 0.14 | 6.17 | 0.04 | 22 | 2.0577 |
| 1 | 0.20 | 8.17 | 0.03 | 19 | 2.0653 |
| 2 | -0.00 | -0.06 | 0.24 | 32 | -0.4971 |
| 3 | 0.12 | 4.41 | 0.10 | 31 | 1.9016 |
| 4 | 0.07 | 5.09 | 0.03 | 24 | 2.0300 |
| 5 | 0.18 | 6.75 | 0.07 | 28 | 2.2103 |
| 6 | 0.82 | 6.17 | 0.08 | 21 | 2.7083 |
| 7 | 0.17 | 3.16 | 0.26 | 45 | 1.5356 |
| 8 | 0.03 | 1.53 | 0.09 | 11 | -0.0203 |

## Stress Test Results

Worst Scenario: **extreme_slippage** (score: 8.4376)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 12.00 | 1.31 | 3.27 | 11.3886 |
| fees_2x | 11.61 | 1.28 | 3.28 | 10.8947 |
| latency_plus1 | 11.45 | 1.26 | 3.27 | 10.8713 |
| latency_plus2 | 11.74 | 1.29 | 3.14 | 11.2272 |
| latency_plus3 | 11.70 | 1.31 | 2.77 | 11.3332 |
| low_liquidity | 12.40 | 1.35 | 3.27 | 11.8825 |
| very_low_liquidity | 12.40 | 1.35 | 3.27 | 11.8825 |
| high_slippage | 11.42 | 1.26 | 3.28 | 10.8474 |
| extreme_slippage | 9.45 | 1.06 | 4.44 | 8.4376 |
| combined_adverse | 10.01 | 1.12 | 4.13 | 9.0111 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
