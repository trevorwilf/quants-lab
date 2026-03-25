# MEXC Public Screener Report

Generated: 2026-03-25T23:56:34Z

## Objective

Shortlist markets for PMM Dynamic research and candle ingestion using public market-data endpoints only.

## Stop-Ship Notes

- This is an ingestion/research gate, not a live-trading approval.
- Passing markets still need post-ingestion audit, walk-forward validation, and live microstructure checks.
- Exchange rule fields are exported as estimates when the API does not expose exact tick/step filters.

## Counts

- Universe: 2413
- Shortlist: 100
- Enriched: 100
- Selected: 11
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
interval: 1m
interval_seconds: 60
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
universe_top_k: 100
user_agent: pmm-lab-screener/0.1
vol_to_spread_soft_max: 50.0
vol_to_spread_soft_min: 1.0
vol_to_spread_target_max: 20.0
vol_to_spread_target_min: 3.0
```

## Top Selected Pairs

| trading_pair   |   screen_score |   quote_volume_24h |   spread_bps |   top_of_book_quote |   sym_depth_quote_10bps |   sym_depth_quote_50bps |   sym_depth_quote_1xspread |   natr_bps_mean |
|:---------------|---------------:|-------------------:|-------------:|--------------------:|------------------------:|------------------------:|---------------------------:|----------------:|
| WLD-USDT       |        75.2087 |        4.33421e+06 |      3.07834 |            1262.51  |                14524    |               129853    |                   1262.51  |         13.0677 |
| XLM-USDT       |        67.6322 |        7.45893e+06 |      5.63539 |            2285.63  |                14469    |               228816    |                   2285.63  |         11.8307 |
| DOT-USDT       |        66.4102 |        5.94291e+06 |      7.33407 |            4136.62  |                 4136.62 |               102171    |                   4136.62  |         14.5459 |
| PEPE-USDT      |        64.0851 |        9.8756e+06  |      5.65451 |             425.512 |                 4497.28 |               228006    |                   2427.34  |         10.269  |
| PUMP-USDT      |        63.1238 |        2.72806e+06 |      5.24797 |             784.026 |                 9037.85 |               103199    |                    784.026 |         15.2775 |
| FET-USDT       |        62.2659 |        3.61231e+06 |      3.85134 |             621.015 |                 2910.06 |                14203.6  |                    621.015 |         31.3076 |
| JST-USDT       |        54.7554 |        1.35747e+06 |      1.66987 |             331.136 |                 1499.47 |                 5151.77 |                    331.136 |         10.3846 |
| RENDER-USDT    |        51.7654 |        1.09623e+06 |      5.37779 |             705.398 |                 7327.35 |                50232.2  |                    705.398 |         12.9126 |
| CRV-USDT       |        49.7521 |        1.11854e+06 |      4.25622 |             356.127 |                 1317.89 |                27105.5  |                    356.127 |         11.1501 |
| OP-USDT        |        47.048  |        1.18564e+06 |      8.81446 |            4611.67  |                 4611.67 |                66218.3  |                   4611.67  |         13.497  |
| ETC-USDT       |        46.7104 |        1.78171e+06 |     11.5274  |            2933.85  |                 2933.85 |                91765.9  |                   2933.85  |         14.2337 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
