"""Phase 3 — scanner-state mutation parity.

After a full session, every key under ``state["in_play_pool"]``,
``symbol_last_emit_ts``, ``signal_emits_per_symbol_today`` and
``state["scanner_last_run_ts"]`` must match between the two paths.
Scanner state mutates on EMITTED candidates (not filled entries).
"""
from __future__ import annotations

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.scanner.scan_matrix_runtime import evaluate_one_scan_compat


def test_state_mutation_full_session(matrix_parity) -> None:
    fx = matrix_parity
    state_leg: dict = {}
    state_cmp: dict = {}
    for ts in fx.scan_times:
        evaluate_one_scan(
            cfg=fx.cfg, universe_snapshot=fx.universe, daily_cache=fx.daily_cache,
            volume_curve=None, state=state_leg, scan_ts=ts,
            bars_supplier=fx.bars_supplier, scan_context=fx.scan_context,
            collect_gate_dump=False,
        )
        evaluate_one_scan_compat(
            cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
            state=state_cmp, scan_context=fx.scan_context,
            universe_snapshot=fx.universe, volume_curve=None,
            collect_gate_dump=False,
        )
    assert state_leg.get("in_play_pool") == state_cmp.get("in_play_pool")
    assert state_leg.get("symbol_last_emit_ts") == state_cmp.get("symbol_last_emit_ts")
    assert (
        state_leg.get("signal_emits_per_symbol_today")
        == state_cmp.get("signal_emits_per_symbol_today")
    )
    assert state_leg.get("scanner_last_run_ts") == state_cmp.get("scanner_last_run_ts")
