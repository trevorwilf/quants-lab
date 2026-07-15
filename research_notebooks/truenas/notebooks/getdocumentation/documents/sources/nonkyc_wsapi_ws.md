_Source: webscrape/nonkyc/nonkyc_wsapi.html (browser-rendered)_

_Loaded: 2026-04-04T04:30:31.348117Z_

NonKYC Cryptocurrency Exchange

[![NonKYC logo](/images/nonkyclogoicon.png)nonkyc](/)
[nonkyc](/)

[Log in](/login)
[Sign up](/signup)
en

![logo](/images/logo-yellow-header-micon.png)

* Login or Create Account

---

* [Markets](/markets)

---

* [Sign Up](/signup)

---

* [Log In](/login)

---

* [Support](/createticket)

---

* [Download App](https://nonkyc.io/download/latestAPK)

en

#### **NonKYC Websocket API** v1.0.0

  

#### API Endpoint URL

The endpoint for our WebSockets API is: `wss://ws.nonkyc.io`

#### Authentication

Public methods do not require any authentication. Private methods use the "login" method to authenticate using your Api Key & API Secret. Once authenticated, you do not need to reauthenticate as long as your websocket connection remains active.

#### Datetime Formatting

Unless otherwise stated, all timestamps are returned in ISO8601 format in UTC. Example: "2018-04-01T00:00:00Z" or "2018-04-01T00:00:00.000Z". If a timestamp is returned as an Integer, then that is a Unix timestamp in milliseconds.

#### Number Formatting

All finance data such as price, quantity, and fee should be arbitrary precision numbers and string representation. Example: "5.39300000"

#### Helpful Classes

You can find an example JS class here: <https://github.com/NonKYCExchange/websocketapiexample-main>

#### Heartbeat

The server will send a ping/pong heartbeat every 60 seconds while connected

#### Sequence

Subscription notifications include an integer sequence number. This number is unique for each subscribed pair and is incremented by one on each notification sent.

#### Errors

All Errors are formatted with error code and message (HTTP status codes are not used). If the 'error' field exists, then the call was not successful.

```
{
  "jsonrpc":"2.0",
  "error": {
    "code":10001,
    "message":"Invalid JSON Request"
  },
  "id": 123
}
```

#### Error Codes

| Error Code | HTTP Status Code | Message | Details |
| --- | --- | --- | --- |
| 400 | 400 | Unknown error | An unknown error occurred somewhere in the system |
| 402 | 400 | Method not found | The requested API method was not found |
| 403 | 401 | Action is forbidden for account |  |
| 429 | 429 | Too many requests | Action is being rate limited for account |
| 500 | 500 | Internal Server Error |  |
| 503 | 503 | Service Unavailable | Try it again later |
| 504 | 504 | Gateway Timeout | Check the result of your request later |
| 1001 | 401 | Authorization required |  |
| 1002 | 401 | Authorization failed |  |
| 1003 | 403 | Action is forbidden for this API key | Check permissions for API key |
| 1004 | 401 | Unsupported authorisation method | Use Basic authentication |
| 2001 | 400 | Symbol not found |  |
| 2002 | 400 | Currency not found |  |
| 10001 | 400 | Validation error | Input not valid |
| 20001 | 400 | Insufficient funds | Insufficient funds for creating order or any account operation |
| 20002 | 400 | Order not found | Attempt to get active order that not existing, filled, canceled or expired. |
| 20003 | 400 | Limit exceeded | Withdrawal limit exceeded |
| 20004 | 400 | Transaction not found | Requested transaction not found |
| 20005 | 400 | Payout not found |  |
| 20006 | 400 | Payout already committed |  |
| 20007 | 400 | Payout already rolled back |  |
| 20008 | 400 | Duplicate clientOrderId |  |
| 20010 | 400 | Address generation error | Unable to generate a new deposit address. Try request later. |
| 20011 | 400 | Withdrawal not found | The referenced withdrawal was not found. |
| 20012 | 400 | Withdrawals disabled | Withdrawals are disabled for this currency or system wide. Check system status page. |
| 20013 | 400 | Withdrawal amount below minimum | Minimum withdrawal amount for any currency is Withdraw Fee \* 2. |
| 20014 | 400 | Withdrawal address invalid | Ensure the address you are withdrawing to is correct. |
| 20015 | 400 | Payment ID Required | This currency requires a paymentId when making a withdrawal request. |
| 20016 | 400 | Invalid confirmation code | The provided confirmation code is incorrect. |
| 20017 | 400 | Withdraw already confirmed | The withdrawal request has already been confirmed. |

#### Global Paramaters

`method` - The method you would like to call

`params` - The parameters for the method

`id` - An identification you can pass to the server, the same id will be passed in the results.

---

Asset Lists
-----------

  
  

#### Request method: getAsset Public Method

Get single asset information
  
  
Input Parameters:

`currency` - The asset ticker you would like information on.

  
  

#### Request method: getAssets Public Method

Get all asset information
  
  
Input Parameters:

none

Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "getAsset",
  "params": {
    "ticker": "BTC"
  },
  "id": 123
}
```

  
Response
  

```
{
  "jsonrpc": "2.0",
  "result": {
	"_id" : "613b32b83a865a18ba4d3373",
	"createdAt" : 1631269560538.0,
	"updatedAt" : 1666755900150.0,
	"ticker" : "BTC",
	"name" : "Bitcoin",
	"network" : "Bitcoin Mainnet",
	"logo" : "bitcoin-btc-logo.png",
	"isActive" : true,
	"hasChildren" : false,
	"isChild" : false,
	"childOf" : null,
	"isToken" : false,
	"tokenDetails" : "",
	"useParentAddress" : false,
	"usdValue" : "20196",
	"depositActive" : true,
	"depositNotes" : "",
	"depositPayid" : false,
	"withdrawalActive" : true,
	"withdrawalNotes" : "",
	"withdrawalPayid" : false,
	"withdrawalPayidRequired" : false,
	"withdrawFeeMultiply" : 1.9,
	"confirmsRequired" : 2,
	"withdrawDecimals" : 8,
	"isDeflationary" : false,
	"deflationPercent" : 0,
	"withdrawFee" : "0.00050",
	"explorer" : "https://blockchair.com/bitcoin/",
	"explorerTxid" : "https://blockchair.com/bitcoin/transaction/%txid%",
	"explorerAddress" : "https://blockchair.com/bitcoin/address/%addr%",
	"website" : "https://www.bitcoin.org/",
	"coinMarketCap" : "https://coinmarketcap.com/currencies/bitcoin/",
	"coinGecko" : "https://www.coingecko.com/en/coins/bitcoin",
	"addressRegEx" : "^(?:[13]{1}[a-km-zA-HJ-NP-Z1-9]{26,33}|bc1[a-z0-9]{39,59})$",
	"payidRegEx" : "",
	"socialCommunity" : {
		"Reddit" : "https://reddit.com/r/Bitcoin",
		"X" : "https://x.com/bitcoin",
		"Facebook" : "https://www.facebook.com/134466763256650",
		"BitcoinTalk" : "https://bitcointalk.org/",
		"Github" : "https://github.com/bitcoin"
	},
	"coinGeckoApiId" : "bitcoin",
	"tokenOf" : null,
	"lastPriceUpdate" : 1666750835346.0,
	"circulation" : "19189418",
	"marketcapNumber" : 387549485928.0,
	"coinPaprika" : "https://coinpaprika.com/coin/btc-bitcoin/",
	"coinPaprikaApiId" : "btc-bitcoin",
	"coinCodex" : "https://coincodex.com/crypto/bitcoin/",
	"coinCodexApiId" : "BTC",
	"canLiquidityPool" : true,
	"canStake" : false,
	"canVote" : false,
	"imageUUID" : "d7cb5280-d0f2-4d0e-94f1-9c70b8df4883"
  },
  "id":123
}
```

  
Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "getAssets",
  "params": {},
  "id": 123
}
```

  
Response
  

