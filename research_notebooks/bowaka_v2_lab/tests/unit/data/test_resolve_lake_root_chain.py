"""Verify the resolver chain handles every input shape correctly.

The lake-root bug was caused by callsites bypassing this resolver and
getting ``None`` implicitly stringified to ``Path("None")``. The resolver
itself must be the single source of truth for lake-root resolution; this
test pins its behavior so any future regression is caught here, not in
production silent-fail mode.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

from bowaka_v2_lab.data.lineage import resolve_lake_root


def test_resolver_uses_market_data_shared_root_when_set(tmp_path):
    real = tmp_path / "lake"
    real.mkdir()
    cfg = {"market_data": {"shared_root": str(real)}}
    got = resolve_lake_root(cfg)
    assert got == real.resolve()


def test_resolver_falls_through_to_env_when_cfg_missing(tmp_path):
    real = tmp_path / "lake_env"
    real.mkdir()
    cfg = {"market_data": {}}
    with mock.patch.dict(os.environ, {"MARKET_DATA_ROOT": str(real)}):
        got = resolve_lake_root(cfg)
    assert got == real.resolve()


def test_resolver_falls_through_to_inrepo_default_when_nothing_set():
    cfg = {"market_data": {}}
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("MARKET_DATA_ROOT", None)
        got = resolve_lake_root(cfg)
    # The in-repo default exists at <repo>/research_notebooks/market_data.
    # We don't assert the exact path here (varies by checkout); we just
    # assert that the resolver returned SOMETHING and didn't pass None or
    # Path("None") downstream.
    assert got is not None
    assert isinstance(got, Path)
    assert str(got) != "None"
    assert got.name != "None"


def test_resolver_never_returns_path_none_when_cfg_is_explicit_none():
    """Regression for 2026-05-29: ``cfg.market_data.shared_root: null``
    must not stringify to ``Path('None')``."""
    cfg = {"market_data": {"shared_root": None}}
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("MARKET_DATA_ROOT", None)
        got = resolve_lake_root(cfg)
    assert got.name != "None"
    assert str(got) != "None"
