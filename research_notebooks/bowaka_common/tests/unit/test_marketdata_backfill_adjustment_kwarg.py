"""``make_alpaca_bars_fetcher`` threads ``cfg.adjustment`` into the Alpaca SDK request.

Pre-patch the helper omitted the ``adjustment`` kwarg from
``StockBarsRequest``; Alpaca's default is RAW, so any partition labelled
``adjustment="split_adjusted"`` got silently mislabelled (path said
adjusted, payload was raw). Bowaka v2 speedup-v2 P0-A follow-up: the
fetcher now maps the config string to the SDK enum and passes it
through. This test mocks the Alpaca classes so the test never opens a
network connection.
"""
from __future__ import annotations

import datetime as dt
import logging
from unittest import mock

import pytest

from bowaka_common.marketdata import backfill


def _cfg(tmp_path, **kw):
    base = dict(
        api_key="k", api_secret="s", paper=True, feed="iex",
        start_date=dt.date(2026, 5, 1), end_date=dt.date(2026, 5, 5),
        lake_root=tmp_path,
    )
    base.update(kw)
    return backfill.BackfillConfig(**base)


@pytest.mark.parametrize(
    "cfg_adjustment,expected_enum_name",
    [
        ("raw", "RAW"),
        ("split_adjusted", "SPLIT"),
        ("split", "SPLIT"),
        ("dividend_adjusted", "DIVIDEND"),
        ("dividend", "DIVIDEND"),
        ("all", "ALL"),
        ("adjusted", "ALL"),
    ],
)
def test_fetcher_passes_adjustment_enum_to_stockbars_request(
    cfg_adjustment, expected_enum_name, tmp_path,
):
    cfg = _cfg(tmp_path, adjustment=cfg_adjustment)
    limiter = backfill.RateLimiter(60)

    captured_requests: list = []

    class _FakeResp:
        def __init__(self):
            self.data = {"A": []}
            self.next_page_token = None

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        def get_stock_bars(self, req):
            captured_requests.append(req)
            return _FakeResp()

    with mock.patch(
        "alpaca.data.historical.StockHistoricalDataClient", _FakeClient,
    ):
        fetcher = backfill.make_alpaca_bars_fetcher(
            cfg, limiter, logging.getLogger("test"),
        )
        start = dt.datetime(2026, 5, 1, tzinfo=dt.timezone.utc)
        end = dt.datetime(2026, 5, 2, tzinfo=dt.timezone.utc)
        fetcher(["A"], "1d", start, end)

    assert captured_requests, "fetcher did not call get_stock_bars"
    req = captured_requests[0]
    # The SDK accepts ``adjustment`` as a kwarg + stores it on the request.
    assert hasattr(req, "adjustment"), (
        f"StockBarsRequest produced without adjustment attr; got {req}"
    )
    assert req.adjustment.name == expected_enum_name, (
        f"cfg.adjustment={cfg_adjustment!r} → "
        f"expected {expected_enum_name!r}, got {req.adjustment.name!r}"
    )


def test_unknown_adjustment_falls_back_to_raw(tmp_path):
    """An unknown ``cfg.adjustment`` falls back to RAW (defensive)."""
    cfg = _cfg(tmp_path, adjustment="nonsense_value")
    limiter = backfill.RateLimiter(60)

    captured: list = []

    class _FakeResp:
        data = {"A": []}
        next_page_token = None

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        def get_stock_bars(self, req):
            captured.append(req)
            return _FakeResp()

    with mock.patch("alpaca.data.historical.StockHistoricalDataClient", _FakeClient):
        fetcher = backfill.make_alpaca_bars_fetcher(
            cfg, limiter, logging.getLogger("test"),
        )
        start = dt.datetime(2026, 5, 1, tzinfo=dt.timezone.utc)
        end = dt.datetime(2026, 5, 2, tzinfo=dt.timezone.utc)
        fetcher(["A"], "1d", start, end)

    assert captured[0].adjustment.name == "RAW"
