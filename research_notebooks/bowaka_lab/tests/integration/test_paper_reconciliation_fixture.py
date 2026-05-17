"""Phase 7: full reconciliation pipeline on minimal fixture."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from bowaka_lab.reconcile.paper_log_importer import load_daily_summary, load_trade_ledger
from bowaka_lab.reconcile.replay_comparator import detect_ledger_contamination, reconcile


def _build_paper_trades_from_summary(summary_df: pd.DataFrame) -> pd.DataFrame:
    closed = summary_df[summary_df["record_type"] == "closed"].copy()
    if closed.empty:
        return closed
    closed = closed.rename(columns={"ticker": "symbol", "link_id": "trade_id", "entry_timestamp": "entry_time", "exit_timestamp": "exit_time"})
    closed["session_date"] = closed["entry_time"].dt.date
    return closed


def test_full_pipeline_on_minimal_fixture(fixtures_dir: Path):
    root = fixtures_dir / "paper_trade_logs_minimal"
    summary = load_daily_summary(root / "daily_summary.jsonl").df
    ledger = load_trade_ledger(root / "trade_ledger.jsonl").df

    paper_trades = _build_paper_trades_from_summary(summary)
    # Backtest trades that match AAA target, BBB stop, DDD time_stop but NOT CCC (which had
    # the implementation-mismatch signal_fade rejection in paper).
    bt_trades = pd.DataFrame(
        [
            {"symbol": "AAA", "session_date": date(2026, 5, 11), "entry_time": pd.Timestamp("2026-05-11T13:45:00", tz="UTC"), "entry_price": 5.00, "exit_reason": "target_hit"},
            {"symbol": "BBB", "session_date": date(2026, 5, 11), "entry_time": pd.Timestamp("2026-05-11T13:45:00", tz="UTC"), "entry_price": 10.00, "exit_reason": "stop_hit"},
            {"symbol": "CCC", "session_date": date(2026, 5, 11), "entry_time": pd.Timestamp("2026-05-11T13:45:00", tz="UTC"), "entry_price": 4.00, "exit_reason": "hold"},
            {"symbol": "DDD", "session_date": date(2026, 5, 11), "entry_time": pd.Timestamp("2026-05-11T13:45:00", tz="UTC"), "entry_price": 8.00, "exit_reason": "time_stop"},
        ]
    )

    out = reconcile(paper_trades=paper_trades, backtest_trades=bt_trades)
    classifications = set(out["classification"].tolist())
    assert "candidate_match" in classifications
    assert "implementation_mismatch" in classifications  # CCC


def test_contamination_detected_in_minimal_ledger(fixtures_dir: Path):
    root = fixtures_dir / "paper_trade_logs_minimal"
    ledger = load_trade_ledger(root / "trade_ledger.jsonl").df
    flagged = detect_ledger_contamination(ledger, production_account="PA123456")
    flagged_trade_ids = set(flagged["trade_id"].tolist())
    assert any("TEST" in t for t in flagged_trade_ids) or any("SANITY" in t for t in flagged_trade_ids)
