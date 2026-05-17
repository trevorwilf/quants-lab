"""Compare paper-trading events to backtest replay results.

Produces one row per (session_date, symbol, paper_trade_id) carrying both the
paper-side and backtest-side trade snapshots plus a classification label per
``[Report §15.4]``:

  candidate_match
  candidate_missing_in_backtest
  data_feed_mismatch
  entry_timing_mismatch
  fill_model_mismatch
  exit_rule_mismatch
  implementation_mismatch
  broker_rejection_mismatch
  paper_log_corruption
  test_ledger_contamination
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

import pandas as pd

VALID_CLASSIFICATIONS: tuple[str, ...] = (
    "candidate_match",
    "candidate_missing_in_backtest",
    "data_feed_mismatch",
    "entry_timing_mismatch",
    "fill_model_mismatch",
    "exit_rule_mismatch",
    "implementation_mismatch",
    "broker_rejection_mismatch",
    "paper_log_corruption",
    "test_ledger_contamination",
)

_KNOWN_TEST_SYMBOLS = {"AAPL_TEST", "CAT_TEST", "T0", "T1", "T2", "T3", "T4", "Y"}
_TEST_LIKE_RE = re.compile(r"TEST|SANITY|DRYRUN|FAKE", re.IGNORECASE)


def _is_contaminated(row: dict, *, production_account: str | None) -> bool:
    """Heuristics from ``[Report §E.3]`` and Phase 7 spec."""
    tid = str(row.get("trade_id") or row.get("link_id") or "")
    if _TEST_LIKE_RE.search(tid):
        return True
    if row.get("mode") == "test":
        return True
    if production_account is not None and row.get("account_id") not in (None, production_account):
        return True
    sym = str(row.get("ticker") or row.get("symbol") or "")
    if sym in _KNOWN_TEST_SYMBOLS:
        return True
    return False


def detect_ledger_contamination(ledger_df: pd.DataFrame, *, production_account: str | None = None) -> pd.DataFrame:
    """Return contaminated rows with a ``contamination_reason`` column."""
    if ledger_df.empty:
        return ledger_df.assign(contamination_reason=pd.Series([], dtype=str))
    flagged_rows = []
    for _, row in ledger_df.iterrows():
        r = row.to_dict()
        if _is_contaminated(r, production_account=production_account):
            reasons = []
            tid = str(r.get("trade_id") or r.get("link_id") or "")
            if _TEST_LIKE_RE.search(tid):
                reasons.append("trade_id_test_pattern")
            if r.get("mode") == "test":
                reasons.append("mode_test")
            if production_account is not None and r.get("account_id") not in (None, production_account):
                reasons.append("account_id_mismatch")
            sym = str(r.get("ticker") or r.get("symbol") or "")
            if sym in _KNOWN_TEST_SYMBOLS:
                reasons.append("symbol_in_known_test_set")
            r["contamination_reason"] = ",".join(reasons) or "unknown"
            flagged_rows.append(r)
    return pd.DataFrame(flagged_rows)


@dataclass
class ReconciliationRecord:
    session_date: date
    symbol: str
    paper_trade_id: str | None
    paper_candidate_rank: int | None
    backtest_candidate_rank: int | None
    candidate_match: bool
    paper_entered: bool
    backtest_entered: bool
    paper_entry_time: pd.Timestamp | None
    backtest_entry_time: pd.Timestamp | None
    paper_entry_price: float | None
    backtest_entry_price: float | None
    entry_price_diff_pct: float | None
    paper_exit_reason: str | None
    backtest_exit_reason: str | None
    classification: str
    notes: str = ""


def reconcile(
    *,
    paper_trades: pd.DataFrame,
    backtest_trades: pd.DataFrame,
    paper_candidates: dict[date, pd.DataFrame] | None = None,
    production_account: str | None = None,
) -> pd.DataFrame:
    """Compare paper vs backtest trades per (session_date, symbol).

    Both dataframes should have columns: ``symbol``, ``trade_date`` /
    ``session_date``, ``entry_time``, ``entry_price``, ``exit_reason``.
    Paper trades additionally carry ``trade_id`` (link_id) and optionally
    ``account_id`` and ``mode``.
    """
    records: list[ReconciliationRecord] = []

    if paper_trades.empty and backtest_trades.empty:
        return pd.DataFrame()

    paper = paper_trades.copy()
    if "session_date" not in paper.columns and "trade_date" in paper.columns:
        paper["session_date"] = paper["trade_date"]
    bt = backtest_trades.copy()
    if "session_date" not in bt.columns and "trade_date" in bt.columns:
        bt["session_date"] = bt["trade_date"]

    paper_index = paper.set_index(["session_date", "symbol"]).sort_index() if not paper.empty else pd.DataFrame().set_index([[], []])
    bt_index = bt.set_index(["session_date", "symbol"]).sort_index() if not bt.empty else pd.DataFrame().set_index([[], []])

    all_keys = set()
    if not paper.empty:
        all_keys.update(zip(paper["session_date"], paper["symbol"]))
    if not bt.empty:
        all_keys.update(zip(bt["session_date"], bt["symbol"]))

    for session_date, symbol in sorted(all_keys, key=lambda x: (str(x[0]), x[1])):
        p_rows = paper_index.loc[[(session_date, symbol)]] if (session_date, symbol) in paper_index.index else pd.DataFrame()
        b_rows = bt_index.loc[[(session_date, symbol)]] if (session_date, symbol) in bt_index.index else pd.DataFrame()
        p_row = p_rows.iloc[0].to_dict() if not p_rows.empty else {}
        b_row = b_rows.iloc[0].to_dict() if not b_rows.empty else {}

        if p_row and _is_contaminated(p_row, production_account=production_account):
            records.append(
                ReconciliationRecord(
                    session_date=session_date,
                    symbol=symbol,
                    paper_trade_id=str(p_row.get("trade_id") or p_row.get("link_id") or ""),
                    paper_candidate_rank=None,
                    backtest_candidate_rank=None,
                    candidate_match=False,
                    paper_entered=True,
                    backtest_entered=bool(b_row),
                    paper_entry_time=p_row.get("entry_time"),
                    backtest_entry_time=b_row.get("entry_time") if b_row else None,
                    paper_entry_price=p_row.get("entry_price"),
                    backtest_entry_price=b_row.get("entry_price") if b_row else None,
                    entry_price_diff_pct=None,
                    paper_exit_reason=p_row.get("exit_reason"),
                    backtest_exit_reason=b_row.get("exit_reason") if b_row else None,
                    classification="test_ledger_contamination",
                    notes="Paper trade row matches contamination heuristics; excluded from performance.",
                )
            )
            continue

        paper_entered = bool(p_row)
        bt_entered = bool(b_row)

        paper_exit_reason = p_row.get("exit_reason") if paper_entered else None
        bt_exit_reason = b_row.get("exit_reason") if bt_entered else None
        paper_entry_time = p_row.get("entry_time") if paper_entered else None
        bt_entry_time = b_row.get("entry_time") if bt_entered else None
        paper_entry_price = p_row.get("entry_price") if paper_entered else None
        bt_entry_price = b_row.get("entry_price") if bt_entered else None

        if not paper_entered:
            classification = "candidate_missing_in_backtest" if bt_entered else "candidate_match"
            notes = "Backtest entered but paper did not." if bt_entered else "Neither entered."
        elif not bt_entered:
            classification = "candidate_missing_in_backtest"
            notes = "Paper entered but backtest did not."
        else:
            if paper_exit_reason and bt_exit_reason and paper_exit_reason != bt_exit_reason:
                paper_lower = str(paper_exit_reason).lower()
                # signal_fade-related rejections are documented implementation bugs
                # (e.g. after-close OPG behavior), so they precede the generic
                # broker-rejection bucket.
                if "signal_fade" in paper_lower:
                    classification = "implementation_mismatch"
                    notes = "Paper logged signal-fade exit; backtest model did not."
                elif "rejected" in paper_lower or "broker" in paper_lower:
                    classification = "broker_rejection_mismatch"
                    notes = f"Paper exit_reason={paper_exit_reason} vs backtest={bt_exit_reason}"
                else:
                    classification = "exit_rule_mismatch"
                    notes = f"Paper exit_reason={paper_exit_reason} vs backtest={bt_exit_reason}"
            elif paper_entry_price and bt_entry_price and bt_entry_price != 0:
                diff = float(paper_entry_price) / float(bt_entry_price) - 1.0
                if abs(diff) > 0.02:
                    classification = "fill_model_mismatch"
                    notes = f"Entry price diff {diff:.3f}"
                elif paper_entry_time and bt_entry_time and abs((pd.Timestamp(paper_entry_time) - pd.Timestamp(bt_entry_time)).total_seconds()) > 600:
                    classification = "entry_timing_mismatch"
                    notes = "Entry-time delta > 10 min"
                else:
                    classification = "candidate_match"
                    notes = ""
            else:
                classification = "candidate_match"
                notes = ""

        diff = None
        if paper_entry_price and bt_entry_price and bt_entry_price != 0:
            diff = float(paper_entry_price) / float(bt_entry_price) - 1.0

        records.append(
            ReconciliationRecord(
                session_date=session_date,
                symbol=symbol,
                paper_trade_id=str(p_row.get("trade_id") or p_row.get("link_id") or "") if p_row else None,
                paper_candidate_rank=p_row.get("rank") if p_row else None,
                backtest_candidate_rank=b_row.get("prefilter_rank") if b_row else None,
                candidate_match=paper_entered == bt_entered,
                paper_entered=paper_entered,
                backtest_entered=bt_entered,
                paper_entry_time=paper_entry_time,
                backtest_entry_time=bt_entry_time,
                paper_entry_price=paper_entry_price,
                backtest_entry_price=bt_entry_price,
                entry_price_diff_pct=diff,
                paper_exit_reason=paper_exit_reason,
                backtest_exit_reason=bt_exit_reason,
                classification=classification,
                notes=notes,
            )
        )
    return pd.DataFrame([r.__dict__ for r in records])
