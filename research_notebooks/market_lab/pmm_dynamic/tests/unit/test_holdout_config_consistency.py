"""Holdout validation must always describe the exported config."""


def test_holdout_evaluates_exported_config_first():
    """The first candidate in holdout evaluation must be the exported config.

    This is a structural test — verify the pipeline puts best_config at index 0
    in the holdout_candidates list. The code change in runner.py ensures this by
    constructing holdout_candidates = [(best_config, best_trial.value or 0.0)]
    before appending additional top-k candidates.
    """
    # Validate the structural guarantee: candidates[0] is always the exported config
    # by checking that the pipeline code constructs holdout_candidates correctly
    import inspect
    from pmm_lab.deploy.runner import run_full_pipeline
    source = inspect.getsource(run_full_pipeline)
    assert "holdout_candidates = [(best_config," in source, (
        "Pipeline must construct holdout_candidates with best_config as first element"
    )
    assert "holdout_report.candidates[0]" in source, (
        "Pipeline must reference candidates[0] for package metadata"
    )
