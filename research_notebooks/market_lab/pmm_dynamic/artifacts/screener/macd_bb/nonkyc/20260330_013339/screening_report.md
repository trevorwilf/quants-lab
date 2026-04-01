# MACD-BB public screener report

## Executive summary

- Connector: `nonkyc`
- Screening mode: `long_only`
- Universe rows: `345`
- Shortlist rows: `345`
- Enriched rows: `345`
- Selected rows: `20`
- Selection mode: `fallback_ranked`
- Fitness: **research / paper-trade triage only**
- Main live blockers:
  1. public REST candles + order book snapshots do not model queue position, latency, partial fills, or fees
  2. barrier outcomes are inferred from candle paths and treat same-bar TP/SL collisions conservatively
  3. screen results are recent-sample diagnostics, not walk-forward validation

## Research and validation summary

This notebook reuses the public REST PMM screener structure for universe discovery and microstructure gating, then adds
MACD-BB signal extraction using the repo's `macd_bb_v1` indicator logic. Strategy quality metrics are based on recent
signal events extracted from public candles and evaluated with an approximate TP / SL / time-limit barrier.

### Market-data gates

- quote-volume, spread, top-of-book, depth, trade recency, and candle-quality checks are inherited from the public PMM screener stack
- strategy metrics are added **after** microstructure enrichment and combined into the final `screen_score`

### Strategy settings used for diagnostics

```yaml
interval: 5m
interval_seconds: 300
bb_length: 100
bb_std: 2.0
bb_long_threshold: 0.0
bb_short_threshold: 1.0
macd_fast: 21
macd_slow: 42
macd_signal: 9
cooldown_time: 300
take_profit: 0.02
stop_loss: 0.03
time_limit_sec: 2700
side_mode: long_only
min_signal_events: 3
min_events_per_day: 0.0
min_hit_rate: 0.0
min_mean_net_edge_bps: 0.0
min_profit_factor_proxy: 0.95
max_ambiguous_rate: 0.6
strategy_score_weight: 0.4

```

### Controller template settings used for exports

```yaml
connector_name: nonkyc
candles_connector: nonkyc
interval: 5m
total_amount_quote: 100.0
max_executors_per_side: 1
cooldown_time: 300
leverage: 1
position_mode: HEDGE
stop_loss: 0.03
take_profit: 0.02
time_limit: 2700
take_profit_order_type: 2
trailing_stop: null
bb_length: 100
bb_std: 2.0
bb_long_threshold: 0.0
bb_short_threshold: 1.0
macd_fast: 21
macd_slow: 42
macd_signal: 9
controller_name: macd_bb_v1
controller_type: directional_trading
manual_kill_switch: false
initial_positions: []

```

## Selected pairs

