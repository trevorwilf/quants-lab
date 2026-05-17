"""Phase 7: live paper-log reconciliation against the legacy archive.

Skipped unless ``BOWAKA_PAPER_LOGS_ROOT`` is set. The env var must point to a
directory containing ``daily_summary.jsonl``, ``trade_ledger.jsonl``, and
``trades/``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from bowaka_lab.reconcile.paper_log_importer import load_daily_summary, load_trade_ledger
from bowaka_lab.reconcile.replay_comparator import detect_ledger_contamination


def _live_root() -> Path:
    root = os.environ.get("BOWAKA_PAPER_LOGS_ROOT")
    if not root:
        pytest.skip("BOWAKA_PAPER_LOGS_ROOT not set")
    return Path(root)


def test_live_imports_without_exception():
    root = _live_root()
    summary = load_daily_summary(root / "daily_summary.jsonl")
    assert summary.df.shape[0] > 0 or summary.errors.shape[0] > 0


def test_live_contamination_produces_non_empty_or_clean_table():
    root = _live_root()
    ledger_path = root / "trade_ledger.jsonl"
    if not ledger_path.exists():
        # Some archives put it under test/. Try the alternate path.
        ledger_path = root / "test" / "trade_ledger.jsonl"
    res = load_trade_ledger(ledger_path)
    # The function should at least produce a DataFrame (possibly empty).
    assert isinstance(res.df, pd.DataFrame)
    contam = detect_ledger_contamination(res.df)
    # Either at least one contamination row OR a clean ledger (both are valid).
    assert isinstance(contam, pd.DataFrame)
