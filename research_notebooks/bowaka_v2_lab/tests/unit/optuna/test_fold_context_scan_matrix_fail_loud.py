"""The fold-context scan-matrix opener fails loud, not silent (speedup P1).

``_open_fold_scan_matrix_store(cfg, scope)`` is the helper the per-fold
context builder calls to open a built matrix. The whole point of the matrix
runtime is that an *enabled* study uses it; a silent fall-through to the slow
legacy scanner on a misconfigured store would waste days of a 5000-trial run.
So when the runtime is enabled and a store path is configured but cannot be
opened, the helper raises :class:`OptunaStudyInvalidError`.

It still returns ``None`` (legacy scanner, no raise) for the deliberate
cases: disabled runtime, ``runtime_mode: disabled``, no store configured, and
the holdout scope under ``separate_holdout_matrix`` (holdout isolation).
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from bowaka_v2_lab.optuna.fold_context import _open_fold_scan_matrix_store


def _cfg(scan_matrix: dict) -> dict:
    return {"optuna": {"acceleration": {"scan_matrix": scan_matrix}}}


def test_enabled_vectorized_but_store_missing_raises(tmp_path):
    missing = tmp_path / "never_built" / "scan_matrix"
    cfg = _cfg({
        "enabled": True,
        "runtime_mode": "vectorized",
        "store_root": str(missing),
    })
    with pytest.raises(OptunaStudyInvalidError) as exc:
        _open_fold_scan_matrix_store(cfg, "validation")
    # Actionable message: names the path tried, the scope, and the build cmd.
    msg = str(exc.value)
    assert "validation" in msg
    assert "scan-matrix build" in msg
    assert str(missing) in msg or "validation" in msg


def test_enabled_compatibility_but_store_missing_raises(tmp_path):
    missing = tmp_path / "never_built"
    cfg = _cfg({
        "enabled": True,
        "runtime_mode": "compatibility",
        "root": str(missing),
    })
    with pytest.raises(OptunaStudyInvalidError):
        _open_fold_scan_matrix_store(cfg, "validation")


def test_disabled_runtime_mode_returns_none_no_raise(tmp_path):
    # enabled flag set but runtime_mode disabled -> legacy path, never raises.
    cfg = _cfg({
        "enabled": True,
        "runtime_mode": "disabled",
        "store_root": str(tmp_path / "missing"),
    })
    assert _open_fold_scan_matrix_store(cfg, "validation") is None


def test_not_enabled_returns_none(tmp_path):
    cfg = _cfg({
        "enabled": False,
        "runtime_mode": "vectorized",
        "store_root": str(tmp_path / "missing"),
    })
    assert _open_fold_scan_matrix_store(cfg, "validation") is None


def test_enabled_but_unconfigured_returns_none():
    # Genuinely unconfigured (no path at all) keeps the legacy scanner even
    # when enabled+vectorized — this is the ONLY silent-None case for an
    # enabled runtime.
    cfg = _cfg({"enabled": True, "runtime_mode": "vectorized"})
    assert _open_fold_scan_matrix_store(cfg, "validation") is None


def test_holdout_scope_isolated_returns_none_even_if_configured(tmp_path):
    # separate_holdout_matrix (default True) — the holdout window is never
    # read from a matrix during tuning, so a configured-but-missing store
    # does NOT raise for the holdout scope.
    cfg = _cfg({
        "enabled": True,
        "runtime_mode": "vectorized",
        "separate_holdout_matrix": True,
        "store_root": str(tmp_path / "missing"),
    })
    assert _open_fold_scan_matrix_store(cfg, "holdout") is None


def test_holdout_scope_without_separation_resolves_and_raises(tmp_path):
    # If an operator explicitly disables separate_holdout_matrix, the holdout
    # scope is treated like any other and a broken store fails loud.
    cfg = _cfg({
        "enabled": True,
        "runtime_mode": "vectorized",
        "separate_holdout_matrix": False,
        "store_root": str(tmp_path / "missing"),
    })
    with pytest.raises(OptunaStudyInvalidError):
        _open_fold_scan_matrix_store(cfg, "holdout")


def test_opens_built_store_returns_store(tmp_path):
    # A present manifest -> the store opens and is returned (no raise, not None).
    import json

    store_root = tmp_path / "scan_matrix" / "validation"
    store_root.mkdir(parents=True)
    (store_root / "manifest.json").write_text(
        json.dumps({"matrix_id": "x", "matrix_version": 1, "sessions": []}),
        encoding="utf-8",
    )
    cfg = _cfg({
        "enabled": True,
        "runtime_mode": "vectorized",
        # base path; resolver appends /validation to match the built layout.
        "store_root": str(tmp_path / "scan_matrix"),
    })
    store = _open_fold_scan_matrix_store(cfg, "validation")
    assert store is not None
    assert store.root == store_root
