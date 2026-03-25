# MEXC Public Screener Report

Generated: 2026-03-24T01:32:06Z

## Objective

Shortlist markets for PMM Dynamic research and candle ingestion using public market-data endpoints only.

## Stop-Ship Notes

- This is an ingestion/research gate, not a live-trading approval.
- Passing markets still need post-ingestion audit, walk-forward validation, and live microstructure checks.
- Exchange rule fields are exported as estimates when the API does not expose exact tick/step filters.

## Counts

- Universe: 2018
- Shortlist: 100
- Enriched: 100
- Selected: 23

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
min_natr_bps: 10.0
min_quote_volume_24h: 1000000.0
min_recent_trade_count: 100
min_top_of_book_quote: 250.0
natr_soft_max: 250.0
natr_soft_min: 6.0
natr_target_max: 120.0
natr_target_min: 15.0
quote_asset: USDT
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
timeout_seconds: 30.0
universe_top_k: 100
user_agent: pmm-lab-screener/0.1
vol_to_spread_soft_max: 50.0
vol_to_spread_soft_min: 1.0
vol_to_spread_target_max: 20.0
vol_to_spread_target_min: 3.0
```

## Top Selected Pairs

| trading_pair   |   screen_score |   quote_volume_24h |   spread_bps |   sym_depth_quote_10bps |   natr_bps_mean |
|:---------------|---------------:|-------------------:|-------------:|------------------------:|----------------:|
| BTC-USDT       |        94.4147 |        1.05668e+09 |   0.00141145 |               424780    |         25.1568 |
| ETH-USDT       |        93.1487 |        8.99134e+08 |   0.0465837  |               131604    |         34.1377 |
| XRP-USDT       |        91.3717 |        1.15667e+08 |   0.703705   |               356349    |         31.4586 |
| DOGE-USDT      |        90.1751 |        3.99317e+07 |   1.06992    |               243790    |         30.9981 |
| SUI-USDT       |        85.5905 |        2.33313e+07 |   1.05792    |                92650.4  |         34.7117 |
| LTC-USDT       |        85.054  |        1.02246e+07 |   1.80554    |                64427.5  |         23.4284 |
| ADA-USDT       |        83.775  |        1.99754e+07 |   3.84394    |               106701    |         34.4656 |
| TRX-USDT       |        79.5557 |        1.08574e+07 |   3.23363    |               112217    |         14.2349 |
| WLD-USDT       |        73.9911 |        5.8519e+06  |   3.10704    |                 5594.82 |         42.8681 |
| WXT-USDT       |        71.876  |        2.01859e+06 |   1.8909     |                11550.2  |         22.977  |
| HYPE-USDT      |        71.4357 |        1.67779e+07 |   5.3234     |                 4795.69 |         44.5368 |
| XLM-USDT       |        69.12   |        5.44753e+06 |   6.05144    |                15023.6  |         35.4359 |
| ICP-USDT       |        65.2525 |        2.80813e+06 |   4.18498    |                 6487.49 |         32.8266 |
| ASTER-USDT     |        65.2023 |        2.93228e+06 |   6.05235    |                 8431.46 |         24.7991 |
| ZRO-USDT       |        65.176  |        2.18353e+06 |   4.54236    |                 2342.52 |         61.3988 |
| PUMP-USDT      |        63.8777 |        2.46611e+06 |   5.57569    |                 6897.62 |         43.799  |
| WLFI-USDT      |        63.244  |        5.65184e+06 |   9.68523    |                 2006.54 |         43.3777 |
| SHIB-USDT      |        62.684  |        4.88923e+06 |   6.62581    |                 1918.52 |         36.6603 |
| DOT-USDT       |        62.6466 |        6.17846e+06 |   7.05965    |                 1882.09 |         38.6001 |
| SAHARA-USDT    |        61.9433 |        2.11793e+06 |   3.82922    |                 1783.74 |         46.4086 |
| RENDER-USDT    |        60.458  |        1.14634e+06 |   5.85652    |                 6872.79 |         43.8488 |
| OP-USDT        |        60.164  |        2.26261e+06 |   8.91663    |                 2149.24 |         40.3527 |
| ATOM-USDT      |        56.9686 |        1.66613e+06 |   5.58503    |                 4465.43 |         28.7749 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
