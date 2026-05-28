"""Phase 2.5 — worker-count parity check unit tests.

The script ``scripts/check_worker_count_parity.py`` reads a worker-count
matrix JSON and scores per-row parity vs the lowest-n_workers reference.
This test feeds it synthetic JSON snapshots covering the parity-clean,
within-tolerance, and out-of-tolerance cases.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_SCRIPT = (
    Path(__file__).resolve().parents[3] / "scripts" / "check_worker_count_parity.py"
)


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "check_worker_count_parity", _SCRIPT,
    )
    assert spec and spec.loader, _SCRIPT
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("check_worker_count_parity", mod)
    spec.loader.exec_module(mod)
    return mod


def _row(
    n_workers: int, *, status: str = "ok",
    trades: int = 5,
    eq: list[float] | None = None,
    pnl: float = 12345.6789,
    replay_error: str | None = None,
) -> dict:
    snapshot = {
        "trades_count": trades,
        "daily_equity_first_last": list(eq if eq is not None else [100000.0, 101000.0]),
        "final_pnl": pnl,
    }
    if replay_error is not None:
        snapshot = {"replay_error": replay_error}
    return {
        "n_workers": n_workers,
        "status": status,
        "trials_per_hour": 50.0,
        "p50_trial_seconds": 10.0,
        "peak_rss_gib": 5.0,
        "fixed_replay_snapshot": snapshot,
    }


def test_parity_clean_when_every_replay_matches_reference() -> None:
    mod = _load_script()
    matrix = {
        "results": [
            _row(1), _row(4), _row(8), _row(12),
        ]
    }
    report = mod.check_parity(matrix)
    assert report["status"] == "ok"
    for row in report["results"]:
        assert row.get("parity_clean") is True


def test_parity_fail_when_one_replay_diverges_beyond_tolerance() -> None:
    mod = _load_script()
    matrix = {
        "results": [
            _row(1),
            _row(4),
            # pnl drift of 1.0 is far beyond 1e-9 tolerance.
            _row(8, pnl=12346.6789),
            _row(12),
        ]
    }
    report = mod.check_parity(matrix)
    assert report["status"] == "fail"
    fails = [r for r in report["results"] if r.get("parity_clean") is False]
    assert len(fails) == 1
    assert fails[0]["n_workers"] == 8


def test_parity_fail_when_a_worker_count_errored() -> None:
    mod = _load_script()
    matrix = {
        "results": [
            _row(1),
            _row(4, status="error"),
            _row(8),
        ]
    }
    report = mod.check_parity(matrix)
    assert report["status"] == "fail"
    fails = [r for r in report["results"] if r.get("parity_clean") is False]
    assert any(r["n_workers"] == 4 for r in fails)


def test_parity_fail_when_replay_snapshot_carries_error() -> None:
    mod = _load_script()
    matrix = {
        "results": [
            _row(1),
            _row(8, replay_error="lake disk full"),
        ]
    }
    report = mod.check_parity(matrix)
    assert report["status"] == "fail"


def test_parity_pass_within_tolerance() -> None:
    """A 1e-13 drift in equity is within the price tolerance (1e-12)."""
    mod = _load_script()
    matrix = {
        "results": [
            _row(1, eq=[100000.0, 101000.0]),
            _row(8, eq=[100000.0 + 1e-13, 101000.0 - 1e-13]),
        ]
    }
    report = mod.check_parity(matrix)
    assert report["status"] == "ok"
