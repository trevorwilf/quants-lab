"""Verbatim excerpt of source ``compute_fade_score`` + ``fade_score_to_band``.

Lifted from ``reference/source_strategy/scripts/bowaka_strategy.py`` lines
4371-4432. Pulled here as a fixture so parity tests don't depend on
importing the full source module (which transitively requires the
``alpaca`` SDK).
"""

from __future__ import annotations


# Source verbatim.
_FADE_COMPONENTS = [
    ("rvol_below_min",            "rvol_min",            "rvol"),
    ("atr_pct_below_min",         "atr_pct_min",         "atr_pct"),
    ("range_expansion_below_min", "range_expansion_min", "range_expansion"),
    ("close_location_below_min",  "close_location_min",  "close_location"),
    ("ema_distance_below_min",    "ema_distance_min",    "ema_distance"),
    ("ema_slope_negative",        "ema_slope_min",       "ema_slope"),
]


def compute_fade_score(features: dict, gates: dict, weights: dict | None = None):
    weights = weights or {}
    component_results: dict = {}
    contrib_weight = 0.0
    fail_weight = 0.0
    for name, gate_key, feat_key in _FADE_COMPONENTS:
        thr = gates.get(gate_key)
        if thr is None:
            continue
        val = features.get(feat_key)
        failed = (val is None) or (float(val) < float(thr))
        component_results[name] = bool(failed)
        w = float(weights.get(name) if weights else 1.0)
        contrib_weight += w
        if failed:
            fail_weight += w
    score = fail_weight / contrib_weight if contrib_weight > 0 else 0.0
    return score, component_results


def fade_score_to_band(score: float, *, soft: float = 0.34, hard: float = 0.50, critical: float = 0.67) -> str:
    if score >= critical:
        return "critical"
    if score >= hard:
        return "hard"
    if score >= soft:
        return "soft"
    return "hold"
