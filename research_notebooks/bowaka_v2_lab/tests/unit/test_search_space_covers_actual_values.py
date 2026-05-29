"""Every live contract value lies inside the search-space bounds (Phase 9, P0-013).

The search-space bounds MUST cover the live Bowaka v2 parameter values frozen in
``reference/actual_bowaka_v2_contract.yaml`` — otherwise the optimizer can never
reproduce the live config, and a study's "best" result is unreachable in
production. Audit P0-013 flagged exactly this for ``signals.rvol_so_far_min``
(live 0.7, old lower bound 1.0).

Each search-space key is mapped to its contract location. A few values need a
documented unit transform (e.g. the contract stores the quote-gate spread as a
fraction; the search space tunes it in basis points).
"""
from __future__ import annotations

from typing import Any, Callable

import pytest

from bowaka_v2_lab.optuna.search_space import SEARCH_SPACE_SPEC
from bowaka_v2_lab.reference import load_actual_contract


def _dig(doc: dict, dotted: str) -> Any:
    """Walk a nested dict by a dotted path; return None if any segment is absent."""
    node: Any = doc
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


#: search-space key -> (contract dotted path, value transform applied to the
#: contract value before the bounds check). The transform handles unit
#: mismatches between how the contract stores a value and how the search space
#: tunes it.
_CONTRACT_MAP: dict[str, tuple[str, Callable[[Any], Any]]] = {
    # signal gates — same units, direct.
    "signals.rvol_so_far_min":             ("signals.rvol_so_far_min", float),
    "signals.rvol_so_far_max":             ("signals.rvol_so_far_max", float),
    "signals.projected_full_day_rvol_min": ("signals.projected_full_day_rvol_min", float),
    "signals.projected_full_day_rvol_max": ("signals.projected_full_day_rvol_max", float),
    "signals.prior_atr_pct_min":           ("signals.prior_atr_pct_min", float),
    "signals.range_expansion_so_far_min":  ("signals.range_expansion_so_far_min", float),
    "signals.range_expansion_so_far_max":  ("signals.range_expansion_so_far_max", float),
    "signals.close_location_so_far_min":   ("signals.close_location_so_far_min", float),
    "signals.ema_distance_min":            ("signals.ema_distance_min", float),
    "signals.ema_slope_min":               ("signals.ema_slope_min", float),
    "signals.gap_pct_max":                 ("signals.gap_pct_max", float),
    "signals.current_return_pct_max":      ("signals.current_return_pct_max", float),
    # sizing.
    "sizing.equal_slice_bankroll_fraction": ("sizing.equal_slice_bankroll_fraction", float),
    "sizing.target_risk_dollars":          ("sizing.target_risk_dollars", float),
    "sizing.max_concurrent_positions":     ("sizing.max_concurrent_positions", int),
    # risk.
    "risk.daily_loss_pct":                 ("risk.daily_loss_pct", float),
    "risk.max_gross_exposure_pct":         ("risk.max_gross_exposure_pct", float),
    "risk.max_total_entries_per_day":      ("risk.max_total_entries_per_day", int),
    "risk.max_lots_per_symbol":            ("risk.max_lots_per_symbol", int),
    "risk.max_stopouts_per_day":           ("risk.max_stopouts_per_day", int),
    "risk.stop_trading_after_consecutive_stopouts": (
        "risk.stop_trading_after_consecutive_stopouts", int),
    # execution.
    "execution.max_quote_age_seconds": (
        "execution.quote_gate.max_quote_age_seconds", int),
    # contract stores the quote-gate spread as a fraction (0.01); the search
    # space tunes basis points -> multiply by 10_000.
    "execution.max_spread_bps": (
        "execution.quote_gate.max_spread_pct", lambda v: float(v) * 10_000.0),
    # exits.
    "exits.stop_pct":                      ("exits.stop_pct", float),
    "exits.max_hold_days":                 ("exits.max_hold_days", int),
    "exits.signal_fade.score_thresholds.soft": (
        "exits.signal_fade.score_thresholds.soft", float),
}


#: Audit 2026-05-29 §6.8 — v3 derived (gap/ratio) search-space keys have no
#: single contract path; their live value is computed from multiple contract
#: fields. Each entry maps a search key to a function of the contract that
#: yields the live derived value the bounds must cover.
_DERIVED_MAP: dict[str, Callable[[dict], float]] = {
    "exits.signal_fade.score_thresholds.hard_gap": lambda c: (
        float(_dig(c, "exits.signal_fade.score_thresholds.hard"))
        - float(_dig(c, "exits.signal_fade.score_thresholds.soft"))
    ),
    "exits.signal_fade.score_thresholds.critical_gap": lambda c: (
        float(_dig(c, "exits.signal_fade.score_thresholds.critical"))
        - float(_dig(c, "exits.signal_fade.score_thresholds.hard"))
    ),
    "exits.reward_risk_ratio": lambda c: (
        float(_dig(c, "exits.target_pct")) / float(_dig(c, "exits.stop_pct"))
    ),
}


def test_every_numeric_search_key_is_mapped_to_the_contract() -> None:
    """No numeric search-space key may silently skip the coverage check."""
    numeric = {
        name for name, spec in SEARCH_SPACE_SPEC.items()
        if spec[0] in ("uniform", "log_uniform", "int")
    }
    unmapped = numeric - set(_CONTRACT_MAP) - set(_DERIVED_MAP)
    assert not unmapped, (
        f"numeric search-space keys not mapped to the contract: {sorted(unmapped)} "
        f"— add them to _CONTRACT_MAP (direct) or _DERIVED_MAP (computed) so "
        f"coverage is verified"
    )


@pytest.mark.parametrize("search_key", sorted(_DERIVED_MAP))
def test_search_bounds_cover_derived_live_value(search_key: str) -> None:
    """v3 gap/ratio keys: the live derived contract value lies in the bounds."""
    contract = load_actual_contract()
    live_value = _DERIVED_MAP[search_key](contract)
    spec = SEARCH_SPACE_SPEC[search_key]
    kind, lo, hi = spec[0], spec[1], spec[2]
    assert kind in ("uniform", "log_uniform", "int")
    assert lo <= live_value <= hi, (
        f"{search_key}: live derived value {live_value} is outside the search "
        f"bounds [{lo}, {hi}] — the optimizer cannot reproduce the live config"
    )


@pytest.mark.parametrize("search_key", sorted(_CONTRACT_MAP))
def test_search_bounds_cover_live_contract_value(search_key: str) -> None:
    contract = load_actual_contract()
    contract_path, transform = _CONTRACT_MAP[search_key]
    raw = _dig(contract, contract_path)
    assert raw is not None, f"contract has no value at {contract_path}"
    live_value = transform(raw)

    spec = SEARCH_SPACE_SPEC[search_key]
    kind, lo, hi = spec[0], spec[1], spec[2]
    assert kind in ("uniform", "log_uniform", "int")
    assert lo <= live_value <= hi, (
        f"{search_key}: live contract value {live_value} (from {contract_path}) "
        f"is outside the search bounds [{lo}, {hi}] — the optimizer cannot "
        f"reproduce the live config"
    )


def test_time_stop_exit_time_choice_covers_live_value() -> None:
    """The discrete time_stop.exit_time set must include the live contract value."""
    contract = load_actual_contract()
    live = _dig(contract, "exits.time_stop.exit_time")
    assert live is not None
    kind, choices = SEARCH_SPACE_SPEC["exits.time_stop.exit_time"]
    assert kind == "categorical"
    assert live in choices, (
        f"live time_stop.exit_time {live!r} not in the discrete search set {choices}"
    )
