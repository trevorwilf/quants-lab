"""Event-driven simulator primitives (Realism remediation 2 Phase 4).

The pre-Phase-4 backtester batched all scans for a session, then evaluated all
exits at the end. Audit P0-002 documents how that ordering inverts the live
strategy: an early stop should update ``daily_realized_pnl`` / ``stopouts_today``
*before* later scans, but the old loop deferred that until after every scan ran.

This module provides:

* :class:`EventType` — every event the dispatch loop recognises (SCAN,
  MINUTE_BAR, QUOTE, PARENT_ACK, PARENT_FILL, OCO_ATTACH_ATTEMPT, CHILD_FILL,
  PROTECTION_CHECK, TIME_STOP_CHECK, SIGNAL_FADE_CHECK, EOD_MARK). Their numeric
  values double as the *priority* tiebreaker so two events at the exact same
  timestamp dispatch in the stable order live trading would observe.

* :class:`Event` — an immutable timestamped envelope.

* :class:`EventQueue` — a min-heap ordered by ``(timestamp, priority, sequence)``.
  ``sequence`` is a monotonic counter; with the heap's stable ordering it gives
  a total ordering even when both ``timestamp`` and ``priority`` collide.

* :class:`CadenceConfig` — the four poll cadences (scan, fill, protection,
  time-stop). All default to the live ``loop_interval_seconds: 5`` except the
  scanner (60s) and time-stop (60s) checks per the live contract.

* :func:`preload_session_events` — materialise the per-session SCAN /
  PROTECTION_CHECK / FILL_POLL / TIME_STOP_CHECK ticks plus the EOD_MARK. The
  MINUTE_BAR and QUOTE events are NOT preloaded; suppliers materialise them on
  demand when an open lot or pending order needs them.

The old ``run_one_scan`` helper is preserved at the bottom of this file
unchanged — the SCAN handler in :mod:`sim.backtester` still calls it.
"""
from __future__ import annotations

import datetime as _dt
import heapq
import itertools
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Iterable, Iterator, Mapping, Optional

import pandas as pd

from ..scanner.scan_loop import ScanResult, evaluate_one_scan
from .strategy_consumer import StrategyConsumer, StrategyConsumerResult


# ---- event taxonomy ------------------------------------------------------


class EventType(IntEnum):
    """Every event the dispatch loop recognises.

    The integer value doubles as the *priority* tiebreaker on a same-timestamp
    collision — lower wins. EOD_MARK is last (highest int) so all other events
    at 16:00 close drain before the daily snapshot. PROTECTION_CHECK is highest
    priority among polls (it can release a slot used by the very next SCAN).
    """

    PROTECTION_CHECK = 10
    OCO_ATTACH_ATTEMPT = 15
    CHILD_FILL = 20
    PARENT_FILL = 25
    PARENT_ACK = 30
    MINUTE_BAR = 35
    QUOTE = 40
    TIME_STOP_CHECK = 45
    SIGNAL_FADE_CHECK = 50
    SCAN = 60
    EOD_MARK = 100


@dataclass(frozen=True)
class Event:
    """A timestamped event envelope.

    ``timestamp`` is a tz-aware UTC ``pd.Timestamp``. ``payload`` is an arbitrary
    dict carrying the dispatch-relevant context (candidate event, parent-order
    id, position id, etc.). The queue's tiebreaker is the event's
    ``(timestamp, priority, sequence)`` triple.
    """

    timestamp: pd.Timestamp
    type: EventType
    payload: Mapping[str, Any] = field(default_factory=dict)


# ---- min-heap event queue ------------------------------------------------


class EventQueue:
    """A min-heap of events keyed by ``(timestamp, priority, sequence)``.

    The ``sequence`` counter is monotonic per-queue: two events at the same
    timestamp + priority pop in FIFO order. The class is single-process — the
    backtester drives a single queue per session.
    """

    def __init__(self) -> None:
        self._heap: list[tuple[pd.Timestamp, int, int, Event]] = []
        self._seq: Iterator[int] = itertools.count()

    def push(self, event: Event) -> None:
        """Push ``event`` onto the heap, breaking ties with a monotonic counter."""
        seq = next(self._seq)
        heapq.heappush(
            self._heap, (event.timestamp, int(event.type), seq, event)
        )

    def push_many(self, events: Iterable[Event]) -> None:
        """Bulk-push for the per-session preload."""
        for ev in events:
            self.push(ev)

    def pop(self) -> Event:
        """Pop the earliest event. Raises :class:`IndexError` if empty."""
        _, _, _, ev = heapq.heappop(self._heap)
        return ev

    def peek(self) -> Optional[Event]:
        """Return the next event without removing it; ``None`` if empty."""
        if not self._heap:
            return None
        return self._heap[0][3]

    def empty(self) -> bool:
        return not self._heap

    def __len__(self) -> int:
        return len(self._heap)


