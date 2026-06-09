"""Alpaca market-data API reachability probe for scheduled_weekly_refresh.ps1.

Exit codes:
  0  UP            — the SIP data API answered a minimal request with data.
  1  DOWN          — transient (maintenance / 5xx / connection / timeout / empty
                     payload) -> the wrapper retries in 1h.
  2  CONFIG/AUTH   — missing creds, or HTTP 401/403 (incl. a missing SIP
                     entitlement) -> do NOT retry (an hourly retry won't fix it).

Probes the SAME feed the backfill uses (SIP), so a lapsed SIP entitlement
surfaces here as a 403 instead of silently failing the backfill weeks later.
Classifies on the structured HTTP ``status_code`` (the alpaca-py APIError message
is the raw response BODY, not the status), falling back to body-substring only
for non-APIError exceptions. Credentials are never printed.
"""
from __future__ import annotations

import sys


def main() -> int:
    try:
        from bowaka_common.marketdata.backfill import find_and_load_dotenv, resolve_env
    except Exception as exc:  # noqa: BLE001 — import/path problem is config-level
        print(f"IMPORT_ERROR: {type(exc).__name__}: {exc}")
        return 2

    find_and_load_dotenv()
    try:
        env = resolve_env()
    except Exception as exc:  # noqa: BLE001 — missing creds: config error, no retry
        print(f"CONFIG_ERROR: {exc}")
        return 2

    try:
        from alpaca.data.enums import DataFeed
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockLatestBarRequest
    except Exception as exc:  # noqa: BLE001
        print(f"IMPORT_ERROR (alpaca sdk): {type(exc).__name__}: {exc}")
        return 2

    try:
        client = StockHistoricalDataClient(
            api_key=env["ALPACA_API_KEY_ID"], secret_key=env["ALPACA_API_SECRET_KEY"]
        )
        # Minimal call on the SAME feed the backfill uses (SIP). Exercises auth,
        # the SIP entitlement, and connectivity to the data API.
        bars = client.get_stock_latest_bar(
            StockLatestBarRequest(symbol_or_symbols="AAPL", feed=DataFeed.SIP)
        )
        if not bars or "AAPL" not in bars:
            print("DOWN: SIP latest-bar returned an empty payload")
            return 1
        print("UP")
        return 0
    except Exception as exc:  # noqa: BLE001
        # Classify on the structured HTTP status first (immune to body format).
        status = getattr(exc, "status_code", None)
        if status in (401, 403):
            print(f"AUTH_ERROR (status={status}): {type(exc).__name__}: {exc}")
            return 2
        if status is None:
            # Non-APIError (connection/timeout) — fall back to body text only for
            # an unambiguous auth phrase; otherwise treat as transient.
            msg = str(exc).lower()
            if "unauthorized" in msg or "forbidden" in msg:
                print(f"AUTH_ERROR (body): {type(exc).__name__}: {exc}")
                return 2
        print(f"DOWN: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
