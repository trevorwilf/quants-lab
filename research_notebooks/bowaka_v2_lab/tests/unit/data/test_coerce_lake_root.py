"""Defensive boundary checks on lake_root values.

The 2026-05-29 diagnostic identified that ``md.get("shared_root")``
returning ``None`` was being passed downstream as ``Path("None")``,
producing silent zero-output failures. :func:`_coerce_lake_root` is the
boundary guard that converts those silent failures into loud
:class:`RuntimeError` raises.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_v2_lab.data.lineage import _coerce_lake_root


def test_none_raises():
    with pytest.raises(RuntimeError, match="None"):
        _coerce_lake_root(None)


def test_path_none_raises():
    with pytest.raises(RuntimeError, match="None"):
        _coerce_lake_root(Path("None"))


def test_string_none_raises():
    with pytest.raises(RuntimeError, match="None"):
        _coerce_lake_root("None")


def test_empty_string_raises():
    with pytest.raises(RuntimeError):
        _coerce_lake_root("")


def test_valid_string_returns_path(tmp_path):
    real = tmp_path / "lake"
    real.mkdir()
    got = _coerce_lake_root(str(real))
    assert got == real.resolve()


def test_valid_path_returns_path(tmp_path):
    real = tmp_path / "lake"
    real.mkdir()
    got = _coerce_lake_root(real)
    assert got == real.resolve()
