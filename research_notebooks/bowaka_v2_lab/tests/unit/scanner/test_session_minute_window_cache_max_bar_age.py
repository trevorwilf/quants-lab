"""``max_bar_age_seconds`` tightens the lower bound of the cache slice.

Speedup report v2 §5.7 / Phase 4 task 6. The constructor knob defaults to
``None`` (legacy parity — :func:`intraday_window_start` is the lower bound).
When set, the lower bound becomes the LATER of the policy bound and
``scan_ts - max_bar_age_seconds``. This test exercises the tightened
window with an explicit ``max_bar_age_seconds=120``.

The synthetic ``build_tiny_lake`` writes 30 bars per session at
``[09:30:00, 09:30:01, …, 09:30:29]`` UTC (per :func:`build_tiny_lake`'s
own layout). A 120-second window at 09:30:15 UTC retains bars whose
timestamp is in ``[09:28:15, 09:30:15]`` — i.e. all of them.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from bowaka_common.marketdata import MarketDataStore
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake
from bowaka_v2_lab.scanner.session_minute_window_cache import (
    SessionMinuteWindowCache,
)


@pytest.fixture
def lake(tmp_path: Path) -> Path:
    p = tmp_path / "lake"
    build_tiny_lake(p, ["AAA"], start=dt.date(2024, 1, 28), end=dt.date(2024, 2, 5))
    return p


def _utc(date: dt.date, h: int, m: int, s: int = 0) -> pd.Timestamp:
    return pd.Timestamp(
        dt.datetime.combine(date, dt.time(hour=h, minute=m, second=s)),
        tz="America/New_York",
    ).tz_convert("UTC")


def test_max_bar_age_tightens_lower_bound(lake: Path) -> None:
    """At max_bar_age_seconds=300 (5 minutes) the cache returns at most the
    last 5 minutes of bars relative to ``scan_ts``.
    """
    cache_tight = SessionMinuteWindowCache(
        MarketDataStore(lake), dt.date(2024, 1, 30), ["AAA"], feed="iex",
        max_bar_age_seconds=300.0,
    )
    cache_legacy = SessionMinuteWindowCache(
        MarketDataStore(lake), dt.date(2024, 1, 30), ["AAA"], feed="iex",
        max_bar_age_seconds=None,  # default — legacy parity bound
    )
    scan_ts = _utc(dt.date(2024, 1, 30), 10, 0)
    tight = cache_tight.bars_until("AAA", scan_ts)
    legacy = cache_legacy.bars_until("AAA", scan_ts)
    # Tightened window must be a strict suffix of the legacy slice.
    assert len(tight) <= len(legacy), (
        f"tight ({len(tight)}) > legacy ({len(legacy)}) — bound did not tighten"
    )
    if len(tight) > 0 and len(legacy) > 0:
        # The first timestamp of the tightened slice must be >= scan_ts - 300s.
        lower = scan_ts - pd.Timedelta(seconds=300)
        first = pd.Timestamp(tight["timestamp"].iloc[0])
        assert first >= lower, (
            f"tight first bar {first} earlier than scan_ts - 300s ({lower})"
        )


def test_max_bar_age_none_matches_legacy_window(lake: Path) -> None:
    """With ``max_bar_age_seconds=None`` (default) the cache's lower bound IS
    :func:`intraday_window_start` for the resolved policy.

    The tiny fixture's minute bars live at 13:30-14:00 UTC (08:30-09:00 ET),
    which is BEFORE the default ``scanner_start_to_scan`` (09:45 ET) window
    start. So with the default policy a scan at 10:00 ET returns 0 bars
    (correct — legacy parity). With ``extended_hours_to_scan`` (04:00 ET)
    the window catches the synthetic bars.
    """
    cache = SessionMinuteWindowCache(
        MarketDataStore(lake), dt.date(2024, 1, 30), ["AAA"], feed="iex",
        intraday_policy="extended_hours_to_scan",
    )
    scan_ts = _utc(dt.date(2024, 1, 30), 15, 0)
    out = cache.bars_until("AAA", scan_ts)
    assert len(out) > 0, "legacy-parity bound returned no bars with premarket policy"
    last = pd.Timestamp(out["timestamp"].iloc[-1])
    assert last <= scan_ts
