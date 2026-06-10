"""Score a finished study's top-N finalists on the reserved final-holdout window
ONLY -- the holdout half of topn_robustness_sweep.py, without rebuilding the
validation contexts or re-running the neighbour-robustness pass.

Use this to fill in **Holdout net%** + **12-mo OOS%** for finalists when a full
sweep already produced the dev/robustness columns. It reuses the sweep's exact
finalist selection + holdout-scoring path, so the numbers match a full sweep run.

Requires the holdout-scope scan matrix to be built + parity-verified AND
optuna.acceleration.scan_matrix.separate_holdout_matrix = false (so the holdout
matrix is actually opened -- with true it is skipped and vectorized scoring
raises a parity-proof error). Resolves configs/_local_container_matrix.yml the
same way notebook 10 does (feed auto, mode current_code_parity).

  python scripts/score_finalist_holdout.py [--top-n 12] [--study-name NAME]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Make the lab + bowaka_common importable, and this script's dir (for the sweep
# import), whether run via PYTHONPATH or directly.
_HERE = Path(__file__).resolve().parent
_LAB = _HERE.parent
for _p in (str(_LAB / "src"), str(_LAB.parent / "bowaka_common" / "src"), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import optuna  # noqa: E402

import bowaka_v2_lab.optuna.walkforward_runner as wr  # noqa: E402
from bowaka_v2_lab.optuna.autoconfig import resolve_walkforward_config  # noqa: E402
from bowaka_v2_lab.optuna.fold_context import build_holdout_context  # noqa: E402
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard  # noqa: E402
from bowaka_v2_lab.optuna.objective import (  # noqa: E402
    compute_objective,
    fold_result_from_backtest_result,
)
from topn_robustness_sweep import (  # noqa: E402  (same dir)
    _agg_fold_metrics,
    _ann_pct,
    _ann_yield,
    _is_valid,
    _months_between,
    _pct,
    _pick_study_name,
    _rank_score,
    _setup,
)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/_local_container_matrix.yml")
    p.add_argument("--top-n", type=int, default=12)
    p.add_argument("--study-name", default=None)
    p.add_argument("--feed", default="auto")
    p.add_argument("--mode-override", default="current_code_parity")
    args = p.parse_args(argv)

    # Resolve exactly as notebook 10 does (so the overlay's
    # separate_holdout_matrix=false flows through -> the holdout matrix is opened).
    r = resolve_walkforward_config(
        args.config, feed_override=args.feed, mode_override=args.mode_override,
        out_path="/tmp/score_finalist_holdout_resolved.yml",
    )
    print(f"resolved: feed={r.feed} mode={r.mode}", flush=True)
    s = _setup(str(r.path))
    sm = (s["cfg"].get("optuna") or {}).get("acceleration", {}).get("scan_matrix", {})
    if bool(sm.get("separate_holdout_matrix", True)):
        raise SystemExit(
            "separate_holdout_matrix is TRUE -> the holdout matrix is not opened "
            "and vectorized scoring will fail. Set it false in "
            f"{args.config} and retry."
        )

    study_name = _pick_study_name(s["storage_uri"], args.study_name)
    study = optuna.load_study(study_name=study_name, storage=s["storage_uri"])
    plan = s["plan"]
    n_splits = len(plan.splits)
    w_var = float(wr.DEFAULT_PENALTY_WEIGHTS.fold_variance)
    completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    valid = [t for t in completed if _is_valid(t, n_splits)]
    ranked = sorted(valid, key=lambda t: _rank_score(t, w_var), reverse=True)
    top = ranked[: args.top_n]
    print(f"study={study_name} completed={len(completed)} valid={len(valid)} "
          f"finalists={len(top)}", flush=True)
    if not top:
        raise SystemExit("no valid finalists to score")

    print("building holdout fold context (once; single-threaded -- dominates)...", flush=True)
    t0 = time.perf_counter()
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    holdout_ctx = build_holdout_context(
        s["cfg"], plan, lake_root=s["lake_root"], feed=s["feed"], symbols=s["symbols"],
        paths=s["paths"], holdout_guard=guard, cached_suppliers=s["cached_suppliers"],
    )
    print(f"holdout context built in {time.perf_counter() - t0:.0f}s", flush=True)

    ho_months = _months_between(plan.final_holdout_start, plan.final_holdout_end)
    rows = []
    for t in top:
        try:
            guard.enter_final_eval()
            res = wr._run_fold_backtest_objective(
                wr.apply_trial_params(s["cfg"], dict(t.params)),
                val_start=plan.final_holdout_start, val_end=plan.final_holdout_end,
                lake_root=s["lake_root"], feed=s["feed"], symbols=s["symbols"],
                paths=s["paths"], ctx=holdout_ctx,
            )
            guard.exit_final_eval()
            hf = fold_result_from_backtest_result("holdout", res) if res is not None else None
            if hf is None:
                rows.append((t.number, "—", "—", "no result"))
                continue
            net = hf.net_return
            oos = _ann_pct(_ann_yield(net, ho_months))
            rows.append((t.number, _pct(net), oos,
                         f"obj {float(compute_objective([hf]).objective):.3f} · "
                         f"{hf.n_trades} trades · dd {_pct(hf.max_drawdown)}"))
            print(f"  trial {t.number}: holdout_net%={_pct(net)} 12mo_OOS%={oos} "
                  f"trades={hf.n_trades}", flush=True)
        except Exception as exc:  # noqa: BLE001
            rows.append((t.number, "ERR", "ERR", str(exc).splitlines()[0][:140]))
            print(f"  trial {t.number}: ERROR {str(exc).splitlines()[0][:140]}", flush=True)

    print("\n================ Finalist holdout scores ================")
    print(f"study : {study_name}")
    print(f"holdout window: {plan.final_holdout_start} .. {plan.final_holdout_end} "
          f"({ho_months:.1f} months)")
    print(f"{'trial':>6} | {'Holdout net%':>13} | {'12-mo OOS%':>24} | detail")
    print("-" * 88)
    for num, net, oos, detail in rows:
        print(f"{num:>6} | {net:>13} | {oos:>24} | {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
