# MEXC Public Screener Report

Generated: 2026-03-24T04:11:18Z

## Objective

Shortlist markets for PMM Dynamic research and candle ingestion using public market-data endpoints only.

## Stop-Ship Notes

- This is an ingestion/research gate, not a live-trading approval.
- Passing markets still need post-ingestion audit, walk-forward validation, and live microstructure checks.
- Exchange rule fields are exported as estimates when the API does not expose exact tick/step filters.

## Counts

- Universe: 2403
- Shortlist: 100
- Enriched: 100
- Selected: 27
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
universe_top_k: 100
user_agent: pmm-lab-screener/0.1
vol_to_spread_soft_max: 50.0
vol_to_spread_soft_min: 1.0
vol_to_spread_target_max: 20.0
vol_to_spread_target_min: 3.0
```

## Top Selected Pairs

| trading_pair    |   screen_score |   quote_volume_24h |   spread_bps |   top_of_book_quote |   sym_depth_quote_10bps |   sym_depth_quote_50bps |   sym_depth_quote_1xspread |   natr_bps_mean |
|:----------------|---------------:|-------------------:|-------------:|--------------------:|------------------------:|------------------------:|---------------------------:|----------------:|
| SOL-USDT        |        92.0664 |        1.53687e+08 |    1.1032    |            2177.68  |               679348    |             1.50488e+06 |                   2177.68  |         34.2926 |
| DOGE-USDT       |        91.0145 |        3.99788e+07 |    1.06866   |            3895.81  |               274980    |        863837           |                   3895.81  |         31.3716 |
| ADA-USDT        |        85.096  |        1.98742e+07 |    3.82044   |            7053.73  |                80497.7  |        436698           |                   7053.73  |         34.5809 |
| LTC-USDT        |        84.448  |        1.03718e+07 |    1.80131   |            1581.95  |                76504.9  |        359823           |                   1581.95  |         23.402  |
| BNB-USDT        |        84.0963 |        4.90077e+07 |    0.158072  |             572.91  |                91829.9  |        135391           |                    572.91  |         20.9362 |
| LINK-USDT       |        84.0325 |        3.24189e+07 |    1.09655   |             455.95  |                31867.1  |        769807           |                    455.95  |         32.9403 |
| GOLD(PAXG)-USDT |        83.2101 |        5.71943e+07 |    0.0229193 |            1391.36  |                87005.1  |        155404           |                   1391.36  |         41.6531 |
| TRX-USDT        |        81.6376 |        1.08219e+07 |    3.2305    |           10714     |               146108    |             1.31975e+06 |                  10714     |         14.3367 |
| TAO-USDT        |        80.978  |        2.50858e+07 |    4.45066   |            2845.51  |                10335.5  |        102321           |                   2845.51  |         70.3758 |
| UNI-USDT        |        75.225  |        6.55553e+06 |    2.78823   |             846.891 |                15865.8  |        178440           |                    846.891 |         33.7341 |
| TRUMP-USDT      |        73.4665 |        3.7621e+06  |    3.05483   |             536.707 |                27060.3  |        259986           |                    536.707 |         33.5745 |
| HBAR-USDT       |        73.2443 |        6.18094e+06 |    1.07579   |             355.534 |                11696.2  |         96694.5         |                    355.534 |         30.3047 |
| WLD-USDT        |        72.72   |        5.82836e+06 |    3.10222   |            1177.28  |                 7801.91 |        109914           |                   1177.28  |         43.0236 |
| TON-USDT        |        68.32   |        2.90821e+06 |    7.50469   |           12594.8   |                12594.8  |        205045           |                  12594.8   |         25.5974 |
| DOT-USDT        |        67.1049 |        6.24297e+06 |    7.05467   |            2131.52  |                 2131.52 |        120768           |                   2131.52  |         39.5854 |
| WXT-USDT        |        65.96   |        2.02188e+06 |    1.42109   |            1620.5   |                 9531.03 |         34290.5         |                   1620.5   |         23.0833 |
| ZRO-USDT        |        64.468  |        2.38102e+06 |    4.68713   |             530.278 |                 1349.16 |         48431.9         |                    530.278 |         64.6552 |
| ASTER-USDT      |        62.9272 |        2.81407e+06 |    4.55685   |             408.402 |                 3913.37 |        137386           |                    584.116 |         24.2817 |
| SHIB-USDT       |        62.002  |        4.92895e+06 |    8.22707   |            1090.96  |                 2179.68 |         78432.5         |                   1090.96  |         36.5348 |
| PUMP-USDT       |        58.7555 |        2.47456e+06 |    5.58503   |            1280.27  |                 8989.69 |         58142.7         |                   1280.27  |         43.9173 |
| SAHARA-USDT     |        57.79   |        2.39166e+06 |    3.83803   |             362.408 |                 1841.49 |          3848.02        |                    362.408 |         45.6478 |
| ICP-USDT        |        56.2642 |        2.86786e+06 |    4.17798   |             260.3   |                 2201.35 |         20512.4         |                    260.3   |         33      |
| OP-USDT         |        56.1204 |        2.38715e+06 |    8.89284   |            3168.15  |                 3168.15 |         65301.2         |                   3168.15  |         41.7876 |
| ETC-USDT        |        55.204  |        2.77099e+06 |   11.8554    |            2599.54  |                 2599.54 |         83583.7         |                   2599.54  |         41.0993 |
| RENDER-USDT     |        54.8    |        1.33861e+06 |    5.71592   |             309.435 |                 9340.88 |         50996           |                    309.435 |         45.6193 |
| CRV-USDT        |        52.8712 |        1.11264e+06 |    4.53001   |             368.383 |                 1612.3  |         54269.5         |                    368.383 |         38.0087 |
| ATOM-USDT       |        50.8875 |        1.70774e+06 |    5.62272   |             573.069 |                 3321.59 |         54468.9         |                    573.069 |         29.5082 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
