"""Build ``notebooks/10_optuna_walkforward.ipynb``.

Smoke-only Optuna run (default 20 trials). Real walk-forward studies should
run via QuantLab task runner against Postgres-backed Optuna storage.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

from _notebook_common import BOOTSTRAP, code_cell, finalize, md_cell

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "10_optuna_walkforward.ipynb"


TITLE = """# 10 — Optuna walk-forward smoke

**Default is a 20-trial smoke run** to sanity-check the search space and
objective. Production walk-forward studies that run for hours-to-days
should go through ``make run-task config=bowaka_lab_tasks.yml`` against a
Postgres-backed Optuna storage URL — not this notebook.

Saves ``optuna_trials.parquet`` and ``optuna_best.json`` for the weekly
report aggregator.
"""


PARAMETERS = '''import os

RUN_ID         = "bt_iex_default"
ARTIFACTS_ROOT = "research_notebooks/bowaka_lab/artifacts"
N_TRIALS       = 20            # smoke; bump for real runs via run-task
STUDY_NAME     = f"bowaka_smoke_{RUN_ID}"
STORAGE_URL    = None          # None = in-memory sqlite; use postgres for production
REBUILD        = False
'''


DERIVED = '''from pathlib import Path

import optuna
import pandas as pd

from bowaka_lab.optuna.search_space import suggest_params
from bowaka_lab.utils import (
    ArtifactPaths,
    artifact_exists,
    load_json,
    load_parquet,
    save_json,
    save_parquet,
)


artifacts_root = Path(ARTIFACTS_ROOT) if Path(ARTIFACTS_ROOT).is_absolute() else (repo_root / ARTIFACTS_ROOT).resolve()
paths = ArtifactPaths.for_run(RUN_ID, artifacts_root)
paths.ensure_dir()
assert paths.candidates.exists(), (
    f"candidates missing: {paths.candidates} — run notebook 03 first."
)

print(f"artifacts:  {paths.root}")
print(f"trials:     {N_TRIALS}")
print(f"storage:    {'in-memory sqlite' if STORAGE_URL is None else STORAGE_URL}")
'''


SEARCH_OBJECTIVE = '''# Synthetic objective: rewards parameters that score well on a cheap proxy
# (median signal_strength × candidate count). Real walk-forward objectives
# replay the backtester against held-out folds — that lives in
# bowaka_lab.optuna.objective and runs via the task runner.
#
# The objective itself is a small library helper so the notebook cell stays
# orchestration-only (no def at cell scope).
from bowaka_lab.optuna.objective import smoke_objective_from_candidates

candidates = load_parquet(paths.candidates)
objective = smoke_objective_from_candidates(candidates)
print(f"smoke objective bound to {candidates.shape[0]:,} candidate rows")
'''


RUN_STUDY = '''trials_df = None
best_payload = None

if not REBUILD and artifact_exists(paths, "optuna_trials") and artifact_exists(paths, "optuna_best"):
    print("Fast path: optuna artifacts exist; loading.")
    trials_df = load_parquet(paths.optuna_trials)
    best_payload = load_json(paths.optuna_best)
else:
    sampler = optuna.samplers.TPESampler(seed=42)
    storage = STORAGE_URL
    study = optuna.create_study(
        study_name=STUDY_NAME,
        direction="maximize",
        storage=storage,
        load_if_exists=True if storage else False,
        sampler=sampler,
    )
    study.optimize(objective, n_trials=N_TRIALS, n_jobs=1)

    # Materialise the trial table — params + value + state.
    rows = []
    for t in study.trials:
        row = {"trial_number": t.number, "objective_value": t.value,
               "state": str(t.state).split(".")[-1]}
        row.update({f"param_{k}": v for k, v in (t.params or {}).items()})
        rows.append(row)
    trials_df = pd.DataFrame(rows)
    save_parquet(paths.optuna_trials, trials_df)

    best_payload = {
        "study_name": STUDY_NAME,
        "n_trials": len(study.trials),
        "best_value": study.best_value if study.trials else None,
        "best_params": study.best_params if study.trials else {},
    }
    save_json(paths.optuna_best, best_payload)
    print(f"wrote {paths.optuna_trials}")
    print(f"wrote {paths.optuna_best}")

print(f"completed trials: {trials_df.shape[0]}")
print("best:")
print(best_payload)
'''


DIAGNOSTICS = '''top = trials_df.sort_values("objective_value", ascending=False).head(10)
try:
    from IPython.display import display
    display(top)
except Exception:
    print(top.to_string(index=False))
'''


PLOTS = '''try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

if plt is not None and not trials_df.empty:
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(trials_df["trial_number"], trials_df["objective_value"], marker="o", linewidth=1)
    ax.set_title(f"Optimization history — {STUDY_NAME}")
    ax.set_xlabel("trial")
    ax.set_ylabel("objective_value")
    fig.tight_layout()
    plt.show()
'''


NEXT = """## Next

Run **`notebooks/11_weekly_research_report.ipynb`** to aggregate everything
into the final Markdown + JSON report."""


def main() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        md_cell(TITLE),
        code_cell(BOOTSTRAP, tag="bootstrap"),
        md_cell("## Configuration"),
        code_cell(PARAMETERS, tag="parameters"),
        md_cell("## Derived paths"),
        code_cell(DERIVED, tag="derived"),
        md_cell("## Search space + objective"),
        code_cell(SEARCH_OBJECTIVE, tag="objective"),
        md_cell("## Run smoke study"),
        code_cell(RUN_STUDY, tag="run_study"),
        md_cell("## Top-K trials"),
        code_cell(DIAGNOSTICS, tag="diagnostics"),
        md_cell("## Optimization-history plot"),
        code_cell(PLOTS, tag="plots"),
        md_cell(NEXT),
    ]
    finalize(nb)
    nbformat.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}")


if __name__ == "__main__":
    main()
