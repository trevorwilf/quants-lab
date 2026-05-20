"""Token-bucket rate limiter.

Used to keep Alpaca HTTP calls comfortably below the documented 200 RPM limit
on the Basic Trading API data plan. Default 180 RPM = 3 calls/sec average.
"""

from __future__ import annotations

import threading
import time as _time
from dataclasses import dataclass


@dataclass
class _Bucket:
    capacity: float
    tokens: float
    refill_per_sec: float
    last_refill: float


class TokenBucket:
    """Simple thread-safe token bucket."""

    def __init__(self, requests_per_minute: float = 180.0, *, burst: int | None = None):
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be > 0")
        capacity = float(burst if burst is not None else max(1, int(requests_per_minute / 60.0 * 2)))
        self._lock = threading.Lock()
        self._b = _Bucket(
            capacity=capacity,
            tokens=capacity,
            refill_per_sec=requests_per_minute / 60.0,
            last_refill=_time.monotonic(),
        )

    def _refill(self, now: float | None = None) -> None:
        now = now if now is not None else _time.monotonic()
        elapsed = now - self._b.last_refill
        if elapsed <= 0:
            return
        new_tokens = elapsed * self._b.refill_per_sec
        self._b.tokens = min(self._b.capacity, self._b.tokens + new_tokens)
        self._b.last_refill = now

    def try_acquire(self, n: int = 1) -> bool:
        with self._lock:
            self._refill()
            if self._b.tokens >= n:
                self._b.tokens -= n
                return True
            return False

    def acquire(self, n: int = 1, *, sleep_fn=_time.sleep) -> float:
        """Block until ``n`` tokens are available. Returns seconds waited."""
        waited = 0.0
        while True:
            with self._lock:
                self._refill()
                if self._b.tokens >= n:
                    self._b.tokens -= n
                    return waited
                deficit = n - self._b.tokens
                wait_s = deficit / self._b.refill_per_sec
            sleep_fn(wait_s)
            waited += wait_s

    @property
    def tokens_available(self) -> float:
        with self._lock:
            self._refill()
            return self._b.tokens
