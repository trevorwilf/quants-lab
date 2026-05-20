"""max_hold_days uses XNYS sessions; holidays don't count.

Regression for [Report §15.2 P1]: pd.bdate_range ignores US market holidays
(Christmas, July 4, MLK Day), causing the time-stop to fire too early.
"""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_v2_lab.sim.exits import trading_days_since


def test_xnys_excludes_christmas() -> None:
    # 2024-12-23 (Mon) → 2024-12-31 (Tue). Wednesday 12-25 is Christmas (closed).
    # Sessions: Dec 23, 24 (early close), 26, 27, 30, 31.
    n = trading_days_since(_dt.date(2024, 12, 23), _dt.date(2024, 12, 31))
    # We exclude the entry day → 5 trading days from 12-23 onwards.
    assert n == 5


def test_xnys_excludes_july_fourth_2024() -> None:
    # 2024-07-01 (Mon) → 2024-07-08 (Mon). Thu 7-4 is Independence Day; Wed 7-3 is early close.
    # Sessions: Jul 1, 2, 3, 5, 8 (5 sessions inclusive of both ends).
    n = trading_days_since(_dt.date(2024, 7, 1), _dt.date(2024, 7, 8))
    # Excluding entry day: 4 trading days held.
    assert n == 4


def test_same_day_returns_zero() -> None:
    assert trading_days_since(_dt.date(2024, 9, 4), _dt.date(2024, 9, 4)) == 0
