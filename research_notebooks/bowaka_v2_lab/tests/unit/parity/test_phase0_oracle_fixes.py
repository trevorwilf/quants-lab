"""Phase 0 (parity oracle) — the oracle-repair fixes.

Covers:
  1. the lab trade dict carries ``entry_timestamp`` (and round-trips through the
     normalizer to a real, non-NaT join key);
  2. the normalizer FAILS LOUD on a missing/NaT entry timestamp instead of
     silently producing a NaT join key (which structurally zeroed
     ``trade_intersection_rate``);
  3. candidate metrics report NOT-MEASURED (``None``) — never a false ``1.0``
     PASS — when a side lacks candidate telemetry;
  4. ``n_sessions`` reports the requested XNYS count, with ``n_trade_sessions``
     kept separate.
"""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_v2_lab.parity.metrics import compute_parity_metrics
from bowaka_v2_lab.parity.normalizers import _normalize_lab_trades
from bowaka_v2_lab.parity.schemas import NormalizedCandidate, NormalizedTrade
from bowaka_v2_lab.sim.portfolio import Portfolio, Position


# --- Task 1: the trade schema carries entry_timestamp -----------------------
def test_record_close_emits_entry_timestamp_and_round_trips_without_nat() -> None:
    pf = Portfolio(initial_bankroll=100_000.0)
    entry_ts = "2026-05-19T14:30:00+00:00"
    pos = Position(
        symbol="AAA", entry_date=_dt.date(2026, 5, 19), entry_price=10.0,
        qty=100, stop_pct=0.02, target_pct=0.04, max_hold_days=1,
        entry_timestamp=entry_ts,
    )
    pf.open_positions[pos.position_id] = pos
    trade = pf.close_position_by_id(
        pos.position_id, exit_price=10.4, exit_reason="target",
        exit_date=_dt.date(2026, 5, 19),
    )
    # Task 1: present and non-null on a minute-path close.
    assert trade["entry_timestamp"] == entry_ts
    # End-to-end: the field round-trips to a real (non-NaT) minute join key.
    normd = _normalize_lab_trades([trade])
    assert len(normd) == 1
    assert normd[0].entry_ts_minute == _dt.datetime(2026, 5, 19, 14, 30, tzinfo=_dt.UTC)


# --- Task 2: the normalizer fails loud on a missing/NaT entry timestamp ------
def test_normalizer_raises_on_missing_entry_timestamp() -> None:
    # No entry_timestamp / entry_ts / scan_timestamp key at all.
    row = {"session_date": _dt.date(2026, 5, 19), "symbol": "AAA",
           "entry_price": 10.0, "qty": 100}
    with pytest.raises(ValueError, match="entry timestamp"):
        _normalize_lab_trades([row])


def test_normalizer_raises_on_none_entry_timestamp() -> None:
    row = {"session_date": "2026-05-19", "symbol": "AAA", "entry_timestamp": None,
           "entry_price": 10.0, "qty": 100}
    with pytest.raises(ValueError, match="entry timestamp"):
        _normalize_lab_trades([row])


# --- helpers for the metric tasks -------------------------------------------
def _trade(sym: str, minute: int) -> NormalizedTrade:
    return NormalizedTrade(
        session_date=_dt.date(2026, 5, 19), symbol=sym,
        entry_ts_minute=_dt.datetime(2026, 5, 19, 14, minute, tzinfo=_dt.UTC),
        entry_price=10.0, qty_filled=100,
        exit_ts_minute=_dt.datetime(2026, 5, 19, 15, minute, tzinfo=_dt.UTC),
        exit_price=10.5, exit_reason="target", pnl_dollars=5.0,
    )


def _cand(sym: str, minute: int) -> NormalizedCandidate:
    return NormalizedCandidate(
        session_date=_dt.date(2026, 5, 19), symbol=sym,
        candidate_ts_minute=_dt.datetime(2026, 5, 19, 14, minute, tzinfo=_dt.UTC),
        gate_passed=True, gate_rejection_reason=None,
    )


# --- Task 3: candidate metrics NOT-MEASURED when a side lacks telemetry ------
def test_candidate_metrics_not_measured_when_prod_candidates_absent() -> None:
    t = _trade("AAA", 30)
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=1, prod_trades=[t], prod_candidates=[],   # prod: NO telemetry
        lab_trades=[t], lab_candidates=[_cand("AAA", 30)],       # lab: present
    )
    # NOT a false degenerate 1.0 PASS — reported as N/A.
    assert report.candidate_recall is None
    assert report.gate_match_rate is None
    # Excluded from the verdict (neither pass nor fail).
    assert "candidate_recall" not in report.failing_metrics
    assert "gate_match_rate" not in report.failing_metrics
    # The measured metrics still drive the (here passing) verdict.
    assert report.passes_audit_thresholds is True


def test_candidate_metrics_measured_when_both_sides_present() -> None:
    t = _trade("AAA", 30)
    c = _cand("AAA", 30)
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=1, prod_trades=[t], prod_candidates=[c],
        lab_trades=[t], lab_candidates=[c],
    )
    assert report.candidate_recall == 1.0
    assert report.gate_match_rate == 1.0


# --- Task 4: n_sessions == requested XNYS count, n_trade_sessions separate ---
def test_n_sessions_reports_requested_count_not_trade_bearing() -> None:
    sessions = [_dt.date(2026, 5, d) for d in (19, 20, 21, 22, 26)]  # 5 requested
    t = _trade("AAA", 30)  # trades only on 2026-05-19
    report = compute_parity_metrics(
        window_start=sessions[0], window_end=sessions[-1],
        universe_size=1, prod_trades=[t], prod_candidates=[],
        lab_trades=[t], lab_candidates=[], requested_sessions=sessions,
    )
    assert report.n_sessions == 5          # requested XNYS count
    assert report.n_trade_sessions == 1    # only one trade-bearing session


def test_n_sessions_falls_back_to_trade_bearing_when_not_threaded() -> None:
    t = _trade("AAA", 30)
    report = compute_parity_metrics(
        window_start=_dt.date(2026, 5, 19), window_end=_dt.date(2026, 5, 19),
        universe_size=1, prod_trades=[t], prod_candidates=[],
        lab_trades=[t], lab_candidates=[],
    )
    assert report.n_sessions == 1
    assert report.n_trade_sessions == 1
