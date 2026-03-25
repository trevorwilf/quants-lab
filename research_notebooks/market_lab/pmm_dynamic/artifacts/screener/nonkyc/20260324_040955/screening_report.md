# NONKYC Public Screener Report

Generated: 2026-03-24T04:11:51Z

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
- Selected: 6
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
| BTC-USDT       |        82.1451 |        1.64467e+07 |      72.8134 |          13563.1    |                  0      |              303908     |                344494      |         26.1508 |
| SOL-USDT       |        76.5451 |        3.08922e+06 |      75.0883 |            159.689  |                  0      |                1611.66  |                 84354.1    |         30.227  |
| NKYC-USDT      |        70.6176 |   164185           |      19.9195 |             26.8359 |                 26.8359 |                 214.755 |                    26.8359 |         19.6453 |
| ENA-USDT       |        67.9562 |   117255           |     119.112  |           1755.64   |                  0      |                   0     |                 12301.6    |         27.0478 |
| POL-USDT       |        65.9999 |    92922           |      73.2601 |            554.488  |                  0      |                 554.488 |                  1516.42   |         23.6537 |
| ARB-USDT       |        65.2702 |   116693           |      93.4094 |            182.522  |                  0      |                 182.522 |                  8797.04   |         28.3284 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
