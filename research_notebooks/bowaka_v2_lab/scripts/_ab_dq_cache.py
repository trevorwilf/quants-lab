"""A/B objective-parity test for the startup_dq_cache fix.

Builds one real fold context, then runs the SAME fold two ways:
  * baseline  — DQ cache forced OFF (startup_dq_report=None) → full rebuild,
                the current always-miss behaviour;
  * fixed     — DQ cache ON → with the symbols_hash fix it now HITS.

Asserts the FoldResult (the objective inputs: net_return, max_drawdown,
turnover, concentration, n_trades, ...) is byte-identical between the two, and
reports both fold wall-clocks (baseline ~full DQ; fixed should collapse if the
cache hits). Identical FoldResult => the fix does not change the objective.
"""
from __future__ import annotations

import dataclasses
import sys
import time

from bowaka_v2_lab.config import BowakaV2Paths, SimulationConfig, load_config
from bowaka_v2_lab.data.lineage import resolve_lake_root
from bowaka_v2_lab.optuna.fold_context import _build_one_fold_context
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
from bowaka_v2_lab.optuna.objective import fold_result_from_backtest_result
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
        full_start=_to_date(bt["start_date"]), full_end=_to_date(bt["end_date"]),
        train_months=int(wf.get("train_months", 6)), val_months=int(wf.get("val_months", 1)),
        final_holdout_months=int(wf.get("final_holdout_months", 1)),
    )
    feed = str(md.get("feed", "iex"))
    lake_root = resolve_lake_root(cfg)
    symbols = _resolve_symbols(cfg, md, sim_mode=sim_cfg.mode, plan=plan)
    holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    cached_suppliers_flag = bool(optuna_cfg.get("cached_suppliers", False))
    split = plan.splits[split_index]

    ctx = _build_one_fold_context(
        fold_id=f"f{split_index}", val_start=split.val_start, val_end=split.val_end,
        base_cfg=cfg, lake_root=lake_root, feed=feed, symbols=tuple(symbols),
        paths=paths, holdout_guard=holdout_guard,
        cached_suppliers=cached_suppliers_flag, scope="validation",
    )
    print(f"fold {split.val_start}..{split.val_end}  "
          f"dq_cached={'yes' if ctx.startup_dq_report is not None else 'NO'}", flush=True)
    ctx_nocache = dataclasses.replace(ctx, startup_dq_report=None)

    from bowaka_v2_lab.utils.profile_counters import profile_counters_context

    def _run(ctx_):
        return _run_fold_backtest_objective(
            cfg, val_start=split.val_start, val_end=split.val_end,
            lake_root=lake_root, feed=feed, symbols=symbols, paths=paths, ctx=ctx_,
        )

    # Warm the matrix store cache once (shared by both paths) so the A/B times
    # isolate the DQ cost, not the one-time matrix session load.
    _run(ctx)

    t = time.perf_counter()
    base = _run(ctx_nocache)
    t_base = time.perf_counter() - t

    with profile_counters_context(enable=True) as counters:
        t = time.perf_counter()
        fixed = _run(ctx)
        t_fix = time.perf_counter() - t
    print(f"\nDQ cache counters (fixed run): "
          f"full_builds={counters.startup_dq_builds} "
          f"cached_hits={counters.startup_dq_cached_hits}  "
          f"(want hits>0, builds=0 => cache HIT + trial-dep skip)", flush=True)

    fr_base = dataclasses.asdict(fold_result_from_backtest_result("f0", base))
    fr_fix = dataclasses.asdict(fold_result_from_backtest_result("f0", fixed))
    diffs = {k: (fr_base[k], fr_fix[k]) for k in fr_base if fr_base.get(k) != fr_fix.get(k)}

    print(f"\nbaseline (cache OFF, full rebuild): {t_base:6.1f}s")
    print(f"fixed    (cache ON,  hits)        : {t_fix:6.1f}s")
    if t_fix > 0:
        print(f"per-fold speedup                  : {t_base / t_fix:5.2f}x")
    print(f"\nFoldResult (baseline): {fr_base}")
    print(f"\n=== OBJECTIVE PARITY ===")
    print("FoldResult diffs:", diffs or "NONE — byte-identical objective ✓")
    return 0 if not diffs else 1


if __name__ == "__main__":
    raise SystemExit(main())