```
{
  "jsonrpc": "2.0",
  "result": [
  
  ... Array of assets ... 
  
  ],
  "id":123
}
```

  

---

Market Lists
------------

  

#### Request method: getMarket Public Method

Get single market information
  
  
Input Parameters:

`symbol` - The market symbol you would like information on.

  
  

#### Request method: getMarkets Public Method

Get all market information
  
  
Input Parameters:

none

Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "getMarket",
  "params": {
    "symbol": "BTC/USDT"
  },
  "id": 123
}
```

  
Response
  

```
{
  "jsonrpc": "2.0",
  "result": {
    "_id" : "613b3cc3cd39a81b02a75d7e",
    "createdAt" : 1631272131450.0,
    "updatedAt" : 1666757734600.0,
    "symbol" : "BTC/USDT",
    "primaryName" : "Bitcoin",
    "primaryTicker" : "BTC",
    "lastPrice" : "20232.79",
    "yesterdayPrice" : "19349.78",
    "highPrice" : "20374.96",
    "lowPrice" : "19241.14",
    "volume" : "1.9774",
    "lastTradeAt" : 1666757627884.0,
    "priceDecimals" : 2,
    "quantityDecimals" : 7,
    "isActive" : true,
    "primaryAsset" : "613b32b83a865a18ba4d3373",
    "secondaryAsset" : "613b398ed7a0bd1a304f963e",
    "bestAsk" : "20225.67",
    "bestAskNumber" : 20225.67,
    "bestBid" : "20220",
    "bestBidNumber" : 20220,
    "changePercent" : "+4.56",
    "changePercentNumber" : 4.56,
    "highPriceNumber" : 20374.96,
    "lastPriceNumber" : 20232.79,
    "lowPriceNumber" : 19241.14,
    "volumeNumber" : 1.9774,
    "yesterdayPriceNumber" : 19349.78,
    "volumeUsdNumber" : 39935.57,
    "primaryCirculation" : "19189418",
    "primaryUsdValue" : "20196",
    "secondaryCirculation" : "68473108026.8332",
    "secondaryUsdValue" : "0.999765",
    "marketcapNumber" : 387549485928.0,
    "spreadPercent" : "0.028",
    "lastPriceUpDown" : "down",
    "engineId" : 5,
    "isPaused" : false,
    "imageUUID" : "d7cb5280-d0f2-4d0e-94f1-9c70b8df4883"
  },
  "id": 123
}
```

  
Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "getMarkets",
  "params": {},
  "id": 123
}
```

  
Response
  

