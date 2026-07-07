"""Runtime scan-matrix freshness gate (2026-07-01 stale-matrix incident).

The study-fbe6b208 run silently degraded to the legacy per-symbol scanner
(~15x/trial) because nothing at runtime compared the built store to the
resolved window / current lake. These tests pin the new gate:

* session-coverage miss  -> raises OptunaStudyInvalidError
* code_hashes drift      -> raises
* dataset_hash drift     -> raises
* BOWAKA_V2_ALLOW_STALE_SCAN_MATRIX=1 -> downgrades to a warning
* MATRICES_STALE.flag    -> assert_no_stale_matrix_flag raises (study start)
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pytest

from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from bowaka_v2_lab.scanner.scan_matrix import (
    ScanMatrixStore,
    _source_file_hashes,
    assert_no_stale_matrix_flag,
    assert_scan_matrix_fresh,
)
from bowaka_v2_lab.scanner import scan_matrix as _sm


def _mk_store(tmp_path: Path, manifest_extra: dict) -> tuple[ScanMatrixStore, Path]:
    root = tmp_path / "store"
    root.mkdir()
    manifest = {
        "matrix_id": "test",
        "scope": "validation",
        "sessions": ["2026-01-05", "2026-01-06"],
        **manifest_extra,
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return ScanMatrixStore(root, readonly=True), root


@pytest.fixture(autouse=True)
def _clear_freshness_cache():
    _sm._FRESHNESS_VALIDATED.clear()
    yield
    _sm._FRESHNESS_VALIDATED.clear()


_CFG = {"backtest": {"start_date": "2026-01-01", "end_date": "2026-02-01"}}


def test_session_coverage_miss_raises(tmp_path):
    store, root = _mk_store(tmp_path, {})
    with pytest.raises(OptunaStudyInvalidError, match="required session"):
        assert_scan_matrix_fresh(
            _CFG, store, root,
            required_sessions=[_dt.date(2026, 1, 5), _dt.date(2026, 1, 7)],
        )


def test_covered_sessions_pass(tmp_path):
    store, root = _mk_store(tmp_path, {})
    assert_scan_matrix_fresh(
        _CFG, store, root, required_sessions=[_dt.date(2026, 1, 5)],
    )


def test_code_hash_drift_raises(tmp_path):
    store, root = _mk_store(
        tmp_path, {"code_hashes": {"features/forming_bar.py": "deadbeef"}},
    )
    with pytest.raises(OptunaStudyInvalidError, match="source file"):
        assert_scan_matrix_fresh(
            _CFG, store, root, required_sessions=[_dt.date(2026, 1, 5)],
        )


def test_matching_code_hashes_pass(tmp_path):
    src_root = Path(_sm.__file__).resolve().parents[1]
    store, root = _mk_store(tmp_path, {"code_hashes": _source_file_hashes(src_root)})
    assert_scan_matrix_fresh(
        _CFG, store, root, required_sessions=[_dt.date(2026, 1, 5)],
    )


def test_dataset_hash_drift_raises(tmp_path, monkeypatch):
    store, root = _mk_store(tmp_path, {"dataset_hash": "built-against-old-lake"})
    monkeypatch.setattr(
        _sm, "_expected_manifest_dataset_hash", lambda manifest, cfg: "current-lake",
    )
    with pytest.raises(OptunaStudyInvalidError, match="dataset_hash drift"):
        assert_scan_matrix_fresh(
            _CFG, store, root, required_sessions=[_dt.date(2026, 1, 5)],
        )


def test_dataset_hash_match_passes_and_caches(tmp_path, monkeypatch):
    store, root = _mk_store(tmp_path, {"dataset_hash": "same"})
    calls = []

    def _fake(manifest, cfg):
        calls.append(1)
        return "same"

    monkeypatch.setattr(_sm, "_expected_manifest_dataset_hash", _fake)
    assert_scan_matrix_fresh(_CFG, store, root, required_sessions=[_dt.date(2026, 1, 5)])
    assert_scan_matrix_fresh(_CFG, store, root, required_sessions=[_dt.date(2026, 1, 6)])
    assert len(calls) == 1  # second call served from the per-process cache


def test_allow_stale_env_downgrades_to_warning(tmp_path, monkeypatch, caplog):
    store, root = _mk_store(tmp_path, {})
    monkeypatch.setenv("BOWAKA_V2_ALLOW_STALE_SCAN_MATRIX", "1")
    with caplog.at_level("WARNING"):
        assert_scan_matrix_fresh(
            _CFG, store, root,
            required_sessions=[_dt.date(2026, 1, 5), _dt.date(2026, 1, 7)],
        )
    assert any("STALE" in r.message for r in caplog.records)


def test_stale_flag_raises(tmp_path, monkeypatch):
    (tmp_path / "MATRICES_STALE.flag").write_text("refresh died", encoding="utf-8")
    monkeypatch.setenv("BOWAKA_V2_REPO_ROOT_OVERRIDE", str(tmp_path))
    with pytest.raises(OptunaStudyInvalidError, match="MATRICES_STALE"):
        assert_no_stale_matrix_flag()


def test_no_stale_flag_passes(tmp_path, monkeypatch):
    monkeypatch.setenv("BOWAKA_V2_REPO_ROOT_OVERRIDE", str(tmp_path))
    assert_no_stale_matrix_flag()
