#!/usr/bin/env python
"""Multi-signal parameter-contribution analysis for a finished study.

Goal: decide which tuned params *never contribute*, so the 30-dim search space
can be pared toward ~15 (TPE/Bayesian opt degrades past ~15-20 effective dims).

A single importance number from a single evaluator is fragile, so we triangulate
FOUR independent signals per parameter:

  1. fANOVA importance      (variance attributed by a random forest; sums to 1)
  2. MDI importance         (mean decrease in impurity; different RF estimator)
  3. PED-ANOVA importance   (density-ratio estimator; methodology-independent)
  4. best-decile spread     (std of the param among the top-10% trials / std over
                             all trials). ~1.0 => the optimizer never concentrated
                             it (flat / doesn't matter); <<1 => it pinned it down.

A param is a robust PRUNE candidate only if it is near-zero on the importance
evaluators AND its best-decile spread stays wide (the optimizer was indifferent).
Importance alone can be misleading when one param dominates the variance (it
compresses everyone else), so signal #4 is the cross-check.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
import optuna

optuna.logging.set_verbosity(optuna.logging.WARNING)

STORAGE = os.environ.get("OPTUNA_STORAGE",
    "postgresql+psycopg2://optuna:optuna@optuna-postgres:5432/optuna")
NAME = sys.argv[1] if len(sys.argv) > 1 else \
    "bowaka_v2_sip_walkforward_conservative_54ec4858_20260616"

st = optuna.load_study(study_name=NAME, storage=STORAGE)
comp = [t for t in st.trials if t.state == optuna.trial.TrialState.COMPLETE
        and t.value is not None]
print(f"study: {NAME}")
print(f"complete trials: {len(comp)} | direction: {st.direction.name}")

# union of param names
params = sorted({k for t in comp for k in t.params})

# ---- importance evaluators (triangulate methodology) ----
from optuna.importance import (FanovaImportanceEvaluator,
                               MeanDecreaseImpurityImportanceEvaluator)
evs = {"fanova": FanovaImportanceEvaluator(seed=0),
       "mdi": MeanDecreaseImpurityImportanceEvaluator(seed=0)}
try:
    from optuna.importance import PedAnovaImportanceEvaluator
    evs["pedanova"] = PedAnovaImportanceEvaluator()
except Exception as e:
    print("(PedAnova unavailable:", e, ")")
imp = {}
for k, ev in evs.items():
    print(f"  computing {k} ...", flush=True)
    imp[k] = optuna.importance.get_param_importances(st, evaluator=ev)

# ---- best-decile spread (signal #4) ----
vals = np.array([t.value for t in comp])
order = np.argsort(vals)                       # ascending
topn = max(50, len(comp) // 10)
top_idx = set(order[-topn:].tolist())          # MAXIMIZE -> top decile = highest

def spread_ratio(p):
    allv, topv = [], []
    cat = False
    for i, t in enumerate(comp):
        if p in t.params:
            v = t.params[p]
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                cat = True
                break
            allv.append(v)
            if i in top_idx:
                topv.append(v)
    if cat:
        return None
    allv, topv = np.array(allv, float), np.array(topv, float)
    s = allv.std()
    return float(topv.std() / s) if s > 0 and topv.size else float("nan")

# ---- combine ----
rows = []
for p in params:
    f = imp["fanova"].get(p, 0.0)
    m = imp["mdi"].get(p, 0.0)
    pa = imp.get("pedanova", {}).get(p, None)
    sr = spread_ratio(p)
    rows.append({"param": p, "fanova": f, "mdi": m, "pedanova": pa, "spread_ratio": sr})

rows.sort(key=lambda r: -r["fanova"])

def prune_candidate(r):
    low = r["fanova"] < 0.01 and r["mdi"] < 0.01 and (r["pedanova"] is None or r["pedanova"] < 0.02)
    flat = (r["spread_ratio"] is None) or (r["spread_ratio"] != r["spread_ratio"]) or r["spread_ratio"] > 0.85
    return low and flat

print("\n" + "=" * 100)
hdr = f'{"#":>2} {"fANOVA":>8} {"MDI":>8} {"PedAnova":>9} {"bestDecileSpread":>17}  PRUNE?  param'
print(hdr); print("-" * 100)
for i, r in enumerate(rows, 1):
    pa = "   n/a  " if r["pedanova"] is None else f'{r["pedanova"]*100:7.2f}%'
    sr = " cat " if r["spread_ratio"] is None else (
        "  nan " if r["spread_ratio"] != r["spread_ratio"] else f'{r["spread_ratio"]:.2f}')
    flag = "  CUT " if prune_candidate(r) else "  keep"
    print(f'{i:>2} {r["fanova"]*100:7.2f}% {r["mdi"]*100:7.2f}% {pa:>9} {sr:>17} {flag}  {r["param"]}')

cuts = [r["param"] for r in rows if prune_candidate(r)]
keeps = [r["param"] for r in rows if not prune_candidate(r)]
print("=" * 100)
print(f"\nKEEP ({len(keeps)}): consensus-contributing")
for p in keeps: print("   +", p)
print(f"\nCUT ({len(cuts)}): near-zero on all importance evaluators AND wide best-decile spread")
for p in cuts: print("   -", p)

out = "artifacts/optuna/param_contribution_54ec4858.json"
json.dump({"study": NAME, "n_complete": len(comp), "rows": rows,
           "keep": keeps, "cut": cuts}, open(out, "w"), indent=2, default=str)
print(f"\nwrote {out}")