```
{
  "jsonrpc": "2.0",
  "result": [
  
  ... Array of markets ... 
  
  ],
  "id":123
}
```

  

---

Trade History
-------------

  

#### Request method: getTrades Public Method

Get trade history information on a market
  
  
Input Parameters:

`symbol` - The market symbol you would like information on. (ie. ETH/BTC or ETH\_BTC)

`limit` - The limit of total results you would like (Optional, default: 100, max: 1000)

`offset` - Offset the results by this number (Optional, default: 0)

`sort` - 'ASC' for ascending order, 'DESC' for decending order. (Optional, default: DESC)

`from` - This is earliest datetime. (Optional). When using from or till, then both are required

`till` - This is latest datetime. (Optional). When using from or till, then both are required

Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "getTrades",
  "params": {
    "symbol": "ETH/BTC",
    "limit": 3,
    "offset": 0,
    "sort": "DESC",
    "from": "2022-10-19T06:39:20.796Z",
    "till": "2022-10-19T18:39:20.796Z"
  },
  "id": 123
}
```

  
Response
  

```
{
  "jsonrpc": "2.0",
  "result": {
    "data": [
      {
        "id": "629ac7b8d4d2fd8969724d44",
        "price": "0.054443",
        "quantity": "2.213",
        "triggeredBy": "sell",
        "timestamp": "2022-10-19T16:39:20.796Z",
        "timestampms": 1666843143000
      },
      {
        "id": "624ff8abe2bc9634ee08841d",
        "price": "0.054453",
        "quantity": "0.030",
        "triggeredBy": "sell",
        "timestamp": "2022-10-19T16:39:20.796Z",
        "timestampms": 1666843143000
      },
      {
        "id": "613b398ed7a0bd1a304f963e",
        "price": "0.054454",
        "quantity": "0.052",
        "triggeredBy": "sell",
        "timestamp": "2022-10-19T16:39:20.796Z",
        "timestampms": 1666843143000
      }
    ],
    "symbol": "ETH/BTC"
  },
  "id": 123
}
```

  

---

Subscribe to Ticker
-------------------

  

#### Request method: subscribeTicker Public Method

Subscribe to ticker information
  
  
Input Parameters:

`symbol` - The market symbol you would like to subscribe to.

  
Notification method: ticker
  
  
  

#### Request method: unsubscribeTicker Public Method

Unsubscribe from ticker information
  
  
Input Parameters:

`symbol` - The market symbol you would like to unsubscribe.

```
wscat -c wss://ws.nonkyc.io

