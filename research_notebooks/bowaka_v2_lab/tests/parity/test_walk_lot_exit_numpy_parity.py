"""Differential parity lock — numpy fast-path walk vs the pandas reference.

Per-trial sim speedup: :func:`bowaka_v2_lab.sim.exits.walk_lot_exit` dispatches a
numeric-OHLC minute frame to :func:`_walk_lot_exit_numpy` (pre-extracted numpy
arrays, ``pd.Timestamp`` only on the exit bar) instead of
:func:`_walk_lot_exit_pandas` (``df.iterrows()`` + per-bar ``Series`` /
``tz_convert`` — the profiled hot spot). The numeric work is the SAME IEEE-754
double arithmetic, so the two MUST produce byte-identical ``ExitEvent`` objects
and ``FadeTelemetry`` rows.

This module proves that directly: it drives BOTH production implementations with
identical inputs over (a) hand-built edge cases for every exit branch and (b) a
seeded fuzzer of ~400 randomized lots / minute-paths / configs / suppliers, and
asserts every output field is exactly equal (NaN-aware). The pandas function is
the frozen oracle (its behaviour defines correctness); a divergence here means
the fast path changed a result and is a hard failure — the whole point is that
the 5000-trial study's accuracy is untouched.
"""
from __future__ import annotations

import datetime as _dt
import math
import random

import numpy as np
import pandas as pd
import pytest

from bowaka_v2_lab.sim.exits import (
    FadeTelemetry,
    _exit_walk_fast_eligible,
    _walk_lot_exit_numpy,
    _walk_lot_exit_pandas,
)
from bowaka_v2_lab.sim.portfolio import Position

_ET = "America/New_York"


# --------------------------------------------------------------------------
# Comparison helpers
# --------------------------------------------------------------------------
def _f_eq(a, b) -> bool:
    """Exact float equality, treating NaN == NaN (we want byte-identity, not a
    tolerance — the two paths run the same double arithmetic)."""
    af, bf = float(a), float(b)
    if math.isnan(af) and math.isnan(bf):
        return True
    return af == bf


def _assert_exit_equal(ref, fast, ctx: str) -> None:
    if ref is None or fast is None:
        assert ref is None and fast is None, (
            f"{ctx}: one path exited and the other did not — "
            f"ref={ref!r} fast={fast!r}"
        )
        return
    assert ref.symbol == fast.symbol, f"{ctx}: symbol"
    assert ref.exit_date == fast.exit_date, f"{ctx}: exit_date {ref.exit_date} != {fast.exit_date}"
    assert ref.exit_reason == fast.exit_reason, (
        f"{ctx}: exit_reason {ref.exit_reason!r} != {fast.exit_reason!r}"
    )
    assert _f_eq(ref.exit_price, fast.exit_price), (
        f"{ctx}: exit_price {ref.exit_price!r} != {fast.exit_price!r}"
    )
    assert ref.ambiguous_bar_resolved == fast.ambiguous_bar_resolved, f"{ctx}: ambiguous"
    assert ref.position_id == fast.position_id, f"{ctx}: position_id"
    assert ref.exit_timestamp == fast.exit_timestamp, (
        f"{ctx}: exit_timestamp {ref.exit_timestamp!r} != {fast.exit_timestamp!r}"
    )
    assert _f_eq(ref.mfe_pct, fast.mfe_pct), f"{ctx}: mfe_pct {ref.mfe_pct!r} != {fast.mfe_pct!r}"
    assert _f_eq(ref.mae_pct, fast.mae_pct), f"{ctx}: mae_pct {ref.mae_pct!r} != {fast.mae_pct!r}"
    assert _f_eq(ref.exit_slippage_bps, fast.exit_slippage_bps), (
        f"{ctx}: slippage {ref.exit_slippage_bps!r} != {fast.exit_slippage_bps!r}"
    )
    assert ref.halted == fast.halted, f"{ctx}: halted"


