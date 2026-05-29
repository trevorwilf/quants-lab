"""Diagnostic: run the incumbent (actual-contract) params through ONE validation
fold and dump the FoldResult metrics + penalty breakdown + objective.

Answers: is the -1.5 objective floor a systemic lab issue (the incumbent
known-good live params also produce no trades / floor) or just unfit random
trial params (the incumbent trades normally)?

Run:
  cd research_notebooks/bowaka_v2_lab
  PYTHONPATH=src:../bowaka_common/src python scripts/diag_incumbent_fold.py \
      --config configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True, type=Path)
    p.add_argument("--fold-index", type=int, default=0)
    args = p.parse_args(argv)

    from bowaka_v2_lab.config import load_config
    from bowaka_v2_lab.config.paths import BowakaV2Paths
    from bowaka_v2_lab.data.lineage import resolve_lake_root
    from bowaka_v2_lab.optuna.fold_context import build_fold_contexts
    from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
    from bowaka_v2_lab.optuna.objective import (
        compute_objective, fold_penalties, fold_score,
        fold_result_from_backtest_result,
    )
    from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits
    from bowaka_v2_lab.optuna.walkforward_runner import (
        _incumbent_baseline_params, _run_fold_backtest_objective, apply_trial_params,
    )

    cfg = load_config(args.config)
    lake_root = resolve_lake_root(cfg)
    feed = str((cfg.get("market_data") or {}).get("feed", "iex"))
    bt = cfg.get("backtest") or {}
    wf = (cfg.get("optuna") or {}).get("walkforward") or {}
    import pandas as pd

    plan = build_walkforward_splits(
        full_start=pd.Timestamp(bt["start_date"]).date(),
        full_end=pd.Timestamp(bt["end_date"]).date(),
        train_months=int(wf.get("train_months", 6)),
        val_months=int(wf.get("val_months", 1)),
        final_holdout_months=int(wf.get("final_holdout_months", 1)),
    )
    print(f"[diag] splits={len(plan.splits)} fold_index={args.fold_index}")
    split = plan.splits[args.fold_index]
    print(f"[diag] val window: {split.val_start} .. {split.val_end}")

    incumbent = _incumbent_baseline_params()
    print(f"[diag] incumbent params ({len(incumbent)} keys):")
    print(json.dumps(incumbent, indent=2, default=str))

    cfg_inc = apply_trial_params(dict(cfg), incumbent)
    repo_root = Path(__file__).resolve().parents[5]
    paths = BowakaV2Paths.from_config(cfg_inc, repo_root=repo_root)
    symbols = [str(s) for s in ((cfg.get("universe") or {}).get("symbols") or [])]
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)

    contexts = build_fold_contexts(
        cfg_inc, plan, lake_root=lake_root, feed=feed, symbols=symbols,
        paths=paths, holdout_guard=guard,
    )
    ctx = contexts[args.fold_index]
    if ctx is None:
        print("[diag] fold context is None (no sessions in window) — aborting")
        return 2
    print(f"[diag] fold sessions={len(ctx.sessions)} "
          f"eligible(sample)={len(ctx.eligible_symbols_by_session.get(ctx.sessions[0], ()))}")

    t0 = _dt.datetime.now()
    result = _run_fold_backtest_objective(
        cfg_inc, val_start=split.val_start, val_end=split.val_end,
        lake_root=lake_root, feed=feed, symbols=symbols, paths=paths, ctx=ctx,
    )
    elapsed = (_dt.datetime.now() - t0).total_seconds()
    print(f"[diag] fold backtest elapsed={elapsed:.1f}s")
    if result is None:
        print("[diag] _run_fold_backtest_objective returned None (degraded fold)")
        return 3

    fr = fold_result_from_backtest_result(f"diag_{split.val_start.isoformat()}", result)
    print("[diag] FoldResult metrics:")
    print(json.dumps({
        "net_return": fr.net_return,
        "max_drawdown": fr.max_drawdown,
        "worst_day_loss": fr.worst_day_loss,
        "n_trades": fr.n_trades,
        "turnover": fr.turnover,
        "concentration": fr.concentration,
        "quote_coverage": fr.quote_coverage,
        "fill_rate": fr.fill_rate,
        "missing_quote_count": fr.missing_quote_count,
    }, indent=2, default=str))
    pen = fold_penalties(fr)
    print("[diag] fold penalties:")
    print(json.dumps(pen, indent=2, default=str))
    print(f"[diag] fold_score = {fold_score(fr):.6f}")
    obj = compute_objective([fr])
    print(f"[diag] single-fold objective = {obj.objective:.6f}")
    print(f"[diag] VERDICT: {'NO TRADES -> low-trade penalty floor' if fr.n_trades == 0 else 'trades present'}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