{
  "method": "subscribeTicker",
  "params": {
    "symbol": "ETH/BTC"
  }
}
```

  
Notification ticker
  

```
{
  "jsonrpc": "2.0",
  "method": "ticker",
  "params": {
    symbol: "ETH/BTC"
    lastPrice: "0", 
    lastPriceUpDown: "up",
    yesterdayPrice: "0", 
    changePercent: "0", 
    highPrice: "0", 
    lowPrice: "0", 
    volume: "0", 
    bestBid: "0", 
    bestAsk: "0", 
    spreadPercent: "0",
    lastPriceNumber: 0, 
    yesterdayPriceNumber: 0, 
    changePercentNumber: 0, 
    highPriceNumber: 0, 
    lowPriceNumber: 0, 
    volumeNumber: 0, 
    volumeUsdNumber: 0, 
    bestBidNumber: 0, 
    bestAskNumber: 0, 
    lastTradeAt: 0, 
    updatedAt: 0,
    sequence: 0
  }
}
```

  
Unsubscribe
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "unsubscribeTicker",
  "params": {
    "symbol": "ETH/BTC"
  }
}
```

  
Unsubscribe Response
  

```
{
  "jsonrpc": "2.0",
  "result": true
}
```

  

---

Subscribe to Orderbook
----------------------

  

#### Request method: subscribeOrderbook Public Method

Subscribe to orderbook information
  
  
Input Parameters:

`symbol` - The market symbol you would like to subscribe to.

`limit` - (Optional) The number of items on each side of the books. Default: 100

  
Notification snapshot method: **snapshotOrderbook**   
- Message contains a full snapshot of order book.
  
  
Notification update method: **updateOrderbook**   
- Message contains incremental changes, size = 0 means that price level was deleted.
  Sequence is an increasing number for each update, each symbol has its own sequence.
  
  
  

#### Request method: unsubscribeOrderbook Public Method

Unsubscribe from orderbook information
  
  
Input Parameters:

`symbol` - The market symbol you would like to unsubscribe.

```
wscat -c wss://ws.nonkyc.io

{
  "method": "subscribeOrderbook",
  "params": {
    "symbol": "ETH/BTC",
    "limit": 100
  }
}
```

  
Notification snapshot
  

```
{
  "jsonrpc": "2.0",
  "method": "snapshotOrderbook",
  "params": {
    "asks": [
      {
        "price": "0.054588",
        "quantity": "0.245"
      },
      {
        "price": "0.054590",
        "quantity": "1.000"
      },
      {
        "price": "0.054591",
        "quantity": "2.784"
      }
    ],
    "bids": [
      {
        "price": "0.054558",
        "quantity": "0.500"
      },
      {
        "price": "0.054557",
        "quantity": "0.076"
      },
      {
        "price": "0.054524",
        "quantity": "7.725"
      }
    ],
    "symbol": "ETH/BTC",
    "timestamp": "2022-10-19T16:33:42.821Z",
    "sequence": 8073827
  }
}
```

  
Notification update
  

```
{
  "jsonrpc": "2.0",
  "method": "updateOrderbook",
  "params": {    
    "asks": [
      {
        "price": "0.054590",
        "quantity": "0.000"
      }
    ],
    "bids": [],
    "symbol": "ETH/BTC",
    "timestamp": "2022-10-19T16:33:42.821Z",
    "sequence": 8073830
  }
}
```

  
Unsubscribe
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "unsubscribeOrderbook",
  "params": {
    "symbol": "ETH/BTC"
  }
}
```

  
Unsubscribe Response
  

```
{
  "jsonrpc": "2.0",
  "result": true
}
```

  

---

Subscribe to Trades
-------------------

  

#### Request method: subscribeTrades Public Method

Subscribe to trade information
  
  
Input Parameters:

`symbol` - The market symbol you would like to subscribe to.

  
Notification snapshot method: **snapshotTrades**   
- Message contains a snapshot of the last 50 trades.
  
  
Notification update method: **updateTrades**   
- Message contains new trade information as it occurs.
  
  
  

#### Request method: unsubscribeTrades Public Method

Unsubscribe from trade information
  
  
Input Parameters:

`symbol` - The market symbol you would like to unsubscribe.

```
wscat -c wss://ws.nonkyc.io

