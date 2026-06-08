"""Phase 3 end-to-end: run a SCOPED $2M intended_realism walkforward study
(/tmp/ir2m_smoke.yml: train3/val1/holdout1, n_trials 1) to confirm the full
pipeline runs now that Option A unblocks the preflight — folds build, the
backtest runs under intended_realism with the §10f T3 depth+impact fill model,
and the study completes. Also surfaces fill execution_tier from the artifacts.
"""
import glob
import json
import os
import sys
import time
import traceback

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study  # noqa: E402

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ir2m_smoke.yml"
t0 = time.time()
print("=== Phase 3: scoped intended_realism study starting: %s ===" % CONFIG, flush=True)
try:
    result = run_walkforward_study(CONFIG)
    dt = (time.time() - t0) / 60.0
    print("\n=== STUDY COMPLETED in %.1f min ===" % dt)
    print("result type:", type(result).__name__)
    if isinstance(result, dict):
        for k in ("status", "study_name", "n_trials", "n_completed_trials",
                  "best_value", "finalist", "finalist_score", "stop_ship_passed",
                  "failure_reason", "yaml_path", "artifact_path"):
            if k in result:
                print("  %-20s %s" % (k, str(result[k])[:220]))
        print("  all keys:", list(result.keys()))
except Exception as e:  # noqa: BLE001
    traceback.print_exc()
    print("\n=== STUDY RAISED:", type(e).__name__, str(e)[:400])

# Surface fill execution_tier from the freshest artifact (confirm T3 engaged).
try:
    arts = sorted(glob.glob("/quants-lab/research_notebooks/bowaka_v2_lab/artifacts/optuna/*.json"),
                  key=os.path.getmtime)
    print("\n=== fill-model evidence (newest artifacts) ===")
    found = False
    for path in arts[-6:]:
        try:
            blob = json.load(open(path))
        except Exception:
            continue
        s = json.dumps(blob)
        if "execution_tier" in s or "T3_NBBO_DEPTH" in s:
            from collections import Counter
            tiers = Counter()
            def walk(o):
                if isinstance(o, dict):
                    t = o.get("execution_tier")
                    if t:
                        tiers[str(t)] += 1
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for x in o:
                        walk(x)
            walk(blob)
            if tiers:
                found = True
                print("  %s -> execution_tier counts: %s" % (os.path.basename(path), dict(tiers)))
    if not found:
        print("  (no execution_tier in the latest artifacts — check the per-trial fill log)")
except Exception as e:  # noqa: BLE001
    print("  artifact scan error:", e)
