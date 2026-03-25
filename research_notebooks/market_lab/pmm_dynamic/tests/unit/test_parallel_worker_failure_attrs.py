"""Tests that parallel workers use _wrapped_objective for failure attribution."""

import inspect


class TestParallelWorkerWrappedObjective:
    """Verify that _worker_fn uses _wrapped_objective."""

    def test_worker_fn_imports_wrapped_objective(self):
        """_worker_fn must import _wrapped_objective from study module."""
        from pmm_lab.optuna import parallel
        source = inspect.getsource(parallel._worker_fn)
        assert "_wrapped_objective" in source

    def test_worker_fn_wraps_objective(self):
        """_worker_fn must call _wrapped_objective on the factory result."""
        from pmm_lab.optuna import parallel
        source = inspect.getsource(parallel._worker_fn)
        # Must wrap: _wrapped_objective(objective_factory(**factory_kwargs))
        assert "_wrapped_objective(objective_factory(" in source
