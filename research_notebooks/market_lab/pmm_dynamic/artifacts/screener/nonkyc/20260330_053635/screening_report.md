# NONKYC Public Screener Report

Generated: 2026-03-30T05:44:58Z

## Objective

Shortlist markets for PMM Dynamic research and candle ingestion using public market-data endpoints only.

## Stop-Ship Notes

- This is an ingestion/research gate, not a live-trading approval.
- Passing markets still need post-ingestion audit, walk-forward validation, and live microstructure checks.
- Exchange rule fields are exported as estimates when the API does not expose exact tick/step filters.

## Counts

- Universe: 345
- Shortlist: 345
- Enriched: 345
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
| NKYC-USDT      |        89.8104 |   159244           |      13.2619 |            97.2886  |                97.2886  |               272.998   |                   97.2886  |         24.149  |
| TRX-USDT       |        89.244  |   424003           |      68.2382 |          1070.46    |                 0       |             29366.1     |                96390       |         20.8098 |
| SOL-USDT       |        88.7887 |        1.4643e+06  |      70.2841 |            98.5608  |                 0       |              1135.13    |                33585.1     |         26.6425 |
| BNB-USDT       |        87.801  |        1.16531e+06 |      34.9568 |           137.764   |                 0       |               138.381   |                  138.381   |         20.7908 |
| LTC-USDT       |        87.3515 |   539515           |      16.5609 |             6.82008 |                 6.82008 |                 6.82008 |                    6.82008 |         18.6635 |
| USDC-USDT      |        87.0108 |        1.09537e+06 |      44.9798 |            75.4431  |                 0       |            642736       |               478439       |         14.6969 |
| AAVE-USDT      |        82.7853 |    56313.8         |      64.2104 |           390.418   |                 0       |              5224.03    |                 9816.41    |         24.6298 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
