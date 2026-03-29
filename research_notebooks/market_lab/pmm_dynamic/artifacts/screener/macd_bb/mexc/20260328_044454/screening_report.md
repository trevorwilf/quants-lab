# MACD-BB public screener report

## Executive summary

- Connector: `mexc`
- Screening mode: `long_only`
- Universe rows: `2363`
- Shortlist rows: `1000`
- Enriched rows: `1000`
- Selected rows: `4`
- Selection mode: `strict`
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
max_ambiguous_rate: 0.5
strategy_score_weight: 0.4

```

### Controller template settings used for exports

```yaml
connector_name: mexc
candles_connector: mexc
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

| trading_pair   |   screen_score |   strategy_score |   strategy_signal_count |   strategy_hit_rate |   strategy_mean_barrier_return_net_bps |   strategy_profit_factor_proxy |   spread_bps |   quote_volume_24h |   strategy_current_signal | rejection_reason   |
|:---------------|---------------:|-----------------:|------------------------:|--------------------:|---------------------------------------:|-------------------------------:|-------------:|-------------------:|--------------------------:|:-------------------|
| UNI-USDT       |        90.2487 |          82.839  |                       5 |                0.8  |                                44.9173 |                        28.0641 |    2.96956   |        4.61271e+06 |                         0 |                    |
| LTC-USDT       |        89.3107 |          77.201  |                       4 |                0.75 |                                16.3065 |                        10.7654 |    1.86515   |        7.34743e+06 |                         0 |                    |
| ETH-USDT       |        85.8142 |          71.3011 |                       3 |                1    |                                19.3771 |                       inf      |    0.0502198 |        5.81185e+08 |                         0 |                    |
| OP-USDT        |        81.5083 |          72.6274 |                       3 |                1    |                                25.224  |                       inf      |    9.66651   |        1.26051e+06 |                         0 |                    |

## Critical issues and live blockers

- Passing the screener means the pair looks usable for **research** and possibly **paper trading**, not live deployment.
- Net-edge figures subtract observed spread only. They do **not** include venue-specific fee schedules unless you add them.
- Spot deployments should assume **long-only** unless you already hold inventory for sell-side management or use a perpetual connector.
- The controller templates are starter YAMLs. Exchange rules in the patch file remain estimates unless you verify them against the live connector.

## Rejection summary

| rejection_reason                     |   count |
|:-------------------------------------|--------:|
| depth_10bps<1000                     |     904 |
| quote_volume_24h<1e+06               |     895 |
| top_of_book_quote<250                |     871 |
| strategy_signal_count<3              |     862 |
| missing_strategy_profit_factor_proxy |     539 |
| missing_strategy_mean_net_edge_bps   |     525 |
| strategy_mean_net_edge_bps<0         |     302 |
| strategy_profit_factor_proxy<0.95    |     192 |
| spread_bps>60                        |      78 |
| natr_bps_mean<10                     |      49 |
| zero_volume_fraction>0.15            |      22 |
| natr_bps_mean>350                    |       9 |
| last_trade_age_sec>1800              |       6 |
| n_candles<400                        |       1 |
| recent_trade_count<100               |       1 |

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
