"""Phase 2: token-bucket behavior."""

from __future__ import annotations

import pytest

from bowaka_lab.data.rate_limit import TokenBucket


def test_rejects_zero_rate():
    with pytest.raises(ValueError):
        TokenBucket(0)


def test_initial_burst_fills_bucket():
    tb = TokenBucket(60.0)  # 1 per second
    assert tb.try_acquire(1)
    assert tb.try_acquire(1)


def test_try_acquire_returns_false_when_exhausted():
    tb = TokenBucket(60.0, burst=2)
    assert tb.try_acquire(1)
    assert tb.try_acquire(1)
    assert tb.try_acquire(1) is False


def test_refill_replenishes_tokens():
    sleep_calls = []

    def fake_sleep(s):
        sleep_calls.append(s)

    tb = TokenBucket(120.0, burst=1)  # 2/sec
    assert tb.try_acquire(1)
    # Bucket now empty; second call should block ~0.5s before granting.
    waited = tb.acquire(1, sleep_fn=fake_sleep)
    assert waited > 0
    assert sum(sleep_calls) == pytest.approx(waited, rel=0.5)


def test_tokens_available_property():
    tb = TokenBucket(60.0, burst=4)
    assert tb.tokens_available == pytest.approx(4.0, abs=0.01)
    tb.try_acquire(2)
    assert tb.tokens_available <= 2.1
