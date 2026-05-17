"""Phase 2: live Alpaca smoke. Skipped when credentials are missing."""

from __future__ import annotations

import os
from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.live_alpaca


def _has_creds() -> bool:
    return bool(os.environ.get("ALPACA_API_KEY_ID") and os.environ.get("ALPACA_API_SECRET_KEY"))


def test_live_alpaca_asset_fetch():
    if not _has_creds():
        pytest.skip("Alpaca credentials not configured")
    from alpaca.trading.requests import GetAssetsRequest

    from bowaka_lab.data.alpaca_client import AlpacaClient
    from bowaka_lab.data.assets import build_asset_snapshot

    client = AlpacaClient()
    raw = client.call(client.trading().get_all_assets, GetAssetsRequest(status="active"))
    meta, rows = build_asset_snapshot(raw, allowed_exchanges=["NASDAQ", "NYSE"])
    assert meta["asset_count"] > 0
    assert rows[0].instrument_class in (
        "operating_equity",
        "etf",
        "etn",
        "leveraged_etp",
        "inverse_etp",
        "spac",
        "preferred",
        "unknown",
    )


def test_live_alpaca_daily_bar_fetch():
    if not _has_creds():
        pytest.skip("Alpaca credentials not configured")

    from bowaka_lab.data.alpaca_client import AlpacaClient
    from bowaka_lab.data.bars import fetch_daily_bars

    client = AlpacaClient()
    df = fetch_daily_bars(
        client,
        symbols=["AAPL"],
        start=date.today() - timedelta(days=14),
        end=date.today() - timedelta(days=1),
    )
    # Even on a weekend run, we should have at least one daily bar.
    assert df.shape[0] >= 1
    assert "symbol" in df.columns
    assert "close" in df.columns
