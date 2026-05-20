"""5-trial run on a synthetic fixture completes."""
from __future__ import annotations

import optuna

from bowaka_v2_lab.optuna.dispatcher import OptunaStudy
from bowaka_v2_lab.optuna.objective import FoldResult, compute_objective
from bowaka_v2_lab.optuna.search_space import suggest_params


def test_optuna_dispatcher_short_run() -> None:
    s = OptunaStudy(feed="sip", cost_stress="conservative",
                     dataset_hash="cafebabecafebabe",
                     config_hash="deadbeefdeadbeef",
                     storage_uri=None, n_trials=5)
    s.create()

    def obj(trial: optuna.Trial) -> float:
        params = suggest_params(trial)
        f = FoldResult(fold_id="f0",
                        net_return=0.01 - abs(params["signals.gap_pct_max"] - 0.10) * 0.1,
                        max_drawdown=0.02, turnover=0.0, concentration=0.0,
                        n_trades=20, ambiguous_bar_count=0, missing_quote_count=0)
        return compute_objective([f]).objective

    s.optimize(obj)
    assert s.study.best_value is not None
