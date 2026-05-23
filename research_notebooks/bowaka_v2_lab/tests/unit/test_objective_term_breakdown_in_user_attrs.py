"""Every Optuna trial carries the objective term breakdown in user_attrs.

Realism remediation 2 Phase 8 (audit §P1-008). ``compute_objective`` returns an
``objective_terms`` dict capturing every term's contribution: ``median_net_return``
(positive driver), every penalty key (subtracted), ``fold_variance`` (subtracted),
plus the final ``objective`` and ``median_fold_score`` for forensics.

The walk-forward objective writes this dict to ``trial.user_attrs["objective_terms"]``
so downstream tooling (and the Phase-9 review notebook) can read it directly.
"""
from __future__ import annotations

import optuna

from bowaka_v2_lab.optuna.objective import (
    DEFAULT_PENALTY_WEIGHTS,
    FoldResult,
    compute_objective,
    fold_penalties,
)


def _toy_folds() -> list[FoldResult]:
    """Three folds with deterministic per-fold metrics."""
    return [
        FoldResult(
            fold_id="f0",
            net_return=0.02, max_drawdown=0.03, turnover=0.05,
            concentration=0.1, n_trades=40, worst_day_loss=0.01,
            quote_coverage=0.98, fill_rate=0.92,
        ),
        FoldResult(
            fold_id="f1",
            net_return=0.05, max_drawdown=0.04, turnover=0.02,
            concentration=0.15, n_trades=60, worst_day_loss=0.02,
            quote_coverage=0.96, fill_rate=0.90,
        ),
        FoldResult(
            fold_id="f2",
            net_return=-0.01, max_drawdown=0.06, turnover=0.1,
            concentration=0.05, n_trades=20, worst_day_loss=0.03,
            quote_coverage=0.92, fill_rate=0.88,
        ),
    ]


def test_compute_objective_emits_objective_terms() -> None:
    """ObjectiveResult.objective_terms carries every term contribution."""
    result = compute_objective(_toy_folds())
    terms = result.objective_terms
    # Positive driver.
    assert "median_net_return" in terms
    # Every default penalty key is in the breakdown.
    for key in ("drawdown", "cvar", "turnover", "concentration",
                "low_trade_count", "missing_quote", "missing_coverage",
                "fill_rate", "fold_variance"):
        assert key in terms, f"missing objective term {key!r}"
    # Reporting fields.
    assert "objective" in terms
    assert "median_fold_score" in terms
    # The reported objective in objective_terms matches the result.
    assert terms["objective"] == result.objective
    assert terms["median_fold_score"] == result.median_fold_score


def test_objective_terms_breakdown_decomposes_to_objective() -> None:
    """median_fold_score - fold_variance penalty ≈ objective (the reported decomposition)."""
    result = compute_objective(_toy_folds())
    decomposed = result.median_fold_score - result.objective_terms["fold_variance"]
    assert abs(decomposed - result.objective) < 1e-12


def test_walkforward_objective_persists_terms_to_user_attrs() -> None:
    """``make_walkforward_objective`` writes objective_terms to trial.user_attrs."""
    from bowaka_v2_lab.optuna.walkforward_runner import make_walkforward_objective

    captured = {}

    def fake_folds(*_args, **_kwargs):
        return _toy_folds()

    # Build a study + run one trial against a stubbed fold runner so we can
    # observe the trial.user_attrs the wrapper writes.
    study = optuna.create_study(direction="maximize",
                                sampler=optuna.samplers.TPESampler(seed=1337))

    import bowaka_v2_lab.optuna.walkforward_runner as wfr

    # Replace _run_validation_folds with a stub that returns our toy folds —
    # so the test never touches a real lake or runs a real backtest.
    orig = wfr._run_validation_folds
    wfr._run_validation_folds = fake_folds

    class _FakePaths: pass

    class _FakeGuard:
        def assert_can_read(self, *_a, **_kw): pass

    try:
        objective = make_walkforward_objective(
            base_cfg={}, plan=None, lake_root="/lake", feed="iex",
            symbols=["AAA"], paths=_FakePaths(), holdout_guard=_FakeGuard(),
            log=__import__("logging").getLogger("test"),
            dataset_hash="ds", config_hash="cfg", code_hash="code",
        )

        def capture_objective(trial: optuna.Trial) -> float:
            v = objective(trial)
            captured["user_attrs"] = dict(trial.user_attrs)
            return v

        study.optimize(capture_objective, n_trials=1)
    finally:
        wfr._run_validation_folds = orig

    ua = captured["user_attrs"]
    assert "objective_terms" in ua, "trial.user_attrs is missing 'objective_terms'"
    # Lineage user_attrs (audit §P1-005) are persisted per-trial too.
    assert ua.get("dataset_hash") == "ds"
    assert ua.get("config_hash") == "cfg"
    assert ua.get("code_hash") == "code"

    terms = ua["objective_terms"]
    # Every default penalty key is present in the per-trial breakdown.
    for key in ("drawdown", "cvar", "turnover", "concentration",
                "low_trade_count", "missing_quote", "missing_coverage",
                "fill_rate", "fold_variance", "median_net_return"):
        assert key in terms
