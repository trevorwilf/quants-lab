"""Source-aligned signal-fade scoring (Phase fidelity-6).

Verbatim component spec lifted from
``reference/source_strategy/scripts/bowaka_strategy.py`` lines 4374-4432.
Each component checks one gate against a feature; ``failed`` means the
gate is broken. Score is the weighted fail rate in [0, 1]. Bands map to
hold / soft / hard / critical.

The lab also retains a legacy integer-score "research_intraday_fade"
hypothesis in ``sim/signal_fade.py``; that one is kept untouched. The
source-aligned implementation here is the one ``BowakaPortfolioBacktester``
will use in exact mode (Phase fidelity-6).
"""

from __future__ import annotations

from typing import Literal


# Verbatim component spec from source bowaka_strategy.py lines 4374-4381.
_FADE_COMPONENTS: list[tuple[str, str, str]] = [
    ("rvol_below_min",            "rvol_min",            "rvol"),
    ("atr_pct_below_min",         "atr_pct_min",         "atr_pct"),
    ("range_expansion_below_min", "range_expansion_min", "range_expansion"),
    ("close_location_below_min",  "close_location_min",  "close_location"),
    ("ema_distance_below_min",    "ema_distance_min",    "ema_distance"),
    ("ema_slope_negative",        "ema_slope_min",       "ema_slope"),
]


def compute_source_fade_score(
    features: dict,
    signal_gates: dict,
    weights: dict | None = None,
) -> tuple[float, dict]:
    """Source-parity port of ``bowaka_strategy.compute_fade_score``.

    Parameters
    ----------
    features
        Mapping of feature name → value (``rvol``, ``atr_pct``, ...).
    signal_gates
        Mapping of gate threshold name → value (``rvol_min``, ...).
        Null/missing gates skip the corresponding component.
    weights
        Optional per-component weight overrides. Defaults to equal
        weight on every active component.

    Returns
    -------
    (score, component_results)
        ``score`` in [0, 1] (higher = stronger fade); ``component_results``
        is ``{component_name: bool_failed}`` for every active gate.
    """
    weights = weights or {}
    component_results: dict = {}
    contrib_weight = 0.0
    fail_weight = 0.0
    for name, gate_key, feat_key in _FADE_COMPONENTS:
        thr = signal_gates.get(gate_key)
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


def source_fade_score_to_band(
    score: float,
    *,
    soft: float = 0.34,
    hard: float = 0.50,
    critical: float = 0.67,
) -> Literal["hold", "soft", "hard", "critical"]:
    """Source-parity port of ``bowaka_strategy.fade_score_to_band``.

    Boundaries are inclusive at the lower edge: score == hard → "hard".
    """
    if score >= critical:
        return "critical"
    if score >= hard:
        return "hard"
    if score >= soft:
        return "soft"
    return "hold"
