"""Headless Optuna walk-forward runner.

Usage::

    python scripts/run_optuna_walkforward.py \\
        --run-id bt_iex_default \\
        --n-trials 500 \\
        --n-jobs 4 \\
        --study-name bowaka_prod_bt_iex_default_v1

Requires ``OPTUNA_STORAGE`` pointing at PostgreSQL. Exits non-zero with a
clear error if the storage URL is missing or points at SQLite.

The YAML at ``configs/bowaka_optuna_walkforward.yml`` is currently not read
by this script -- it is intended for the QuantLab task runner integration
(a future prompt). CLI args take precedence today.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    here = Path(__file__).resolve()
    bowaka_root = here.parent.parent  # scripts/.. == bowaka_lab/
    src = bowaka_root / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))


_ensure_src_on_path()

from bowaka_lab.optuna import (  # noqa: E402
    DegeneracyCheckCallback,
    TrialLoggingCallback,
    get_storage_url,
    optimize_study_for_notebook,
    print_environment,
    require_postgres,
)
from bowaka_lab.optuna.objective import (  # noqa: E402
    smoke_objective_factory_from_candidates_path,
)
from bowaka_lab.utils import (  # noqa: E402
    ArtifactPaths,
    save_json,
    save_parquet,
)
from bowaka_lab.utils.env import load_project_dotenv  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(
        description="Headless Optuna walk-forward runner (PostgreSQL-backed).",
    )
    p.add_argument("--run-id", required=True, help="ArtifactPaths run id")
    p.add_argument("--n-trials", type=int, default=500)
    p.add_argument("--n-jobs", type=int, default=4)
    p.add_argument(
        "--artifacts-root",
        default="research_notebooks/bowaka_lab/artifacts",
    )
    p.add_argument("--study-name", default=None)
    p.add_argument("--no-strict-parallel", action="store_true", default=False)
    args = p.parse_args()

    load_project_dotenv()

    print_environment()

    try:
        storage_url = require_postgres(get_storage_url())
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(
            "Production walk-forward runs require PostgreSQL. "
            "Set OPTUNA_STORAGE to e.g. "
            "'postgresql+psycopg2://optuna:optuna@localhost:5433/optuna'.",
            file=sys.stderr,
        )
        return 2

    artifacts_root = Path(args.artifacts_root).resolve()
    paths = ArtifactPaths.for_run(args.run_id, artifacts_root)
    paths.ensure_dir()
    if not paths.candidates.exists():
        print(
            f"ERROR: candidates missing: {paths.candidates}\n"
            f"Run notebook 03 (or your candidates pipeline) first.",
            file=sys.stderr,
        )
        return 3

    study_name = args.study_name or f"bowaka_prod_{args.run_id}_v1"
    strict_parallel = not args.no_strict_parallel

    study = optimize_study_for_notebook(
        study_name=study_name,
        storage_url=storage_url,
        n_trials=args.n_trials,
        n_jobs=args.n_jobs,
        objective_factory=smoke_objective_factory_from_candidates_path,
        factory_kwargs={"candidates_path": str(paths.candidates)},
        callbacks=[TrialLoggingCallback(log_every=10), DegeneracyCheckCallback()],
        strict_parallel=strict_parallel,
    )

    rows = []
    for t in study.trials:
        row = {
            "trial_number": t.number,
            "objective_value": t.value,
            "state": str(t.state).split(".")[-1],
        }
        row.update({f"param_{k}": v for k, v in (t.params or {}).items()})
        rows.append(row)

    import pandas as pd

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

    print(f"\nStudy: {study_name}")
    print(f"Trials: {len(study.trials)}")
    if completed:
        print(f"Best value: {study.best_value}")
    else:
        print("Best value: n/a (no completed trials)")
    print(f"Wrote: {paths.optuna_trials}")
    print(f"Wrote: {paths.optuna_best}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
