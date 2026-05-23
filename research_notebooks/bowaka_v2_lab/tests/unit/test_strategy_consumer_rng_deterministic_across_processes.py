"""Audit P1-001: synthetic-quote RNG is deterministic across separate processes.

The pre-fix code seeded the RNG with Python's built-in ``hash()`` of
``(symbol, scan_ts)``. ``hash()`` is process-salted by ``PYTHONHASHSEED``, so
two identical runs in separate processes produced different synthetic quote
ages.

The fix uses ``hashlib.sha256(run_seed|symbol|scan_ts)`` so the seed is stable
across processes / runs. This test launches two fresh Python processes — each
with the default ``PYTHONHASHSEED=random`` — and asserts the quote ages are
identical.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap


_SCRIPT = textwrap.dedent(
    """
    import json
    from bowaka_v2_lab.sim.strategy_consumer import StrategyConsumer
    from bowaka_v2_lab.sim.broker import SimulatedBroker
    from bowaka_v2_lab.sim.portfolio import Portfolio
    import pandas as pd
    import datetime as _dt

    cfg = {
        # smoke_fixture -> quote_fallback_policy resolves to synthetic_calibrated
        "simulation": {"mode": "smoke_fixture"},
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                      "order_type": "marketable_limit",
                      "price_chase_gate": {"enabled": False},
                      "halt_gate": {"enabled": False}},
        "sizing": {"dollars_per_position": 5000, "max_position_dollars": 25000,
                   "sizing_mode": "fixed_dollar", "max_concurrent_positions": 50,
                   "min_order_notional": 100.0},
        "risk": {"max_total_entries_per_day": 99, "max_gross_exposure_pct": 0.99,
                 "daily_loss_pct": 0.99, "max_stopouts_per_day": 99,
                 "stop_trading_after_consecutive_stopouts": 99,
                 "max_lots_per_symbol": 5},
        "exits": {"stop_loss_pct": 0.02, "take_profit_pct": 0.05, "max_hold_days": 30},
        "scanner": {"min_signal_strength": 0.0},
        "backtest": {"cost_stress": "base"},
        "run": {"seed": 42},
    }
    p = Portfolio(initial_bankroll=1_000_000.0)
    p.begin_session(_dt.date(2024, 9, 4))
    consumer = StrategyConsumer(portfolio=p, broker=SimulatedBroker(), cfg=cfg)
    candidate = {
        "event_id": "bowaka_v2:2024-09-04:AAA:2024-09-04T13:30:00Z",
        "schema_version": 3, "strategy": "bowaka_v2", "event_type": "candidate_signal",
        "symbol": "AAA", "session_date": "2024-09-04",
        "scan_timestamp": "2024-09-04T13:30:00Z",
        "forming_session_bar": {"last_price": 100.0, "session_high": 101.0, "session_low": 99.5},
        "features": {"signal_strength": 5.0},
        "prior_daily_baselines": {"avg_dollar_volume_20d": 5_000_000_000},
    }
    res = consumer.consume(candidate,
                           decision_ts=pd.Timestamp("2024-09-04 13:30:01", tz="UTC"))
    # ``historical_quote=None`` + smoke_fixture -> synthetic_calibrated; the RNG
    # decides ``quote_age_seconds``. Grab the resolved quote out of the decision.
    age = None
    for d in res.decisions:
        q = d.get("quote") or {}
        if q.get("quote_age_seconds") is not None:
            age = q["quote_age_seconds"]
            break
    # If no decision recorded a quote, fall back to the fill record.
    if age is None and res.fills:
        age = res.fills[0].get("quote_age_seconds")
    print(json.dumps({"quote_age_seconds": age}))
    """
)


def test_rng_deterministic_across_processes() -> None:
    """Two subprocess runs produce identical synthetic quote ages."""
    out1 = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        capture_output=True, text=True, timeout=60,
    )
    out2 = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        capture_output=True, text=True, timeout=60,
    )
    assert out1.returncode == 0, f"run1 stderr: {out1.stderr}"
    assert out2.returncode == 0, f"run2 stderr: {out2.stderr}"
    assert out1.stdout.strip() == out2.stdout.strip(), (
        f"Process-to-process determinism broken: run1={out1.stdout!r}, run2={out2.stdout!r}"
    )
