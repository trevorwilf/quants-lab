"""Diagnostic: cProfile ONE validation fold on the real matrix path.

Builds a single FoldRuntimeContext (with the read-only scan-matrix store) the
same way run_walkforward_study does, then times + cProfiles
``_run_fold_backtest_objective`` for that one fold. NO Optuna study, NO storage
writes — safe to run alongside a live study (1 core). Reports the warm
(un-profiled) fold wall-clock + the cumulative/total function breakdown so we
can see what actually dominates the per-trial-per-fold cost now.

    PYTHONPATH=research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src \
      python research_notebooks/bowaka_v2_lab/scripts/_profile_one_fold.py \
      research_notebooks/bowaka_v2_lab/configs/_local_container_matrix.yml [split_index]
"""
from __future__ import annotations

import cProfile
import io
import pstats
import sys
import time

from bowaka_v2_lab.config import BowakaV2Paths, SimulationConfig, load_config
from bowaka_v2_lab.data.lineage import resolve_lake_root
from bowaka_v2_lab.optuna.fold_context import _build_one_fold_context
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits
from bowaka_v2_lab.optuna.walkforward_runner import (
    _REPO_ROOT,
    _resolve_symbols,
    _run_fold_backtest_objective,
    _to_date,
)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    config_path = sys.argv[1]
    split_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    cfg = load_config(config_path)
    paths = BowakaV2Paths.from_config(cfg, repo_root=_REPO_ROOT)
    optuna_cfg = cfg.get("optuna", {}) or {}
    wf = optuna_cfg.get("walkforward", {}) or {}
    bt = cfg.get("backtest", {}) or {}
    md = cfg.get("market_data", {}) or {}
    sim_cfg = SimulationConfig.model_validate(cfg.get("simulation") or {})

    plan = build_walkforward_splits(
        full_start=_to_date(bt["start_date"]),
        full_end=_to_date(bt["end_date"]),
        train_months=int(wf.get("train_months", 6)),
        val_months=int(wf.get("val_months", 1)),
        final_holdout_months=int(wf.get("final_holdout_months", 1)),
    )
    feed = str(md.get("feed", "iex"))
    lake_root = resolve_lake_root(cfg)
    symbols = _resolve_symbols(cfg, md, sim_mode=sim_cfg.mode, plan=plan)
    holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    cached_suppliers_flag = bool(optuna_cfg.get("cached_suppliers", False))

    split = plan.splits[split_index]
    accel = (optuna_cfg.get("acceleration") or {})
    print(f"config           : {config_path}")
    print(f"n_splits         : {len(plan.splits)}  (profiling split {split_index})")
    print(f"fold window      : {split.val_start} .. {split.val_end}")
    print(f"feed/symbols     : {feed} / {len(symbols)} symbols")
    print(f"cached_suppliers : {cached_suppliers_flag}")
    print(f"accel flags      : matrix={((accel.get('scan_matrix') or {}).get('runtime_mode'))} "
          f"batch_daily={((accel.get('batch_daily_cache') or {}).get('enabled'))} "
          f"sess_window={((accel.get('session_minute_window_cache') or {}).get('enabled'))} "
          f"startup_dq={((accel.get('startup_dq_cache') or {}).get('enabled'))}", flush=True)

    t0 = time.perf_counter()
    ctx = _build_one_fold_context(
        fold_id=f"f{split_index}", val_start=split.val_start, val_end=split.val_end,
        base_cfg=cfg, lake_root=lake_root, feed=feed, symbols=tuple(symbols),
        paths=paths, holdout_guard=holdout_guard,
        cached_suppliers=cached_suppliers_flag, scope="validation",
    )
    print(f"ctx build        : {time.perf_counter() - t0:.1f}s  "
          f"sessions={len(ctx.sessions) if ctx else 0}  "
          f"matrix_store={'yes' if (ctx and ctx.scan_matrix_store is not None) else 'NO'}  "
          f"startup_dq_cached={'yes' if (ctx and ctx.startup_dq_report is not None) else 'no'}",
          flush=True)
    if ctx is None:
        print("empty fold window — pick another split_index")
        return 2

    def _run():
        return _run_fold_backtest_objective(
            cfg, val_start=split.val_start, val_end=split.val_end,
            lake_root=lake_root, feed=feed, symbols=symbols, paths=paths, ctx=ctx,
        )

    # Warm run (loads matrix sessions into the store cache) + the REAL fold wall.
    t0 = time.perf_counter()
    r0 = _run()
    warm = time.perf_counter() - t0
    nt = getattr(r0, "n_trades", None)
    if nt is None and r0 is not None:
        nt = len(getattr(r0, "trades", []) or [])
    print(f"WARM fold run    : {warm:.1f}s  n_trades={nt}", flush=True)

    # Second warm to confirm steady-state (matrix cached now).
    t0 = time.perf_counter()
    _run()
    warm2 = time.perf_counter() - t0
    print(f"WARM fold run #2 : {warm2:.1f}s  (steady-state, matrix cached)", flush=True)

    # Profiled run.
    pr = cProfile.Profile()
    pr.enable()
    _run()
    pr.disable()
    print(f"\n(cProfile inflates absolute time ~2x; read the RELATIVE shares)\n")

    buf = io.StringIO()
    st = pstats.Stats(pr, stream=buf)
    st.sort_stats("cumulative")
    buf.write("===== TOP 35 by CUMULATIVE time =====\n")
    st.print_stats(35)
    st.sort_stats("tottime")
    buf.write("\n===== TOP 30 by TOTAL (self) time =====\n")
    st.print_stats(30)
    print(buf.getvalue())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
