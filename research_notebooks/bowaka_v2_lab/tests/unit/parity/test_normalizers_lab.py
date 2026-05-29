"""Lab-side normalizer reads ``BacktestResult.trades`` (list[dict])."""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

from bowaka_v2_lab.parity.normalizers import (
    _normalize_lab_trades,
    normalize_lab_output,
)


def test_normalize_lab_trades_handles_both_naming_conventions() -> None:
    rows = [
        # New-style keys.
        {
            "session_date": _dt.date(2026, 5, 19),
            "symbol": "AAA",
            "entry_timestamp": "2026-05-19T14:30:00+00:00",
            "entry_price": 10.5,
            "qty": 100,
            "exit_timestamp": "2026-05-19T14:50:00+00:00",
            "exit_price": 11.0,
            "exit_reason": "target_hit",
            "pnl_dollars": 50.0,
        },
        # Older-style: entry_ts, qty_filled, pnl, entry_date.
        {
            "entry_date": "2026-05-19",
            "symbol": "BBB",
            "entry_ts": _dt.datetime(2026, 5, 19, 14, 35, 12, tzinfo=_dt.UTC),
            "entry_price": 7.0,
            "qty_filled": 50,
            "exit_ts": None,
            "exit_price": None,
            "exit_reason": "EOD",
            "pnl": -3.0,
        },
    ]
    trades = _normalize_lab_trades(rows)
    assert [t.symbol for t in trades] == ["AAA", "BBB"]
    assert trades[0].entry_ts_minute == _dt.datetime(2026, 5, 19, 14, 30, tzinfo=_dt.UTC)
    # Sub-minute timestamp is floored.
    assert trades[1].entry_ts_minute == _dt.datetime(2026, 5, 19, 14, 35, tzinfo=_dt.UTC)
    assert trades[1].qty_filled == 50
    assert trades[1].exit_reason == "eod"
    assert trades[1].pnl_dollars == -3.0


def test_normalize_lab_output_accepts_dataclass_with_trades_attribute() -> None:

    @dataclass
    class _LabResult:
        trades: list[dict] = field(default_factory=list)
        candidate_events: list[dict] = field(default_factory=list)

    res = _LabResult(
        trades=[{
            "session_date": "2026-05-19", "symbol": "AAA",
            "entry_timestamp": "2026-05-19T14:30:00+00:00",
            "entry_price": 10.0, "qty": 100,
            "exit_timestamp": "2026-05-19T14:45:00+00:00",
            "exit_price": 10.1, "exit_reason": "TARGET",
            "pnl_dollars": 10.0,
        }],
        candidate_events=[{
            "session_date": "2026-05-19", "symbol": "AAA",
            "scan_timestamp": "2026-05-19T14:30:00+00:00",
            "passed_gates": True,
        }],
    )
    trades, cands = normalize_lab_output(res)
    assert len(trades) == 1
    assert len(cands) == 1
    assert cands[0].gate_passed is True
    assert cands[0].gate_rejection_reason is None
