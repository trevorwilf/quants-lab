# Source and Documentation Issues

Upstream client library bugs and documentation anomalies that engineers should be aware of.

## NonKYC Python Client

### `ws_unsubscribe_reports` sends `subscribeReports`

The official Python client at `NonKYCExchange/NonKycPythonApiClient` defines a method called `ws_unsubscribe_reports` that sends the WS method `subscribeReports` instead of `unsubscribeReports`. This means calling the unsubscribe function will **re-subscribe** instead of unsubscribing.

**Impact**: If you copy the official client's unsubscribe logic, report notifications will continue.

**Workaround**: Send `{"method": "unsubscribeReports", "params": {}}` directly.

### `get_asset_by_id` defined twice with different semantics

The Python client defines `get_asset_by_id` for both `/asset/getbyid/{id}` and `/asset/getbyticker/{ticker}`. In Python, the second definition silently shadows the first.

**Impact**: Calling `client.get_asset_by_id(some_id)` will actually call `getbyticker`, not `getbyid`.

**Workaround**: Call the REST endpoints directly instead of relying on the client wrapper.

### NonKYC WebSocket URL mismatch

The official WS API docs page references `wss://ws.nonkyc.io` but the Python client uses `wss://api.nonkyc.io`. Live validation confirms `wss://api.nonkyc.io` works. The `ws.nonkyc.io` endpoint may still work but is not tested.

### `cancel_order` path drift between Python client and OpenAPI

The official Python client uses path `/cancel_order` (with underscore), but the OpenAPI spec documents `/cancelorder` (no underscore). Both may work at runtime, but implementations should use the OpenAPI path `/cancelorder` as canonical.

**Impact**: Code derived from the Python client may use the wrong endpoint path.

**Workaround**: Use `/cancelorder` as documented in the OpenAPI spec.

### `ws_get_asset` sends `getAssets` (plural) instead of `getAsset` (singular)

The official Python client method `ws_get_asset(ticker)` sends the WS method `getAssets` (plural) with a `ticker` parameter, rather than `getAsset` (singular). This may work because the server accepts `getAssets` with a ticker filter, but the method name is misleading.

**Impact**: The singular `getAsset` WS method may have different behavior or be a separate method entirely.

**Workaround**: Test both `getAsset` and `getAssets` with ticker param to confirm server behavior.

## MEXC Spot

### `POST /api/v3/userDataStream` requires signed parameters despite docs

The official MEXC docs state `Parameters: NONE` for creating a listen key. However, live testing shows that a header-only POST returns HTTP 400. A second attempt with signed query parameters (`timestamp`, `recvWindow`, `signature`) succeeds.

**Impact**: Implementations that follow the docs literally will fail to create listen keys.

**Workaround**: Always sign the request with `timestamp` and `signature` parameters.

## MEXC Futures

### Private endpoint base URL inconsistency

Public futures endpoints work on `https://api.mexc.com/api/v1/contract/...`. Private endpoints under `/api/v1/private/...` may return 400 on `api.mexc.com` and require `https://contract.mexc.com` as the base URL instead.

**Impact**: Using a single base URL for all futures endpoints will fail for private calls.

**Workaround**: Use `contract.mexc.com` for private futures endpoints, or implement a fallback mechanism.

