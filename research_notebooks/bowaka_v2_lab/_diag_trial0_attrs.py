import os, sys, json
sys.path.insert(0, "src"); sys.path.insert(0, "../bowaka_common/src")
import optuna

# Note: psycopg2 driver, port 5433 (host mapping of container's 5432).
storage = "postgresql+psycopg2://optuna:optuna@localhost:5433/optuna"

study_name = "iex__bowaka_v2_iex_walkforward_conservative_d87c5548_20260529"
study = optuna.load_study(study_name=study_name, storage=storage)
print(f"Loaded study: {study.study_name}")
print(f"Trials so far: {len(study.trials)}")

# Look at trial 0 in detail — that's the production-incumbent.
t0 = study.trials[0]
print()
print(f"=== Trial 0 ({t0.state}) ===")
print(f"value:               {t0.value}")
print(f"datetime_start:      {t0.datetime_start}")
print(f"datetime_complete:   {t0.datetime_complete}")
print(f"duration:            {(t0.datetime_complete - t0.datetime_start) if t0.datetime_complete else 'still running'}")

print()
print(f"=== Trial 0 user_attrs ===")
for k, v in sorted(t0.user_attrs.items()):
    sv = json.dumps(v, default=str)
    if len(sv) > 400:
        sv = sv[:400] + "...TRUNCATED"
    print(f"  {k}: {sv}")

print()
print(f"=== Trial 0 intermediate_values (per-fold scores) ===")
print(f"  {dict(t0.intermediate_values)}")

print()
print(f"=== Trial 0 system_attrs ===")
for k, v in sorted(t0.system_attrs.items()):
    sv = json.dumps(v, default=str)
    if len(sv) > 200:
        sv = sv[:200] + "..."
    print(f"  {k}: {sv}")

# Compare across trials to see if anything varies at all.
print()
print(f"=== values across trials (first 10) ===")
for t in study.trials[:10]:
    print(f"  trial {t.number}: value={t.value}, state={t.state}")

# Study-level user_attrs (often contains the dataset_hash, lake_root, etc.)
print()
print(f"=== study user_attrs ===")
for k, v in sorted(study.user_attrs.items()):
    sv = json.dumps(v, default=str)
    if len(sv) > 300:
        sv = sv[:300] + "..."
    print(f"  {k}: {sv}")
