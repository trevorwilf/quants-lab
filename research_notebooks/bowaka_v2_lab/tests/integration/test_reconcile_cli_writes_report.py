"""Phase 9 — the ``reconcile`` CLI writes the JSON/MD report pair.

The Phase-9 prompt requires the ``bowaka-v2-lab reconcile`` subcommand to
write ``artifacts/reconcile/<run_id>/report.{json,md}`` (or, when ``--out`` is
set, into that directory). The scaffolding-only path always produces the pair
even when no paper logs are resolved.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from bowaka_v2_lab import cli


def test_reconcile_cli_writes_report_pair_no_paper_logs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No paper logs anywhere → scaffolding report.{md,json} pair, exit 0."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    out_dir = tmp_path / "recon"
    rc = cli.main([
        "reconcile",
        "--session-date", "2024-09-03",
        "--out", str(out_dir),
    ])
    assert rc == 0
    md = out_dir / "reconciliation_report.md"
    js = out_dir / "reconciliation_report.json"
    assert md.is_file()
    assert js.is_file()


def test_reconcile_cli_paper_logs_no_config_writes_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, lab_root: Path
) -> None:
    """Paper logs given but no --config → still writes the scaffolding report."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    out_dir = tmp_path / "recon"
    plr = lab_root / "tests" / "fixtures" / "paper_logs" / "2024-09-03"
    rc = cli.main([
        "reconcile",
        "--session-date", "2024-09-03",
        "--paper-logs-root", str(plr),
        "--out", str(out_dir),
    ])
    assert rc == 0
    md = out_dir / "reconciliation_report.md"
    js = out_dir / "reconciliation_report.json"
    assert md.is_file()
    assert js.is_file()
    report = json.loads(js.read_text(encoding="utf-8"))
    # Either scaffolding or filled — but the contract is "writes the pair".
    assert "session_date" in report


def test_reconcile_cli_env_var_writes_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``$BOWAKA_V2_PAPER_LOGS_ROOT`` resolves the path and the report is written."""
    plr = tmp_path / "paper_logs"
    plr.mkdir()
    monkeypatch.setenv("BOWAKA_V2_PAPER_LOGS_ROOT", str(plr))
    out_dir = tmp_path / "recon"
    rc = cli.main([
        "reconcile",
        "--session-date", "2024-09-03",
        "--out", str(out_dir),
    ])
    assert rc == 0
    assert (out_dir / "reconciliation_report.json").is_file()
    assert (out_dir / "reconciliation_report.md").is_file()