{
  "method": "subscribeTrades",
  "params": {
    "symbol": "ETH/BTC"
  }
}
```

  
Notification snapshot
  

```
{
  "jsonrpc": "2.0",
  "method": "snapshotTrades",
  "params": {
    "data": [
      {
        "id": "613b398ed7a0bd1a304f963e",
        "price": "0.054656",
        "quantity": "0.057",
        "side": "buy",
        "timestamp": "2022-10-19T16:33:42.821Z"
      },
      {
        "id": "613b398ed7a0be1a304f963e",
        "price": "0.054656",
        "quantity": "0.092",
        "side": "buy",
        "timestamp": "2022-10-19T16:33:48.754Z"
      },
      {
        "id": "613b398ed7a0bd1a304f363e",
        "price": "0.054669",
        "quantity": "0.002",
        "side": "buy",
        "timestamp": "2022-10-19T16:34:13.288Z"
      }
    ],
    "symbol": "ETH/BTC",
    "sequence": 0
  }
}
```

  
Notification update
  

```
{
  "jsonrpc": "2.0",
  "method": "updateTrades",
  "params": {
    "data": [
      {
        "id": "613b398ed7a0bd1a304f163e",
        "price": "0.054670",
        "quantity": "0.183",
        "side": "buy",
        "timestamp": "2022-10-19T16:34:25.041Z"
      }
    ],
    "symbol": "ETH/BTC",
    "sequence": 0
  }
}
```

  
Unsubscribe
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "unsubscribeTrades",
  "params": {
    "symbol": "ETH/BTC"
  }
}
```

  
Unsubscribe Response
  

```
{
  "jsonrpc": "2.0",
  "result": true
}
```

  

---

Subscribe to Candles
--------------------

  

#### Request method: subscribeCandles Public Method

Subscribe to candlestick information
  
  
Input Parameters:

`symbol` - The market symbol you would like to subscribe to.

`period` - The candlestick period you would like (Minutes). (5, 15, 30, 60, 180, 240, 480, 720, 1440)

`limit` - Limit the results. (Optional, default: 100)

  
Notification snapshot method: **snapshotCandles**   
- Message contains a a snapshot of the candlestick information up to the limit, sorted by newest first.
  
  
Notification update method: **updateCandles**   
- Message contains any new changes to the candlestick data.
  
  
  

#### Request method: unsubscribeCandles Public Method

Unsubscribe from candlestick information
  
  
Input Parameters:

`symbol` - The market symbol you would like to unsubscribe.

`period` - The candlestick period you would like unsubscribe from. (5, 15, 30, 60, 180, 240, 480, 720, 1440)

```
wscat -c wss://ws.nonkyc.io

{
  "method": "subscribeCandles",
  "params": {
    "symbol": "ETH/BTC",
    "period": 30
  },
  "id": 123
}
```

  
Notification snapshot
  

```
{
  "jsonrpc": "2.0",
  "method": "snapshotCandles",
  "params": {
    "data": [
      {
        "timestamp": "2017-10-19T15:00:00.000Z",
        "open": "0.054801",
        "close": "0.054625",
        "min": "0.054601",
        "max": "0.054894",
        "volume": "380.750"
      },
      {
        "timestamp": "2017-10-19T15:30:00.000Z",
        "open": "0.054616",
        "close": "0.054618",
        "min": "0.054420",
        "max": "0.054724",
        "volume": "348.527"
      },
      {
        "timestamp": "2017-10-19T16:00:00.000Z",
        "open": "0.054587",
        "close": "0.054626",
        "min": "0.054408",
        "max": "0.054768",
        "volume": "194.014"
      },
      {
        "timestamp": "2017-10-19T16:30:00.000Z",
        "open": "0.054614",
        "close": "0.054443",
        "min": "0.054339",
        "max": "0.054724",
        "volume": "141.213"
      }
    ],
    "symbol": "ETH/BTC",
    "period": 30
  }
}
```

  
Notification update
  

