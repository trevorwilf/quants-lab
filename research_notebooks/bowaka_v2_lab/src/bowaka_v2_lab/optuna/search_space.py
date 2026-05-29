"""Versioned Optuna search space (realism remediation Phase 9).

The search space is rebuilt against the live Bowaka v2 strategy parameters.
Two hard invariants hold (and are tested):

1. **Versioning.** :data:`SEARCH_SPACE_VERSION` is bumped on every change to
   :data:`SEARCH_SPACE_SPEC`. ``tests/unit/test_search_space_versioned.py``
   compares the spec against a frozen fixture and fails if the spec changed
   without a version bump.

2. **Coverage.** Every numeric bound COVERS the corresponding live value in
   ``reference/actual_bowaka_v2_contract.yaml``. Audit P0-013 flagged the
   pre-Phase-9 ``signals.rvol_so_far_min`` lower bound of ``1.0`` as a bug —
   the live IEX value is ``0.7``, outside the search range, so the optimizer
   could never reproduce the live config.
   ``tests/unit/test_search_space_covers_actual_values.py`` enforces this.

Parameters can be overridden per-run via ``cfg.optuna.search_space_overrides``
(see :func:`resolve_search_space`): a key maps to either a full ``(kind, ...)``
tuple, or the string ``"freeze"`` to drop that parameter from the search.

Excluded parameters
-------------------
Some live parameters are deliberately NOT in the search space because the
realistic simulator cannot yet model them faithfully. Tuning them would
optimize against simulator artifacts rather than strategy behavior. They are
listed in :data:`EXCLUDED_PARAMETERS` with a documented reason.
"""
from __future__ import annotations

from typing import Any


#: Bump this on EVERY change to ``SEARCH_SPACE_SPEC`` (or to the discrete value
#: sets below that feed it). The versioned-fixture test fails otherwise.
#: v3 (audit 2026-05-29 §6.8): replaced the three independent signal-fade
#: thresholds with ``soft`` + ``hard_gap`` + ``critical_gap`` (so
#: ``soft < hard < critical`` ALWAYS holds) and ``exits.target_pct`` with
#: ``exits.reward_risk_ratio`` (so ``target_pct > stop_pct`` ALWAYS holds). The
#: derived ``hard`` / ``critical`` / ``target_pct`` are computed in
#: ``apply_trial_params``.
SEARCH_SPACE_VERSION = 3

#: Discrete option set for ``exits.time_stop.exit_time`` — the live contract
#: value is ``15:45``; the set brackets it with nearby end-of-session cutoffs.
TIME_STOP_EXIT_TIME_CHOICES: tuple[str, ...] = ("15:15", "15:30", "15:45", "15:55")


