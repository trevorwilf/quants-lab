"""Holdout sessions of the matrix cannot be opened under purpose='objective'.

Matrix doc §17.2 — the matrix store must isolate the holdout window from
the optimization loop. ``ScanMatrixStore.assert_can_read(session_date,
purpose='objective')`` raises ``HoldoutMatrixReadError`` for a session
inside the holdout window; ``purpose='final_holdout'`` passes.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from bowaka_v2_lab.scanner.scan_matrix import (
    HoldoutMatrixReadError,
    ScanMatrixStore,
)


def _make_store_root(tmp_path: Path) -> Path:
    root = tmp_path / "matrix"
    root.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps({"matrix_id": "x", "matrix_version": 1, "sessions": []}),
        encoding="utf-8",
    )
    return root


def test_assert_can_read_blocks_holdout_under_objective_purpose(tmp_path):
    holdout = (dt.date(2024, 11, 1), dt.date(2025, 1, 1))
    store = ScanMatrixStore(
        _make_store_root(tmp_path), holdout_window=holdout,
    )
    with pytest.raises(HoldoutMatrixReadError):
        store.assert_can_read(dt.date(2024, 11, 15), purpose="objective")


def test_assert_can_read_allows_validation_session_under_objective(tmp_path):
    holdout = (dt.date(2024, 11, 1), dt.date(2025, 1, 1))
    store = ScanMatrixStore(
        _make_store_root(tmp_path), holdout_window=holdout,
    )
    # 2024-09-15 is well before the holdout window; objective open OK.
    store.assert_can_read(dt.date(2024, 9, 15), purpose="objective")


def test_assert_can_read_allows_holdout_under_final_holdout_purpose(tmp_path):
    holdout = (dt.date(2024, 11, 1), dt.date(2025, 1, 1))
    store = ScanMatrixStore(
        _make_store_root(tmp_path), holdout_window=holdout,
    )
    store.assert_can_read(dt.date(2024, 11, 15), purpose="final_holdout")


def test_no_holdout_configured_is_a_noop(tmp_path):
    """Without a holdout window the guard never fires."""
    store = ScanMatrixStore(
        _make_store_root(tmp_path), holdout_window=None,
    )
    store.assert_can_read(dt.date(2024, 11, 15), purpose="objective")


def test_unknown_purpose_treated_as_objective(tmp_path):
    """Any unrecognised purpose fails closed (treated as objective)."""
    holdout = (dt.date(2024, 11, 1), dt.date(2025, 1, 1))
    store = ScanMatrixStore(
        _make_store_root(tmp_path), holdout_window=holdout,
    )
    with pytest.raises(HoldoutMatrixReadError):
        store.assert_can_read(dt.date(2024, 11, 15), purpose="something_else")
