"""Phase 0 (phases 4-7) — Section 7 records EVIDENCE_DEFERRED for a lake that
lacks split_adjusted daily partitions (a data-engineering pre-requisite), and
a real FAIL for any other preflight error.
"""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.devtools import verify_bayesian_fix as vbf
from bowaka_v2_lab.optuna import walkforward_runner
from bowaka_v2_lab.optuna.preflight import PreflightError


def test_section7_deferred_on_daily_adjustment_partition(monkeypatch) -> None:
    def _raise(*args, **kwargs):
        raise PreflightError(
            "no split_adjusted daily_adjustment_partition on disk for feed='iex'"
        )

    monkeypatch.setattr(walkforward_runner, "run_walkforward_study", _raise)
    s7, _sha = vbf._run_short_run(Path("configs/x.yml"), 3)
    assert len(s7.checks) == 1
    assert s7.checks[0].passed is True
    assert s7.checks[0].actual.startswith("DEFERRED:")


def test_section7_fail_on_other_preflight_error(monkeypatch) -> None:
    def _raise(*args, **kwargs):
        raise PreflightError("minute coverage below threshold")

    monkeypatch.setattr(walkforward_runner, "run_walkforward_study", _raise)
    s7, _sha = vbf._run_short_run(Path("configs/x.yml"), 3)
    assert len(s7.checks) == 1
    assert s7.checks[0].passed is False
    assert not s7.checks[0].actual.startswith("DEFERRED:")
