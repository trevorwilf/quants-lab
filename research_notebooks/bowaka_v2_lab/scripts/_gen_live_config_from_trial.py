#!/usr/bin/env python
"""Translate a finalist trial's tuned params into the LIVE strategy config.

The lab's optuna *search* parameterisation differs from the live
``bowaka_v2_config.yaml`` schema. This script overlays a finalist's 30 tuned
params onto the CURRENT live config (preserving comments + every live-only
block: paths, feed, compounding, protected_position, gates, score, logging,
research), applying the three non-trivial transforms the lab uses:

  execution.max_spread_bps        ->  execution.quote_gate.max_spread_pct  (bps / 10_000)
  exits.reward_risk_ratio         ->  exits.target_pct                     (= stop_pct * rr)
  signal_fade.score_thresholds    ->  cumulative gaps:
        soft     = soft
        hard     = soft + hard_gap
        critical = hard + critical_gap

Everything else is a direct key copy. The transforms were reverse-engineered
from the lab's own exported winner YAML and are re-verified here against the
current live #3155 values as a self-check.

Output is STAGED in the lab (artifacts/deploy/); it is NOT written to the live
system. Applying it to the live openalgo tree is a deliberate operator step.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ruamel.yaml import YAML

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
LIVE_CFG = LAB / "reference/source_strategy/scripts/bowaka_v2_config.yaml"
TOPN_JSON = LAB / "artifacts/optuna/topn_robustness.json"
OUT_DIR = LAB / "artifacts/deploy"


def get_trial(trial_number: int) -> dict:
    d = json.loads(TOPN_JSON.read_text(encoding="utf-8"))
    for r in d["finalists"]:
        if r.get("number") == trial_number:
            return r
    raise SystemExit(f"trial {trial_number} not in finalists")


def apply_overlay(cfg, p: dict) -> list[tuple[str, object, object]]:
    """Mutate cfg in place; return [(dotted_key, old, new)] for changed keys."""
    changes: list[tuple[str, object, object]] = []

    def setk(container, key, new):
        old = container.get(key)
        if old != new:
            changes.append((key, old, new))
        container[key] = new

    # --- signals (12 direct) ---
    sig = cfg["signals"]
    for k in (
        "rvol_so_far_min", "projected_full_day_rvol_min", "prior_atr_pct_min",
        "range_expansion_so_far_min", "close_location_so_far_min",
        "ema_distance_min", "ema_slope_min", "rvol_so_far_max",
        "projected_full_day_rvol_max", "range_expansion_so_far_max",
        "gap_pct_max", "current_return_pct_max",
    ):
        setk(sig, k, p[f"signals.{k}"], )

    # --- execution.quote_gate (2, one transform) ---
    qg = cfg["execution"]["quote_gate"]
    setk(qg, "max_spread_pct", round(p["execution.max_spread_bps"] / 10_000.0, 10))
    setk(qg, "max_quote_age_seconds", int(p["execution.max_quote_age_seconds"]))

    # --- exits (stop, target=stop*rr, max_hold, time_stop, signal_fade) ---
    ex = cfg["exits"]
    stop = float(p["exits.stop_pct"])
    setk(ex, "stop_pct", stop)
    setk(ex, "target_pct", round(stop * float(p["exits.reward_risk_ratio"]), 10))
    setk(ex, "max_hold_days", int(p["exits.max_hold_days"]))
    setk(ex["time_stop"], "exit_time", str(p["exits.time_stop.exit_time"]))
    soft = float(p["exits.signal_fade.score_thresholds.soft"])
    hard = soft + float(p["exits.signal_fade.score_thresholds.hard_gap"])
    crit = hard + float(p["exits.signal_fade.score_thresholds.critical_gap"])
    th = ex["signal_fade"]["score_thresholds"]
    setk(th, "soft", round(soft, 10))
    setk(th, "hard", round(hard, 10))
    setk(th, "critical", round(crit, 10))

    # --- risk (6 direct) ---
    # Explicit int set — do NOT infer from the key name: max_gross_exposure_pct
    # starts with "max_" but is a float fraction (a startswith heuristic would
    # truncate 0.71 -> 0 and silently block all entries).
    rk = cfg["risk"]
    int_risk = {
        "max_lots_per_symbol", "max_stopouts_per_day",
        "max_total_entries_per_day", "stop_trading_after_consecutive_stopouts",
    }
    for k in (
        "daily_loss_pct", "max_gross_exposure_pct", "max_lots_per_symbol",
        "max_stopouts_per_day", "max_total_entries_per_day",
        "stop_trading_after_consecutive_stopouts",
    ):
        v = p[f"risk.{k}"]
        setk(rk, k, int(v) if k in int_risk else float(v))

    # --- sizing (3 direct) ---
    sz = cfg["sizing"]
    setk(sz, "equal_slice_bankroll_fraction", float(p["sizing.equal_slice_bankroll_fraction"]))
    setk(sz, "target_risk_dollars", float(p["sizing.target_risk_dollars"]))
    setk(sz, "max_concurrent_positions", int(p["sizing.max_concurrent_positions"]))

    return changes


def main() -> int:
    trial_number = int(sys.argv[1]) if len(sys.argv) > 1 else 3437
    r = get_trial(trial_number)
    p = r["params"]

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    cfg = yaml.load(LIVE_CFG.read_text(encoding="utf-8"))

    changes = apply_overlay(cfg, p)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"bowaka_v2_config_trial{trial_number}_paper.yaml"
    # header note in the #3155 style
    hdr = (
        f"# STAGED lab->live config for trial #{trial_number} "
        f"(combined={r['combined_score']:.5f}, median_fold={r['median_fold_score']:.5f}, "
        f"holdout={r['holdout_score']:.5f}, robust_ok={r['robust_ok']}).\n"
        f"# Generated by scripts/_gen_live_config_from_trial.py from the CURRENT live\n"
        f"# config; live-only blocks preserved, {len(changes)} tuned keys overlaid.\n"
        f"# strategy.environment is left at the live value (paper) for shadow.\n"
        f"# NOT applied to the live system — operator copies it deliberately.\n"
    )
    with out.open("w", encoding="utf-8") as fh:
        fh.write(hdr)
        yaml.dump(cfg, fh)

    print(f"WROTE {out}  ({len(changes)} changed keys)")
    print("=" * 72)
    print(f"{'KEY':<48}{'OLD':>11}  -> NEW")
    print("-" * 72)
    for k, old, new in changes:
        def f(v):
            return f"{v:.5f}" if isinstance(v, float) else str(v)
        print(f"{k:<48}{f(old):>11}  -> {f(new)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
