# MEXC Public Screener Report

Generated: 2026-04-04T00:24:42Z

## Objective

Shortlist markets for PMM Dynamic research and candle ingestion using public market-data endpoints only.

## Stop-Ship Notes

- This is an ingestion/research gate, not a live-trading approval.
- Passing markets still need post-ingestion audit, walk-forward validation, and live microstructure checks.
- Exchange rule fields are exported as estimates when the API does not expose exact tick/step filters.

## Counts

- Universe: 2380
- Shortlist: 2344
- Enriched: 2344
- Selected: 16
- Selection mode: strict

## Configuration

```yaml
candle_limit: 288
connector: mexc
depth_limit: 200
efficiency_soft_max: 0.75
efficiency_soft_min: 0.0
efficiency_target_max: 0.4
efficiency_target_min: 0.05
exclude_regex:
- (?:^|[^A-Z])(3L|3S|5L|5S)$
- (?:UP|DOWN|BULL|BEAR)$
exclude_symbols: []
fallback_if_empty: false
final_top_n: 30
include_symbols: []
interval: 5m
interval_seconds: 300
max_last_trade_age_sec: 1800.0
max_natr_bps: 250.0
max_retries: 3
max_spread_bps: 50.0
max_zero_volume_fraction: 0.2
min_candle_count: 240
min_candle_coverage_ratio: 0.97
min_depth_10bps_quote: 1000.0
min_depth_1xspread_quote: 0.0
min_depth_50bps_quote: 0.0
min_natr_bps: 10.0
min_quote_volume_24h: 1000000.0
min_recent_trade_count: 100
min_top_of_book_quote: 250.0
natr_soft_max: 250.0
natr_soft_min: 6.0
natr_target_max: 120.0
natr_target_min: 15.0
quote_asset: '*'
recent_trade_limit: 500
request_pause_sec: 0.12
retry_backoff: 1.8
score_weights:
  activity: 0.12
  alpha: 0.1
  depth: 0.2
  quality: 0.1
  spread: 0.16
  top_of_book: 0.08
  volume: 0.24
selection_mode: strict
timeout_seconds: 30.0
universe_top_k: 3000
user_agent: pmm-lab-screener/0.1
vol_to_spread_soft_max: 50.0
vol_to_spread_soft_min: 1.0
vol_to_spread_target_max: 20.0
vol_to_spread_target_min: 3.0
```

## Top Selected Pairs

| trading_pair   |   screen_score |   quote_volume_24h |   spread_bps |   top_of_book_quote |   sym_depth_quote_10bps |   sym_depth_quote_50bps |   sym_depth_quote_1xspread |   natr_bps_mean |
|:---------------|---------------:|-------------------:|-------------:|--------------------:|------------------------:|------------------------:|---------------------------:|----------------:|
| SOL-USDT       |        99.3068 |        3.7454e+07  |   1.24448    |             405.657 |               477235    |             1.40114e+06 |                    405.657 |         20.2639 |
| LTC-USDT       |        98.2838 |        3.4682e+06  |   1.87882    |            1807.61  |                61044.8  |        364583           |                   1807.61  |         14.2244 |
| ADA-USDT       |        98.1281 |        6.02433e+06 |   4.06256    |            3086.84  |                40437.1  |        387434           |                   3086.84  |         24.913  |
| XRP-USDT       |        96.2587 |        2.5431e+07  |   0.758639   |             445.473 |               244450    |        601245           |                    445.473 |         15.8796 |
| WXT-USDT       |        95.9832 |        6.06348e+06 |   2.66973    |            1757.36  |                 7920.27 |         35155.2         |                   1757.36  |         12.5355 |
| SHIB-USDT      |        95.0054 |        1.69411e+06 |   5.00877    |             399.967 |                 1244.81 |        127383           |                    399.967 |         22.2957 |
| BNB-USDT       |        94.5698 |        9.34461e+06 |   0.169911   |            7592.64  |                93442    |        128339           |                   7592.64  |         11.9952 |
| PENGU-USDT     |        93.858  |        1.28856e+06 |   1.59122    |             459.954 |                 7637.01 |         19733           |                    459.954 |         26.4526 |
| UNI-USDT       |        93.5183 |        3.0243e+06  |   3.15706    |            1119.06  |                15165.7  |        100771           |                   1119.06  |         25.6522 |
| WLD-USDT       |        92.987  |        1.49699e+06 |   3.75587    |            2166.23  |                16001.8  |        121570           |                   2166.23  |         28.1488 |
| XLM-USDT       |        92.6894 |        1.1665e+06  |   6.13685    |            2600.35  |                12579.4  |        105715           |                   2600.35  |         23.3026 |
| TRUMP-USDT     |        92.3355 |        1.61313e+06 |   3.57974    |            1297.39  |                18691.9  |        144446           |                   1297.39  |         21.7555 |
| DOT-USDT       |        92.0599 |        1.20584e+06 |   8.08081    |            4694.89  |                 4694.89 |        124029           |                   4694.89  |         24.3468 |
| BTC-USDT       |        91.8781 |        2.12122e+08 |   0.00149397 |           38120.8   |               378730    |        737241           |                  38120.8   |         10.9786 |
| TON-USDT       |        91.8314 |        2.92932e+06 |   8.06127    |            9905.05  |                 9905.05 |        195013           |                   9905.05  |         21.3461 |
| ETH-USDC       |        91.1537 |        3.91161e+06 |   3.01916    |             398.819 |               137339    |        208781           |                    902.471 |         13.4271 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
