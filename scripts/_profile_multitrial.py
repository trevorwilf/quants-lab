"""(c) Adversarially verify the "ctx-build is the one-time dominator, per-trial
cost collapses" hypothesis.

In the real study, _build_one_fold_context runs ONCE per fold (daily cache +
startup DQ cache + session-window preload) and is reused across every trial; only
the strategy params vary per trial. So if ctx-build dominates, the per-_run
(per-trial) wall time should be (a) small relative to ctx-build and (b) flat
across calls. If instead the per-scan sliding-window MACD recompute dominates,
per-_run stays LARGE and flat every call (no amortization) — which is the case
the scan_matrix is meant to fix (it moves the per-scan feature compute to a
one-time build).

Small FIXED universe so each fold call is seconds-to-minutes (the collapse
question is universe-size-independent: it's the trial-1 vs trial-N RATIO that
matters, not the absolute). Reports ctx-build time (one-time) vs N warm per-_run
times + per-call counters (matrix_scans_evaluated, matrix_session_miss,
session_window_cache_hits, scanner_symbol_evals) so matrix ON/OFF is explicit.
"""
from __future__ import annotations

import sys
import time

import pandas as pd

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.config import BowakaV2Paths, SimulationConfig, load_config  # noqa: E402
from bowaka_v2_lab.data.lineage import resolve_lake_root  # noqa: E402
from bowaka_v2_lab.optuna.fold_context import _build_one_fold_context  # noqa: E402
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard  # noqa: E402
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits  # noqa: E402
from bowaka_v2_lab.optuna.walkforward_runner import (  # noqa: E402
    _REPO_ROOT, _run_fold_backtest_objective, _to_date,
)
from bowaka_v2_lab.utils.profile_counters import profile_counters_context  # noqa: E402

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ir2m_smoke.yml"
N_SYMS = int(sys.argv[2]) if len(sys.argv) > 2 else 30
N_WARM = int(sys.argv[3]) if len(sys.argv) > 3 else 3

cfg = load_config(CONFIG)
paths = BowakaV2Paths.from_config(cfg, repo_root=_REPO_ROOT)
wf = (cfg.get("optuna") or {}).get("walkforward", {}) or {}
bt = cfg.get("backtest", {}) or {}
md = cfg.get("market_data", {}) or {}
feed = str(md.get("feed", "sip"))
lake_root = resolve_lake_root(cfg)

plan = build_walkforward_splits(
    full_start=_to_date(bt["start_date"]), full_end=_to_date(bt["end_date"]),
    train_months=int(wf.get("train_months", 3)), val_months=int(wf.get("val_months", 1)),
    final_holdout_months=int(wf.get("final_holdout_months", 1)),
)
split = plan.splits[0]
cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
symbols = sorted({str(s) for s in cdf[cdf.daily_eligible == 1].symbol.dropna().unique()})[:N_SYMS]
holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)

print(f"config={CONFIG}  fold val {split.val_start}..{split.val_end}  "
      f"symbols={len(symbols)} (fixed)  N_warm={N_WARM}", flush=True)

# ---- ONE-TIME ctx build (daily cache + DQ cache + session-window preload) ----
t0 = time.perf_counter()
ctx = _build_one_fold_context(
    fold_id="prof", val_start=split.val_start, val_end=split.val_end,
    base_cfg=cfg, lake_root=lake_root, feed=feed, symbols=tuple(symbols),
    paths=paths, holdout_guard=holdout_guard, cached_suppliers=True, scope="validation",
)
ctx_build_s = time.perf_counter() - t0
if ctx is None:
    print("empty fold — abort"); raise SystemExit(2)
n_sess = len(ctx.sessions)
has_matrix = ctx.scan_matrix_store is not None
print(f"ctx build (ONE-TIME): {ctx_build_s:.1f}s  sessions={n_sess}  "
      f"matrix_store={'YES' if has_matrix else 'NO'}", flush=True)


def _run_once():
    return _run_fold_backtest_objective(
        cfg, val_start=split.val_start, val_end=split.val_end,
        lake_root=lake_root, feed=feed, symbols=symbols, paths=paths, ctx=ctx,
    )


# ---- COLD call (pays one-time JIT/lazy warmup, also amortized in a real study) ----
t0 = time.perf_counter()
with profile_counters_context() as ctr0:
    r0 = _run_once()
cold_s = time.perf_counter() - t0
snap0 = ctr0.snapshot()
nt = getattr(r0, "n_trades", None) or len(getattr(r0, "trades", []) or [])
print(f"\ncall 0 (COLD/warmup): {cold_s:6.1f}s  trades={nt}  "
      f"matrix_evals={snap0.get('matrix_scans_evaluated')}  "
      f"matrix_miss={snap0.get('matrix_session_miss')}  "
      f"win_cache_hits={snap0.get('session_window_cache_hits')}  "
      f"sym_evals={snap0.get('scanner_symbol_evals')}", flush=True)

# ---- N WARM calls (steady-state per-trial: ctx reused, JIT warm) ----
warm_times = []
for i in range(1, N_WARM + 1):
    t0 = time.perf_counter()
    with profile_counters_context() as ctr:
        _run_once()
    dt = time.perf_counter() - t0
    warm_times.append(dt)
    s = ctr.snapshot()
    print(f"call {i} (WARM)       : {dt:6.1f}s  "
          f"matrix_evals={s.get('matrix_scans_evaluated')}  "
          f"matrix_miss={s.get('matrix_session_miss')}  "
          f"win_cache_hits={s.get('session_window_cache_hits')}  "
          f"sym_evals={s.get('scanner_symbol_evals')}", flush=True)

warm_mean = sum(warm_times) / len(warm_times)
print("\n================= VERDICT =================")
print(f"ctx build (one-time)     : {ctx_build_s:7.1f}s")
print(f"per-trial warm (mean of {N_WARM}): {warm_mean:7.1f}s  (calls: "
      + ", ".join(f"{t:.1f}" for t in warm_times) + ")")
print(f"cold->warm collapse      : {cold_s/max(warm_mean,1e-9):6.2f}x "
      "(one-time JIT/lazy warmup; ~1x means no warmup tax)")
ratio = warm_mean / max(ctx_build_s, 1e-9)
print(f"per-trial / ctx-build    : {ratio:6.2f}")
if warm_mean > ctx_build_s:
    print(">>> REFUTED: per-trial cost EXCEEDS one-time ctx build and is FLAT across\n"
          "    trials -> the per-scan recompute is the PER-TRIAL dominator, NOT a\n"
          "    one-time ctx cost. Over a real study (n_trials*folds) this is what\n"
          "    compounds; the scan_matrix (precomputed per-scan features) is the lever.")
else:
    print(">>> CONFIRMED: one-time ctx build dominates and per-trial is cheaper +\n"
          "    flat -> per-trial cost amortizes; matrix gains are smaller than ctx.")
