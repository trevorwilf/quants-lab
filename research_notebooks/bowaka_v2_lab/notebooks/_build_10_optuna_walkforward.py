"""Build notebook 10 — real walk-forward Optuna optimization."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _notebook_common import make_notebook, write_notebook  # noqa: E402

HERE = Path(__file__).resolve().parent


def main() -> None:
    nb = make_notebook([
        {"type": "code", "source": (
            "# Papermill parameters.\n"
            "CONFIG_PATH = 'research_notebooks/bowaka_v2_lab/configs/bowaka_v2_walkforward_optuna.yml'\n"
            "N_TRIALS = None          # None -> optuna.n_trials from the config; or set an integer\n"
            "N_STARTUP_TRIALS = None  # None -> optuna.n_startup_trials; random trials before TPE\n"
            "ALLOW_SMOKE = False      # True -> permit optimization on a smoke_fixture config\n"
        )},
        {"type": "markdown", "source": (
            "# 10 — Walk-Forward Optuna\n\n"
            "Runs a **real** walk-forward parameter optimization against the shared\n"
            "market-data lake. Each Optuna trial samples a parameter set, applies it\n"
            "to the config, and runs a real backtest over every walk-forward\n"
            "validation window; the trial objective is the median fold score. The\n"
            "final-holdout window is never read during tuning.\n\n"
            "**Parameters:** `N_TRIALS` is the total trial count (`None` -> the\n"
            "config's `optuna.n_trials`). `N_STARTUP_TRIALS` is how many of those are\n"
            "random-sampling trials before TPE-guided search begins (`None` -> the\n"
            "config's `optuna.n_startup_trials`).\n\n"
            "**Compute:** a run is `N_TRIALS` x `n_folds` real backtests — the config\n"
            "default (2500 trials) is a multi-day job. Set a small `N_TRIALS` and a\n"
            "focused `universe.symbols` for a quick run."
        )},
        {"type": "code", "source": (
            "import json\n"
            "from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study\n"
            "result = run_walkforward_study(CONFIG_PATH, n_trials=N_TRIALS,\n"
            "  n_startup_trials=N_STARTUP_TRIALS, allow_smoke=ALLOW_SMOKE)\n"
            "print(json.dumps(result, indent=2, default=str))\n"
        )},
    ])
    write_notebook(nb, HERE / "10_optuna_walkforward.ipynb")
    print("Built 10_optuna_walkforward.ipynb")


if __name__ == "__main__":
    main()
