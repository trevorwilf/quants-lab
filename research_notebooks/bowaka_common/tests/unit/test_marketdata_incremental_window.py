"""Regression tests for ``incremental_window`` daily-bar tail planning.

Covers the weekend/holiday end-date case that previously produced an inverted
``fetch_tail`` window (start > end) — every symbol then fired a guaranteed-400
"end should not be before start" request, spamming the run log with thousands of
tracebacks even though the lake was fully up to date.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from bowaka_common.marketdata.backfill import incremental_window


class _FakeCalendar:
    """Minimal XNYS stand-in: maps a session date to its next session date."""

    def __init__(self, mapping: dict[str, str]) -> None:
        self._m = {pd.Timestamp(k).date(): pd.Timestamp(v) for k, v in mapping.items()}

    def next_session(self, ts) -> pd.Timestamp:
        return self._m[pd.Timestamp(ts).date()]


def _write_daily(path, last_session: str) -> None:
    # 20:00 UTC == 16:00 ET in summer, so the session date is stable in NY.
    ts = pd.to_datetime([f"{last_session} 20:00:00"], utc=True)
    pd.DataFrame({"timestamp": ts, "close": [1.0]}).to_parquet(path)


def test_weekend_end_date_is_up_to_date(tmp_path):
    """Last bar = Friday, auto end = Saturday → up_to_date, no inverted fetch."""
    f = tmp_path / "d.parquet"
    _write_daily(f, "2026-06-05")  # Friday
    cal = _FakeCalendar({"2026-06-05": "2026-06-08"})  # next session = Monday
    plan = incremental_window(f, date(2026, 6, 6), calendar=cal)  # Saturday
    assert plan.action == "up_to_date"


def test_exact_end_date_is_up_to_date(tmp_path):
    """Last bar == target end → up_to_date (unchanged existing behavior)."""
    f = tmp_path / "d.parquet"
    _write_daily(f, "2026-06-05")
    cal = _FakeCalendar({"2026-06-05": "2026-06-08"})
    plan = incremental_window(f, date(2026, 6, 5), calendar=cal)
    assert plan.action == "up_to_date"


def test_normal_forward_tail_still_fetches(tmp_path):
    """A genuine gap (next session on or before target end) still tails."""
    f = tmp_path / "d.parquet"
    _write_daily(f, "2026-06-03")  # Wednesday
    cal = _FakeCalendar({"2026-06-03": "2026-06-04"})  # next session = Thursday
    plan = incremental_window(f, date(2026, 6, 5), calendar=cal)  # Friday
    assert plan.action == "fetch_tail"
    assert plan.start == date(2026, 6, 4)
    assert plan.end == date(2026, 6, 5)
