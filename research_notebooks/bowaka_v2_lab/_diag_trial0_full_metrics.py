import sys, json
sys.path.insert(0, "src"); sys.path.insert(0, "../bowaka_common/src")
import optuna
storage = "postgresql+psycopg2://optuna:optuna@localhost:5433/optuna"
study_name = "iex__bowaka_v2_iex_walkforward_conservative_d87c5548_20260529"
study = optuna.load_study(study_name=study_name, storage=storage)
t0 = study.trials[0]
# Dump the FULL fold_metrics for trial 0 — postgres-truncated last time.
print(json.dumps(t0.user_attrs.get("fold_metrics"), indent=2, default=str))