# ---- cadence configuration ------------------------------------------------


@dataclass(frozen=True)
class CadenceConfig:
    """The four decoupled poll cadences (audit P1-009).

    The live contract has ``loop_interval_seconds: 5`` for the strategy poll
    loop and ``scan_interval_seconds: 60`` for the scanner. The protection and
    fill polls inherit the 5s loop default; the time-stop check is a 60s tick
    since the live time-stop fires on a 1-minute boundary.

    All four values are positive integers (seconds). The backtester reads them
    from ``cfg.session`` / ``cfg.simulation`` / ``cfg.scanner`` — explicit
    values win, otherwise the field defaults stand.
    """

    scan_interval_seconds: int = 60
    fill_poll_interval_seconds: int = 5
    protection_poll_interval_seconds: int = 5
    time_stop_check_interval_seconds: int = 60

    @classmethod
    def from_cfg(cls, cfg: Mapping[str, Any]) -> "CadenceConfig":
        """Resolve a :class:`CadenceConfig` from a backtester ``cfg`` dict.

        Honoured keys (each falls back to the dataclass default when absent):

        * ``session.scan_interval_seconds`` (live contract field)
        * ``simulation.fill_poll_interval_seconds`` /
          ``session.loop_interval_seconds`` (the live 5s loop default)
        * ``simulation.protection_poll_interval_seconds`` /
          ``session.loop_interval_seconds``
        * ``simulation.time_stop_check_interval_seconds``
        """
        session_cfg = (cfg.get("session") or {}) if cfg else {}
        sim_cfg = (cfg.get("simulation") or {}) if cfg else {}
        loop = int(session_cfg.get("loop_interval_seconds", 5))
        return cls(
            scan_interval_seconds=int(session_cfg.get("scan_interval_seconds", 60)),
            fill_poll_interval_seconds=int(
                sim_cfg.get("fill_poll_interval_seconds", loop)
            ),
            protection_poll_interval_seconds=int(
                sim_cfg.get("protection_poll_interval_seconds", loop)
            ),
            time_stop_check_interval_seconds=int(
                sim_cfg.get("time_stop_check_interval_seconds", 60)
            ),
        )


# ---- per-session preload --------------------------------------------------


def _et(ts: pd.Timestamp) -> pd.Timestamp:
    """Convert ``ts`` to America/New_York for ET-window arithmetic."""
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.tz_convert("America/New_York")


def _ticks_between(
    start: pd.Timestamp,
    end: pd.Timestamp,
    interval_seconds: int,
    *,
    inclusive_end: bool = False,
) -> list[pd.Timestamp]:
    """Tick timestamps in ``[start, end)`` (or ``[start, end]``) at the cadence.

    Used for PROTECTION_CHECK / FILL_POLL / TIME_STOP_CHECK preload. The first
    tick lands at ``start``; subsequent ticks at ``start + N * interval`` up to
    (but not including) ``end`` by default. The cadence is fixed-second so two
    runs with identical inputs produce the bit-identical tick list.
    """
    if end <= start:
        return []
    step = pd.Timedelta(seconds=int(interval_seconds))
    if step <= pd.Timedelta(0):
        return []
    ticks: list[pd.Timestamp] = []
    cur = start
    while (cur < end) if not inclusive_end else (cur <= end):
        ticks.append(cur)
        cur = cur + step
    return ticks


