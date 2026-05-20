"""Build notebook 10 — Optuna walk-forward."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _notebook_common import make_notebook, write_notebook  # noqa: E402


HERE = Path(__file__).resolve().parent


def main() -> None:
    nb = make_notebook([
        {"type": "code", "source": (
            "# Papermill parameter cell.\n"
            "CONFIG_PATH = 'research_notebooks/bowaka_v2_lab/configs/bowaka_v2_walkforward_optuna.yml'\n"
            "N_TRIALS = 5  # smoke; raise to 200+ for real runs\n"
        )},
        {"type": "markdown", "source": "# 10 — Optuna Walk-Forward\n\nRuns a small TPE study against the SIP config."},
        {"type": "code", "source": (
            "import optuna\n"
            "from bowaka_v2_lab.optuna.dispatcher import OptunaStudy\n"
            "from bowaka_v2_lab.optuna.search_space import suggest_params\n"
            "from bowaka_v2_lab.optuna.objective import compute_objective, FoldResult\n"
            "study = OptunaStudy(feed='sip', cost_stress='conservative',\n"
            "                      dataset_hash='cafebabecafebabe', config_hash='deadbeefdeadbeef',\n"
            "                      n_trials=N_TRIALS)\n"
            "study.create()\n"
            "\n"
            "def objective(trial):\n"
            "    params = suggest_params(trial)\n"
            "    # Synthetic single-fold: penalise extreme params.\n"
            "    fold = FoldResult(fold_id='f0',\n"
            "        net_return=0.01 - abs(params['signals.gap_pct_max'] - 0.10) * 0.1,\n"
            "        max_drawdown=0.02, turnover=0.0, concentration=0.0,\n"
            "        n_trades=8, ambiguous_bar_count=0, missing_quote_count=0)\n"
            "    return compute_objective([fold]).objective\n"
            "\n"
            "study.optimize(objective)\n"
            "print('best value:', study.study.best_value)\n"
            "print('best params:', study.study.best_params)\n"
        )},
    ])
    write_notebook(nb, HERE / "10_optuna_walkforward.ipynb")
    print("Built 10_optuna_walkforward.ipynb")


if __name__ == "__main__":
    main()
