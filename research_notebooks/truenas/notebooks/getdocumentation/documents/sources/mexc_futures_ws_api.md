_Source: https://www.mexc.com/api-docs/futures/websocket-api_

_Fetched: 2026-04-04T04:30:24.683481Z_

WebSocket API | MEXC API







[Skip to main content](#__docusaurus_skipToContent_fallback)

[![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)](https://www.mexc.com/)[SpotV3](/api-docs/spot-v3/introduction)[Futures](/api-docs/futures/update-log)[Broker](/api-docs/broker/mexc-broker-introduction)

[English](#)

* [English](/api-docs/futures/websocket-api)
* [中文](/zh-MY/api-docs/futures/websocket-api)

* [Update log](/api-docs/futures/update-log)
* [Integration Guide](/api-docs/futures/integration-guide)
* [Internationalization Support](/api-docs/futures/error-code)
* [Market Endpoints](/api-docs/futures/market-endpoints)
* [Account and Trading Endpoints](/api-docs/futures/account-and-trading-endpoints)
* [WebSocket API](/api-docs/futures/websocket-api)

On this page

WebSocket API
=============

WebSocket is a new HTML5 protocol that enables full-duplex communication between client and server, allowing data to flow quickly in both directions. A simple handshake establishes the connection; after that, the server can proactively push messages to the client based on business rules. Benefits:

1. Very small header overhead during data transfer (about 2 bytes).
2. Both client and server can actively send data to each other.
3. No repeated TCP connection setup/teardown—saves bandwidth and server resources.

We strongly recommend developers use the WebSocket API to obtain market quotes and order book depth.

Native ws endpoint[​](#native-ws-endpoint "Direct link to Native ws endpoint")
------------------------------------------------------------------------------

* wss://contract.mexc.com/edge

Command details for data exchange[​](#command-details-for-data-exchange "Direct link to Command details for data exchange")
---------------------------------------------------------------------------------------------------------------------------

> Send ping

```
{  
  "method": "ping"  
}
```

> Server response

```
{  
  "channel": "pong",  
  "data": 1587453241453  
}
```

Subscribe/unsubscribe command list (except personal/private commands, all others do **not** require WS auth).

If no ping is received from the client within 1 minute, the connection will be closed. Send a ping every 10–20 seconds.

Subscription filtering[​](#subscription-filtering "Direct link to Subscription filtering")
------------------------------------------------------------------------------------------

> Disable default pushes

```
{  
  "subscribe": false,  
  "method": "login",  
  "param": {  
    "apiKey": "mxU1TzSmRDW1o5AsE",  
    "signature": "8c957a757ea31672eca05cb652d26bab7f46a41364adb714dda5475264aff120",  
    "reqTime": "1611038237237"  
  }  
}
```

> Only assets

```
{  
  "method": "personal.filter",  
  "param": {  
    "filters": [  
      {  
        "filter": "asset"  
      }  
    ]  
  }  
}
```

> Only ADL level

```
{  
  "method": "personal.filter",  
  "param": {  
    "filters": [  
      {  
        "filter": "adl.level"  
      }  
    ]  
  }  
}
```

> All fills only

```
{  
  "method": "personal.filter",  
  "param": {  
    "filters": [  
      {  
        "filter": "order.deal",  
        "rules": []  
      }  
    ]  
  }  
}
```

> Or

```
{  
  "method": "personal.filter",  
  "param": {  
    "filters": [  
      {  
        "filter": "order.deal"  
      }  
    ]  
  }  
}
```

> Fills for a single contract only

```
{  
  "method": "personal.filter",  
  "param": {  
    "filters": [  
      {  
        "filter": "order.deal",  
        "rules": ["BTC_USDT"]  
      }  
    ]  
  }  
}
```

> Mixed usage

```
{  
  "method": "personal.filter",  
  "param": {  
    "filters": [  
      {  
        "filter": "order",  
        "rules": ["BTC_USDT"]  
      },  
      {  
        "filter": "order.deal",  
        "rules": ["EOS_USDT", "ETH_USDT", "BTC_USDT"]  
      },  
      {  
        "filter": "position",  
        "rules": ["EOS_USDT", "BTC_USDT"]  
      },  
      {  
        "filter": "asset"  
      }  
    ]  
  }  
}
```

After login, all personal data will be pushed by default: `order` (orders), `order.deal` (fills), `position` (positions), `plan.order` (plan orders), `stop.order` (TP/SL orders), `stop.planorder` (TP/SL plan orders), `risk.limit` (risk limits), `adl.level` (ADL level), `asset` (assets).

1. To cancel default pushes, add `"subscribe": false` to the login params (default is `true`).
2. After login, send the `personal.filter` event to filter what you need. To restore all pushes, send `{"method":"personal.filter"}` or `{"method":"personal.filter","param":{"filters":[]}}`.
3. Valid `filter` keys (fixed values; errors if incorrect): `order`, `order.deal`, `position`, `plan.order`, `stop.order`, `stop.planorder`, `risk.limit`, `adl.level`, `asset`.

`asset` and `adl.level` do not support per-symbol filtering; others can filter by a single contract.

Subsequent `filter` events overwrite previous ones.

Public channels[​](#public-channels "Direct link to Public channels")
---------------------------------------------------------------------

### Tickers[​](#tickers "Direct link to Tickers")

> Subscribe

```
{  
  "method": "sub.tickers",  
  "param": {}  
}
```

> If you need plaintext responses (same for other subs):

```
{  
  "method": "sub.tickers",  
  "param": {},  
  "gzip": false  
}
```

> Unsubscribe

```
{  
  "method": "unsub.tickers",  
  "param": {}  
}
```

> Sample data

```
{  
  "channel": "push.tickers",  
  "data": [  
    {  
      "fairPrice": 183.01,  
      "lastPrice": 183,  
      "riseFallRate": -0.0708,  
      "symbol": "BSV_USDT",  
      "volume24": 200,  
      "maxBidPrice": 7073.42,  
      "minAskPrice": 6661.37  
    },  
    {  
      "fairPrice": 220.22,  
      "lastPrice": 220.4,  
      "riseFallRate": -0.0686,  
      "symbol": "BCH_USDT",  
      "volume24": 200,  
      "maxBidPrice": 7073.42,  
      "minAskPrice": 6661.37  
    }  
  ]  
}
```

Get latest price, best bid/ask, and 24h volume for all perpetual contracts. No login required. Pushes every 2s.

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| timestamp | long | Trade time |
| lastPrice | decimal | Last price |
| volume24 | decimal | 24h volume (in contracts) |
| amount24 | decimal | 24h turnover (in currency) |
| riseFallRate | decimal | Change rate |
| fairPrice | decimal | Fair price |
| indexPrice | decimal | Index price |
| maxBidPrice | decimal | Max buy price |
| minAskPrice | decimal | Min sell price |
| lower24Price | decimal | 24h low |
| high24Price | decimal | 24h high |

### Get a single ticker[​](#get-a-single-ticker "Direct link to Get a single ticker")

> Subscribe

```
{  
  "method": "sub.ticker",  
  "param": {  
    "symbol": "BTC_USDT"  
  }  
}
```

> Unsubscribe

```
{  
  "method": "unsub.ticker",  
  "param": {  
    "symbol": "BTC_USDT"  
  }  
}
```

> Sample data

```
{  
  "channel": "push.ticker",  
  "data": {  
    "ask1": 6866.5,  
    "bid1": 6865,  
    "contractId": 1,  
    "fairPrice": 6867.4,  
    "fundingRate": 0.0008,  
    "high24Price": 7223.5,  
    "indexPrice": 6861.6,  
    "lastPrice": 6865.5,  
    "lower24Price": 6756,  
    "maxBidPrice": 7073.42,  
    "minAskPrice": 6661.37,  
    "riseFallRate": -0.0424,  
    "riseFallValue": -304.5,  
    "symbol": "BTC_USDT",  
    "timestamp": 1587442022003,  
    "holdVol": 2284742,  
    "volume24": 164586129  
  },  
  "symbol": "BTC_USDT"  
}
```

Get latest price, best bid/ask, and 24h volume for a given contract. No login required. Pushes every 1s when trades occur.

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| timestamp | long | Trade time |
| lastPrice | decimal | Last price |
| bid1 | decimal | Best bid |
| ask1 | decimal | Best ask |
| holdVol | decimal | Open interest |
| fundingRate | decimal | Funding rate |
| riseFallRate | decimal | Change rate |
| riseFallValue | decimal | Change amount |
| volume24 | decimal | 24h volume (contracts) |
| amount24 | decimal | 24h turnover (currency) |
| fairPrice | decimal | Fair price |
| indexPrice | decimal | Index price |
| maxBidPrice | decimal | Max buy price |
| minAskPrice | decimal | Min sell price |
| lower24Price | decimal | 24h low |
| high24Price | decimal | 24h high |

### Deal[​](#deal "Direct link to Deal")

> Subscribe

```
{  
  "method": "sub.deal",  
  "param": {  
    "symbol": "BTC_USDT"  
  }  
}
```

> Unsubscribe

```
{  
  "method": "unsub.deal",  
  "param": {  
    "symbol": "BTC_USDT"  
  }  
}
```

> Sample data

```
{  
  "symbol": "BTC_USDT",  
  "data": [  
    {  
      "p": 115309.8,  
      "v": 55,  
      "T": 2,  
      "O": 3,  
      "M": 1,  
      "t": 1755487578276,  
      "i": 13064218826  
    },  
    {  
      "p": 115309.8,  
      "v": 11,  
      "T": 1,  
      "O": 3,  
      "M": 1,  
      "t": 1755487578275,  
      "i": 13064218827  
    }  
  ],  
  "channel": "push.deal",  
  "ts": 1755487578276  
}
```

Receive recent trades. No login required. Pushed whenever trades occur. Trade stream enables aggregation by default; to disable, set `compress=false` in the subscription.

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| p | decimal | Price |
| v | decimal | Quantity |
| T | int | Trade side: 1 buy, 2 sell |
| O | int | Open/close flag: 1 new position, 2 reduce position, 3 position unchanged. If `O=1`, `v` is the added position size |
| M | int | Self-trade: 1 yes, 2 no |
| i | int | Transaction ID |
| t | long | Trade time |

### Order book depth[​](#order-book-depth "Direct link to Order book depth")

> Subscribe

```
{  
  "method": "sub.depth",  
  "param": {  
    "symbol": "BTC_USDT"  
  }  
}
```

> Unsubscribe

```
{  
  "method": "unsub.depth",  
  "param": {  
    "symbol": "BTC_USDT"  
  }  
}
```

> Sample data

```
{  
  "channel": "push.depth",  
  "data": {  
    "asks": [[6859.5, 3251, 1]],  
    "bids": [],  
    "version": 96801927  
  },  
  "symbol": "BTC_USDT",  
  "ts": 1587442022003  
}
```

Receive depth data for a specific contract; after subscribing, updates are pushed every 200 ms.

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| asks | `List<Numeric[]>` | Ask depth |
| bids | `List<Numeric[]>` | Bid depth |
| version | long | Version |

Note: `[411.8, 10, 1]` → 411.8 is price，10 is the order numbers of the contract ,1 is the order quantity

### Depth — specify minimum notional step[​](#depth--specify-minimum-notional-step "Direct link to Depth — specify minimum notional step")

> Subscribe

```
{ "method": "sub.depth.step", "param": { "symbol": "BTC_USDT", "step": "10" } }
```

Note: `10` means notional bucket size of 10; e.g., levels like 100010, 100020, 100030.

> Unsubscribe

```
{  
  "method": "unsub.depth.step",  
  "param": { "symbol": "BTC_USDT", "step": "10" }  
}
```

> Sample data

```
{  
  "channel": "push.depth.step",  
  "data": {  
    "askMarketLevelPrice": 111089.4,  
    "asks": [  
      [111090, 398676, 26],  
      [111100, 410175, 8]  
    ],  
    "bidMarketLevelPrice": 111085.5,  
    "bids": [  
      [111080, 461204, 35],  
      [111070, 386809, 3]  
    ],  
    "ct": 1760950364388,  
    "version": 27883254360  
  },  
  "symbol": "BTC_USDT"  
}
```

Receive depth data for contracts with a specified minimum notional step; after subscribing, updates are pushed every 200 ms.

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| asks | `List<Numeric[]>` | Ask depth |
| bids | `List<Numeric[]>` | Bid depth |
| askMarketLevelPrice | decimal | Highest willing ask |
| bidMarketLevelPrice | decimal | Highest willing bid |
| version | long | Version |

Note: `[111090,398676,26]` → 111090 is price，398676 is the order numbers of the contract ,26 is the order quantity

### K-line data[​](#k-line-data "Direct link to K-line data")

> Subscribe

```
{  
  "method": "sub.kline",  
  "param": {  
    "symbol": "BTC_USDT",  
    "interval": "Min60"  
  },  
  "gzip": false  
}
```

> Unsubscribe

```
{  
  "method": "unsub.kline",  
  "param": {  
    "symbol": "BTC_USDT"  
  }  
}
```

> Sample data

```
{  
  "channel": "push.kline",  
  "data": {  
    "a": 233.740269343644737245,  
    "c": 6885,  
    "h": 6910.5,  
    "interval": "Min60",  
    "l": 6885,  
    "o": 6894.5,  
    "q": 1611754,  
    "symbol": "BTC_USDT",  
    "t": 1587448800  
  },  
  "symbol": "BTC_USDT"  
}
```

Receive K-line updates as they occur.

`interval` options: Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1, Week1, Month1

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| interval | string | Interval: Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1, Week1, Month1 |
| a | decimal | Total traded amount |
| q | decimal | Total traded volume |
| o | decimal | Open |
| c | decimal | Close |
| h | decimal | High |
| l | decimal | Low |
| v | decimal | Total volume |
| ro | decimal | Real open |
| rc | decimal | Real close |
| rh | decimal | Real high |
| rl | decimal | Real low |
| t | long | Trade time in seconds (window start) |

### Funding rate[​](#funding-rate "Direct link to Funding rate")

> Subscribe

```
{  
  "method": "sub.funding.rate",  
  "param": {  
    "symbol": "BTC_USDT"  
  },  
  "gzip": false  
}
```

> Unsubscribe

```
{  
  "method": "unsub.funding.rate",  
  "param": {  
    "symbol": "BTC_USDT"  
  }  
}
```

> Sample data

```
{  
  "channel": "push.funding.rate",  
  "data": {  
    "rate": 0.001,  
    "symbol": "BTC_USDT"  
  },  
  "symbol": "BTC_USDT",  
  "ts": 1587442022003  
}
```

Get funding rate updates.

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| fundingRate | decimal | Funding rate |
| nextSettleTime | long | Next settlement |

### Index price[​](#index-price "Direct link to Index price")

> Subscribe

For both linear and inverse contracts, use the same `symbol` (e.g., for inverse BTC\_USD, use `BTC_USDT` when subscribing to index price).

```
{  
  "method": "sub.index.price",  
  "param": {  
    "symbol": "BTC_USDT"  
  },  
  "gzip": false  
}
```

> Unsubscribe

```
{  
  "method": "unsub.index.price",  
  "param": {  
    "symbol": "BTC_USDT"  
  }  
}
```

> Sample data

```
{  
  "channel": "push.index.price",  
  "data": {  
    "price": 0.001,  
    "symbol": "BTC_USDT"  
  },  
  "symbol": "BTC_USDT",  
  "ts": 1587442022003  
}
```

Get the contract’s index price; updates are pushed whenever there are changes.

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| price | decimal | Price |

### Fair price[​](#fair-price "Direct link to Fair price")

> Subscribe

```
{  
  "method": "sub.fair.price",  
  "param": {  
    "symbol": "BTC_USDT"  
  },  
  "gzip": false  
}
```

> Unsubscribe

```
{  
  "method": "unsub.fair.price",  
  "param": {  
    "symbol": "BTC_USDT"  
  }  
}
```

> Sample data

```
{  
  "channel": "push.fair.price",  
  "data": {  
    "price": 0.001,  
    "symbol": "BTC_USDT"  
  },  
  "symbol": "BTC_USDT",  
  "ts": 1587442022003  
}
```

Get the contract’s fair price; updates are pushed whenever there are changes.

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| price | decimal | Price |

### Contract data[​](#contract-data "Direct link to Contract data")

> Subscribe

```
{ "method": "sub.contract" }
```

> Unsubscribe

```
{ "method": "unsub.contract" }
```

> Sample data

```
{  
  "channel": "push.contract",  
  "data": {  
    "amountScale": 4,  
    "askLimitPriceRate": 0.2,  
    "baseCoin": "CLO",  
    "baseCoinName": "CLO",  
    "bidLimitPriceRate": 0.2,  
    "conceptPlate": [],  
    "conceptPlateId": [],  
    "contractSize": 10,  
    "depthStepList": ["0.0001", "0.001", "0.01", "0.1"],  
    "displayName": "CLO_USDT永续",  
    "displayNameEn": "CLO_USDT PERPETUAL",  
    "feeRateMode": "NORMAL",  
    "futureType": 1,  
    "indexOrigin": ["MEXC_FUTURE", "MEXC", "KUCOIN"],  
    "initialMarginRate": 0.02,  
    "isHidden": false,  
    "isHot": false,  
    "isNew": false,  
    "liquidationFeeRate": 0.0002,  
    "limitMaxVol": 9000,  
    "maintenanceMarginRate": 0.01,  
    "makerFeeRate": 0,  
    "maxLeverage": 50,  
    "maxNumOrders": [200, 50],  
    "maxVol": 9000,  
    "minLeverage": 1,  
    "minVol": 1,  
    "openingCountdownOption": 1,  
    "openingTime": 1760440200000,  
    "positionOpenType": 3,  
    "priceCoefficientVariation": 0.4,  
    "priceScale": 4,  
    "priceUnit": 0.0001,  
    "quoteCoin": "USDT",  
    "quoteCoinName": "USDT",  
    "riskBaseVol": 9000,  
    "riskIncrImr": 0.005,  
    "riskIncrMmr": 0.005,  
    "riskIncrVol": 9000,  
    "riskLevelLimit": 1,  
    "riskLimitMode": "INCREASE",  
    "riskLimitType": "BY_VOLUME",  
    "riskLongShortSwitch": 0,  
    "settleCoin": "USDT",  
    "state": 0,  
    "symbol": "CLO_USDT",  
    "takerFeeRate": 0.0002,  
    "triggerProtect": 0.1,  
    "volScale": 0,  
    "volUnit": 1  
  },  
  "symbol": "CLO_USDT",  
  "ts": 1760942212002  
}
```

Get contract data; updates are pushed whenever there are changes.

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Contract, e.g., BTC\_USDT |
| displayName | string | Display name, e.g., BTC\_USDT 永续 |
| displayNameEn | string | Display English name, e.g., BTC\_USDT PERPETUAL |
| positionOpenType | int | Open mode: 1 both cross & isolated; 2 cross; 3 isolated |
| baseCoin | string | Base currency (e.g., BTC) |
| quoteCoin | string | Quote currency (e.g., USDT) |
| baseCoinName | string | Base currency name |
| quoteCoinName | string | Quote currency name |
| futureType | int | 1 PERPETUAL, 2 DAILY |
| settleCoin | string | Settlement currency |
| contractSize | decimal | Contract size |
| minLeverage | int | Min leverage |
| maxLeverage | int | Max leverage |
| priceScale | int | Price decimals |
| volScale | int | Volume decimals |
| amountScale | int | Amount decimals |
| priceUnit | decimal | Min price tick |
| volUnit | decimal | Min volume step |
| minVol | decimal | Min order size (contracts) |
| maxVol | decimal | Max order size (contracts) |
| limitMaxVol | decimal | Max size for limit orders |
| bidLimitPriceRate | decimal | Order price limit—seller |
| askLimitPriceRate | decimal | Order price limit—buyer |
| takerFeeRate | decimal | Taker fee |
| makerFeeRate | decimal | Maker fee |
| maintenanceMarginRate | decimal | Maintenance margin rate |
| initialMarginRate | decimal | Initial margin rate |
| riskBaseVol | decimal | Base contracts for risk limit |
| riskIncrVol | decimal | Incremental contracts |
| riskIncrMmr | decimal | MMR increment |
| riskIncrImr | decimal | IMR increment |
| riskLevelLimit | decimal | Number of risk tiers |
| priceCoefficientVariation | decimal | Fair vs index price deviation coefficient |
| state | int | 0 enabled, 1 deliver, 2 delivered, 3 delist, 4 paused |
| isNew | boolean | New contract tag |
| isHot | boolean | Hot contract tag |
| isHidden | boolean | Hidden contract |
| triggerProtect | decimal | Price protection threshold |
| riskLongShortSwitch | int | Separate long/short risk limits (0 off, 1 on) |
| riskBaseVolLong | decimal | Long base contracts |
| riskIncrVolLong | decimal | Long incremental contracts |
| riskBaseVolShort | decimal | Short base contracts |
| riskIncrVolShort | decimal | Short incremental contracts |
| openingCountdownOption | int | Opening countdown option 1 - Display opening time and countdown 2 - Display opening time only 3 - Hide both opening time and countdown |
| openingTime | long | Opening timestamp |
| liquidationFeeRate | decimal | Liquidation fee rate |
| tieredDealAmount | decimal | Tiered turnover amount |
| tieredEffectiveDay | int | Effective days |
| tieredExcludeZeroFee | boolean | Exclude zero-fee turnover? (false no, true yes) |
| tieredAppointContract | boolean | Specify contracts? (false no, true yes) |
| tieredExcludeContractId | boolean | Include/exclude contracts (false exclude, true include) |

### Event contracts[​](#event-contracts "Direct link to Event contracts")

> Subscribe

```
{ "method": "sub.event.contract" }
```

> Unsubscribe

```
{ "method": "unsub.event.contract" }
```

Get event contract data; updates are pushed whenever there are changes.

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| contractId | string | Contract ID |
| symbol | string | Contract, e.g., BTC\_USDT |
| baseCoin | string | Base currency, e.g., BTC |
| quoteCoin | string | Quote currency, e.g., USDT |
| baseCoinName | string | Base currency name |
| quoteCoinName | string | Quote currency name |
| settleCoin | string | Settlement currency |
| baseCoinIconUrl | string | Base currency |
| baseCoinName | string | Base currency icon config |
| investMinAmount | decimal | Minimum investment |
| investMaxAmount | decimal | Maximum investment |
| amountScale | int | Quantity precision |
| payRateScale | int | Payout rate precision |
| indexPriceScale | int | Index price precision |
| availableScale | int | Availability precision |

Private channels[​](#private-channels "Direct link to Private channels")
------------------------------------------------------------------------

**Signature method:**

Concatenate `api_key` and `req_time`, then HMAC-SHA256 with `sec_key`. `api_key` and `sec_key` are your ACCESS KEY and SECRET KEY.

### Signature string[​](#signature-string "Direct link to Signature string")

`"mx0aBYs33eIilxBW5C1657186536762"`

### Login authentication[​](#login-authentication "Direct link to Login authentication")

> Example

```
{  
  "method": "login",  
  "param": {  
    "token": "token", // web & app must provide token to complete auth  
    "apiKey": "apiKey", // for openapi; construct per openapi docs  
    "reqTime": "reqTime", // for openapi; construct per openapi docs  
    "signature": "signature" // for openapi; construct per openapi docs  
  }  
}
```

**Response:**

> Example

```
{ "channel": "rs.login", "data": "success", "ts": "1587442022003" }
```

Success: none. Failure: return error info, `channel = rs.error`.

On success: `channel = rs.login`.

### Order[​](#order "Direct link to Order")

> Sample

```
{  
  "channel": "push.personal.order",  
  "data": {  
    "orderId": 123456789,  
    "symbol": "BTC_USDT",  
    "positionId": 987654321,  
    "price": 45000.5,  
    "vol": 10,  
    "leverage": 20,  
    "side": 1,  
    "category": 1,  
    "orderType": 1,  
    "dealAvgPrice": 45000.0,  
    "dealVol": 5,  
    "orderMargin": 2250.0,  
    "usedMargin": 1125.0,  
    "takerFee": 0.1125,  
    "makerFee": 0.09,  
    "profit": 0,  
    "feeCurrency": "USDT",  
    "openType": 1,  
    "state": 2,  
    "errorCode": 0,  
    "externalOid": "ext_001",  
    "createTime": 1760942212000,  
    "updateTime": 1760942212000,  
    "remainVol": 5,  
    "positionMode": 1,  
    "reduceOnly": false,  
    "bboTypeNum": 0,  
    "makerFeeRate": 0.0002,  
    "takerFeeRate": 0.0004  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.order`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| orderId | long | Order ID |
| symbol | string | Contract |
| positionId | long | Position ID |
| price | decimal | Order price |
| vol | decimal | Order quantity |
| leverage | long | Leverage |
| side | int | 1 open long, 2 close short, 3 open short, 4 close long |
| category | int | 1 limit, 2 forced liquidation custody, 3 custody close, 4 ADL |
| orderType | int | 1 limit, 2 Post Only, 3 IOC, 4 FOK, 5 market, 6 market-to-limit |
| dealAvgPrice | decimal | Average fill price |
| dealVol | decimal | Filled quantity |
| orderMargin | decimal | Order margin |
| usedMargin | decimal | Used margin |
| takerFee | decimal | Taker fee |
| makerFee | decimal | Maker fee |
| profit | decimal | Close PnL |
| feeCurrency | string | Fee currency |
| openType | int | 1 isolated, 2 cross |
| state | int | 1 pending, 2 open, 3 filled, 4 canceled, 5 invalid |
| errorCode | int | ENUM:errorCode |
| externalOid | string | External order ID |
| createTime | long | Create time |
| updateTime | long | Update time |
| remainVol | decimal | Remaining quantity |
| positionMode | int | Position mode |
| reduceOnly | boolean | Reduce-only |
| bboTypeNum | int | BBO limit order subtype |
| makerFeeRate | decimal | Maker fee rate |
| takerFeeRate | decimal | Taker fee rate |

### Assets[​](#assets "Direct link to Assets")

> Sample

```
{  
  "channel": "push.personal.asset",  
  "data": {  
    "currency": "USDT",  
    "positionMargin": 5000.0,  
    "frozenBalance": 1000.0,  
    "availableBalance": 9000.0,  
    "bonus": 100.0  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.asset`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| currency | string | Currency |
| positionMargin | decimal | Position margin |
| frozenBalance | decimal | Frozen balance |
| availableBalance | decimal | Currently available balance |
| bonus | decimal | Trial bonus |

### Position[​](#position "Direct link to Position")

> Sample

```
{  
  "channel": "push.personal.position",  
  "data": {  
    "positionId": 123456789,  
    "symbol": "BTC_USDT",  
    "holdVol": 10,  
    "positionType": 1,  
    "openType": 1,  
    "state": 1,  
    "frozenVol": 0,  
    "closeVol": 0,  
    "holdAvgPrice": 45000.5,  
    "holdAvgPriceFullyScale": "45000.500000000000000000",  
    "closeAvgPrice": 0,  
    "openAvgPrice": 45000.5,  
    "openAvgPriceFullyScale": "45000.500000000000000000",  
    "liquidatePrice": 40000.0,  
    "oim": 2250.025,  
    "adlLevel": 1,  
    "im": 2250.025,  
    "holdFee": 0,  
    "realised": 0,  
    "leverage": 20,  
    "autoAddIm": false,  
    "pnl": 100.5,  
    "marginRatio": 0.2,  
    "newOpenAvgPrice": 45000.5,  
    "newCloseAvgPrice": 0,  
    "closeProfitLoss": 0,  
    "fee": 0,  
    "deductFeeList": [  
      {  
        "currency": "USDT",  
        "deductFee": 0.1125,  
        "convertSettleFee": 0.1125  
      }  
    ],  
    "makerFeeRate": 0.0002,  
    "takerFeeRate": 0.0004,  
    "createTime": 1760942212000,  
    "updateTime": 1760942212000,  
    "version": 1  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.position`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| positionId | long | Position ID |
| symbol | string | Contract |
| holdVol | decimal | Position size |
| positionType | int | 1 long, 2 short |
| openType | int | 1 isolated, 2 cross |
| state | int | 1 holding, 2 system custody, 3 closed |
| frozenVol | decimal | Frozen quantity |
| closeVol | decimal | Closed quantity |
| holdAvgPrice | decimal | Position average price |
| holdAvgPriceFullyScale | string | Full-precision position avg price |
| closeAvgPrice | decimal | Close average price |
| openAvgPrice | decimal | Open average price |
| openAvgPriceFullyScale | string | Full-precision open avg price |
| liquidatePrice | decimal | Liquidation price (isolated) |
| oim | decimal | Original initial margin |
| adlLevel | int | ADL level |
| im | decimal | Initial margin (adjustable in isolated to tune liq price) |
| holdFee | decimal | Funding fee (positive received, negative paid) |
| realised | decimal | Realized PnL |
| leverage | int | Leverage |
| autoAddIm | boolean | Auto-add margin |
| pnl | decimal | Unrealized PnL |
| marginRatio | decimal | Margin ratio |
| newOpenAvgPrice | decimal | Open average price |
| newCloseAvgPrice | decimal | Close average price |
| closeProfitLoss | decimal | Close PnL |
| fee | decimal | Fee |
| deductFeeList | array | Deduction info |
| makerFeeRate | decimal | Maker fee rate |
| takerFeeRate | decimal | Taker fee rate |
| createTime | long | Create time |
| updateTime | long | Update time |
| version | long | Version |

### Deduction info[​](#deduction-info "Direct link to Deduction info")

> Sample

```
{  
  "channel": "push.personal.plan.order",  
  "data": {  
    "currency": "USDT",  
    "deductFee": 0.1125,  
    "convertSettleFee": 0.1125  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.position`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| currency | string | Deduction currency |
| deductFee | decimal | Fee in deduction currency |
| convertSettleFee | decimal | Fee converted to settlement currency |

### Plan orders[​](#plan-orders "Direct link to Plan orders")

> Sample

```
{  
  "channel": "push.personal.plan.order",  
  "data": {  
    "id": 987654321,  
    "symbol": "BTC_USDT",  
    "leverage": 20,  
    "side": 1,  
    "triggerPrice": 46000.0,  
    "price": 45990.0,  
    "vol": 5,  
    "openType": 1,  
    "triggerType": 1,  
    "state": 1,  
    "executeCycle": 24,  
    "trend": 1,  
    "errorCode": 0,  
    "orderId": 0,  
    "orderType": 1,  
    "marketOrderLevel": 0,  
    "positionMode": 1,  
    "lossTrend": 1,  
    "profitTrend": 1,  
    "stopLossPrice": 44000.0,  
    "takeProfitPrice": 47000.0,  
    "reduceOnly": false,  
    "createTime": 1760942212000,  
    "updateTime": 1760942212000  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.plan.order`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| id | long | Order ID |
| symbol | string | Contract |
| leverage | int | Leverage |
| side | int | 1 open long, 2 close short, 3 open short, 4 close long |
| triggerPrice | decimal | Trigger price |
| price | decimal | Execution price |
| vol | decimal | Quantity |
| openType | int | 1 isolated, 2 cross |
| triggerType | int | 1 ≥, 2 ≤ |
| state | int | 1 untriggered, 2 canceled, 3 executed, 4 expired, 5 execution failed |
| executeCycle | int | Execution cycle (hours) |
| trend | int | Reference price: 1 last, 2 fair, 3 index |
| errorCode | int | ENUM:errorCode |
| orderId | long | Order ID after execution |
| orderType | int | 1 limit, 2 Post Only, 3 IOC, 4 FOK, 5 market |
| marketOrderLevel | int | Custom level for market orders |
| positionMode | int | 0 historical none, 2 one-way, 1 hedge |
| lossTrend | int | SL reference: 1 last, 2 fair, 3 index |
| profitTrend | int | TP reference: 1 last, 2 fair, 3 index |
| stopLossPrice | decimal | SL price |
| takeProfitPrice | decimal | TP price |
| reduceOnly | boolean | Reduce-only |
| createTime | long | Create time |
| updateTime | long | Update time |

### Risk limit[​](#risk-limit "Direct link to Risk limit")

> Sample

```
{  
  "channel": "push.personal.risk.limit",  
  "data": {  
    "symbol": "BTC_USDT",  
    "positionType": 1,  
    "riskSource": 1,  
    "level": 2,  
    "maxVol": 500,  
    "maxLeverage": 50,  
    "mmr": 0.02,  
    "imr": 0.04,  
    "leverage": 20,  
    "openType": 1,  
    "limitBySys": true,  
    "maxVolView": 1000  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.risk.limit`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| positionType | int | 1 long, 2 short |
| riskSource | int | 0 other, 1 liquidation service |
| level | int | Current risk tier |
| maxVol | decimal | Max position size |
| maxLeverage | int | Max leverage |
| mmr | decimal | Maintenance margin rate |
| imr | decimal | Initial margin rate |
| leverage | int | Current leverage |
| openType | int | Margin mode, default isolated |
| limitBySys | boolean | Limited by system |
| maxVolView | decimal | Front-end slider helper (independent of lev) |

### TP/SL plan orders[​](#tpsl-plan-orders "Direct link to TP/SL plan orders")

> Sample

```
{  
  "channel": "push.personal.stop.planorder",  
  "data": {  
    "id": 987654321,  
    "orderId": 123456789,  
    "symbol": "BTC_USDT",  
    "positionId": 456789123,  
    "lossTrend": 1,  
    "profitTrend": 2,  
    "stopLossPrice": 42000.0,  
    "takeProfitPrice": 48000.0,  
    "state": 1,  
    "triggerSide": 1,  
    "positionType": 1,  
    "vol": 10,  
    "takeProfitVol": 10,  
    "stopLossVol": 10,  
    "realityVol": 10,  
    "placeOrderId": 987654321,  
    "version": 1,  
    "isFinished": 0,  
    "profitLossVolType": "SAME",  
    "volType": 1,  
    "takeProfitReverse": 2,  
    "stopLossReverse": 2,  
    "closeTryTimes": 0,  
    "reverseTryTimes": 0,  
    "reverseErrorCode": 0,  
    "stopLossType": 1,  
    "stopLossOrderPrice": 41990.0,  
    "createTime": 1760942212000,  
    "updateTime": 1760942212000  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.stop.planorder`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| id | long | Primary ID |
| orderId | long | Order ID |
| symbol | string | Contract |
| positionId | long | Position ID |
| lossTrend | int | SL reference type |
| profitTrend | int | TP reference type |
| stopLossPrice | decimal | SL price |
| takeProfitPrice | decimal | TP price |
| state | int | State |
| triggerSide | int | Trigger direction: 1 TP, 2 SL |
| positionType | int | Position type |
| vol | decimal | Quantity |
| takeProfitVol | decimal | TP quantity |
| stopLossVol | decimal | SL quantity |
| realityVol | decimal | Actual placed quantity |
| placeOrderId | long | Actual placed order ID |
| version | int | Version |
| isFinished | int | Completed |
| profitLossVolType | string | TP/SL qty type (SAME / SEPARATE) |
| volType | int | 1 staged TP/SL, 2 position TP/SL |
| takeProfitReverse | int | TP reverse: 1 yes, 2 no |
| stopLossReverse | int | SL reverse: 1 yes, 2 no |
| closeTryTimes | int | Close retry count |
| reverseTryTimes | int | Reverse retry count |
| reverseErrorCode | int | Reverse open error code (0 default) |
| stopLossType | int | 0 market SL, 1 limit SL |
| stopLossOrderPrice | decimal | Limit SL price |
| createTime | long | Create time |
| updateTime | long | Update time |

### Trailing orders[​](#trailing-orders "Direct link to Trailing orders")

> Sample

```
{  
  "channel": "push.personal.track.order",  
  "data": {  
    "id": 987654321,  
    "symbol": "BTC_USDT",  
    "leverage": 20,  
    "side": 1,  
    "vol": 50,  
    "openType": 1,  
    "trend": 1,  
    "activePrice": 45000.0,  
    "markPrice": 44950.0,  
    "backType": 1,  
    "backValue": 0.5,  
    "triggerPrice": 44750.0,  
    "triggerType": 2,  
    "orderId": 123456789,  
    "errorCode": 0,  
    "state": 1,  
    "positionMode": 2,  
    "reduceOnly": false,  
    "createTime": 1760942212000,  
    "updateTime": 1760942212000  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.track.order`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| id | long | Primary ID |
| symbol | string | Contract |
| leverage | int | Leverage |
| side | int | 1 open long, 2 close short, 3 open short, 4 close long |
| vol | decimal | Quantity |
| openType | int | 1 isolated, 2 cross |
| trend | int | Reference price (1 last, 2 fair, 3 index) |
| activePrice | decimal | Activation price |
| markPrice | decimal | Reference price after activation (highest/lowest) |
| backType | int | Callback type (1 percentage, 2 absolute) |
| backValue | decimal | Callback value |
| triggerPrice | decimal | Trigger price (updates with reference) |
| triggerType | int | Trigger condition |
| orderId | long | Order ID after triggering |
| errorCode | int | ENUM:errorCode |
| state | int | 0 not active, 1 active, 2 success, 3 failed, 4 canceled |
| positionMode | int | Position mode |
| reduceOnly | boolean | Reduce-only |
| createTime | long | Create time |
| updateTime | long | Update time |

### TP/SL prices[​](#tpsl-prices "Direct link to TP/SL prices")

> Sample

```
{  
  "channel": "push.personal.stop.order",  
  "data": {  
    "symbol": "BTC_USDT",  
    "orderId": 123456789,  
    "lossTrend": 1,  
    "profitTrend": 2,  
    "stopLossPrice": 42000.0,  
    "takeProfitPrice": 48000.0  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.stop.order`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| orderId | long | Order ID |
| lossTrend | int | SL reference type |
| profitTrend | int | TP reference type |
| stopLossPrice | decimal | SL price |
| takeProfitPrice | decimal | TP price |

### Fill details[​](#fill-details "Direct link to Fill details")

> Sample

```
{  
  "channel": "push.personal.order.deal",  
  "data": {  
    "id": 987654321,  
    "symbol": "BTC_USDT",  
    "side": 1,  
    "vol": 10,  
    "price": 45000.5,  
    "feeCurrency": "USDT",  
    "fee": 0.225,  
    "timestamp": 1760942212000,  
    "profit": 0,  
    "isTaker": true,  
    "category": 1,  
    "orderId": 123456789,  
    "isSelf": false,  
    "externalOid": "ext_001",  
    "positionMode": 1,  
    "reduceOnly": false,  
    "opponentUid": 987654321  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.order.deal`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| id | long | Fill ID |
| symbol | string | Contract |
| side | int | 1 open long, 2 close short, 3 open short, 4 close long |
| vol | decimal | Quantity |
| price | decimal | Price |
| feeCurrency | string | Fee currency |
| fee | decimal | One-side fee (positive = paid by user, negative = received by user) |
| timestamp | long | Fill time |
| profit | decimal | PnL |
| isTaker | boolean | Taker? |
| category | int | Order category |
| orderId | long | Order ID |
| isSelf | boolean | Self-trade? |
| externalOid | string | External order ID |
| positionMode | int | Position mode |
| reduceOnly | boolean | Reduce-only |
| opponentUid | long | Counterparty UID |

### Chase order failure[​](#chase-order-failure "Direct link to Chase order failure")

> Sample

```
{  
  "channel": "push.personal.order.chase",  
  "data": {  
    "ec": 1001,  
    "s": "BTC_USDT"  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.order.chase`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| ec | int | Error code |
| s | string | Contract |

### Liquidation risk change[​](#liquidation-risk-change "Direct link to Liquidation risk change")

> Sample

```
{  
  "channel": "push.personal.liquidate.risk",  
  "data": {  
    "symbol": "BTC_USDT",  
    "positionId": 123456789,  
    "liquidatePrice": 35000.0,  
    "marginRatio": 0.1,  
    "adlLevel": 3  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.liquidate.risk`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| positionId | long | Position ID |
| liquidatePrice | decimal | Liq price |
| marginRatio | decimal | Margin ratio |
| adlLevel | int | ADL level |

### Leverage mode change[​](#leverage-mode-change "Direct link to Leverage mode change")

> Sample

```
{  
  "channel": "push.personal.leverage.mode",  
  "data": {  
    "lm": 1  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.leverage.mode`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| lm | int | Leverage mode |

### Position mode change[​](#position-mode-change "Direct link to Position mode change")

> Sample

```
{  
  "channel": "push.personal.position.mode",  
  "data": {  
    "positionMode": 2  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.position.mode`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| positionMode | int | Position mode (1 hedge, 2 one-way) |

### Close-all failure[​](#close-all-failure "Direct link to Close-all failure")

`channel = push.personal.position.closeall.fail`

**Response:**
No body; channel message only.

### Reverse position[​](#reverse-position "Direct link to Reverse position")

> Sample

```
{  
  "channel": "push.personal.reverse.position",  
  "data": {  
    "contractId": 1,  
    "positionId": 123456789,  
    "state": 2,  
    "errorCode": 0  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.reverse.position`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| contractId | int | Contract ID |
| positionId | long | Position ID |
| state | int | State |
| errorCode | int | ENUM:errorCode |

### Trial bonus notification[​](#trial-bonus-notification "Direct link to Trial bonus notification")

> Sample

```
{  
  "channel": "push.personal.bonus",  
  "data": {  
    "c": "USDT",  
    "b": 100.0,  
    "be": 1763539200000,  
    "g": true,  
    "ret": 1763539200000,  
    "rea": 100.0  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.bonus`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| c | string | Currency |
| b | decimal | Trial bonus amount |
| be | long | Trial bonus expiry time |
| g | boolean | Whether trial bonus granted |
| ret | long | Most recent expiry time |
| rea | decimal | Most recent expiring amount |

### User notifications — liquidation warning/notice[​](#user-notifications--liquidation-warningnotice "Direct link to User notifications — liquidation warning/notice")

> Sample

```
{  
  "channel": "push.personal.generic.notify",  
  "data": {  
    "type": 1,  
    "param": {  
      "notifyType": 2,  
      "openType": 1,  
      "dn": "BTC_USDT永续",  
      "dne": "BTC_USDT PERPETUAL",  
      "multiAssets": false,  
      "marginRate": 0.085  
    }  
  },  
  "ts": 1760942212000  
}
```

`channel = push.personal.generic.notify`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| type | int | Notification type (1 liquidation) |
| param | object | Notification parameters |

Notification params (for liquidation types)

| Field | Type | Description |
| --- | --- | --- |
| notifyType | int | 1 liquidation, 2 liquidation warning |
| openType | int | 1 isolated, 2 cross |
| dn | string | Display name |
| dne | string | Display name (EN) |
| multiAssets | boolean | Multi-asset mode enabled? |
| marginRate | decimal | Margin ratio |

### Event contract positions[​](#event-contract-positions "Direct link to Event contract positions")

> Sample

```
{  
  "channel": "push.personal.event.contract.position",  
  "data": {  
    "positionId": 123456789,  
    "symbol": "BTC_USDT",  
    "side": "1",  
    "payRate": 0.15,  
    "amount": 1000.0,  
    "openPrice": 45000.5,  
    "closePrice": 46250.75,  
    "rewardAmount": 25.5,  
    "rewardAmountUsdt": 25.5,  
    "state": "3",  
    "closeResult": "PROFIT",  
    "createTime": 1760942212000,  
    "closeTime": 1760945812000,  
    "pnlAmount": 125.25  
  },  
  "ts": 1760945812000  
}
```

`channel = push.personal.event.contract.position`

**Response fields:**

| Field | Type | Description |
| --- | --- | --- |
| positionId | long | Position ID |
| symbol | string | Contract |
| side | string | Side |
| payRate | decimal | Bonus pay rate |
| amount | decimal | Order amount |
| openPrice | decimal | Open price |
| closePrice | decimal | Close price |
| rewardAmount | decimal | Reward amount |
| rewardAmountUsdt | decimal | Reward amount in USDT |
| state | string | State |
| closeResult | string | Close result |
| createTime | long | Create time |
| closeTime | long | Close time |
| pnlAmount | decimal | Total PnL |

Incremental Order Book Maintenance Mechanism[​](#incremental-order-book-maintenance-mechanism "Direct link to Incremental Order Book Maintenance Mechanism")
------------------------------------------------------------------------------------------------------------------------------------------------------------

1. Obtain Full Depth Snapshot (Initialization)
   Endpoint: `GET https://api.mexc.com/api/v1/contract/depth/{symbol}?limit=1000`
   Save the version from the response as localLastVersion.
2. Subscribe to WebSocket Depth Stream
3. Subscribe to push.depth
   When a push.depth update is received:

* If the message `version` > `localLastVersion`, updates for the same price level should override earlier ones (updates can be cached temporarily).
* Under normal conditions, if `version` == `localLastVersion + 1`, apply the update directly.

4. Packet Loss Recovery: Fetch Latest Depth Commits
   Endpoint: `GET https://api.mexc.com/api/v1/contract/depth_commits/{symbol}/1000` Retrieves the latest 1000 depth incremental commits (sorted in ascending order by version).
5. Apply Commits and Clear Cache Iterate through the commits

* skip any with `version` <= `localLastVersion`.
* Starting from the first commit where `version` == `localLastVersion + 1`, sequentially apply each commit's updates (quantity > 0: update or - insert the price level; quantity == 0: delete the price level).
* Update `localLastVersion` to the `version` of the last applied commit.
* If there are cached WebSocket updates, apply them as well (higher version takes priority).

6. Resume Real-Time Updates

* Continue applying incoming WebSocket events to the local order book.
* Each new event's version should be exactly equal to the previous `version + 1`.
* If the sequence is discontinuous (gaps or out-of-order versions), packet loss may have occurred → restart recovery from step 4 (or fall back to step 1 for full reinitialization).

7. Update Rules

* The quantity in each event is an absolute value (the current total quantity at that price level, not a relative change).
* If quantity == 0, the price level has been canceled or fully filled and should be removed.

ENUM definitions[​](#enum-definitions "Direct link to ENUM definitions")
------------------------------------------------------------------------

### errorCode[​](#errorcode "Direct link to errorCode")

* 0 NORMAL
* 1 PARAM\_INVALID
* 2 INSUFFICIENT\_BALANCE
* 3 POSITION\_NOT\_EXISTS
* 4 POSITION\_NOT\_ENOUGH
* 5 POSITION\_LIQ
* 6 ORDER\_LIQ
* 7 RISK\_LEVEL\_LIMIT
* 8 SYS\_CANCEL
* 9 POSITION\_MODE\_NOT\_MATCH
* 10 REDUCE\_ONLY\_LIQ
* 11 CONTRACT\_NOT\_ENABLE
* 12 DELIVERY\_CANCEL
* 13 POSITION\_LIQ\_CANCEL
* 14 ADL\_CANCEL
* 15 BLACK\_USER\_CANCEL
* 16 SETTLE\_FUNDING\_CANCEL
* 17 POSITION\_IM\_CHANGE\_CANCEL
* 18 IOC\_CANCEL
* 19 FOK\_CANCEL
* 20 POST\_ONLY\_CANCEL
* 21 MARKET\_CANCEL
* 22 OID\_DUPLICATE
* 23 CID\_DUPLICATE
* 999 OTHER

[Previous

Account and Trading Endpoints](/api-docs/futures/account-and-trading-endpoints)

* [Native ws endpoint](#native-ws-endpoint)
* [Command details for data exchange](#command-details-for-data-exchange)
* [Subscription filtering](#subscription-filtering)
* [Public channels](#public-channels)
  + [Tickers](#tickers)
  + [Get a single ticker](#get-a-single-ticker)
  + [Deal](#deal)
  + [Order book depth](#order-book-depth)
  + [Depth — specify minimum notional step](#depth--specify-minimum-notional-step)
  + [K-line data](#k-line-data)
  + [Funding rate](#funding-rate)
  + [Index price](#index-price)
  + [Fair price](#fair-price)
  + [Contract data](#contract-data)
  + [Event contracts](#event-contracts)
* [Private channels](#private-channels)
  + [Signature string](#signature-string)
  + [Login authentication](#login-authentication)
  + [Order](#order)
  + [Assets](#assets)
  + [Position](#position)
  + [Deduction info](#deduction-info)
  + [Plan orders](#plan-orders)
  + [Risk limit](#risk-limit)
  + [TP/SL plan orders](#tpsl-plan-orders)
  + [Trailing orders](#trailing-orders)
  + [TP/SL prices](#tpsl-prices)
  + [Fill details](#fill-details)
  + [Chase order failure](#chase-order-failure)
  + [Liquidation risk change](#liquidation-risk-change)
  + [Leverage mode change](#leverage-mode-change)
  + [Position mode change](#position-mode-change)
  + [Close-all failure](#close-all-failure)
  + [Reverse position](#reverse-position)
  + [Trial bonus notification](#trial-bonus-notification)
  + [User notifications — liquidation warning/notice](#user-notifications--liquidation-warningnotice)
  + [Event contract positions](#event-contract-positions)
* [Incremental Order Book Maintenance Mechanism](#incremental-order-book-maintenance-mechanism)
* [ENUM definitions](#enum-definitions)
  + [errorCode](#errorcode)