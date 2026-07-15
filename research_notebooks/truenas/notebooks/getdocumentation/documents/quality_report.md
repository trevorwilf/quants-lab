# Quality Report

* **Script version**: 4.14.0
* **Generated**: 2026-04-04T04:32:31.501269Z

## NonKYC

* REST base: `https://api.nonkyc.io/api/v2`
* WS base: `wss://api.nonkyc.io`
* REST endpoints documented: **50** (tested: 45, schema-only: 4)
* REST test coverage: **90%** (45/50)
* REST with live response schema: **43**
* REST with live response example: **43**
* WS methods documented: **12** (tested: 12)

## MEXC Spot V3

* REST base: `https://api.mexc.com`
* WS base: `wss://wbs-api.mexc.com/ws`
* REST endpoints documented: **70** (tested: 46, schema-only: 24)
* REST test coverage: **66%** (46/70)
* REST with live response schema: **42**
* REST with live response example: **42**
* WS methods documented: **15** (tested: 2)

## MEXC Futures

* REST base: `https://api.mexc.com`
* WS base: `wss://contract.mexc.com/edge`
* REST endpoints documented: **107** (tested: 36, schema-only: 71)
* REST test coverage: **34%** (36/107)
* REST with live response schema: **18**
* REST with live response example: **18**
* WS methods documented: **11** (tested: 2)

## Validation Summary

### mexc_futures

* fail: 0
* pass: 18
* skip: 0
* warn: 20

### mexc_spot

* fail: 0
* pass: 43
* skip: 0
* warn: 6

### nonkyc

* fail: 0
* pass: 56
* skip: 0
* warn: 2

## Issues

* INFO: MEXC Spot V3 WS coverage low — 2/15 methods tested
* WARNING: MEXC Futures REST test coverage is 34% (36/107)
* INFO: MEXC Futures has 2 mutating endpoints without request-field tables: POST /api/v1/private/order/batch_cancel_with_external, POST /api/v1/private/order/batch_query_with_external
* INFO: MEXC Futures WS coverage low — 2/11 methods tested

## Source Freshness

Documentation coverage is bounded by the official source mirrors fetched during the run. If the official docs add new endpoints between fetches, the bundle will lag until re-run.

| Exchange | Primary Sources | Freshness Model |
| --- | --- | --- |
| MEXC Spot V3 | Official pages (`mexc.com/api-docs/spot-v3/*`) + GitHub mirror | Fetched live each run |
| MEXC Futures | Official pages (`mexc.com/api-docs/futures/*`) + GitHub mirror | Fetched live each run |
| NonKYC | `api.nonkyc.io/openapi.json` + GitHub clients | Fetched live each run |

To check for freshness drift: compare `_raw/catalog.json` endpoint counts against the official docs, or check the fetched `sources/mexc_spot_v3_changelog.md` for items not yet in the endpoint catalog.

