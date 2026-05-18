"""Phase fidelity-8: ``evaluate_promotion`` happy + blocker paths."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from bowaka_lab.promotion import evaluate_promotion


def _make_run(tmp_path, *, with_recon: dict | None = None, missing: set[str] | None = None) -> Path:
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    missing = missing or set()
    if "config.json" not in missing:
        (run_dir / "config.json").write_text("{}", encoding="utf-8")
    if "summary.json" not in missing:
        (run_dir / "summary.json").write_text('{"trade_count": 10}', encoding="utf-8")
    if "trades.parquet" not in missing:
        pd.DataFrame({"trade_id": ["x"]}).to_parquet(run_dir / "trades.parquet")
    if "candidates.parquet" not in missing:
        pd.DataFrame({"symbol": ["AAA"]}).to_parquet(run_dir / "candidates.parquet")
    if with_recon is not None:
        (run_dir / "reconciliation_status.json").write_text(
            json.dumps(with_recon), encoding="utf-8",
        )
    return run_dir


def test_clean_research_only_run_is_not_paper_candidate(tmp_path):
    run_dir = _make_run(tmp_path, with_recon={
        "status": "skipped_no_paper_logs",
        "paper_root": None,
        "implementation_mismatch_count": None,
        "broker_rejection_mismatch_count": None,
        "candidate_missing_in_backtest_count": None,
    })
    out = evaluate_promotion(run_dir)
    assert out.backtest_valid is True
    assert out.paper_candidate is False
    assert out.live_candidate is False
    assert out.promotion_status == "research_only_paper_not_evaluated"
    assert not out.blockers


def test_clean_paper_run_is_paper_candidate(tmp_path):
    run_dir = _make_run(tmp_path, with_recon={
        "status": "ok",
        "paper_root": "/x/y",
        "implementation_mismatch_count": 0,
        "broker_rejection_mismatch_count": 0,
        "candidate_missing_in_backtest_count": 0,
    })
    out = evaluate_promotion(run_dir)
    assert out.backtest_valid is True
    assert out.paper_candidate is True
    assert out.live_candidate is False  # SIP + PIT universe out of scope
    assert out.promotion_status == "paper_candidate"
    assert not out.blockers


def test_paper_blocked_on_unexplained_mismatch(tmp_path):
    run_dir = _make_run(tmp_path, with_recon={
        "status": "ok",
        "paper_root": "/x/y",
        "implementation_mismatch_count": 2,
        "broker_rejection_mismatch_count": 0,
        "candidate_missing_in_backtest_count": 0,
    })
    out = evaluate_promotion(run_dir)
    assert out.paper_candidate is False
    assert out.promotion_status == "paper_blocked"
    assert any("implementation_mismatch_count=2" in b for b in out.blockers)


def test_missing_required_artifact_blocks_backtest_valid(tmp_path):
    run_dir = _make_run(tmp_path, missing={"trades.parquet"}, with_recon={
        "status": "skipped_no_paper_logs"})
    out = evaluate_promotion(run_dir)
    assert out.backtest_valid is False
    assert "missing_required_artifact:trades.parquet" in out.blockers


def test_missing_reconciliation_status_is_blocker(tmp_path):
    run_dir = _make_run(tmp_path, with_recon=None)
    out = evaluate_promotion(run_dir)
    assert "missing_reconciliation_status_json" in out.blockers


def test_unknown_status_is_blocker(tmp_path):
    run_dir = _make_run(tmp_path, with_recon={"status": "wat"})
    out = evaluate_promotion(run_dir)
    assert any("reconciliation_status_unrecognized" in b for b in out.blockers)
