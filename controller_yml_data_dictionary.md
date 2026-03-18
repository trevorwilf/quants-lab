# Controller YAML data dictionary

This dictionary is built from the controller config classes that back files under `conf/controllers/*.yml`.

How to read it:
- `field_path` uses dot notation for nested objects and `[]` for list item schemas.
- `defined_in` tells you whether a field comes from a shared base config or a controller-specific config.
- Some composite fields have CLI shortcut parsers (for example comma-separated strings), but the YAML ultimately represents the same schema described here.
- Example/demo controllers under `controllers/generic/examples/` are included for completeness and flagged as example controllers.

## Controller summary

| Controller type | Controller name | Example? | Module | Top-level fields | Nested schema rows |
|---|---|---:|---|---:|---:|
| directional_trading | `ai_livestream` | no | `controllers/directional_trading/ai_livestream.py` | 20 | 6 |
| directional_trading | `bollinger_v1` | no | `controllers/directional_trading/bollinger_v1.py` | 24 | 6 |
| directional_trading | `bollinger_v2` | no | `controllers/directional_trading/bollinger_v2.py` | 24 | 6 |
| directional_trading | `bollingrid` | no | `controllers/directional_trading/bollingrid.py` | 32 | 6 |
| directional_trading | `dman_v3` | no | `controllers/directional_trading/dman_v3.py` | 29 | 6 |
| directional_trading | `macd_bb_v1` | no | `controllers/directional_trading/macd_bb_v1.py` | 27 | 6 |
| directional_trading | `supertrend_v1` | no | `controllers/directional_trading/supertrend_v1.py` | 23 | 6 |
| market_making | `dman_maker_v2` | no | `controllers/market_making/dman_maker_v2.py` | 29 | 6 |
| market_making | `pmm_dynamic` | no | `controllers/market_making/pmm_dynamic.py` | 32 | 6 |
| market_making | `pmm_simple` | no | `controllers/market_making/pmm_simple.py` | 25 | 6 |
| generic | `arbitrage_controller` | no | `controllers/generic/arbitrage_controller.py` | 13 | 8 |
| generic | `examples.basic_order_example` | yes | `controllers/generic/examples/basic_order_example.py` | 13 | 4 |
| generic | `examples.basic_order_open_close_example` | yes | `controllers/generic/examples/basic_order_open_close_example.py` | 15 | 4 |
| generic | `examples.buy_three_times_example` | yes | `controllers/generic/examples/buy_three_times_example.py` | 12 | 4 |
| generic | `examples.candles_data_controller` | yes | `controllers/generic/examples/candles_data_controller.py` | 7 | 8 |
| generic | `examples.full_trading_example` | yes | `controllers/generic/examples/full_trading_example.py` | 11 | 4 |
| generic | `examples.liquidations_monitor_controller` | yes | `controllers/generic/examples/liquidations_monitor_controller.py` | 10 | 4 |
| generic | `examples.market_status_controller` | yes | `controllers/generic/examples/market_status_controller.py` | 8 | 4 |
| generic | `examples.price_monitor_controller` | yes | `controllers/generic/examples/price_monitor_controller.py` | 9 | 4 |
| generic | `grid_strike` | no | `controllers/generic/grid_strike.py` | 22 | 14 |
| generic | `hedge_asset` | no | `controllers/generic/hedge_asset.py` | 15 | 4 |
| generic | `lp_rebalancer` | no | `controllers/generic/lp_rebalancer/lp_rebalancer.py` | 21 | 8 |
| generic | `multi_grid_strike` | no | `controllers/generic/multi_grid_strike.py` | 19 | 21 |
| generic | `pmm_mister` | no | `controllers/generic/pmm_mister.py` | 35 | 4 |
| generic | `pmm_v1` | no | `controllers/generic/pmm_v1.py` | 19 | 4 |
| generic | `quantum_grid_allocator` | no | `controllers/generic/quantum_grid_allocator.py` | 35 | 5 |
| generic | `stat_arb` | no | `controllers/generic/stat_arb.py` | 24 | 8 |
| generic | `xemm_multiple_levels` | no | `controllers/generic/xemm_multiple_levels.py` | 15 | 4 |

## `ai_livestream`

- Controller type: `directional_trading`
- Example controller: `no`
- Module: `controllers/directional_trading/ai_livestream.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | ai_livestream | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `AILivestreamControllerConfig` | `controllers/directional_trading/ai_livestream.py:17` |
| `controller_type` | `string` | no | directional_trading | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:24` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:25` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:31` |
| `max_executors_per_side` | `integer` | no | 2 | Maximum number of concurrent executors the directional controller may keep open on each side (long/buy or short/sell). | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:37` |
| `cooldown_time` | `integer` | no | 60 * 5 | Minimum wait time between signal/executor creations or rebalance actions, depending on the controller. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:43` |
| `leverage` | `integer` | no | 1 | Leverage applied when the connector supports perpetual or margin trading. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:49` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:55` |
| `stop_loss` | `decimal or null` | no | 0.03 | Relative loss threshold that closes an executor/position when exceeded. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:60` |
| `take_profit` | `decimal or null` | no | 0.02 | Relative profit threshold that closes an executor/position when reached. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:66` |
| `time_limit` | `integer or null` | no | 60 * 45 | Maximum time in seconds that an executor/position may remain open before it is closed. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:72` |
| `take_profit_order_type` | `integer (OrderType enum: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER)` | no | 2 | Integer enum for the order type used when placing the take-profit exit order. Values: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:78` |
| `trailing_stop` | `TrailingStop or null` | no | null | Trailing-stop configuration. In prompts this is entered as `activation_price,trailing_delta`; in YAML it can serialize as an object. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:84` |
| `trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `long_threshold` | `float` | no | 0.5 | Minimum long probability required for the AI livestream controller to emit a buy/long signal. | `AILivestreamControllerConfig` | `controllers/directional_trading/ai_livestream.py:18` |
| `short_threshold` | `float` | no | 0.5 | Minimum short probability required for the AI livestream controller to emit a sell/short signal. | `AILivestreamControllerConfig` | `controllers/directional_trading/ai_livestream.py:19` |
| `topic` | `string` | no | hbot/predictions | MQTT topic prefix from which the controller reads ML predictions. The strategy appends the normalized trading pair and `/ML_SIGNALS`. | `AILivestreamControllerConfig` | `controllers/directional_trading/ai_livestream.py:20` |

## `bollinger_v1`

- Controller type: `directional_trading`
- Example controller: `no`
- Module: `controllers/directional_trading/bollinger_v1.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | bollinger_v1 | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `BollingerV1ControllerConfig` | `controllers/directional_trading/bollinger_v1.py:15` |
| `controller_type` | `string` | no | directional_trading | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:24` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:25` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:31` |
| `max_executors_per_side` | `integer` | no | 2 | Maximum number of concurrent executors the directional controller may keep open on each side (long/buy or short/sell). | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:37` |
| `cooldown_time` | `integer` | no | 60 * 5 | Minimum wait time between signal/executor creations or rebalance actions, depending on the controller. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:43` |
| `leverage` | `integer` | no | 1 | Leverage applied when the connector supports perpetual or margin trading. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:49` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:55` |
| `stop_loss` | `decimal or null` | no | 0.03 | Relative loss threshold that closes an executor/position when exceeded. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:60` |
| `take_profit` | `decimal or null` | no | 0.02 | Relative profit threshold that closes an executor/position when reached. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:66` |
| `time_limit` | `integer or null` | no | 60 * 45 | Maximum time in seconds that an executor/position may remain open before it is closed. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:72` |
| `take_profit_order_type` | `integer (OrderType enum: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER)` | no | 2 | Integer enum for the order type used when placing the take-profit exit order. Values: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:78` |
| `trailing_stop` | `TrailingStop or null` | no | null | Trailing-stop configuration. In prompts this is entered as `activation_price,trailing_delta`; in YAML it can serialize as an object. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:84` |
| `trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `candles_connector` | `string` | no | null | Connector used as the candle-data source. If left blank/null, validators fall back to the main trading connector. | `BollingerV1ControllerConfig` | `controllers/directional_trading/bollinger_v1.py:16` |
| `candles_trading_pair` | `string` | no | null | Trading pair used as the candle-data source. If left blank/null, validators fall back to the main trading pair. | `BollingerV1ControllerConfig` | `controllers/directional_trading/bollinger_v1.py:21` |
| `interval` | `string` | no | 3m | Candle interval / analysis timeframe used for indicator calculations and signal generation. | `BollingerV1ControllerConfig` | `controllers/directional_trading/bollinger_v1.py:26` |
| `bb_length` | `integer` | no | 100 | Lookback length used for Bollinger Band calculations. | `BollingerV1ControllerConfig` | `controllers/directional_trading/bollinger_v1.py:31` |
| `bb_std` | `float` | no | 2.0 | Standard-deviation multiplier used to build the Bollinger Bands. | `BollingerV1ControllerConfig` | `controllers/directional_trading/bollinger_v1.py:34` |
| `bb_long_threshold` | `float` | no | 0.0 | Lower Bollinger-percent threshold that triggers a long/buy signal when price falls below it. | `BollingerV1ControllerConfig` | `controllers/directional_trading/bollinger_v1.py:35` |
| `bb_short_threshold` | `float` | no | 1.0 | Upper Bollinger-percent threshold that triggers a short/sell signal when price rises above it. | `BollingerV1ControllerConfig` | `controllers/directional_trading/bollinger_v1.py:36` |

## `bollinger_v2`

