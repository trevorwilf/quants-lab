_Source: webscrape/mexc/mexc_spot_public_api_definitions.html (browser-rendered)_

_Loaded: 2026-04-04T04:30:30.994292Z_

Public API Definitions | MEXC API

[Skip to main content](#__docusaurus_skipToContent_fallback "Skip to main content")

[![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)](https://www.mexc.com/ "https://www.mexc.com/")[SpotV3](/api-docs/spot-v3/introduction "SpotV3")[Futures](/api-docs/futures/update-log "Futures")[Broker](/api-docs/broker/mexc-broker-introduction "Broker")

[English](# "English")

* [English](/api-docs/spot-v3/public-api-definitions "English")
* [中文](/zh-MY/api-docs/spot-v3/public-api-definitions "中文")

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

Public API Definitions
======================

ENUM definitions[​](#enum-definitions "Direct link to ENUM definitions")
------------------------------------------------------------------------

### Order side[​](#order-side "Direct link to order-side")

* BUY
* SELL

### Order type[​](#order-type "Direct link to order-type")

* LIMIT
* MARKET
* LIMIT\_MAKER
* IMMEDIATE\_OR\_CANCEL
* FILL\_OR\_KILL
* STOP\_MARKET\_ORDER (Query only)

### Order Status[​](#order-status "Direct link to order-status")

* NEW Uncompleted
* FILLED Filled
* PARTIALLY\_FILLED Partially filled
* CANCELED Canceled
* PARTIALLY\_CANCELED Partially canceled

### Deposit Status[​](#deposit-status "Direct link to deposit-status")

* 1 SMALL
* 2 TIME\_DELAY
* 3 LARGE\_DELAY
* 4 PENDING
* 5 SUCCESS
* 6 AUDITING
* 7 REJECTED
* 8 REFUND
* 9 PRE\_SUCCESS
* 10 INVALID
* 11 RESTRICTED
* 12 COMPLETED

### Withdraw Status[​](#withdraw-status "Direct link to withdraw-status")

* 1 APPLY
* 2 AUDITING
* 3 WAIT
* 4 PROCESSING
* 5 WAIT\_PACKAGING
* 6 WAIT\_CONFIRM
* 7 SUCCESS
* 8 FAILED
* 9 CANCEL
* 10 MANUAL

### Kline Interval[​](#kline-interval "Direct link to kline-interval")

* 1m 1 minute
* 5m 5 minute
* 15m 15 minute
* 30m 30 minute
* 60m 60 minute
* 4h 4 hour
* 1d 1 day
* 1W 1 week
* 1M 1 month

### changed type[​](#changed-type "Direct link to changed-type")

* WITHDRAW withdraw
* WITHDRAW\_FEE withdraw fee
* DEPOSIT deposit
* DEPOSIT\_FEE deposit fee
* ENTRUST deal
* ENTRUST\_PLACE place order
* ENTRUST\_CANCEL cancel order
* TRADE\_FEE trade fee
* ENTRUST\_UNFROZEN return frozen order funds
* SUGAR airdrop
* ETF\_INDEX ETF place order

[Previous

Rebate Endpoints](/api-docs/spot-v3/rebate-endpoints "PreviousRebate Endpoints")

* [ENUM definitions](#enum-definitions "ENUM definitions")
  + Order side
  + Order type
  + Order Status
  + Deposit Status
  + Withdraw Status
  + Kline Interval
  + changed type

![](https://www.mexc.com/akam/13/pixel_7c47f328?a=dD0wOTBhNTFkZWMxM2Y1OWM5OTE4N2QwOTliZDM3YjdiNDM4YzZkYzFjJmpzPW9mZg==)