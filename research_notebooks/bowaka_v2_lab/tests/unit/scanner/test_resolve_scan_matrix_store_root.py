"""Store-root resolution for the scan-matrix runtime (walk-forward speedup P1).

``resolve_scan_matrix_store_root(sm_cfg, scope)`` is the single resolver the
fold-context builder uses to find a built matrix. It must:

* prefer ``store_root`` over the back-compat ``root`` key the committed
  configs write;
* append the ``scope`` segment unless the configured path already names it,
  so ``root: .../scan_matrix`` (base) and ``store_root: .../scan_matrix/
  validation`` (suffixed) resolve to the same built location;
* resolve a repo-relative path to an absolute one against the repo root;
* return ``None`` only when no path is configured at all.

The pre-fix code read ``sm_cfg.get("store_root")`` verbatim, so the committed
``root:`` key resolved to ``None`` and a multi-hour build was silently
ignored. These tests pin the corrected behaviour.

Note on absoluteness: tests use ``tmp_path`` (a genuinely-absolute,
platform-correct directory) for the "absolute path passed through" cases —
a POSIX-style ``/abs/...`` literal is NOT absolute on Windows (no drive), so
hard-coding it would make the resolver anchor it to the repo-root drive.
"""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.scanner.scan_matrix import resolve_scan_matrix_store_root

#: Repo root — the resolver anchors repo-relative paths here (parents[5] of
#: scan_matrix.py == .../quants-lab).
_REPO_ROOT = Path(__file__).resolve().parents[5]


def test_store_root_used_verbatim_when_already_scoped(tmp_path):
    base = tmp_path / "cache" / "scan_matrix" / "validation"
    out = resolve_scan_matrix_store_root({"store_root": str(base)}, "validation")
    # Already ends with the scope segment → no double-append, used verbatim.
    assert out == base


def test_store_root_gets_scope_suffix_when_absent(tmp_path):
    base = tmp_path / "cache" / "scan_matrix"
    out = resolve_scan_matrix_store_root({"store_root": str(base)}, "validation")
    assert out == base / "validation"


def test_root_fallback_used_with_scope_suffix(tmp_path):
    # Only the back-compat ``root`` key present (as the committed configs write).
    base = tmp_path / "cache" / "scan_matrix"
    out = resolve_scan_matrix_store_root({"root": str(base)}, "validation")
    assert out == base / "validation"


def test_store_root_preferred_over_root(tmp_path):
    preferred = tmp_path / "preferred" / "scan_matrix"
    legacy = tmp_path / "legacy" / "scan_matrix"
    out = resolve_scan_matrix_store_root(
        {"store_root": str(preferred), "root": str(legacy)}, "validation",
    )
    assert out == preferred / "validation"


def test_neither_key_returns_none():
    assert resolve_scan_matrix_store_root({}, "validation") is None
    assert resolve_scan_matrix_store_root({"enabled": True}, "validation") is None
    # Empty-string values are treated as unconfigured.
    assert resolve_scan_matrix_store_root({"root": ""}, "validation") is None


def test_repo_relative_path_resolved_absolute():
    sm_cfg = {"root": "research_notebooks/bowaka_v2_lab/artifacts/cache/scan_matrix"}
    out = resolve_scan_matrix_store_root(sm_cfg, "validation")
    assert out is not None
    assert out.is_absolute()
    assert out == (
        _REPO_ROOT
        / "research_notebooks/bowaka_v2_lab/artifacts/cache/scan_matrix/validation"
    )


def test_holdout_scope_appends_holdout_segment(tmp_path):
    base = tmp_path / "cache" / "scan_matrix"
    out = resolve_scan_matrix_store_root({"root": str(base)}, "holdout")
    assert out == base / "holdout"
