_Source: https://www.mexc.com/api-docs/futures/market-endpoints_

_Fetched: 2026-04-04T04:30:21.181013Z_

Market Endpoints | MEXC API







[Skip to main content](#__docusaurus_skipToContent_fallback)

[![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)](https://www.mexc.com/)[SpotV3](/api-docs/spot-v3/introduction)[Futures](/api-docs/futures/update-log)[Broker](/api-docs/broker/mexc-broker-introduction)

[English](#)

* [English](/api-docs/futures/market-endpoints)
* [中文](/zh-MY/api-docs/futures/market-endpoints)

* [Update log](/api-docs/futures/update-log)
* [Integration Guide](/api-docs/futures/integration-guide)
* [Internationalization Support](/api-docs/futures/error-code)
* [Market Endpoints](/api-docs/futures/market-endpoints)
* [Account and Trading Endpoints](/api-docs/futures/account-and-trading-endpoints)
* [WebSocket API](/api-docs/futures/websocket-api)

On this page

Market Endpoints
================

APIs under the [Market Data] module do not require authentication.

Get Server Time[​](#get-server-time "Direct link to Get Server Time")
---------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/ping"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": 1761875313209  
}
```

* **GET** `/api/v1/contract/ping`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

None

Get Contract Info[​](#get-contract-info "Direct link to Get Contract Info")
---------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/detail"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": {  
        "symbol": "BTC_USDT",  
        "displayName": "BTC_USDT永续",  
        "displayNameEn": "BTC_USDT PERPETUAL",  
        "positionOpenType": 3,  
        "baseCoin": "BTC",  
        "quoteCoin": "USDT",  
        "baseCoinName": "BTC",  
        "quoteCoinName": "USDT",  
        "futureType": 1,  
        "settleCoin": "USDT",  
        "contractSize": 0.0001,  
        "minLeverage": 1,  
        "maxLeverage": 500,  
        "countryConfigContractMaxLeverage": 0,  
        "priceScale": 1,  
        "volScale": 0,  
        "amountScale": 4,  
        "priceUnit": 0.1,  
        "volUnit": 1,  
        "minVol": 1,  
        "maxVol": 400000,  
        "bidLimitPriceRate": 0.1,  
        "askLimitPriceRate": 0.1,  
        "takerFeeRate": 0.0004,  
        "makerFeeRate": 0.0001,  
        "maintenanceMarginRate": 0.001,  
        "initialMarginRate": 0.002,  
        "riskBaseVol": 4500000,  
        "riskIncrVol": 0,  
        "riskLongShortSwitch": 0,  
        "riskIncrMmr": 0,  
        "riskIncrImr": 0,  
        "riskLevelLimit": 1,  
        "priceCoefficientVariation": 0.004,  
        "indexOrigin": [  
            "BITGET",  
            "BYBIT",  
            "BINANCE",  
            "HTX",  
            "OKX",  
            "MEXC",  
            "KUCOIN"  
        ],  
        "state": 0,  
        "isNew": false,  
        "isHot": false,  
        "isHidden": false,  
        "conceptPlate": [  
            "mc-trade-zone-pow"  
        ],  
        "conceptPlateId": [  
            12  
        ],  
        "riskLimitType": "BY_VOLUME",  
        "maxNumOrders": [  
            200,  
            50  
        ],  
        "marketOrderMaxLevel": 20,  
        "marketOrderPriceLimitRate1": 0.2,  
        "marketOrderPriceLimitRate2": 0.005,  
        "triggerProtect": 0.1,  
        "appraisal": 0,  
        "showAppraisalCountdown": 0,  
        "automaticDelivery": 0,  
        "apiAllowed": false,  
        "depthStepList": [  
            "0.1",  
            "1",  
            "10",  
            "100"  
        ],  
        "limitMaxVol": 2500000,  
        "threshold": 0,  
        "baseCoinIconUrl": "https://public.mocortech.com/coin/F20250612182226438Ba037qttKoGcrm.png",  
        "id": 10,  
        "vid": "128f589271cb4951b03e71e6323eb7be",  
        "baseCoinId": "febc9973be4d4d53bb374476239eb219",  
        "createTime": 1591242684000,  
        "openingTime": 0,  
        "openingCountdownOption": 1,  
        "showBeforeOpen": true,  
        "isMaxLeverage": true,  
        "isZeroFeeRate": true,  
        "riskLimitMode": "CUSTOM",  
        "isZeroFeeSymbol": true,  
        "riskLimitCustom": [  
            {  
                "level": 1,  
                "maxVol": 50000,  
                "mmr": 0.001,  
                "imr": 0.002,  
                "maxLeverage": 500  
            },  
            {  
                "level": 2,  
                "maxVol": 60000,  
                "mmr": 0.004,  
                "imr": 0.005,  
                "maxLeverage": 200  
            },  
            {  
                "level": 3,  
                "maxVol": 250000,  
                "mmr": 0.005,  
                "imr": 0.01,  
                "maxLeverage": 100  
            },  
            {  
                "level": 4,  
                "maxVol": 1200000,  
                "mmr": 0.01,  
                "imr": 0.02,  
                "maxLeverage": 50  
            },  
            {  
                "level": 5,  
                "maxVol": 3000000,  
                "mmr": 0.02,  
                "imr": 0.05,  
                "maxLeverage": 20  
            },  
            {  
                "level": 6,  
                "maxVol": 4500000,  
                "mmr": 0.05,  
                "imr": 0.1,  
                "maxLeverage": 10  
            }  
        ],  
        "liquidationFeeRate": 0.0004,  
        "feeRateMode": "TIERED",  
        "leverageFeeRates": [],  
        "tieredFeeRates": [  
            {  
                "takerFeeRate": 0,  
                "makerFeeRate": 0,  
                "minTieredDealAmount": 0,  
                "maxTieredDealAmount": 10000000  
            },  
            {  
                "takerFeeRate": 0.0004,  
                "makerFeeRate": 0.0001,  
                "minTieredDealAmount": 10000001  
            }  
        ],  
        "tieredDealAmount": 0,  
        "tieredEffectiveDay": 0,  
        "tieredAppointContract": true,  
        "tieredExcludeContractId": true,  
        "tieredContractIds": [  
            10,  
            77,  
            1104  
        ],  
        "tieredExcludeZeroFee": false,  
        "type": 1,  
        "stopOnlyFair": false,  
        "statisticType": "FIXED",  
        "fixedStartTime": 1760544000000,  
        "fixedEndTime": 1763049600000  
    }  
}
```

* **GET** `/api/v1/contract/detail`

Rate limit: 10 time / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | false | Contract symbol |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| symbol | string | Contract symbol |
| displayName | string | Display name |
| displayNameEn | string | English display name |
| positionOpenType | int | Opening type: 1 Isolated, 2 Cross, 3 Both supported |
| baseCoin | string | Base currency, e.g., BTC |
| quoteCoin | string | Quote currency, e.g., USDT |
| settleCoin | string | Settlement currency, e.g., USDT |
| contractSize | decimal | Contract value |
| minLeverage | int | Minimum leverage |
| maxLeverage | int | Maximum leverage |
| priceScale | int | Price precision |
| volScale | int | Quantity precision |
| amountScale | int | Amount precision |
| priceUnit | int | Minimum price tick |
| volUnit | int | Minimum quantity step |
| minVol | decimal | Minimum order size (contracts) |
| maxVol | decimal | Maximum order size (contracts) |
| bidLimitPriceRate | decimal | Buy-side price limit ratio |
| askLimitPriceRate | decimal | Sell-side price limit ratio |
| takerFeeRate | decimal | Taker fee rate |
| makerFeeRate | decimal | Maker fee rate |
| maintenanceMarginRate | decimal | Maintenance margin rate |
| initialMarginRate | decimal | Initial margin rate |
| riskBaseVol | decimal | Base contracts |
| riskIncrVol | decimal | Incremental contracts |
| riskLongShortSwitch | int | Separate long/short risk limits switch; 0-off, 1-on |
| riskBaseVolLong | decimal | Base contracts - Long |
| riskIncrVolLong | decimal | Incremental contracts - Long |
| riskBaseVolShort | decimal | Base contracts - Short |
| riskIncrVolShort | decimal | Incremental contracts - Short |
| riskIncrMmr | decimal | Increment of maintenance margin rate |
| riskIncrImr | decimal | Increment of initial margin rate |
| riskLevelLimit | int | Number of risk limit tiers |
| priceCoefficientVariation | decimal | Coefficient for fair price deviation from index price |
| indexOrigin | `List<String>` | Index sources |
| state | int | Status: 0 enabled, 1 delivery, 2 delivered, 3 offline, 4 paused |
| apiAllowed | boolean | Whether API trading is allowed |
| conceptPlate | `List<String>` | Sector tags; corresponds to the `entryKey` of sector list |
| riskLimitType | string | Risk limit type: BY\_VOLUME (by contracts), BY\_VALUE (by position value) |
| maxNumOrders | `List<Integer>` | Max open orders: [Hedged mode max, One-way mode max] |
| type | int | Pair type: 1 normal, 2 suspended (default 1 normal) |

Get Transferable Currencies[​](#get-transferable-currencies "Direct link to Get Transferable Currencies")
---------------------------------------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/support_currencies"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": [  
        "STETH",  
        "MXSOL",  
        "CRV",  
        "USDT",  
        "DOGE",  
        "ATOM",  
        "WBTC",  
        "CHZ",  
        "XRP",  
        "XLM",  
        "LINK",  
        "TRX",  
        "BSV",  
        "BCH",  
        "SUI",  
        "DOT",  
        "FIL",  
        "MX",  
        "BTC",  
        "WLFI",  
        "SOL",  
        "AVAX",  
        "ETC",  
        "BNB",  
        "ETH",  
        "USDE",  
        "LTC",  
        "USDC",  
        "ADA"  
    ]  
}
```

* **GET** `/api/v1/contract/support_currencies`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

None

**Response Parameters:**

The `"data"` field is an array of strings. Each string represents a supported currency.

Get Contract Order Book Depth[​](#get-contract-order-book-depth "Direct link to Get Contract Order Book Depth")
---------------------------------------------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/depth/BTC_USDT"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": {  
        "asks": [  
            [  
                108779.2,  
                3240,  
                1  
            ],  
            [  
                108779.3,  
                3884,  
                1  
            ]  
        ],  
        "bids": [  
            [  
                108779.1,  
                3240,  
                1  
            ],  
            [  
                108779,  
                3884,  
                1  
            ]  
        ],  
        "version": 28111438870,  
        "timestamp": 1761879567135  
    }  
}
```

* **GET** `/api/v1/contract/depth/{symbol}`

Rate limit: 10 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |
| limit | int | false | Number of rows |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| asks | `List<Numeric[]>` | Ask depth |
| bids | `List<Numeric[]>` | Bid depth |
| version | long | Version |
| timestamp | long | System timestamp |

Note: `[411.8, 10, 1]` 411.8 is price，10 is the order numbers of the contract ,1 is the order quantity.

Get the Last N Depth Snapshots[​](#get-the-last-n-depth-snapshots "Direct link to Get the Last N Depth Snapshots")
------------------------------------------------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/depth_commits/BTC_USDT/20"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": [  
        {  
            "asks": [],  
            "bids": [  
                [  
                    3818.91,  
                    272,  
                    1  
                ]  
            ],  
            "version": 26457599299  
        },  
        {  
            "asks": [],  
            "bids": [  
                [  
                    3818.89,  
                    1524,  
                    3  
                ]  
            ],  
            "version": 26457599298  
        },  
        {  
            "asks": [],  
            "bids": [  
                [  
                    3818.89,  
                    1123,  
                    2  
                ]  
            ],  
            "version": 26457599297  
        },  
        {  
            "asks": [],  
            "bids": [  
                [  
                    3818.87,  
                    788,  
                    1  
                ]  
            ],  
            "version": 26457599296  
        },  
        {  
            "asks": [],  
            "bids": [  
                [  
                    3818.88,  
                    886,  
                    1  
                ]  
            ],  
            "version": 26457599295  
        }  
    ]  
}
```

* **GET** `/api/v1/contract/depth_commits/{symbol}/{limit}`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |
| limit | int | true | Number of rows |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| asks | `List<Numeric[]>` | Ask depth |
| bids | `List<Numeric[]>` | Bid depth |
| version | long | Version |

Get Index Price[​](#get-index-price "Direct link to Get Index Price")
---------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/index_price/BTC_USDT"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": {  
        "symbol": "BTC_USDT",  
        "indexPrice": 31103.4,  
        "timestamp": 1609829705178  
    }  
}
```

* **GET** `/api/v1/contract/index_price/{symbol}`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| symbol | string | Trading pair |
| indexPrice | decimal | Index price |
| timestamp | long | System timestamp |

Get Fair Price[​](#get-fair-price "Direct link to Get Fair Price")
------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/fair_price/BTC_USDT"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": {  
        "symbol": "BTC_USDT",  
        "fairPrice": 31103.4,  
        "timestamp": 1609829705178  
    }  
}
```

* **GET** `/api/v1/contract/fair_price/{symbol}`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| fairPrice | decimal | Fair price |
| timestamp | long | System timestamp |

Get Funding Rate[​](#get-funding-rate "Direct link to Get Funding Rate")
------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/funding_rate/BTC_USDT"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": {  
        "symbol": "BTC_USDT",  
        "fundingRate": 0.000018,  
        "maxFundingRate": 0.0018,  
        "minFundingRate": -0.0018,  
        "collectCycle": 8,  
        "nextSettleTime": 1761897600000,  
        "timestamp": 1761879755894  
    }  
}
```

* **GET** `/api/v1/contract/funding_rate/{symbol}`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| fundingRate | decimal | Funding rate |
| maxFundingRate | decimal | Funding rate ceiling |
| minFundingRate | decimal | Funding rate floor |
| collectCycle | int | Collection cycle |
| nextSettleTime | long | Next settlement time |
| timestamp | long | System timestamp |

Get Candlestick Data[​](#get-candlestick-data "Direct link to Get Candlestick Data")
------------------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/kline/BTC_USDT?interval=Min15&start=1609992674&end=1610113500"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": {  
        "time": [  
            1761876000,  
            1761876900,  
            1761877800,  
            1761878700,  
            1761879600  
        ],  
        "open": [  
            109573.9,  
            109006.4,  
            109301.5,  
            108725.9,  
            108794.7  
        ],  
        "close": [  
            109006.4,  
            109301.5,  
            108725.9,  
            108794.7,  
            108669.9  
        ],  
        "high": [  
            109628.1,  
            109426.2,  
            109350.2,  
            108913.8,  
            108815.1  
        ],  
        "low": [  
            108953.3,  
            109006.4,  
            108666.2,  
            108498.5,  
            108649.0  
        ],  
        "vol": [  
            5587051.0,  
            5739575.0,  
            5945477.0,  
            5863529.0,  
            1668892.0  
        ],  
        "amount": [  
            6.106243567181E7,  
            6.270099147368E7,  
            6.47966331717E7,  
            6.374986900458E7,  
            1.814907510911E7  
        ],  
        "realOpen": [  
            109574.0,  
            109010.0,  
            109301.4,  
            108726.0,  
            108794.8  
        ],  
        "realClose": [  
            109006.4,  
            109301.5,  
            108725.9,  
            108794.7,  
            108669.9  
        ],  
        "realHigh": [  
            109628.1,  
            109426.2,  
            109350.2,  
            108913.8,  
            108815.1  
        ],  
        "realLow": [  
            108953.3,  
            109010.0,  
            108666.2,  
            108498.5,  
            108649.0  
        ]  
    }  
}
```

* **GET** `/api/v1/contract/kline/{symbol}`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |
| interval | string | false | Interval: Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1, Week1, Month1. Default is Min1 if omitted |
| start | long | false | Start timestamp (seconds) |
| end | long | false | End timestamp (seconds) |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| open | double | Open |
| close | double | Close |
| high | double | High |
| low | double | Low |
| vol | double | Volume |
| time | long | Time window |

Notes:

1. The maximum number of data points per request is 2000. If your chosen start/end time and granularity exceed this limit, only 2000 data points will be returned. To obtain fine-grained data over a larger time span, make multiple requests with segmented time ranges.
2. If only the start time is provided, data from the start time to the current system time is returned. If only the end time is provided, the 2000 data points closest to the end time are returned. If neither is provided, the 2000 most recent data points relative to the current system time are returned.

Get Index Price Candles[​](#get-index-price-candles "Direct link to Get Index Price Candles")
---------------------------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/kline/index_price/BTC_USDT?interval=Min15&start=1609992674&end=1610113500"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": {  
        "time": [  
            1761876000,  
            1761876900,  
            1761877800,  
            1761878700,  
            1761879600  
        ],  
        "open": [  
            109620.6,  
            109057.0,  
            109358.4,  
            108788.3,  
            108857.6  
        ],  
        "close": [  
            109057.0,  
            109358.4,  
            108788.3,  
            108857.6,  
            108628.4  
        ],  
        "high": [  
            109685.6,  
            109474.8,  
            109408.0,  
            108963.7,  
            108872.3  
        ],  
        "low": [  
            109013.6,  
            109057.0,  
            108745.9,  
            108564.5,  
            108622.8  
        ],  
        "vol": [  
            0.0,  
            0.0,  
            0.0,  
            0.0,  
            0.0  
        ],  
        "amount": [  
            0.0,  
            0.0,  
            0.0,  
            0.0,  
            0.0  
        ],  
        "realOpen": [  
            109057.0,  
            109358.4,  
            108788.3,  
            108857.6,  
            108628.4  
        ],  
        "realClose": [  
            109057.0,  
            109358.4,  
            108788.3,  
            108857.6,  
            108628.4  
        ],  
        "realHigh": [  
            109057.0,  
            109358.4,  
            108788.3,  
            108857.6,  
            108628.4  
        ],  
        "realLow": [  
            109057.0,  
            109358.4,  
            108788.3,  
            108857.6,  
            108628.4  
        ]  
    }  
}
```

* **GET** `/api/v1/contract/kline/index_price/{symbol}`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |
| interval | string | false | Interval: Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1, Week1, Month1. Default is Min1 if omitted |
| start | long | false | Start timestamp (seconds) |
| end | long | false | End timestamp (seconds) |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| open | double | Open |
| close | double | Close |
| high | double | High |
| low | double | Low |
| vol | double | Volume |
| time | long | Time window |

Notes:

1. The maximum number of data points per request is 2000. If your chosen start/end time and granularity exceed this limit, only 2000 data points will be returned. To obtain fine-grained data over a larger time span, make multiple requests with segmented time ranges.
2. If only the start time is provided, data from the start time to the current system time is returned. If only the end time is provided, the 2000 data points closest to the end time are returned. If neither is provided, the 2000 most recent data points relative to the current system time are returned.

Get Fair Price Candles[​](#get-fair-price-candles "Direct link to Get Fair Price Candles")
------------------------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/kline/fair_price/BTC_USDT?interval=Min15&start=1609992674&end=1610113500"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": {  
        "time": [  
            1761876000,  
            1761876900,  
            1761877800,  
            1761878700,  
            1761879600  
        ],  
        "open": [  
            109573.9,  
            109003.9,  
            109304.4,  
            108726.1,  
            108794.9  
        ],  
        "close": [  
            109003.9,  
            109304.4,  
            108726.1,  
            108794.9,  
            108629.1  
        ],  
        "high": [  
            109631.6,  
            109421.8,  
            109353.0,  
            108904.4,  
            108810.6  
        ],  
        "low": [  
            108960.4,  
            109003.9,  
            108681.1,  
            108500.3,  
            108555.6  
        ],  
        "vol": [  
            0.0,  
            0.0,  
            0.0,  
            0.0,  
            0.0  
        ],  
        "amount": [  
            0.0,  
            0.0,  
            0.0,  
            0.0,  
            0.0  
        ],  
        "realOpen": [  
            109003.9,  
            109304.4,  
            108726.1,  
            108794.9,  
            108629.1  
        ],  
        "realClose": [  
            109003.9,  
            109304.4,  
            108726.1,  
            108794.9,  
            108629.1  
        ],  
        "realHigh": [  
            109003.9,  
            109304.4,  
            108726.1,  
            108794.9,  
            108629.1  
        ],  
        "realLow": [  
            109003.9,  
            109304.4,  
            108726.1,  
            108794.9,  
            108629.1  
        ]  
    }  
}
```

* **GET** `/api/v1/contract/kline/fair_price/{symbol}`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |
| interval | string | false | Interval: Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1, Week1, Month1. Default is Min1 if omitted |
| start | long | false | Start timestamp (seconds) |
| end | long | false | End timestamp (seconds) |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| open | double | Open |
| close | double | Close |
| high | double | High |
| low | double | Low |
| vol | double | Volume |
| time | long | Time window |

Notes:

1. The maximum number of data points per request is 2000. If your chosen start/end time and granularity exceed this limit, only 2000 data points will be returned. To obtain fine-grained data over a larger time span, make multiple requests with segmented time ranges.
2. If only the start time is provided, data from the start time to the current system time is returned. If only the end time is provided, the 2000 data points closest to the end time are returned. If neither is provided, the 2000 most recent data points relative to the current system time are returned.

Get Recent Trades[​](#get-recent-trades "Direct link to Get Recent Trades")
---------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/deals/BTC_USDT"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": [  
        {  
            "p": 109177.4,  
            "v": 14,  
            "T": 1,  
            "O": 1,  
            "M": 2,  
            "t": 1761883066648  
        },  
        {  
            "p": 109177.4,  
            "v": 12,  
            "T": 1,  
            "O": 1,  
            "M": 2,  
            "t": 1761883066624  
        }  
    ]  
}
```

* **GET** `/api/v1/contract/deals/{symbol}`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |
| limit | int | false | Number of results, max 100, default 100 if omitted |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| p | decimal | Trade price |
| v | decimal | Quantity |
| T | int | Trade side: 1 buy, 2 sell |
| O | int | Open/Close flag: 1 both taker and maker open; 2 both not open; 3 other; if 1, `vol` is added position |
| M | int | Self-trade: 1 yes, 2 no |
| t | long | Trade time |

Get Ticker (Contract Market Data)[​](#get-ticker-contract-market-data "Direct link to Get Ticker (Contract Market Data)")
-------------------------------------------------------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/ticker"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": {  
        "contractId": 10,  
        "symbol": "BTC_USDT",  
        "lastPrice": 109167.1,  
        "bid1": 109167,  
        "ask1": 109167.1,  
        "volume24": 954830625,  
        "amount24": 10374579341.00211,  
        "holdVol": 381485808,  
        "lower24Price": 106226,  
        "high24Price": 111553.8,  
        "riseFallRate": 0.014,  
        "riseFallValue": 1510.6,  
        "indexPrice": 109235,  
        "fairPrice": 109168.9,  
        "fundingRate": 0,  
        "maxBidPrice": 120158.5,  
        "minAskPrice": 98311.5,  
        "timestamp": 1761883095759,  
        "riseFallRates": {  
            "zone": "UTC+8",  
            "r": 0.014,  
            "v": 1510.6,  
            "r7": -0.0061,  
            "r30": -0.0343,  
            "r90": -0.0532,  
            "r180": 0.1329,  
            "r365": 0.5149  
        },  
        "riseFallRatesOfTimezone": [  
            -0.0157,  
            0.0083,  
            0.014  
        ]  
    }  
}
```

* **GET** `/api/v1/contract/ticker`

Rate limit: 10 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | false | Contract symbol |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| lastPrice | decimal | Last price |
| bid1 | decimal | Best bid |
| ask1 | decimal | Best ask |
| volume24 | decimal | 24h volume (in contracts) |
| amount24 | decimal | 24h turnover |
| holdVol | decimal | Open interest (contracts) |
| lower24Price | decimal | 24h low |
| high24Price | decimal | 24h high |
| riseFallRate | decimal | Change rate |
| riseFallValue | decimal | Change amount |
| indexPrice | decimal | Index price |
| fairPrice | decimal | Fair price |
| fundingRate | decimal | Funding rate |
| timestamp | long | Trade time |

Get Insurance Fund Balance[​](#get-insurance-fund-balance "Direct link to Get Insurance Fund Balance")
------------------------------------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/risk_reverse"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": [  
        {  
            "symbol": "BTC_USDT",  
            "currency": "USDT",  
            "available": 97284530.448634083318792525314410007362,  
            "timestamp": 1761883124789  
        }  
    ]  
}
```

* **GET** `/api/v1/contract/risk_reverse/{symbol}`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| symbol | string | Contract |
| currency | string | Settlement coin |
| available | decimal | Balance |
| timestamp | long | System timestamp |

Get Insurance Fund Balance History[​](#get-insurance-fund-balance-history "Direct link to Get Insurance Fund Balance History")
------------------------------------------------------------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/risk_reverse/history?symbol=BTC_USDT&page_num=1&page_size=20"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": {  
        "pageSize": 3,  
        "totalCount": 42,  
        "totalPage": 14,  
        "currentPage": 1,  
        "resultList": [  
            {  
                "symbol": "BTC_USDT",  
                "currency": "USDT",  
                "available": 97284530.448634083318792525314410007362,  
                "snapshotTime": 1761883200000  
            },  
            {  
                "symbol": "BTC_USDT",  
                "currency": "USDT",  
                "available": 97278356.693307391915362536014224404257,  
                "snapshotTime": 1761868800000  
            },  
            {  
                "symbol": "BTC_USDT",  
                "currency": "USDT",  
                "available": 97275052.998679590630831496951543806325,  
                "snapshotTime": 1761854400000  
            }  
        ]  
    }  
}
```

* **GET** `/api/v1/contract/risk_reverse/history`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |
| page\_num | int | true | Current page, default 1 |
| page\_size | int | true | Page size, default 20, max 100 |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| pageSize | int | Page size |
| totalCount | int | Total count |
| totalPage | int | Total pages |
| currentPage | int | Current page |
| resultList | list | Result set |
| symbol | string | Contract |
| currency | string | Settlement coin |
| available | decimal | Balance |
| snapshotTime | long | Snapshot time |

Get Funding Rate History[​](#get-funding-rate-history "Direct link to Get Funding Rate History")
------------------------------------------------------------------------------------------------

> Request Example

```
curl "https://api.mexc.com/api/v1/contract/funding_rate/history?symbol=BTC_USDT&page_num=1&page_size=20"
```

> Response Example

```
{  
    "success": true,  
    "code": 0,  
    "data": {  
        "pageSize": 3,  
        "totalCount": 1619,  
        "totalPage": 540,  
        "currentPage": 1,  
        "resultList": [  
            {  
                "symbol": "BTC_USDT",  
                "fundingRate": 0.000021,  
                "settleTime": 1761868800000,  
                "collectCycle": 8  
            },  
            {  
                "symbol": "BTC_USDT",  
                "fundingRate": 0.000032,  
                "settleTime": 1761840000000,  
                "collectCycle": 8  
            },  
            {  
                "symbol": "BTC_USDT",  
                "fundingRate": -0.000001,  
                "settleTime": 1761811200000,  
                "collectCycle": 8  
            }  
        ]  
    }  
}
```

* **GET** `/api/v1/contract/funding_rate/history`

Rate limit: 20 times / 2 seconds

**Request Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| symbol | string | true | Contract symbol |
| page\_num | int | true | Current page, default 1 |
| page\_size | int | true | Page size, default 20, max 1000 |

**Response Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| pageSize | int | Page size |
| totalCount | int | Total count |
| totalPage | int | Total pages |
| currentPage | int | Current page |
| resultList | list | Result set |
| symbol | string | Contract |
| fundingRate | decimal | Funding rate |
| settleTime | long | Settlement time |
| collectCycle | int | Funding cycle (hours) |

[Previous

Internationalization Support](/api-docs/futures/error-code)[Next

Account and Trading Endpoints](/api-docs/futures/account-and-trading-endpoints)

* [Get Server Time](#get-server-time)
* [Get Contract Info](#get-contract-info)
* [Get Transferable Currencies](#get-transferable-currencies)
* [Get Contract Order Book Depth](#get-contract-order-book-depth)
* [Get the Last N Depth Snapshots](#get-the-last-n-depth-snapshots)
* [Get Index Price](#get-index-price)
* [Get Fair Price](#get-fair-price)
* [Get Funding Rate](#get-funding-rate)
* [Get Candlestick Data](#get-candlestick-data)
* [Get Index Price Candles](#get-index-price-candles)
* [Get Fair Price Candles](#get-fair-price-candles)
* [Get Recent Trades](#get-recent-trades)
* [Get Ticker (Contract Market Data)](#get-ticker-contract-market-data)
* [Get Insurance Fund Balance](#get-insurance-fund-balance)
* [Get Insurance Fund Balance History](#get-insurance-fund-balance-history)
* [Get Funding Rate History](#get-funding-rate-history)