- Controller type: `directional_trading`
- Example controller: `no`
- Module: `controllers/directional_trading/bollinger_v2.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | bollinger_v2 | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `BollingerV2ControllerConfig` | `controllers/directional_trading/bollinger_v2.py:19` |
| `controller_type` | `string` | no | directional_trading | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:24` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:25` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:31` |
| `max_executors_per_side` | `integer` | no | 2 | Maximum number of concurrent executors the directional controller may keep open on each side (long/buy or short/sell). | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:37` |
| `cooldown_time` | `integer` | no | 60 * 5 | Minimum wait time between signal/executor creations or rebalance actions, depending on the controller. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:43` |
| `leverage` | `integer` | no | 1 | Leverage applied when the connector supports perpetual or margin trading. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:49` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:55` |
| `stop_loss` | `decimal or null` | no | 0.03 | Relative loss threshold that closes an executor/position when exceeded. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:60` |
| `take_profit` | `decimal or null` | no | 0.02 | Relative profit threshold that closes an executor/position when reached. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:66` |
| `time_limit` | `integer or null` | no | 60 * 45 | Maximum time in seconds that an executor/position may remain open before it is closed. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:72` |
| `take_profit_order_type` | `integer (OrderType enum: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER)` | no | 2 | Integer enum for the order type used when placing the take-profit exit order. Values: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:78` |
| `trailing_stop` | `TrailingStop or null` | no | null | Trailing-stop configuration. In prompts this is entered as `activation_price,trailing_delta`; in YAML it can serialize as an object. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:84` |
| `trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `candles_connector` | `string` | no | null | Connector used as the candle-data source. If left blank/null, validators fall back to the main trading connector. | `BollingerV2ControllerConfig` | `controllers/directional_trading/bollinger_v2.py:20` |
| `candles_trading_pair` | `string` | no | null | Trading pair used as the candle-data source. If left blank/null, validators fall back to the main trading pair. | `BollingerV2ControllerConfig` | `controllers/directional_trading/bollinger_v2.py:25` |
| `interval` | `string` | no | 3m | Candle interval / analysis timeframe used for indicator calculations and signal generation. | `BollingerV2ControllerConfig` | `controllers/directional_trading/bollinger_v2.py:30` |
| `bb_length` | `integer` | no | 100 | Lookback length used for Bollinger Band calculations. | `BollingerV2ControllerConfig` | `controllers/directional_trading/bollinger_v2.py:35` |
| `bb_std` | `float` | no | 2.0 | Standard-deviation multiplier used to build the Bollinger Bands. | `BollingerV2ControllerConfig` | `controllers/directional_trading/bollinger_v2.py:38` |
| `bb_long_threshold` | `float` | no | 0.0 | Lower Bollinger-percent threshold that triggers a long/buy signal when price falls below it. | `BollingerV2ControllerConfig` | `controllers/directional_trading/bollinger_v2.py:39` |
| `bb_short_threshold` | `float` | no | 1.0 | Upper Bollinger-percent threshold that triggers a short/sell signal when price rises above it. | `BollingerV2ControllerConfig` | `controllers/directional_trading/bollinger_v2.py:40` |

## `bollingrid`

- Controller type: `directional_trading`
- Example controller: `no`
- Module: `controllers/directional_trading/bollingrid.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | bollingrid | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:18` |
| `controller_type` | `string` | no | directional_trading | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:24` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:25` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:31` |
| `max_executors_per_side` | `integer` | no | 2 | Maximum number of concurrent executors the directional controller may keep open on each side (long/buy or short/sell). | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:37` |
| `cooldown_time` | `integer` | no | 60 * 5 | Minimum wait time between signal/executor creations or rebalance actions, depending on the controller. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:43` |
| `leverage` | `integer` | no | 1 | Leverage applied when the connector supports perpetual or margin trading. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:49` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:55` |
| `stop_loss` | `decimal or null` | no | 0.03 | Relative loss threshold that closes an executor/position when exceeded. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:60` |
| `take_profit` | `decimal or null` | no | 0.02 | Relative profit threshold that closes an executor/position when reached. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:66` |
| `time_limit` | `integer or null` | no | 60 * 45 | Maximum time in seconds that an executor/position may remain open before it is closed. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:72` |
| `take_profit_order_type` | `integer (OrderType enum: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER)` | no | 2 | Integer enum for the order type used when placing the take-profit exit order. Values: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:78` |
| `trailing_stop` | `TrailingStop or null` | no | null | Trailing-stop configuration. In prompts this is entered as `activation_price,trailing_delta`; in YAML it can serialize as an object. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:84` |
| `trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `candles_connector` | `string` | no | null | Connector used as the candle-data source. If left blank/null, validators fall back to the main trading connector. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:19` |
| `candles_trading_pair` | `string` | no | null | Trading pair used as the candle-data source. If left blank/null, validators fall back to the main trading pair. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:24` |
| `interval` | `string` | no | 3m | Candle interval / analysis timeframe used for indicator calculations and signal generation. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:29` |
| `bb_length` | `integer` | no | 100 | Lookback length used for Bollinger Band calculations. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:34` |
| `bb_std` | `float` | no | 2.0 | Standard-deviation multiplier used to build the Bollinger Bands. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:37` |
| `bb_long_threshold` | `float` | no | 0.0 | Lower Bollinger-percent threshold that triggers a long/buy signal when price falls below it. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:38` |
| `bb_short_threshold` | `float` | no | 1.0 | Upper Bollinger-percent threshold that triggers a short/sell signal when price rises above it. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:39` |
| `grid_start_price_coefficient` | `float` | no | 0.25 | Multiplier of current Bollinger Band width used to place the grid start boundary away from the current price. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:42` |
| `grid_end_price_coefficient` | `float` | no | 0.75 | Multiplier of current Bollinger Band width used to place the grid end boundary away from the current price. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:45` |
| `grid_limit_price_coefficient` | `float` | no | 0.35 | Multiplier of current Bollinger Band width used to place the protective limit price beyond the grid. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:48` |
| `min_spread_between_orders` | `decimal` | no | 0.005 | Minimum spacing between neighboring grid/order levels. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:51` |
| `order_frequency` | `integer` | no | 2 | Minimum number of seconds between placing batches of new orders or grid levels. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:54` |
| `max_orders_per_batch` | `integer` | no | 1 | Maximum number of orders the controller will create in one batch/update cycle. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:57` |
| `min_order_amount_quote` | `decimal` | no | 6 | Minimum quote-currency notional that a single order/grid level is allowed to use. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:60` |
| `max_open_orders` | `integer` | no | 5 | Maximum number of simultaneous open orders/grid levels the controller allows. | `BollinGridControllerConfig` | `controllers/directional_trading/bollingrid.py:63` |

## `dman_v3`

- Controller type: `directional_trading`
- Example controller: `no`
- Module: `controllers/directional_trading/dman_v3.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | dman_v3 | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:20` |
| `controller_type` | `string` | no | directional_trading | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:24` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:25` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:31` |
| `max_executors_per_side` | `integer` | no | 2 | Maximum number of concurrent executors the directional controller may keep open on each side (long/buy or short/sell). | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:37` |
| `cooldown_time` | `integer` | no | 60 * 5 | Minimum wait time between signal/executor creations or rebalance actions, depending on the controller. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:43` |
| `leverage` | `integer` | no | 1 | Leverage applied when the connector supports perpetual or margin trading. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:49` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:55` |
| `stop_loss` | `decimal or null` | no | 0.03 | Relative loss threshold that closes an executor/position when exceeded. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:60` |
| `take_profit` | `decimal or null` | no | 0.02 | Relative profit threshold that closes an executor/position when reached. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:66` |
| `time_limit` | `integer or null` | no | 60 * 45 | Maximum time in seconds that an executor/position may remain open before it is closed. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:72` |
| `take_profit_order_type` | `integer (OrderType enum: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER)` | no | 2 | Integer enum for the order type used when placing the take-profit exit order. Values: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:78` |
| `trailing_stop` | `TrailingStop or null` | no | 0.015,0.005 | Trailing-stop configuration. In prompts this is entered as `activation_price,trailing_delta`; in YAML it can serialize as an object. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:42` |
| `trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `candles_connector` | `string` | no | null | Connector used as the candle-data source. If left blank/null, validators fall back to the main trading connector. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:21` |
| `candles_trading_pair` | `string` | no | null | Trading pair used as the candle-data source. If left blank/null, validators fall back to the main trading pair. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:26` |
| `interval` | `string` | no | 3m | Candle interval / analysis timeframe used for indicator calculations and signal generation. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:31` |
| `bb_length` | `integer` | no | 100 | Lookback length used for Bollinger Band calculations. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:36` |
| `bb_std` | `float` | no | 2.0 | Standard-deviation multiplier used to build the Bollinger Bands. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:39` |
| `bb_long_threshold` | `float` | no | 0.0 | Lower Bollinger-percent threshold that triggers a long/buy signal when price falls below it. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:40` |
| `bb_short_threshold` | `float` | no | 1.0 | Upper Bollinger-percent threshold that triggers a short/sell signal when price rises above it. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:41` |
| `dca_spreads` | `list[decimal]` | no | 0.001,0.018,0.15,0.25 | Per-level DCA spread multipliers. When `dynamic_order_spread` is true, each value multiplies current Bollinger Band width; otherwise each value is used directly. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:49` |
| `dca_amounts_pct` | `list[decimal]` | no | null | Per-level percentage weights for DCA sizing. Values are normalized across the defined DCA levels. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:57` |
| `dynamic_order_spread` | `boolean` | no | null | If true, D-Man V3 multiplies each configured DCA spread by half the current Bollinger Band width before placing orders. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:64` |
| `dynamic_target` | `boolean` | no | null | If true, D-Man V3 scales stop loss, take profit, and trailing-stop thresholds by the same volatility multiplier used for spread adjustment. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:67` |
| `activation_bounds` | `list[decimal] or null` | no | null | Optional price-distance bounds that gate when an executor or next order level is allowed to activate. | `DManV3ControllerConfig` | `controllers/directional_trading/dman_v3.py:70` |

## `macd_bb_v1`

- Controller type: `directional_trading`
- Example controller: `no`
- Module: `controllers/directional_trading/macd_bb_v1.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | macd_bb_v1 | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `MACDBBV1ControllerConfig` | `controllers/directional_trading/macd_bb_v1.py:15` |
| `controller_type` | `string` | no | directional_trading | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:24` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:25` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:31` |
| `max_executors_per_side` | `integer` | no | 2 | Maximum number of concurrent executors the directional controller may keep open on each side (long/buy or short/sell). | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:37` |
| `cooldown_time` | `integer` | no | 60 * 5 | Minimum wait time between signal/executor creations or rebalance actions, depending on the controller. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:43` |
| `leverage` | `integer` | no | 1 | Leverage applied when the connector supports perpetual or margin trading. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:49` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:55` |
| `stop_loss` | `decimal or null` | no | 0.03 | Relative loss threshold that closes an executor/position when exceeded. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:60` |
| `take_profit` | `decimal or null` | no | 0.02 | Relative profit threshold that closes an executor/position when reached. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:66` |
| `time_limit` | `integer or null` | no | 60 * 45 | Maximum time in seconds that an executor/position may remain open before it is closed. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:72` |
| `take_profit_order_type` | `integer (OrderType enum: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER)` | no | 2 | Integer enum for the order type used when placing the take-profit exit order. Values: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:78` |
| `trailing_stop` | `TrailingStop or null` | no | null | Trailing-stop configuration. In prompts this is entered as `activation_price,trailing_delta`; in YAML it can serialize as an object. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:84` |
| `trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `candles_connector` | `string` | no | null | Connector used as the candle-data source. If left blank/null, validators fall back to the main trading connector. | `MACDBBV1ControllerConfig` | `controllers/directional_trading/macd_bb_v1.py:16` |
| `candles_trading_pair` | `string` | no | null | Trading pair used as the candle-data source. If left blank/null, validators fall back to the main trading pair. | `MACDBBV1ControllerConfig` | `controllers/directional_trading/macd_bb_v1.py:21` |
| `interval` | `string` | no | 3m | Candle interval / analysis timeframe used for indicator calculations and signal generation. | `MACDBBV1ControllerConfig` | `controllers/directional_trading/macd_bb_v1.py:26` |
| `bb_length` | `integer` | no | 100 | Lookback length used for Bollinger Band calculations. | `MACDBBV1ControllerConfig` | `controllers/directional_trading/macd_bb_v1.py:31` |
| `bb_std` | `float` | no | 2.0 | Standard-deviation multiplier used to build the Bollinger Bands. | `MACDBBV1ControllerConfig` | `controllers/directional_trading/macd_bb_v1.py:34` |
| `bb_long_threshold` | `float` | no | 0.0 | Lower Bollinger-percent threshold that triggers a long/buy signal when price falls below it. | `MACDBBV1ControllerConfig` | `controllers/directional_trading/macd_bb_v1.py:35` |
| `bb_short_threshold` | `float` | no | 1.0 | Upper Bollinger-percent threshold that triggers a short/sell signal when price rises above it. | `MACDBBV1ControllerConfig` | `controllers/directional_trading/macd_bb_v1.py:36` |
| `macd_fast` | `integer` | no | 21 | Fast-period length used in MACD calculations. | `MACDBBV1ControllerConfig` | `controllers/directional_trading/macd_bb_v1.py:37` |
| `macd_slow` | `integer` | no | 42 | Slow-period length used in MACD calculations. | `MACDBBV1ControllerConfig` | `controllers/directional_trading/macd_bb_v1.py:40` |
| `macd_signal` | `integer` | no | 9 | Signal-period length used in MACD calculations. | `MACDBBV1ControllerConfig` | `controllers/directional_trading/macd_bb_v1.py:43` |

## `supertrend_v1`

- Controller type: `directional_trading`
- Example controller: `no`
- Module: `controllers/directional_trading/supertrend_v1.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | supertrend_v1 | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `SuperTrendConfig` | `controllers/directional_trading/supertrend_v1.py:15` |
| `controller_type` | `string` | no | directional_trading | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:24` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:25` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:31` |
| `max_executors_per_side` | `integer` | no | 2 | Maximum number of concurrent executors the directional controller may keep open on each side (long/buy or short/sell). | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:37` |
| `cooldown_time` | `integer` | no | 60 * 5 | Minimum wait time between signal/executor creations or rebalance actions, depending on the controller. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:43` |
| `leverage` | `integer` | no | 1 | Leverage applied when the connector supports perpetual or margin trading. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:49` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:55` |
| `stop_loss` | `decimal or null` | no | 0.03 | Relative loss threshold that closes an executor/position when exceeded. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:60` |
| `take_profit` | `decimal or null` | no | 0.02 | Relative profit threshold that closes an executor/position when reached. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:66` |
| `time_limit` | `integer or null` | no | 60 * 45 | Maximum time in seconds that an executor/position may remain open before it is closed. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:72` |
| `take_profit_order_type` | `integer (OrderType enum: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER)` | no | 2 | Integer enum for the order type used when placing the take-profit exit order. Values: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:78` |
| `trailing_stop` | `TrailingStop or null` | no | null | Trailing-stop configuration. In prompts this is entered as `activation_price,trailing_delta`; in YAML it can serialize as an object. | `DirectionalTradingControllerConfigBase` | `hummingbot/strategy_v2/controllers/directional_trading_controller_base.py:84` |
| `trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `candles_connector` | `string` | no | null | Connector used as the candle-data source. If left blank/null, validators fall back to the main trading connector. | `SuperTrendConfig` | `controllers/directional_trading/supertrend_v1.py:16` |
| `candles_trading_pair` | `string` | no | null | Trading pair used as the candle-data source. If left blank/null, validators fall back to the main trading pair. | `SuperTrendConfig` | `controllers/directional_trading/supertrend_v1.py:21` |
| `interval` | `string` | no | 3m | Candle interval / analysis timeframe used for indicator calculations and signal generation. | `SuperTrendConfig` | `controllers/directional_trading/supertrend_v1.py:26` |
| `length` | `integer` | no | 20 | Lookback length used by the indicator in this controller. | `SuperTrendConfig` | `controllers/directional_trading/supertrend_v1.py:29` |
| `multiplier` | `float` | no | 4.0 | Indicator multiplier used to widen or tighten the calculated bands/thresholds. | `SuperTrendConfig` | `controllers/directional_trading/supertrend_v1.py:32` |
| `percentage_threshold` | `float` | no | 0.01 | Extra percentage filter the Supertrend controller applies before acting on a signal. | `SuperTrendConfig` | `controllers/directional_trading/supertrend_v1.py:35` |

