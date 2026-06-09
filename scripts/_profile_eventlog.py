"""Measure #1 (optimization menu rank 1): how much of the per-trial (objective_minimal)
fold cost is the UNCONDITIONAL per-event _log_event / _portfolio_snapshot / Timestamp.floor
construction that is discarded when artifact_mode != 'full'.

cProfile ONE fold (CCP + matrix ON, fixed small universe), then sum the tottime of the
event-log construction functions and report their share of the fold. No study / PIT-union /
matrix build.
"""
from __future__ import annotations

import cProfile
import io
import pstats
import sys
import time

import pandas as pd

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.config import BowakaV2Paths, SimulationConfig, load_config  # noqa: E402,F401
from bowaka_v2_lab.data.lineage import resolve_lake_root  # noqa: E402
from bowaka_v2_lab.optuna.fold_context import _build_one_fold_context  # noqa: E402
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard  # noqa: E402
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits  # noqa: E402
from bowaka_v2_lab.optuna.walkforward_runner import (  # noqa: E402
    _REPO_ROOT, _run_fold_backtest_objective, _to_date,
)

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ir2m_smoke_ccp.yml"
N_SYMS = int(sys.argv[2]) if len(sys.argv) > 2 else 30

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

print(f"config={CONFIG}  fold val {split.val_start}..{split.val_end}  symbols={len(symbols)}", flush=True)
t0 = time.perf_counter()
ctx = _build_one_fold_context(
    fold_id="prof", val_start=split.val_start, val_end=split.val_end,
    base_cfg=cfg, lake_root=lake_root, feed=feed, symbols=tuple(symbols),
    paths=paths, holdout_guard=holdout_guard, cached_suppliers=True, scope="validation",
)
print(f"ctx build: {time.perf_counter()-t0:.1f}s  matrix={'YES' if (ctx and ctx.scan_matrix_store is not None) else 'NO'}", flush=True)
if ctx is None:
    print("empty fold — abort"); raise SystemExit(2)


def _run():
    return _run_fold_backtest_objective(
        cfg, val_start=split.val_start, val_end=split.val_end,
        lake_root=lake_root, feed=feed, symbols=symbols, paths=paths, ctx=ctx,
    )


pr = cProfile.Profile()
pr.enable()
t0 = time.perf_counter()
_run()
fold_wall = time.perf_counter() - t0
pr.disable()

st = pstats.Stats(pr)
total_tt = st.total_tt  # total self time across all functions (cProfile-inflated but internally consistent)

# Sum tottime for the event-log construction call chain.
EVENTLOG_FUNCS = {"_log_event", "_portfolio_snapshot"}
PANDAS_TS = {"floor", "isoformat", "_floor", "isoformat"}
buckets = {"_log_event": 0.0, "_portfolio_snapshot": 0.0, "Timestamp.floor": 0.0, "isoformat": 0.0}
rows = []
for (fn, lineno, func), (cc, nc, tt, ct, callers) in st.stats.items():
    base = str(fn).split("/")[-1].split("\\")[-1]
    if func in EVENTLOG_FUNCS and base == "backtester.py":
        buckets[func] += tt
        rows.append((func, base, lineno, nc, tt, ct))
    elif func == "floor" and ("times" in base or "timestamps" in base or "pandas" in str(fn)):
        buckets["Timestamp.floor"] += tt
        rows.append((func, base, lineno, nc, tt, ct))
    elif func == "isoformat":
        buckets["isoformat"] += tt
        rows.append((func, base, lineno, nc, tt, ct))

eventlog_tt = sum(buckets.values())
print(f"\nfold wall (cProfiled): {fold_wall:.1f}s   cProfile total_tt: {total_tt:.2f}s", flush=True)
print("\n=== event-log construction tottime (the #1 candidate) ===")
for k, v in buckets.items():
    print(f"  {k:24s}: {v:8.3f}s  ({v/max(total_tt,1e-9)*100:5.2f}% of total_tt)")
print(f"  {'SUBTOTAL':24s}: {eventlog_tt:8.3f}s  ({eventlog_tt/max(total_tt,1e-9)*100:5.2f}% of total_tt)")
print("\n=== matching rows (func | file | line | ncalls | tottime | cumtime) ===")
for func, base, lineno, nc, tt, ct in sorted(rows, key=lambda r: -r[4]):
    print(f"  {func:22s} {base}:{lineno}  ncalls={nc:>8}  tt={tt:8.3f}  ct={ct:8.3f}")

buf = io.StringIO()
st2 = pstats.Stats(pr, stream=buf)
st2.sort_stats("tottime")
buf.write("\n===== TOP 30 by tottime (context) =====\n")
st2.print_stats(30)
print(buf.getvalue())
print("(cProfile inflates absolute time ~2x; read the RELATIVE % share — that transfers to the real run.)")
