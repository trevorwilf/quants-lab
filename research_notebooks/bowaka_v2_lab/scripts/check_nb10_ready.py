"""Notebook-10 launch-readiness check (weekly automation STEP 5).

Proves — right after the Friday refresh + matrix rebuild — that
``10_optuna_walkforward.ipynb`` would clear every launch gate, instead of the
operator discovering a blocker at study start days later. Mirrors the gate
chain of ``run_walkforward_study`` without starting a study:

  1. frozen contract available + config↔contract PARITY
     (catches: contract re-mirrored but the hand-tuned study config not
     reconciled — the 2026-07-07 OptunaParityError)
  2. no MATRICES_STALE.flag breadcrumb
  3. scan-matrix store present, covering every fold-val session of the
     auto-anchored window, and FRESH vs the current lake
     (catches: lake refreshed without a matrix rebuild)
  4. OPTUNA_STORAGE reachable (WARN-only: an unset var falls back to SQLite)

Run inside the ql-jupyter container from the lab dir:
    PYTHONPATH=src:../bowaka_common/src MARKET_DATA_ROOT=/opt/market_data_cache \
        python scripts/check_nb10_ready.py [--config configs/_fastrealism_study.yml]

Exit 0 = READY; exit 1 = NOT READY (each failed check printed).
"""

from __future__ import annotations

import argparse
import sys
import traceback


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/_fastrealism_study.yml")
    args = ap.parse_args()

    failures: list[str] = []
    warnings: list[str] = []

    def check(name: str, fn) -> None:
        try:
            fn()
            print(f"[nb10-ready] PASS  {name}")
        except Exception as e:  # noqa: BLE001 — every gate failure is reported
            print(f"[nb10-ready] FAIL  {name}: {e}")
            failures.append(f"{name}: {e}")

    # --- resolve exactly like notebook 10 --------------------------------
    from bowaka_v2_lab.config.loader import load_config
    from bowaka_v2_lab.optuna.autoconfig import resolve_walkforward_config

    declared = (load_config(args.config).get("simulation") or {}).get("mode")
    kwargs = {"feed_override": "auto", "out_path": "/tmp/_nb10_ready_resolved.yml"}
    if declared == "fast_realism":
        kwargs["mode_override"] = "fast_realism"
    try:
        resolved = resolve_walkforward_config(args.config, **kwargs)
    except Exception as e:  # noqa: BLE001
        print(f"[nb10-ready] FAIL  config resolution: {e}")
        traceback.print_exc()
        return 1
    cfg = load_config("/tmp/_nb10_ready_resolved.yml")
    cfg["_source_path"] = str(args.config)
    print(f"[nb10-ready] resolved {args.config}: feed={resolved.feed} "
          f"mode={resolved.mode} tier={resolved.tier}")

    # --- 1. contract parity (the 2026-07-07 OptunaParityError) -----------
    def _parity():
        from bowaka_v2_lab.optuna.walkforward_runner import assert_optuna_config_parity
        from bowaka_v2_lab.reference import contract_available

        if not contract_available():
            raise RuntimeError("frozen contract unavailable on this host")
        assert_optuna_config_parity(cfg)

    check("contract parity gate", _parity)

    # --- 2. stale-flag breadcrumb ----------------------------------------
    def _flag():
        from bowaka_v2_lab.scanner.scan_matrix import assert_no_stale_matrix_flag

        assert_no_stale_matrix_flag()

    check("no MATRICES_STALE.flag", _flag)

    # --- 3. scan-matrix freshness over the fold-val sessions --------------
    def _matrix():
        from bowaka_v2_lab.optuna.fold_context import (
            _open_fold_scan_matrix_store, calendar_sessions_half_open,
        )
        from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits
        from bowaka_v2_lab.optuna.walkforward_runner import _to_date
        from bowaka_v2_lab.scanner.scan_matrix import (
            assert_scan_matrix_fresh, resolve_scan_matrix_store_root,
        )
        from bowaka_v2_lab.scanner.scan_matrix_runtime import resolve_runtime_mode

        sm_cfg = ((cfg.get("optuna") or {}).get("acceleration") or {}).get("scan_matrix") or {}
        if not bool(sm_cfg.get("enabled", False)):
            raise RuntimeError(
                "scan_matrix acceleration is DISABLED in the resolved config — "
                "a study would run ~15x slower on the legacy scanner"
            )
        if resolve_runtime_mode(cfg) not in ("compatibility", "vectorized"):
            raise RuntimeError(
                f"scan_matrix runtime_mode={sm_cfg.get('runtime_mode')!r} inactive"
            )
        store = _open_fold_scan_matrix_store(cfg, "validation")
        if store is None:
            raise RuntimeError(
                "validation scan-matrix store could not be opened at "
                f"{resolve_scan_matrix_store_root(sm_cfg, 'validation')}"
            )
        bt = cfg.get("backtest") or {}
        wf = (cfg.get("optuna") or {}).get("walkforward") or {}
        plan = build_walkforward_splits(
            full_start=_to_date(bt["start_date"]),
            full_end=_to_date(bt["end_date"]),
            train_months=int(wf.get("train_months", 6)),
            val_months=int(wf.get("val_months", 1)),
            final_holdout_months=int(wf.get("final_holdout_months", 1)),
            step_months=(int(wf["step_months"]) if wf.get("step_months") else None),
        )
        required: list = []
        for s in plan.splits:
            required.extend(calendar_sessions_half_open(s.val_start, s.val_end))
        assert_scan_matrix_fresh(
            cfg, store,
            resolve_scan_matrix_store_root(sm_cfg, "validation"),
            required_sessions=required,
        )
        print(f"[nb10-ready]       matrix covers all {len(required)} fold-val "
              f"sessions and matches the current lake")

    check("scan-matrix freshness (validation)", _matrix)

    # --- 4. Optuna storage (warn-only) ------------------------------------
    import os
    storage = os.environ.get("OPTUNA_STORAGE", "")
    if storage:
        try:
            import sqlalchemy

            eng = sqlalchemy.create_engine(storage, connect_args={"connect_timeout": 5})
            with eng.connect():
                pass
            print("[nb10-ready] PASS  OPTUNA_STORAGE reachable")
        except Exception as e:  # noqa: BLE001
            warnings.append(f"OPTUNA_STORAGE unreachable: {e}")
            print(f"[nb10-ready] WARN  OPTUNA_STORAGE unreachable: {e}")
    else:
        warnings.append("OPTUNA_STORAGE not set (SQLite fallback; n_jobs>1 unavailable)")
        print("[nb10-ready] WARN  OPTUNA_STORAGE not set (SQLite fallback)")

    if failures:
        print(f"[nb10-ready] NOT READY — {len(failures)} gate(s) would refuse "
              "notebook 10:")
        for f in failures:
            print(f"[nb10-ready]   - {f}")
        return 1
    print("[nb10-ready] READY — notebook 10 would clear every launch gate."
          + (f" ({len(warnings)} warning(s))" if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
