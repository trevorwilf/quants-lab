"""Profile the per-scan backtest compute on a SMALL fixed universe so we can see
where the controller_compat intended_realism per-trial time actually goes —
without paying the ~15-min full-study PIT-union symbol resolution or a full
~1150-name fold. ~30 eligible small-caps over the 1-month smoke fold (val 2025-11).
One warm run (loads suppliers/cache) + one cProfiled run.
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
from bowaka_v2_lab.config import BowakaV2Paths, SimulationConfig, load_config  # noqa: E402
from bowaka_v2_lab.data.lineage import resolve_lake_root  # noqa: E402
from bowaka_v2_lab.optuna.fold_context import _build_one_fold_context  # noqa: E402
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard  # noqa: E402
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits  # noqa: E402
from bowaka_v2_lab.optuna.walkforward_runner import (  # noqa: E402
    _REPO_ROOT, _run_fold_backtest_objective, _to_date,
)

CONFIG = "/tmp/ir2m_smoke.yml"
N_SYMS = int(sys.argv[1]) if len(sys.argv) > 1 else 30

cfg = load_config(CONFIG)
paths = BowakaV2Paths.from_config(cfg, repo_root=_REPO_ROOT)
wf = (cfg.get("optuna") or {}).get("walkforward", {}) or {}
bt = cfg.get("backtest", {}) or {}
md = cfg.get("market_data", {}) or {}
sim_cfg = SimulationConfig.model_validate(cfg.get("simulation") or {})
feed = str(md.get("feed", "sip"))
lake_root = resolve_lake_root(cfg)

plan = build_walkforward_splits(
    full_start=_to_date(bt["start_date"]), full_end=_to_date(bt["end_date"]),
    train_months=int(wf.get("train_months", 3)), val_months=int(wf.get("val_months", 1)),
    final_holdout_months=int(wf.get("final_holdout_months", 1)),
)
split = plan.splits[0]

# Fixed small universe: distinct daily-eligible small-caps from the staged probe.
cdf = pd.read_csv("/quants-lab/scripts/_pair_dataset.csv")
symbols = sorted({str(s) for s in cdf[cdf.daily_eligible == 1].symbol.dropna().unique()})[:N_SYMS]
holdout_guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)

print(f"config={CONFIG}  fold val {split.val_start}..{split.val_end}  symbols={len(symbols)} (fixed)", flush=True)
t0 = time.perf_counter()
ctx = _build_one_fold_context(
    fold_id="prof", val_start=split.val_start, val_end=split.val_end,
    base_cfg=cfg, lake_root=lake_root, feed=feed, symbols=tuple(symbols),
    paths=paths, holdout_guard=holdout_guard, cached_suppliers=False, scope="validation",
)
print(f"ctx build: {time.perf_counter()-t0:.1f}s  sessions={len(ctx.sessions) if ctx else 0}  "
      f"matrix_store={'yes' if (ctx and ctx.scan_matrix_store is not None) else 'NO'}", flush=True)
if ctx is None:
    print("empty fold — abort"); raise SystemExit(2)


def _run():
    return _run_fold_backtest_objective(
        cfg, val_start=split.val_start, val_end=split.val_end,
        lake_root=lake_root, feed=feed, symbols=symbols, paths=paths, ctx=ctx,
    )


t0 = time.perf_counter()
r0 = _run()
warm = time.perf_counter() - t0
nt = getattr(r0, "n_trades", None) or len(getattr(r0, "trades", []) or [])
n_sess = len(ctx.sessions)
print(f"WARM run: {warm:.1f}s  n_trades={nt}  -> {warm/max(n_sess,1):.2f}s/session over {n_sess} sessions, "
      f"{warm/max(n_sess*len(symbols),1)*1000:.1f}ms/(symbol*session)", flush=True)

pr = cProfile.Profile()
pr.enable()
_run()
pr.disable()
buf = io.StringIO()
st = pstats.Stats(pr, stream=buf)
st.sort_stats("tottime")
buf.write("\n===== TOP 30 by TOTAL (self) time — the real hotspots =====\n")
st.print_stats(30)
st.sort_stats("cumulative")
buf.write("\n===== TOP 25 by CUMULATIVE time =====\n")
st.print_stats(25)
print(buf.getvalue())
print("(cProfile inflates absolute ~2x; read RELATIVE shares + tottime hotspots)")