## `dman_maker_v2`

- Controller type: `market_making`
- Example controller: `no`
- Module: `controllers/market_making/dman_maker_v2.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | dman_maker_v2 | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `DManMakerV2Config` | `controllers/market_making/dman_maker_v2.py:20` |
| `controller_type` | `string` | no | market_making | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:21` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:22` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:28` |
| `buy_spreads` | `list[float]` | no | 0.01,0.02 | Buy-side distance(s) from the reference price. Each value represents one quote/order level. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:34` |
| `sell_spreads` | `list[float]` | no | 0.01,0.02 | Sell-side distance(s) from the reference price. Each value represents one quote/order level. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:40` |
| `buy_amounts_pct` | `list[decimal] or null` | no | null | Relative allocation weights for buy levels. The controller normalizes the values when converting them into quote amounts. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:46` |
| `sell_amounts_pct` | `list[decimal] or null` | no | null | Relative allocation weights for sell levels. The controller normalizes the values when converting them into quote amounts. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:52` |
| `executor_refresh_time` | `integer` | no | 60 * 5 | How long an existing executor/order level can live before the controller refreshes/replaces it. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:58` |
| `cooldown_time` | `integer` | no | 15 | Minimum wait time between signal/executor creations or rebalance actions, depending on the controller. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:64` |
| `leverage` | `integer` | no | 1 | Leverage applied when the connector supports perpetual or margin trading. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:70` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:76` |
| `stop_loss` | `decimal or null` | no | 0.03 | Relative loss threshold that closes an executor/position when exceeded. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:81` |
| `take_profit` | `decimal or null` | no | 0.02 | Relative profit threshold that closes an executor/position when reached. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:87` |
| `time_limit` | `integer or null` | no | 60 * 45 | Maximum time in seconds that an executor/position may remain open before it is closed. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:93` |
| `take_profit_order_type` | `integer (OrderType enum: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER)` | no | 2 | Integer enum for the order type used when placing the take-profit exit order. Values: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:99` |
| `trailing_stop` | `TrailingStop or null` | no | null | Trailing-stop configuration. In prompts this is entered as `activation_price,trailing_delta`; in YAML it can serialize as an object. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:105` |
| `trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `position_rebalance_threshold_pct` | `decimal` | no | 0.05 | Inventory deviation threshold, expressed as a fraction of required base inventory, that triggers a rebalance order. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:112` |
| `rebalance_cooldown_time` | `integer` | no | 60 | Cooldown in seconds after a rebalance attempt before another rebalance can be triggered. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:118` |
| `skip_rebalance` | `boolean` | no | false | If true, disables the spot inventory rebalance path in market-making controllers. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:124` |
| `use_wallet_balance` | `boolean` | no | false | If true, seed sell-side inventory from the wallet's available base balance instead of relying only on quote-side sizing. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:125` |
| `dca_spreads` | `list[decimal]` | no | 0.01,0.02,0.04,0.08 | Per-level DCA spread distances. These define where each DCA order is placed relative to the reference price. | `DManMakerV2Config` | `controllers/market_making/dman_maker_v2.py:23` |
| `dca_amounts` | `list[decimal]` | no | 0.1,0.2,0.4,0.8 | Relative DCA size weights for each market-making DCA level. The controller normalizes them when splitting total size across levels. | `DManMakerV2Config` | `controllers/market_making/dman_maker_v2.py:26` |
| `top_executor_refresh_time` | `float or null` | no | null | Optional shorter refresh time that applies only to the top/first executor level. | `DManMakerV2Config` | `controllers/market_making/dman_maker_v2.py:29` |
| `executor_activation_bounds` | `list[decimal] or null` | no | null | Optional activation-distance bounds passed to the DCA executor so deeper levels only activate when price moves far enough. | `DManMakerV2Config` | `controllers/market_making/dman_maker_v2.py:30` |

## `pmm_dynamic`

