"""Reconcile against real paper logs at BOWAKA_V2_PAPER_LOGS_ROOT.

Runs only when the env var is set; otherwise skipped.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from bowaka_v2_lab.reconcile.importer import import_paper_logs


@pytest.mark.live_paper
def test_paper_logs_root_importable() -> None:
    root = os.environ.get("BOWAKA_V2_PAPER_LOGS_ROOT")
    if not root:
        pytest.skip("BOWAKA_V2_PAPER_LOGS_ROOT not set")
    p = Path(root)
    if not p.is_dir():
        pytest.skip(f"BOWAKA_V2_PAPER_LOGS_ROOT={p} is not a directory")
    imp = import_paper_logs(p)
    # If any of the four log kinds is empty, skip rather than fail — fixture shape varies.
    if not (imp.candidates or imp.decisions or imp.orders or imp.fills):
        pytest.skip("no candidate/decision/order/fill records in paper logs")
    # All timestamps normalised.
    import pandas as pd
    for c in imp.candidates:
        if c.get("scan_timestamp"):
            assert pd.Timestamp(c["scan_timestamp"]).tzinfo is not None
