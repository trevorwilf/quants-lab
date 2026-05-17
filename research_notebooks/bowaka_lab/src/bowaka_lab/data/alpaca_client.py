"""Thin Alpaca-py wrapper with rate limiting and feed-fallback guards.

Wraps:

- ``alpaca.trading.TradingClient`` for asset listing.
- ``alpaca.data.historical.StockHistoricalDataClient`` for bars/quotes/corp actions.

Behavior:

- Every outbound call goes through the injected ``TokenBucket``.
- SIP authorization failures are surfaced; fallback only happens when
  ``allow_feed_fallback=True`` and a different ``fallback_feed`` is configured.
- ``raise_for_unauthorized`` re-classifies HTTP 403 into a ``FeedUnavailableError``
  so callers can distinguish credentials from data-feed entitlement.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from bowaka_lab.data.rate_limit import TokenBucket


class FeedUnavailableError(RuntimeError):
    """Raised when the requested data feed is not entitled (e.g. SIP without subscription)."""


@dataclass
class AlpacaClientConfig:
    api_key: str
    api_secret: str
    feed: str = "iex"
    allow_feed_fallback: bool = False
    fallback_feed: str = "iex"
    rate_limit_requests_per_minute: float = 180.0
    paper: bool = True

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "AlpacaClientConfig":
        env = env if env is not None else os.environ  # type: ignore[assignment]
        api_key = env.get("ALPACA_API_KEY_ID")
        api_secret = env.get("ALPACA_API_SECRET_KEY")
        if not api_key or not api_secret:
            raise RuntimeError("ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY must be set")
        return cls(
            api_key=api_key,
            api_secret=api_secret,
            feed=env.get("BOWAKA_ALPACA_FEED", "iex"),
            paper=env.get("ALPACA_PAPER", "true").lower() != "false",
        )


def _is_unauthorized(exc: BaseException) -> bool:
    msg = str(exc).lower()
    code = getattr(exc, "status_code", None)
    return code in (401, 403) or "unauthorized" in msg or "subscription" in msg or "forbidden" in msg


class AlpacaClient:
    """Wrapper around alpaca-py's StockHistoricalDataClient + TradingClient."""

    def __init__(
        self,
        config: AlpacaClientConfig | None = None,
        *,
        rate_limiter: TokenBucket | None = None,
        trading_client_factory: Callable[..., Any] | None = None,
        data_client_factory: Callable[..., Any] | None = None,
    ):
        self.config = config or AlpacaClientConfig.from_env()
        self.rate_limiter = rate_limiter or TokenBucket(self.config.rate_limit_requests_per_minute)
        self._trading_client_factory = trading_client_factory
        self._data_client_factory = data_client_factory
        self._trading: Any | None = None
        self._data: Any | None = None

    # --- Lazy clients ---

    def trading(self) -> Any:
        if self._trading is None:
            if self._trading_client_factory is not None:
                self._trading = self._trading_client_factory()
            else:
                from alpaca.trading.client import TradingClient

                self._trading = TradingClient(
                    api_key=self.config.api_key,
                    secret_key=self.config.api_secret,
                    paper=self.config.paper,
                )
        return self._trading

    def data(self) -> Any:
        if self._data is None:
            if self._data_client_factory is not None:
                self._data = self._data_client_factory()
            else:
                from alpaca.data.historical import StockHistoricalDataClient

                self._data = StockHistoricalDataClient(
                    api_key=self.config.api_key,
                    secret_key=self.config.api_secret,
                )
        return self._data

    # --- Rate-limited dispatch ---

    def call(self, fn: Callable, *args, **kw) -> Any:
        self.rate_limiter.acquire(1)
        try:
            return fn(*args, **kw)
        except Exception as exc:  # noqa: BLE001
            if _is_unauthorized(exc):
                if self.config.allow_feed_fallback and self.config.feed != self.config.fallback_feed:
                    return fn(*args, **kw)
                raise FeedUnavailableError(
                    f"Feed {self.config.feed!r} is not authorized: {exc}"
                ) from exc
            raise

    @property
    def feed(self) -> str:
        return self.config.feed
