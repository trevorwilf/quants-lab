"""Phase 10 — the `reconcile` CLI command on the missing-paper-logs path.

When no paper logs are supplied (``--paper-logs-root`` absent AND
``$BOWAKA_V2_PAPER_LOGS_ROOT`` unset), the command must exit 0 and write a
scaffolding-only reconciliation report — it never fabricates paper data
(the Phase-10 operator constraint).
"""
from __future__ import annotations

import json

from bowaka_v2_lab import cli


def test_reconcile_cli_exits_zero_with_no_paper_logs(tmp_path, monkeypatch) -> None:
    """No paper logs anywhere -> exit 0 + a scaffolding-only report."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    out_dir = tmp_path / "recon"
    rc = cli.main([
        "reconcile", "--session-date", "2024-09-04", "--out", str(out_dir),
    ])
    assert rc == 0
    md = out_dir / "reconciliation_report.md"
    js = out_dir / "reconciliation_report.json"
    assert md.is_file()
    assert js.is_file()

    report = json.loads(js.read_text(encoding="utf-8"))
    assert report["scaffolding_only"] is True
    assert report["session_date"] == "2024-09-04"
    # The report explains that no paper logs were provided.
    assert "no paper logs" in (report.get("note") or "").lower()

    text = md.read_text(encoding="utf-8")
    assert "Paper-vs-Lab Reconciliation Report" in text
    assert "scaffolding_only: True" in text


def test_reconcile_cli_scaffold_report_has_calibration_section(tmp_path, monkeypatch) -> None:
    """The scaffolding-only report still carries the report's section set."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    out_dir = tmp_path / "recon"
    rc = cli.main([
        "reconcile", "--session-date", "2025-01-15", "--out", str(out_dir),
    ])
    assert rc == 0
    text = (out_dir / "reconciliation_report.md").read_text(encoding="utf-8")
    assert "## Stage Match Counts" in text
    assert "## Suggested Calibration Adjustments" in text
    # The calibration advice names the missing paper logs.
    assert "paper log" in text.lower()


def test_reconcile_cli_paper_logs_but_no_config(tmp_path, monkeypatch) -> None:
    """Paper logs given but no --config -> scaffolding report, still exit 0."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    # A real (but empty) paper-logs directory.
    plr = tmp_path / "paper_logs"
    plr.mkdir()
    out_dir = tmp_path / "recon"
    rc = cli.main([
        "reconcile", "--session-date", "2024-09-04",
        "--paper-logs-root", str(plr), "--out", str(out_dir),
    ])
    assert rc == 0
    report = json.loads((out_dir / "reconciliation_report.json").read_text(encoding="utf-8"))
    assert report["scaffolding_only"] is True


def test_reconcile_cli_env_var_resolves_paper_logs(tmp_path, monkeypatch) -> None:
    """$BOWAKA_V2_PAPER_LOGS_ROOT is honoured when the flag is absent."""
    plr = tmp_path / "env_paper_logs"
    plr.mkdir()
    monkeypatch.setenv("BOWAKA_V2_PAPER_LOGS_ROOT", str(plr))
    out_dir = tmp_path / "recon"
    # No --config -> the command resolves the env var, then writes a
    # scaffolding-only report (config needed to replay the lab). Still exit 0.
    rc = cli.main([
        "reconcile", "--session-date", "2024-09-04", "--out", str(out_dir),
    ])
    assert rc == 0
    report = json.loads((out_dir / "reconciliation_report.json").read_text(encoding="utf-8"))
    # The env var resolved -> the reason is "no --config", not "no paper logs".
    assert report["scaffolding_only"] is True
    assert "config" in (report.get("note") or "").lower()
