"""Point-in-time universe builder (realism remediation Phase 3).

``universe.builder`` is the **canonical** v2 universe builder: a daily
point-in-time eligible-symbol set derived from the lake asset snapshot plus
prior-day bars, with the live contract filters and no current-day leakage. It
supersedes the synthetic ``sim.replay_fixtures.synthetic_universe`` fan-out for
all non-smoke runs.
"""
from .builder import (
    DEFAULT_ALLOWED_EXCHANGES,
    DEFAULT_TICKER_BLOCKLIST,
    UniverseRecord,
    build_pit_universe,
    build_pit_universe_for_sessions,
    classify_instrument,
    eligible_symbols,
    funnel,
    to_scanner_snapshot,
    universe_hash,
)
from .persist import write_universe_artifacts

__all__ = [
    "UniverseRecord",
    "build_pit_universe",
    "build_pit_universe_for_sessions",
    "classify_instrument",
    "eligible_symbols",
    "universe_hash",
    "to_scanner_snapshot",
    "funnel",
    "write_universe_artifacts",
    "DEFAULT_ALLOWED_EXCHANGES",
    "DEFAULT_TICKER_BLOCKLIST",
]
