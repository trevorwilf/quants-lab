"""Phase 2.5 — worker-count winner selection unit tests.

The script ``scripts/select_worker_count_winner.py`` picks the parity-clean
worker count with the best ``trials_per_hour``, tiebreaks on
``p50_trial_seconds`` then ``peak_rss_gib``, and falls back to 8 when no
parity-clean row survives.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_SCRIPT = (
    Path(__file__).resolve().parents[3] / "scripts" / "select_worker_count_winner.py"
)


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "select_worker_count_winner", _SCRIPT,
    )
    assert spec and spec.loader, _SCRIPT
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("select_worker_count_winner", mod)
    spec.loader.exec_module(mod)
    return mod


def _row(
    n_workers: int, *,
    status: str = "ok", parity_clean: bool = True, error: str | None = None,
    trials_per_hour: float = 50.0, p50_trial_seconds: float = 10.0,
    peak_rss_gib: float = 5.0,
) -> dict:
    out = {
        "n_workers": n_workers, "status": status, "parity_clean": parity_clean,
        "trials_per_hour": trials_per_hour,
        "p50_trial_seconds": p50_trial_seconds, "peak_rss_gib": peak_rss_gib,
    }
    if error is not None:
        out["error"] = error
    return out


def test_picks_highest_trials_per_hour() -> None:
    mod = _load_script()
    matrix = {
        "results": [
            _row(1, trials_per_hour=10.0),
            _row(8, trials_per_hour=60.0),
            _row(12, trials_per_hour=100.0),
        ]
    }
    decision = mod.select_winner(matrix)
    assert decision["winner_n_workers"] == 12
    assert decision["fallback"] is False


def test_refuses_worker_count_with_failure_even_if_throughput_higher() -> None:
    mod = _load_script()
    matrix = {
        "results": [
            _row(1, trials_per_hour=10.0),
            _row(8, trials_per_hour=60.0),
            _row(12, trials_per_hour=100.0, status="error", error="OOM"),
        ]
    }
    decision = mod.select_winner(matrix)
    # 12 was the throughput leader but is disqualified by the worker failure.
    assert decision["winner_n_workers"] == 8


def test_refuses_worker_count_with_parity_violation() -> None:
    mod = _load_script()
    matrix = {
        "results": [
            _row(1, trials_per_hour=10.0),
            _row(12, trials_per_hour=100.0, parity_clean=False),
        ]
    }
    decision = mod.select_winner(matrix)
    assert decision["winner_n_workers"] == 1


def test_falls_back_to_eight_when_no_survivor() -> None:
    mod = _load_script()
    matrix = {
        "results": [
            _row(1, status="error"),
            _row(8, parity_clean=False),
            _row(12, error="PG lock storm"),
        ]
    }
    decision = mod.select_winner(matrix)
    assert decision["winner_n_workers"] == 8
    assert decision["fallback"] is True
    assert "no parity-clean worker count survived" in decision["reason"]


def test_tiebreaks_on_p50_then_peak_rss() -> None:
    mod = _load_script()
    matrix = {
        "results": [
            _row(8, trials_per_hour=100.0, p50_trial_seconds=12.0, peak_rss_gib=5.0),
            _row(12, trials_per_hour=100.0, p50_trial_seconds=10.0, peak_rss_gib=6.0),
            _row(16, trials_per_hour=100.0, p50_trial_seconds=10.0, peak_rss_gib=4.0),
        ]
    }
    decision = mod.select_winner(matrix)
    # Same trials_per_hour -> lower p50 wins (12 and 16 both 10.0); lower rss
    # wins the second tiebreak -> 16.
    assert decision["winner_n_workers"] == 16


def test_baseline_eight_clean_wins_when_others_have_problems() -> None:
    mod = _load_script()
    matrix = {
        "results": [
            _row(1, parity_clean=False),
            _row(4, status="error"),
            _row(8, trials_per_hour=40.0),
            _row(12, error="OOM"),
        ]
    }
    decision = mod.select_winner(matrix)
    assert decision["winner_n_workers"] == 8
    assert decision["fallback"] is False