def _assert_telemetry_equal(ref_t, fast_t, ctx: str) -> None:
    assert len(ref_t) == len(fast_t), (
        f"{ctx}: fade_telemetry length {len(ref_t)} != {len(fast_t)}"
    )
    for j, (a, b) in enumerate(zip(ref_t, fast_t)):
        assert a.symbol == b.symbol, f"{ctx}: telemetry[{j}].symbol"
        assert a.position_id == b.position_id, f"{ctx}: telemetry[{j}].position_id"
        assert a.eval_date == b.eval_date, f"{ctx}: telemetry[{j}].eval_date"
        assert a.eval_timestamp == b.eval_timestamp, f"{ctx}: telemetry[{j}].eval_timestamp"
        assert _f_eq(a.score, b.score), f"{ctx}: telemetry[{j}].score"
        assert a.threshold_name == b.threshold_name, f"{ctx}: telemetry[{j}].threshold_name"
        assert _f_eq(a.threshold_value, b.threshold_value), f"{ctx}: telemetry[{j}].threshold_value"
        assert a.would_exit_reason == b.would_exit_reason, f"{ctx}: telemetry[{j}].reason"


def _run_both(pos: Position, bars: pd.DataFrame, *, ctx: str, **kwargs) -> None:
    """Drive both implementations with identical args; assert identical output.

    fade_telemetry_out lists are kept separate (the call appends to them) and
    compared. Any supplier passed in must be pure so both calls see the same
    answers.
    """
    ref_tel: list = []
    fast_tel: list = []
    ref = _walk_lot_exit_pandas(pos, bars, fade_telemetry_out=ref_tel, **kwargs)
    fast = _walk_lot_exit_numpy(pos, bars, fade_telemetry_out=fast_tel, **kwargs)
    _assert_exit_equal(ref, fast, ctx)
    _assert_telemetry_equal(ref_tel, fast_tel, ctx)


# --------------------------------------------------------------------------
# Fixture builders
# --------------------------------------------------------------------------
def _lot(
    *, entry_price=100.0, stop_pct=0.08, target_pct=0.15, max_hold_days=3,
    entry_date=_dt.date(2024, 9, 4), entry_clock="09:30",
    stop_price=None, target_price=None, qty=10,
) -> Position:
    base = pd.Timestamp(f"{entry_date} {entry_clock}", tz=_ET).tz_convert("UTC")
    return Position(
        symbol="AAA", entry_date=entry_date, entry_price=entry_price, qty=qty,
        stop_pct=stop_pct, target_pct=target_pct, max_hold_days=max_hold_days,
        entry_session=entry_date, entry_timestamp=base.isoformat(),
        stop_price=stop_price, target_price=target_price,
    )


def _path(rows: list[dict], *, start_date=_dt.date(2024, 9, 4), start_clock="09:31",
          cadence_min=1) -> pd.DataFrame:
    """Minute frame at ``cadence_min`` from ``start_date start_clock`` ET (UTC ts)."""
    base = pd.Timestamp(f"{start_date} {start_clock}", tz=_ET).tz_convert("UTC")
    out = []
    for i, r in enumerate(rows):
        out.append({
            "symbol": "AAA",
            "timestamp": base + pd.Timedelta(minutes=i * cadence_min),
            "open": r["o"], "high": r["h"], "low": r["l"], "close": r["c"],
            "volume": r.get("v", 1000.0),
        })
    return pd.DataFrame(out)


# --------------------------------------------------------------------------
# Deterministic edge cases — one per exit branch
# --------------------------------------------------------------------------
def test_eligibility_gate_numeric_vs_object() -> None:
    good = _path([{"o": 100, "h": 100.5, "l": 99.5, "c": 100}])
    assert _exit_walk_fast_eligible(good) is True
    obj = good.copy()
    obj["high"] = obj["high"].astype(object)
    assert _exit_walk_fast_eligible(obj) is False  # object dtype -> reference
    assert _exit_walk_fast_eligible(good.drop(columns=["low"])) is False
    assert _exit_walk_fast_eligible(good.iloc[0:0]) is False
    assert _exit_walk_fast_eligible(None) is False


def test_plain_stop() -> None:
    bars = _path([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 100.5, "l": 91.0, "c": 95},   # low 91 <= stop 92
    ])
    _run_both(_lot(stop_price=92.0, target_price=115.0), bars, ctx="plain_stop")


def test_plain_target() -> None:
    bars = _path([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 116.0, "l": 99.0, "c": 110},  # high 116 >= target 115
    ])
    _run_both(_lot(stop_price=92.0, target_price=115.0), bars, ctx="plain_target")


