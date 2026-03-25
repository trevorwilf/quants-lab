# MEXC Public Screener Report

Generated: 2026-03-23T23:46:18Z

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
- Selected: 26

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
| BTC-USDT        |        94.2587 |        1.07059e+09 |   0.00141306 |               462512    |         25.5251 |
| DOGE-USDT       |        92.1382 |        3.9781e+07  |   1.06377    |               255612    |         31.211  |
| SOL-USDT        |        91.2464 |        1.5315e+08  |   1.09511    |               567094    |         34.7897 |
| BNB-USDT        |        91.1407 |        5.02012e+07 |   0.156665   |               121528    |         21.186  |
| XRP-USDT        |        90.2696 |        1.14886e+08 |   0.698836   |               338466    |         32.0425 |
| LTC-USDT        |        87.098  |        1.01648e+07 |   1.79872    |                95407.5  |         23.8743 |
| TRX-USDT        |        84.6963 |        1.08292e+07 |   3.2568     |               171969    |         14.3475 |
| LINK-USDT       |        84.0373 |        3.13981e+07 |   1.09908    |                30812.2  |         32.9878 |
| ADA-USDT        |        83.1144 |        1.97788e+07 |   3.8219     |               102797    |         34.8495 |
| TAO-USDT        |        81.41   |        2.06702e+07 |   4.79206    |                13625    |         64.9408 |
| GOLD(XAUT)-USDT |        78.3635 |        1.62976e+08 |   7.24375    |                85235    |         44.2488 |
| PEPE-USDT       |        76.926  |        1.51724e+07 |   5.81226    |                12501.4  |         42.4155 |
| UNI-USDT        |        76.5144 |        6.53914e+06 |   2.79135    |                20733.3  |         33.8675 |
| WLD-USDT        |        74.78   |        5.66696e+06 |   3.0755     |                 6819.61 |         42.4811 |
| HBAR-USDT       |        73.8881 |        5.92411e+06 |   1.07417    |                 4737.9  |         29.7388 |
| TRUMP-USDT      |        73.8284 |        3.88393e+06 |   3.04739    |                17249.5  |         33.69   |
| WLFI-USDT       |        70.4246 |        5.66138e+06 |   1.91957    |                 1371.44 |         43.3282 |
| XLM-USDT        |        70.0284 |        5.33338e+06 |   6.01866    |                17793.4  |         35.2717 |
| WXT-USDT        |        66.326  |        1.98785e+06 |   2.82805    |                 4651.5  |         23.2457 |
| ICP-USDT        |        66.0424 |        2.78869e+06 |   4.15714    |                 5244.05 |         32.9232 |
| DOT-USDT        |        65.6074 |        5.72312e+06 |   7.04473    |                 6489.83 |         38.5515 |
| PUMP-USDT       |        61.0263 |        2.45854e+06 |   5.52944    |                 5058.09 |         43.6367 |
| TON-USDT        |        58.252  |        2.6167e+06  |  15.1745     |                11922.3  |         25.3474 |
| ETC-USDT        |        58.226  |        2.70244e+06 |  11.6618     |                 7230.81 |         40.8456 |
| SHIB-USDT       |        57.7844 |        4.75745e+06 |   8.19874    |                 1735.9  |         36.8386 |
| RENDER-USDT     |        55.1904 |        1.11089e+06 |   5.94354    |                 7772.41 |         43.1589 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