```
{
  "jsonrpc": "2.0",
  "method": "updateCandles",
  "params": {
    "data": [
      {
        "timestamp": "2017-10-19T16:30:00.000Z",
        "open": "0.054614",
        "close": "0.054465",
        "min": "0.054339",
        "max": "0.054724",
        "volume": "141.268",
      }
    ],
    "symbol": "ETH/BTC",
    "period": 30
  }
}
```

  
Unsubscribe
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "unsubscribeCandles",
  "params": {
    "symbol": "ETH/BTC",
    "period": 30
  }
}
```

  
Unsubscribe Response
  

```
{
  "jsonrpc": "2.0",
  "result": true
}
```

  

---

Socket Session Authentication
-----------------------------

  

#### Request method: login Public Method

Authenticate session with your API keys in order to use any Private Method
  
  
Input Parameters:

`algo` - Either "BASIC" or "HS256".

`pKey` - API Public Key

`sKey` - API Secret Key, required for BASIC algo

`nonce` - Random string, required on HS256 algo

`signature` - HMAC SHA256 sign nonce with API secret key, required on HS256 algo

  
Here is an example of creating the signature in Nodejs

```
var hmac = crypto.createHmac('sha256', sKey);
hmac.update(nonce);
var signature = hmac.digest('hex');
```

BASIC Authorization Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "login",
  "params": {
    "algo": "BASIC",
    "pKey": "3ef4a9f8322f04bd8f09823b98403eae",
    "sKey": "2deb5702358fd553a4ed3e3229fd2d51"
  }
}
```

  
Response
  

```
{
  "jsonrpc": "2.0",
  "result": true
  "id": 123
}
```

  
HS256 Authorization Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "login",
  "params": {
    "algo": "HS256",
    "pKey": "3ef4a9f8c8bf04bd8f09884b98403eae",
    "nonce": "N1g287gL8YOwDZr",
    "signature": "b1c0ae399c2d341866a214f7d3ed755b821c1c36fc6f17083ef05fbb55b7f986"
  }
}
```

  
Response
  

```
{
  "jsonrpc": "2.0",
  "result": true
  "id": 123
}
```

  

---

Order Creation
--------------

  

#### Request method: newOrder Private Method

Submit a new order request
  
  
Input Parameters:

`symbol` - The market symbol you are submitting an order for.

`userProvidedId` - Unique string. If not provided, we will generate a random UUIDv4.

`side` - 'buy' or 'sell'

`type` - 'limit', 'market' (Optional, default: limit)

`quantity` - Required. Order quantity.

`price` - Order price. Required for limit type.

`strictValidate` - Boolean (true/false). Price and quantity will be checked that they increment within tick size and quantity step. See symbol tickSize and quantityIncrement. (default: false)

Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "newOrder",
  "params": {
    "userProvidedId": "57d5525562c945448e3cbd559bd068c4",
    "symbol": "ETH/BTC",
    "side": "sell",
    "price": "0.059837",
    "quantity": "0.015"
  },
  "id": 123
}
```

  
Success Response
  

```
{
  "jsonrpc": "2.0",
  "result": {
    "id": "6d55e562c9453448e3cbd559bd068c4",
    "userProvidedId": "57d5525562c945448e3cbd559bd068c4",
    "symbol": "ETH/BTC",
    "side": "sell",
    "type": "limit",
    "price": "0.059837",
    "numberprice": 0.059837,
    "quantity": "0.015",
    "executedQuantity": "0.00",
    "remainQuantity": "0.015",
    "remainTotal": "0.000897555",
    "remainTotalWithFee": "0.000897555",
    "lastTradeAt": 0,
    "status": "New",
    "isActive": true,
    "isNew": true,
    "createdAt": 1636676119991,
    "updatedAt": 1636676119991,
    "reportType": "new"
  },
  "id": 123
}
```

  
Error Response
  

```
{
  "jsonrpc": "2.0",
  "error": {
    "code": 20001,
    "message": "Insufficient funds",
    "description": "Check that the funds are sufficient, given commissions"
  },
  "id": 123
}
```

  

---

Order Cancellation
------------------

  

#### Request method: cancelOrder Private Method

Cancel an existing order request
  
  
Input Parameters:

`orderId` - Use this parameter if you want to cancel by order id.

-or-

`userProvidedId` - Use this paramter if you want to cancel by userProvidedId

Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "cancelOrder",
  "params": {
    "userProvidedId": "57d5525562c945448e3cbd559bd068c4"
  },
  "id": 123
}
```

  
Success Response
  

```
{
  "jsonrpc": "2.0",
  "result": {
    "id": "6d55e562c9453448e3cbd559bd068c4",
    "userProvidedId": "57d5525562c945448e3cbd559bd068c4",
    "symbol": "ETH/BTC",
    "side": "sell",
    "type: "limit",
    "price: "0.059837",
    "numberprice: 0.059837,
    "quantity: "0.015",
    "executedQuantity: "0.00",
    "remainQuantity: "0.015",
    "remainTotal: "0.000897555",
    "remainTotalWithFee: "0.000897555",
    "lastTradeAt: 0,
    "status: "Cancelled",
    "isActive: false,
    "isNew: false
    "createdAt": 1636676119991,
    "updatedAt": 1636676119991,
    "reportType": "cancelled"
  },
  "id": 123
}
```

  

---

Get Active Orders
-----------------

  

#### Request method: getOrders Private Method

Get a list of all open orders
  
  
Input Parameters:

`symbol` - (Optional) The market symbol

Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "getOrders",
  "params": {
  	"symbol": "BTC/USDT"
  },
  "id": 123
}
```

  
Response
  