def test_gap_stop_and_gap_target() -> None:
    gap_stop = _path([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 90.0, "h": 91.0, "l": 88.0, "c": 89},   # open 90 <= stop 92 -> gap
    ])
    _run_both(_lot(stop_price=92.0, target_price=115.0), gap_stop, ctx="gap_stop")
    gap_tgt = _path([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 120.0, "h": 121.0, "l": 119.0, "c": 120},  # open 120 >= target 115
    ])
    _run_both(_lot(stop_price=92.0, target_price=115.0), gap_tgt, ctx="gap_target")


@pytest.mark.parametrize("res", ["conservative", "optimistic", "random_with_seed"])
def test_same_minute_tie(res: str) -> None:
    bars = _path([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 116.0, "l": 91.0, "c": 100},  # both brackets in one bar
    ])
    _run_both(_lot(stop_price=92.0, target_price=115.0), bars,
              ctx=f"same_minute_{res}", same_minute_resolution=res, seed=7)


def test_time_stop_with_and_without_quote() -> None:
    bars = _path([{"o": 100, "h": 100.3, "l": 99.7, "c": 100} for _ in range(20)],
                 start_clock="15:40")  # crosses 15:45 default time-stop clock
    cfg = {"time_stop": {"enabled": True, "exit_time": "15:45"}}
    _run_both(_lot(stop_price=70.0, target_price=130.0), bars, ctx="time_stop_noquote",
              exit_cfg=cfg)
    quote = lambda sym, ts: {"bid": 99.42}  # noqa: E731
    _run_both(_lot(stop_price=70.0, target_price=130.0), bars, ctx="time_stop_quote",
              exit_cfg=cfg, quote_supplier=quote)


def test_max_hold_fallback_and_inline() -> None:
    # A quiet single-session path that never trips a bracket -> the loop ends
    # and the max-hold fallback closes on the last bar.
    bars = _path([{"o": 100, "h": 100.2, "l": 99.8, "c": 100} for _ in range(10)])
    _run_both(_lot(stop_price=50.0, target_price=200.0, max_hold_days=1), bars,
              ctx="max_hold_fallback", exit_cfg={"time_stop": {"enabled": False}})
    # Inline max-hold: a path reaching 15:59 on the exit session.
    long = _path([{"o": 100, "h": 100.2, "l": 99.8, "c": 100} for _ in range(25)],
                 start_clock="15:40")
    _run_both(_lot(stop_price=50.0, target_price=200.0, max_hold_days=1), long,
              ctx="max_hold_inline", exit_cfg={"time_stop": {"enabled": False}})


@pytest.mark.parametrize("active", [True, False])
def test_signal_fade_active_and_telemetry(active: bool) -> None:
    cfg = {
        "time_stop": {"enabled": False},
        "signal_fade": {
            "enabled": True,
            "initial_mode": "telemetry_then_active_after_validation",
            "activation_state": "active" if active else "telemetry",
            "eval_time": "15:45",
            "score_thresholds": {"soft": 0.34, "hard": 0.50, "critical": 0.67},
            "exit_on": ["hard", "critical"],
        },
    }
    bars = _path([{"o": 100, "h": 100.3, "l": 99.7, "c": 100} for _ in range(20)],
                 start_clock="15:40")
    _run_both(_lot(stop_price=70.0, target_price=130.0), bars,
              ctx=f"fade_active={active}", exit_cfg=cfg,
              signal_score_fn=lambda pos, ts: 0.40,
              quote_supplier=lambda sym, ts: {"bid": 99.5})


def test_severe_halt_path() -> None:
    bars = _path([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 100.5, "l": 91.0, "c": 95},   # trips stop -> severe halt
        {"o": 95, "h": 96.0, "l": 94.0, "c": 95},     # 60s later -> halt resume
        {"o": 95, "h": 96.0, "l": 94.0, "c": 95},
    ])
    _run_both(_lot(stop_price=92.0, target_price=115.0), bars, ctx="severe_halt",
              cost_stress="severe", quote_supplier=lambda sym, ts: {"bid": 94.9})


