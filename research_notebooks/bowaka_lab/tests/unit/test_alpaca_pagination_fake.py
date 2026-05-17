"""Phase 2: fake Alpaca client to assert pagination is correct."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd
import pytest

from bowaka_lab.data.alpaca_client import AlpacaClient, AlpacaClientConfig
from bowaka_lab.data.bars import fetch_daily_bars, fetch_minute_bars


@dataclass
class _FakeBar:
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float | None = None
    trade_count: int | None = None


@dataclass
class _FakeResponse:
    data: dict[str, list[_FakeBar]]
    next_page_token: str | None = None


class _FakeDataClient:
    """Returns three pages keyed by ``page_token``."""

    def __init__(self):
        self.calls: list[dict[str, Any]] = []
        # Three pages: tokens None -> "p2" -> "p3" -> end
        self._pages = {
            None: _FakeResponse(
                data={
                    "AAA": [_FakeBar(pd.Timestamp("2026-05-12 13:30Z"), 10, 11, 9, 10.5, 100)],
                    "BBB": [_FakeBar(pd.Timestamp("2026-05-12 13:30Z"), 20, 21, 19, 20.5, 200)],
                },
                next_page_token="p2",
            ),
            "p2": _FakeResponse(
                data={
                    "AAA": [_FakeBar(pd.Timestamp("2026-05-13 13:30Z"), 10.5, 11.5, 10, 11.0, 110)],
                    "BBB": [_FakeBar(pd.Timestamp("2026-05-13 13:30Z"), 20.5, 21.5, 20, 21.0, 210)],
                },
                next_page_token="p3",
            ),
            "p3": _FakeResponse(
                data={
                    "AAA": [_FakeBar(pd.Timestamp("2026-05-14 13:30Z"), 11.0, 12.0, 10.8, 11.8, 120)],
                    "BBB": [_FakeBar(pd.Timestamp("2026-05-14 13:30Z"), 21.0, 22.0, 20.8, 21.8, 220)],
                },
                next_page_token=None,
            ),
        }

    def get_stock_bars(self, request: dict):
        token = request.get("page_token")
        self.calls.append(dict(request))
        page = self._pages[token]
        requested = set(request.get("symbols") or [])
        if requested:
            filtered_data = {s: bars for s, bars in page.data.items() if s in requested}
            return _FakeResponse(data=filtered_data, next_page_token=page.next_page_token)
        return page


def _client_with_fake() -> tuple[AlpacaClient, _FakeDataClient]:
    fake = _FakeDataClient()
    config = AlpacaClientConfig(
        api_key="fake",
        api_secret="fake",
        feed="iex",
        rate_limit_requests_per_minute=10_000,
    )
    client = AlpacaClient(config=config, data_client_factory=lambda: fake)
    return client, fake


def _request_factory(*, symbol_or_symbols, start, end, page_token, limit):
    return {"symbols": symbol_or_symbols, "start": start, "end": end, "page_token": page_token, "limit": limit}


def test_pagination_collects_all_pages():
    client, fake = _client_with_fake()
    df = fetch_daily_bars(
        client,
        symbols=["AAA", "BBB"],
        start=date(2026, 5, 12),
        end=date(2026, 5, 14),
        request_factory=_request_factory,
    )
    # 2 symbols × 3 days = 6 rows
    assert df.shape[0] == 6
    # All symbols present with three rows each.
    counts = df["symbol"].value_counts()
    assert counts["AAA"] == 3
    assert counts["BBB"] == 3


def test_pagination_no_duplicates():
    client, fake = _client_with_fake()
    df = fetch_daily_bars(
        client,
        symbols=["AAA", "BBB"],
        start=date(2026, 5, 12),
        end=date(2026, 5, 14),
        request_factory=_request_factory,
    )
    dup = df.duplicated(subset=["symbol", "timestamp"])
    assert dup.sum() == 0


def test_pagination_three_api_calls_made():
    client, fake = _client_with_fake()
    fetch_daily_bars(
        client,
        symbols=["AAA", "BBB"],
        start=date(2026, 5, 12),
        end=date(2026, 5, 14),
        request_factory=_request_factory,
    )
    assert len(fake.calls) == 3


def test_pagination_request_uses_returned_token():
    client, fake = _client_with_fake()
    fetch_daily_bars(
        client,
        symbols=["AAA"],
        start=date(2026, 5, 12),
        end=date(2026, 5, 14),
        request_factory=_request_factory,
    )
    tokens = [c["page_token"] for c in fake.calls]
    assert tokens == [None, "p2", "p3"]


def test_minute_bars_use_same_factory_contract():
    client, fake = _client_with_fake()
    df = fetch_minute_bars(
        client,
        symbols=["AAA"],
        start=date(2026, 5, 12),
        end=date(2026, 5, 14),
        request_factory=_request_factory,
    )
    assert df.shape[0] == 3


def test_empty_symbols_returns_empty_df():
    client, _ = _client_with_fake()
    df = fetch_daily_bars(
        client,
        symbols=[],
        start=date(2026, 5, 12),
        end=date(2026, 5, 14),
        request_factory=_request_factory,
    )
    assert df.empty
