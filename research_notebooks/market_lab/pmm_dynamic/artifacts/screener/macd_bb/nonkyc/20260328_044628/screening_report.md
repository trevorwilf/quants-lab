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

| trading_pair   |   screen_score |   strategy_score |   strategy_signal_count |   strategy_hit_rate |   strategy_mean_barrier_return_net_bps |   strategy_profit_factor_proxy |   spread_bps |   quote_volume_24h |   strategy_current_signal | rejection_reason                                                                                                 |
|:---------------|---------------:|-----------------:|------------------------:|--------------------:|---------------------------------------:|-------------------------------:|-------------:|-------------------:|--------------------------:|:-----------------------------------------------------------------------------------------------------------------|
| ALGO-USDC      |        77.7647 |          65.1318 |                       1 |            1        |                              -25.7154  |                     inf        |     73.6196  |          48741.8   |                         0 | quote_volume_24h<50000; strategy_signal_count<3; strategy_mean_net_edge_bps<0                                    |
| ARB-USDT       |        77.7045 |          65.6351 |                       2 |            1        |                              -45.2139  |                     inf        |     67.2646  |          52796.4   |                         0 | strategy_signal_count<3; strategy_mean_net_edge_bps<0                                                            |
| AAVE-USDT      |        77.5797 |          63.8796 |                       4 |            0.5      |                              -75.8659  |                       1.22398  |     78.399   |          80001.3   |                         0 | strategy_mean_net_edge_bps<0                                                                                     |
| ETC-USDT       |        75.8505 |          65.7953 |                       1 |            1        |                              -24.4364  |                     inf        |     61.8429  |          45108.6   |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0               |
| LTC-USDT       |        75.2501 |          66.0797 |                       2 |            1        |                              -43.0392  |                     inf        |     59.7796  |         617564     |                         0 | top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0                                       |
| SAL-USDT       |        74.9083 |          70.1217 |                       1 |            1        |                               22.2017  |                     inf        |      0.58584 |          40521.8   |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_signal_count<3                                             |
| SCASH-USDT     |        74.0485 |          69.7831 |                       7 |            1        |                              -46.1604  |                     inf        |     84.738   |          10587.7   |                         0 | quote_volume_24h<50000; strategy_mean_net_edge_bps<0                                                             |
| ZEC-USDT       |        73.711  |          69.6618 |                       2 |            1        |                              -22.8562  |                     inf        |     84.678   |          40142.8   |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0               |
| ARB-USDC       |        73.0635 |          66.9133 |                       3 |            0.666667 |                              -71.1651  |                       3.00331  |     78.5193  |          14883.9   |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_mean_net_edge_bps<0                                        |
| ADA-USDT       |        73.0306 |          64.5542 |                       3 |            0.333333 |                              -58.4039  |                       1.50076  |     61.1122  |           8187.77  |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_mean_net_edge_bps<0                                        |
| EQPAY-USDT     |        72.2245 |          80.4554 |                       5 |            0.8      |                              -21.7776  |                      18.2048   |     49.6792  |            289.071 |                         0 | quote_volume_24h<50000; top_of_book_quote<5; coverage_ratio<0.92; strategy_mean_net_edge_bps<0                   |
| SHIB-USDT      |        72.0354 |          66.0112 |                       1 |            1        |                              -24.409   |                     inf        |     41.7973  |         203638     |                         0 | top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0                                       |
| UNI-USDT       |        71.3726 |          49.9232 |                       2 |            0.5      |                             -129.821   |                       0.143764 |     68.2391  |         284034     |                         0 | top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0; strategy_profit_factor_proxy<0.95    |
| BTC-USDC       |        70.7898 |          44.6188 |                       1 |            0        |                              -78.1558  |                       0        |     64.0148  |         613262     |                         0 | top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0; strategy_profit_factor_proxy<0.95    |
| CAKE-USDC      |        70.2082 |          60.1838 |                       1 |            1        |                              -51.1035  |                     inf        |     73.2601  |           7767.78  |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0               |
| PEP-DOGE       |        69.9954 |          64.8614 |                       3 |            1        |                              -58.5775  |                     inf        |     84.9994  |          44893.1   |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_mean_net_edge_bps<0                                        |
| XLM-USDT       |        69.813  |          55.8201 |                       1 |            0        |                               -6.03682 |                     nan        |      6.03682 |         121129     |                         0 | top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0; missing_strategy_profit_factor_proxy |
| PEP-USDC       |        69.7735 |          64.2105 |                       1 |            1        |                              -30.6153  |                     inf        |     84.4206  |          34040.8   |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_signal_count<3; strategy_mean_net_edge_bps<0               |
| ARRR-USDT      |        69.6407 |          71.7919 |                       1 |            1        |                              113.541   |                     inf        |     86.459   |         267643     |                         0 | top_of_book_quote<5; strategy_signal_count<3                                                                     |
| PEP-USDT       |        69.0662 |          71.8224 |                       1 |            1        |                               82.2311  |                     inf        |    117.769   |          45445.4   |                         0 | quote_volume_24h<50000; top_of_book_quote<5; strategy_signal_count<3                                             |

## Critical issues and live blockers

- Passing the screener means the pair looks usable for **research** and possibly **paper trading**, not live deployment.
- Net-edge figures subtract observed spread only. They do **not** include venue-specific fee schedules unless you add them.
- Spot deployments should assume **long-only** unless you already hold inventory for sell-side management or use a perpetual connector.
- The controller templates are starter YAMLs. Exchange rules in the patch file remain estimates unless you verify them against the live connector.

## Rejection summary

| rejection_reason                     |   count |
|:-------------------------------------|--------:|
| top_of_book_quote<5                  |     306 |
| quote_volume_24h<50000               |     303 |
| strategy_signal_count<3              |     302 |
| missing_strategy_profit_factor_proxy |     226 |
| missing_strategy_mean_net_edge_bps   |     206 |
| coverage_ratio<0.92                  |     201 |
| strategy_mean_net_edge_bps<0         |     126 |
| natr_bps_mean<15                     |      71 |
| strategy_profit_factor_proxy<0.95    |      39 |
| spread_bps>180                       |      16 |
| last_trade_age_sec>3600              |       8 |
| missing_spread_bps                   |       3 |
| missing_top_of_book_quote            |       3 |
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