def preload_session_events(
    *,
    session_date: _dt.date,
    scan_times: Iterable[pd.Timestamp],
    cadence: CadenceConfig,
    eod_clock: _dt.time = _dt.time(16, 0),
) -> list[Event]:
    """Build the per-session SCAN + PROTECTION_CHECK + FILL_POLL +
    TIME_STOP_CHECK + EOD_MARK preload.

    The SCAN events come from the supplied ``scan_times`` (live cadence ticks).
    The poll ticks span the regular session window
    ``[scan_window_start, 16:00 ET]`` so a poll lands on the boundary of every
    candidate signal-strength check the live strategy would have run. The
    EOD_MARK is anchored at ``session_date 16:00 ET`` (live regular close).

    MINUTE_BAR and QUOTE events are NOT preloaded — the dispatcher's handlers
    materialise them on demand when an open lot or pending order needs one.
    """
    scan_ts_list = sorted(set(pd.Timestamp(s) for s in scan_times))
    # Normalize tz on every scan timestamp.
    scan_ts_list = [
        s.tz_localize("UTC") if s.tzinfo is None else s.tz_convert("UTC")
        for s in scan_ts_list
    ]

    # Poll-tick window: from the first scan (or session open) to 16:00 ET.
    eod_et = pd.Timestamp(
        _dt.datetime.combine(session_date, eod_clock), tz="America/New_York"
    ).tz_convert("UTC")
    if scan_ts_list:
        window_start = scan_ts_list[0]
    else:
        # No scans — anchor the window at 09:30 ET so EOD_MARK still fires.
        window_start = pd.Timestamp(
            _dt.datetime.combine(session_date, _dt.time(9, 30)),
            tz="America/New_York",
        ).tz_convert("UTC")

    events: list[Event] = []
    for ts in scan_ts_list:
        events.append(Event(timestamp=ts, type=EventType.SCAN, payload={
            "scan_ts": ts, "session_date": session_date,
        }))

    for ts in _ticks_between(
        window_start, eod_et, cadence.protection_poll_interval_seconds,
    ):
        events.append(Event(
            timestamp=ts, type=EventType.PROTECTION_CHECK,
            payload={"session_date": session_date},
        ))

    # FILL_POLL preload: a marker for when the dispatcher should sweep pending
    # parent orders. Distinct from PROTECTION_CHECK because the fill-side cap
    # may diverge from the protection-side cap on a custom config.
    for ts in _ticks_between(
        window_start, eod_et, cadence.fill_poll_interval_seconds,
    ):
        events.append(Event(
            timestamp=ts, type=EventType.QUOTE,
            payload={"session_date": session_date, "source": "fill_poll"},
        ))

    for ts in _ticks_between(
        window_start, eod_et, cadence.time_stop_check_interval_seconds,
    ):
        events.append(Event(
            timestamp=ts, type=EventType.TIME_STOP_CHECK,
            payload={"session_date": session_date},
        ))

    events.append(Event(
        timestamp=eod_et, type=EventType.EOD_MARK,
        payload={"session_date": session_date},
    ))

    return events


# ---- legacy per-scan helper (kept stable for SCAN dispatch) ----------------


def _call_quote_supplier(
    quote_supplier: Callable[..., Optional[dict]], symbol: str, scan_ts: Any, max_age: int
) -> Optional[dict]:
    """Call ``quote_supplier`` tolerating both the 2-arg and 3-arg signatures.

    Phase 6 quote suppliers take ``(symbol, ts, max_age_seconds)``; older test
    suppliers take ``(symbol, ts)``. Try the 3-arg form first, fall back to
    2-arg on a ``TypeError``.
    """
    try:
        return quote_supplier(symbol, scan_ts, max_age)
    except TypeError:
        return quote_supplier(symbol, scan_ts)


def run_one_scan(
    *,
    cfg: Mapping[str, Any],
    universe_snapshot: Mapping[str, Any],
    daily_cache: pd.DataFrame | None,
    volume_curve: pd.DataFrame | None,
    state: dict[str, Any],
    scan_ts: Any,
    bars_supplier: Callable[[str, Any], pd.DataFrame | None],
    consumer: StrategyConsumer,
    quote_supplier: Optional[Callable[..., Optional[dict]]] = None,
    forward_minute_supplier: Optional[Callable[[str, Any], pd.DataFrame | None]] = None,
) -> tuple[ScanResult, list[StrategyConsumerResult]]:
    """Run one scan tick and consume each emitted candidate.

    Retained verbatim from the pre-Phase-4 module so the SCAN handler in
    :mod:`sim.backtester` still calls it. ``quote_supplier`` resolves the
    historical quote per candidate (Phase 6). ``forward_minute_supplier``
    returns the minute path forward from ``scan_ts`` so a marketable-limit fill
    can detect a timeout.
    """
    scan_result = evaluate_one_scan(
        cfg=cfg, universe_snapshot=universe_snapshot, daily_cache=daily_cache,
        volume_curve=volume_curve, state=state, scan_ts=scan_ts,
        bars_supplier=bars_supplier,
    )
    max_quote_age = int((cfg.get("execution") or {}).get("max_quote_age_seconds", 5))
    consumer_results: list[StrategyConsumerResult] = []
    for ev in scan_result.emitted:
        q = (
            _call_quote_supplier(quote_supplier, ev["symbol"], scan_ts, max_quote_age)
            if quote_supplier
            else None
        )
        # Realism Phase 6: record quote presence for the coverage gate. A row
        # counts as covered only when a real *historical* quote came back.
        is_historical = bool(q) and str((q or {}).get("source", "")) == "historical"
        scan_result.quote_coverage.append({
            "symbol": ev["symbol"],
            "scan_ts": str(scan_ts),
            "quote_present": is_historical,
            "quote_age_seconds": float((q or {}).get("quote_age_seconds", 0.0) or 0.0),
        })
        fwd = forward_minute_supplier(ev["symbol"], scan_ts) if forward_minute_supplier else None
        cr = consumer.consume(
            ev, decision_ts=scan_ts, historical_quote=q, forward_minute_bars=fwd
        )
        consumer_results.append(cr)
    return scan_result, consumer_results
