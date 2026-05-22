"""Phase 10 — the `reconcile` CLI command on the full synthetic-fixture path.

With a config AND the frozen synthetic paper logs, the command replays the
session against the lab and writes a real (non-scaffolding) reconciliation
report. Still no real paper data, no network.
"""
from __future__ import annotations

import json

import yaml

from bowaka_v2_lab import cli

from .conftest import PAPER_LOGS_SYNTHETIC, SYNTHETIC_SESSION


def test_reconcile_cli_full_path(parity_lake_config, tmp_path, monkeypatch) -> None:
    """`reconcile` with --config + --paper-logs-root runs the lab and reconciles."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    cfg_path = tmp_path / "parity.yml"
    cfg_path.write_text(yaml.safe_dump(parity_lake_config), encoding="utf-8")
    out_dir = tmp_path / "recon"

    rc = cli.main([
        "reconcile",
        "--session-date", SYNTHETIC_SESSION.isoformat(),
        "--paper-logs-root", str(PAPER_LOGS_SYNTHETIC),
        "--config", str(cfg_path),
        "--out", str(out_dir),
    ])
    assert rc == 0
    md = out_dir / "reconciliation_report.md"
    js = out_dir / "reconciliation_report.json"
    assert md.is_file()
    assert js.is_file()

    report = json.loads(js.read_text(encoding="utf-8"))
    # The synthetic paper logs were found -> this is a real reconciliation.
    assert report["scaffolding_only"] is False
    assert report["session_date"] == SYNTHETIC_SESSION.isoformat()
    # Candidate-set buckets are populated.
    assert report["n_paper_candidates"] == 3
    assert len(report["rows"]) >= 3


def test_reconcile_cli_picks_up_config_paper_logs_root(
    parity_lake_config, tmp_path, monkeypatch
) -> None:
    """``reconcile.paper_logs_root`` in the config is used when the flag is absent."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    cfg = dict(parity_lake_config)
    cfg["reconcile"] = {"paper_logs_root": str(PAPER_LOGS_SYNTHETIC)}
    cfg_path = tmp_path / "parity_with_recon.yml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    out_dir = tmp_path / "recon"

    rc = cli.main([
        "reconcile",
        "--session-date", SYNTHETIC_SESSION.isoformat(),
        "--config", str(cfg_path),
        "--out", str(out_dir),
    ])
    assert rc == 0
    report = json.loads((out_dir / "reconciliation_report.json").read_text(encoding="utf-8"))
    assert report["scaffolding_only"] is False
