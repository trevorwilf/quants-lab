"""Phase 2 (audit 2026-05-29 §6.8) — search-space relation constraints always hold.

The v3 search space samples soft + hard_gap + critical_gap and
reward_risk_ratio so that, after derivation, ``soft < hard < critical`` and
``target_pct > stop_pct`` hold for EVERY sample — no wasted trials on
parameter sets the strategy would reject.
"""
from __future__ import annotations

import random

from bowaka_v2_lab.optuna.search_space import resolve_search_space
from bowaka_v2_lab.optuna.walkforward_runner import _derived_strategy_fields

_SF = "exits.signal_fade.score_thresholds."


def _sample(spec: dict, rng: random.Random) -> dict:
    out = {}
    for k, e in spec.items():
        if e[0] in ("uniform", "log_uniform"):
            out[k] = rng.uniform(e[1], e[2])
        elif e[0] == "int":
            out[k] = rng.randint(e[1], e[2])
        else:
            out[k] = rng.choice(list(e[1]))
    return out


def test_relations_hold_across_10000_samples() -> None:
    spec = resolve_search_space({})
    rng = random.Random(20260529)
    soft_ok = target_ok = ratio_ok = 0
    n = 10_000
    for _ in range(n):
        p = _sample(spec, rng)
        d = _derived_strategy_fields(p)
        soft = p[_SF + "soft"]
        hard = d[_SF + "hard"]
        critical = d[_SF + "critical"]
        if soft < hard < critical:
            soft_ok += 1
        if d["exits.target_pct"] > p["exits.stop_pct"]:
            target_ok += 1
        if d["exits.target_pct"] / p["exits.stop_pct"] >= 1.5:
            ratio_ok += 1
    assert soft_ok == n, f"soft<hard<critical held for only {soft_ok}/{n}"
    assert target_ok == n, f"target>stop held for only {target_ok}/{n}"
    assert ratio_ok == n, f"reward/risk>=1.5 held for only {ratio_ok}/{n}"
