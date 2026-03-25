# MEXC Public Screener Report

Generated: 2026-03-23T23:27:09Z

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
- Selected: 25

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

| trading_pair    |   screen_score |   quote_volume_24h |   spread_bps |   sym_depth_quote_10bps |   natr_bps_mean |
|:----------------|---------------:|-------------------:|-------------:|------------------------:|----------------:|
| BTC-USDT        |        94.3147 |        1.07212e+09 |   0.00141737 |               474389    |         25.6101 |
| SOL-USDT        |        92.186  |        1.52962e+08 |   2.18986    |               411573    |         34.7536 |
| XRP-USDT        |        91.7491 |        1.14795e+08 |   0.70055    |               330888    |         31.9603 |
| DOGE-USDT       |        89.5239 |        3.97292e+07 |   1.06695    |               280818    |         31.0582 |
| BNB-USDT        |        89.4719 |        5.02468e+07 |   0.156992   |               110747    |         21.1609 |
| SUI-USDT        |        84.8362 |        2.33928e+07 |   1.0538     |                91129.8  |         34.8641 |
| TRX-USDT        |        84.6207 |        1.07587e+07 |   3.26318    |               164392    |         14.435  |
| GOLD(PAXG)-USDT |        83.6505 |        6.40221e+07 |   0.0224669  |                61930.6  |         43.6171 |
| LTC-USDT        |        83.344  |        1.01028e+07 |   1.79711    |                79259.5  |         23.8473 |
| ADA-USDT        |        83.024  |        1.98002e+07 |   3.83215    |                90600    |         34.8612 |
| LINK-USDT       |        80.33   |        3.1219e+07  |   2.20167    |                52715.3  |         32.8311 |
| UNI-USDT        |        74.778  |        6.54064e+06 |   2.79759    |                16805.7  |         33.8866 |
| WLD-USDT        |        72.23   |        5.65055e+06 |   3.0888     |                 5701.24 |         42.3406 |
| TRUMP-USDT      |        70.8182 |        3.87538e+06 |   3.0689     |                17786.6  |         33.8283 |
| WXT-USDT        |        70.504  |        1.99951e+06 |   1.88893    |                13241.6  |         23.1986 |
| XLM-USDT        |        67.65   |        5.33147e+06 |   6.01504    |                16351.1  |         35.3291 |
| PUMP-USDT       |        61.6895 |        2.45841e+06 |   5.5571     |                 8539.08 |         43.7432 |
| SHIB-USDT       |        61.366  |        4.73421e+06 |   6.53915    |                 2296.51 |         36.8695 |
| DOT-USDT        |        60.6589 |        5.67427e+06 |   7.06464    |                 1499.74 |         38.4551 |
| ETC-USDT        |        59.056  |        2.72052e+06 |  11.6754     |                 4211.04 |         40.7903 |
| CHZ-USDT        |        55.608  |        2.01876e+06 |   5.59284    |                 3628.82 |         27.7912 |
| OP-USDT         |        54.5459 |        2.16624e+06 |   8.85347    |                 1300.34 |         39.8376 |
| CRV-USDT        |        51.4564 |        1.09782e+06 |   4.5798     |                 1499.25 |         38.7938 |
| RENDER-USDT     |        51.0873 |        1.11031e+06 |   5.94707    |                 5511.81 |         42.8809 |
| CAKE-USDT       |        46.8973 |        1.19164e+06 |   7.11491    |                 1006.64 |         30.0626 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
