"""Schema constructor + invariants."""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_v2_lab.parity.schemas import (
    NormalizedCandidate,
    NormalizedTrade,
    ParityReport,
)


_SD = _dt.date(2026, 5, 19)
_TS = _dt.datetime(2026, 5, 19, 14, 30, tzinfo=_dt.UTC)


def test_normalized_trade_constructs_and_exposes_join_key() -> None:
    t = NormalizedTrade(
        session_date=_SD, symbol="AAA", entry_ts_minute=_TS,
        entry_price=10.0, qty_filled=100,
        exit_ts_minute=_TS + _dt.timedelta(minutes=30),
        exit_price=10.5, exit_reason="target",
        pnl_dollars=50.0,
    )
    assert t.join_key == (_SD, "AAA", _TS)
    assert t.side == "long"


def test_normalized_trade_rejects_non_long_side() -> None:
    with pytest.raises(ValueError, match="long-only"):
        NormalizedTrade(
            session_date=_SD, symbol="AAA", entry_ts_minute=_TS,
            entry_price=10.0, qty_filled=100,
            exit_ts_minute=None, exit_price=None, exit_reason=None,
            pnl_dollars=0.0, side="short",
        )


def test_normalized_candidate_join_key_uses_candidate_ts() -> None:
    c = NormalizedCandidate(
        session_date=_SD, symbol="BBB", candidate_ts_minute=_TS,
        gate_passed=False, gate_rejection_reason="price_gate",
    )
    assert c.join_key == (_SD, "BBB", _TS)


def test_parity_report_defaults_are_falsy() -> None:
    r = ParityReport(
        window_start=_SD, window_end=_SD, universe_size=5, n_sessions=1,
        n_trade_sessions=1,
        prod_n_candidates=0, prod_n_trades=0, prod_gross_pnl=0.0,
        lab_n_candidates=0, lab_n_trades=0, lab_gross_pnl=0.0,
        candidate_recall=1.0, gate_match_rate=1.0,
        trade_intersection_rate=1.0, fill_price_mae_bps=0.0,
        exit_reason_match_rate=1.0, daily_pnl_sign_match_rate=1.0,
    )
    assert r.passes_audit_thresholds is False
    assert r.failing_metrics == []
    assert r.prod_only_trades == []
    assert r.lab_only_trades == []