# --------------------------------------------------------------------------
# Authoritative search-space spec.
#
# Each value is a tuple ``(kind, *args)``:
#   ("uniform", lo, hi)          -> trial.suggest_float(name, lo, hi)
#   ("int", lo, hi)              -> trial.suggest_int(name, lo, hi)
#   ("log_uniform", lo, hi)      -> trial.suggest_float(name, lo, hi, log=True)
#   ("categorical", [choices])   -> trial.suggest_categorical(name, choices)
#
# Bounds are RESEARCH PRIORS, widened beyond the live contract so the optimizer
# can both reproduce live and explore around it. Coverage of the live value is
# a tested invariant; the widening factor is a methodology choice.
# --------------------------------------------------------------------------
SEARCH_SPACE_SPEC: dict[str, tuple] = {
    # ---- signal gates --------------------------------------------------
    # live rvol_so_far_min = 0.7  -> lower bound MUST be <= 0.7 (audit P0-013)
    "signals.rvol_so_far_min":             ("uniform", 0.3, 3.0),
    "signals.rvol_so_far_max":             ("uniform", 4.0, 20.0),       # live 8.0
    "signals.projected_full_day_rvol_min": ("uniform", 0.2, 3.0),        # live 0.5
    "signals.projected_full_day_rvol_max": ("uniform", 4.0, 20.0),       # live 8.0
    "signals.prior_atr_pct_min":           ("uniform", 0.01, 0.20),      # live 0.06
    "signals.range_expansion_so_far_min":  ("uniform", 0.2, 2.5),        # live 0.5
    "signals.range_expansion_so_far_max":  ("uniform", 2.0, 10.0),       # live 2.5
    "signals.close_location_so_far_min":   ("uniform", 0.2, 0.95),       # live 0.6
    "signals.ema_distance_min":            ("uniform", -0.15, 0.30),     # live -0.05
    "signals.ema_slope_min":               ("uniform", -0.10, 0.10),     # live -0.05
    "signals.gap_pct_max":                 ("uniform", 0.05, 0.60),      # live 0.25
    "signals.current_return_pct_max":      ("uniform", 0.10, 1.00),      # live 0.5
    # ---- sizing --------------------------------------------------------
    "sizing.equal_slice_bankroll_fraction": ("uniform", 0.20, 1.00),     # live 0.8
    "sizing.target_risk_dollars":          ("uniform", 50.0, 1000.0),    # live 200
    "sizing.max_concurrent_positions":     ("int", 1, 30),               # live 18
    # ---- risk ----------------------------------------------------------
    "risk.daily_loss_pct":                 ("uniform", 0.005, 0.10),     # live 0.03
    "risk.max_gross_exposure_pct":         ("uniform", 0.20, 1.00),      # live 0.8
    "risk.max_total_entries_per_day":      ("int", 1, 25),               # live 10
    "risk.max_lots_per_symbol":            ("int", 1, 5),                # live 3
    "risk.max_stopouts_per_day":           ("int", 1, 8),                # live 2
    "risk.stop_trading_after_consecutive_stopouts": ("int", 1, 8),       # live 2
    # ---- execution -----------------------------------------------------
    "execution.max_quote_age_seconds":     ("int", 1, 120),              # live 15
    "execution.max_spread_bps":            ("int", 5, 200),              # live 0.01 frac = 100 bps
    # ---- exits ---------------------------------------------------------
    "exits.stop_pct":                      ("uniform", 0.01, 0.20),      # live 0.025
    # Audit 2026-05-29 §6.8 — reward/risk ratio replaces the independent
    # ``target_pct`` so ``target_pct = stop_pct * ratio > stop_pct`` ALWAYS.
    # live target_pct/stop_pct = 0.15/0.025 = 6.0. ``exits.target_pct`` is
    # DERIVED from this in ``apply_trial_params`` (clamped to <= 0.40).
    "exits.reward_risk_ratio":             ("uniform", 1.5, 8.0),        # live 6.0
    "exits.max_hold_days":                 ("int", 1, 10),               # live 3
    "exits.time_stop.exit_time":           ("categorical", list(TIME_STOP_EXIT_TIME_CHOICES)),
    # Audit 2026-05-29 §6.8 — signal-fade thresholds as soft + gaps so
    # ``soft < hard < critical`` ALWAYS holds. ``hard = soft + hard_gap`` and
    # ``critical = hard + critical_gap`` are DERIVED in ``apply_trial_params``
    # (clamped to <= 0.70 / <= 0.90). live soft/hard/critical = 0.34/0.5/0.67
    # -> soft=0.34, hard_gap=0.16, critical_gap=0.17.
    "exits.signal_fade.score_thresholds.soft":         ("uniform", 0.10, 0.50),
    "exits.signal_fade.score_thresholds.hard_gap":     ("uniform", 0.01, 0.30),
    "exits.signal_fade.score_thresholds.critical_gap": ("uniform", 0.01, 0.30),
}


