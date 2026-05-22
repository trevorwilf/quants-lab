"""Phase 8 — qr.05 rejects a placeholder dataset hash.

The pre-Phase-2 lineage stub set ``dataset_hash = run_hash[:16]``. A run that
regressed to that placeholder cannot be promoted — ``qr.05_dataset_lineage_present``
must fail it. A real content-derived hash, and an honest ``fixture`` provider on
a genuinely-synthetic run, both pass.
"""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.promotion.checklist import QUANT_REVIEWER_CHECKLIST

_QR05 = QUANT_REVIEWER_CHECKLIST["qr.05_dataset_lineage_present"]


def _write_manifest(rd: Path, doc: dict) -> None:
    (rd / "run_manifest.json").write_text(json.dumps(doc), encoding="utf-8")


def test_placeholder_dataset_hash_fails_qr05(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    run_hash = "abcdef0123456789" + "f" * 48  # 64-hex
    _write_manifest(rd, {
        "run_hash": run_hash,
        # The legacy placeholder: dataset_hash == run_hash[:16].
        "dataset_hash": run_hash[:16],
        "lineage": {"dataset_hash": run_hash[:16], "dataset_provider": "fixture",
                    "dataset_regime": "synthetic"},
    })
    status, evidence = _QR05(rd)
    assert status == "fail"
    assert isinstance(evidence, dict)
    assert "placeholder" in evidence.get("detail", "")


def test_real_content_hash_passes_qr05(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    run_hash = "1111111111111111" + "2" * 48
    dataset_hash = "9999999999999999" + "8" * 48  # different from run_hash[:16]
    _write_manifest(rd, {
        "run_hash": run_hash,
        "dataset_hash": dataset_hash,
        "lineage": {"dataset_hash": dataset_hash, "dataset_provider": "fixture",
                    "dataset_regime": "synthetic"},
    })
    status, evidence = _QR05(rd)
    assert status == "pass"
    assert evidence["placeholder"] is False


def test_fixture_provider_on_lake_run_fails_qr05(tmp_path: Path) -> None:
    """A 'fixture' provider on a non-synthetic (lake) regime is dishonest -> fail."""
    rd = tmp_path / "run"
    rd.mkdir()
    run_hash = "aaaaaaaaaaaaaaaa" + "b" * 48
    dataset_hash = "cccccccccccccccc" + "d" * 48
    _write_manifest(rd, {
        "run_hash": run_hash,
        "dataset_hash": dataset_hash,
        "lineage": {"dataset_hash": dataset_hash, "dataset_provider": "fixture",
                    "dataset_regime": "lake"},
    })
    status, evidence = _QR05(rd)
    assert status == "fail"
    assert "fixture" in evidence.get("detail", "")


def test_missing_manifest_fails_qr05(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    status, evidence = _QR05(rd)
    assert status == "fail"
    assert isinstance(evidence, dict)