```
{
  "jsonrpc": "2.0",
  "result": [
    {
      "id": "4346371528",
      "userProvidedId": "9cbe79cb6f864b71a811402a48d4b5b2",
      "symbol": "ETH/BTC",
      "side": "sell",
      "status": "new",
      "type": "limit",
      "quantity": "0.002",
      "price": "0.083837",
      "executedQuantity": "0.000",
      "createdAt": 1636676119991,
      "updatedAt": 1636676119991,
      "reportType": "status",
    },
    {
      "id": "4346371529",
      "userProvidedId": "9cbe79cb6f864b71a811402a48d48c73",
      "symbol": "ETH/BTC",
      "side": "buy",
      "status": "new",
      "type": "limit",
      "quantity": "0.002",
      "price": "0.073837",
      "executedQuantity": "0.000",
      "createdAt": 1636676119991,
      "updatedAt": 1636676119991,
      "reportType": "status",
    }
  ],
  "id": 123
}
```

  

---

Get Trading Balance
-------------------

  

#### Request method: getTradingBalance Private Method

Get a list of all account balances
  
  
Input Parameters:

none

Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "getTradingBalance",
  "params": {},
  "id": 123
}
```

  
Response
  

```
{
  "jsonrpc": "2.0",
  "result": [
    {
      "asset": "USDT",
      "available": "100.000000000",
      "held": "0.00000000"
    },
    {
      "asset": "BTC",
      "available": "0.013634021",
      "held": "0.00000000"
    },
    {
      "asset": "ETH",
      "available": "0",
      "held": "0.00000000"
    }
  ],
  "id": 123
}
```

  

---

Subscribe to Order/Trade Reports
--------------------------------

  

#### Request method: subscribeReports Private Method

Subscribe to all order updates and new trades on your account
  
  
Input Parameters:

none

  
Notification snapshot method: **activeOrders**   
- Message contains a list of all currently active orders.
  
  
Notification update method: **report**   
- Message contains any new changes to your orders such as new order, cancelled order, or trade.

Request
  

```
wscat -c wss://ws.nonkyc.io

