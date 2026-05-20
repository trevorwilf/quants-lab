"""Paper/live event consumer.

Port of ``bowaka_v2_strategy.py``'s consumer with the same §15 fixes applied
in ``sim/strategy_consumer.py``. Used by paper/live; never imported by the
backtester (which uses the sim variant).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class LiveEventConsumer:
    """Skeleton for paper/live mode (Phase 7+ wires this in).

    Reads signal_strength from features.signal_strength (§15.2 P1 fix).
    Emits ENTRY decision AFTER broker confirm; on reject emits broker_reject
    canonical record (§15.1 P0).
    """

    cfg: Mapping[str, Any]

    def consume(self, candidate_event: dict) -> dict:
        # Phase 7 fills this in. We just preserve the interface.
        raise NotImplementedError("LiveEventConsumer.consume is wired in Phase 7+")
