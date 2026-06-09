"""§10i Path 4+3 — (a) surface the best fast_realism trial's honest-fill stats + PnL,
and (b) validate the top-3 finalists under intended_realism.

Runs in objective_minimal (BacktestResult carries fills+trades+summary in memory;
NO gate_dump/event-log → no $2M memory explosion). Builds the full-$2M fold ctx
ONCE, reuses it for both modes (suppliers/universe are mode-independent).
"""
from __future__ import annotations

import sys
import time

import optuna

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.config import BowakaV2Paths, SimulationConfig, load_config  # noqa: E402
from bowaka_v2_lab.data.lineage import resolve_lake_root  # noqa: E402
from bowaka_v2_lab.optuna.autoconfig import derive_validation_config  # noqa: E402
from bowaka_v2_lab.optuna.fold_context import _build_one_fold_context  # noqa: E402
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard  # noqa: E402
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits  # noqa: E402
from bowaka_v2_lab.optuna.walkforward_runner import (  # noqa: E402
    _REPO_ROOT, _resolve_symbols, _run_fold_backtest_objective, _to_date,
    apply_trial_params,
)

STORAGE = "sqlite:////tmp/fr_run.db"
SEARCH_CFG = "/tmp/fr_run.yml"


def _fill_dist(result) -> dict:
    recs = list(getattr(result, "fills", []) or []) or list(getattr(result, "fill_records", []) or [])
    full = partial = nofill = 0
    fracs = []
    for f in recs:
        req = float(f.get("requested_qty", f.get("qty", 0)) or 0)
        fl = float(f.get("filled_qty", f.get("filled_quantity", 0)) or 0)
        if req <= 0:
            continue
        frac = fl / req
        fracs.append(frac)
        if frac >= 0.999:
            full += 1
        elif frac <= 0.001:
            nofill += 1
        else:
            partial += 1
    n = full + partial + nofill
    med = sorted(fracs)[len(fracs) // 2] if fracs else 0.0
    return {"orders": n, "full": full, "partial": partial, "nofill": nofill,
            "full_pct": 100 * full / n if n else 0, "partial_pct": 100 * partial / n if n else 0,
            "nofill_pct": 100 * nofill / n if n else 0, "median_fill_frac": med}


def _pnl(result) -> float:
    trades = list(getattr(result, "trades", []) or [])
    return sum(float(t.get("pnl", t.get("trade_pnl", 0)) or 0) for t in trades), len(trades)


def _run(cfg, params, split, lake_root, feed, symbols, paths, holdout_guard, ctx, label):
    c = apply_trial_params(cfg, params)
    t0 = time.perf_counter()
    try:
        r = _run_fold_backtest_objective(
            c, val_start=split.val_start, val_end=split.val_end, lake_root=lake_root,
            feed=feed, symbols=symbols, paths=paths, ctx=ctx,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[{label}] ABORTED: {type(exc).__name__}: {exc}", flush=True)
        return
    dt = time.perf_counter() - t0
    fd = _fill_dist(r)
    pnl, ntr = _pnl(r)
    print(f"[{label}] {dt:.0f}s | trades={ntr} realized_pnl=${pnl:,.0f} | "
          f"fills: {fd['orders']} orders -> {fd['full_pct']:.0f}% full / "
          f"{fd['partial_pct']:.0f}% partial / {fd['nofill_pct']:.0f}% no-fill "
          f"(median fill frac {fd['median_fill_frac']:.2f})", flush=True)


names = optuna.get_all_study_names(STORAGE)
study = optuna.load_study(study_name=names[0], storage=STORAGE)
done = [t for t in study.trials if t.value is not None]
top3 = sorted(done, key=lambda t: t.value, reverse=True)[:3]
print(f"study={names[0]}  completed={len(done)}  top3 by objective: "
      + ", ".join(f"#{t.number}={t.value:.3f}" for t in top3), flush=True)

cfg = load_config(SEARCH_CFG)
paths = BowakaV2Paths.from_config(cfg, repo_root=_REPO_ROOT)
md = cfg.get("market_data") or {}
feed = str(md.get("feed", "sip"))
lake_root = resolve_lake_root(cfg)
bt = cfg.get("backtest") or {}
wf = (cfg.get("optuna") or {}).get("walkforward") or {}
plan = build_walkforward_splits(
    full_start=_to_date(bt["start_date"]), full_end=_to_date(bt["end_date"]),
    train_months=int(wf.get("train_months", 3)), val_months=int(wf.get("val_months", 1)),
    final_holdout_months=int(wf.get("final_holdout_months", 1)),
)
split = plan.splits[0]
sim_cfg = SimulationConfig.model_validate(cfg.get("simulation") or {})
print("[setup] resolving full PIT universe (this is the ~10-15min union build)...", flush=True)
t0 = time.perf_counter()
symbols = _resolve_symbols(cfg, md, sim_mode=sim_cfg.mode, plan=plan)
print(f"[setup] symbols={len(symbols)} in {(time.perf_counter()-t0)/60:.1f}min; building fold ctx...", flush=True)
holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
t0 = time.perf_counter()
ctx = _build_one_fold_context(
    fold_id="finalist", val_start=split.val_start, val_end=split.val_end, base_cfg=cfg,
    lake_root=lake_root, feed=feed, symbols=tuple(symbols), paths=paths,
    holdout_guard=holdout_guard, cached_suppliers=True, scope="validation",
)
print(f"[setup] ctx built in {(time.perf_counter()-t0)/60:.1f}min, sessions={len(ctx.sessions) if ctx else 0}", flush=True)

# (a) best trial under fast_realism (the search mode)
best = top3[0]
print("\n=== (a) best fast_realism trial — honest-fill stats + PnL ===", flush=True)
_run(cfg, best.params, split, lake_root, feed, symbols, paths, holdout_guard, ctx, f"FR  #{best.number}")

# (b) top-3 under intended_realism (Path 3 validation)
ir_cfg = derive_validation_config(cfg, validation_mode="intended_realism")
print("\n=== (b) top-3 finalists under intended_realism (Path 3 deploy gate) ===", flush=True)
for t in top3:
    _run(ir_cfg, t.params, split, lake_root, feed, symbols, paths, holdout_guard, ctx,
         f"IR  #{t.number} (FR obj={t.value:.3f})")
print("\n[done]", flush=True)