- Controller type: `market_making`
- Example controller: `no`
- Module: `controllers/market_making/pmm_dynamic.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | pmm_dynamic | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `PMMDynamicControllerConfig` | `controllers/market_making/pmm_dynamic.py:17` |
| `controller_type` | `string` | no | market_making | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:21` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:22` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:28` |
| `buy_spreads` | `list[float]` | no | 1,2,4 | Buy-side spread levels measured in units of current volatility (NATR-derived spread multiplier), not fixed raw percentages. | `PMMDynamicControllerConfig` | `controllers/market_making/pmm_dynamic.py:18` |
| `sell_spreads` | `list[float]` | no | 1,2,4 | Sell-side spread levels measured in units of current volatility (NATR-derived spread multiplier), not fixed raw percentages. | `PMMDynamicControllerConfig` | `controllers/market_making/pmm_dynamic.py:24` |
| `buy_amounts_pct` | `list[decimal] or null` | no | null | Relative allocation weights for buy levels. The controller normalizes the values when converting them into quote amounts. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:46` |
| `sell_amounts_pct` | `list[decimal] or null` | no | null | Relative allocation weights for sell levels. The controller normalizes the values when converting them into quote amounts. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:52` |
| `executor_refresh_time` | `integer` | no | 60 * 5 | How long an existing executor/order level can live before the controller refreshes/replaces it. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:58` |
| `cooldown_time` | `integer` | no | 15 | Minimum wait time between signal/executor creations or rebalance actions, depending on the controller. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:64` |
| `leverage` | `integer` | no | 1 | Leverage applied when the connector supports perpetual or margin trading. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:70` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:76` |
| `stop_loss` | `decimal or null` | no | 0.03 | Relative loss threshold that closes an executor/position when exceeded. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:81` |
| `take_profit` | `decimal or null` | no | 0.02 | Relative profit threshold that closes an executor/position when reached. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:87` |
| `time_limit` | `integer or null` | no | 60 * 45 | Maximum time in seconds that an executor/position may remain open before it is closed. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:93` |
| `take_profit_order_type` | `integer (OrderType enum: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER)` | no | 2 | Integer enum for the order type used when placing the take-profit exit order. Values: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:99` |
| `trailing_stop` | `TrailingStop or null` | no | null | Trailing-stop configuration. In prompts this is entered as `activation_price,trailing_delta`; in YAML it can serialize as an object. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:105` |
| `trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `position_rebalance_threshold_pct` | `decimal` | no | 0.05 | Inventory deviation threshold, expressed as a fraction of required base inventory, that triggers a rebalance order. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:112` |
| `rebalance_cooldown_time` | `integer` | no | 60 | Cooldown in seconds after a rebalance attempt before another rebalance can be triggered. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:118` |
| `skip_rebalance` | `boolean` | no | false | If true, disables the spot inventory rebalance path in market-making controllers. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:124` |
| `use_wallet_balance` | `boolean` | no | false | If true, seed sell-side inventory from the wallet's available base balance instead of relying only on quote-side sizing. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:125` |
| `candles_connector` | `string` | no | null | Connector used as the candle-data source. If left blank/null, validators fall back to the main trading connector. | `PMMDynamicControllerConfig` | `controllers/market_making/pmm_dynamic.py:30` |
| `candles_trading_pair` | `string` | no | null | Trading pair used as the candle-data source. If left blank/null, validators fall back to the main trading pair. | `PMMDynamicControllerConfig` | `controllers/market_making/pmm_dynamic.py:35` |
| `interval` | `string` | no | 3m | Candle interval / analysis timeframe used for indicator calculations and signal generation. | `PMMDynamicControllerConfig` | `controllers/market_making/pmm_dynamic.py:40` |
| `macd_fast` | `integer` | no | 21 | Fast-period length used in MACD calculations. | `PMMDynamicControllerConfig` | `controllers/market_making/pmm_dynamic.py:45` |
| `macd_slow` | `integer` | no | 42 | Slow-period length used in MACD calculations. | `PMMDynamicControllerConfig` | `controllers/market_making/pmm_dynamic.py:48` |
| `macd_signal` | `integer` | no | 9 | Signal-period length used in MACD calculations. | `PMMDynamicControllerConfig` | `controllers/market_making/pmm_dynamic.py:51` |
| `natr_length` | `integer` | no | 14 | Lookback length used for the NATR volatility indicator. | `PMMDynamicControllerConfig` | `controllers/market_making/pmm_dynamic.py:54` |

## `pmm_simple`

- Controller type: `market_making`
- Example controller: `no`
- Module: `controllers/market_making/pmm_simple.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | pmm_simple | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `PMMSimpleConfig` | `controllers/market_making/pmm_simple.py:11` |
| `controller_type` | `string` | no | market_making | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:21` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:22` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:28` |
| `buy_spreads` | `list[float]` | no | 0.01,0.02 | Buy-side distance(s) from the reference price. Each value represents one quote/order level. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:34` |
| `sell_spreads` | `list[float]` | no | 0.01,0.02 | Sell-side distance(s) from the reference price. Each value represents one quote/order level. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:40` |
| `buy_amounts_pct` | `list[decimal] or null` | no | null | Relative allocation weights for buy levels. The controller normalizes the values when converting them into quote amounts. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:46` |
| `sell_amounts_pct` | `list[decimal] or null` | no | null | Relative allocation weights for sell levels. The controller normalizes the values when converting them into quote amounts. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:52` |
| `executor_refresh_time` | `integer` | no | 60 * 5 | How long an existing executor/order level can live before the controller refreshes/replaces it. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:58` |
| `cooldown_time` | `integer` | no | 15 | Minimum wait time between signal/executor creations or rebalance actions, depending on the controller. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:64` |
| `leverage` | `integer` | no | 1 | Leverage applied when the connector supports perpetual or margin trading. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:70` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:76` |
| `stop_loss` | `decimal or null` | no | 0.03 | Relative loss threshold that closes an executor/position when exceeded. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:81` |
| `take_profit` | `decimal or null` | no | 0.02 | Relative profit threshold that closes an executor/position when reached. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:87` |
| `time_limit` | `integer or null` | no | 60 * 45 | Maximum time in seconds that an executor/position may remain open before it is closed. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:93` |
| `take_profit_order_type` | `integer (OrderType enum: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER)` | no | 2 | Integer enum for the order type used when placing the take-profit exit order. Values: 1=MARKET, 2=LIMIT, 3=LIMIT_MAKER. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:99` |
| `trailing_stop` | `TrailingStop or null` | no | null | Trailing-stop configuration. In prompts this is entered as `activation_price,trailing_delta`; in YAML it can serialize as an object. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:105` |
| `trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `position_rebalance_threshold_pct` | `decimal` | no | 0.05 | Inventory deviation threshold, expressed as a fraction of required base inventory, that triggers a rebalance order. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:112` |
| `rebalance_cooldown_time` | `integer` | no | 60 | Cooldown in seconds after a rebalance attempt before another rebalance can be triggered. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:118` |
| `skip_rebalance` | `boolean` | no | false | If true, disables the spot inventory rebalance path in market-making controllers. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:124` |
| `use_wallet_balance` | `boolean` | no | false | If true, seed sell-side inventory from the wallet's available base balance instead of relying only on quote-side sizing. | `MarketMakingControllerConfigBase` | `hummingbot/strategy_v2/controllers/market_making_controller_base.py:125` |

## `arbitrage_controller`

- Controller type: `generic`
- Example controller: `no`
- Module: `controllers/generic/arbitrage_controller.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | arbitrage_controller | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `ArbitrageControllerConfig` | `controllers/generic/arbitrage_controller.py:17` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:70` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `exchange_pair_1` | `ConnectorPair` | no | {connector_name: binance, trading_pair: SOL-USDT} | First market pair used by the arbitrage controller. | `ArbitrageControllerConfig` | `controllers/generic/arbitrage_controller.py:18` |
| `exchange_pair_1.connector_name` | `string` | no | — | Connector/exchange name for this market leg. | `ConnectorPair` | `hummingbot/strategy_v2/executors/data_types.py:41` |
| `exchange_pair_1.trading_pair` | `string` | no | — | Trading pair for this market leg. | `ConnectorPair` | `hummingbot/strategy_v2/executors/data_types.py:42` |
| `exchange_pair_2` | `ConnectorPair` | no | {connector_name: jupiter/router, trading_pair: SOL-USDC} | Second market pair used by the arbitrage controller. | `ArbitrageControllerConfig` | `controllers/generic/arbitrage_controller.py:19` |
| `exchange_pair_2.connector_name` | `string` | no | — | Connector/exchange name for this market leg. | `ConnectorPair` | `hummingbot/strategy_v2/executors/data_types.py:41` |
| `exchange_pair_2.trading_pair` | `string` | no | — | Trading pair for this market leg. | `ConnectorPair` | `hummingbot/strategy_v2/executors/data_types.py:42` |
| `min_profitability` | `decimal` | no | 0.01 | Minimum profitability threshold required before creating an executor or trade. | `ArbitrageControllerConfig` | `controllers/generic/arbitrage_controller.py:20` |
| `delay_between_executors` | `integer` | no | 10 | Minimum wait in seconds after a completed arbitrage before opening the next one. | `ArbitrageControllerConfig` | `controllers/generic/arbitrage_controller.py:21` |
| `max_executors_imbalance` | `integer` | no | 1 | Maximum allowed imbalance between long/buy-side and short/sell-side executors before the controller stops creating more on the dominant side. | `ArbitrageControllerConfig` | `controllers/generic/arbitrage_controller.py:22` |
| `rate_connector` | `string` | no | binance | Connector used to fetch extra FX/rate conversions needed for valuation and profitability checks. | `ArbitrageControllerConfig` | `controllers/generic/arbitrage_controller.py:23` |
| `quote_conversion_asset` | `string` | no | USDT | Common quote asset into which prices/profits are converted for cross-market comparison. | `ArbitrageControllerConfig` | `controllers/generic/arbitrage_controller.py:24` |

## `examples.basic_order_example`

- Controller type: `generic`
- Example controller: `yes`
- Module: `controllers/generic/examples/basic_order_example.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | examples.basic_order_example | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `BasicOrderExampleConfig` | `controllers/generic/examples/basic_order_example.py:10` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:70` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `BasicOrderExampleConfig` | `controllers/generic/examples/basic_order_example.py:11` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `BasicOrderExampleConfig` | `controllers/generic/examples/basic_order_example.py:12` |
| `side` | `enum string (BUY, SELL)` | no | BUY | Trade side used by the demo order controller (`BUY` or `SELL`). Allowed values / format: BUY, SELL. | `BasicOrderExampleConfig` | `controllers/generic/examples/basic_order_example.py:13` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `BasicOrderExampleConfig` | `controllers/generic/examples/basic_order_example.py:14` |
| `leverage` | `integer` | no | 20 | Leverage applied when the connector supports perpetual or margin trading. | `BasicOrderExampleConfig` | `controllers/generic/examples/basic_order_example.py:15` |
| `amount_quote` | `decimal` | no | 10 | Order notional in quote currency. | `BasicOrderExampleConfig` | `controllers/generic/examples/basic_order_example.py:16` |
| `order_frequency` | `integer` | no | 10 | Minimum number of seconds between placing batches of new orders or grid levels. | `BasicOrderExampleConfig` | `controllers/generic/examples/basic_order_example.py:17` |

## `examples.basic_order_open_close_example`

- Controller type: `generic`
- Example controller: `yes`
- Module: `controllers/generic/examples/basic_order_open_close_example.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | examples.basic_order_open_close_example | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `BasicOrderOpenCloseExampleConfig` | `controllers/generic/examples/basic_order_open_close_example.py:10` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `BasicOrderOpenCloseExampleConfig` | `controllers/generic/examples/basic_order_open_close_example.py:11` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `BasicOrderOpenCloseExampleConfig` | `controllers/generic/examples/basic_order_open_close_example.py:12` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `BasicOrderOpenCloseExampleConfig` | `controllers/generic/examples/basic_order_open_close_example.py:13` |
| `side` | `enum string (BUY, SELL)` | no | BUY | Opening trade side used by the demo open/close controller (`BUY` or `SELL`). Allowed values / format: BUY, SELL. | `BasicOrderOpenCloseExampleConfig` | `controllers/generic/examples/basic_order_open_close_example.py:14` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `BasicOrderOpenCloseExampleConfig` | `controllers/generic/examples/basic_order_open_close_example.py:15` |
| `leverage` | `integer` | no | 50 | Leverage applied when the connector supports perpetual or margin trading. | `BasicOrderOpenCloseExampleConfig` | `controllers/generic/examples/basic_order_open_close_example.py:16` |
| `close_order_delay` | `integer` | no | 10 | Delay in seconds between opening a position and submitting the closing order in the open/close example controller. | `BasicOrderOpenCloseExampleConfig` | `controllers/generic/examples/basic_order_open_close_example.py:17` |
| `open_short_to_close_long` | `boolean` | no | false | In the example controller, use an opposite-side short/open action to close a long position. | `BasicOrderOpenCloseExampleConfig` | `controllers/generic/examples/basic_order_open_close_example.py:18` |
| `close_partial_position` | `boolean` | no | false | In the example controller, close only part of the position instead of the full size. | `BasicOrderOpenCloseExampleConfig` | `controllers/generic/examples/basic_order_open_close_example.py:19` |
| `amount_quote` | `decimal` | no | 20 | Order notional in quote currency. | `BasicOrderOpenCloseExampleConfig` | `controllers/generic/examples/basic_order_open_close_example.py:20` |

