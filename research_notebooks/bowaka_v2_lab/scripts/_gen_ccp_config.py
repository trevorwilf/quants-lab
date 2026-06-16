"""Derive the stage-1 CCP study config from the fast_realism base (same window/universe/
scanner/feed → reuses the FR scan matrix, since simulation.mode is NOT in the matrix
hash). Forces mode=current_code_parity, 5000 trials, 16 workers, reuses the FR matrix
store_root. Throwaway helper for the two-stage pivot."""
import yaml

from bowaka_v2_lab.optuna.autoconfig import resolve_walkforward_config

BASE = "configs/_fastrealism_study.yml"
OUT = "configs/_ccp_study_resolved.yml"
FR_MATRIX = "/opt/scan_matrix_cache/fast_realism/validation"

r = resolve_walkforward_config(BASE, feed_override="auto", mode_override="current_code_parity",
                               out_path=OUT)
assert r.mode == "current_code_parity", f"mode resolved to {r.mode}"

c = yaml.safe_load(open(OUT))
c["optuna"]["n_trials"] = 5000
c["optuna"]["n_startup_trials"] = 500
c["optuna"]["n_jobs"] = 16
c["optuna"]["parallel"]["max_workers"] = 16
c["optuna"]["study_name_prefix"] = "bowaka_v2_actual_sip_ccp_2stage"
sm = c["optuna"]["acceleration"]["scan_matrix"]
sm["enabled"] = True
sm["runtime_mode"] = "vectorized"
sm["store_root"] = FR_MATRIX
sm["build_if_missing"] = False
yaml.safe_dump(c, open(OUT, "w"), sort_keys=False)
print(f"wrote {OUT}: mode={c['simulation']['mode']} feed={c['market_data']['feed']} "
      f"window={c['backtest']['start_date']}..{c['backtest']['end_date']} "
      f"folds={c['optuna']['walkforward']} n_trials={c['optuna']['n_trials']} "
      f"n_jobs={c['optuna']['n_jobs']} matrix={sm['enabled']} store_root={sm['store_root']}")
