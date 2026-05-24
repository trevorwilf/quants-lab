"""Optuna storage-URI resolution against the lab root (audit 2026-05-23 §P1-006).

Pre-remediation ``optuna.storage: sqlite:///research_notebooks/bowaka_v2_lab/artifacts/optuna/local.db``
was CWD-sensitive: launching from the lab directory made the relative path
resolve to ``research_notebooks/bowaka_v2_lab/research_notebooks/bowaka_v2_lab/``.
:func:`resolve_storage_uri` repoints relative SQLite URIs at an absolute path
under ``paths.lab_root`` and creates the parent directory.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.optuna.storage_path import resolve_storage_uri


def _paths(lab_root: Path) -> BowakaV2Paths:
    return BowakaV2Paths(
        lab_root=lab_root,
        data_root=lab_root / "data",
        artifact_root=lab_root / "artifacts",
        config_path=lab_root / "configs" / "irrelevant.yml",
    )


def test_resolves_relative_sqlite_path_from_lab_root(tmp_path, monkeypatch):
    """A relative SQLite URI lands under the lab root regardless of CWD."""
    lab = tmp_path / "research_notebooks" / "bowaka_v2_lab"
    lab.mkdir(parents=True)
    monkeypatch.chdir(lab)
    uri = resolve_storage_uri(
        "sqlite:///artifacts/optuna/local.db", paths=_paths(lab),
    )
    assert uri.startswith("sqlite:////"), f"expected absolute uri, got {uri!r}"
    assert (lab / "artifacts" / "optuna").is_dir()
    # The resolved path is under the lab root, not the CWD.
    assert str(lab).replace("\\", "/") in uri


def test_resolves_relative_sqlite_path_from_repo_root(tmp_path, monkeypatch):
    """Launching from the repo root resolves to the same absolute path under lab."""
    repo = tmp_path
    lab = repo / "research_notebooks" / "bowaka_v2_lab"
    lab.mkdir(parents=True)
    monkeypatch.chdir(repo)
    uri = resolve_storage_uri(
        "sqlite:///artifacts/optuna/local.db", paths=_paths(lab),
    )
    assert uri.startswith("sqlite:////")
    assert str(lab).replace("\\", "/") in uri


def test_resolves_relative_path_that_includes_lab_root_prefix(tmp_path, monkeypatch):
    """A relative URI that already prefixes ``research_notebooks/bowaka_v2_lab/``
    should NOT double up — the legacy path syntax is honored as
    relative-to-lab-root."""
    repo = tmp_path
    lab = repo / "research_notebooks" / "bowaka_v2_lab"
    lab.mkdir(parents=True)
    monkeypatch.chdir(lab)
    uri = resolve_storage_uri(
        "sqlite:///research_notebooks/bowaka_v2_lab/artifacts/optuna/local.db",
        paths=_paths(lab),
    )
    assert uri.startswith("sqlite:////")
    # The double-prefix bug would surface as ``.../bowaka_v2_lab/research_notebooks/bowaka_v2_lab/...``.
    expected_dir = (lab / "artifacts" / "optuna").as_posix()
    assert expected_dir in uri, f"expected {expected_dir} in {uri}"
    assert "research_notebooks/bowaka_v2_lab/research_notebooks" not in uri


def test_pg_uri_passthrough(tmp_path):
    """PostgreSQL URIs are returned unchanged (no path manipulation)."""
    uri = resolve_storage_uri(
        "postgresql+psycopg://u:p@h:5432/d", paths=_paths(tmp_path),
    )
    assert uri == "postgresql+psycopg://u:p@h:5432/d"


def test_creates_parent_dir(tmp_path):
    """The SQLite parent directory is created if absent."""
    lab = tmp_path / "lab"
    lab.mkdir()
    target = lab / "artifacts" / "optuna"
    assert not target.exists()
    resolve_storage_uri(
        "sqlite:///artifacts/optuna/local.db", paths=_paths(lab),
    )
    assert target.is_dir()


def test_absolute_sqlite_uri_passthrough(tmp_path):
    """An already-absolute SQLite URI is returned unchanged."""
    abs_uri = f"sqlite:////{tmp_path.as_posix()}/db.sqlite"
    out = resolve_storage_uri(abs_uri, paths=_paths(tmp_path))
    assert out == abs_uri


def test_unsupported_scheme_raises(tmp_path):
    """A URI with an unrecognised scheme is rejected."""
    with pytest.raises(ValueError, match="unsupported optuna storage URI"):
        resolve_storage_uri("mysql://u@h/d", paths=_paths(tmp_path))
