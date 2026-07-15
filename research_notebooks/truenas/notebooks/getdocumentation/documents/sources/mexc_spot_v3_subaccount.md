_Source: https://www.mexc.com/api-docs/spot-v3/subaccount-endpoints_

_Fetched: 2026-04-04T04:30:13.119655Z_

Sub-Account Endpoints(Only supports main account API key) | MEXC API







[Skip to main content](#__docusaurus_skipToContent_fallback)

[![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)](https://www.mexc.com/)[SpotV3](/api-docs/spot-v3/introduction)[Futures](/api-docs/futures/update-log)[Broker](/api-docs/broker/mexc-broker-introduction)

[English](#)

* [English](/api-docs/spot-v3/subaccount-endpoints)
* [中文](/zh-MY/api-docs/spot-v3/subaccount-endpoints)

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

Sub-Account Endpoints(Only supports main account API key)
=========================================================

Create a Sub-account(For Master Account)[​](#create-a-sub-accountfor-master-account "Direct link to Create a Sub-account(For Master Account)")
----------------------------------------------------------------------------------------------------------------------------------------------

Create a sub-account from the master account.

> Response

```
{  
    "subAccount":"mexc1",  
    "note":"1"  
}
```

* POST / api/v3/sub-account/virtualSubAccount

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| subAccount | STRING | YES | Sub-account Name |
| note | STRING | YES | Sub-account notes |
| recvWindow | LONG | NO |  |
| timestamp | LONG | YES |  |

Query Sub-account List (For Master Account)[​](#query-sub-account-list-for-master-account "Direct link to Query Sub-account List (For Master Account)")
-------------------------------------------------------------------------------------------------------------------------------------------------------

Get details of the sub-account list

> Response

```
{  
    "subAccounts":[  
        {  
            "subAccount":"mexc666",  
            "isFreeze":false,  
            "createTime":1544433328000,  
            "uid": "49910511"  
        },  
        {  
            "subAccount":"mexc888",  
            "isFreeze":false,  
            "createTime":1544433328000,  
            "uid": "91921059"  
        }  
    ]  
}
```

* GET / api/v3/sub-account/list

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| subAccount | STRING | NO | Sub-account Name |
| isFreeze | STRING | NO | true or false |
| page | INT | NO | Default value: 1 |
| limit | INT | NO | Default value: 10, Max value: 200 |
| timestamp | LONG | YES |  |
| recvWindow | LONG | NO |  |

Response:

| Name | Description |
| --- | --- |
| subAccount | subAccount name |
| isFreeze | isFreeze |
| createTime | createTime |
| uid | subaccount uid |

Create an APIKey for a sub-account (For Master Account)[​](#create-an-apikey-for-a-sub-account-for-master-account "Direct link to Create an APIKey for a sub-account (For Master Account)")
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

> Response

```
    {  
        "subAccount": "mexc1",  
        "note": "1",  
        "apiKey": "arg13sdfgs",  
        "secretKey": "nkjwn21973ihi",  
        "permissions": "SPOT_ACCOUNT_READ",  
        "ip": "135.181.193",  
        "creatTime": 1597026383085  
    }
```

* POST /api/v3/sub-account/apiKey

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| subAccount | STRING | YES | Sub-account Name |
| note | STRING | YES | APIKey note |
| permissions | STRING | YES | Permission of APIKey: SPOT\_ACCOUNT\_READ, SPOT\_ACCOUNT\_WRITE, SPOT\_DEAL\_READ, SPOT\_DEAL\_WRITE, CONTRACT\_ACCOUNT\_READ, CONTRACT\_ACCOUNT\_WRITE, CONTRACT\_DEAL\_READ, CONTRACT\_DEAL\_WRITE, SPOT\_TRANSFER\_READ, SPOT\_TRANSFER\_WRITE |
| ip | STRING | NO | Link IP addresses, separate with commas if more than one. Support up to 20 addresses. |
| recvWindow | LONG | NO |  |
| timestamp | LONG | YES |  |

Query the APIKey of a sub-account (For Master Account)[​](#query-the-apikey-of-a-sub-account-for-master-account "Direct link to Query the APIKey of a sub-account (For Master Account)")
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Applies to master accounts only

> Response

```
   {  
       "subAccount":[  
        {  
            "note":"v5",  
            "apiKey":"arg13sdfgs",  
            "permissions":"SPOT_ACCOUNT_READ,SPOT_ACCOUNT_WRITE",  
            "ip":"1.1.1.1,2.2.2.2",  
            "creatTime":1597026383085  
        },  
        {  
            "note":"v5.1",  
            "apiKey":"arg13sdfgs12",  
            "permissions":"SPOT_ACCOUNT_READ,SPOT_ACCOUNT_WRITE",  
            "ip":"1.1.1.1,2.2.2.2",  
            "creatTime":1597026383085  
        }  
        ]  
   }
```

* GET/api/v3/sub-account/apiKey

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| subAccount | STRING | YES | Sub-account Name |
| recvWindow | LONG | NO |  |
| timestamp | LONG | YES |  |

Delete the APIKey of a sub-account (For Master Account)[​](#delete-the-apikey-of-a-sub-account-for-master-account "Direct link to Delete the APIKey of a sub-account (For Master Account)")
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

> Response

```
  {  
           "subAccount":"mexc1"  
}
```

* DELETE /api/v3/sub-account/apiKey

**Permission:** SPOT\_ACCOUNT\_READ

**Weight(IP):** 1

Parameters:

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| subAccount | STRING | YES | Sub-account Name |
| apiKey | STRING | YES | API public key |
| recvWindow | LONG | NO |  |
| timestamp | LONG | YES |  |

Universal Transfer (For Master Account)[​](#universal-transfer-for-master-account "Direct link to Universal Transfer (For Master Account)")
-------------------------------------------------------------------------------------------------------------------------------------------

> Request

```
post /api/v3/capital/sub-account/universalTransfer
```

> Response

```
 {  
    "tranId":11945860693   
 }
```

* **POST** `/api/v3/capital/sub-account/universalTransfer`

**Permission:** SPOT\_TRANSFER\_WRITE

**Weight(IP):** 50

**Parameters:**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| clientTranId | string | NO | 32-character alphanumeric string |
| fromAccount | string | NO | Transfer from master account by default if fromAccount is not sent |
| toAccount | string | NO | Transfer to master account by default if toAccount is not sent |
| fromAccountType | string | YES | fromAccountType:"SPOT","FUTURES" |
| toAccountType | string | YES | toAccountType:"SPOT","FUTURES" |
| asset | string | YES | asset,eg:USDT |
| amount | string | YES | amount,eg:1.82938475 |
| timestamp | string | YES | timestamp |
| signature | string | YES | sign |

**Response:**

| Name | Type | Description |
| --- | --- | --- |
| tranId | string | transfer ID |

Query Universal Transfer History (For Master Account)[​](#query-universal-transfer-history-for-master-account "Direct link to Query Universal Transfer History (For Master Account)")
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

> Request

```
get /api/v3/capital/sub-account/universalTransfer
```

> Response

```
  {  
    "tranId":"11945860693",  
    "fromAccount":"master@test.com",  
    "toAccount":"subaccount1@test.com",  
    "clientTranId":"test",  
    "asset":"BTC",  
    "amount":"0.1",  
    "fromAccountType":"SPOT",  
    "toAccountType":"FUTURE",  
    "fromSymbol":"SPOT",  
    "toSymbol":"FUTURE",  
    "status":"SUCCESS",  
    "timestamp":1544433325000  
  }
```

* **GET** `/api/v3/capital/sub-account/universalTransfer`

**Permission:** SPOT\_TRANSFER\_READ

**Weight(IP):** 1

**Parameters:**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| clientTranId | string | NO | 32-character alphanumeric string |
| fromAccount | string | NO | Transfer from master account by default if fromAccount is not sent |
| toAccount | string | NO | Transfer to master account by default if toAccount is not sent |
| fromAccountType | string | YES | fromAccountType:"SPOT","FUTURES" |
| toAccountType | string | YES | toAccountType:"SPOT","FUTURES" |
| startTime | string | NO | startTime |
| endTime | string | NO | endTime |
| page | string | NO | default 1 |
| limit | string | NO | default 500, max 500 |
| timestamp | string | YES | timestamp |
| signature | string | YES | sign |

**Response:**

| Name | Type | Description |
| --- | --- | --- |
| tranId | string | transfer ID |
| fromAccount | string | fromAccount |
| toAccount | string | toAccount |
| clientTranId | string | clientTranId |
| asset | string | asset |
| amount | string | transfer amount |
| fromAccountType | string | fromAccountType |
| toAccountType | string | toAccountType |
| fromSymbol | string | fromSymbol |
| toSymbol | string | toSymbol |
| status | string | status |
| timestamp | number | timestamp |

Query Sub-account Asset[​](#query-sub-account-asset "Direct link to Query Sub-account Asset")
---------------------------------------------------------------------------------------------

> request

```
get /api/v3/sub-account/asset?subAccount=account1&accountType=SPOT&timestamp={{timestamp}}&signature={{signature}}
```

> response

```
{  
    "balances": [  
        {  
            "asset": "MX",  
            "free": "3",  
            "locked": "0"  
        },  
        {  
            "asset": "BTC",  
            "free": "0.0003",  
            "locked": "0"  
        }  
    ]  
}
```

* **GET** `/api/v3/sub-account/asset`

**Permission:** SPOT\_TRANSFER\_READ

**Weight(IP):** 1

**request**

| Name | Type | Mandatory | Description |
| --- | --- | --- | --- |
| subAccount | string | Yes | subAccount name,only support query for single subaccount |
| accountType | string | Yes | account type:"SPOT","FUTURES",only support SPOT currently |
| timestamp | string | Yes | timestamp |
| signature | string | Yes | signature |

**response**

| Name | Type | Description |
| --- | --- | --- |
| balances | string | balance |
| asset | string | asset |
| free | string | free |
| locked | string | locked |

[Previous

Market Data Endpoints](/api-docs/spot-v3/market-data-endpoints)[Next

Spot Account/Trade](/api-docs/spot-v3/spot-account-trade)

* [Create a Sub-account(For Master Account)](#create-a-sub-accountfor-master-account)
* [Query Sub-account List (For Master Account)](#query-sub-account-list-for-master-account)
* [Create an APIKey for a sub-account (For Master Account)](#create-an-apikey-for-a-sub-account-for-master-account)
* [Query the APIKey of a sub-account (For Master Account)](#query-the-apikey-of-a-sub-account-for-master-account)
* [Delete the APIKey of a sub-account (For Master Account)](#delete-the-apikey-of-a-sub-account-for-master-account)
* [Universal Transfer (For Master Account)](#universal-transfer-for-master-account)
* [Query Universal Transfer History (For Master Account)](#query-universal-transfer-history-for-master-account)
* [Query Sub-account Asset](#query-sub-account-asset)