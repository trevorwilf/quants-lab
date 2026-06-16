"""Derive a fast_realism walk-forward config from the committed SIP IR optuna config
(same $250k-ADV universe + contract params; mode flipped to fast_realism; window matched
to the 11-month container lake). Usage:
    python scripts/_gen_fastrealism_config.py <out.yml> [--matrix <store_root>] [--ntrials N]
Throwaway helper for the fast_realism feasibility proof + study setup."""
import sys

import yaml

out = sys.argv[1]
matrix_root = None
ntrials = None
for i, a in enumerate(sys.argv):
    if a == "--matrix":
        matrix_root = sys.argv[i + 1]
    if a == "--ntrials":
        ntrials = int(sys.argv[i + 1])

c = yaml.safe_load(open("configs/bowaka_v2_actual_sip_intended_realism_optuna.yml"))
c["simulation"]["mode"] = "fast_realism"
c["backtest"]["start_date"] = "2025-08-01"
c["backtest"]["end_date"] = "2026-06-12"
c["optuna"]["walkforward"] = {"train_months": 6, "val_months": 1, "final_holdout_months": 2}
c["optuna"]["study_name_prefix"] = "bowaka_v2_actual_sip_fast_realism"
if ntrials is not None:
    c["optuna"]["n_trials"] = ntrials
sm = c["optuna"]["acceleration"]["scan_matrix"]
if matrix_root:
    sm["enabled"] = True
    sm["runtime_mode"] = "vectorized"
    sm["store_root"] = matrix_root
    sm["scope"] = "validation"
    sm["separate_holdout_matrix"] = False
    sm["build_if_missing"] = False
else:
    sm["enabled"] = False
    sm["runtime_mode"] = "disabled"
yaml.safe_dump(c, open(out, "w"), sort_keys=False)
print(f"wrote {out}: mode={c['simulation']['mode']} feed={c['market_data']['feed']} "
      f"min_adv={c['universe']['min_adv_dollars']} window={c['backtest']['start_date']}..{c['backtest']['end_date']} "
      f"folds={c['optuna']['walkforward']} n_trials={c['optuna']['n_trials']} "
      f"matrix={sm['enabled']}/{sm['runtime_mode']}"
      + (f" @ {sm.get('store_root')}" if sm["enabled"] else ""))
