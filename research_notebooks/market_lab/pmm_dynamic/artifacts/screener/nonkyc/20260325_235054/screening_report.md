# NONKYC Public Screener Report

Generated: 2026-03-25T23:52:57Z

## Objective

Shortlist markets for PMM Dynamic research and candle ingestion using public market-data endpoints only.

## Stop-Ship Notes

- This is an ingestion/research gate, not a live-trading approval.
- Passing markets still need post-ingestion audit, walk-forward validation, and live microstructure checks.
- Exchange rule fields are exported as estimates when the API does not expose exact tick/step filters.

## Counts

- Universe: 345
- Shortlist: 80
- Enriched: 80
- Selected: 10
- Selection mode: strict

## Configuration

```yaml
candle_limit: 288
connector: nonkyc
depth_limit: 200
efficiency_soft_max: 0.8
efficiency_soft_min: 0.0
efficiency_target_max: 0.45
efficiency_target_min: 0.05
exclude_regex:
- (?:^|[^A-Z])(3L|3S|5L|5S)$
- (?:UP|DOWN|BULL|BEAR)$
exclude_symbols: []
fallback_if_empty: true
final_top_n: 15
include_symbols: []
interval: 5m
interval_seconds: 300
max_last_trade_age_sec: 3600.0
max_natr_bps: 400.0
max_retries: 3
max_spread_bps: 120.0
max_zero_volume_fraction: 0.3
min_candle_count: 220
min_candle_coverage_ratio: 0.9
min_depth_10bps_quote: 0.0
min_depth_1xspread_quote: 0.0
min_depth_50bps_quote: 0.0
min_natr_bps: 12.0
min_quote_volume_24h: 50000.0
min_recent_trade_count: 40
min_top_of_book_quote: 5.0
natr_soft_max: 350.0
natr_soft_min: 8.0
natr_target_max: 180.0
natr_target_min: 20.0
quote_asset: '*'
recent_trade_limit: 500
request_pause_sec: 0.2
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
universe_top_k: 80
user_agent: pmm-lab-screener/0.1
vol_to_spread_soft_max: 60.0
vol_to_spread_soft_min: 1.0
vol_to_spread_target_max: 25.0
vol_to_spread_target_min: 3.0
```

## Top Selected Pairs

| trading_pair   |   screen_score |   quote_volume_24h |   spread_bps |   top_of_book_quote |   sym_depth_quote_10bps |   sym_depth_quote_50bps |   sym_depth_quote_1xspread |   natr_bps_mean |
|:---------------|---------------:|-------------------:|-------------:|--------------------:|------------------------:|------------------------:|---------------------------:|----------------:|
| USDC-USDT      |        82.1727 |        1.68375e+06 |      51.9948 |           472.974   |                  0      |            730399       |               750705       |         15.0334 |
| SOL-USDT       |        78.2614 |        2.02664e+06 |      61.2089 |          1596.8     |                  0      |              1596.8     |                 1808.4     |         27.132  |
| UNI-USDT       |        74.1667 |   363201           |      78.3466 |          2204.44    |                  0      |              5710.68    |                33052.9     |         26.9368 |
| LTC-USDT       |        72.0221 |   815333           |      40.8489 |            28.2382  |                  0      |                28.2382  |                   28.2382  |         22.6155 |
| AVAX-USDT      |        71.2213 |   511044           |      82.7301 |           258.772   |                  0      |               258.772   |                18068.4     |         23.2034 |
| AAVE-USDT      |        70.9534 |   100127           |      65.7369 |           369.314   |                  0      |              6205.6     |                 9780.65    |         26.031  |
| RENDER-USDT    |        69.4692 |   112697           |      75.4717 |           887.04    |                  0      |              1681.18    |                 5172.9     |         40.6513 |
| NKYC-USDT      |        69.2798 |   168514           |      10.5143 |            36.8642  |                 36.8642 |               193.264   |                   36.8642  |         13.8218 |
| PEPE-USDT      |        67.8953 |   119686           |      56.6572 |           119.553   |                  0      |               119.553   |                  119.553   |         13.0464 |
| BCH-USDT       |        64.723  |   132840           |      65.3526 |             5.66414 |                  0      |                 5.83904 |                    5.83904 |         27.2525 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
