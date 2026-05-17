"""Same-bar stop+target ambiguity policy.

When a one-minute bar's high >= target and its low <= stop, we cannot tell which
was touched first without sub-minute data. Convention from ``[Report §12.5]``:
``stop_first`` is the conservative default; ``target_first`` is optionally
enabled when the caller specifically wants the optimistic interpretation;
``skip`` discards the trade (treat as no-action). All variants produce an
``ambiguous_bar`` flag that callers can persist into diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Policy = Literal["stop_first", "target_first", "skip"]


@dataclass(frozen=True)
class AmbiguityResolution:
    outcome: Literal["stop", "target", "none"]
    ambiguous_bar: bool
    reason: str


def resolve(
    *,
    bar_high: float,
    bar_low: float,
    stop_price: float,
    target_price: float,
    policy: Policy = "stop_first",
) -> AmbiguityResolution:
    """Decide which of stop/target wins for a single bar."""
    hit_stop = bar_low <= stop_price
    hit_target = bar_high >= target_price
    if hit_stop and hit_target:
        if policy == "stop_first":
            return AmbiguityResolution(outcome="stop", ambiguous_bar=True, reason="ambiguous_bar_stop_first")
        if policy == "target_first":
            return AmbiguityResolution(outcome="target", ambiguous_bar=True, reason="ambiguous_bar_target_first")
        return AmbiguityResolution(outcome="none", ambiguous_bar=True, reason="ambiguous_bar_skipped")
    if hit_stop:
        return AmbiguityResolution(outcome="stop", ambiguous_bar=False, reason="stop_only")
    if hit_target:
        return AmbiguityResolution(outcome="target", ambiguous_bar=False, reason="target_only")
    return AmbiguityResolution(outcome="none", ambiguous_bar=False, reason="no_trigger")
