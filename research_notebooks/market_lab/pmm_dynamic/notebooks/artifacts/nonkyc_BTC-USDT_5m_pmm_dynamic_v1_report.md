# PMM Dynamic Optimization Report: nonkyc_BTC-USDT_5m_pmm_dynamic_v1

Generated: 2026-03-06 22:26:41 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 53341
- **dataset_hash**: b141925073e0838a7b4dcbfe6b01b712adfc28e32932208dee05d3e6e5d12e29

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.2611356733506898 |
| buy_n_levels | 5 |
| buy_side_weight | 0.29526073414560894 |
| buy_spread_base | 3.962919995365543 |
| buy_spread_ratio | 2.848514434466193 |
| cooldown_time | 1638.9204974633988 |
| executor_refresh_time | 490.6781901074263 |
| macd_fast | 30 |
| macd_signal | 28 |
| macd_slow | 65 |
| natr_length | 29 |
| sell_n_levels | 6 |
| sell_spread_base | 4.524512519580714 |
| sell_spread_ratio | 1.3420574029831618 |
| stop_loss | 0.016498840290474572 |
| take_profit | 0.017040973358564554 |
| time_limit | 71173 |
| total_amount_quote | 127.30130126686649 |
| trailing_stop_activation | 0.0028678326702579545 |
| trailing_stop_delta | 0.007646769113832752 |

## Best Metrics

- **PnL %**: -253.1854
- **Net PnL (quote)**: -253.1854
- **Sharpe Ratio**: 0.3825
- **Max Drawdown %**: 251.4798
- **Profit Factor**: 0.6332272905858728
- **Trade Count**: 5849
- **Total Fees (quote)**: 261.6883
- **Maker Fees**: 97.2900
- **Taker Fees**: 164.3983
- **Fee Drag %**: 261.6883

## Objective Decomposition

- **Raw Score**: -482.4595
- **PnL Component**: -253.1854
- **Sharpe Component**: 0.1912
- **Drawdown Component**: -75.4439
- **Fee Drag Component**: -52.3377
- **Inventory Component**: -101.6838
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-41.7319**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | -21.61 | -13.16 | 22.96 | 434 | -41.9461 |
| 1 | -28.92 | -10.07 | 29.27 | 446 | -54.1247 |
| 2 | -18.82 | -6.34 | 26.60 | 442 | -41.6161 |
| 3 | -20.80 | -10.57 | 22.23 | 443 | -40.2543 |
| 4 | -14.19 | -6.76 | 18.68 | 452 | -34.2531 |
| 5 | -18.07 | -14.07 | 19.58 | 456 | -37.3794 |
| 6 | -23.07 | -13.37 | 23.48 | 419 | -43.6024 |
| 7 | -12.22 | -5.34 | 16.74 | 433 | -28.5024 |
| 8 | -11.76 | -3.97 | 20.23 | 445 | -31.2467 |
| 9 | -19.16 | -7.87 | 25.90 | 447 | -40.0981 |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -798.9731)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -384.03 | -1.35 | 380.68 | -598.1775 |
| fees_2x | -514.87 | -2.03 | 510.34 | -798.9731 |
| latency_plus1 | -260.57 | 0.77 | 259.24 | -439.5703 |
| latency_plus2 | -265.66 | 0.17 | 264.13 | -498.8445 |
| latency_plus3 | -260.23 | 1.57 | 259.59 | -486.5536 |
| low_liquidity | -253.31 | -0.95 | 251.60 | -488.0945 |
| very_low_liquidity | -253.32 | -1.14 | 251.61 | -517.4009 |
| high_slippage | -286.73 | 1.47 | 284.42 | -465.3679 |
| extreme_slippage | -353.81 | 1.60 | 350.30 | -664.6850 |
| combined_adverse | -423.68 | 1.57 | 420.61 | -663.5218 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: **FAIL**
- yaml_validates: PASS
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
