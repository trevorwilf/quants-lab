# Documentation vs Live Behavior Discrepancies

Differences between official documentation and actual API behavior observed during live validation.

## MEXC Spot

### `POST /api/v3/userDataStream` — unsigned request fails

| | Documented | Observed |
| --- | --- | --- |
| Parameters | `NONE` | Requires `timestamp`, `recvWindow`, `signature` |
| Unsigned POST | Should work | Returns HTTP 400 |
| Signed POST | Not mentioned | Returns HTTP 200 with `listenKey` |

### Spot WS market data encoding

| | Documented | Observed |
| --- | --- | --- |
| Format | JSON | Subscription ACK is JSON; market data frames are protobuf/base64 |

Implementations must decode protobuf frames for actual market data.

## MEXC Futures

### Private endpoint base URL

| | Documented | Observed |
| --- | --- | --- |
| Base URL | `https://api.mexc.com` | Returns 400 for `/api/v1/private/*` |
| Fallback | Not documented | `https://contract.mexc.com` works |

### Account assets endpoint — API key permission

| | Expected | Observed |
| --- | --- | --- |
| Response | Account balances | `{"code": 701, "message": "Please enable API Key read access"}` |

This is a credential/permission configuration issue, not a protocol failure. Ensure the API key has 'read' permission enabled for futures.

## NonKYC

### `/asset/getbyid/{id}` — Cloudflare WAF block

| | Documented | Observed |
| --- | --- | --- |
| Response | Asset object | HTTP 403 Cloudflare block page |

This endpoint appears to be blocked by Cloudflare WAF for certain IP ranges/patterns. The alternative `/asset/getbyticker/{ticker}` works and returns the same data.