## `examples.buy_three_times_example`

- Controller type: `generic`
- Example controller: `yes`
- Module: `controllers/generic/examples/buy_three_times_example.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | examples.buy_three_times_example | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `BuyThreeTimesExampleConfig` | `controllers/generic/examples/buy_three_times_example.py:11` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:70` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `BuyThreeTimesExampleConfig` | `controllers/generic/examples/buy_three_times_example.py:12` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `BuyThreeTimesExampleConfig` | `controllers/generic/examples/buy_three_times_example.py:13` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `BuyThreeTimesExampleConfig` | `controllers/generic/examples/buy_three_times_example.py:14` |
| `leverage` | `integer` | no | 20 | Leverage applied when the connector supports perpetual or margin trading. | `BuyThreeTimesExampleConfig` | `controllers/generic/examples/buy_three_times_example.py:15` |
| `amount_quote` | `decimal` | no | 10 | Order notional in quote currency. | `BuyThreeTimesExampleConfig` | `controllers/generic/examples/buy_three_times_example.py:16` |
| `order_frequency` | `integer` | no | 10 | Minimum number of seconds between placing batches of new orders or grid levels. | `BuyThreeTimesExampleConfig` | `controllers/generic/examples/buy_three_times_example.py:17` |

## `examples.candles_data_controller`

