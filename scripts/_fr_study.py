"""§10i Path 4 — kick off a real fast_realism SEARCH study on the $2M universe
(scoped val 2025-11 window, matrix-covered) and report the honest-fill ranking.
"""
from __future__ import annotations

import sys
import time
import traceback

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study  # noqa: E402

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fr_run.yml"
t0 = time.perf_counter()
print(f"[fr-study] START {time.strftime('%Y-%m-%d %H:%M:%S')} config={CONFIG}", flush=True)
try:
    res = run_walkforward_study(CONFIG)
    dt = (time.perf_counter() - t0) / 60.0
    print(f"\n[fr-study] DONE in {dt:.1f} min", flush=True)
    if isinstance(res, dict):
        print(f"[fr-study] result keys: {sorted(res.keys())}", flush=True)
        for k in ("study_name", "n_trials", "n_completed_trials", "best_value",
                  "best_trial_number", "preflight_passed", "stop_ship_passed"):
            if k in res:
                print(f"[fr-study]   {k} = {res[k]}", flush=True)
        # the per-trial ranking (objective values) if present
        ranked = res.get("ranked") or res.get("ranked_trials") or res.get("trials")
        if ranked:
            print("[fr-study] ranking (top by objective):", flush=True)
            for i, t in enumerate(list(ranked)[:12]):
                v = t.get("value") if isinstance(t, dict) else getattr(t, "value", None)
                n = t.get("number") if isinstance(t, dict) else getattr(t, "number", i)
                print(f"[fr-study]   #{n}: objective={v}", flush=True)
        if "best_params" in res:
            print(f"[fr-study] best_params = {res['best_params']}", flush=True)
except Exception as exc:  # noqa: BLE001
    print(f"\n[fr-study] ERROR after {(time.perf_counter()-t0)/60:.1f} min: "
          f"{type(exc).__name__}: {exc}", flush=True)
    traceback.print_exc()
    raise
