_Source: webscrape/mexc/mexc_market_data.html (browser-rendered)_

_Loaded: 2026-04-04T04:30:31.038431Z_

Market Data Endpoints | MEXC API

[Skip to main content](#__docusaurus_skipToContent_fallback "Skip to main content")

[![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)](https://www.mexc.com/ "https://www.mexc.com/")[SpotV3](/api-docs/spot-v3/introduction "SpotV3")[Futures](/api-docs/futures/update-log "Futures")[Broker](/api-docs/broker/mexc-broker-introduction "Broker")

[English](# "English")

* [English](/api-docs/spot-v3/market-data-endpoints "English")
* [中文](/zh-MY/api-docs/spot-v3/market-data-endpoints "中文")

* [Introduction](/api-docs/spot-v3/introduction "Introduction")
* [Change Log](/api-docs/spot-v3/change-log "Change Log")
* [FAQs](/api-docs/spot-v3/faqs "FAQs")
* [General Info](/api-docs/spot-v3/general-info "General Info")
* [Market Data Endpoints](/api-docs/spot-v3/market-data-endpoints "Market Data Endpoints")
* [Sub-Account Endpoints(Only supports main account API key)](/api-docs/spot-v3/subaccount-endpoints "Sub-Account Endpoints(Only supports main account API key)")
* [Spot Account/Trade](/api-docs/spot-v3/spot-account-trade "Spot Account/Trade")
* [Wallet Endpoints](/api-docs/spot-v3/wallet-endpoints "Wallet Endpoints")
* [Websocket Market Streams](/api-docs/spot-v3/websocket-market-streams "Websocket Market Streams")
* [Websocket User Data Streams](/api-docs/spot-v3/websocket-user-data-streams "Websocket User Data Streams")
* [Rebate Endpoints](/api-docs/spot-v3/rebate-endpoints "Rebate Endpoints")
* [Public API Definitions](/api-docs/spot-v3/public-api-definitions "Public API Definitions")

On this page

Market Data Endpoints
=====================

Download Historical Market Data[​](#download-historical-market-data "Direct link to Download Historical Market Data")
---------------------------------------------------------------------------------------------------------------------

Provides kline and trading data for all Spot pairs since 01-01-2023:[Historical Market Data](https://www.mexc.co/zh-CN/market-data-download "Historical Market Data")

Test Connectivity[​](#test-connectivity "Direct link to Test Connectivity")
---------------------------------------------------------------------------

> Response

```
{}
```

* **GET** `/api/v3/ping`

Test connectivity to the Rest API.

**Weight(IP):** 1

Parameter:

NONE

Check Server Time[​](#check-server-time "Direct link to Check Server Time")
---------------------------------------------------------------------------

> Response

```
{  
    "serverTime" : 1645539742000  
}
```

* **GET** `/api/v3/time`

**Weight(IP):** 1

Parameter:

NONE

API default symbol[​](#api-default-symbol "Direct link to API default symbol")
------------------------------------------------------------------------------

> Request

```
GET /api/v3/defaultSymbols
```

> Response

```
{  
    "code": 200,  
    "data": [  
        "GENE1USDT",  
        "SNTUSDT",  
        "SQUAWKUSDT",  
        "HEGICUSDT",  
        "GUMUSDT"  
    ],  
    "msg": null  
}
```

* **GET** `/api/v3/defaultSymbols`

**Weight(IP):** 1

**Request**

NONE

**Response**

| Name | Type | Description |
| --- | --- | --- |
| symbol | string | symbol |

Query Offline Symbols[​](#query-offline-symbols "Direct link to Query Offline Symbols")
---------------------------------------------------------------------------------------

Get information on trading pairs that have been suspended or delisted.

> Request

```
GET /api/v3/symbol/offline
```

> Response

```
{  
    "data": [  
        {  
            "symbol": "LVNUSDT",  
            "state": 3  
        },  
        {  
            "symbol": "LOKAUSDT",  
            "state": 3,  
            "offlineTime": 1724125694000  
        },  
        {  
            "symbol": "PIASBTC",  
            "state": 3,  
            "offlineTime": 1669886455000  
        },  
        {  
            "symbol": "SUBUSDT",  
            "state": 3,  
            "offlineTime": 1738245924000  
        },  
        {  
            "symbol": "BARTOLD2USDT",  
            "state": 3,  
            "offlineTime": 1653753197000  
        },  
        {  
            "symbol": "MISHAUSDT",  
            "state": 3,  
            "offlineTime": 1740751476000  
        },  
        {  
            "symbol": "OPENOLDETH",  
            "state": 3  
        }  
    ]  
}
```

* **GET** `/api/v3/symbol/offline`

**Weight(IP):** 10

**Request**

NONE

**Response**

| Name | Type | Description |
| --- | --- | --- |
| symbol | string | symbol |
| state | int | Status: 2 - Suspended, 3 - Delisted |
| offlineTime | long | Delisting time (ms) |

Exchange Information[​](#exchange-information "Direct link to Exchange Information")
------------------------------------------------------------------------------------

> Response

```
{  
    "timezone": "CST",  
    "serverTime": 1765342336768,  
    "rateLimits": [],  
    "exchangeFilters": [],  
    "symbols": [  
        {  
            "symbol": "BTCUSDT",  
            "status": "1",  
            "baseAsset": "BTC",  
            "baseAssetPrecision": 8,  
            "quoteAsset": "USDT",  
            "quotePrecision": 2,  
            "quoteAssetPrecision": 2,  
            "baseCommissionPrecision": 8,  
            "quoteCommissionPrecision": 2,  
            "orderTypes": [  
                "LIMIT",  
                "MARKET",  
                "LIMIT_MAKER"  
            ],  
            "isSpotTradingAllowed": false,  
            "isMarginTradingAllowed": false,  
            "quoteAmountPrecision": "1",  
            "baseSizePrecision": "0.000001",  
            "permissions": [  
                "SPOT"  
            ],  
            "filters": [  
                {  
                    "filterType": "PERCENT_PRICE_BY_SIDE",  
                    "bidMultiplierUp": "0.005",  
                    "askMultiplierDown": "0.005"  
                }  
            ],  
            "maxQuoteAmount": "4000000",  
            "makerCommission": "0",  
            "takerCommission": "0.0005",  
            "quoteAmountPrecisionMarket": "1",  
            "maxQuoteAmountMarket": "4000000",  
            "fullName": "Bitcoin",  
            "tradeSideType": 1,  
            "contractAddress": "",  
            "conceptPlateIds": [  
                50,  
                5,  
                39,  
                12  
            ],  
            "st": false  
        }  
    ]  
}
```

* **GET** `/api/v3/exchangeInfo`

Current exchange trading rules and symbol information

**Weight(IP):** 25

**Parameter**:

There are 3 possible options:

| Method | **Example** |
| --- | --- |
| No parameter | curl -X GET "[https://api.mexc.com/api/v3/exchangeInfo](https://api.mexc.com/api/v3/exchangeInfo "https://api.mexc.com/api/v3/exchangeInfo")" |
| symbol | curl -X GET "[https://api.mexc.com/api/v3/exchangeInfo?symbol=MXUSDT](https://api.mexc.com/api/v3/exchangeInfo?symbol=MXUSDT "https://api.mexc.com/api/v3/exchangeInfo?symbol=MXUSDT")" |
| symbols | curl -X GET "[https://api.mexc.com/api/v3/exchangeInfo?symbols=MXUSDT,BTCUSDT](https://api.mexc.com/api/v3/exchangeInfo?symbols=MXUSDT,BTCUSDT "https://api.mexc.com/api/v3/exchangeInfo?symbols=MXUSDT,BTCUSDT")" |

**Response:**

| Name | Type | Description |
| --- | --- | --- |
| timezone | string | timezone |
| serverTime | long | server Time |
| rateLimits | Array | rate Limits |
| exchangeFilters | Array | exchange Filters |
| symbol | String | symbol |
| status | String | status:1 - online, 2 - Pause, 3 - offline |
| baseAsset | String | base Asset |
| baseAssetPrecision | Int | base Asset Precision |
| quoteAsset | String | quote Asset |
| quotePrecision | Int | quote Precision |
| quoteAssetPrecision | Int | quote Asset Precision |
| baseCommissionPrecision | Int | base Commission Precision |
| quoteCommissionPrecision | Int | quote Commission Precision |
| orderTypes | Array | ENUM: [Order Type](/api-docs/spot-v3/public-api-definitions#order-type "Order Type") |
| isSpotTradingAllowed | Boolean | allow api spot trading |
| isMarginTradingAllowed | Boolean | allow api margin trading |
| permissions | Array | permissions |
| filterType | String | filter type:PERCENT\_PRICE\_BY\_SIDE |
| bidMultiplierUp | String | bidMultiplierUp |
| askMultiplierDown | String | askMultiplierDown |
| maxQuoteAmount | String | max Quote Amount |
| makerCommission | String | marker Commission |
| takerCommission | String | taker Commission |
| quoteAmountPrecision | string | min order amount |
| baseSizePrecision | string | min order quantity |
| quoteAmountPrecisionMarket | string | min order amount in market order |
| maxQuoteAmountMarket | String | max quote Amount in market order |
| tradeSideType | String | tradeSide Type:1 - All, 2 - buy order only, 3 - Sell order only, 4 - Close |
| contractAddress | String | contract Address |
| st | String | symbol st status:false,true |

filter parameter description:

* lastPrice means using the latest trade price, orderPrice means the order placement price.
* For buy orders (only for LIMIT, IMMEDIATE\_OR\_CANCEL, FILL\_OR\_KILL):
  `orderPrice <= lastPrice * bidMultiplierUp`
* For sell orders:
  `orderPrice >= lastPrice * askMultiplierDown`

Order Book[​](#order-book "Direct link to Order Book")
------------------------------------------------------

> Response

```
{  
  "lastUpdateId": 1112416,  
  "bids": [  
      ["15.00000", "49999.00000"]  
  ],  
  "asks": [  
    ["14.0000", "1.0000"]  
  ]  
}
```

* **GET** `/api/v3/depth`

**Weight(IP):** 3

Parameter:

| Name | Type | Mandatory | Description | Scope |
| --- | --- | --- | --- | --- |
| symbol | string | YES | Symbol |  |
| limit | integer | NO | Returen number | default 100; max 5000 |

Response:

| Name | Type | Description |
| --- | --- | --- |
| lastUpdateId | long | Last Update Id |
| bids | list | Bid [Price, Quantity ] |
| asks | list | Ask [Price, Quantity ] |

Recent Trades List[​](#recent-trades-list "Direct link to Recent Trades List")
------------------------------------------------------------------------------

> Response

```
[  
  {  
    "id": null,  
    "price": "23",  
    "qty": "0.478468",  
    "quoteQty": "11.004764",  
    "time": 1640830579240,  
    "isBuyerMaker": true,  
    "isBestMatch": true  
  }  
]
```

* **GET** `/api/v3/trades`

**Weight(IP):** 5

Parameter:

| Name | Type | Mandatory | Description | Scope |
| --- | --- | --- | --- | --- |
| symbol | string | YES |  |  |
| limit | integer | NO |  | Default 500; max 1000 |

Response:

| Name | Description |
| --- | --- |
| id | Trade id |
| price | Price |
| qty | Number |
| quoteQty | Trade total |
| time | Trade time |
| isBuyerMaker | Was the buyer the maker? |
| isBestMatch | Was the trade the best price match? |

Compressed/Aggregate Trades List[​](#compressedaggregate-trades-list "Direct link to Compressed/Aggregate Trades List")
-----------------------------------------------------------------------------------------------------------------------

> Response

```
[  
  {  
    "a": null,  
    "f": null,  
    "l": null,  
    "p": "46782.67",  
    "q": "0.0038",  
    "T": 1641380483000,  
    "m": false,  
    "M": true  
  }  
]
```

* **GET** `/api/v3/aggTrades`

**Weight(IP):** 1

Get compressed, aggregate trades. Trades that fill at the time, from the same order, with the same price will have the quantity aggregated.

Parameters:

| Name | Type | Mandatory | Description | Scope |
| --- | --- | --- | --- | --- |
| symbol | string | YES |  |  |
| startTime | long | NO | Timestamp in ms to get aggregate trades from INCLUSIVE. |  |
| endTime | long | NO | Timestamp in ms to get aggregate trades until INCLUSIVE. |  |
| limit | integer | NO |  | Default 500; max 1000. |

startTime and endTime must be used at the same time.

Response:

| Name | Description |
| --- | --- |
| a | Aggregate tradeId |
| f | First tradeId |
| l | Last tradeId |
| p | Price |
| q | Quantity |
| T | Timestamp |
| m | Was the buyer the maker? |
| M | Was the trade the best price match? |

Kline/Candlestick Data[​](#klinecandlestick-data "Direct link to Kline/Candlestick Data")
-----------------------------------------------------------------------------------------

> Response

```
[  
  [  
    1640804880000,   
    "47482.36",   
    "47482.36",   
    "47416.57",   
    "47436.1",   
    "3.550717",   
    1640804940000,   
    "168387.3"  
  ]  
]
```

* **GET** `/api/v3/klines`

**Weight(IP):** 1

Kline/candlestick bars for a symbol.
Klines are uniquely identified by their open time.

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | string | YES |  |
| interval | ENUM | YES | ENUM: [Kline Interval](/api-docs/spot-v3/public-api-definitions#kline-interval "Kline Interval") |
| startTime | long | NO |  |
| endTime | long | NO |  |
| limit | integer | NO | Default 500; max 500. |

Response:

| Index | Description |
| --- | --- |
| 0 | Open time |
| 1 | Open |
| 2 | High |
| 3 | Low |
| 4 | Close |
| 5 | Volume |
| 6 | Close time |
| 7 | Quote asset volume |

Current Average Price[​](#current-average-price "Direct link to Current Average Price")
---------------------------------------------------------------------------------------

> Response

```
{  
  "mins": 5,  
  "price": "9.35751834"  
}
```

* **GET** `/api/v3/avgPrice`

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | string | YES |  |

Response:

| Name | Description |
| --- | --- |
| mins | Average price time frame |
| price | Price |

24hr Ticker Price Change Statistics[​](#24hr-ticker-price-change-statistics "Direct link to 24hr Ticker Price Change Statistics")
---------------------------------------------------------------------------------------------------------------------------------

> Response

```
{  
    "symbol": "BTCUSDT",  
    "priceChange": "184.34",  
    "priceChangePercent": "0.00400048",  
    "prevClosePrice": "46079.37",  
    "lastPrice": "46263.71",  
    "bidPrice": "46260.38",  
    "bidQty": "",  
    "askPrice": "46260.41",  
    "askQty": "",  
    "openPrice": "46079.37",  
    "highPrice": "47550.01",  
    "lowPrice": "45555.5",  
    "volume": "1732.461487",  
    "quoteVolume": null,  
    "openTime": 1641349500000,  
    "closeTime": 1641349582808,  
    "count": null  
}  
or  
[  
  {  
    "symbol": "BTCUSDT",  
    "priceChange": "184.34",  
    "priceChangePercent": "0.00400048",  
    "prevClosePrice": "46079.37",  
    "lastPrice": "46263.71",  
    "bidPrice": "46260.38",  
    "bidQty": "",  
    "askPrice": "46260.41",  
    "askQty": "",  
    "openPrice": "46079.37",  
    "highPrice": "47550.01",  
    "lowPrice": "45555.5",  
    "volume": "1732.461487",  
    "quoteVolume": null,  
    "openTime": 1641349500000,  
    "closeTime": 1641349582808,  
    "count": null  
  },  
  {  
    "symbol": "ETHUSDT",  
    "priceChange": "184.34",  
    "priceChangePercent": "0.00400048",  
    "prevClosePrice": "46079.37",  
    "lastPrice": "46263.71",  
    "bidPrice": "46260.38",  
    "bidQty": "",  
    "askPrice": "46260.41",  
    "askQty": "",  
    "openPrice": "46079.37",  
    "highPrice": "47550.01",  
    "lowPrice": "45555.5",  
    "volume": "1732.461487",  
    "quoteVolume": null,  
    "openTime": 1641349500000,  
    "closeTime": 1641349582808,  
    "count": null  
  }  
]
```

* **GET** `/api/v3/ticker/24hr`

**Weight(IP):** 25

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | string | NO | If the symbol is not sent, tickers for all symbols will be returned in an array. |

Response:

| Name | Description |
| --- | --- |
| symbol | Symbol |
| priceChange | price Change |
| priceChangePercent | price change percent |
| prevClosePrice | Previous close price |
| lastPrice | Last price |
| lastQty | Last quantity |
| bidPrice | Bid best price |
| bidQty | Bid best quantity |
| askPrice | Ask best price |
| askQty | Ask best quantity |
| openPrice | Open |
| highPrice | High |
| lowPrice | Low |
| volume | Deal volume |
| quoteVolume | Quote asset volume |
| openTime | Start time |
| closeTime | Close time |
| count |  |

Symbol Price Ticker[​](#symbol-price-ticker "Direct link to Symbol Price Ticker")
---------------------------------------------------------------------------------

> Response

```
{  
    "symbol": "BTCUSDT",  
    "price": "184.34"  
}  
or  
[  
  {  
    "symbol": "BTCUSDT",  
    "price": "6.65"  
  },  
  {  
    "symbol": "ETHUSDT",  
    "price": "5.65"  
  }  
]
```

* **GET** `/api/v3/ticker/price`

**Weight(IP):** 10

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | string | NO | If the symbol is not sent, all symbols will be returned in an array. |

Response:

| Name | Description |
| --- | --- |
| symbol |  |
| price | Last price |

Symbol Order Book Ticker[​](#symbol-order-book-ticker "Direct link to Symbol Order Book Ticker")
------------------------------------------------------------------------------------------------

> Response

```
{  
  "symbol": "AEUSDT",  
  "bidPrice": "0.11001",  
  "bidQty": "115.59",  
  "askPrice": "0.11127",  
  "askQty": "215.48"  
}  
OR  
[  
  {  
    "symbol": "AEUSDT",  
    "bidPrice": "0.11001",  
    "bidQty": "115.59",  
    "askPrice": "0.11127",  
    "askQty": "215.48"  
  },  
  {  
    "symbol": "AEUSDT",  
    "bidPrice": "0.11001",  
    "bidQty": "115.59",  
    "askPrice": "0.11127",  
    "askQty": "215.48"  
  }  
]
```

* **GET** `/api/v3/ticker/bookTicker`

**Weight(IP):** 10

Best price/qty on the order book for a symbol or symbols.

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | string | NO | If the symbol is not sent, all symbols will be returned in an array. |

Response:

| Name | Description |
| --- | --- |
| symbol | Symbol |
| bidPrice | Best bid price |
| bidQty | Best bid quantity |
| askPrice | Best ask price |
| askQty | Best ask quantity |

[Previous

General Info](/api-docs/spot-v3/general-info "PreviousGeneral Info")[Next

Sub-Account Endpoints(Only supports main account API key)](/api-docs/spot-v3/subaccount-endpoints "NextSub-Account Endpoints(Only supports main account API key)")

* [Download Historical Market Data](#download-historical-market-data "Download Historical Market Data")
* [Test Connectivity](#test-connectivity "Test Connectivity")
* [Check Server Time](#check-server-time "Check Server Time")
* [API default symbol](#api-default-symbol "API default symbol")
* [Query Offline Symbols](#query-offline-symbols "Query Offline Symbols")
* [Exchange Information](#exchange-information "Exchange Information")
* [Order Book](#order-book "Order Book")
* [Recent Trades List](#recent-trades-list "Recent Trades List")
* [Compressed/Aggregate Trades List](#compressedaggregate-trades-list "Compressed/Aggregate Trades List")
* [Kline/Candlestick Data](#klinecandlestick-data "Kline/Candlestick Data")
* [Current Average Price](#current-average-price "Current Average Price")
* [24hr Ticker Price Change Statistics](#24hr-ticker-price-change-statistics "24hr Ticker Price Change Statistics")
* [Symbol Price Ticker](#symbol-price-ticker "Symbol Price Ticker")
* [Symbol Order Book Ticker](#symbol-order-book-ticker "Symbol Order Book Ticker")

![](https://www.mexc.com/akam/13/pixel_7a0ac5a5?a=dD0wYmVjNTk3OGFlMmYyMzQ1MWFjN2JmOWUyMWU5NDVlNTNmYzEwNzI3JmpzPW9mZg==)