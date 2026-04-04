# NONKYC Public Screener Report

Generated: 2026-04-03T22:51:18Z

## Objective

Shortlist markets for PMM Dynamic research and candle ingestion using public market-data endpoints only.

## Stop-Ship Notes

- This is an ingestion/research gate, not a live-trading approval.
- Passing markets still need post-ingestion audit, walk-forward validation, and live microstructure checks.
- Exchange rule fields are exported as estimates when the API does not expose exact tick/step filters.

## Counts

- Universe: 343
- Shortlist: 343
- Enriched: 343
- Selected: 7
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
universe_top_k: 3000
user_agent: pmm-lab-screener/0.1
vol_to_spread_soft_max: 60.0
vol_to_spread_soft_min: 1.0
vol_to_spread_target_max: 25.0
vol_to_spread_target_min: 3.0
```

## Top Selected Pairs

| trading_pair   |   screen_score |   quote_volume_24h |   spread_bps |   top_of_book_quote |   sym_depth_quote_10bps |   sym_depth_quote_50bps |   sym_depth_quote_1xspread |   natr_bps_mean |
|:---------------|---------------:|-------------------:|-------------:|--------------------:|------------------------:|------------------------:|---------------------------:|----------------:|
| LTC-USDT       |        91.6069 |   326516           |      1.87248 |            10.68    |                 10.68   |                  24.12  |                    10.68   |         19.185  |
| SOL-USDT       |        88.7077 |   793626           |     79.7607  |           117.482   |                  0      |                 117.482 |                100716      |         31.8667 |
| BTC-USDT       |        87.8216 |        3.51211e+06 |     50.0611  |           177.449   |                  0      |              426207     |                426207      |         15.4013 |
| USDC-USDT      |        87.808  |        1.47467e+06 |     49.0025  |             6.16476 |                  0      |              725619     |                704877      |         16.8676 |
| NKYC-USDT      |        87.5975 |   149871           |     14.3718  |            43.7559  |                 43.7559 |                 241.269 |                    43.7559 |         17.6425 |
| ETH-USDT       |        87.2229 |        1.61758e+06 |     73.6668  |          5880.34    |                  0      |               73843     |                 90300.2    |         21.5181 |
| BNB-USDT       |        85.6453 |   580456           |     50.1748  |            12.8494  |                  0      |                  13.44  |                    13.44   |         18.3902 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