- Controller type: `generic`
- Example controller: `yes`
- Module: `controllers/generic/examples/candles_data_controller.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | examples.candles_data_controller | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `CandlesDataControllerConfig` | `controllers/generic/examples/candles_data_controller.py:14` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:70` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `candles_config` | `list[CandlesConfig]` | no | default_factory=lambda: [{connector: binance, trading_pair: ETH-USDT, interval: 1m, max_records: 1000}, {connector: binance, trading_pair... | List of candle subscriptions the example controller initializes and prints/monitors. | `CandlesDataControllerConfig` | `controllers/generic/examples/candles_data_controller.py:17` |
| `candles_config[].connector` | `string` | no | — | Connector from which candles should be fetched. | `CandlesConfig` | `hummingbot/data_feed/candles_feed/data_types.py:13` |
| `candles_config[].trading_pair` | `string` | no | — | Trading pair for the candle feed. | `CandlesConfig` | `hummingbot/data_feed/candles_feed/data_types.py:14` |
| `candles_config[].interval` | `string` | no | 5m | Candle interval/timeframe for that subscription. | `CandlesConfig` | `hummingbot/data_feed/candles_feed/data_types.py:15` |
| `candles_config[].max_records` | `integer` | no | 500 | Maximum number of candle rows to keep/load for that subscription. | `CandlesConfig` | `hummingbot/data_feed/candles_feed/data_types.py:16` |

## `examples.full_trading_example`

- Controller type: `generic`
- Example controller: `yes`
- Module: `controllers/generic/examples/full_trading_example.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | examples.full_trading_example | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `FullTradingExampleConfig` | `controllers/generic/examples/full_trading_example.py:11` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:70` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `FullTradingExampleConfig` | `controllers/generic/examples/full_trading_example.py:12` |
| `trading_pair` | `string` | no | ETH-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `FullTradingExampleConfig` | `controllers/generic/examples/full_trading_example.py:13` |
| `amount` | `decimal` | no | 0.1 | Base-asset size used for each demo order in the full trading example. | `FullTradingExampleConfig` | `controllers/generic/examples/full_trading_example.py:14` |
| `spread` | `decimal` | no | 0.002 | Relative distance from mid/reference price used when the example places buy and sell orders. | `FullTradingExampleConfig` | `controllers/generic/examples/full_trading_example.py:15` |
| `max_open_orders` | `integer` | no | 3 | Maximum number of simultaneous open orders/grid levels the controller allows. | `FullTradingExampleConfig` | `controllers/generic/examples/full_trading_example.py:16` |

## `examples.liquidations_monitor_controller`

- Controller type: `generic`
- Example controller: `yes`
- Module: `controllers/generic/examples/liquidations_monitor_controller.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | examples.liquidations_monitor_controller | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `LiquidationsMonitorControllerConfig` | `controllers/generic/examples/liquidations_monitor_controller.py:13` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:70` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `exchange` | `string` | no | binance_paper_trade | Exchange/connector being monitored by the example controller. | `LiquidationsMonitorControllerConfig` | `controllers/generic/examples/liquidations_monitor_controller.py:14` |
| `trading_pair` | `string` | no | BTC-USDT | Primary market used for connector initialization by the liquidation-monitor example. | `LiquidationsMonitorControllerConfig` | `controllers/generic/examples/liquidations_monitor_controller.py:15` |
| `liquidations_trading_pairs` | `list` | no | ['BTC-USDT', '1000PEPE-USDT', '1000BONK-USDT', 'HBAR-USDT'] | List of markets for which liquidation events are subscribed to and retained in memory. | `LiquidationsMonitorControllerConfig` | `controllers/generic/examples/liquidations_monitor_controller.py:16` |
| `max_retention_seconds` | `integer` | no | 10 | How long liquidation events are kept before they are dropped from the in-memory view. | `LiquidationsMonitorControllerConfig` | `controllers/generic/examples/liquidations_monitor_controller.py:17` |

## `examples.market_status_controller`

- Controller type: `generic`
- Example controller: `yes`
- Module: `controllers/generic/examples/market_status_controller.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | examples.market_status_controller | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `MarketStatusControllerConfig` | `controllers/generic/examples/market_status_controller.py:12` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:70` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `exchanges` | `list` | no | ['binance_paper_trade', 'kucoin_paper_trade', 'gate_io_paper_trade'] | List of exchanges/connectors whose order books and prices are shown by the monitoring example. | `MarketStatusControllerConfig` | `controllers/generic/examples/market_status_controller.py:13` |
| `trading_pairs` | `list` | no | ['ETH-USDT', 'BTC-USDT', 'POL-USDT', 'AVAX-USDT', 'WLD-USDT', 'DOGE-USDT', 'SHIB-USDT', 'XRP-USDT', 'SOL-USDT'] | List of markets shown by the market-status example. | `MarketStatusControllerConfig` | `controllers/generic/examples/market_status_controller.py:14` |

## `examples.price_monitor_controller`

- Controller type: `generic`
- Example controller: `yes`
- Module: `controllers/generic/examples/price_monitor_controller.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | examples.price_monitor_controller | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `PriceMonitorControllerConfig` | `controllers/generic/examples/price_monitor_controller.py:11` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:70` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `exchanges` | `list` | no | ['binance_paper_trade', 'kucoin_paper_trade', 'gate_io_paper_trade'] | List of exchanges/connectors whose prices are periodically logged by the monitoring example. | `PriceMonitorControllerConfig` | `controllers/generic/examples/price_monitor_controller.py:12` |
| `trading_pair` | `string` | no | ETH-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `PriceMonitorControllerConfig` | `controllers/generic/examples/price_monitor_controller.py:13` |
| `log_interval` | `integer` | no | 60 | Interval in seconds between status/price log messages. | `PriceMonitorControllerConfig` | `controllers/generic/examples/price_monitor_controller.py:14` |

## `grid_strike`

- Controller type: `generic`
- Example controller: `no`
- Module: `controllers/generic/grid_strike.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | grid_strike | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:20` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:19` |
| `total_amount_quote` | `decimal` | no | 1000 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:35` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `leverage` | `integer` | no | 20 | Leverage applied when the connector supports perpetual or margin trading. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:23` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:24` |
| `connector_name` | `string` | no | okx | Exchange/connector name that the controller uses for trading or market data. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:27` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:28` |
| `side` | `enum string (BUY, SELL)` | no | BUY | Grid direction to open when the price is inside bounds (`BUY` for long/bid-side grid, `SELL` for short/ask-side grid). Allowed values / format: BUY, SELL. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:29` |
| `start_price` | `decimal` | no | 0.38 | Lower boundary of the single grid that GridStrike will place once price is inside range. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:30` |
| `end_price` | `decimal` | no | 0.75 | Upper boundary of the single grid that GridStrike will place once price is inside range. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:31` |
| `limit_price` | `decimal` | no | 0.35 | Protective limit price associated with the GridStrike grid. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:32` |
| `min_spread_between_orders` | `decimal or null` | no | 0.001 | Minimum spacing between neighboring grid/order levels. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:36` |
| `min_order_amount_quote` | `decimal or null` | no | 5 | Minimum quote-currency notional that a single order/grid level is allowed to use. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:37` |
| `max_open_orders` | `integer` | no | 2 | Maximum number of simultaneous open orders/grid levels the controller allows. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:40` |
| `max_orders_per_batch` | `integer or null` | no | 1 | Maximum number of orders the controller will create in one batch/update cycle. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:41` |
| `order_frequency` | `integer` | no | 3 | Minimum number of seconds between placing batches of new orders or grid levels. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:42` |
| `activation_bounds` | `decimal or null` | no | null | Optional price-distance bounds that gate when an executor or next order level is allowed to activate. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:43` |
| `keep_position` | `boolean` | no | false | If true, the grid keeps the resulting inventory/position instead of forcing a full flatten after execution. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:44` |
| `triple_barrier_config` | `TripleBarrierConfig` | no | TripleBarrierConfig(take_profit=0.001, open_order_type=LIMIT_MAKER, take_profit_order_type=LIMIT_MAKER) | Nested triple-barrier risk settings passed directly into the generated grid executor. | `GridStrikeConfig` | `controllers/generic/grid_strike.py:47` |
| `triple_barrier_config.stop_loss` | `decimal or null` | no | null | Relative stop-loss threshold used by the executor. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:18` |
| `triple_barrier_config.take_profit` | `decimal or null` | no | null | Relative take-profit threshold used by the executor. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:19` |
| `triple_barrier_config.time_limit` | `integer or null` | no | null | Maximum runtime in seconds before the executor exits. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:20` |
| `triple_barrier_config.trailing_stop` | `TrailingStop or null` | no | null | Nested trailing-stop settings used by the executor. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:21` |
| `triple_barrier_config.trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `triple_barrier_config.trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `triple_barrier_config.open_order_type` | `enum string (OrderType)` | no | LIMIT | Order type used for the entry/opening order. Allowed values / format: OrderType enum. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:22` |
| `triple_barrier_config.take_profit_order_type` | `enum string (OrderType)` | no | MARKET | Order type used for the take-profit exit. Allowed values / format: OrderType enum. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:23` |
| `triple_barrier_config.stop_loss_order_type` | `enum string (OrderType)` | no | MARKET | Order type used for the stop-loss exit. Allowed values / format: OrderType enum. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:24` |
| `triple_barrier_config.time_limit_order_type` | `enum string (OrderType)` | no | MARKET | Order type used when closing because of the time limit. Allowed values / format: OrderType enum. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:25` |

## `hedge_asset`

- Controller type: `generic`
- Example controller: `no`
- Module: `controllers/generic/hedge_asset.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | hedge_asset | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:28` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:27` |
| `total_amount_quote` | `decimal` | no | Decimal(0) | Compatibility field inherited from the base controller. HedgeAsset sizes from spot balances and hedge ratio rather than from a quote budget. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:29` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `spot_connector_name` | `string` | no | binance | Spot connector from which the controller reads inventory that needs to be hedged. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:32` |
| `asset_to_hedge` | `string` | no | SOL | Spot asset symbol whose inventory the strategy hedges. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:33` |
| `hedge_connector_name` | `string` | no | binance_perpetual | Perpetual or hedge connector used to open the offsetting hedge position. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:36` |
| `hedge_trading_pair` | `string` | no | SOL-USDT | Perpetual market used to hedge the spot asset. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:37` |
| `leverage` | `integer` | no | 20 | Leverage applied when the connector supports perpetual or margin trading. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:38` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:39` |
| `hedge_ratio` | `decimal` | no | 0 | Target fraction of spot inventory to hedge on the perpetual market. `0` means no hedge and `1` means fully hedge the tracked spot balance. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:42` |
| `min_notional_size` | `float` | no | 10 | Minimum quote notional required before the controller will submit a hedge order. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:43` |
| `cooldown_time` | `float` | no | 10.0 | Minimum number of seconds between hedge adjustments. | `HedgeAssetConfig` | `controllers/generic/hedge_asset.py:44` |

## `lp_rebalancer`

- Controller type: `generic`
- Example controller: `no`
- Module: `controllers/generic/lp_rebalancer/lp_rebalancer.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | lp_rebalancer | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:26` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:25` |
| `total_amount_quote` | `decimal` | no | 50 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:36` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `integer enum (0=BOTH, 1=BUY, 2=SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: 0=BOTH, 1=BUY, 2=SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `candles_config` | `list[CandlesConfig]` | no | [] | List of candle-feed configurations that the controller should initialize. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:27` |
| `candles_config[].connector` | `string` | no | — | Connector from which candles should be fetched. | `CandlesConfig` | `hummingbot/data_feed/candles_feed/data_types.py:13` |
| `candles_config[].trading_pair` | `string` | no | — | Trading pair for the candle feed. | `CandlesConfig` | `hummingbot/data_feed/candles_feed/data_types.py:14` |
| `candles_config[].interval` | `string` | no | 5m | Candle interval/timeframe for that subscription. | `CandlesConfig` | `hummingbot/data_feed/candles_feed/data_types.py:15` |
| `candles_config[].max_records` | `integer` | no | 500 | Maximum number of candle rows to keep/load for that subscription. | `CandlesConfig` | `hummingbot/data_feed/candles_feed/data_types.py:16` |
| `connector_name` | `string` | no | meteora/clmm | Exchange/connector name that the controller uses for trading or market data. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:30` |
| `network` | `string` | no | solana-mainnet-beta | Network identifier used by the LP connector (for example Solana mainnet). | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:31` |
| `trading_pair` | `string` | no | — | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:32` |
| `pool_address` | `string` | no | — | On-chain LP pool address the controller should manage. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:33` |
| `side` | `integer enum (0=BOTH, 1=BUY, 2=SELL)` | no | 1 | LP side mode encoded as an integer: `0 = BOTH`, `1 = BUY`, `2 = SELL`. Allowed values / format: 0=BOTH, 1=BUY, 2=SELL. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:37` |
| `position_width_pct` | `decimal` | no | 0.5 | LP width setting used when calculating the lower/upper LP bounds around the current price. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:38` |
| `position_offset_pct` | `decimal` | no | 0.01 | Offset from current price used when computing LP bounds so single-sided positions start out of range. The code comments treat values as percent-style numbers (for example `0.1` means `0.1%`). | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:39` |
| `rebalance_seconds` | `integer` | no | 60 | How long price must remain out of range before the LP controller rebalances. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:46` |
| `rebalance_threshold_pct` | `decimal` | no | 0.1 | How far price must move beyond the LP range before the rebalance timer starts. The code comments treat values as percent-style numbers (for example `0.1` means `0.1%`, `2` means `2%`). | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:47` |
| `sell_price_max` | `decimal or null` | no | null | Upper hard ceiling for sell-side LP ranges/rebalances. If a computed threshold exceeds it, the controller will not rebalance further upward. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:56` |
| `sell_price_min` | `decimal or null` | no | null | Lower hard floor for sell-side LP ranges/rebalances. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:57` |
| `buy_price_max` | `decimal or null` | no | null | Upper hard ceiling for buy-side LP ranges/rebalances. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:58` |
| `buy_price_min` | `decimal or null` | no | null | Lower hard floor for buy-side LP ranges/rebalances. If a computed threshold falls below it, the controller will not rebalance further downward. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:59` |
| `strategy_type` | `integer or null` | no | null | Optional integer passed through to the LP executor/connector to select a connector-specific LP strategy mode. The repository does not document the numeric values. | `LPRebalancerConfig` | `controllers/generic/lp_rebalancer/lp_rebalancer.py:62` |

## `multi_grid_strike`

- Controller type: `generic`
- Example controller: `no`
- Module: `controllers/generic/multi_grid_strike.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | multi_grid_strike | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:31` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:30` |
| `total_amount_quote` | `decimal` | no | 1000 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:42` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `leverage` | `integer` | no | 20 | Leverage applied when the connector supports perpetual or margin trading. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:34` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:35` |
| `connector_name` | `string` | no | binance_perpetual | Exchange/connector name that the controller uses for trading or market data. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:38` |
| `trading_pair` | `string` | no | WLD-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:39` |
| `grids` | `list[GridConfig]` | no | default_factory=list | List of individual grid definitions. Each entry defines one independently managed grid under the same controller. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:45` |
| `grids[].grid_id` | `string` | no | — | Unique identifier for the individual grid. | `GridConfig` | `controllers/generic/multi_grid_strike.py:17` |
| `grids[].start_price` | `decimal` | no | — | Lower boundary of the individual grid. | `GridConfig` | `controllers/generic/multi_grid_strike.py:18` |
| `grids[].end_price` | `decimal` | no | — | Upper boundary of the individual grid. | `GridConfig` | `controllers/generic/multi_grid_strike.py:19` |
| `grids[].limit_price` | `decimal` | no | — | Protective limit price associated with the individual grid. | `GridConfig` | `controllers/generic/multi_grid_strike.py:20` |
| `grids[].side` | `enum string (BUY, SELL)` | no | — | Direction of the grid (`BUY` or `SELL`). Allowed values / format: BUY, SELL. | `GridConfig` | `controllers/generic/multi_grid_strike.py:21` |
| `grids[].amount_quote_pct` | `decimal` | no | — | Fraction of the controller's `total_amount_quote` allocated to this grid. | `GridConfig` | `controllers/generic/multi_grid_strike.py:22` |
| `grids[].enabled` | `boolean` | no | true | Whether this grid is active and should be managed by the controller. | `GridConfig` | `controllers/generic/multi_grid_strike.py:23` |
| `min_spread_between_orders` | `decimal or null` | no | 0.001 | Minimum spacing between neighboring grid/order levels. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:48` |
| `min_order_amount_quote` | `decimal or null` | no | 5 | Minimum quote-currency notional that a single order/grid level is allowed to use. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:49` |
| `max_open_orders` | `integer` | no | 2 | Maximum number of simultaneous open orders/grid levels the controller allows. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:52` |
| `max_orders_per_batch` | `integer or null` | no | 1 | Maximum number of orders the controller will create in one batch/update cycle. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:53` |
| `order_frequency` | `integer` | no | 3 | Minimum number of seconds between placing batches of new orders or grid levels. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:54` |
| `activation_bounds` | `decimal or null` | no | null | Optional per-controller activation-distance guard passed to each generated grid executor. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:55` |
| `keep_position` | `boolean` | no | false | If true, the grid keeps the resulting inventory/position instead of forcing a full flatten after execution. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:56` |
| `triple_barrier_config` | `TripleBarrierConfig` | no | TripleBarrierConfig(take_profit=0.001, open_order_type=LIMIT_MAKER, take_profit_order_type=LIMIT_MAKER) | Nested triple-barrier risk settings shared by every grid defined in `grids`. | `MultiGridStrikeConfig` | `controllers/generic/multi_grid_strike.py:59` |
| `triple_barrier_config.stop_loss` | `decimal or null` | no | null | Relative stop-loss threshold used by the executor. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:18` |
| `triple_barrier_config.take_profit` | `decimal or null` | no | null | Relative take-profit threshold used by the executor. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:19` |
| `triple_barrier_config.time_limit` | `integer or null` | no | null | Maximum runtime in seconds before the executor exits. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:20` |
| `triple_barrier_config.trailing_stop` | `TrailingStop or null` | no | null | Nested trailing-stop settings used by the executor. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:21` |
| `triple_barrier_config.trailing_stop.activation_price` | `decimal` | no | — | Profit distance/trigger at which the trailing stop becomes active. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:13` |
| `triple_barrier_config.trailing_stop.trailing_delta` | `decimal` | no | — | Distance the stop trails behind price once the trailing stop has activated. | `TrailingStop` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:14` |
| `triple_barrier_config.open_order_type` | `enum string (OrderType)` | no | LIMIT | Order type used for the entry/opening order. Allowed values / format: OrderType enum. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:22` |
| `triple_barrier_config.take_profit_order_type` | `enum string (OrderType)` | no | MARKET | Order type used for the take-profit exit. Allowed values / format: OrderType enum. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:23` |
| `triple_barrier_config.stop_loss_order_type` | `enum string (OrderType)` | no | MARKET | Order type used for the stop-loss exit. Allowed values / format: OrderType enum. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:24` |
| `triple_barrier_config.time_limit_order_type` | `enum string (OrderType)` | no | MARKET | Order type used when closing because of the time limit. Allowed values / format: OrderType enum. | `TripleBarrierConfig` | `hummingbot/strategy_v2/executors/position_executor/data_types.py:25` |

## `pmm_mister`

- Controller type: `generic`
- Example controller: `no`
- Module: `controllers/generic/pmm_mister.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | pmm_mister | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:21` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:20` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance | Exchange/connector name that the controller uses for trading or market data. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:22` |
| `trading_pair` | `string` | no | BTC-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:23` |
| `portfolio_allocation` | `decimal` | no | 0.1 | Fraction of total controller capital that PMMister is allowed to deploy in this market. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:24` |
| `target_base_pct` | `decimal` | no | 0.5 | Target share of portfolio value that should be held in the base asset. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:25` |
| `min_base_pct` | `decimal` | no | 0.3 | Lower bound of desired base-inventory share used by inventory-skew logic. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:26` |
| `max_base_pct` | `decimal` | no | 0.7 | Upper bound of desired base-inventory share used by inventory-skew logic. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:27` |
| `buy_spreads` | `list[float]` | no | 0.0005 | Buy-side distance(s) from the reference price. Each value represents one quote/order level. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:28` |
| `sell_spreads` | `list[float]` | no | 0.0005 | Sell-side distance(s) from the reference price. Each value represents one quote/order level. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:29` |
| `buy_amounts_pct` | `list[decimal] or null` | no | 1 | Relative allocation weights for buy levels. The controller normalizes the values when converting them into quote amounts. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:30` |
| `sell_amounts_pct` | `list[decimal] or null` | no | 1 | Relative allocation weights for sell levels. The controller normalizes the values when converting them into quote amounts. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:31` |
| `executor_refresh_time` | `integer` | no | 30 | How long an existing executor/order level can live before the controller refreshes/replaces it. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:32` |
| `buy_cooldown_time` | `integer` | no | 60 | Minimum time between refreshing/creating buy-side PMMister levels. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:35` |
| `sell_cooldown_time` | `integer` | no | 60 | Minimum time between refreshing/creating sell-side PMMister levels. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:36` |
| `buy_position_effectivization_time` | `integer` | no | 120 | How long PMMister waits before treating a buy-side position/order as effective for control logic. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:37` |
| `sell_position_effectivization_time` | `integer` | no | 120 | How long PMMister waits before treating a sell-side position/order as effective for control logic. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:38` |
| `price_distance_tolerance` | `decimal` | no | 0.0005 | Minimum distance from current price required before PMMister will place another order at the same level. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:41` |
| `refresh_tolerance` | `decimal` | no | 0.0005 | Reference-price drift required before PMMister refreshes/replaces an existing order. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:43` |
| `tolerance_scaling` | `decimal` | no | 1.2 | Per-level multiplier applied to PMMister distance/refresh tolerances for deeper levels. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:44` |
| `leverage` | `integer` | no | 20 | Leverage applied when the connector supports perpetual or margin trading. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:46` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | ONEWAY | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:47` |
| `take_profit` | `decimal or null` | no | 0.0001 | Relative profit threshold that closes an executor/position when reached. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:48` |
| `take_profit_order_type` | `enum string (OrderType)` | no | LIMIT_MAKER | Order type used when placing the take-profit exit order. Allowed values / format: OrderType enum. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:49` |
| `open_order_type` | `enum string (OrderType)` | no | LIMIT_MAKER | Order type used for opening positions/orders. Allowed values / format: OrderType enum. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:50` |
| `max_active_executors_by_level` | `integer or null` | no | 4 | Maximum number of simultaneously active PMMister executors allowed for a single level. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:51` |
| `tick_mode` | `boolean` | no | false | If true, PMMister measures spreads in exchange tick-size increments instead of raw percentages. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:52` |
| `position_profit_protection` | `boolean` | no | false | If true, PMMister avoids placing sell orders below breakeven and uses breakeven-aware inventory controls. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:53` |
| `min_skew` | `decimal` | no | 1.0 | Minimum inventory-skew factor PMMister will apply so order sizes do not collapse to zero. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:54` |
| `global_take_profit` | `decimal` | no | 0.03 | Portfolio/controller-level PnL take-profit threshold for PMMister. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:55` |
| `global_stop_loss` | `decimal` | no | 0.05 | Portfolio/controller-level PnL stop-loss threshold for PMMister. | `PMMisterConfig` | `controllers/generic/pmm_mister.py:56` |

## `pmm_v1`

- Controller type: `generic`
- Example controller: `no`
- Module: `controllers/generic/pmm_v1.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | pmm_v1 | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `PMMV1Config` | `controllers/generic/pmm_v1.py:34` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `PMMV1Config` | `controllers/generic/pmm_v1.py:33` |
| `total_amount_quote` | `decimal` | no | 0 | Compatibility field inherited from the base controller. PMM V1 sizes orders with `order_amount` in base units, so this value is effectively unused. | `PMMV1Config` | `controllers/generic/pmm_v1.py:54` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_name` | `string` | no | binance | Exchange/connector name that the controller uses for trading or market data. | `PMMV1Config` | `controllers/generic/pmm_v1.py:37` |
| `trading_pair` | `string` | no | BTC-USDT | Market symbol the controller trades or monitors, in `BASE-QUOTE` form. | `PMMV1Config` | `controllers/generic/pmm_v1.py:44` |
| `order_amount` | `decimal` | no | 1 | Per-order amount. In PMM V1 this is expressed in base asset units. | `PMMV1Config` | `controllers/generic/pmm_v1.py:56` |
| `buy_spreads` | `list[float]` | no | 0.01 | Buy-side distance(s) from the reference price. Each value represents one quote/order level. | `PMMV1Config` | `controllers/generic/pmm_v1.py:63` |
| `sell_spreads` | `list[float]` | no | 0.01 | Sell-side distance(s) from the reference price. Each value represents one quote/order level. | `PMMV1Config` | `controllers/generic/pmm_v1.py:70` |
| `order_refresh_time` | `integer` | no | 30 | Time in seconds after which an existing order should be refreshed/replaced. | `PMMV1Config` | `controllers/generic/pmm_v1.py:79` |
| `order_refresh_tolerance_pct` | `decimal` | no | -1 | Allowed price drift before an existing order is refreshed. A sentinel value may disable the check. | `PMMV1Config` | `controllers/generic/pmm_v1.py:86` |
| `filled_order_delay` | `integer` | no | 60 | Delay in seconds after a fill before the controller places replacement orders. | `PMMV1Config` | `controllers/generic/pmm_v1.py:93` |
| `inventory_skew_enabled` | `boolean` | no | false | If true, order sizes are skewed to steer inventory back toward the target base/quote mix. | `PMMV1Config` | `controllers/generic/pmm_v1.py:102` |
| `target_base_pct` | `decimal` | no | 0.5 | Target share of portfolio value that should be held in the base asset. | `PMMV1Config` | `controllers/generic/pmm_v1.py:109` |
| `inventory_range_multiplier` | `decimal` | no | 1.0 | Multiplier used when converting inventory deviation into skewed order-size adjustments. | `PMMV1Config` | `controllers/generic/pmm_v1.py:116` |
| `price_ceiling` | `decimal` | no | -1 | Static upper price cap. Above this value the controller only allows sells; a negative sentinel disables the cap. | `PMMV1Config` | `controllers/generic/pmm_v1.py:125` |
| `price_floor` | `decimal` | no | -1 | Static lower price floor. Below this value the controller only allows buys; a negative sentinel disables the floor. | `PMMV1Config` | `controllers/generic/pmm_v1.py:132` |

## `quantum_grid_allocator`

- Controller type: `generic`
- Example controller: `no`
- Module: `controllers/generic/quantum_grid_allocator.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | quantum_grid_allocator | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:18` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:70` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `long_only_threshold` | `decimal` | no | 0.2 | Negative-deviation threshold below which the allocator enters a long-only zone for that asset. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:21` |
| `short_only_threshold` | `decimal` | no | 0.2 | Positive-deviation threshold above which the allocator enters a short-only zone for that asset. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:22` |
| `hedge_ratio` | `decimal` | no | 2 | Relative hedge sizing between opposing hedge-zone grids; used when balancing buy/sell grid exposure around the theoretical allocation. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:23` |
| `base_grid_value_pct` | `decimal` | no | 0.08 | Base percentage of theoretical asset value used when sizing a grid. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:26` |
| `max_grid_value_pct` | `decimal` | no | 0.15 | Larger grid-size percentage used when the allocation deviation exceeds the configured max-deviation threshold. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:27` |
| `safe_extra_spread` | `decimal` | no | 0.0001 | Additional safety spread applied inside the grid executor so orders are not placed too aggressively. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:30` |
| `favorable_order_frequency` | `integer` | no | 2 | Order creation frequency used when the grid setup is considered favorable. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:31` |
| `unfavorable_order_frequency` | `integer` | no | 5 | Slower order creation frequency used when the setup is considered unfavorable. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:32` |
| `max_orders_per_batch` | `integer` | no | 1 | Maximum number of orders the controller will create in one batch/update cycle. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:33` |
| `portfolio_allocation` | `object/map[str, Decimal]` | no | {'SOL': 0.50} | Per-asset target allocation map. Keys are asset symbols and values are target fractions of total portfolio value; the remaining fraction is implicitly quote asset. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:36` |
| `portfolio_allocation.<asset_symbol>` | `decimal` | no | example default: SOL=0.50 | One entry in the allocation map. The key is an asset symbol and the value is that asset’s target share of total portfolio value. Allowed values / format: keys = asset symbols; values = allocation fractions. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:36` |
| `grid_range` | `decimal` | no | 0.002 | Base grid half-range / width used to place grid boundaries around the reference price. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:42` |
| `tp_sl_ratio` | `decimal` | no | 0.8 | Take-profit versus stop-loss weighting used when splitting grid range between the two sides. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:43` |
| `min_order_amount` | `decimal` | no | 5 | Minimum notional size allowed for a single order or a single grid level. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:44` |
| `max_deviation` | `decimal` | no | 0.05 | Deviation threshold beyond which the controller switches to a larger grid size or otherwise treats the imbalance as more urgent. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:46` |
| `max_open_orders` | `integer` | no | 2 | Maximum number of simultaneous open orders/grid levels the controller allows. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:47` |
| `connector_name` | `string` | no | binance | Exchange/connector name that the controller uses for trading or market data. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:49` |
| `leverage` | `integer` | no | 1 | Leverage applied when the connector supports perpetual or margin trading. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:50` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:51` |
| `quote_asset` | `string` | no | USDT | Quote asset used for valuation and to build per-asset markets (for example `SOL-USDT`). | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:52` |
| `fee_asset` | `string` | no | BNB | Fee token tracked for valuation purposes when running the allocator on an exchange like Binance. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:53` |
| `min_spread_between_orders` | `decimal` | no | 0.0001 | Minimum spacing between neighboring grid/order levels. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:55` |
| `grid_tp_multiplier` | `decimal` | no | 0.0001 | Take-profit distance used inside generated grid executors. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:58` |
| `limit_price_spread` | `decimal` | no | 0.001 | Extra spread used to place the limit price slightly beyond the main grid boundary. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:62` |
| `activation_bounds` | `decimal` | no | 0.0002 | Activation-distance guard passed into the generated grid executor. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:65` |
| `bb_length` | `integer` | no | 100 | Lookback length used for Bollinger Band calculations. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:68` |
| `bb_std_dev` | `float` | no | 2.0 | Standard-deviation multiplier used by QGA when it computes Bollinger Band width for dynamic ranges. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:69` |
| `interval` | `string` | no | 1s | Candle interval / analysis timeframe used for indicator calculations and signal generation. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:70` |
| `dynamic_grid_range` | `boolean` | no | false | If true, compute grid width from current Bollinger Band width instead of a fixed `grid_range`. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:71` |
| `show_terminated_details` | `boolean` | no | false | Whether status output should include extra detail for terminated grids/executors. | `QGAConfig` | `controllers/generic/quantum_grid_allocator.py:72` |

## `stat_arb`

- Controller type: `generic`
- Example controller: `no`
- Module: `controllers/generic/stat_arb.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | stat_arb | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `StatArbConfig` | `controllers/generic/stat_arb.py:21` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `StatArbConfig` | `controllers/generic/stat_arb.py:20` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `connector_pair_dominant` | `ConnectorPair` | no | {connector_name: binance_perpetual, trading_pair: SOL-USDT} | Dominant leg in the statistical arbitrage pair. | `StatArbConfig` | `controllers/generic/stat_arb.py:22` |
| `connector_pair_dominant.connector_name` | `string` | no | — | Connector/exchange name for this market leg. | `ConnectorPair` | `hummingbot/strategy_v2/executors/data_types.py:41` |
| `connector_pair_dominant.trading_pair` | `string` | no | — | Trading pair for this market leg. | `ConnectorPair` | `hummingbot/strategy_v2/executors/data_types.py:42` |
| `connector_pair_hedge` | `ConnectorPair` | no | {connector_name: binance_perpetual, trading_pair: POPCAT-USDT} | Hedge leg in the statistical arbitrage pair. | `StatArbConfig` | `controllers/generic/stat_arb.py:23` |
| `connector_pair_hedge.connector_name` | `string` | no | — | Connector/exchange name for this market leg. | `ConnectorPair` | `hummingbot/strategy_v2/executors/data_types.py:41` |
| `connector_pair_hedge.trading_pair` | `string` | no | — | Trading pair for this market leg. | `ConnectorPair` | `hummingbot/strategy_v2/executors/data_types.py:42` |
| `interval` | `string` | no | 1m | Candle interval / analysis timeframe used for indicator calculations and signal generation. | `StatArbConfig` | `controllers/generic/stat_arb.py:24` |
| `lookback_period` | `integer` | no | 300 | Historical lookback window used to estimate the statistical arbitrage model and z-score. | `StatArbConfig` | `controllers/generic/stat_arb.py:25` |
| `entry_threshold` | `decimal` | no | 2.0 | Absolute z-score threshold required before a stat-arb entry signal is generated. | `StatArbConfig` | `controllers/generic/stat_arb.py:26` |
| `take_profit` | `decimal` | no | 0.0008 | Relative profit threshold that closes an executor/position when reached. | `StatArbConfig` | `controllers/generic/stat_arb.py:27` |
| `tp_global` | `decimal` | no | 0.01 | Global pair-level take-profit threshold. If pair PnL exceeds this, the controller closes both legs. | `StatArbConfig` | `controllers/generic/stat_arb.py:28` |
| `sl_global` | `decimal` | no | 0.05 | Global pair-level stop-loss threshold. If pair PnL falls below this, the controller closes both legs. | `StatArbConfig` | `controllers/generic/stat_arb.py:29` |
| `min_amount_quote` | `decimal` | no | 10 | Minimum quote notional used when sizing a single quoter/order action. | `StatArbConfig` | `controllers/generic/stat_arb.py:30` |
| `quoter_spread` | `decimal` | no | 0.0001 | Extra spread applied around the best/min/max price when placing stat-arb quoting orders. | `StatArbConfig` | `controllers/generic/stat_arb.py:31` |
| `quoter_cooldown` | `integer` | no | 30 | Minimum age before a filled/placed stat-arb executor can be replaced on the same side. | `StatArbConfig` | `controllers/generic/stat_arb.py:32` |
| `quoter_refresh` | `integer` | no | 10 | Refresh interval for placed stat-arb quoters that have not yet traded. | `StatArbConfig` | `controllers/generic/stat_arb.py:33` |
| `max_orders_placed_per_side` | `integer` | no | 2 | Maximum number of active placed stat-arb orders allowed per side/leg. | `StatArbConfig` | `controllers/generic/stat_arb.py:34` |
| `max_orders_filled_per_side` | `integer` | no | 2 | Maximum number of already-filled stat-arb executors allowed per side/leg. | `StatArbConfig` | `controllers/generic/stat_arb.py:35` |
| `max_position_deviation` | `decimal` | no | 0.1 | Maximum tolerated imbalance between dominant and hedge legs before the controller stops adding to the overrepresented side. | `StatArbConfig` | `controllers/generic/stat_arb.py:36` |
| `pos_hedge_ratio` | `decimal` | no | 1.0 | Target hedge ratio between dominant and hedge leg exposures. | `StatArbConfig` | `controllers/generic/stat_arb.py:37` |
| `leverage` | `integer` | no | 20 | Leverage applied when the connector supports perpetual or margin trading. | `StatArbConfig` | `controllers/generic/stat_arb.py:38` |
| `position_mode` | `enum string (HEDGE, ONEWAY)` | no | HEDGE | Perpetual position mode. Typical values are `HEDGE` and `ONEWAY`. Allowed values / format: HEDGE, ONEWAY. | `StatArbConfig` | `controllers/generic/stat_arb.py:39` |

## `xemm_multiple_levels`

- Controller type: `generic`
- Example controller: `no`
- Module: `controllers/generic/xemm_multiple_levels.py`

| Field path | Type | Required | Default | What it does | Defined in | Source |
|---|---|---:|---|---|---|---|
| `id` | `string` | yes | required | Unique identifier for this controller instance. Other strategy components use it to route executor actions and reports. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:68` |
| `controller_name` | `string` | no | xemm_multiple_levels | Controller module name. This must match the controller implementation and is used when loading the controller from the YAML file. | `XEMMMultipleLevelsConfig` | `controllers/generic/xemm_multiple_levels.py:18` |
| `controller_type` | `string` | no | generic | Controller family used for grouping/loading the controller. In this repo the main families are generic, directional_trading, and market_making. Allowed values / format: generic, directional_trading, market_making. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:70` |
| `total_amount_quote` | `decimal` | no | 100 | Total budget in quote currency that the controller uses when sizing positions, grids, or quote-side order allocations. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:71` |
| `manual_kill_switch` | `boolean` | no | false | Manual per-controller stop flag. In the `v2_with_controllers` script, setting this to true stops the controller and issues StopExecutor actions for its executors; clearing it allows restart. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:79` |
| `initial_positions` | `list[InitialPositionConfig]` | no | [] | List of pre-existing positions that the controller should adopt and manage at startup instead of assuming a flat book. | `ControllerConfigBase` | `hummingbot/strategy_v2/controllers/controller_base.py:80` |
| `initial_positions[].connector_name` | `string` | no | — | Connector on which the pre-existing position exists. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:15` |
| `initial_positions[].trading_pair` | `string` | no | — | Trading pair of the pre-existing position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:16` |
| `initial_positions[].amount` | `decimal` | no | — | Base-asset amount currently held in that initial position. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:17` |
| `initial_positions[].side` | `enum string (BUY, SELL)` | no | — | Direction of the initial position (`BUY` for long/base inventory, `SELL` for short inventory). Allowed values / format: BUY, SELL. | `InitialPositionConfig` | `hummingbot/strategy_v2/models/position_config.py:18` |
| `maker_connector` | `string` | no | mexc | Connector used for the maker side in cross-exchange market making. | `XEMMMultipleLevelsConfig` | `controllers/generic/xemm_multiple_levels.py:19` |
| `maker_trading_pair` | `string` | no | PEPE-USDT | Trading pair used on the maker connector. | `XEMMMultipleLevelsConfig` | `controllers/generic/xemm_multiple_levels.py:22` |
| `taker_connector` | `string` | no | binance | Connector used for the taker/hedging side in cross-exchange market making. | `XEMMMultipleLevelsConfig` | `controllers/generic/xemm_multiple_levels.py:25` |
| `taker_trading_pair` | `string` | no | PEPE-USDT | Trading pair used on the taker connector. | `XEMMMultipleLevelsConfig` | `controllers/generic/xemm_multiple_levels.py:28` |
| `buy_levels_targets_amount` | `list[list[decimal]]` | no | 0.003,10-0.006,20-0.009,30 | List of buy-side `[target_profitability, level_amount]` pairs. In prompts it is entered as `profit,amount-profit,amount`. | `XEMMMultipleLevelsConfig` | `controllers/generic/xemm_multiple_levels.py:31` |
| `sell_levels_targets_amount` | `list[list[decimal]]` | no | 0.003,10-0.006,20-0.009,30 | List of sell-side `[target_profitability, level_amount]` pairs. In prompts it is entered as `profit,amount-profit,amount`. | `XEMMMultipleLevelsConfig` | `controllers/generic/xemm_multiple_levels.py:36` |
| `min_profitability` | `decimal` | no | 0.003 | Minimum profitability threshold required before creating an executor or trade. | `XEMMMultipleLevelsConfig` | `controllers/generic/xemm_multiple_levels.py:41` |
| `max_profitability` | `decimal` | no | 0.01 | Upper profitability band above the target profitability that still allows an executor to trade. | `XEMMMultipleLevelsConfig` | `controllers/generic/xemm_multiple_levels.py:44` |
| `max_executors_imbalance` | `integer` | no | 1 | Maximum allowed imbalance between long/buy-side and short/sell-side executors before the controller stops creating more on the dominant side. | `XEMMMultipleLevelsConfig` | `controllers/generic/xemm_multiple_levels.py:47` |
