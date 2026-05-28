"""Phase 4 — three-way full-session parity.

Drives legacy / compatibility / vectorized through every scan timestamp of
the fixture session with one threaded state dict each; asserts the
cumulative emitted-event sequence, final state, and rejection counts match.
"""
from __future__ import annotations

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.scanner.scan_matrix_runtime import evaluate_one_scan_compat
from bowaka_v2_lab.scanner.scan_matrix_vectorized import (
    evaluate_one_scan_vectorized,
)


def test_three_way_full_session_parity(matrix_parity) -> None:
    fx = matrix_parity
    s_leg: dict = {}
    s_cmp: dict = {}
    s_vec: dict = {}
    e_leg: list = []
    e_cmp: list = []
    e_vec: list = []
    c_leg: dict = {}
    c_cmp: dict = {}
    c_vec: dict = {}

    def _acc(counts, result):
        for k, v in result.rejection_counts.items():
            counts[k] = counts.get(k, 0) + int(v)

    for ts in fx.scan_times:
        r_leg = evaluate_one_scan(
            cfg=fx.cfg, universe_snapshot=fx.universe, daily_cache=fx.daily_cache,
            volume_curve=None, state=s_leg, scan_ts=ts,
            bars_supplier=fx.bars_supplier, scan_context=fx.scan_context,
            collect_gate_dump=False,
        )
        r_cmp = evaluate_one_scan_compat(
            cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
            state=s_cmp, scan_context=fx.scan_context,
            universe_snapshot=fx.universe, volume_curve=None, collect_gate_dump=False,
        )
        r_vec = evaluate_one_scan_vectorized(
            cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
            state=s_vec, scan_context=fx.scan_context,
            universe_snapshot=fx.universe, volume_curve=None, collect_gate_dump=False,
        )
        e_leg.extend((e["symbol"], e["event_id"]) for e in r_leg.emitted)
        e_cmp.extend((e["symbol"], e["event_id"]) for e in r_cmp.emitted)
        e_vec.extend((e["symbol"], e["event_id"]) for e in r_vec.emitted)
        _acc(c_leg, r_leg)
        _acc(c_cmp, r_cmp)
        _acc(c_vec, r_vec)

    assert e_leg == e_cmp == e_vec
    assert c_leg == c_cmp == c_vec
    for key in ("symbol_last_emit_ts", "signal_emits_per_symbol_today",
                "in_play_pool", "scanner_last_run_ts"):
        assert s_leg.get(key) == s_cmp.get(key) == s_vec.get(key), key
