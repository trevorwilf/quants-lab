"""Realism remediation 3 closing-check reproduction (audit §1.3).

Pre-remediation: the tiny-lake walk-forward study would complete with
``status: "ok"`` and ``best_value: -1.0e9`` (the sentinel score). Post-
remediation: either a real (non-sentinel) ``best_value`` or
``OptunaStudyInvalidError`` is raised. The forbidden outcome is the old
``status=ok, best_value=-1e9`` combination.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import tempfile
from pathlib import Path


def main() -> int:
    from bowaka_v2_lab.devtools.wf_lake import (
        build_tiny_lake,
        write_walkforward_test_config,
    )
    from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
    from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study

    lab_root = Path.cwd()
    tmp = Path(tempfile.mkdtemp())
    lake = tmp / "lake"
    build_tiny_lake(
        lake, ["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
    )
    cfg = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp / "wf.yml", lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=2,
    )
    try:
        r = run_walkforward_study(cfg, allow_smoke=True)
    except OptunaStudyInvalidError as e:
        print("OK (study invalid as expected for trivial lake):", e)
        return 0
    assert r["status"] == "ok", f"unexpected status: {r['status']}"
    assert r["best_value"] > -1e9 + 1e-6, (
        f"sentinel leaked through: {r['best_value']}"
    )
    summary = {
        "status": r["status"],
        "best_value": r["best_value"],
        "n_folds": r["n_folds"],
        "n_trials_completed": r["n_trials_completed"],
        "best_params_keys": sorted(r["best_params"].keys()),
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