def test_until_ts_window_leaves_lot_open() -> None:
    bars = _path([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 100.5, "l": 91.0, "c": 95},   # stop, but after the window
    ])
    until = pd.Timestamp("2024-09-04 09:32", tz=_ET).tz_convert("UTC")
    _run_both(_lot(stop_price=92.0, target_price=115.0), bars, ctx="until_ts",
              until_ts=until)


def test_status_supplier_defers() -> None:
    bars = _path([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 100.5, "l": 91.0, "c": 95},   # would stop, but halted
        {"o": 100, "h": 100.5, "l": 91.0, "c": 95},   # not halted -> stop here
    ])

    def status(sym, ts):
        et = pd.Timestamp(ts).tz_convert(_ET)
        return {"status": "halted"} if (et.hour, et.minute) == (9, 32) else None

    _run_both(_lot(stop_price=92.0, target_price=115.0), bars, ctx="status_defer",
              status_supplier=status)


def test_nan_cells_and_duplicate_and_unsorted_timestamps() -> None:
    bars = _path([
        {"o": 100, "h": float("nan"), "l": 99.8, "c": 100},   # NaN high
        {"o": float("nan"), "h": 100.5, "l": float("nan"), "c": float("nan")},
        {"o": 100, "h": 116.0, "l": 99.0, "c": 110},          # target
    ])
    _run_both(_lot(stop_price=92.0, target_price=115.0), bars, ctx="nan_cells")
    # Duplicate + unsorted timestamps: both impls call df.sort_values identically.
    dup = _path([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 116.0, "l": 91.0, "c": 100},
    ])
    dup = pd.concat([dup, dup.iloc[[1]]], ignore_index=True)  # duplicate the tie bar
    shuffled = dup.iloc[::-1].reset_index(drop=True)          # reverse order
    _run_both(_lot(stop_price=92.0, target_price=115.0), shuffled, ctx="dup_unsorted",
              same_minute_resolution="random_with_seed", seed=3)


# --------------------------------------------------------------------------
# PB.1 — sell-side spread-crossing exits (exits.cross_spread)
# --------------------------------------------------------------------------
def _cfg_xspread(on: bool) -> dict:
    return {"time_stop": {"enabled": False}, "cross_spread": on}


def _stop_bars() -> pd.DataFrame:
    return _path([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 100.5, "l": 91.0, "c": 95},   # low 91 <= stop 92
    ])


def test_cross_spread_off_fills_exactly_at_bracket():
    # Knob OFF: even WITH a bid well below the stop, the fill is the exact bracket
    # price and slippage is 0 — byte-identical to the legacy engine.
    quote = lambda sym, ts: {"bid": 90.0}  # noqa: E731
    ev = _walk_lot_exit_pandas(_lot(stop_price=92.0, target_price=115.0), _stop_bars(),
                               exit_cfg=_cfg_xspread(False), quote_supplier=quote)
    assert ev.exit_reason == "stop"
    assert ev.exit_price == 92.0
    assert ev.exit_slippage_bps == 0.0


def test_cross_spread_stop_fills_at_bid_with_giveup():
    quote = lambda sym, ts: {"bid": 90.0}  # noqa: E731 — bid below the stop
    pos = _lot(stop_price=92.0, target_price=115.0)
    ev = _walk_lot_exit_pandas(pos, _stop_bars(), exit_cfg=_cfg_xspread(True),
                               quote_supplier=quote, cost_stress="conservative")
    assert ev.exit_reason == "stop"
    # fill = min(92, 90*(1 - 5/1e4))  (conservative half_spread_bps = 5)
    assert ev.exit_price == pytest.approx(90.0 * (1 - 5.0 / 1e4))
    assert ev.exit_price < 92.0
    assert ev.exit_slippage_bps < 0.0  # adverse give-up
    _run_both(pos, _stop_bars(), ctx="xspread_stop", exit_cfg=_cfg_xspread(True),
              quote_supplier=quote, cost_stress="conservative")


def test_cross_spread_no_quote_falls_back_to_bracket():
    pos = _lot(stop_price=92.0, target_price=115.0)
    ev = _walk_lot_exit_pandas(pos, _stop_bars(), exit_cfg=_cfg_xspread(True))  # no quote
    assert ev.exit_reason == "stop"
    assert ev.exit_price == 92.0  # no bid -> legacy bracket fill
    assert ev.exit_slippage_bps == 0.0


