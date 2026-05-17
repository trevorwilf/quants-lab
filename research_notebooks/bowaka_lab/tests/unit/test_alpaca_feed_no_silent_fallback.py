"""Phase 2: SIP 403 raises unless allow_feed_fallback=True."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from bowaka_lab.data.alpaca_client import (
    AlpacaClient,
    AlpacaClientConfig,
    FeedUnavailableError,
)
from bowaka_lab.data.bars import fetch_daily_bars


class _UnauthorizedException(Exception):
    """Mimic alpaca-py's APIError shape for 403 responses."""

    def __init__(self, msg: str = "subscription required"):
        super().__init__(msg)
        self.status_code = 403


class _Sip403DataClient:
    def __init__(self, response_when_allowed: Any | None = None):
        self.response = response_when_allowed
        self.call_count = 0

    def get_stock_bars(self, request):
        self.call_count += 1
        if self.response is None or self.call_count == 1:
            raise _UnauthorizedException("Unauthorized: SIP subscription required")
        return self.response


def _request_factory(*, symbol_or_symbols, start, end, page_token, limit):
    return {"symbols": symbol_or_symbols, "start": start, "end": end, "page_token": page_token, "limit": limit}


def test_sip_403_raises_when_fallback_disabled():
    fake = _Sip403DataClient()
    config = AlpacaClientConfig(
        api_key="fake",
        api_secret="fake",
        feed="sip",
        allow_feed_fallback=False,
        rate_limit_requests_per_minute=10_000,
    )
    client = AlpacaClient(config=config, data_client_factory=lambda: fake)
    with pytest.raises(FeedUnavailableError):
        fetch_daily_bars(
            client,
            symbols=["AAA"],
            start=date(2026, 5, 12),
            end=date(2026, 5, 12),
            request_factory=_request_factory,
        )


def test_sip_403_silently_falls_back_when_allowed():
    from dataclasses import dataclass

    import pandas as pd

    @dataclass
    class _Bar:
        timestamp: pd.Timestamp
        open: float
        high: float
        low: float
        close: float
        volume: int
        vwap: float | None = None
        trade_count: int | None = None

    @dataclass
    class _Resp:
        data: dict
        next_page_token: str | None = None

    resp = _Resp(data={"AAA": [_Bar(pd.Timestamp("2026-05-12", tz="UTC"), 10, 11, 9, 10.5, 100)]})
    fake = _Sip403DataClient(response_when_allowed=resp)
    config = AlpacaClientConfig(
        api_key="fake",
        api_secret="fake",
        feed="sip",
        allow_feed_fallback=True,
        fallback_feed="iex",
        rate_limit_requests_per_minute=10_000,
    )
    client = AlpacaClient(config=config, data_client_factory=lambda: fake)
    df = fetch_daily_bars(
        client,
        symbols=["AAA"],
        start=date(2026, 5, 12),
        end=date(2026, 5, 12),
        request_factory=_request_factory,
    )
    assert df.shape[0] == 1
    assert fake.call_count == 2  # one failed SIP, one fallback success
