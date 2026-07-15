_Source: https://www.mexc.com/api-docs/spot-v3/introduction_

_Fetched: 2026-04-04T04:30:10.391866Z_

Introduction | MEXC API







[Skip to main content](#__docusaurus_skipToContent_fallback)

[![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)![MEXC Logo](/api-docs-assets/img/mexc-logo.svg)](https://www.mexc.com/)[SpotV3](/api-docs/spot-v3/introduction)[Futures](/api-docs/futures/update-log)[Broker](/api-docs/broker/mexc-broker-introduction)

[English](#)

* [English](/api-docs/spot-v3/introduction)
* [中文](/zh-MY/api-docs/spot-v3/introduction)

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

Introduction
============

API Key Setup[​](#api-key-setup "Direct link to API Key Setup")
---------------------------------------------------------------

* Some endpoints will require an API Key. Please refer to [this page](https://www.mexc.com/user/openapi "this page") regarding API key creation.
* Once API key is created, it is recommended to set IP restrictions on the key for security reasons.
* Trading pair settings: You can set the trading pairs that can be traded while using the API key in [My API Key—Trading Pairs—Set].
* Renewal: 5 days prior to the expiry of your API key, you can extend its validity by 90 days in [My API Key—Action—Renew].
* Never share your API key/secret key to ANYONE.

danger

If the API keys were accidentally shared, please delete them immediately and create a new key.

API Key Restrictions[​](#api-key-restrictions "Direct link to API Key Restrictions")
------------------------------------------------------------------------------------

Check the required permissions when creating an API Key

API Library[​](#api-library "Direct link to API Library")
---------------------------------------------------------

We provide developers with SDKs in five languages: Python, DotNET, Java, Javascript, and Go, and provide users with methods to call APIs directly through the SDK. Currently supports all interfaces in spot.

[<https://github.com/mexcdevelop/mexc-api-sdk>](https://github.com/mexcdevelop/mexc-api-sdk "https://github.com/mexcdevelop/mexc-api-sdk")

info

Any problem please submit [feedback](https://github.com/mexcdevelop/mexc-api-sdk/issues "feedback")

MEXC Broker Introduction[​](#mexc-broker-introduction "Direct link to MEXC Broker Introduction")
------------------------------------------------------------------------------------------------

MEXC is committed to building crypto infrastructure, with API broker partners that provide valuable services being an essential part of the MEXC ecosystem. To reward the partners, MEXC now provides privileges for MEXC brokers, including trading rebates and marketing support.

### Broker Modes Supported by MEXC[​](#broker-modes-supported-by-mexc "Direct link to Broker Modes Supported by MEXC")

**1. API Broker**

This includes copy trade platforms, trading bots, quantitative strategy platforms, or other asset management platforms with more than 500 people, etc. Users can authorize the API key to the API broker, and the API broker will send the trading orders containing the broker ID on behalf of the user and receive profit shares from fees.

**2. Independent Broker**

This includes wallet platforms, market data platforms, aggregation trading platforms, stockbrokers, as well as stock and securities trading platforms, etc., all of which have their own independent users. MEXC can provide order matching systems, account management systems, settlement systems, as well as main and sub-account systems, etc. Independent brokers can share the trading fluidity and depth over the MEXC platform and receive profit shares from fees.

To apply for a partnership, please contact: [institution@mexc.com](mailto:institution@mexc.com)

Contact us[​](#contact-us "Direct link to Contact us")
------------------------------------------------------

MEXC API Telegram Group [MEXC API Support Group](https://t.me/MEXCAPIsupport "MEXC API Support Group")

* For any general questions about the API not covered in the documentation.
* For any MM questions

MEXC Customer Support website.app online customer server

* For cases such as missing funds, help with 2FA, etc.

[Next

Change Log](/api-docs/spot-v3/change-log)

* [API Key Setup](#api-key-setup)
* [API Key Restrictions](#api-key-restrictions)
* [API Library](#api-library)
* [MEXC Broker Introduction](#mexc-broker-introduction)
  + [Broker Modes Supported by MEXC](#broker-modes-supported-by-mexc)
* [Contact us](#contact-us)