def test_cross_spread_target_gives_up_to_bid():
    bars = _path([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 116.0, "l": 99.0, "c": 110},  # high 116 >= target 115
    ])
    quote = lambda sym, ts: {"bid": 114.0}  # noqa: E731 — bid below target
    pos = _lot(stop_price=92.0, target_price=115.0)
    ev = _walk_lot_exit_pandas(pos, bars, exit_cfg=_cfg_xspread(True),
                               quote_supplier=quote, cost_stress="conservative")
    assert ev.exit_reason == "target"
    assert ev.exit_price == pytest.approx(min(115.0, 114.0 * (1 - 5.0 / 1e4)))
    assert ev.exit_price < 115.0
    assert ev.exit_slippage_bps < 0.0
    _run_both(pos, bars, ctx="xspread_target", exit_cfg=_cfg_xspread(True),
              quote_supplier=quote, cost_stress="conservative")


# --------------------------------------------------------------------------
# PB.2 — sell-side size cap + sqrt-impact (exits.participation_cap)
# --------------------------------------------------------------------------
def _cfg_pcap(cap, *, cross_spread=False):
    c = {"time_stop": {"enabled": False}, "cross_spread": cross_spread}
    if cap is not None:
        c["participation_cap"] = cap
    return c


def test_participation_cap_off_is_byte_identical():
    # cap absent -> exact bracket fill / 0 slip even for a lot huge vs the minute.
    pos = _lot(stop_price=92.0, target_price=115.0, qty=5000)  # 5000 vs 1000-share min
    ev = _walk_lot_exit_pandas(pos, _stop_bars(), exit_cfg={"time_stop": {"enabled": False}})
    assert ev.exit_reason == "stop"
    assert ev.exit_price == 92.0
    assert ev.exit_slippage_bps == 0.0


def test_participation_cap_applies_capped_sqrt_impact():
    pos = _lot(stop_price=92.0, target_price=115.0, qty=5000)  # participation 5.0 -> cap 0.10
    ev = _walk_lot_exit_pandas(pos, _stop_bars(), exit_cfg=_cfg_pcap(0.10),
                               cost_stress="conservative")
    assert ev.exit_reason == "stop"
    exp_impact = 10.0 * math.sqrt(0.10) * 2.0  # impact_coef * sqrt(cap) * conservative mult
    assert ev.exit_price == pytest.approx(92.0 * (1 - exp_impact / 1e4))
    assert ev.exit_price < 92.0
    assert ev.exit_slippage_bps < 0.0
    _run_both(pos, _stop_bars(), ctx="pcap_stop", exit_cfg=_cfg_pcap(0.10),
              cost_stress="conservative")


def test_participation_cap_small_lot_uses_actual_participation():
    pos = _lot(stop_price=92.0, target_price=115.0, qty=50)  # 50/1000 = 0.05 < cap 0.10
    ev = _walk_lot_exit_pandas(pos, _stop_bars(), exit_cfg=_cfg_pcap(0.10), cost_stress="base")
    exp_impact = 10.0 * math.sqrt(0.05) * 1.0  # base mult = 1.0
    assert ev.exit_price == pytest.approx(92.0 * (1 - exp_impact / 1e4))


def test_participation_cap_composes_with_cross_spread():
    quote = lambda sym, ts: {"bid": 90.0}  # noqa: E731
    pos = _lot(stop_price=92.0, target_price=115.0, qty=5000)
    ev = _walk_lot_exit_pandas(pos, _stop_bars(), exit_cfg=_cfg_pcap(0.10, cross_spread=True),
                               quote_supplier=quote, cost_stress="conservative")
    base = min(92.0, 90.0 * (1 - 5.0 / 1e4))    # PB.1 marketable base
    exp_impact = 10.0 * math.sqrt(0.10) * 2.0   # PB.2 impact on top
    assert ev.exit_price == pytest.approx(base * (1 - exp_impact / 1e4))
    _run_both(pos, _stop_bars(), ctx="pcap_xspread", exit_cfg=_cfg_pcap(0.10, cross_spread=True),
              quote_supplier=quote, cost_stress="conservative")


def test_exit_stress_mult_mirrors_buy_side():
    from bowaka_v2_lab.sim import exits as _ex
    from bowaka_v2_lab.sim import fills as _fl
    assert _ex._COST_STRESS_SLIPPAGE_MULT == _fl.COST_STRESS_SLIPPAGE_MULT


