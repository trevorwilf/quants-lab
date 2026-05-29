"""Phase 1 (audit 2026-05-29 §5.4 / §13.1) — run manifest records adjustment.

Every completed walk-forward run records the daily-bar adjustment the readers
used (``effective_daily_adjustment``, resolved from the config) alongside what
the lake's ingestion manifest declares (``manifest_daily_adjustment``), so a
reviewer can confirm the run honoured the strategy's adjusted-bar contract.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import yaml

from bowaka_common.marketdata import layout
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def _read_ok_artifact(tmp_path: Path) -> dict:
    for p in sorted(tmp_path.rglob("optuna/*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("status") == "ok":
            return d
    raise AssertionError("no status=ok study artifact found")


def test_manifest_records_effective_and_manifest_daily_adjustment(
    tmp_path: Path, lab_root: Path,
) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    # Declare split_adjusted in the lake ingestion manifest.
    mpath = layout.ingestion_manifest_path(lake)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(
        json.dumps({"feed": "iex", "adjustment": "split_adjusted"}), encoding="utf-8",
    )
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    # The contract requires split-adjusted daily bars (smoke mode skips the
    # full-fold preflight, so the run completes and records the adjustment).
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    doc["market_data"]["require_split_adjustment"] = True
    cfg_path.write_text(yaml.safe_dump(doc), encoding="utf-8")

    run_walkforward_study(cfg_path, allow_smoke=True)

    art = _read_ok_artifact(tmp_path)
    md = art["study_metadata"]
    assert md["effective_daily_adjustment"] == "split_adjusted"
    assert md["manifest_daily_adjustment"] == "split_adjusted"
    assert md["effective_daily_adjustment"] == md["manifest_daily_adjustment"]