# --------------------------------------------------------------------------
# Parameters deliberately EXCLUDED from the search space.
#
# Each maps to the reason the realistic simulator cannot yet tune it faithfully.
# Tuning these would optimize against simulator artifacts, not strategy edge.
# --------------------------------------------------------------------------
EXCLUDED_PARAMETERS: dict[str, str] = {
    "execution.price_chase_gate.max_pct_above_signal_price": (
        "The quote model reconstructs marketable-limit fills from historical "
        "1-minute bars, not a live order book; the lab does not simulate "
        "price-chasing across a moving NBBO, so this gate cannot be tuned "
        "without optimizing against a synthetic fill artifact."
    ),
    "execution.price_chase_gate.min_pct_below_signal_price": (
        "Same as max_pct_above_signal_price — no live order book is modeled."
    ),
    "execution.halt_gate.block_on_recent_luld_pause": (
        "LULD pause / halt history is not in the shared market-data lake; the "
        "simulator has no halt feed to react to, so this gate is inert."
    ),
    "scanner.symbol_cooldown_minutes": (
        "The cooldown interacts with intraday re-entry timing; with 1-minute "
        "bars the lab cannot resolve sub-minute re-entry order, so tuning it "
        "would chase bar-granularity artifacts rather than real behavior."
    ),
    "risk.adv_tier_caps": (
        "ADV-tier caps are a nested ordered list, not a scalar; they gate "
        "position notional against a liquidity model the lab approximates "
        "coarsely. Sweeping the whole structure is out of scope for Phase 9."
    ),
    "historical_features.volume_curve.bucket_edges": (
        "The intraday volume curve is calibrated upstream of the strategy; it "
        "is a data-preparation parameter, not a strategy decision variable."
    ),
}


def _suggest_one(trial: Any, name: str, spec: tuple) -> Any:
    """Apply one ``(kind, *args)`` spec entry against the Optuna trial API."""
    kind = spec[0]
    if kind == "uniform":
        return trial.suggest_float(name, spec[1], spec[2])
    if kind == "int":
        return trial.suggest_int(name, spec[1], spec[2])
    if kind == "log_uniform":
        return trial.suggest_float(name, spec[1], spec[2], log=True)
    if kind == "categorical":
        return trial.suggest_categorical(name, list(spec[1]))
    raise ValueError(f"unknown suggest kind {kind!r} for {name!r}")


def resolve_search_space(overrides: dict[str, Any] | None = None) -> dict[str, tuple]:
    """Return the effective search-space spec after applying ``overrides``.

    ``overrides`` (``cfg.optuna.search_space_overrides``) maps a parameter name
    to either a full ``(kind, ...)`` tuple (replace its bounds) or the string
    ``"freeze"`` (drop it from the search entirely). An override naming a key
    that is not in the base spec ADDS it. This is how a study narrows, widens,
    or pins individual parameters without editing this module.
    """
    spec = dict(SEARCH_SPACE_SPEC)
    for key, value in (overrides or {}).items():
        if value == "freeze" or value is None:
            spec.pop(key, None)
            continue
        if isinstance(value, (list, tuple)) and value:
            spec[key] = tuple(value)
    return spec


def suggest_params(
    trial: "object", *, overrides: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Use the Optuna trial API to suggest a parameter set.

    The spec is resolved through :func:`resolve_search_space` so per-study
    ``search_space_overrides`` take effect.
    """
    spec = resolve_search_space(overrides)
    out: dict[str, Any] = {}
    for name, entry in spec.items():
        out[name] = _suggest_one(trial, name, entry)
    return out


def search_space_bounds() -> dict[str, dict[str, Any]]:
    """Return a plain-data view of the search space for coverage checks / reports.

    Each entry is ``{"kind", "low", "high"}`` for numeric parameters or
    ``{"kind": "categorical", "choices": [...]}`` for discrete ones.
    """
    out: dict[str, dict[str, Any]] = {}
    for name, spec in SEARCH_SPACE_SPEC.items():
        kind = spec[0]
        if kind == "categorical":
            out[name] = {"kind": kind, "choices": list(spec[1])}
        else:
            out[name] = {"kind": kind, "low": spec[1], "high": spec[2]}
    return out


__all__ = [
    "SEARCH_SPACE_VERSION",
    "SEARCH_SPACE_SPEC",
    "EXCLUDED_PARAMETERS",
    "TIME_STOP_EXIT_TIME_CHOICES",
    "resolve_search_space",
    "suggest_params",
    "search_space_bounds",
]
