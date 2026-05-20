"""Ingest bundled minimal fixture; normalised timestamps tz-aware."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.reconcile.importer import import_paper_logs


_FIX = Path(__file__).resolve().parents[1] / "fixtures" / "paper_logs_minimal"


def test_import_minimal_fixture() -> None:
    r = import_paper_logs(_FIX)
    assert len(r.candidates) == 4
    assert len(r.decisions) == 3
    assert len(r.orders) == 2
    assert len(r.fills) == 2
    # State.json loaded.
    assert r.state.get("schema_version") == 1


def test_timestamps_normalised_to_utc() -> None:
    r = import_paper_logs(_FIX)
    for c in r.candidates:
        ts = pd.Timestamp(c["scan_timestamp"])
        assert ts.tzinfo is not None
    for d in r.decisions:
        ts = pd.Timestamp(d["decision_timestamp"])
        assert ts.tzinfo is not None


def test_drift_issues_empty_on_clean_fixture() -> None:
    r = import_paper_logs(_FIX)
    assert r.drift_issues == [], r.drift_issues
