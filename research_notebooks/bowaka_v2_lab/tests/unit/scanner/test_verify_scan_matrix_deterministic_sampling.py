"""Phase 2 §2 — verify_scan_matrix's random sampling is seed-deterministic.

Two calls with the same ``seed`` MUST report identical ``sampled``,
``session_sampled``, and issue lists. Different seeds may legally pick
different cells but must still report ``status == "ok"`` on a clean
matrix.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import yaml

from bowaka_v2_lab import cli
from bowaka_v2_lab.devtools.wf_lake import (
    build_tiny_lake,
    write_walkforward_test_config,
)
from bowaka_v2_lab.scanner.scan_matrix import verify_scan_matrix


def _build_matrix(tmp_path: Path, lab_root: Path) -> tuple[Path, Path]:
    lake = tmp_path / "lake"
    build_tiny_lake(
        lake, ["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
    )
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=1,
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    raw.setdefault("session", {})["scan_interval_seconds"] = 1800
    raw["simulation"]["intraday_window_policy"] = "extended_hours_to_scan"
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    store_root = tmp_path / "matrix"
    rc = cli.main([
        "scan-matrix", "build",
        "--config", str(cfg_path),
        "--scope", "validation",
        "--store-root", str(store_root),
        "--workers", "1",
        "--reserve-system-gib", "0.1",
        "--max-optuna-workers", "1",
    ])
    assert rc == 0
    return store_root, cfg_path


def test_same_seed_produces_same_sampled_grid(tmp_path, lab_root) -> None:
    store_root, cfg_path = _build_matrix(tmp_path, lab_root)
    a = verify_scan_matrix(store_root, cfg_path, sample_count=5, seed=42)
    b = verify_scan_matrix(store_root, cfg_path, sample_count=5, seed=42)
    assert a["sampled"] == b["sampled"]
    assert a["session_sampled"] == b["session_sampled"]
    assert a["issues"] == b["issues"]
    assert a["dataset_hash"] == b["dataset_hash"]


def test_seed_appears_in_report(tmp_path, lab_root) -> None:
    store_root, cfg_path = _build_matrix(tmp_path, lab_root)
    report = verify_scan_matrix(store_root, cfg_path, sample_count=3, seed=7)
    assert report["seed"] == 7
