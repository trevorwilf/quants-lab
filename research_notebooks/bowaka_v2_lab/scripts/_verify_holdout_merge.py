#!/usr/bin/env python
"""Adversarial deterministic check of the holdout-merge: numbers match the log,
combined-score arithmetic is right, collapse flags are right, and NO dev-side
field drifted vs the pre-merge backup."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "scripts")
import topn_robustness_sweep as tn  # noqa: E402

BASE = Path("artifacts/optuna")
new = json.loads((BASE / "topn_robustness.json").read_text(encoding="utf-8"))
old = json.loads((BASE / "_pre_holdout_merge_backup/topn_robustness.json").read_text(encoding="utf-8"))

sys.argv = ["x"]  # _merge import below parses argv lazily; guard anyway
from importlib import import_module  # noqa: E402
mh = import_module("_merge_holdout_into_report")
log = mh.parse_log(Path("artifacts/score_finalist_holdout.log"))

new_by = {r["number"]: r for r in new["finalists"]}
old_by = {r["number"]: r for r in old["finalists"]}

fails = []
def chk(cond, msg):
    if not cond:
        fails.append(msg)

# 1. holdout numbers match the log exactly (as stored: decimals / int / obj)
for num, h in log.items():
    r = new_by.get(num)
    chk(r is not None, f"{num}: missing from new json")
    if r is None:
        continue
    hm = r.get("holdout_metrics") or {}
    chk(abs(hm.get("net_return_pct", -9) - h["net_return_pct"]) < 1e-9, f"{num}: net mismatch {hm.get('net_return_pct')} vs {h['net_return_pct']}")
    chk(abs(hm.get("max_drawdown_pct", -9) - h["max_drawdown_pct"]) < 1e-9, f"{num}: dd mismatch")
    chk(hm.get("n_trades") == h["n_trades"], f"{num}: trades mismatch {hm.get('n_trades')} vs {h['n_trades']}")
    chk(abs((r.get("holdout_score") or -9) - h["obj"]) < 1e-9, f"{num}: holdout_score mismatch")
    chk(r.get("holdout_error") is None, f"{num}: holdout_error not cleared")

# 2. combined_score == mean(median_fold_score, neighbour_mean, holdout_score)
for num, r in new_by.items():
    parts = [v for v in (r.get("median_fold_score"), r.get("neighbour_mean"), r.get("holdout_score")) if v is not None]
    exp = sum(parts) / len(parts)
    chk(abs(r["combined_score"] - exp) < 1e-9, f"{num}: combined {r['combined_score']} != mean parts {exp}")
    chk(len(parts) == 3, f"{num}: combined uses {len(parts)} parts (expected 3 incl holdout)")

# 3. holdout_collapse correctness (re-derive via the script's own rule)
for num, r in new_by.items():
    dev = r.get("median_fold_score") if r.get("median_fold_score") is not None else r.get("dev_value")
    hs = r.get("holdout_score")
    exp_collapse = bool((dev is not None and dev > 0 and hs < dev * 0.4) or (hs < 0 <= (dev or 0.0)))
    chk(r.get("holdout_collapse") == exp_collapse, f"{num}: collapse {r.get('holdout_collapse')} != {exp_collapse}")

# 4. NO dev-side field drifted vs backup
DEV_KEYS = ["params", "dev_value", "median_fold_score", "fold_variance", "fold_scores",
            "rank_score", "dev_metrics", "neighbour_scores", "neighbour_min",
            "neighbour_max", "neighbour_mean", "dev_minus_neighbour_mean"]
for num, r in new_by.items():
    o = old_by.get(num)
    if o is None:
        fails.append(f"{num}: not in backup")
        continue
    for k in DEV_KEYS:
        if json.dumps(r.get(k), sort_keys=True, default=str) != json.dumps(o.get(k), sort_keys=True, default=str):
            fails.append(f"{num}: dev field '{k}' CHANGED vs backup")

# 5. ranking is by combined desc; winner = top (all robust_ok False -> results[0])
combs = [r["combined_score"] for r in new["finalists"]]
chk(combs == sorted(combs, reverse=True), "finalists not sorted by combined desc")
chk(new["winner_trial"] == new["finalists"][0]["number"], "winner_trial != top finalist")
chk(all(not r.get("robust_ok") for r in new["finalists"]), "expected all robust_ok False")
chk(new["winner_trial"] == 3503, f"winner {new['winner_trial']} != 3503")
chk(new["study_best_trial"] == 3920, f"study_best {new['study_best_trial']} != 3920")

# 6. derived 12-mo OOS vs the log's printed OOS (rounding tolerance)
ho_months = tn._months_between(*[__import__("datetime").date.fromisoformat(x) for x in ("2025-12-20", "2026-05-20")])
print(f"ho_months={ho_months:.4f}")
max_oos_delta = 0.0
import re as _re
logtext = Path("artifacts/score_finalist_holdout.log").read_text(encoding="utf-8")
logged_oos = {int(m[0]): float(m[1]) for m in _re.findall(r"^\s*(\d+)\s*\|\s*[-+][\d.]+%\s*\|\s*([-+][\d.]+)%", logtext, _re.M)}
for num, r in new_by.items():
    net = (r["holdout_metrics"] or {}).get("net_return_pct")
    derived = tn._ann_yield(net, ho_months) * 100.0
    if num in logged_oos:
        max_oos_delta = max(max_oos_delta, abs(derived - logged_oos[num]))
print(f"max |derived OOS% - logged OOS%| = {max_oos_delta:.3f} percentage points")

print(f"\nholdout rows verified: {len(log)}")
if fails:
    print(f"\n❌ {len(fails)} CHECK(S) FAILED:")
    for f in fails:
        print("  -", f)
    raise SystemExit(1)
print("\n✅ ALL CHECKS PASSED — holdout numbers match the log, combined arithmetic correct, "
      "collapse flags correct, dev-side fields byte-identical to backup, ranking/winner correct.")
