_Source: https://www.mexc.com/api-docs/spot-v3/wallet-endpoints_

_Fetched: 2026-04-04T04:30:14.713492Z_

Wallet Endpoints | MEXC API







[Skip to main content](#__docusaurus_skipToContent_fallback)

[![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)](https://www.mexc.com/)[SpotV3](/api-docs/spot-v3/introduction)[Futures](/api-docs/futures/update-log)[Broker](/api-docs/broker/mexc-broker-introduction)

[English](#)

* [English](/api-docs/spot-v3/wallet-endpoints)
* [中文](/zh-MY/api-docs/spot-v3/wallet-endpoints)

* [Introduction](/api-docs/spot-v3/introduction)
* [Change Log](/api-docs/spot-v3/change-log)
* [FAQs](/api-docs/spot-v3/faqs)
* [General Info](/api-docs/spot-v3/general-info)
* [Market Data Endpoints](/api-docs/spot-v3/market-data-endpoints)
* [Sub-Account Endpoints(Only supports main account API key)](/api-docs/spot-v3/subaccount-endpoints)
* [Spot Account/Trade](/api-docs/spot-v3/spot-account-trade)
* [Wallet Endpoints](/api-docs/spot-v3/wallet-endpoints)
* [Websocket Market Streams](/api-docs/spot-v3/websocket-market-streams)
* [Websocket User Data Streams](/api-docs/spot-v3/websocket-user-data-streams)
* [Rebate Endpoints](/api-docs/spot-v3/rebate-endpoints)
* [Public API Definitions](/api-docs/spot-v3/public-api-definitions)

On this page

Wallet Endpoints
================

Query the currency information[​](#query-the-currency-information "Direct link to Query the currency information")
------------------------------------------------------------------------------------------------------------------

> Request

```
Get /api/v3/capital/config/getall
```

> Response

```
[  
  {  
        "coin": "BTC",  
        "name": "BTC-BSC",  
        "networkList": [  
            {  
                "coin": "BTC",  
                "depositDesc": null,  
                "depositEnable": true,  
                "minConfirm": 3,  
                "name": "Bitcoin",  
                "network": "Bitcoin(BTC)",  
                "withdrawEnable": true,  
                "withdrawFee": "0.000014",  
                "withdrawIntegerMultiple": null,  
                "withdrawMax": "50",  
                "withdrawMin": "0.00008",  
                "sameAddress": false,  
                "contract": "",  
                "withdrawTips": "",  
                "depositTips": null,  
                "netWork": "BTC"  
            },  
            {  
                "coin": "BTC",  
                "depositDesc": null,  
                "depositEnable": true,  
                "minConfirm": 61,  
                "name": "BTC-BSC",  
                "network": "BNB Smart Chain(BEP20)",  
                "withdrawEnable": true,  
                "withdrawFee": "0.00000028",  
                "withdrawIntegerMultiple": null,  
                "withdrawMax": "100",  
                "withdrawMin": "0.00003",  
                "sameAddress": false,  
                "contract": "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c",  
                "withdrawTips": null,  
                "depositTips": null,  
                "netWork": "BSC"  
            }  
        ]  
    },  
    {  
        "coin": "SUT",  
        "name": "SUPERTRUST",  
        "networkList": [  
            {  
                "coin": "SUT",  
                "depositDesc": null,  
                "depositEnable": true,  
                "minConfirm": 450,  
                "name": "SUPERTRUST",  
                "network": "Polygon(MATIC)",  
                "withdrawEnable": true,  
                "withdrawFee": "0.2",  
                "withdrawIntegerMultiple": null,  
                "withdrawMax": "100000",  
                "withdrawMin": "10",  
                "sameAddress": false,  
                "contract": "0x98965474EcBeC2F532F1f780ee37b0b05F77Ca55",  
                "withdrawTips": null,  
                "depositTips": null,  
                "netWork": "MATIC"  
            }  
        ]  
    }  
]
```

* **GET** `/api/v3/capital/config/getall`

**Permission:** SPOT\_WITHDRAW\_READ

**Weight(IP):** 10

Query currency details and the smart contract address

Parameters:

None

Response:

| Name | Description |
| --- | --- |
| depositEnable | depositEnable |
| withdrawEnable | withdrawEnable |
| withdrawFee | withdrawFee |
| withdrawMax | Max withdraw amount |
| withdrawMin | Min withdraw amount |
| contract | coin contract |
| withdrawTips | withdrawTips |
| depositTips | depositTips |
| network | withdraw network(previous params,offline soon) |
| netWork | withdraw network(new params,for new withdraw endpoint) |

Withdraw(new)[​](#withdrawnew "Direct link to Withdraw(new)")
-------------------------------------------------------------

> Request

```
post /api/v3/capital/withdraw?coin=EOS&address=zzqqqqqqqqqq&amount=10&netWork=EOS&memo=MX10086&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
{  
    "id":"7213fea8e94b4a5593d507237e5a555b"  
}
```

* **POST** `/api/v3/capital/withdraw`

**Permission:** SPOT\_WITHDRAW\_WRITE

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| coin | string | YES | coin |
| withdrawOrderId | string | NO | withdrawOrderId |
| netWork | string | NO | withdraw network |
| contractAddress | string | NO | coin contract address |
| address | string | YES | withdraw address |
| memo | string | NO | memo(If memo is required in the address, it must be passed in) |
| amount | string | YES | withdraw amount |
| remark | string | NO | remark |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

Can get `netWork` via endpoints `Get /api/v3/capital/config/getall`'s response params `networkList`.

Response:

| Name | Description |
| --- | --- |
| id | withdraw ID |

Cancel withdraw[​](#cancel-withdraw "Direct link to Cancel withdraw")
---------------------------------------------------------------------

> Request

```
delete /api/v3/capital/withdraw?id=ca7bd51895134fb5bd749f1cf875b8af&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
{  
    "id": "ca7bd51895134fb5bd749f1cf875b8af"  
}
```

* **DELETE** `/api/v3/capital/withdraw`

**Permission:** SPOT\_WITHDRAW\_W

**Weight(IP):** 1

**Request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| id | string | Yes | withdraw id |

**Response**

| Name | Description |
| --- | --- |
| id | withdraw id |

Deposit History(supporting network)[​](#deposit-historysupporting-network "Direct link to Deposit History(supporting network)")
-------------------------------------------------------------------------------------------------------------------------------

> Request

```
get /api/v3/capital/deposit/hisrec?coin=EOS&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
[  
  {  
        "amount": "50000",  
        "coin": "EOS",  
        "network": "EOS",  
        "status": 5,  
        "address": "0x20b7cf77db93d6ef1ab979c49142ec168427fdee",  
        "txId": "01391d1c1397ef0a3cbb3c7f99a90846f7c8c2a8dddcdcf84f46b530dede203e1bc804",  
        "insertTime": 1659513342000,  
        "unlockConfirm": "10",  
        "confirmTimes": "241",  
        "memo": "xxyy1122"  
  }  
]
```

* **GET** `/api/v3/capital/deposit/hisrec`

**Permission:** SPOT\_WITHDRAW\_READ

**Weight(IP):** 10

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| coin | string | NO | coin |
| status | string | NO | [deposit status](/api-docs/spot-v3/public-api-definitions#deposit_status) |
| startTime | string | NO | default: 7 days ago from current time |
| endTime | string | NO | default:current time |
| limit | string | NO | default:1000,max:1000 |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

1. default return the records of the last 7 days.
2. Ensure that the default timestamp of 'startTime' and 'endTime' does not exceed 7 days.
3. can query 90 days data at most.

Response:

| Name | Description |
| --- | --- |
| amount | deposit amount |
| coin | coin |
| network | deposit network |
| status | [deposit status](/api-docs/spot-v3/public-api-definitions#deposit_status) |
| address | deposit adress |
| addressTag | addressTag |
| txId | txId |
| insertTime | insertTime |
| unlockConfirm | unlockConfirm |
| confirmTimes | confirmTimes |
| memo | memo |

Withdraw History (supporting network)[​](#withdraw-history-supporting-network "Direct link to Withdraw History (supporting network)")
-------------------------------------------------------------------------------------------------------------------------------------

> Request

```
get /api/v3/capital/withdraw/history?coin=USDT&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
[  
  {  
        "id": "bb17a2d452684f00a523c015d512a341",  
        "txId": null,  
        "coin": "EOS",  
        "network": "EOS",  
        "address": "zzqqqqqqqqqq",  
        "amount": "10",  
        "transferType": 0,  
        "status": 3,  
        "transactionFee": "0",  
        "confirmNo": null,  
        "applyTime": 1665300874000,  
        "remark": "",  
        "memo": "MX10086",  
        "transHash": "0x0ced593b8b5adc9f600334d0d7335456a7ed772ea5547beda7ffc4f33a065c",  
        "updateTime": 1712134082000,  
        "coinId": "128f589271cb495b03e71e6323eb7be",  
        "vcoinId": "af42c6414b9a46c8869ce30fd51660f"  
  }  
]
```

* **GET** `/api/v3/capital/withdraw/history`

**Permission:** SPOT\_WITHDRAW\_READ

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| coin | string | NO | coin |
| status | string | NO | [withdraw status](/api-docs/spot-v3/public-api-definitions#withdraw_status) |
| limit | string | NO | default:1000, max:1000 |
| startTime | string | NO | default: 7 days ago from current time |
| endTime | string | NO | default:current time |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

1. default return the records of the last 7 days.
2. Ensure that the default timestamp of 'startTime' and 'endTime' does not exceed 7 days.
3. can query 90 days data at most.
4. Supported multiple network coins's withdraw history may not return the 'network' field.

Response:

| Name | Description |
| --- | --- |
| address | withdraw address |
| amount | withdraw amount |
| applyTime | apply time |
| coin | coin |
| id | withdraw id |
| withdrawOrderId | withdrawOrderId |
| network | withdraw network |
| transferType | transferType, 0: outside transfer,1: inside transfer |
| status | [withdraw status](/api-docs/spot-v3/public-api-definitions#withdraw_status) |
| transactionFee | transactionFee |
| confirmNo | confirmNo |
| txId | txId |
| remark | remark |
| memo | memo |
| transHash | transaction Hash |
| coinId | asset id |
| vcoinId | currency id |

Generate deposit address (supporting network)[​](#generate-deposit-address-supporting-network "Direct link to Generate deposit address (supporting network)")
-------------------------------------------------------------------------------------------------------------------------------------------------------------

> Request

```
post /api/v3/capital/deposit/address?coin=EOS&network=EOS&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
[  
  {  
      "coin": "USDT",  
      "network": "TRC20",  
      "address": "TXobiKkdciupZrhdvZyTSSLjE8CmZAufS",  
      "tag": null  
  },  
  {  
     "coin": "EOS",  
     "network": "EOS",  
     "address": "zzqqqqqqqqqq",  
     "memo": "MX10068"  
  }  
]
```

* **POST** `/api/v3/capital/deposit/address`

**Permission:** SPOT\_WITHDRAW\_WRITE

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| coin | string | YES | coin |
| network | string | YES | deposit network |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

Response:

| Name | Description |
| --- | --- |
| address | deposit address |
| coin | coin |
| memo | memo |
| network | network |

Deposit Address (supporting network)[​](#deposit-address-supporting-network "Direct link to Deposit Address (supporting network)")
----------------------------------------------------------------------------------------------------------------------------------

> Request

```
get /api/v3/capital/deposit/address?coin=USDT&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
[  
  {  
      "coin": "USDT",  
      "network": "TRC20",  
      "address": "TXobiKkdciupZrhdvZyTSSLjE8CmZAufS",  
      "memo": null  
  },  
  {  
      "coin": "USDT",  
      "network": "BEP20(BSC)",  
      "address": "0xebe4804f7ecc22d5011c42e6ea1f2e6c891d89b",  
      "memo": null  
  },  
  {  
      "coin": "USDT",  
      "network": "ERC20",  
      "address": "0x3f4d1f43761b52fd594e5a77cd83cab6955e85b",  
      "memo": null  
  }  
]
```

* **GET** `/api/v3/capital/deposit/address`

**Permission:** SPOT\_WITHDRAW\_READ

**Weight(IP):** 10

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| coin | string | YES | coin |
| network | string | NO | deposit network |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

Response:

| Name | Description |
| --- | --- |
| address | deposit address |
| coin | coin |
| memo | memo |
| network | network |

Withdraw Address (supporting network)[​](#withdraw-address-supporting-network "Direct link to Withdraw Address (supporting network)")
-------------------------------------------------------------------------------------------------------------------------------------

> Request

```
get /api/v3/capital/withdraw/address?coin=USDT&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
{  
    "data": [  
        {  
            "coin": "USDT",  
            "network": "TRC20",  
            "address": "TArGWdTApuuZtiWMjupXqbZqQYsBTy126o",  
            "addressTag": "test",  
            "memo": null  
        },  
        {  
            "coin": "USDT",  
            "network": "BEP20(BSC)",  
            "address": "0xa82898C70BeB5E1b1621fdA62fD17Ba27227BBC5",  
            "addressTag": "usdt",  
            "memo": null  
        }  
    ],  
    "totalRecords": 2,  
    "page": 1,  
    "totalPageNum": 1  
}
```

* **GET** `/api/v3/capital/withdraw/address`

**Permission:** SPOT\_WITHDRAW\_R

**Weight(IP):** 10

**Request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| coin | string | No | coin |
| page | number | No | page,default 1 |
| limit | number | No | limit for per page |
| timestamp | string | Yes | timestamp |
| signature | string | Yes | signature |

**Response**

| Name | Description |
| --- | --- |
| coin | coin |
| network | network |
| address | address |
| addressTag | addressTag |
| memo | memo |
| totalRecords | totalRecords |
| totalPageNum | totalPageNum |
| page | page |

User Universal Transfer[​](#user-universal-transfer "Direct link to User Universal Transfer")
---------------------------------------------------------------------------------------------

> Request

```
post /api/v3/capital/transfer?fromAccountType=FUTURES&toAccountType=SPOT&asset=USDT&amount=1&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
[  
  {  
    "tranId": "c45d800a47ba4cbc876a5cd29388319"  
  }  
]
```

* **POST** `/api/v3/capital/transfer`

**Permission:** SPOT\_TRANSFER\_WRITE

**Weight(IP):** 50

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| fromAccountType | string | YES | fromAccountType:"SPOT","FUTURES" |
| toAccountType | string | YES | toAccountType:"SPOT","FUTURES" |
| asset | string | YES | asset |
| amount | string | YES | amount |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

Response:

| Name | Description |
| --- | --- |
| tranId | tranId |

Query User Universal Transfer History[​](#query-user-universal-transfer-history "Direct link to Query User Universal Transfer History")
---------------------------------------------------------------------------------------------------------------------------------------

> Request

```
get /api/v3/capital/transfer
```

> Response

```
[  
  {  
    "rows":[  
    {  
      "tranId":"11945860693",  
      "clientTranId":"test",  
      "asset":"BTC",  
      "amount":"0.1",  
      "fromAccountType":"SPOT",  
      "toAccountType":"FUTURE",  
      "fromSymbol":"SPOT",  
      "toSymbol":"FUTURE",  
      "status":"SUCCESS",  
      "timestamp":1544433325000  
    },  
    {  
      "tranId":"11945860693",  
      "clientTranId":"test",  
      "asset":"BTC",  
      "amount":"0.1",  
      "fromAccountType":"SPOT",  
      "toAccountType":"FUTURE",  
      "fromSymbol":"SPOT",  
      "toSymbol":"FUTURE",  
      "status":"SUCCESS",  
      "timestamp":1544433325000  
    }],  
    "total": 2,  
  }  
]
```

* **GET** `/api/v3/capital/transfer`

**Permission:** SPOT\_TRANSFER\_READ

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| fromAccountType | string | YES | fromAccountType:"SPOT","FUTURES" |
| toAccountType | string | YES | toAccountType:"SPOT","FUTURES" |
| startTime | string | NO | startTime |
| endTime | string | NO | endTime |
| page | string | NO | default:1 |
| size | string | NO | default:10, max:100 |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

1. Only can quary the data for the last six months
2. If 'startTime' and 'endTime' are not send, will return the last seven days' data by default

Response:

| Name | Description |
| --- | --- |
| total | total |
| tranId | tranId |
| clientTranId | client ID |
| asset | coin |
| amount | amount |
| fromAccountType | fromAccountType |
| toAccountType | toAccountType |
| symbol | symbol |
| status | status |
| timestamp | timestamp |

Query User Universal Transfer History （by tranId）[​](#query-user-universal-transfer-history-by-tranid "Direct link to Query User Universal Transfer History （by tranId）")
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

> Request

```
get /api/v3/capital/transfer/tranId?tranId=cb28c88cd20c42819e4d5148d5fb5742&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
{  
    "tranId": "cb28c88cd20c42819e4d5148d5fb5742",  
    "clientTranId": null,  
    "asset": "USDT",  
    "amount": "10",  
    "fromAccountType": "SPOT",  
    "toAccountType": "FUTURES",  
    "symbol": null,  
    "status": "SUCCESS",  
    "timestamp": 1678603205000  
}
```

* **GET** `/api/v3/capital/transfer/tranId`

**Permission:** SPOT\_TRANSFER\_R

**Weight(IP):** 1

**request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| tranId | string | YES | tranId |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

Only can quary the data for the last six months

**response**

| Name | Description |
| --- | --- |
| tranId | tranId |
| clientTranId | client ID |
| asset | coin |
| amount | amount |
| fromAccountType | fromAccountType |
| toAccountType | toAccountType |
| symbol | symbol |
| status | status |
| timestamp | timestamp |

Get Assets That Can Be Converted Into MX[​](#get-assets-that-can-be-converted-into-mx "Direct link to Get Assets That Can Be Converted Into MX")
------------------------------------------------------------------------------------------------------------------------------------------------

> Request

```
get {{api_url}}/api/v3/capital/convert/list?timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
[  
    {  
           "convertMx": "0.000009",  
           "convertUsdt": "0.000009",  
           "balance": "0.000441",  
           "asset": "USDT",  
           "code": "30021",  
           "message": "xxxxxxx"  
 },  
{  
           "convertMx": "0.000009",  
           "convertUsdt": "0.000009",  
           "balance": "0.000441",  
           "asset": "BTC",  
           "code": "30021",  
           "message": "xxxxxxx"  
 }  
]
```

* **GET** `/api/v3/capital/convert/list`

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

Response:

| Name | Description |
| --- | --- |
| convertMx | MX amount（Deducted commission fee） |
| convertUsdt | usdt amount |
| balance | Convertible balance |
| asset | asset |
| code | code |
| message | message |

Dust Transfer[​](#dust-transfer "Direct link to Dust Transfer")
---------------------------------------------------------------

> Request

```
post {{api_url}}/api/v3/capital/convert?asset=BTC,FIL,ETH&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
{  
  "successList":["ALGO","OMG"],  
  "failedList":[],  
  "totalConvert":"0.07085578",  
  "convertFee":"0.00071571"  
  }
```

* **POST** `/api/v3/capital/convert`

**Permission:** SPOT\_ACCOUNT\_W

**Weight(IP):** 10

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| asset | string | YES | The asset being converted.(max 15 assert)eg:asset=BTC,FIL,ETH |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

Response:

| Name | Description |
| --- | --- |
| totalConvert | Convert MX amount(Deducted commission fee) |
| convertFee | convertFee |
| successList | convert success List |
| failedList | convert failed List |
| -asset | asset |
| -message | message |
| -code | code |

DustLog[​](#dustlog "Direct link to DustLog")
---------------------------------------------

> Request

```
get {{api_url}}/api/v3/capital/convert?timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
{  
    "data": [  
        {  
            "totalConvert": "0.00885018",  
            "totalFee": "0.000177",  
            "convertTime": 1665360563000,  
            "convertDetails": [  
                {  
                    "id": "3e52a99c5c3447b2af2163cd829dca28",  
                    "convert": "0.00885018",  
                    "fee": "0.000177",  
                    "amount": "0.007130464601986065",  
                    "time": 1665360563000,  
                    "asset": "ETHF"  
                }  
            ]  
        },  
        {  
            "totalConvert": "0.026782",  
            "totalFee": "0.00053562",  
            "convertTime": 1663631477000,  
            "convertDetails": [  
                {  
                    "id": "6483bfb1766d41d8a4b6b6315ded6e99",  
                    "convert": "0.02098255",  
                    "fee": "0.00041965",  
                    "amount": "0.00000098",  
                    "time": 1663631477000,  
                    "asset": "BTC"  
                },  
                {  
                    "id": "f9e886f28c454f5dae45eec6a11f6c6a",  
                    "convert": "0.00084019",  
                    "fee": "0.0000168",  
                    "amount": "2",  
                    "time": 1663631477000,  
                    "asset": "JAM"  
                }  
            ]  
        }  
    ],    
    "totalRecords": 4,  
    "page": 1,  
    "totalPageNum": 1  
}
```

* **GET** `/api/v3/capital/convert`

**Permission:** SPOT\_DEAL\_READ

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| startTime | long | NO | startTime |
| endTime | long | NO | endTime |
| page | int | NO | page,default 1 |
| limit | int | NO | limit,default 1; max 1000 |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

Response:

| Name | Type | Description |
| --- | --- | --- |
| totalConvert | string | Convert MX amount(Deducted commission fee) |
| totalFee | string | Total fee amount |
| convertTime | long | Convert time |
| convertDetails | object | Convert details |
| id | string | Convert id |
| convert | string | Convert mx |
| fee | string | fee amount |
| amount | string | amount |
| time | long | Convert time |
| asset | string | asset |
| page | int | page |
| totalRecords | int | totalRecords |
| totalPage | int | totalPage |

Internal Transfer[​](#internal-transfer "Direct link to Internal Transfer")
---------------------------------------------------------------------------

> Request

```
post /api/v3/capital/transfer/internal?&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
  {  
    "tranId": "c45d800a47ba4cbc876a5cd29388319"  
  }
```

* **POST** `/api/v3/capital/transfer/internal`

**Permission:** SPOT\_WITHDRAW\_WRITE

**Weight(IP):** 1

**Parameters**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| toAccountType | string | Yes | toAccountTyp:EMAIL/UID/MOBILE |
| toAccount | string | Yes | toAccount:EMAIL/UID/MOBILE |
| areaCode | string | No | areaCode of mobile |
| asset | string | Yes | asset |
| amount | string | Yes | amount |
| timestamp | string | Yes | timestamp |
| signature | string | Yes | signature |

**Response**

| Name | Description |
| --- | --- |
| tranId | tranId |

Query Internal Transfer history[​](#query-internal-transfer-history "Direct link to Query Internal Transfer history")
---------------------------------------------------------------------------------------------------------------------

> Request

```
get /api/v3/capital/transfer/internal?&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
  {  
    "page": 1,    
    "totalRecords": 1,    
    "totalPageNum": 1,    
    "data": [  
             {  
      "tranId":"11945860693",  
      "asset":"BTC",  
      "amount":"0.1",  
      "toAccountType":"EMAIL",  
      "toAccount":"156283619@outlook.com",  
      "fromAccount":"156283618@outlook.com",  
      "status":"SUCCESS",  
      "timestamp":1544433325000  
    },  
    {  
      "tranId":"",  
      "asset":"BTC",  
      "amount":"0.8",  
      "toAccountType":"UID",  
      "fromAccount":"156283619@outlook.com",  
      "toAccount":"87658765",  
      "status":"SUCCESS",  
      "timestamp":1544433325000  
    }  
    ]  
}
```

* **GET**  `/api/v3/capital/transfer/internal`

**Permission:** SPOT\_WITHDRAW\_READ

**Weight(IP):** 1

**Parameters**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| startTime | long | No |  |
| endTime | long | No |  |
| page | int | No | default 1 |
| limit | int | No | default 10 |
| tranId | string | No | tranid |
| timestamp | string | Yes | timestamp |
| signature | string | Yes | signature |

If startTime and endTime are not provided, will default to returning data from the last 7 days.

**Response**

| Name | Description |
| --- | --- |
| page | page |
| totalRecords | totalRecords |
| totalPage | totalPage |
| tranId | tranId |
| asset | asset |
| amount | amount |
| fromAccountType | fromAccountType |
| toAccountType | toAccountType |
| status | status:"SUCCESS","FAILED","WAIT" |
| timestamp | timestamp |

Withdraw(previous,offline soon)[​](#withdrawpreviousoffline-soon "Direct link to Withdraw(previous,offline soon)")
------------------------------------------------------------------------------------------------------------------

> Request

```
post /api/v3/capital/withdraw/apply?coin=EOS&address=zzqqqqqqqqqq&amount=10&network=EOS&memo=MX10086&timestamp={{timestamp}}&signature={{signature}}
```

> Response

```
[  
  {  
    "id":"7213fea8e94b4a5593d507237e5a555b"  
  }  
]
```

* **POST** `/api/v3/capital/withdraw/apply`

**Permission:** SPOT\_WITHDRAW\_WRITE

**Weight(IP):** 10

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| coin | string | YES | coin |
| withdrawOrderId | string | NO | withdrawOrderId |
| network | string | NO | withdraw network |
| address | string | YES | withdraw address |
| memo | string | NO | memo(If memo is required in the address, it must be passed in) |
| amount | string | YES | withdraw amount |
| remark | string | NO | remark |
| timestamp | string | YES | timestamp |
| signature | string | YES | signature |

Can get `network` via endpoints `Get /api/v3/capital/config/getall`'s response params `networkList`.

Response:

| Name | Description |
| --- | --- |
| id | withdraw ID |

[Previous

Spot Account/Trade](/api-docs/spot-v3/spot-account-trade)[Next

Websocket Market Streams](/api-docs/spot-v3/websocket-market-streams)

* [Query the currency information](#query-the-currency-information)
* [Withdraw(new)](#withdrawnew)
* [Cancel withdraw](#cancel-withdraw)
* [Deposit History(supporting network)](#deposit-historysupporting-network)
* [Withdraw History (supporting network)](#withdraw-history-supporting-network)
* [Generate deposit address (supporting network)](#generate-deposit-address-supporting-network)
* [Deposit Address (supporting network)](#deposit-address-supporting-network)
* [Withdraw Address (supporting network)](#withdraw-address-supporting-network)
* [User Universal Transfer](#user-universal-transfer)
* [Query User Universal Transfer History](#query-user-universal-transfer-history)
* [Query User Universal Transfer History （by tranId）](#query-user-universal-transfer-history-by-tranid)
* [Get Assets That Can Be Converted Into MX](#get-assets-that-can-be-converted-into-mx)
* [Dust Transfer](#dust-transfer)
* [DustLog](#dustlog)
* [Internal Transfer](#internal-transfer)
* [Query Internal Transfer history](#query-internal-transfer-history)
* [Withdraw(previous,offline soon)](#withdrawpreviousoffline-soon)