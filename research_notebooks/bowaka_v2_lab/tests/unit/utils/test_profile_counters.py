"""ProfileCounters fast-path + no-op default (speedup report §10.0, §11.1).

Phase 0 wires increments at the supplier/dispatcher/scanner/artifact sites but
gates them on a process-level boolean (default ``False``). These tests prove
the increments don't fire when the flag is off and DO fire when the flag is on
inside an active context.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.utils.profile_counters import (
    ProfileCounters,
    counters_enabled,
    current_profile_counters,
    profile_counters_context,
    set_counters_enabled,
)


def test_counters_default_to_zero():
    c = ProfileCounters()
    snap = c.snapshot()
    assert snap["minute_supplier_calls"] == 0
    assert snap["minute_parquet_reads"] == 0
    assert snap["quote_supplier_calls"] == 0
    assert snap["quote_parquet_reads"] == 0
    assert snap["daily_cache_builds"] == 0
    assert snap["event_count_processed"] == 0
    assert snap["gate_dump_rows_constructed"] == 0
    assert snap["artifact_bytes_written"] == 0


def test_inc_increments_named_fields():
    c = ProfileCounters()
    c.inc(minute_supplier_calls=1, quote_supplier_calls=3, daily_cache_builds=2)
    snap = c.snapshot()
    assert snap["minute_supplier_calls"] == 1
    assert snap["quote_supplier_calls"] == 3
    assert snap["daily_cache_builds"] == 2


def test_inc_stores_unknown_keys_in_extra():
    c = ProfileCounters()
    c.inc(foo=4, bar=2)
    c.inc(foo=1)
    snap = c.snapshot()
    assert snap["foo"] == 5
    assert snap["bar"] == 2


def test_reset_clears_everything():
    c = ProfileCounters()
    c.inc(minute_supplier_calls=7, foo=3)
    c.reset()
    snap = c.snapshot()
    assert snap["minute_supplier_calls"] == 0
    assert "foo" not in snap


def test_counters_default_disabled():
    # Coming into a fresh test process the flag is False unless a prior test
    # forgot to restore it. The profile_counters_context fixture restores it.
    assert counters_enabled() is False


def test_context_manager_enables_then_restores():
    assert counters_enabled() is False
    with profile_counters_context(enable=True) as c:
        assert counters_enabled() is True
        c.inc(minute_supplier_calls=2)
        assert current_profile_counters().minute_supplier_calls == 2
    # Context exited — flag back to off, ContextVar reset (lookup raises).
    assert counters_enabled() is False
    with pytest.raises(LookupError):
        current_profile_counters()


def test_context_manager_can_run_disabled_for_supply_only():
    """``enable=False`` binds the counters but leaves the flag off so the
    benchmarks can compare a hot path with vs without counters."""
    with profile_counters_context(enable=False) as c:
        assert counters_enabled() is False
        c.inc(minute_supplier_calls=4)  # still mutable, just not auto-incremented
        assert c.snapshot()["minute_supplier_calls"] == 4


def test_set_counters_enabled_round_trip():
    set_counters_enabled(True)
    try:
        assert counters_enabled() is True
        set_counters_enabled(False)
        assert counters_enabled() is False
    finally:
        set_counters_enabled(False)


def test_nested_contexts_restore_outer_counters():
    with profile_counters_context(enable=True) as outer:
        outer.inc(minute_supplier_calls=1)
        with profile_counters_context(enable=True) as inner:
            inner.inc(minute_supplier_calls=10)
            assert current_profile_counters() is inner
            assert inner.snapshot()["minute_supplier_calls"] == 10
        # Outer should be the active counter again.
        assert current_profile_counters() is outer
        assert outer.snapshot()["minute_supplier_calls"] == 1