{
  "method": "subscribeReports",
  "params": {}
}
```

  
Notification snapshot
  

```
{
  "jsonrpc": "2.0",
  "method": "activeOrders",
  "params": [
    {
      "id": "6447cf917963464a811a4af426102c19",
      "userProvidedId": "9cbe79cb6f864b71a811402a48d48c73",
      "symbol": "ETH/BTC",
      "side": "buy",
      "status": "new",
      "type": "limit",
      "quantity": "0.002",
      "price": "0.073837",
      "executedQuantity": "0.000",
      "createdAt": 1636676119991,
      "updatedAt": 1636676119991,
      "reportType": "status"
    }
  ]
}
```

  
Notification report (trade)
  

```
{
  "jsonrpc": "2.0",
  "method": "report",
  "params": {
    "id": "6447cf917963464a811a4af426102c19",
    "userProvidedId": "53b7cf917963464a811a4af426102c19",
    "symbol": "ETH/BTC",
    "side": "sell",
    "status": "Partly Filled",
    "type": "limit",
    "quantity": "0.001",
    "price": "0.053868",
    "executedQuantity": "0.001",
    "createdAt": 1636676119991,
    "updatedAt": 1636676119991,
    "reportType": "trade",
    "tradeQuantity": "0.001",
    "tradePrice": "0.053868",
    "tradeId": 55051694,
    "tradeFee": "0.00000000"
  }
}
```

  
Notification report (new order)
  

```
{
  "jsonrpc": "2.0",
  "method": "report",
  "params": {
    "id": "6447cf917963464a811a4af426102c19",
    "userProvidedId": "53b7cf917963464a811a4af426102c19",
    "symbol": "ETH/BTC",
    "side": "sell",
    "status": "New",
    "type": "limit",
    "quantity": "0.001",
    "price": "0.053868",
    "executedQuantity": "0.000",
    "createdAt": 1636676119991,
    "updatedAt": 1636676119991,
    "reportType": "new"
  }
}
```

  
Notification report (cancelled order)
  

```
{
  "jsonrpc": "2.0",
  "method": "report",
  "params": {
    "id": "6447cf917963464a811a4af426102c19",
    "userProvidedId": "53b7cf917963464a811a4af426102c19",
    "symbol": "ETH/BTC",
    "side": "sell",
    "status": "Cancelled",
    "type": "limit",
    "quantity": "0.001",
    "price": "0.053868",
    "executedQuantity": "0.001",
    "createdAt": 1636676119991,
    "updatedAt": 1636676119991,
    "reportType": "cancelled"
  }
}
```

  
Notification report (updated order w/o trade)
  

```
{
  "jsonrpc": "2.0",
  "method": "report",
  "params": {
    "id": "6447cf917963464a811a4af426102c19",
    "userProvidedId": "53b7cf917963464a811a4af426102c19",
    "symbol": "ETH/BTC",
    "side": "sell",
    "status": "Active",
    "type": "limit",
    "quantity": "0.001",
    "price": "0.053868",
    "executedQuantity": "0.001",
    "createdAt": 1636676119991,
    "updatedAt": 1636676119991,
    "reportType": "update"
  }
}
```

* ##### Services

  + [Liquidity Pools](/liquiditypools)
  + [List Asset](/listing)
  + [Market Making](/marketmaking)
  + [Market Making Paid](/marketmakingpaid)
  + [Prepaid Card](/prepaidcard)
* ##### API

  + [Rest API](https://api.nonkyc.io)
  + [Websocket API](/wsapi)
  + [GitHub Repositories](https://github.com/NonKYCExchange)
* ##### Resources

  + [System Status](/systemstatus)
  + [Fees](/fees)
  + [Bug Bounty](https://hackenproof.com/programs/nonkyc-dot-io)
  + [Mobile App](/downloads)
* ##### Info

  + [Media Kit](/mediakit)
  + [Terms](/legal/terms)
  + [Privacy](/legal/privacy)
  + [Referral Program](/referralprogram)
  + [FAQ](/faq)
* ##### Exchange Aggregators

  + [CoinGecko](https://www.coingecko.com/en/exchanges/nonkyc-io/)
  + [CoinMarketCap](https://coinmarketcap.com/exchanges/nonkyc/)
  + [CoinPaprika](https://coinpaprika.com/exchanges/nonkycio/)
  + [CoinCodex](https://coincodex.com/exchange/nonkyc.io/)
  + [Blockspot.io](https://blockspot.io/exchange/nonkyc.io/)
  + [LiveCoinWatch](https://www.livecoinwatch.com/exchange/nonkyc)
  + [CoinCarp](https://www.coincarp.com/exchange/nonkyc/markets/)
* ##### Token Aggregators

  + [CoinGecko](https://www.coingecko.com/en/coins/nkyc-token)
  + [CoinMarketCap](https://coinmarketcap.com/currencies/nonkyc-io-exchange/)
  + [CoinPaprika](https://coinpaprika.com/coin/nkyc-nkyc/)
  + [CoinCodex](https://coincodex.com/crypto/nkyc-token/)
  + [CoinCheckup](https://coincheckup.com/coins/nkyc-token)
  + [CoinCarp](https://www.coincarp.com/currencies/nonkyc/price/)
* ##### Company

  + [About Us](/about)
  + [NonKYC News](/news)
  + [AML](/legal/aml)
  + [All Reserves](/allreserves)
  + [Insurance Fund](/insurance-fund)
  + [NonKYC Verify](/verification-search)
  + [X.com](https://x.com/nonkyc_exchange)
  + [Telegram](https://t.me/nonkyc)

Stable Connection

[Support Ticket](/createticket)

© 2023 - 2026 [NonKyc.io](https://nonkyc.io)

Stable Connection
2026-04-04, 04:29:52 UTC

© 2023 - 2026 [NonKyc.io](https://nonkyc.io)

$14,869,676
 35404
[Support Ticket](/createticket)




### Cookie settings

We use cookies to personalize content and analyze access to our website. You can choose whether you only accept cookies that are necessary for the functioning of the website or whether you also want to allow tracking cookies. For more information, please refer to our [privacy policy](/legal/privacy).

Only accept technically necessary cookiesAccept all cookies

![](data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==)