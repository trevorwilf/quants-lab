"""Tests for the notebook dispatch helper."""
import pytest
from unittest.mock import patch, MagicMock


class TestNotebookDispatch:
    """Notebook helper must route through the same dispatcher as the pipeline."""

    def test_accepts_objective_factory_kwarg(self):
        """optimize_study_for_notebook must accept objective_factory parameter."""
        import inspect
        from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook
        sig = inspect.signature(optimize_study_for_notebook)
        assert "objective_factory" in sig.parameters
        assert "factory_kwargs" in sig.parameters

    def test_does_not_accept_candles_or_pair_rules(self):
        """optimize_study_for_notebook must NOT accept trading-specific params."""
        import inspect
        from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook
        sig = inspect.signature(optimize_study_for_notebook)
        for forbidden in ("candles", "pair_rules", "bar_interval_seconds",
                          "dataset_hash", "reference_price"):
            assert forbidden not in sig.parameters, (
                f"optimize_study_for_notebook should not accept '{forbidden}' — "
                f"it must be a thin dispatch wrapper, not an objective builder."
            )

    def test_delegates_to_dispatcher(self):
        """Must call run_optimization_dispatch, not study.optimize directly."""
        import inspect
        from pmm_lab.optuna import notebook_dispatch
        source = inspect.getsource(notebook_dispatch.optimize_study_for_notebook)
        assert "run_optimization_dispatch" in source
        assert "study.optimize" not in source

    def test_serial_dispatch(self):
        """n_jobs=1 should pass through to dispatcher."""
        from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook
        with patch("pmm_lab.optuna.notebook_dispatch.run_optimization_dispatch") as mock_dispatch, \
             patch("pmm_lab.optuna.notebook_dispatch.create_study") as mock_create:
            mock_study = MagicMock()
            mock_create.return_value = mock_study
            mock_dispatch.return_value = mock_study

            result = optimize_study_for_notebook(
                study_name="test",
                n_trials=10,
                n_jobs=1,
                objective_factory=MagicMock(),
                factory_kwargs={"candles": "fake"},
            )

            mock_dispatch.assert_called_once()
            call_kwargs = mock_dispatch.call_args[1]
            assert call_kwargs["n_jobs"] == 1
            assert call_kwargs["certified"] is False
            assert "objective_factory" in call_kwargs
            assert "factory_kwargs" in call_kwargs

    def test_parallel_dispatch(self):
        """n_jobs>1 should pass through to dispatcher with correct n_jobs."""
        from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook
        with patch("pmm_lab.optuna.notebook_dispatch.run_optimization_dispatch") as mock_dispatch, \
             patch("pmm_lab.optuna.notebook_dispatch.create_study") as mock_create:
            mock_study = MagicMock()
            mock_create.return_value = mock_study
            mock_dispatch.return_value = mock_study

            result = optimize_study_for_notebook(
                study_name="test",
                n_trials=100,
                n_jobs=8,
                objective_factory=MagicMock(),
                factory_kwargs={},
                storage_url="postgresql://localhost/test",
            )

            call_kwargs = mock_dispatch.call_args[1]
            assert call_kwargs["n_jobs"] == 8

    def test_callbacks_passed_through(self):
        """Callbacks should be forwarded to the dispatcher."""
        from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook
        mock_callback = MagicMock()
        with patch("pmm_lab.optuna.notebook_dispatch.run_optimization_dispatch") as mock_dispatch, \
             patch("pmm_lab.optuna.notebook_dispatch.create_study") as mock_create:
            mock_create.return_value = MagicMock()
            mock_dispatch.return_value = MagicMock()

            optimize_study_for_notebook(
                study_name="test",
                n_trials=10,
                n_jobs=1,
                objective_factory=MagicMock(),
                factory_kwargs={},
                callbacks=[mock_callback],
            )

            call_kwargs = mock_dispatch.call_args[1]
            assert call_kwargs["callbacks"] == [mock_callback]

    def test_n_startup_trials_passed_through(self):
        """n_startup_trials should reach both create_study and dispatcher."""
        from pmm_lab.optuna.notebook_dispatch import optimize_study_for_notebook
        with patch("pmm_lab.optuna.notebook_dispatch.run_optimization_dispatch") as mock_dispatch, \
             patch("pmm_lab.optuna.notebook_dispatch.create_study") as mock_create:
            mock_create.return_value = MagicMock()
            mock_dispatch.return_value = MagicMock()

            optimize_study_for_notebook(
                study_name="test",
                n_trials=10,
                n_jobs=1,
                objective_factory=MagicMock(),
                factory_kwargs={},
                n_startup_trials=600,
            )

            # Check create_study got it
            create_kwargs = mock_create.call_args[1]
            assert create_kwargs["n_startup_trials"] == 600

            # Check dispatcher got it
            dispatch_kwargs = mock_dispatch.call_args[1]
            assert dispatch_kwargs["n_startup_trials"] == 600