| trading_pair   |   screen_score |   strategy_score |   strategy_signal_count |   strategy_hit_rate |   strategy_mean_barrier_return_net_bps |   strategy_profit_factor_proxy |   spread_bps |   quote_volume_24h |   strategy_current_signal | rejection_reason                                                                                                                          |
|:---------------|---------------:|-----------------:|------------------------:|--------------------:|---------------------------------------:|-------------------------------:|-------------:|-------------------:|--------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------|
| XMR-USDT       |        83.2096 |          72.7464 |                       1 |            1        |                              115.742   |                     inf        |     30.2948  |        1.18359e+06 |                         0 | strategy_signal_count<3                                                                                                                   |
| NKYC-USDT      |        81.4022 |          72.1232 |                       1 |            1        |                               45.094   |                     inf        |     17.5534  |   161915           |                         0 | strategy_signal_count<3                                                                                                                   |
| RXD-USDT       |        76.6328 |          72.5652 |                       6 |            0.5      |                              -21.0514  |                       0.69333  |     17.0674  |     2241.57        |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_mean_net_edge_bps<0; strategy_profit_factor_proxy<0.95                              |
| EPIC-USDT      |        76.5217 |          68.9783 |                       1 |            1        |                               11.6139  |                     inf        |     63.6315  |    31442.4         |                         0 | quote_volume_24h<50000; strategy_signal_count<3                                                                                           |
| SHIB-USDT      |        75.7206 |          68.6449 |                       1 |            1        |                                6.97446 |                     inf        |      3.40078 |   141628           |                         0 | top_of_book_quote<5; strategy_signal_count<3                                                                                              |
| MANA-USDT      |        75.1767 |          70.1667 |                       1 |            1        |                               19.7644  |                     inf        |      7.40284 |    67525.3         |                         0 | top_of_book_quote<5; strategy_signal_count<3                                                                                              |
| DIVI-USDT      |        74.3807 |          76.4348 |                       2 |            0.5      |                               11.1157  |                      23.9483   |     84.7086  |    31473.7         |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_signal_count<3                                                                      |
| XRP-USDT       |        74.2897 |          57.7754 |                       1 |            1        |                              -57.5054  |                     inf        |     84.5081  |        1.43868e+06 |                         0 | strategy_signal_count<3; strategy_mean_net_edge_bps<0                                                                                     |
| RVN-USDT       |        73.6547 |          76.8478 |                       2 |            1        |                              166.902   |                     inf        |     33.0982  |     5612.89        |                         0 | quote_volume_24h<50000; top_of_book_quote<5; coverage_ratio<0.92; strategy_signal_count<3                                                 |
| ZSD-USDT       |        73.1196 |          64.8188 |                       1 |            1        |                              -13.6709  |                     inf        |     17.8527  |     6852.74        |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0                                        |
| PEP-USDT       |        72.3922 |          61.8152 |                       2 |            0.5      |                              -64.2427  |                       0.855186 |     60.6452  |    41470.2         |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0; strategy_profit_factor_proxy<0.95     |
| INJ-USDT       |        69.6445 |          56.2681 |                       2 |            0.5      |                              -52.5654  |                     inf        |     70.4225  |    29090.7         |                         0 | quote_volume_24h<50000; top_of_book_quote<5; coverage_ratio<0.92; natr_bps_mean<15; strategy_signal_count<3; strategy_mean_net_edge_bps<0 |
| BDX-USDT       |        69.3843 |          49.0127 |                       2 |            0        |                              -70.8221  |                       0        |     21.2063  |    25595.6         |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0; strategy_profit_factor_proxy<0.95     |
| LINK-USDT      |        69.2353 |          53.8623 |                       2 |            0        |                              -35.3149  |                     nan        |     35.3149  |   591343           |                         0 | top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0; missing_strategy_profit_factor_proxy                          |
| ADA-USDT       |        69.2263 |          68.2101 |                       1 |            1        |                                4.71442 |                     inf        |     45.2024  |     6247.7         |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_signal_count<3                                                                      |
| ERG-USDT       |        69.1131 |          63.3261 |                       1 |            1        |                              -18.4112  |                     inf        |     39.9347  |     2679.18        |                         0 | quote_volume_24h<50000; coverage_ratio<0.92; strategy_signal_count<3; strategy_mean_net_edge_bps<0                                        |
| ARB-USDT       |        68.9906 |          66.7428 |                       3 |            0.333333 |                              -37.1518  |                       0.33635  |     22.2717  |    50111.7         |                         0 | top_of_book_quote<5; strategy_mean_net_edge_bps<0; strategy_profit_factor_proxy<0.95                                                      |
| ZANO-USDT      |        68.989  |          71.529  |                       1 |            1        |                               84.0639  |                     inf        |    115.936   |   116944           |                         0 | top_of_book_quote<5; coverage_ratio<0.92; strategy_signal_count<3                                                                         |
| AVAX-USDT      |        68.3985 |          51.1667 |                       3 |            0        |                              -57.5705  |                     nan        |     57.5705  |   294758           |                         0 | top_of_book_quote<5; strategy_mean_net_edge_bps<0; missing_strategy_profit_factor_proxy                                                   |
| BCH-USDT       |        68.2987 |          45.0851 |                       7 |            0        |                             -152.723   |                       0        |     83.8112  |   655015           |                         0 | top_of_book_quote<5; strategy_mean_net_edge_bps<0; strategy_profit_factor_proxy<0.95                                                      |

## Critical issues and live blockers

- Passing the screener means the pair looks usable for **research** and possibly **paper trading**, not live deployment.
- Net-edge figures subtract observed spread only. They do **not** include venue-specific fee schedules unless you add them.
- Spot deployments should assume **long-only** unless you already hold inventory for sell-side management or use a perpetual connector.
- The controller templates are starter YAMLs. Exchange rules in the patch file remain estimates unless you verify them against the live connector.

## Rejection summary

