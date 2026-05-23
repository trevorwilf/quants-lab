"""Phase 4 — unit tests for :mod:`sim.event_loop`.

Covers the primitives that drive the event-driven backtester:

* :class:`EventType` priority ordering (a same-timestamp PROTECTION_CHECK
  must dispatch before a SCAN so a slot released at 10:05 is visible at
  the 10:05 scan).
* :class:`EventQueue` chronological pop order with stable tiebreaks.
* :class:`CadenceConfig` resolution from a backtester config.
* :func:`preload_session_events` SCAN / PROTECTION_CHECK / FILL_POLL /
  TIME_STOP_CHECK / EOD_MARK count + ordering.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.sim.event_loop import (
    CadenceConfig,
    Event,
    EventQueue,
    EventType,
    preload_session_events,
)


def test_event_type_priority_ordering() -> None:
    """At equal timestamps, PROTECTION_CHECK dispatches before SCAN.

    Live: a 10:00 stop's protection check must update Portfolio.state BEFORE
    the 10:00 scan reads ``daily_realized_pnl``. The IntEnum value of each
    EventType doubles as the dispatch priority — lower wins.
    """
    assert EventType.PROTECTION_CHECK < EventType.SCAN
    assert EventType.CHILD_FILL < EventType.PARENT_FILL
    assert EventType.PARENT_FILL < EventType.PARENT_ACK
    assert EventType.EOD_MARK > EventType.SCAN  # EOD fires last


def test_event_queue_chronological_pop() -> None:
    """Events pop in ``(timestamp, priority, sequence)`` order."""
    q = EventQueue()
    t0 = pd.Timestamp("2024-09-04T14:00:00Z")
    q.push(Event(timestamp=t0 + pd.Timedelta(minutes=5), type=EventType.SCAN))
    q.push(Event(timestamp=t0, type=EventType.SCAN))
    q.push(Event(timestamp=t0 + pd.Timedelta(minutes=2), type=EventType.PROTECTION_CHECK))
    out = []
    while not q.empty():
        out.append(q.pop())
    assert [e.timestamp for e in out] == [
        t0, t0 + pd.Timedelta(minutes=2), t0 + pd.Timedelta(minutes=5),
    ]


def test_event_queue_same_ts_priority_then_sequence() -> None:
    """Same-timestamp events sort by priority then by push order."""
    q = EventQueue()
    t = pd.Timestamp("2024-09-04T14:00:00Z")
    # Push SCAN before PROTECTION_CHECK so we know the tiebreaker prefers
    # priority over sequence.
    q.push(Event(timestamp=t, type=EventType.SCAN, payload={"tag": "scan-1"}))
    q.push(Event(timestamp=t, type=EventType.PROTECTION_CHECK, payload={"tag": "prot-1"}))
    q.push(Event(timestamp=t, type=EventType.PROTECTION_CHECK, payload={"tag": "prot-2"}))
    out = [q.pop() for _ in range(3)]
    # Priority order: PROTECTION_CHECK (10) < SCAN (60). Two PROTECTION_CHECK
    # events at the same priority pop in FIFO push order.
    assert out[0].type == EventType.PROTECTION_CHECK
    assert out[0].payload["tag"] == "prot-1"
    assert out[1].type == EventType.PROTECTION_CHECK
    assert out[1].payload["tag"] == "prot-2"
    assert out[2].type == EventType.SCAN


def test_event_queue_peek_does_not_remove() -> None:
    q = EventQueue()
    t = pd.Timestamp("2024-09-04T14:00:00Z")
    q.push(Event(timestamp=t, type=EventType.SCAN))
    assert q.peek() is not None
    assert len(q) == 1
    _ = q.pop()
    assert q.empty()
    assert q.peek() is None


def test_cadence_config_defaults() -> None:
    """Empty cfg → live-contract defaults (60 / 5 / 5 / 60)."""
    c = CadenceConfig.from_cfg({})
    assert c.scan_interval_seconds == 60
    assert c.fill_poll_interval_seconds == 5
    assert c.protection_poll_interval_seconds == 5
    assert c.time_stop_check_interval_seconds == 60


def test_cadence_config_reads_session_loop() -> None:
    """``session.loop_interval_seconds`` is the default for the fill/protection polls."""
    c = CadenceConfig.from_cfg({"session": {"loop_interval_seconds": 10}})
    assert c.fill_poll_interval_seconds == 10
    assert c.protection_poll_interval_seconds == 10
    # The scan + time-stop cadences keep their own defaults.
    assert c.scan_interval_seconds == 60
    assert c.time_stop_check_interval_seconds == 60


def test_cadence_config_simulation_overrides() -> None:
    """``simulation.*`` fields override the loop-interval default."""
    c = CadenceConfig.from_cfg({
        "session": {"loop_interval_seconds": 10, "scan_interval_seconds": 30},
        "simulation": {
            "protection_poll_interval_seconds": 3,
            "fill_poll_interval_seconds": 7,
            "time_stop_check_interval_seconds": 120,
        },
    })
    assert c.scan_interval_seconds == 30
    assert c.fill_poll_interval_seconds == 7
    assert c.protection_poll_interval_seconds == 3
    assert c.time_stop_check_interval_seconds == 120


def test_preload_session_events_emits_scans_and_eod() -> None:
    """The preload contains every SCAN + an EOD_MARK + poll ticks."""
    sd = _dt.date(2024, 9, 4)
    scan_times = [
        pd.Timestamp(f"{sd}T13:45:00Z"),
        pd.Timestamp(f"{sd}T14:00:00Z"),
    ]
    cadence = CadenceConfig(
        scan_interval_seconds=60, fill_poll_interval_seconds=60,
        protection_poll_interval_seconds=60, time_stop_check_interval_seconds=60,
    )
    events = preload_session_events(
        session_date=sd, scan_times=scan_times, cadence=cadence,
    )
    types = [e.type for e in events]
    assert types.count(EventType.SCAN) == 2
    assert types.count(EventType.EOD_MARK) == 1


def test_preload_session_events_eod_is_at_1600_et() -> None:
    sd = _dt.date(2024, 9, 4)
    events = preload_session_events(
        session_date=sd,
        scan_times=[pd.Timestamp(f"{sd}T13:45:00Z")],
        cadence=CadenceConfig(),
    )
    eod = next(e for e in events if e.type == EventType.EOD_MARK)
    # 16:00 ET = 20:00 UTC during EDT (Sep 4 is EDT).
    assert eod.timestamp == pd.Timestamp("2024-09-04T20:00:00Z")


def test_preload_session_events_protection_tick_count() -> None:
    """5s protection cadence between 09:45 ET and 16:00 ET = 4500 ticks."""
    sd = _dt.date(2024, 9, 4)
    scan_times = [pd.Timestamp(f"{sd}T13:45:00Z")]  # 09:45 ET
    cadence = CadenceConfig(
        scan_interval_seconds=60,
        fill_poll_interval_seconds=60,  # keep this big so we count only protection
        protection_poll_interval_seconds=5,
        time_stop_check_interval_seconds=60,
    )
    events = preload_session_events(
        session_date=sd, scan_times=scan_times, cadence=cadence,
    )
    n_prot = sum(1 for e in events if e.type == EventType.PROTECTION_CHECK)
    # 6h 15m = 22_500 seconds → 4_500 5-second ticks.
    assert n_prot == 4_500
