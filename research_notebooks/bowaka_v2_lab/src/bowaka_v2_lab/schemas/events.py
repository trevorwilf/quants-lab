"""Bowaka v2 — candidate-event and entry-decision schemas.

Port of ``bowaka_v2_schemas.py`` with the §15 remediations applied:

- ``CANDIDATE_EVENT_REQUIRED_FIELDS`` now includes ``projected_rvol_gate``,
  ``max_rvol_gate``, ``max_range_expansion_gate`` ([Report §8.3]). The
  archive's list was incomplete; ``apply_v2_gates`` produces these three keys
  and the schema must require them for events to validate.
- ``validate_entry_decision`` now requires ``reason == "all_gates_passed"``
  for accepted decisions (archive lines 220-229 only validated rejection
  reasons; accepted decisions could carry any string).
- ``CANDIDATE_EVENT_SCHEMA_VERSION`` is preserved at ``3``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable


CANDIDATE_EVENT_SCHEMA_VERSION: int = 3


# ---- candidate_signal required fields --------------------------------

CANDIDATE_EVENT_REQUIRED_FIELDS: tuple[Any, ...] = (
    "schema_version",
    "strategy",
    "event_type",
    "event_id",
    "generated_at",
    "session_date",
    "scan_timestamp",
    "provider",
    "data_feed",
    "bar_interval",
    "config_hash",
    "universe_hash",
    "symbol",
    "exchange",
    "venue_code",
    "instrument_class",
    "eligible_for_bowaka_equity_bucket",
    ("prior_daily_baselines", "prior_close"),
    ("prior_daily_baselines", "avg_volume_20d"),
    ("prior_daily_baselines", "avg_dollar_volume_20d"),
    ("prior_daily_baselines", "prior_atr_14d"),
    ("prior_daily_baselines", "prior_atr_pct"),
    ("prior_daily_baselines", "ema_10_prior"),
    ("prior_daily_baselines", "ema_10_lag_3"),
    ("prior_daily_baselines", "ema_slope_prior"),
    ("forming_session_bar", "session_open"),
    ("forming_session_bar", "session_high"),
    ("forming_session_bar", "session_low"),
    ("forming_session_bar", "last_price"),
    ("forming_session_bar", "session_volume"),
    ("forming_session_bar", "session_range"),
    ("forming_session_bar", "last_bar_timestamp"),
    ("intraday_volume_context", "volume_curve_fraction"),
    ("intraday_volume_context", "expected_volume_until_scan"),
    ("intraday_volume_context", "rvol_so_far"),
    ("intraday_volume_context", "projected_full_day_rvol"),
    ("features", "gap_pct"),
    ("features", "current_return_pct"),
    ("features", "range_expansion_so_far"),
    ("features", "close_location_so_far"),
    ("features", "ema_distance"),
    ("features", "ema_slope"),
    ("features", "signal_strength"),
    # Gate keys — per [Report §8.3] fix: projected_rvol_gate, max_rvol_gate,
    # max_range_expansion_gate added below.
    ("gate_results", "price_gate"),
    ("gate_results", "avg_dollar_volume_gate"),
    ("gate_results", "rvol_gate"),
    ("gate_results", "projected_rvol_gate"),
    ("gate_results", "prior_atr_pct_gate"),
    ("gate_results", "range_expansion_gate"),
    ("gate_results", "close_location_gate"),
    ("gate_results", "ema_distance_gate"),
    ("gate_results", "ema_slope_gate"),
    ("gate_results", "max_gap_gate"),
    ("gate_results", "max_rvol_gate"),
    ("gate_results", "max_range_expansion_gate"),
    ("gate_results", "instrument_gate"),
    "candidate_rank",
    "signal_expiry_timestamp",
)


# ---- entry_decision required fields ---------------------------------

ENTRY_DECISION_REQUIRED_FIELDS: tuple[Any, ...] = (
    "schema_version",
    "strategy",
    "event_type",
    "decision",
    "reason",
    "event_id",
    "candidate_event_id",
    "session_date",
    "symbol",
    "entry_trigger",
    "scan_timestamp",
    "decision_timestamp",
    ("quote", "bid"),
    ("quote", "ask"),
    ("quote", "mid"),
    ("quote", "spread_pct"),
    ("quote", "quote_timestamp"),
    ("quote", "quote_age_seconds"),
    ("risk_snapshot", "bankroll"),
    ("risk_snapshot", "gross_exposure_dollars"),
    ("risk_snapshot", "gross_exposure_pct"),
    ("risk_snapshot", "entries_today"),
    ("risk_snapshot", "open_positions"),
    ("risk_snapshot", "candidate_adv"),
    ("risk_snapshot", "target_notional"),
    ("risk_snapshot", "adv_participation_frac"),
    ("order_plan", "side"),
    ("order_plan", "order_style"),
    ("order_plan", "qty"),
    ("order_plan", "estimated_notional"),
    ("order_plan", "stop_pct"),
    ("order_plan", "target_pct"),
    ("order_plan", "max_hold_days"),
)


# ---- canonical rejection reasons (handoff §5.5) ----------------------

CANONICAL_REJECTION_REASONS: frozenset[str] = frozenset({
    "data_feed_mismatch",
    "stale_bar",
    "missing_daily_baseline",
    "instrument_ineligible",
    "halt_or_pending_review",
    "same_symbol_already_entered_today",
    "symbol_cooldown",
    "daily_entry_cap",
    "max_concurrent_positions",
    "gross_exposure_cap",
    "adv_cap",
    "spread_too_wide",
    "quote_stale",
    "price_chase_band",
    "lost_signal_before_entry",
    "past_last_entry_time",
    "kill_switch",
    "broker_reject",
})


ACCEPTED_REASON: str = "all_gates_passed"


# ---- validators ------------------------------------------------------

_MISSING = object()


def _missing(d: dict, key: Any) -> str | None:
    if isinstance(key, tuple):
        parent, child = key
        if not isinstance(d.get(parent), dict):
            return f"missing nested object {parent!r}"
        if child not in d[parent] or d[parent][child] is _MISSING:
            return f"missing required field {parent}.{child}"
        return None
    if key not in d or d[key] is _MISSING:
        return f"missing required field {key!r}"
    return None


def _check_required(d: dict, fields: Iterable[Any]) -> list[str]:
    problems: list[str] = []
    for f in fields:
        m = _missing(d, f)
        if m:
            problems.append(m)
    return problems


def validate_candidate_event(d: dict) -> tuple[bool, list[str]]:
    """Validate a candidate_signal event against schema v3."""
    if not isinstance(d, dict):
        return False, ["not a dict"]
    problems = _check_required(d, CANDIDATE_EVENT_REQUIRED_FIELDS)
    if d.get("schema_version") != CANDIDATE_EVENT_SCHEMA_VERSION:
        problems.append(
            f"schema_version must be {CANDIDATE_EVENT_SCHEMA_VERSION!r}, "
            f"got {d.get('schema_version')!r}"
        )
    if d.get("event_type") != "candidate_signal":
        problems.append(
            f"event_type must be 'candidate_signal', got {d.get('event_type')!r}"
        )
    return (len(problems) == 0), problems


def validate_entry_decision(d: dict) -> tuple[bool, list[str]]:
    """Validate an entry_decision event.

    Per [Report §8.3] remediation: accepted decisions must carry
    ``reason == "all_gates_passed"``. Archive only validated rejection
    reasons.
    """
    if not isinstance(d, dict):
        return False, ["not a dict"]
    problems = _check_required(d, ENTRY_DECISION_REQUIRED_FIELDS)
    if d.get("schema_version") != CANDIDATE_EVENT_SCHEMA_VERSION:
        problems.append(
            f"schema_version must be {CANDIDATE_EVENT_SCHEMA_VERSION!r}, "
            f"got {d.get('schema_version')!r}"
        )
    if d.get("event_type") != "entry_decision":
        problems.append(
            f"event_type must be 'entry_decision', got {d.get('event_type')!r}"
        )
    decision = d.get("decision")
    reason = d.get("reason")
    if decision not in ("accepted", "rejected"):
        problems.append(
            f"decision must be 'accepted' or 'rejected', got {decision!r}"
        )
    elif decision == "accepted" and reason != ACCEPTED_REASON:
        problems.append(
            f"accepted decisions must carry reason={ACCEPTED_REASON!r}, got {reason!r}"
        )
    elif decision == "rejected" and reason not in CANONICAL_REJECTION_REASONS:
        problems.append(
            f"reason {reason!r} is not in CANONICAL_REJECTION_REASONS"
        )
    return (len(problems) == 0), problems


# ---- canonical event id ---------------------------------------------


def make_event_id(
    strategy: str,
    session_date: str,
    symbol: str,
    ts: Any,
    *,
    suffix: str | None = None,
) -> str:
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts_str = ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        ts_str = str(ts)
    if suffix:
        return f"{strategy}:{session_date}:{symbol}:{suffix}:{ts_str}"
    return f"{strategy}:{session_date}:{symbol}:{ts_str}"
