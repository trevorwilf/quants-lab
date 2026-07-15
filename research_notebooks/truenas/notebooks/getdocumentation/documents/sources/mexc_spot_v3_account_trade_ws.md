_Source: webscrape/mexc/mexc_spot_spot_account_trade.html (browser-rendered)_

_Loaded: 2026-04-04T04:30:30.167144Z_

Spot Account/Trade | MEXC API

[Skip to main content](#__docusaurus_skipToContent_fallback "Skip to main content")

[![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)](https://www.mexc.com/ "https://www.mexc.com/")[SpotV3](/api-docs/spot-v3/introduction "SpotV3")[Futures](/api-docs/futures/update-log "Futures")[Broker](/api-docs/broker/mexc-broker-introduction "Broker")

[English](# "English")

* [English](/api-docs/spot-v3/spot-account-trade "English")
* [中文](/zh-MY/api-docs/spot-v3/spot-account-trade "中文")

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

Spot Account/Trade
==================

Query KYC status[​](#query-kyc-status "Direct link to Query KYC status")
------------------------------------------------------------------------

> request

```
GET /api/v3/kyc/status?timestamp={{timestamp}}&signature={{signature}}
```

> response

```
{  
"status": "1"  
}
```

**GET** `/api/v3/kyc/status`

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 1

**Request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| timestamp | string | Yes | timestamp |
| signature | string | Yes | signature |

**Response**

| Name | Type | Description |
| --- | --- | --- |
| status | string | 1:Unverified 2:Primary kyc 3:Advanced kyc 4:Institutional kyc |

Query UID[​](#query-uid "Direct link to Query UID")
---------------------------------------------------

> request

```
GET /api/v3/uid?timestamp={{timestamp}}&signature={[{signature]}
```

> response

```
{  
"uid":"209302839"  
}
```

**GET** `/api/v3/uid`

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 1

**Request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| timestamp | string | Yes | timestamp |
| signature | string | Yes | signature |

**Response**

| Name | Type | Description |
| --- | --- | --- |
| uid | string | account uid |

User API default symbol[​](#user-api-default-symbol "Direct link to User API default symbol")
---------------------------------------------------------------------------------------------

> Request

```
GET /api/v3/selfSymbols?timestamp={{timestamp}}&signature={{signature}}
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

* **GET** `/api/v3/selfSymbols`

**Permission:** SPOT\_ACCOUNT\_R

**Weight(IP):** 1

**Request**

NONE

**Response**

| Name | Type | Description |
| --- | --- | --- |
| symbol | string | api trade symbol |

Test New Order[​](#test-new-order "Direct link to Test New Order")
------------------------------------------------------------------

> Response

```
{}
```

* **POST** `/api/v3/order/test`

**Permission:** SPOT\_DEAL\_WRITE

**Weight(IP):** 1

Creates and validates a new order but does not send it into the matching engine.

Parameters:

equaled POST /api/v3/order

New Order[​](#new-order "Direct link to New Order")
---------------------------------------------------

> Request

```
POST /api/v3/order?symbol=MXUSDT&side=BUY&type=LIMIT&quantity=50&price=0.1&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
{  
    "symbol": "MXUSDT",  
    "orderId": "06a480e69e604477bfb48dddd5f0b750",  
    "orderListId": -1,  
    "price": "0.1",  
    "origQty": "50",  
    "type": "LIMIT",  
    "side": "BUY",  
    "stpMode": "",  
    "transactTime": 1666676533741  
}
```

* **POST** `/api/v3/order`

**Permission:** SPOT\_DEAL\_WRITE

**Rate limit:** Shared with the cancel order endpoint, 12 requests/second

Parameters:

| Name | type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | STRING | YES |  |
| side | ENUM | YES | ENUM: [Order Side](/api-docs/spot-v3/public-api-definitions#order-side "Order Side") |
| type | ENUM | YES | ENUM: [Order Type](/api-docs/spot-v3/public-api-definitions#order-type "Order Type") |
| quantity | DECIMAL | NO | Quantity |
| quoteOrderQty | DECIMAL | NO | Quote order quantity |
| price | DECIMAL | NO | Price |
| newClientOrderId | STRING | NO |  |
| stpMode | STRING | NO | “” - Default value, no restriction on self-trading.“cancel\_maker” - Cancel the maker order.“cancel\_taker” - Cancel the taker order.“cancel\_both” - Cancel both sides. |
| recvWindow | LONG | NO | Max 60000 |
| timestamp | LONG | YES |  |

Response:

| Name | Description |
| --- | --- |
| symbol | Symbol |
| orderId | order id |
| orderListId | order list id |
| price | Price |
| origQty | Original order quantity |
| type | ENUM: [Order Type](/api-docs/spot-v3/public-api-definitions#order-type "Order Type") |
| side | ENUM: [Order Side](/api-docs/spot-v3/public-api-definitions#order-side "Order Side") |
| stpMode | “” - Default value, no restriction on self-trading.“cancel\_maker” - Cancel the maker order.“cancel\_taker” - Cancel the taker order.“cancel\_both” - Cancel both sides. |
| transactTime | transactTime |

Additional mandatory parameters based on `type`:

| Type | Additional mandatory parameters |
| --- | --- |
| `LIMIT` | `quantity`, `price` |
| `MARKET` | `quantity` or `quoteOrderQty` |

Other info:

1. The default value of stpMode is "", meaning no self-trade prevention check.
2. Conditions for self-trade prevention to take effect:

* At least one strategy group must be created;
* The stpMode parameter must not be empty;

3. For other self-trade issues, please refer to: [Introduction to Self-Trade Prevention](https://www.mexc.com/zh-MY/announcements/article/introduction-to-self-trade-prevention-stp-17827791526132 "Introduction to Self-Trade Prevention");
4. When stpMode = "", self-trading is not restricted.

MARKET: When type is market, `quoteOrderQty` or `quantity` required to choose anyone.

* `MARKET` orders using the `quantity` field specifies the amount of the `base asset` the user wants to sell at the market price
  + For example, sending a `MARKET` order on BTCUSDT will specify how much BTC the user is selling.
* `MARKET` orders using `quoteOrderQty` specifies the amount the user wants to spend (when buying) the `quote` asset; the correct `quantity` will be determined based on the market liquidity
  + Using BTCUSDT as an example:
    - On the `BUY` side, the order will buy as many BTC as `quoteOrderQty` USDT can.
    - On the `SELL` side, the order will sell the `quantity` of BTC.

Batch Orders[​](#batch-orders "Direct link to Batch Orders")
------------------------------------------------------------

Supports 20 orders with a same symbol in a batch,rate limit:2 times/s.

> Request

```
POST /api/v3/batchOrders?batchOrders=[{"type": "LIMIT_ORDER","price": "40000","quantity": "0.0002","symbol": "BTCUSDT","side": "BUY","newClientOrderId": 9588234},{"type": "LIMIT_ORDER","price": "4005","quantity": "0.0003","symbol": "BTCUSDT","side": "SELL"}]
```

> Response

```
{  
  { //success response:  
   [  
     {     
       "symbol": "BTCUSDT",     
       "orderId": "1196315350023612316",     
       "orderListId": -1   
     },  
     {     
       "symbol": "BTCUSDT",     
       "orderId": "1196315350023612318",     
       "orderListId": -1   
     }  
   ],  
   //error response:  
   [  
     {   
       "symbol": "BTCUSDT",   
       "orderId": "1196315350023612316",   
       "newClientOrderId": "hio8279hbdsds",   
       "orderListId": -1   
     },  
     {   
       "newClientOrderId": "123456",  
       "msg": "The minimum transaction volume cannot be less than:0.5USDT",   
       "code": 30002  
     },  
     {   
       "symbol": "BTCUSDT",   
       "orderId": "1196315350023612318",   
       "orderListId": -1   
     }  
   ]   
 }  
}
```

* **POST** `/api/v3/batchOrders`

**Permission:** SPOT\_DEAL\_WRITE

**Rate limit:** Shared with the cancel order endpoint, 12 requests/second

Parameters:

| Name | type | Mandatory | Description |
| --- | --- | --- | --- |
| batchOrders | LIST | YES | list of batchOrders,supports max 20 orders |
| symbol | STRING | YES | symbol |
| side | ENUM | YES | ENUM: [Order Side](/api-docs/spot-v3/public-api-definitions#order-side "Order Side") |
| type | ENUM | YES | ENUM: [Order Type](/api-docs/spot-v3/public-api-definitions#order-type "Order Type") |
| quantity | DECIMAL | NO | quantity |
| quoteOrderQty | DECIMAL | NO | quoteOrderQty |
| price | DECIMAL | NO | order price |
| newClientOrderId | STRING | NO | ClientOrderId |
| stpMode | STRING | NO | “” - Default value, no restriction on self-trading.“cancel\_maker” - Cancel the maker order.“cancel\_taker” - Cancel the taker order.“cancel\_both” - Cancel both sides. |
| recvWindow | LONG | NO | less than 60000 |
| timestamp | LONG | YES | order time |

base on different`type`,some params are mandatory:

| type | Mandatory params |
| --- | --- |
| `LIMIT` | `quantity`, `price` |
| `MARKET` | `quantity` or `quoteOrderQty` |

Response

| Name | type | Description |
| --- | --- | --- |
| symbol | STRING | symbol |
| orderId | STRING | orderId |

Cancel Order[​](#cancel-order "Direct link to Cancel Order")
------------------------------------------------------------

> Response

```
{  
  "symbol": "LTCBTC",  
  "origClientOrderId": "myOrder1",  
  "orderId": 4,  
  "clientOrderId": "cancelMyOrder1",  
  "price": "2.00000000",  
  "origQty": "1.00000000",  
  "executedQty": "0.00000000",  
  "cummulativeQuoteQty": "0.00000000",  
  "status": "CANCELED",  
  "type": "LIMIT",  
  "side": "BUY"  
}
```

* **DELETE** `/api/v3/order`

**Permission:** SPOT\_DEAL\_WRITE

**Rate limit:** Shared with the order endpoint, 12 requests/second

Cancel an active order.

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | string | YES |  |
| orderId | string | NO | Order id |
| origClientOrderId | string | NO |  |
| newClientOrderId | string | NO |  |
| recvWindow | long | NO |  |
| timestamp | long | YES |  |

Either `orderId` or `origClientOrderId` must be sent.

Response:

| Name | Description |
| --- | --- |
| symbol | Symbol |
| origClientOrderId | Original client order id |
| orderId | order id |
| clientOrderId | client order id |
| price | Price |
| origQty | Original order quantity |
| executedQty | Executed order quantity |
| cummulativeQuoteQty | Cummulative quote quantity |
| status | ENUM: [Order Status](/api-docs/spot-v3/public-api-definitions#order-status "Order Status") |
| type | ENUM: [Order Type](/api-docs/spot-v3/public-api-definitions#order-type "Order Type") |
| side | ENUM: [Order Side](/api-docs/spot-v3/public-api-definitions#order-side "Order Side") |

Cancel all Open Orders on a Symbol[​](#cancel-all-open-orders-on-a-symbol "Direct link to Cancel all Open Orders on a Symbol")
------------------------------------------------------------------------------------------------------------------------------

> Response

```
[  
  {  
    "symbol": "BTCUSDT",  
    "origClientOrderId": "E6APeyTJvkMvLMYMqu1KQ4",  
    "orderId": 11,  
    "orderListId": -1,  
    "clientOrderId": "pXLV6Hz6mprAcVYpVMTGgx",  
    "price": "0.089853",  
    "origQty": "0.178622",  
    "executedQty": "0.000000",  
    "cummulativeQuoteQty": "0.000000",  
    "status": "CANCELED",  
    "type": "LIMIT",  
    "side": "BUY"  
  },  
  {  
    "symbol": "BTCUSDT",  
    "origClientOrderId": "A3EF2HCwxgZPFMrfwbgrhv",  
    "orderId": 13,  
    "orderListId": -1,  
    "clientOrderId": "pXLV6Hz6mprAcVYpVMTGgx",  
    "price": "0.090430",  
    "origQty": "0.178622",  
    "executedQty": "0.000000",  
    "cummulativeQuoteQty": "0.000000",  
    "status": "CANCELED",  
    "type": "LIMIT",  
    "side": "BUY"  
  }  
]
```

* **DELETE** `/api/v3/openOrders`

**Permission:** SPOT\_DEAL\_WRITE

**Rate limit:** Shared with the place order endpoint, 12 requests/second

Cancel all pending orders for a single symbol, including OCO pending orders.

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | string | YES |  |
| recvWindow | long | NO |  |
| timestamp | long | YES |  |

Response:

| Name | Description |
| --- | --- |
| symbol | Symbol |
| origClientOrderId | Original client order id |
| orderId | order id |
| clientOrderId | client order id |
| price | Price |
| origQty | Original order quantity |
| executedQty | Executed order quantity |
| cummulativeQuoteQty | Cummulative quote quantity |
| status | ENUM: [Order Status](/api-docs/spot-v3/public-api-definitions#order-status "Order Status") |
| type | ENUM: [Order Type](/api-docs/spot-v3/public-api-definitions#order-type "Order Type") |
| side | ENUM: [Order Side](/api-docs/spot-v3/public-api-definitions#order-side "Order Side") |

Query Order[​](#query-order "Direct link to Query Order")
---------------------------------------------------------

> Response

```
{  
  "symbol": "LTCBTC",  
  "orderId": 1,  
  "orderListId": -1,  
  "clientOrderId": "myOrder1",  
  "price": "0.1",  
  "Qty": "1.0",  
  "executedQty": "0.0",  
  "cummulativeQuoteQty": "0.0",  
  "status": "NEW",  
  "timeInForce": "GTC",  
  "type": "LIMIT",  
  "side": "BUY",  
  "stopPrice": "0.0",  
  "time": 1499827319559,  
  "updateTime": 1499827319559,  
  "stpMode":"",   
  "cancelReason":"stp_cancel",   
  "isWorking": true,  
  "origQuoteOrderQty": "0.000000"  
}
```

* **GET** `/api/v3/order`

**Permission:** SPOT\_DEAL\_READ

**Weight(IP):** 2

Check an order's status.

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | String | YES |  |
| origClientOrderId | String | NO |  |
| orderId | String | NO |  |
| recvWindow | long | NO |  |
| timestamp | long | YES |  |

Response:

| Name | Description |
| --- | --- |
| symbol | Symbol |
| origClientOrderId | Original client order id |
| orderId | order id |
| clientOrderId | client order id |
| price | Price |
| Qty | Original order quantity |
| executedQty | Executed order quantity |
| cummulativeQuoteQty | Cummulative quote quantity |
| status | ENUM: [Order Status](/api-docs/spot-v3/public-api-definitions#order-status "Order Status") |
| timeInForce |  |
| type | ENUM: [Order Type](/api-docs/spot-v3/public-api-definitions#order-type "Order Type") |
| side | ENUM: [Order Side](/api-docs/spot-v3/public-api-definitions#order-side "Order Side") |
| stopPrice | stop price |
| time | Order created time |
| updateTime | Last update time |
| isWorking | is orderbook |
| stpMode | “” - Default value, no restriction on self-trading.“cancel\_maker” - Cancel the maker order.“cancel\_taker” - Cancel the taker order.“cancel\_both” - Cancel both sides. |
| cancelReason | cancel reason.stp\_cancel: canceled due to STP rules. |

Current Open Orders[​](#current-open-orders "Direct link to Current Open Orders")
---------------------------------------------------------------------------------

> Response

```
[  
  {  
    "symbol": "LTCBTC",  
    "orderId": 1,  
    "orderListId": -1,   
    "clientOrderId": "myOrder1",  
    "price": "0.1",  
    "origQty": "1.0",  
    "executedQty": "0.0",  
    "cummulativeQuoteQty": "0.0",  
    "status": "NEW",  
    "timeInForce": "GTC",  
    "type": "LIMIT",  
    "side": "BUY",  
    "stopPrice": "0.0",  
    "icebergQty": "0.0",  
    "time": 1499827319559,  
    "updateTime": 1499827319559,  
    "isWorking": true,  
    "stpMode":"",   
    "cancelReason":"stp_cancel",   
    "origQuoteOrderQty": "0.000000"  
  }  
]
```

* **GET** `/api/v3/openOrders`

**Permission:** SPOT\_DEAL\_READ

**Weight(IP):** 3

Get all open orders on a symbol. **Careful** when accessing this with no symbol.

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | string | NO |  |
| recvWindow | long | NO |  |
| timestamp | long | YES |  |

Response:

| Name | Description |
| --- | --- |
| symbol | Symbol |
| origClientOrderId | Original client order id |
| orderId | order id |
| clientOrderId | client order id |
| price | Price |
| origQty | Original order quantity |
| executedQty | Executed order quantity |
| cummulativeQuoteQty | Cummulative quote quantity |
| status | ENUM: [Order Status](/api-docs/spot-v3/public-api-definitions#order-status "Order Status") |
| timeInForce |  |
| type | ENUM: [Order Type](/api-docs/spot-v3/public-api-definitions#order-type "Order Type") |
| side | ENUM: [Order Side](/api-docs/spot-v3/public-api-definitions#order-side "Order Side") |
| stopPrice | stop price |
| time | Order created time |
| updateTime | Last update time |
| isWorking | is orderbook |
| stpMode | “” - Default value, no restriction on self-trading.“cancel\_maker” - Cancel the maker order.“cancel\_taker” - Cancel the taker order.“cancel\_both” - Cancel both sides. |
| cancelReason | cancel reason.stp\_cancel: canceled due to STP rules. |

All Orders[​](#all-orders "Direct link to All Orders")
------------------------------------------------------

> Response

```
[  
  {  
    "symbol": "LTCBTC",  
    "orderId": 1,  
    "orderListId": -1,   
    "clientOrderId": "myOrder1",  
    "price": "0.1",  
    "origQty": "1.0",  
    "executedQty": "0.0",  
    "cummulativeQuoteQty": "0.0",  
    "status": "NEW",  
    "timeInForce": "GTC",  
    "type": "LIMIT",  
    "side": "BUY",  
    "stopPrice": "0.0",  
    "icebergQty": "0.0",  
    "time": 1499827319559,  
    "updateTime": 1499827319559,  
    "isWorking": true,  
    "stpMode":"",   
    "origQuoteOrderQty": "0.000000"  
  }  
]
```

* **GET** `/api/v3/allOrders`

**Permission:** SPOT\_DEAL\_READ

**Weight(IP):** 10

Get all account orders including active, cancelled or completed orders(the query period is the latest 24 hours by default). You can query a maximum of the latest 7 days.

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | string | YES | Symbol |
| startTime | long | NO |  |
| endTime | long | NO |  |
| limit | int | NO | Default 500; max 1000; |
| recvWindow | long | NO |  |
| timestamp | long | YES |  |

Response:

| Name | Description |
| --- | --- |
| symbol | Symbol |
| origClientOrderId | Original client order id |
| orderId | order id |
| clientOrderId | client order id |
| price | Price |
| origQty | Original order quantity |
| executedQty | Executed order quantity |
| cummulativeQuoteQty | Cummulative quote quantity |
| status | ENUM: [Order Status](/api-docs/spot-v3/public-api-definitions#order-status "Order Status") |
| timeInForce |  |
| type | ENUM: [Order Type](/api-docs/spot-v3/public-api-definitions#order-type "Order Type") |
| side | ENUM: [Order Side](/api-docs/spot-v3/public-api-definitions#order-side "Order Side") |
| stopPrice | stop price |
| time | Order created time |
| updateTime | Last update time |
| isWorking | is orderbook |
| stpMode | “” - Default value, no restriction on self-trading.“cancel\_maker” - Cancel the maker order.“cancel\_taker” - Cancel the taker order.“cancel\_both” - Cancel both sides. |
| origQuoteOrderQty |  |

Account Information[​](#account-information "Direct link to Account Information")
---------------------------------------------------------------------------------

> Response

```
{  
    "makerCommission": null,  
    "takerCommission": null,  
    "buyerCommission": null,  
    "sellerCommission": null,  
    "canTrade": true,  
    "canWithdraw": true,  
    "canDeposit": true,  
    "updateTime": null,  
    "accountType": "SPOT",  
    "balances": [{  
        "asset": "NBNTEST",  
        "free": "1111078",  
        "locked": "33",  
        "available": "1"  
    }, {  
        "asset": "MAIN",  
        "free": "1020000",  
        "locked": "0",  
        "available": "102000"  
    }],  
    "permissions": ["SPOT"]  
}
```

* **GET** `/api/v3/account`

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 10

Get current account information,rate limit:2 times/s.

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| recvWindow | long | NO |  |
| timestamp | long | YES |  |

Response:

| Name | Description |
| --- | --- |
| canTrade | Can Trade |
| canWithdraw | Can Withdraw |
| canDeposit | Can Deposit |
| updateTime | Update Time |
| accountType | Account type |
| balances | Balance |
| asset | Asset coin |
| free | Free coin |
| locked | Forzen coin |
| available | Available coin |
| permissions | Permission |

Account Trade List[​](#account-trade-list "Direct link to Account Trade List")
------------------------------------------------------------------------------

> Response

```
[  
  {  
    "symbol": "BNBBTC",  
    "id": "fad2af9e942049b6adbda1a271f990c6",  
    "orderId": "bb41e5663e124046bd9497a3f5692f39",  
    "orderListId": -1,  
    "price": "4.00000100",   
    "qty": "12.00000000",   
    "quoteQty": "48.000012",   
    "commission": "10.10000000",   
    "commissionAsset": "BNB",   
    "time": 1499865549590,   
    "isBuyer": true,   
    "isMaker": false,   
    "isBestMatch": true,  
    "isSelfTrade": true,  
    "clientOrderId": null  
  }  
]
```

* **GET** `/api/v3/myTrades`

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 10

Get trades for a specific account and symbol,Only the transaction records in the past 1 month can be queried. If you want to view more transaction records, please use the export function on the web side, which supports exporting transaction records of the past 540 days at most.

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | string | YES |  |
| orderId | string | NO | order Id |
| startTime | long | NO |  |
| endTime | long | NO |  |
| limit | int | NO | Default 100; max 100; |
| recvWindow | long | NO |  |
| timestamp | long | YES |  |

Response:

| Name | Description |
| --- | --- |
| symbol |  |
| id | deal id |
| orderId | order id |
| price | Price |
| qty | Quantity |
| quoteQty | Deal quantity |
| time | Deal time |
| commission |  |
| commissionAsset |  |
| time | trade time |
| isBuyerMaker |  |
| isBestMatch |  |
| isSelfTrade | isSelfTrade |
| clientOrderId | clientOrderId |

Enable MX Deduct[​](#enable-mx-deduct "Direct link to Enable MX Deduct")
------------------------------------------------------------------------

Enable or disable MX deduct for spot commission fee

> Request

```
post api/v3/mxDeduct/enable
```

> Response

```
{  
  "data":{  
    "mxDeductEnable":true  
  },  
  "code":0,  
  "msg":"success",  
  "timestamp":1669109672280  
}
```

* **POST** `api/v3/mxDeduct/enable`

**Permission:** SPOT\_DEAL\_WRITE

**Weight(IP):** 1

**Parameters:**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| mxDeductEnable | boolean | yes | true:enable,false:disable |
| recvWindow | long | no | recvWindow |
| timestamp | long | yes | timestamp |
| signature | string | yes | signature |

**Response:**

| Name | Type | Description |
| --- | --- | --- |
| mxDeductEnable | boolean | true:enable,false:disable |

Query MX Deduct Status[​](#query-mx-deduct-status "Direct link to Query MX Deduct Status")
------------------------------------------------------------------------------------------

> Request

```
get api/v3/mxDeduct/enable
```

> Response

```
{  
  "data":{  
    "mxDeductEnable":false  
  },  
  "code":0,  
  "msg":"success",  
  "timestamp":1669109672717  
}
```

* **GET** `api/v3/mxDeduct/enable`

**Permission:** SPOT\_DEAL\_READ

**Weight(IP):** 1

**Parameters:**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| recvWindow | long | no | recvWindow |
| timestamp | long | yes | timestamp |
| signature | string | yes | signature |

**Response:**

| Name | Type | Description |
| --- | --- | --- |
| mxDeductEnable | boolean | true:enable,false:disable |

Query Symbol Commission[​](#query-symbol-commission "Direct link to Query Symbol Commission")
---------------------------------------------------------------------------------------------

> request

```
get api/v3/tradeFee?symbol=MXUSDT&timestamp={{timestamp}}&signature={{signature}}
```

> return

```
{  
  "data":{  
    "makerCommission":0.003000000000000000,  
    "takerCommission":0.003000000000000000  
  },  
  "code":0,  
  "msg":"success",  
  "timestamp":1669109672717  
}
```

* **GET** `api/v3/tradeFee`

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 20

**request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| symbol | string | yes | symbol |
| recvWindow | long | no | recvWindow |
| timestamp | long | yes | timestamp |
| signature | string | yes | signature |

**return**

| Name | Type | Description |
| --- | --- | --- |
| makerCommission | long | User Maker Commission |
| takerCommission | long | User Taker Commission |

Create STP strategy group[​](#create-stp-strategy-group "Direct link to Create STP strategy group")
---------------------------------------------------------------------------------------------------

> request

```
post /api/v3/strategy/group?tradeGroupName=tradeGroupOne&timestamp={{timestamp}}&signature={{signature}}
```

> return

```
{  
    "data": {  
        "tradeGroupName": "tradeGroupOne",  
        "tradeGroupId": 91,  
        "createTime": 1758043350000,  
        "updateTime": 1758043350000  
    },  
    "code": 200,  
    "msg": "success",  
    "timestamp": 1758043350233  
}
```

* **POST** `/api/v3/strategy/group`

**Permission:** SPOT\_ACCOUNT\_WRITE

**Weight(IP):** 20

**request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| tradeGroupName | string | yes | stp strategy group name |
| timestamp | long | yes | timestamp |
| signature | string | yes | signature |

**return**

| Name | Type | Description |
| --- | --- | --- |
| tradeGroupName | string | stp strategy group name |
| tradeGroupId | string | stp strategy group id |
| createTime | long | create time |

Precautions:

* Only the master account is allowed to create; sub-accounts cannot operate this endpoint
* The STP strategy group name must be unique under the same master account
* The STP strategy group ID is unique
* A master account can have up to 10 strategy groups

Query STP strategy group[​](#query-stp-strategy-group "Direct link to Query STP strategy group")
------------------------------------------------------------------------------------------------

> request

```
get /api/v3/strategy/group?tradeGroupName=tradeGroupOne&timestamp={{timestamp}}&signature={{signature}}
```

> return

```
{  
    "data": [  
        {  
            "tradeGroupName": "tradeGroupNameOne",  
            "tradeGroupId": 91,  
            "createTime": 1758043350000,  
            "updateTime": 1758043350000  
        }  
    ],  
    "code": 200,  
    "msg": "success",  
    "timestamp": 1758044090972  
}
```

* **GET** `/api/v3/strategy/group`

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 20

**request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| tradeGroupName | string | yes | stp strategy group name |
| timestamp | long | yes | timestamp |
| signature | string | yes | signature |

**return**

| Name | Type | Description |
| --- | --- | --- |
| tradeGroupName | string | stp strategy group name |
| tradeGroupId | string | stp strategy group id |
| tradeGroupUid | string | UIDs contained in stp strategy group, separated by , |
| updateTime | long | update time |
| createTime | long | create time |

Delete STP strategy group[​](#delete-stp-strategy-group "Direct link to Delete STP strategy group")
---------------------------------------------------------------------------------------------------

> request

```
delete /api/v3/strategy/group?tradeGroupId=91&timestamp={{timestamp}}&signature={{signature}}
```

> return

```
{  
    "data": true,  
    "code": 200,  
    "msg": "success",  
    "timestamp": 1758044399749  
}
```

* **DELETE** `/api/v3/strategy/group`

**Permission:** SPOT\_ACCOUNT\_W

**Weight(IP):** 20

**request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| tradeGroupId | string | yes | stp strategy group id |
| timestamp | long | yes | timestamp |
| signature | string | yes | signature |

**return**

| Name | Type | Description |
| --- | --- | --- |
| msg | string | delete status |

Precautions:

* Only the master account is allowed to delete; sub-accounts cannot access
* Only strategy groups under the current master account can be operated; cross-master-account operations are not allowed

Add uid to STP strategy group[​](#add-uid-to-stp-strategy-group "Direct link to Add uid to STP strategy group")
---------------------------------------------------------------------------------------------------------------

> request

```
post /api/v3/strategy/group/uid?uid=49910594&ttradeGroupId=92&timestamp={{timestamp}}&signature={{signature}}
```

> return

```
{  
    "data": {  
        "tradeGroupName": "1",  
        "tradeGroupId": 92,  
        "tradeGroupUid": "49910594",  
        "createTime": 1758044671000,  
        "updateTime": 1758044777000  
    },  
    "code": 200,  
    "msg": "success",  
    "timestamp": 1758044777023  
}
```

* **GET** `/api/v3/strategy/group/uid`

**Permission:** SPOT\_ACCOUNT\_WRITE

**Weight(IP):** 20

**request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| uid | string | yes | separated by , |
| tradeGroupId | string | yes | stp strategy group id |
| timestamp | long | yes | timestamp |
| signature | string | yes | signature |

**return**

| Name | Type | Description |
| --- | --- | --- |
| tradeGroupName | string | stp strategy group name |
| tradeGroupId | string | stp strategy group id |
| tradeGroupUid | string | UIDs just add, separated by , |
| updateTime | long | update time |

Precautions:

* Only the master account is allowed to add uid; sub-accounts cannot access
* Only strategy groups under the current master account can be operated; cross-master-account operations are not allowed

Delete uid to STP strategy group[​](#delete-uid-to-stp-strategy-group "Direct link to Delete uid to STP strategy group")
------------------------------------------------------------------------------------------------------------------------

> request

```
delete /api/v3/strategy/group/uid?uid=49910594&ttradeGroupId=92&timestamp={{timestamp}}&signature={{signature}}
```

> return

```
{  
    "data": true,  
    "code": 200,  
    "msg": "success",  
    "timestamp": 1758045403352  
}
```

* **DELETE** `/api/v3/strategy/group/uid`

**Permission:** SPOT\_ACCOUNT\_WRITE

**Weight(IP):** 20

**request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| uid | string | yes | separated by , |
| tradeGroupId | string | yes | stp strategy group id |
| timestamp | long | yes | timestamp |
| signature | string | yes | signature |

**return**

| Name | Type | Description |
| --- | --- | --- |
| msg | string | delete status |

Precautions:

* Only the main account is allowed to delete; sub-accounts cannot access
* Only strategy groups under the current master account can be operated; cross-master-account operations are not allowed

[Previous

Sub-Account Endpoints(Only supports main account API key)](/api-docs/spot-v3/subaccount-endpoints "PreviousSub-Account Endpoints(Only supports main account API key)")[Next

Wallet Endpoints](/api-docs/spot-v3/wallet-endpoints "NextWallet Endpoints")

* [Query KYC status](#query-kyc-status "Query KYC status")
* [Query UID](#query-uid "Query UID")
* [User API default symbol](#user-api-default-symbol "User API default symbol")
* [Test New Order](#test-new-order "Test New Order")
* [New Order](#new-order "New Order")
* [Batch Orders](#batch-orders "Batch Orders")
* [Cancel Order](#cancel-order "Cancel Order")
* [Cancel all Open Orders on a Symbol](#cancel-all-open-orders-on-a-symbol "Cancel all Open Orders on a Symbol")
* [Query Order](#query-order "Query Order")
* [Current Open Orders](#current-open-orders "Current Open Orders")
* [All Orders](#all-orders "All Orders")
* [Account Information](#account-information "Account Information")
* [Account Trade List](#account-trade-list "Account Trade List")
* [Enable MX Deduct](#enable-mx-deduct "Enable MX Deduct")
* [Query MX Deduct Status](#query-mx-deduct-status "Query MX Deduct Status")
* [Query Symbol Commission](#query-symbol-commission "Query Symbol Commission")
* [Create STP strategy group](#create-stp-strategy-group "Create STP strategy group")
* [Query STP strategy group](#query-stp-strategy-group "Query STP strategy group")
* [Delete STP strategy group](#delete-stp-strategy-group "Delete STP strategy group")
* [Add uid to STP strategy group](#add-uid-to-stp-strategy-group "Add uid to STP strategy group")
* [Delete uid to STP strategy group](#delete-uid-to-stp-strategy-group "Delete uid to STP strategy group")

![](https://www.mexc.com/akam/13/pixel_7c47f328?a=dD0wOTBhNTFkZWMxM2Y1OWM5OTE4N2QwOTliZDM3YjdiNDM4YzZkYzFjJmpzPW9mZg==)