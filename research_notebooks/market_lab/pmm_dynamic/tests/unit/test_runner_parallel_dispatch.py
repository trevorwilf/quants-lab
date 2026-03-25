"""Tests for optimization dispatch routing logic."""

import pytest
from unittest.mock import patch, MagicMock, call
import optuna


def _make_study(name="test_study"):
    """Create an in-memory Optuna study for testing."""
    return optuna.create_study(study_name=name, direction="maximize")


def _dummy_factory(**kwargs):
    """Dummy objective factory."""
    def objective(trial):
        return 0.0
    return objective


class TestDispatchRouting:
    """Verify dispatch routes to serial or parallel correctly."""

    def test_certified_forces_serial(self):
        """certified=True must always route to serial."""
        study = _make_study()
        with patch("pmm_lab.optuna.dispatcher._run_serial", return_value=study) as mock_serial:
            from pmm_lab.optuna.dispatcher import run_optimization_dispatch
            result = run_optimization_dispatch(
                study=study,
                study_name="test",
                objective_factory=_dummy_factory,
                factory_kwargs={},
                n_trials=10,
                n_jobs=4,
                certified=True,
                storage_url="postgresql://localhost/optuna",
            )
            mock_serial.assert_called_once()

    def test_n_jobs_1_forces_serial(self):
        """n_jobs=1 must route to serial."""
        study = _make_study()
        with patch("pmm_lab.optuna.dispatcher._run_serial", return_value=study) as mock_serial:
            from pmm_lab.optuna.dispatcher import run_optimization_dispatch
            result = run_optimization_dispatch(
                study=study,
                study_name="test",
                objective_factory=_dummy_factory,
                factory_kwargs={},
                n_trials=10,
                n_jobs=1,
                certified=False,
                storage_url=None,
            )
            mock_serial.assert_called_once()

    def test_parallel_with_postgres(self):
        """n_jobs>1 + PostgreSQL storage should attempt parallel."""
        study = _make_study()
        mock_worker_result = MagicMock()
        mock_worker_result.n_completed = 5
        mock_worker_result.error = None

        with patch("pmm_lab.optuna.parallel.preflight_check") as mock_pf, \
             patch("pmm_lab.optuna.parallel.run_parallel_optimization",
                   return_value=[mock_worker_result]) as mock_par, \
             patch("optuna.load_study", return_value=study):
            from pmm_lab.optuna.dispatcher import run_optimization_dispatch
            result = run_optimization_dispatch(
                study=study,
                study_name="test",
                objective_factory=_dummy_factory,
                factory_kwargs={},
                n_trials=10,
                n_jobs=4,
                certified=False,
                storage_url="postgresql://localhost/optuna",
            )
            mock_par.assert_called_once()

    def test_strict_raises_on_sqlite(self):
        """strict_parallel=True must raise when preflight fails (e.g., SQLite)."""
        study = _make_study()
        from pmm_lab.optuna.dispatcher import run_optimization_dispatch
        with pytest.raises(ValueError, match="PostgreSQL"):
            run_optimization_dispatch(
                study=study,
                study_name="test",
                objective_factory=_dummy_factory,
                factory_kwargs={},
                n_trials=10,
                n_jobs=4,
                certified=False,
                storage_url="sqlite:///test.db",
                strict_parallel=True,
            )

    def test_non_strict_falls_back_to_serial(self):
        """strict_parallel=False must fall back to serial when preflight fails."""
        study = _make_study()
        with patch("pmm_lab.optuna.dispatcher._run_serial", return_value=study) as mock_serial:
            from pmm_lab.optuna.dispatcher import run_optimization_dispatch
            result = run_optimization_dispatch(
                study=study,
                study_name="test",
                objective_factory=_dummy_factory,
                factory_kwargs={},
                n_trials=10,
                n_jobs=4,
                certified=False,
                storage_url="sqlite:///test.db",
                strict_parallel=False,
            )
            mock_serial.assert_called_once()