# --------------------------------------------------------------------------
# PB.3 — exit quote-age / no-quote handling (exits.require_fresh_quote)
# --------------------------------------------------------------------------
def _cfg_fresh(on, *, cross_spread=True, max_age=15):
    return {"time_stop": {"enabled": False}, "cross_spread": cross_spread,
            "require_fresh_quote": on, "max_quote_age_seconds": max_age}


def test_require_fresh_quote_off_uses_legacy_2arg_supplier():
    # Knob off: the 2-arg supplier is called as in PB.1 (no max-age gating).
    quote = lambda sym, ts: {"bid": 90.0}  # noqa: E731
    pos = _lot(stop_price=92.0, target_price=115.0)
    ev = _walk_lot_exit_pandas(pos, _stop_bars(), exit_cfg=_cfg_fresh(False),
                               quote_supplier=quote, cost_stress="conservative")
    assert ev.exit_price == pytest.approx(90.0 * (1 - 5.0 / 1e4))  # PB.1 bid fill


def test_require_fresh_quote_on_uses_fresh_bid():
    def quote(sym, ts, max_age_seconds=None):  # honors the freshness kwarg
        return {"bid": 90.0}
    pos = _lot(stop_price=92.0, target_price=115.0)
    ev = _walk_lot_exit_pandas(pos, _stop_bars(), exit_cfg=_cfg_fresh(True),
                               quote_supplier=quote, cost_stress="conservative")
    assert ev.exit_price == pytest.approx(90.0 * (1 - 5.0 / 1e4))
    _run_both(pos, _stop_bars(), ctx="fresh_ok", exit_cfg=_cfg_fresh(True),
              quote_supplier=quote, cost_stress="conservative")


def test_require_fresh_quote_on_widens_giveup_when_stale():
    def stale(sym, ts, max_age_seconds=None):  # stale/absent -> supplier returns None
        return None
    pos = _lot(stop_price=92.0, target_price=115.0)
    ev = _walk_lot_exit_pandas(pos, _stop_bars(), exit_cfg=_cfg_fresh(True),
                               quote_supplier=stale, cost_stress="conservative")
    assert ev.exit_reason == "stop"
    # widened give-up = bracket * (1 - 2*half_spread/1e4), NOT the clean bracket.
    assert ev.exit_price == pytest.approx(92.0 * (1 - 2.0 * 5.0 / 1e4))
    assert ev.exit_price < 92.0
    assert ev.exit_slippage_bps < 0.0
    _run_both(pos, _stop_bars(), ctx="fresh_stale", exit_cfg=_cfg_fresh(True),
              quote_supplier=stale, cost_stress="conservative")


# --------------------------------------------------------------------------
# Seeded fuzzer — broad input distribution
# --------------------------------------------------------------------------
def _rand_path(rng: random.Random, *, n: int, start_date: _dt.date,
               nan_rate: float) -> pd.DataFrame:
    """A random multi-session-ish minute path starting 09:31 ET on start_date."""
    rows = []
    px = 100.0
    for _ in range(n):
        drift = rng.uniform(-1.5, 1.5)
        px = max(1.0, px + drift)
        hi = px + abs(rng.uniform(0, 2.5))
        lo = px - abs(rng.uniform(0, 2.5))
        op = rng.uniform(lo, hi)
        cl = rng.uniform(lo, hi)
        if rng.random() < 0.04:  # occasional gap open
            op = px + rng.choice([-1, 1]) * rng.uniform(5, 20)
        row = {"o": op, "h": hi, "l": lo, "c": cl}
        if rng.random() < nan_rate:
            row[rng.choice(["o", "h", "l", "c"])] = float("nan")
        rows.append(row)
    # Span 1-3 sessions by chunking minutes across consecutive weekdays.
    base = pd.Timestamp(f"{start_date} 09:31", tz=_ET).tz_convert("UTC")
    ts = []
    cur = base
    per_session = rng.randint(15, 120)
    count = 0
    day = 0
    for _ in range(n):
        ts.append(cur)
        cur = cur + pd.Timedelta(minutes=1)
        count += 1
        if count >= per_session:
            count = 0
            day += 1
            # jump to the next calendar day 09:31 ET (calendar exactness is
            # irrelevant — both impls use the same max_hold_exit_session)
            nd = start_date + _dt.timedelta(days=day)
            cur = pd.Timestamp(f"{nd} 09:31", tz=_ET).tz_convert("UTC")
    df = pd.DataFrame({
        "symbol": "AAA",
        "timestamp": ts,
        "open": [r["o"] for r in rows],
        "high": [r["h"] for r in rows],
        "low": [r["l"] for r in rows],
        "close": [r["c"] for r in rows],
        "volume": 1000.0,
    })
    return df


