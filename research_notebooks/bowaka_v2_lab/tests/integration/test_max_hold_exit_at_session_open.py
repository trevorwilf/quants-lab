"""Realism Remediation 2 Phase 7 (Task 3 robustness) — a max-hold exit fires
on the session indexed ``entry_session + (max_hold_days - 1)`` XNYS trading
days (holidays inside the window do not count).

This integration test pins:

* a 3-day max-hold opened Mon exits at Wed's close (not Thu),
* a max-hold spanning a US market holiday correctly skips the holiday day,
* a 1-day max-hold exits at the close of the entry session itself.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.exits import walk_lot_exit, max_hold_exit_session
from bowaka_v2_lab.sim.portfolio import Position


_NO_TIME_STOP = {"time_stop": {"enabled": False}}


def _quiet_session_bars(symbol: str, sd: _dt.date) -> list[dict]:
    """A short quiet path 09:30..16:00 ET that NEVER touches the stop or target."""
    rows = []
    base = pd.Timestamp(f"{sd} 09:30", tz="America/New_York").tz_convert("UTC")
    for i in range(0, 391, 15):  # 09:30..16:00 in 15-min steps for speed
        ts = base + pd.Timedelta(minutes=i)
        rows.append({
            "symbol": symbol, "timestamp": ts,
            "open": 100.0, "high": 100.3, "low": 99.7, "close": 100.0,
            "volume": 1000.0,
        })
    return rows


def _multi_day_path(days: list[_dt.date], symbol: str = "AAA") -> pd.DataFrame:
    out = []
    for d in days:
        out.extend(_quiet_session_bars(symbol, d))
    return pd.DataFrame(out)


def _lot(
    entry_session: _dt.date, max_hold_days: int,
    *, entry_clock: str = "09:30",
) -> Position:
    base = pd.Timestamp(f"{entry_session} {entry_clock}",
                        tz="America/New_York").tz_convert("UTC")
    return Position(
        symbol="AAA", entry_date=entry_session, entry_price=100.0, qty=10,
        stop_pct=0.30, target_pct=0.30, max_hold_days=max_hold_days,
        entry_session=entry_session,
        entry_timestamp=base.isoformat(),
        stop_price=70.0, target_price=130.0,
    )


def test_max_hold_3_days_exits_at_close_of_third_trading_day() -> None:
    """Mon entry + max_hold_days=3 → exit at Wed close (Mon+2 trading days)."""
    # 2024-09-09 is a Monday — no surrounding US holidays.
    days = [_dt.date(2024, 9, 9), _dt.date(2024, 9, 10),
            _dt.date(2024, 9, 11), _dt.date(2024, 9, 12)]
    ev = walk_lot_exit(
        _lot(days[0], max_hold_days=3),
        _multi_day_path(days),
        exit_cfg=_NO_TIME_STOP,
    )
    assert ev is not None
    assert ev.exit_reason == "max_hold"
    assert ev.exit_date == _dt.date(2024, 9, 11), (
        f"3-day max-hold opened Mon 9-9 must exit Wed 9-11, got {ev.exit_date}"
    )


def test_max_hold_skips_us_market_holiday() -> None:
    """A max-hold spanning Christmas Day (12-25) skips the holiday — it does
    NOT count as a trading day."""
    # 2024-12-24 (Tue) → 12-25 holiday → 12-26 (Thu) → 12-27 (Fri). With
    # max_hold_days=3, the exit session must be 12-27 (Fri) — 12-25 doesn't count.
    days = [_dt.date(2024, 12, 24), _dt.date(2024, 12, 26),
            _dt.date(2024, 12, 27), _dt.date(2024, 12, 30)]
    ev = walk_lot_exit(
        _lot(days[0], max_hold_days=3),
        _multi_day_path(days),
        exit_cfg=_NO_TIME_STOP,
    )
    assert ev is not None
    assert ev.exit_reason == "max_hold"
    assert ev.exit_date == _dt.date(2024, 12, 27), (
        f"max-hold spanning Christmas must exit Fri 12-27, got {ev.exit_date}"
    )


def test_max_hold_one_day_exits_on_entry_session() -> None:
    """``max_hold_days == 1`` → exit at the close of the entry session itself."""
    sd = _dt.date(2024, 9, 9)  # Monday
    days = [sd, _dt.date(2024, 9, 10)]
    ev = walk_lot_exit(
        _lot(sd, max_hold_days=1),
        _multi_day_path(days),
        exit_cfg=_NO_TIME_STOP,
    )
    assert ev is not None
    assert ev.exit_reason == "max_hold"
    assert ev.exit_date == sd, (
        f"max_hold_days=1 must exit on the entry session itself, got {ev.exit_date}"
    )


def test_max_hold_exit_session_helper_matches_walker_behaviour() -> None:
    """``max_hold_exit_session(entry, max_hold_days)`` is the source-of-truth
    helper the walker uses; pin its math for the three cases above."""
    # 3 trading days from Mon 9-9 → Wed 9-11.
    assert max_hold_exit_session(_dt.date(2024, 9, 9), 3) == _dt.date(2024, 9, 11)
    # 3 trading days from Tue 12-24 with Christmas in between → Fri 12-27.
    assert max_hold_exit_session(_dt.date(2024, 12, 24), 3) == _dt.date(2024, 12, 27)
    # 1 trading day from Mon 9-9 → Mon 9-9 itself.
    assert max_hold_exit_session(_dt.date(2024, 9, 9), 1) == _dt.date(2024, 9, 9)
