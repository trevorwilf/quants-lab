"""Build notebook 10 — real walk-forward Optuna optimization (auto feed-select)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _notebook_common import make_notebook, write_notebook  # noqa: E402

HERE = Path(__file__).resolve().parent


def main() -> None:
    nb = make_notebook([
        {"type": "code", "source": (
            "# Papermill parameters.\n"
            "# NOTE: the prior bowaka_v2_walkforward_optuna.yml is QUARANTINED (realism\n"
            "# audit 2026-05-22 §P0-001). The default below points at the Phase-8\n"
            "# walk-forward-purpose contract-parity config that matches today's lake\n"
            "# (IEX-only, current_code_parity). FEED='auto' upgrades simulation.mode\n"
            "# to intended_realism the moment SIP bars+quotes land in the lake.\n"
            "# Walk-forward sizing is locked to the operator spec (2026-05-23):\n"
            "# train=21, val=1, final_holdout=5 -> 3 folds over the ~29.8-month IEX lake.\n"
            "#\n"
            "# Speedup report v2 §4 P2 / Phase 2 — default points at the workstation\n"
            "# overlay (192 GiB / 18-core box; reserve 62 GiB; strict_parallel=true;\n"
            "# max_workers=8). The base optuna config carries the more conservative\n"
            "# reserve_system_gib=32 / strict_parallel=false defaults; flip\n"
            "# CONFIG_PATH below if you intentionally want those.\n"
            "CONFIG_PATH = 'research_notebooks/bowaka_v2_lab/configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml'\n"
            "N_TRIALS = None          # None -> optuna.n_trials from the config; or set an integer\n"
            "N_STARTUP_TRIALS = None  # None -> optuna.n_startup_trials; random trials before TPE\n"
            "N_JOBS = None            # None -> optuna.n_jobs (Phase 5 default: 8 workers on PostgreSQL)\n"
            "FEED = 'auto'            # 'auto' (SIP > IEX > synthetic) | 'sip' | 'iex' | 'synthetic'\n"
            "# Phase 10 default-on: trial 0 is pinned to the actual-contract\n"
            "# parameter set (the live config) so the optimizer's best can be\n"
            "# compared against the live incumbent. Set False to disable.\n"
            "INCUMBENT_TRIAL = True\n"
        )},
        {"type": "markdown", "source": (
            "# 10 - Walk-Forward Optuna\n\n"
            "Runs a **real** walk-forward parameter optimization against the shared\n"
            "market-data lake. Each Optuna trial samples a parameter set, applies it\n"
            "to the config, and runs a real backtest over every walk-forward\n"
            "validation window; the trial objective is the median fold score. The\n"
            "final-holdout window is never read during tuning.\n\n"
            "**Feed auto-selection (`FEED='auto'`):** the notebook probes the lake\n"
            "and adapts the run to the best data available -\n\n"
            "| Lake holds | feed | simulation.mode |\n"
            "|---|---|---|\n"
            "| SIP bars + SIP quotes | `sip` | `intended_realism` |\n"
            "| SIP bars, no SIP quotes | `sip` | `current_code_parity` |\n"
            "| IEX bars only | `iex` | `current_code_parity` |\n"
            "| neither | - | `smoke_fixture` (synthetic) |\n\n"
            "Set `FEED` to `sip` / `iex` / `synthetic` to override the probe.\n\n"
            "**Parameters:** `N_TRIALS` is the total trial count (`None` -> the\n"
            "config's `optuna.n_trials`). `N_STARTUP_TRIALS` is how many of those are\n"
            "random-sampling trials before TPE-guided search begins.\n\n"
            "**Compute:** a run is `N_TRIALS` x `n_folds` real backtests - the config\n"
            "default is a multi-day job. Set a small `N_TRIALS` for a quick run."
        )},
        {"type": "code", "source": (
            "# Probe the lake and adapt the config's feed + simulation.mode.\n"
            "from bowaka_v2_lab.optuna.autoconfig import resolve_walkforward_config\n"
            "resolved = resolve_walkforward_config(CONFIG_PATH, feed_override=FEED)\n"
            "print(f'feed   : {resolved.feed}')\n"
            "print(f'mode   : {resolved.mode}')\n"
            "print(f'reason : {resolved.reason}')\n"
            "print(f'config : {resolved.path}')\n"
        )},
        {"type": "code", "source": (
            "import json\n"
            "from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study\n"
            "# Realism remediation 2 Phase 8 (audit §P0-011): current_code_parity\n"
            "# studies require an explicit opt-in. ResolvedWalkforwardConfig\n"
            "# carries the auto-opt-in flags when the lake forces parity mode\n"
            "# (IEX-only / SIP-bars-no-quotes); the mechanical cap is research_only.\n"
            "result = run_walkforward_study(\n"
            "  resolved.path, n_trials=N_TRIALS, n_jobs=N_JOBS,\n"
            "  n_startup_trials=N_STARTUP_TRIALS, allow_smoke=resolved.allow_smoke,\n"
            "  allow_current_code_parity_study=resolved.allow_current_code_parity_study,\n"
            "  tier=resolved.tier,\n"
            "  incumbent_trial=INCUMBENT_TRIAL,\n"
            ")\n"
            "print(json.dumps(result, indent=2, default=str))\n"
        )},
    ])
    write_notebook(nb, HERE / "10_optuna_walkforward.ipynb")
    print("Built 10_optuna_walkforward.ipynb")


if __name__ == "__main__":
    main()
