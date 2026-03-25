# MEXC Public Screener Report

Generated: 2026-03-24T01:03:39Z

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
- Selected: 24

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
| BTC-USDT        |        93.7407 |        1.06742e+09 |   0.00141428 |               444869    |         25.2233 |
| XRP-USDT        |        92.3065 |        1.15567e+08 |   0.703755   |               442064    |         31.6802 |
| DOGE-USDT       |        89.9632 |        3.99695e+07 |   1.06855    |               153696    |         31.1307 |
| BNB-USDT        |        89.6587 |        4.93826e+07 |   0.15712    |               123073    |         21.0179 |
| SOL-USDT        |        88.2233 |        1.53409e+08 |   1.0992     |               650466    |         34.4365 |
| TAO-USDT        |        86.0887 |        2.15383e+07 |   0.336717   |                19360.7  |         65.6594 |
| LTC-USDT        |        83.742  |        1.02219e+07 |   1.80424    |                92137.9  |         23.613  |
| ADA-USDT        |        83.696  |        1.99456e+07 |   3.84689    |               121144    |         34.5382 |
| TRX-USDT        |        83.4564 |        1.09383e+07 |   3.23992    |               171621    |         14.4341 |
| GOLD(XAUT)-USDT |        82.9278 |        1.51578e+08 |   3.66754    |                79182.7  |         43.1788 |
| UNI-USDT        |        76.4436 |        6.59687e+06 |   2.8023     |                13793.1  |         33.8908 |
| HBAR-USDT       |        74.2688 |        5.9878e+06  |   1.08278    |                10454.7  |         29.8534 |
| TRUMP-USDT      |        73.7341 |        3.76766e+06 |   3.0567     |                20113.2  |         33.5874 |
| WLD-USDT        |        72.948  |        5.83524e+06 |   3.11769    |                 9155.33 |         42.9491 |
| HYPE-USDT       |        72.7519 |        1.68556e+07 |   5.33191    |                10793    |         44.8134 |
| XLM-USDT        |        72.09   |        5.45384e+06 |   6.05144    |                20653.4  |         35.5314 |
| ZRO-USDT        |        66.096  |        2.16985e+06 |   4.51569    |                 3227.18 |         61.1057 |
| SHIB-USDT       |        66.048  |        4.92588e+06 |   3.31181    |                 2608.19 |         36.9781 |
| ICP-USDT        |        65.177  |        2.80398e+06 |   4.17101    |                 6399.24 |         32.9371 |
| PUMP-USDT       |        61.0327 |        2.47386e+06 |   5.56948    |                 6824.25 |         43.8631 |
| ETC-USDT        |        57.054  |        2.76203e+06 |  11.7855     |                 2870.3  |         41.238  |
| OP-USDT         |        56.6627 |        2.25882e+06 |   8.83002    |                 1604.95 |         40.4549 |
| ATOM-USDT       |        55.1377 |        1.65278e+06 |   5.61325    |                 3190.55 |         28.8368 |
| HUMA-USDT       |        54.028  |        1.31195e+06 |   5.74878    |                 1140.7  |         74.4719 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
