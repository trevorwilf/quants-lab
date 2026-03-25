# MEXC Public Screener Report

Generated: 2026-03-25T23:52:15Z

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
- Selected: 20
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
| BTC-USDT        |        92.0569 |        8.28488e+08 |   0.00140341 |            5427.55  |               385619    |        461625           |                   5427.55  |         17.1839 |
| SOL-USDT        |        90.5387 |        9.69466e+07 |   1.09117    |             361.795 |               661848    |             2.61543e+06 |                    361.795 |         22.7215 |
| DOGE-USDT       |        89.4308 |        3.15203e+07 |   1.0415     |            2632.79  |               176912    |        812775           |                   2632.79  |         22.2969 |
| SUI-USDT        |        86.5703 |        1.27205e+07 |   1.03386    |            2993.75  |                94119.1  |        312459           |                   2993.75  |         23.637  |
| GOLD(PAXG)-USDT |        85.2608 |        1.55844e+07 |   0.0222403  |            2875.5   |               122975    |        173182           |                   2875.5   |         16.5459 |
| ADA-USDT        |        83.0789 |        1.35579e+07 |   3.70302    |           10419     |               123759    |        841208           |                  10419     |         26.4586 |
| LINK-USDT       |        80.2211 |        1.59019e+07 |   2.13516    |             402.457 |                95751.2  |        648138           |                   3383.52  |         22.3606 |
| WLD-USDT        |        76.2283 |        4.33491e+06 |   3.0869     |             763.24  |                 9760.12 |        154866           |                    763.24  |         33.0179 |
| XLM-USDT        |        72.6509 |        7.48465e+06 |   5.63222    |            3520.46  |                14689.9  |        220737           |                   3520.46  |         34.5796 |
| HBAR-USDT       |        71.7873 |        2.9614e+06  |   1.05625    |             337.818 |                14803.5  |        132291           |                    337.818 |         19.3938 |
| TRUMP-USDT      |        71.6351 |        3.8034e+06  |   3.04832    |             434.831 |                24529.8  |        254817           |                    434.831 |         31.1566 |
| DOT-USDT        |        69.03   |        5.92654e+06 |   7.35565    |            4675.22  |                 4675.22 |        107547           |                   4675.22  |         32.4045 |
| PEPE-USDT       |        66.8879 |        9.88083e+06 |   5.66412    |             425.274 |                 2843.8  |        172038           |                   2490.4   |         30.1779 |
| PUMP-USDT       |        65.33   |        2.73035e+06 |   5.24797    |            1794.44  |                11081.1  |         90068.2         |                   1794.44  |         38.1214 |
| WBTC-USDT       |        63.3156 |        1.15201e+06 |   0.00140629 |            5887.84  |                10770.8  |         31919           |                   5887.84  |         15.1235 |
| ASTER-USDT      |        59.5717 |        1.75593e+06 |   4.52523    |             333.355 |                 1119.43 |        118060           |                    438.42  |         19.2931 |
| CRV-USDT        |        56.678  |        1.12623e+06 |   4.25985    |             344.427 |                 1315.22 |         27240.7         |                    344.427 |         35.1279 |
| RENDER-USDT     |        54.352  |        1.09704e+06 |   5.38938    |             675.306 |                12058.9  |         60645.4         |                    675.306 |         47.5065 |
| ETC-USDT        |        52.2752 |        1.78199e+06 |  11.5407     |            3660.2   |                 3660.2  |        108171           |                   3660.2   |         30.6602 |
| OP-USDT         |        52.1303 |        1.18486e+06 |   8.82223    |            2087.98  |                 2087.98 |         75486.7         |                   2087.98  |         33.3864 |

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
