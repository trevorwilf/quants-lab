"""Build ``notebooks/10_optuna_walkforward.ipynb``.

The notebook has two modes:

- ``MODE = "smoke"`` -- 20 trials, serial, in-memory SQLite. Sanity-check for
  search-space + objective.
- ``MODE = "production"`` -- N trials, process-parallel, PostgreSQL-backed.
  Reads ``OPTUNA_STORAGE`` from the env (set by the docker stack).

Production runs are picked up by the Optuna dashboard at http://localhost:8080.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

from _notebook_common import BOOTSTRAP, code_cell, finalize, md_cell

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "10_optuna_walkforward.ipynb"


TITLE = """# 10 -- Optuna walk-forward

Two modes, selected via the ``MODE`` parameter:

- **smoke** -- 20 trials, serial, in-memory SQLite. Use this to sanity-check
  the search space and objective before a real run. Completes in seconds.
- **production** -- many trials, process-parallel, PostgreSQL-backed. Reads
  ``OPTUNA_STORAGE`` from the env (the docker stack injects this in the
  Jupyter container; from the host use ``localhost:5433``). Trials stream
  into the Optuna dashboard at http://localhost:8080.

Saves ``optuna_trials.parquet`` and ``optuna_best.json`` for the weekly
report aggregator.
"""


PARAMETERS = '''# --- Mode ---------------------------------------------------
MODE = "smoke"   # "smoke" (in-notebook, 20 trials, sqlite) or "production" (postgres, n_trials big)

# --- Run identification -------------------------------------
RUN_ID     = "bt_iex_default"
STUDY_NAME = None      # None -> auto-derived from MODE + RUN_ID

# --- Smoke mode ---------------------------------------------
SMOKE_N_TRIALS = 20
SMOKE_N_JOBS   = 1     # sqlite cannot do multi-worker safely

# --- Production mode ----------------------------------------
PROD_N_TRIALS         = 500
PROD_N_JOBS           = 4    # process-parallel workers; requires postgres
PROD_STRICT_PARALLEL  = True # raise on misconfig instead of falling back

ARTIFACTS_ROOT = "research_notebooks/bowaka_lab/artifacts"
REBUILD        = False
'''


DERIVED = '''from pathlib import Path

import pandas as pd

from bowaka_lab.optuna import (
    DegeneracyCheckCallback,
    TrialLoggingCallback,
    get_storage_url,
    optimize_study_for_notebook,
    print_environment,
)
from bowaka_lab.optuna.objective import smoke_objective_factory_from_candidates_path
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
    f"candidates missing: {paths.candidates} -- run notebook 03 first."
)

print_environment()
print(f"artifacts:  {paths.root}")
print(f"candidates: {paths.candidates}")
'''


MODE_DISPATCH = '''if MODE == "smoke":
    storage_url     = None                       # in-memory sqlite via create_study default
    n_trials        = SMOKE_N_TRIALS
    n_jobs          = SMOKE_N_JOBS
    strict_parallel = False
elif MODE == "production":
    storage_url     = get_storage_url()          # reads OPTUNA_STORAGE
    n_trials        = PROD_N_TRIALS
    n_jobs          = PROD_N_JOBS
    strict_parallel = PROD_STRICT_PARALLEL
else:
    raise ValueError(f"Unknown MODE: {MODE!r}")

study_name = STUDY_NAME if STUDY_NAME else f"bowaka_{MODE}_{RUN_ID}"
print(f"MODE={MODE}  n_trials={n_trials}  n_jobs={n_jobs}  study_name={study_name}")
print(f"storage:    {'in-memory sqlite' if storage_url is None else storage_url}")
'''


RUN_STUDY = '''trials_df = None
best_payload = None

if not REBUILD and artifact_exists(paths, "optuna_trials") and artifact_exists(paths, "optuna_best"):
    print("Fast path: optuna artifacts exist; loading.")
    trials_df = load_parquet(paths.optuna_trials)
    best_payload = load_json(paths.optuna_best)
else:
    study = optimize_study_for_notebook(
        study_name=study_name,
        storage_url=storage_url,
        n_trials=n_trials,
        n_jobs=n_jobs,
        objective_factory=smoke_objective_factory_from_candidates_path,
        factory_kwargs={"candidates_path": str(paths.candidates)},
        callbacks=[TrialLoggingCallback(log_every=5), DegeneracyCheckCallback()],
        strict_parallel=strict_parallel,
    )

    # Materialise the trial table -- params + value + state.
    rows = []
    for t in study.trials:
        row = {"trial_number": t.number, "objective_value": t.value,
               "state": str(t.state).split(".")[-1]}
        row.update({f"param_{k}": v for k, v in (t.params or {}).items()})
        rows.append(row)
    trials_df = pd.DataFrame(rows)
    save_parquet(paths.optuna_trials, trials_df)

    completed = [t for t in study.trials if t.value is not None]
    best_payload = {
        "study_name": study_name,
        "n_trials": len(study.trials),
        "best_value": study.best_value if completed else None,
        "best_params": study.best_params if completed else {},
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
    ax.set_title(f"Optimization history -- {study_name}")
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
        md_cell("## Mode dispatch"),
        code_cell(MODE_DISPATCH, tag="mode_dispatch"),
        md_cell("## Run study"),
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