def _rand_cfg(rng: random.Random) -> dict:
    cfg: dict = {}
    cfg["time_stop"] = {"enabled": rng.random() < 0.6,
                        "exit_time": rng.choice(["15:30", "15:45", "15:55"])}
    if rng.random() < 0.6:
        cfg["signal_fade"] = {
            "enabled": True,
            "initial_mode": rng.choice(
                ["telemetry_only", "telemetry_then_active_after_validation", "active"]),
            "activation_state": rng.choice(["telemetry", "active"]),
            "eval_time": rng.choice(["15:30", "15:45"]),
            "score_thresholds": {"soft": 0.34, "hard": 0.50, "critical": 0.67},
            "exit_on": ["hard", "critical"],
        }
    if rng.random() < 0.2:
        cfg["same_minute_tie"] = rng.choice(["stop_first", "target_first"])
    if rng.random() < 0.5:
        cfg["cross_spread"] = True  # PB.1 — exercise spread-crossing in the fuzzer
    if rng.random() < 0.4:
        cfg["participation_cap"] = rng.choice([0.05, 0.10, 0.25])  # PB.2 — size cap + impact
    if rng.random() < 0.4:
        cfg["require_fresh_quote"] = True  # PB.3 — quote-freshness gate
    return cfg


def test_fuzz_numpy_matches_reference() -> None:
    rng = random.Random(20260603)
    n_cases = 400
    for k in range(n_cases):
        entry_price = rng.uniform(20, 300)
        stop_pct = rng.uniform(0.02, 0.20)
        target_pct = rng.uniform(0.02, 0.30)
        max_hold = rng.randint(1, 4)
        pos = _lot(
            entry_price=entry_price, stop_pct=stop_pct, target_pct=target_pct,
            max_hold_days=max_hold,
            stop_price=(entry_price * (1 - stop_pct) if rng.random() < 0.8 else None),
            target_price=(entry_price * (1 + target_pct) if rng.random() < 0.8 else None),
            entry_clock=rng.choice(["09:30", "10:15", "13:00"]),
            qty=rng.choice([10, 100, 5000]),  # PB.2 — vary participation vs minute volume
        )
        # Scale the random path around this lot's entry price.
        n = rng.randint(5, 200)
        bars = _rand_path(rng, n=n, start_date=_dt.date(2024, 9, 4),
                          nan_rate=rng.choice([0.0, 0.0, 0.03]))
        scale = entry_price / 100.0
        for col in ("open", "high", "low", "close"):
            bars[col] = bars[col] * scale

        kwargs: dict = {
            "exit_cfg": _rand_cfg(rng),
            "same_minute_resolution": rng.choice(
                ["conservative", "optimistic", "random_with_seed"]),
            "cost_stress": rng.choice(["base", "base", "severe"]),
            "seed": rng.randint(0, 9999),
        }
        if rng.random() < 0.6:
            bid = rng.uniform(10, 320)
            kwargs["quote_supplier"] = (
                lambda b: (lambda sym, ts, max_age_seconds=None: {"bid": b}))(bid)
        if (cfg_fade := kwargs["exit_cfg"].get("signal_fade")) and rng.random() < 0.9:
            sc = rng.uniform(0.0, 1.0)
            kwargs["signal_score_fn"] = (lambda s: (lambda pos, ts: s))(sc)
        if rng.random() < 0.25:
            # bound the walk at a random minute inside the path
            cut_i = rng.randint(0, max(0, n - 1))
            kwargs["until_ts"] = pd.Timestamp(bars["timestamp"].iloc[cut_i])
        _run_both(pos, bars, ctx=f"fuzz#{k}", **kwargs)
