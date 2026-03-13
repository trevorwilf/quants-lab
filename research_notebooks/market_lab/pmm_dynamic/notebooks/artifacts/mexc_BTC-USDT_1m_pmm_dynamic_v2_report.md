# PMM Dynamic Optimization Report: mexc_BTC-USDT_1m_pmm_dynamic_v2

Generated: 2026-03-07 03:51:32 UTC

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
| amount_skew | 1.744997640959756 |
| buy_n_levels | 5 |
| buy_side_weight | 0.6082406829846517 |
| buy_spread_base | 69.1488537600362 |
| buy_spread_ratio | 1.303294072210773 |
| cooldown_time | 1485.0061080304627 |
| executor_refresh_time | 6795.626110418178 |
| macd_fast | 24 |
| macd_signal | 23 |
| macd_slow | 77 |
| natr_length | 16 |
| sell_n_levels | 9 |
| sell_spread_base | 21.418239815278454 |
| sell_spread_ratio | 6.855871943051588 |
| stop_loss | 0.1528526745927689 |
| take_profit | 0.04261457358189829 |
| time_limit | 84416 |
| total_amount_quote | 582.2494257891109 |
| trailing_stop_activation | 0.02591199509270169 |
| trailing_stop_delta | 0.020332069439860677 |

## Best Metrics

- **PnL %**: 0.7057
- **Net PnL (quote)**: 4.1092
- **Sharpe Ratio**: 5.0381
- **Max Drawdown %**: 0.3016
- **Profit Factor**: 41.33151739818605
- **Trade Count**: 4
- **Total Fees (quote)**: 0.0475
- **Maker Fees**: 0.0226
- **Taker Fees**: 0.0249
- **Fee Drag %**: 0.0082

## Objective Decomposition

- **Raw Score**: 2.8785
- **PnL Component**: 0.7057
- **Sharpe Component**: 2.5000
- **Drawdown Component**: -0.0905
- **Fee Drag Component**: -0.0016
- **Inventory Component**: -0.0352
- **Trade Count Penalty**: -0.2000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **3.0577**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 |
| 4 | 1.39 | 14.97 | 0.57 | 4 | 3.0577 |

## Stress Test Results

Worst Scenario: **fees_2x** (score: 2.8586)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 0.70 | 5.01 | 0.30 | 2.8736 |
| fees_2x | 0.70 | 4.98 | 0.30 | 2.8586 |
| latency_plus1 | 0.71 | 5.04 | 0.30 | 2.8785 |
| latency_plus2 | 0.71 | 5.04 | 0.30 | 2.8785 |
| latency_plus3 | 0.71 | 5.04 | 0.30 | 2.8785 |
| low_liquidity | 0.71 | 5.04 | 0.30 | 2.8785 |
| very_low_liquidity | 0.71 | 5.04 | 0.30 | 2.8785 |
| high_slippage | 0.70 | 5.03 | 0.30 | 2.8770 |
| extreme_slippage | 0.70 | 5.01 | 0.30 | 2.8741 |
| combined_adverse | 0.70 | 5.00 | 0.30 | 2.8714 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: PASS
- determinism: PASS
