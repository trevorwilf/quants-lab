"""Tests that stress baseline reuse produces identical results to fresh computation."""

import inspect


class TestStressBaselineReuse:
    """Verify run_stress_tests accepts and uses pre-computed baseline artifacts."""

    def test_signature_has_baseline_params(self):
        """run_stress_tests must accept baseline_result, baseline_metrics, baseline_objective."""
        from pmm_lab.objective.stress import run_stress_tests
        sig = inspect.signature(run_stress_tests)
        params = list(sig.parameters.keys())
        assert "baseline_result" in params
        assert "baseline_metrics" in params
        assert "baseline_objective" in params

    def test_baseline_params_default_to_none(self):
        """All baseline params must default to None for backward compatibility."""
        from pmm_lab.objective.stress import run_stress_tests
        sig = inspect.signature(run_stress_tests)
        assert sig.parameters["baseline_result"].default is None
        assert sig.parameters["baseline_metrics"].default is None
        assert sig.parameters["baseline_objective"].default is None

    def test_runner_passes_baseline_to_stress(self):
        """Runner Step 9 must pass baseline_result, baseline_metrics, baseline_objective."""
        from pmm_lab.deploy import runner
        source = inspect.getsource(runner.run_full_pipeline)
        assert "baseline_result=sim_result" in source
        assert "baseline_metrics=metrics" in source
        assert "baseline_objective=obj_decomp" in source

    def test_conditional_baseline_computation(self):
        """Baseline computation must be conditional on params being None."""
        from pmm_lab.objective import stress
        source = inspect.getsource(stress.run_stress_tests)
        assert "if baseline_result is None:" in source
        assert "if baseline_metrics is None:" in source
        assert "if baseline_objective is None:" in source