| rejection_reason                     |   count |
|:-------------------------------------|--------:|
| strategy_signal_count<3              |     312 |
| quote_volume_24h<50000               |     310 |
| top_of_book_quote<5                  |     308 |
| missing_strategy_profit_factor_proxy |     236 |
| missing_strategy_mean_net_edge_bps   |     207 |
| coverage_ratio<0.92                  |     203 |
| strategy_mean_net_edge_bps<0         |     108 |
| natr_bps_mean<15                     |      86 |
| strategy_profit_factor_proxy<0.95    |      31 |
| spread_bps>180                       |      15 |
| last_trade_age_sec>3600              |       5 |
| missing_spread_bps                   |       4 |
| missing_top_of_book_quote            |       4 |
| missing_last_trade_age_sec           |       3 |
| recent_trade_count<30                |       3 |
| n_candles<360                        |       3 |
| missing_coverage_ratio               |       3 |
| missing_zero_volume_fraction         |       3 |
| missing_natr_bps_mean                |       3 |
| zero_volume_fraction>0.35            |       2 |

## Controller dictionary fields used

The controller templates were built from `controller_yml_data_dictionary.md` rows for `macd_bb_v1`:

| field_path             | default             | what_it_does                                                                                                                                                                                                          |
|:-----------------------|:--------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| controller_name        | macd_bb_v1          | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file.                                                                                     |
| controller_type        | directional_trading | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. |
| total_amount_quote     | 100                 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations.                                                                                                |
| connector_name         | binance_perpetual   | Exchange/connector name that the controller uses for trading or market data.                                                                                                                                          |
| trading_pair           | WLD-USDT            | Market symbol the controller trades or monitors, in `BASE-QUOTE` form.                                                                                                                                                |
| max_executors_per_side | 2                   | Maximum number of concurrent executors the directional controller may keep open on each side (long/buy or short/sell).                                                                                                |
| cooldown_time          | 60 * 5              | Minimum wait time between signal/executor creations or rebalance actions, depending on the controller.                                                                                                                |
| leverage               | 1                   | Leverage applied when the connector supports perpetual or margin trading.                                                                                                                                             |
| position_mode          | HEDGE               | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY.                                                                                                             |
| stop_loss              | 0.03                | Relative loss threshold that closes an executor/position when exceeded.                                                                                                                                               |
| take_profit            | 0.02                | Relative profit threshold that closes an executor/position when reached.                                                                                                                                              |
| time_limit             | 60 * 45             | Maximum time in seconds that an executor/position may remain open before it is closed.                                                                                                                                |
| take_profit_order_type | 2                   | Integer enum for the order type used when placing the take-profit exit order. Values: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER.                                                                                               |
| trailing_stop          | null                | Trailing-stop configuration. In prompts this is entered as `activation_price,trailing_delta`; in YAML it can serialize as an object.                                                                                  |
| candles_connector      | null                | Connector used as the candle-data source. If left blank/null, validators fall back to the main trading connector.                                                                                                     |
| candles_trading_pair   | null                | Trading pair used as the candle-data source. If left blank/null, validators fall back to the main trading pair.                                                                                                       |
| interval               | 3m                  | Candle interval / analysis timeframe used for indicator calculations and signal generation.                                                                                                                           |
| bb_length              | 100                 | Lookback length used for Bollinger Band calculations.                                                                                                                                                                 |
| bb_std                 | 2.0                 | Standard-deviation multiplier used to build the Bollinger Bands.                                                                                                                                                      |
| bb_long_threshold      | 0.0                 | Lower Bollinger-percent threshold that triggers a long/buy signal when price falls below it.                                                                                                                          |
| bb_short_threshold     | 1.0                 | Upper Bollinger-percent threshold that triggers a short/sell signal when price rises above it.                                                                                                                        |
| macd_fast              | 21                  | Fast-period length used in MACD calculations.                                                                                                                                                                         |
| macd_slow              | 42                  | Slow-period length used in MACD calculations.                                                                                                                                                                         |
| macd_signal            | 9                   | Signal-period length used in MACD calculations.                                                                                                                                                                       |

## Exact next actions

1. Verify exchange trading rules (`price_tick`, `amount_step`, `min_notional`) against the live connector before paper trading.
2. Increase `CANDLE_LIMIT` and re-run if signal counts are too sparse to trust.
3. Paper trade the exported controllers first and compare realized fills against spread-based net-edge estimates.
4. Do not treat this notebook as a substitute for walk-forward backtesting or exchange-specific execution testing.
