"""``bowaka-v2-lab scan-matrix build / verify`` end-to-end on the tiny lake.

Matrix doc §12 phase 1 / Phase 8.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import yaml

from bowaka_v2_lab import cli
from bowaka_v2_lab.devtools.wf_lake import (
    build_tiny_lake,
    write_walkforward_test_config,
)


def test_scan_matrix_build_then_verify(tmp_path, lab_root):
    lake = tmp_path / "lake"
    # Tiny lake spans 4 months so the 1/1/1-month walk-forward plan can
    # build at least one validation split + the holdout window.
    build_tiny_lake(lake, ["AAA"],
                    start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
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
    assert (store_root / "manifest.json").is_file()
    manifest = json.loads((store_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["scope"] == "validation"
    assert manifest["matrix_version"] >= 1
    # At least one session partition was created.
    sess_dirs = list(store_root.glob("session=*"))
    assert sess_dirs, "no session= partitions written"

    rc = cli.main([
        "scan-matrix", "verify",
        "--config", str(cfg_path),
        "--store-root", str(store_root),
        "--sample-count", "5",
    ])
    assert rc == 0

    # Speedup report v2 §10.3 fix 1 / Phase 2 — after a successful build,
    # verify_scan_matrix's report must include a non-empty dataset_hash and
    # status == "ok" with sampled > 0. Drop down to the function for a richer
    # report (the CLI swallows the body to stdout).
    from bowaka_v2_lab.scanner.scan_matrix import verify_scan_matrix

    report = verify_scan_matrix(store_root, cfg_path, sample_count=5)
    assert report["status"] == "ok", report
    assert report["sampled"] > 0, report
    # Manifest dataset_hash must equal the report's recorded value AND the
    # value re-derived from the lake state ("dataset_hash drift catches
    # silent re-ingest").
    assert report["dataset_hash"] == manifest["dataset_hash"], report
