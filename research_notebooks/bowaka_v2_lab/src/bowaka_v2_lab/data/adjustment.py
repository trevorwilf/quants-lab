"""Daily-bar adjustment resolution (audit 2026-05-29 §5.3 / §13.1; §3.5 cutover).

The shared market-data lake stores ``raw``, ``split_adjusted`` and ``all``
(split+dividend) daily partitions in separate directories. ``MarketDataStore.
daily_bars`` / ``available_symbols`` default ``adjustment="raw"`` — so any caller
that does not pass an explicit ``adjustment`` reads raw bars even when the contract
requires adjusted data. This helper is the SINGLE source of truth mapping a config
to the correct ``adjustment``; every daily-bar reader must call it.

§3.5 adjustment contract: the lab EXECUTES on RAW minute bars (tradeable intraday
prices) and GATES/FEATURISES on ADJUSTED daily bars (``all`` = total-return). The
two intentionally differ; :func:`is_mixed_adjustment_session` surfaces the rare
in-window split/dividend sessions where mixing the two scales would distort one
decision (microcaps rarely pay dividends, so it is usually a no-op).
"""
from __future__ import annotations
from typing import Any, Mapping


def daily_adjustment_for_config(cfg: Mapping[str, Any]) -> str:
    """Return the adjustment string daily-bar readers must pass to the lake.

    Resolution order (§3.5 cutover):
    1. ``market_data.require_adjusted_daily_bars: true`` -> ``all`` (split+dividend).
       Was ``split_adjusted``, which silently DROPPED dividend adjustment. "adjusted"
       means fully adjusted; precedence over split-only since adjusted ⊃ split.
    2. ``market_data.require_split_adjustment: true`` -> ``split_adjusted`` (splits only).
    3. explicit ``market_data.daily_adjustment: <value>`` -> as written.
    4. otherwise -> ``raw``.

    The ``all`` partition is produced by ``scripts/backfill_daily_all.py``; a config
    with ``require_adjusted_daily_bars`` reads it (the universe builder warns loudly
    if the partition is missing).
    """
    md = (cfg or {}).get("market_data") or {}
    if md.get("require_adjusted_daily_bars"):
        return "all"
    if md.get("require_split_adjustment"):
        return "split_adjusted"
    return str(md.get("daily_adjustment", "raw"))


#: §3.5 — material divergence (bps) between the raw and adjusted daily close that
#: marks an in-window split/dividend, i.e. a session where executing on RAW minute
#: bars while gating/featurising on ADJUSTED daily bars mixes scales.
MIXED_ADJUSTMENT_DIVERGENCE_BPS = 50.0  # 0.5%


def daily_adjustment_divergence_bps(close_adjusted: Any, close_raw: Any) -> float:
    """``|adjusted - raw| / raw`` in bps for the SAME (symbol, session) daily close.

    On a non-split/dividend day the raw and adjusted closes agree (~0 bps); on an
    in-window split/dividend day they diverge, so a single decision mixes the
    raw-minute (execution) and adjusted-daily (features) scales — the §3.5
    mixed-adjustment hazard. A DQ check compares the ``all`` vs ``raw`` daily
    partitions per session to SURFACE the mixing rather than silently apply it.
    """
    try:
        a, r = float(close_adjusted), float(close_raw)
    except (TypeError, ValueError):
        return 0.0
    if r <= 0.0:
        return 0.0
    return abs(a - r) / r * 10_000.0


def is_mixed_adjustment_session(
    close_adjusted: Any, close_raw: Any, *,
    threshold_bps: float = MIXED_ADJUSTMENT_DIVERGENCE_BPS,
) -> bool:
    """True when raw vs adjusted daily closes diverge beyond ``threshold_bps`` — an
    in-window split/dividend session that mixes raw-minute + adjusted-daily scales (§3.5)."""
    return daily_adjustment_divergence_bps(close_adjusted, close_raw) > float(threshold_bps)


__all__ = [
    "daily_adjustment_for_config",
    "daily_adjustment_divergence_bps",
    "is_mixed_adjustment_session",
    "MIXED_ADJUSTMENT_DIVERGENCE_BPS",
]
