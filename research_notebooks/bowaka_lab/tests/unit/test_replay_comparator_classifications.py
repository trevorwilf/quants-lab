"""Phase 7: each reconciliation classification triggers correctly."""

from __future__ import annotations

from datetime import date

import pandas as pd

from bowaka_lab.reconcile.replay_comparator import reconcile


def _trade_row(*, symbol: str, session_date: date, entry_price: float, exit_reason: str, entry_time: str | None = None):
    return {
        "symbol": symbol,
        "session_date": session_date,
        "entry_time": pd.Timestamp(entry_time or f"{session_date}T13:45:00", tz="UTC"),
        "entry_price": entry_price,
        "exit_reason": exit_reason,
    }


def test_candidate_match_when_both_entered_same_outcome():
    paper = pd.DataFrame([_trade_row(symbol="AAA", session_date=date(2026, 5, 11), entry_price=5.01, exit_reason="target_hit")])
    bt = pd.DataFrame([_trade_row(symbol="AAA", session_date=date(2026, 5, 11), entry_price=5.00, exit_reason="target_hit")])
    out = reconcile(paper_trades=paper, backtest_trades=bt)
    row = out.iloc[0]
    assert row["classification"] == "candidate_match"


def test_candidate_missing_in_backtest_when_only_paper_entered():
    paper = pd.DataFrame([_trade_row(symbol="AAA", session_date=date(2026, 5, 11), entry_price=5.01, exit_reason="target_hit")])
    bt = pd.DataFrame(columns=["symbol", "session_date", "entry_time", "entry_price", "exit_reason"])
    out = reconcile(paper_trades=paper, backtest_trades=bt)
    assert out.iloc[0]["classification"] == "candidate_missing_in_backtest"


def test_fill_model_mismatch_when_entry_prices_diverge():
    paper = pd.DataFrame([_trade_row(symbol="AAA", session_date=date(2026, 5, 11), entry_price=5.50, exit_reason="target_hit")])
    bt = pd.DataFrame([_trade_row(symbol="AAA", session_date=date(2026, 5, 11), entry_price=5.00, exit_reason="target_hit")])
    out = reconcile(paper_trades=paper, backtest_trades=bt)
    assert out.iloc[0]["classification"] == "fill_model_mismatch"


def test_implementation_mismatch_for_signal_fade_rejection():
    paper = pd.DataFrame([_trade_row(symbol="CCC", session_date=date(2026, 5, 11), entry_price=4.00, exit_reason="signal_fade_order_rejected")])
    bt = pd.DataFrame([_trade_row(symbol="CCC", session_date=date(2026, 5, 11), entry_price=4.00, exit_reason="hold")])
    out = reconcile(paper_trades=paper, backtest_trades=bt)
    assert out.iloc[0]["classification"] == "implementation_mismatch"


def test_exit_rule_mismatch_when_exit_reasons_differ_non_rejection():
    paper = pd.DataFrame([_trade_row(symbol="AAA", session_date=date(2026, 5, 11), entry_price=5.0, exit_reason="time_stop")])
    bt = pd.DataFrame([_trade_row(symbol="AAA", session_date=date(2026, 5, 11), entry_price=5.0, exit_reason="target_hit")])
    out = reconcile(paper_trades=paper, backtest_trades=bt)
    assert out.iloc[0]["classification"] == "exit_rule_mismatch"


def test_entry_timing_mismatch_when_entry_times_far_apart():
    paper = pd.DataFrame([_trade_row(symbol="AAA", session_date=date(2026, 5, 11), entry_price=5.0, exit_reason="target_hit", entry_time="2026-05-11T14:30:00")])
    bt = pd.DataFrame([_trade_row(symbol="AAA", session_date=date(2026, 5, 11), entry_price=5.0, exit_reason="target_hit", entry_time="2026-05-11T13:45:00")])
    out = reconcile(paper_trades=paper, backtest_trades=bt)
    assert out.iloc[0]["classification"] == "entry_timing_mismatch"


def test_broker_rejection_mismatch():
    paper = pd.DataFrame([_trade_row(symbol="DDD", session_date=date(2026, 5, 11), entry_price=8.0, exit_reason="broker_rejected_after_hours")])
    bt = pd.DataFrame([_trade_row(symbol="DDD", session_date=date(2026, 5, 11), entry_price=8.0, exit_reason="time_stop")])
    out = reconcile(paper_trades=paper, backtest_trades=bt)
    assert out.iloc[0]["classification"] == "broker_rejection_mismatch"
