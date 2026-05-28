"""Phase 3 — full-session compatibility-runtime parity.

Drives BOTH paths through every scan timestamp of the fixture session with
ONE threaded state dict each (so cooldown / per-day-emit / in-play state
evolves across scans), then asserts the cumulative emitted-event sequence,
the final state, and the rejection counts match end-to-end.
"""
from __future__ import annotations

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.scanner.scan_matrix_runtime import evaluate_one_scan_compat


def test_full_session_cumulative_parity(matrix_parity) -> None:
    fx = matrix_parity
    state_leg: dict = {}
    state_cmp: dict = {}
    emits_leg: list = []
    emits_cmp: list = []
    counts_leg: dict = {}
    counts_cmp: dict = {}

    for ts in fx.scan_times:
        r_leg = evaluate_one_scan(
            cfg=fx.cfg, universe_snapshot=fx.universe, daily_cache=fx.daily_cache,
            volume_curve=None, state=state_leg, scan_ts=ts,
            bars_supplier=fx.bars_supplier, scan_context=fx.scan_context,
            collect_gate_dump=False,
        )
        r_cmp = evaluate_one_scan_compat(
            cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
            state=state_cmp, scan_context=fx.scan_context,
            universe_snapshot=fx.universe, volume_curve=None,
            collect_gate_dump=False,
        )
        emits_leg.extend((e["symbol"], e["event_id"]) for e in r_leg.emitted)
        emits_cmp.extend((e["symbol"], e["event_id"]) for e in r_cmp.emitted)
        for k, v in r_leg.rejection_counts.items():
            counts_leg[k] = counts_leg.get(k, 0) + int(v)
        for k, v in r_cmp.rejection_counts.items():
            counts_cmp[k] = counts_cmp.get(k, 0) + int(v)

    assert emits_leg == emits_cmp
    assert counts_leg == counts_cmp
    assert state_leg.get("symbol_last_emit_ts") == state_cmp.get("symbol_last_emit_ts")
    assert (
        state_leg.get("signal_emits_per_symbol_today")
        == state_cmp.get("signal_emits_per_symbol_today")
    )
    assert state_leg.get("in_play_pool") == state_cmp.get("in_play_pool")
    assert state_leg.get("scanner_last_run_ts") == state_cmp.get("scanner_last_run_ts")
