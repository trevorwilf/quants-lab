"""Post-lake-root-fix verification: pull trial 0 from the most-recent
walkforward study and check decisive markers. Run this after trial 0
completes (~45 min after launching Notebook 10)."""
import sys, json
sys.path.insert(0, "src"); sys.path.insert(0, "../bowaka_common/src")
import optuna
from optuna.trial import TrialState

storage = "postgresql+psycopg2://optuna:optuna@localhost:5433/optuna"

# Connect, list candidate studies.
try:
    summaries = optuna.study.get_all_study_summaries(storage=storage)
except Exception as e:
    print(f"ERROR: could not connect to postgres at {storage}")
    print(f"  Detail: {e}")
    print(f"  Check: docker ps | findstr postgres")
    sys.exit(1)

candidates = sorted(
    [s for s in summaries if "bowaka_v2" in s.study_name and "walkforward" in s.study_name],
    key=lambda s: s.datetime_start or 0,
    reverse=True,
)
if not candidates:
    print("ERROR: no bowaka walkforward studies found")
    sys.exit(1)

print("Recent walkforward studies (most-recent first):")
for i, s in enumerate(candidates[:5]):
    marker = "<-- analyzing" if i == 0 else ""
    print(f"  [{i}] {s.study_name}  trials={s.n_trials}  start={s.datetime_start}  {marker}")
print()

study_name = candidates[0].study_name
study = optuna.load_study(study_name=study_name, storage=storage)

complete = [t for t in study.trials if t.state == TrialState.COMPLETE]
running  = [t for t in study.trials if t.state == TrialState.RUNNING]
failed   = [t for t in study.trials if t.state == TrialState.FAIL]
print(f"Trials: {len(study.trials)} total / {len(complete)} COMPLETE / {len(running)} RUNNING / {len(failed)} FAIL")
print()

if not complete:
    print("Trial 0 not yet complete. Trial 0 takes ~45 min. Re-run this when it's done.")
    sys.exit(0)

# === TRIAL 0 ===
t0 = study.trials[0]
print(f"=== TRIAL 0 ({t0.state.name}) ===")
print(f"  value:           {t0.value}")
if t0.datetime_complete and t0.datetime_start:
    print(f"  duration:        {t0.datetime_complete - t0.datetime_start}")
print(f"  incumbent_trial: {t0.user_attrs.get('incumbent_trial')}")
print()

fm = t0.user_attrs.get("fold_metrics") or []
print(f"=== TRIAL 0 fold_metrics ({len(fm)} folds, full dump) ===")
print(json.dumps(fm, indent=2, default=str))
print()

# === MARKERS ===
print("=== DECISIVE MARKERS ===")
m1 = (t0.value is not None) and (t0.value != -1.5)
print(f"  [{'PASS' if m1 else 'FAIL'}] trial 0 value != -1.5         (got {t0.value})")

nt = [f.get("n_trades", 0) for f in fm]
m2 = sum(1 for n in nt if n > 0) >= 2
print(f"  [{'PASS' if m2 else 'FAIL'}] >=2 of 3 folds have trades   (got n_trades per fold = {nt})")

qc = [f.get("historical_quote_coverage_pct") for f in fm]
m3 = all((q == 0.0 or q is None) for q in qc)
print(f"  [{'PASS' if m3 else 'FAIL'}] quote_coverage = 0.0 (not 100.0)  (got {qc})")

vals = [t.value for t in complete[:20] if t.value is not None]
m4 = len(set(vals)) > 1
print(f"  [{'PASS' if m4 else 'FAIL'}] trial values vary across first 20 trials  (n_unique={len(set(vals))})")
print()

# === TRIAL-BY-TRIAL VALUES ===
print(f"=== first 15 completed trials ===")
for t in complete[:15]:
    fm_t = t.user_attrs.get("fold_metrics") or []
    nt_t = sum(f.get("n_trades", 0) for f in fm_t)
    fold_summary = "/".join(str(f.get("n_trades", 0)) for f in fm_t)
    print(f"  trial {t.number:3d}: value={t.value!s:>20s}  trades=[{fold_summary}]  total={nt_t}")
print()

# === VERDICT ===
print("=== VERDICT ===")
if m1 and m2 and m3 and m4:
    print("  ALL MARKERS PASS — lake-root fix is working.")
    print("  Bayesian optimization is operating on real data.")
elif (not m1) and (not m3):
    print("  FAIL — same pre-fix symptom (value=-1.5 with 100% quote coverage).")
    print("  The fix did not land correctly. Verify the patch:")
    print()
    print('     Select-String -Path "src\\bowaka_v2_lab\\**\\*.py" \\')
    print('         -Pattern ''md\\.get\\("shared_root"\\)'' \\')
    print('         -Exclude "*.ipynb_checkpoints*" |')
    print('         Where-Object { $_.Path -notmatch "data\\\\lineage" }')
    print()
    print("  Expect empty output. Any files listed are still buggy.")
else:
    print("  PARTIAL — send the full output above for diagnosis.")
print()

# === STUDY METADATA ===
print("=== STUDY METADATA ===")
ua = study.user_attrs
for k in ("config_hash", "dataset_hash", "code_hash", "feed",
         "simulation_mode", "dispatch_mode", "dispatch_n_workers",
         "search_space_version", "effective_daily_adjustment",
         "cost_stress"):
    if k in ua:
        v = ua[k]
        if isinstance(v, str) and len(v) > 80:
            v = v[:60] + "..."
        print(f"  {k}: {v}")
