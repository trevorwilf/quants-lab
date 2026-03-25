# NONKYC Public Screener Report

Generated: 2026-03-24T01:32:56Z

## Objective

Shortlist markets for PMM Dynamic research and candle ingestion using public market-data endpoints only.

## Stop-Ship Notes

- This is an ingestion/research gate, not a live-trading approval.
- Passing markets still need post-ingestion audit, walk-forward validation, and live microstructure checks.
- Exchange rule fields are exported as estimates when the API does not expose exact tick/step filters.

## Counts

- Universe: 233
- Shortlist: 80
- Enriched: 80
- Selected: 0

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
final_top_n: 25
include_symbols: []
interval: 5m
interval_seconds: 300
max_last_trade_age_sec: 3600.0
max_natr_bps: 400.0
max_retries: 3
max_spread_bps: 90.0
max_zero_volume_fraction: 0.3
min_candle_count: 220
min_candle_coverage_ratio: 0.95
min_depth_10bps_quote: 250.0
min_natr_bps: 12.0
min_quote_volume_24h: 100000.0
min_recent_trade_count: 40
min_top_of_book_quote: 75.0
natr_soft_max: 350.0
natr_soft_min: 8.0
natr_target_max: 180.0
natr_target_min: 20.0
quote_asset: USDT
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
timeout_seconds: 30.0
universe_top_k: 80
user_agent: pmm-lab-screener/0.1
vol_to_spread_soft_max: 60.0
vol_to_spread_soft_min: 1.0
vol_to_spread_target_max: 25.0
vol_to_spread_target_min: 3.0
```

## Top Selected Pairs

No markets passed the configured gates.

## Notes

- Research/ingestion only. Passing the screener does not imply live readiness.
- Rule fields in exports are estimates unless the exchange API exposes exact constraints.
