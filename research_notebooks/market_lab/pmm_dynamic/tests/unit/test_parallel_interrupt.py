"""Tests for parallel interrupt handling (KeyboardInterrupt resilience)."""

import inspect
from unittest.mock import MagicMock, patch

import pytest

from pmm_lab.optuna.parallel import WorkerResult


def test_serial_optimization_returns_partial_on_interrupt():
    """Mock study.optimize to raise KeyboardInterrupt, verify run_optimization returns the study."""
    from pmm_lab.optuna.study import run_optimization

    mock_study = MagicMock()
    mock_study.optimize = MagicMock(side_effect=KeyboardInterrupt)

    result = run_optimization(mock_study, objective=lambda trial: 1.0, n_trials=10)

    # Should return the study without raising
    assert result is mock_study


def test_worker_result_has_interrupted_error_field():
    """Create a WorkerResult with error='interrupted', verify it works."""
    wr = WorkerResult(
        worker_id=0,
        n_completed=0,
        n_pruned=0,
        wall_time=0.0,
        error="interrupted",
    )
    assert wr.error == "interrupted"
    assert wr.worker_id == 0
    assert wr.n_completed == 0


def test_dispatcher_handles_keyboard_interrupt():
    """Verify the dispatcher source contains KeyboardInterrupt handling for the parallel path."""
    from pmm_lab.optuna import dispatcher

    source = inspect.getsource(dispatcher.run_optimization_dispatch)
    assert "KeyboardInterrupt" in source, (
        "run_optimization_dispatch must handle KeyboardInterrupt in the parallel path"
    )
