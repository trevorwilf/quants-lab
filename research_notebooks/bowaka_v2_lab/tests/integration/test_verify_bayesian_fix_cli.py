"""Phase 3 (audit 2026-05-29 Appendix B + F) — verify-bayesian-fix CLI.

The CLI emits the operator-pasteable Markdown report and exits 0 only when
every PASS/FAIL row is PASS. Re-introducing a P0 regression (padded incumbent)
must flip the report to FAIL and the exit code non-zero.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from bowaka_v2_lab.devtools.verify_bayesian_fix import main as verify_main
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna import walkforward_runner
from bowaka_v2_lab.reference import contract_available


@pytest.fixture(autouse=True)
def _require_contract() -> None:
    if not contract_available():
        pytest.xfail("frozen contract not generated — run mirror_bowaka_v2_source.ps1")


def _smoke_cfg(tmp_path: Path, lab_root: Path) -> Path:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    return write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=3,
    )


def test_cli_passes_after_remediation(tmp_path: Path, lab_root: Path) -> None:
    cfg = _smoke_cfg(tmp_path, lab_root)
    report = tmp_path / "report.md"
    rc = verify_main(["--config", str(cfg), "--n-trials", "3", "--out", str(report)])
    assert rc == 0
    text = report.read_text(encoding="utf-8")
    assert "OVERALL: PASS" in text
    # every Result cell is PASS
    assert "| FAIL |" not in text


def test_cli_fails_when_unfixed(tmp_path: Path, lab_root: Path, monkeypatch) -> None:
    report = tmp_path / "report.md"

    # Re-introduce the padded incumbent (the pre-fix bug): execution keys padded
    # to the search-space midpoints (60 / 102) instead of the contract 15 / 100.
    def _padded_incumbent(*args, **kwargs):
        from bowaka_v2_lab.reference import load_actual_contract
        from bowaka_v2_lab.reference.import_config import build_config_from_contract
        from bowaka_v2_lab.optuna.walkforward_runner import (
            _incumbent_gap_ratio_from_config,
        )

        cfg = build_config_from_contract(
            load_actual_contract(), feed="iex",
            mode="current_code_parity", feed_thresholds="actual",
        )
        out = {"execution.max_quote_age_seconds": 60,   # padded (was 15)
               "execution.max_spread_bps": 102,          # padded (was 100)
               "exits.stop_pct": cfg["exits"]["stop_pct"],
               "sizing.equal_slice_bankroll_fraction":
                   cfg["sizing"]["equal_slice_bankroll_fraction"]}
        out.update(_incumbent_gap_ratio_from_config(cfg))
        return out

    monkeypatch.setattr(
        walkforward_runner, "_incumbent_baseline_params", _padded_incumbent,
    )
    rc = verify_main(["--config", "configs/x.yml", "--n-trials", "3",
                      "--out", str(report), "--skip-short-run"])
    assert rc != 0
    text = report.read_text(encoding="utf-8")
    assert "OVERALL: FAIL" in text
    assert "| FAIL |" in text
