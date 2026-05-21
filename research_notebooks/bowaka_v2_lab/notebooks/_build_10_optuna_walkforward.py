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
            "N_TRIALS = 20  # bounded first run; set None to use optuna.n_trials from the config\n"
        )},
        {"type": "markdown", "source": (
            "# 10 — Walk-Forward Optuna\n\n"
            "Runs a **real** walk-forward parameter optimization against the shared\n"
            "market-data lake. Each Optuna trial samples a parameter set, applies it\n"
            "to the config, and runs a real backtest over every walk-forward\n"
            "validation window; the trial objective is the median fold score. The\n"
            "final-holdout window is never read during tuning.\n\n"
            "**Compute:** each run is `N_TRIALS` x `n_folds` real backtests. `N_TRIALS`\n"
            "defaults to **20** — a bounded, multi-hour run (TPE does ~10 random then\n"
            "~10 guided trials). Raise it, or set `N_TRIALS = None` to use the\n"
            "config's `optuna.n_trials`, for a deeper search. Set `universe.symbols`\n"
            "in the config to bound the universe (otherwise it is the lake's\n"
            "symbols, capped at 100)."
        )},
        {"type": "code", "source": (
            "import json\n"
            "from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study\n"
            "result = run_walkforward_study(CONFIG_PATH, n_trials=N_TRIALS)\n"
            "print(json.dumps(result, indent=2, default=str))\n"
        )},
    ])
    write_notebook(nb, HERE / "10_optuna_walkforward.ipynb")
    print("Built 10_optuna_walkforward.ipynb")


if __name__ == "__main__":
    main()
