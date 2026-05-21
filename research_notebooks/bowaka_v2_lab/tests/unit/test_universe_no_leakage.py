"""Phase 3 — no current-day data leakage in the universe filters.

The PIT builder must compute ``prior_close`` and ``prior_avg_dollar_volume_20d``
from daily bars dated *strictly before* the session date. Flipping the
session-day bar's price or volume — to values that would, if read, change the
price-band / ADV verdict — must not change which symbols are eligible.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.universe.builder import build_pit_universe, eligible_symbols, universe_hash
from tests.fixtures.universe_fixture import FakeLakeStore, asset_master_frame, realism_cfg

_SESSION = _dt.date(2024, 9, 4)


def _daily_with_session_bar(
    symbol: str,
    *,
    prior_close: float,
    prior_volume: float,
    session_close: float,
    session_volume: float,
) -> pd.DataFrame:
    """30 prior sessions + the SESSION's own bar.

    The session bar carries ``session_close`` / ``session_volume`` — a builder
    that (incorrectly) read it would compute a different ``prior_close`` / ADV.
    """
    prior_days = [
        d.date() for d in pd.bdate_range(end=_SESSION - _dt.timedelta(days=1), periods=30)
    ]
    rows = [
        {
            "symbol": symbol,
            "session_date": d,
            "open": prior_close,
            "high": prior_close * 1.01,
            "low": prior_close * 0.99,
            "close": prior_close,
            "volume": float(prior_volume),
        }
        for d in prior_days
    ]
    rows.append(
        {
            "symbol": symbol,
            "session_date": _SESSION,  # the session's OWN bar
            "open": session_close,
            "high": session_close * 1.01,
            "low": session_close * 0.99,
            "close": session_close,
            "volume": float(session_volume),
        }
    )
    return pd.DataFrame(rows)


def test_flipping_session_day_price_does_not_change_inclusion() -> None:
    am = asset_master_frame([{"symbol": "AAA"}])
    # Prior close $10 (in band) — AAA is eligible. The session-day close is set
    # to $0.50 (would fail price_below_min) and then to $25 (would fail
    # price_above_max). Neither must affect AAA's eligibility or prior_close.
    for session_close in (0.50, 25.0):
        daily = {
            "AAA": _daily_with_session_bar(
                "AAA",
                prior_close=10.0,
                prior_volume=500_000,
                session_close=session_close,
                session_volume=500_000,
            )
        }
        records = build_pit_universe(_SESSION, realism_cfg(), FakeLakeStore(am, daily))
        rec = records["AAA"]
        assert rec.prior_close == 10.0, session_close
        assert rec.eligible_for_bowaka_equity_bucket, session_close
        assert rec.rejection_reasons == [], session_close


def test_flipping_session_day_volume_does_not_change_inclusion() -> None:
    am = asset_master_frame([{"symbol": "BBB"}])
    # Prior 20d ADV = $10 * 500k = $5M (over the $250k min) — BBB eligible.
    # Drive the session-day volume to ~0 (would crater the ADV if leaked) and
    # then to a huge value; neither must change BBB's eligibility.
    for session_volume in (1.0, 50_000_000.0):
        daily = {
            "BBB": _daily_with_session_bar(
                "BBB",
                prior_close=10.0,
                prior_volume=500_000,
                session_close=10.0,
                session_volume=session_volume,
            )
        }
        records = build_pit_universe(_SESSION, realism_cfg(), FakeLakeStore(am, daily))
        rec = records["BBB"]
        # ADV must be exactly the prior-window value, untouched by the session bar.
        assert rec.prior_avg_dollar_volume_20d == 10.0 * 500_000, session_volume
        assert rec.eligible_for_bowaka_equity_bucket, session_volume


def test_universe_hash_is_stable_under_session_day_mutation() -> None:
    """The eligible set + its hash are identical regardless of the session bar."""
    am = asset_master_frame([{"symbol": s} for s in ("AAA", "BBB", "CCC")])

    def _build(session_close: float, session_volume: float) -> tuple[list[str], str]:
        daily = {
            s: _daily_with_session_bar(
                s,
                prior_close=10.0,
                prior_volume=500_000,
                session_close=session_close,
                session_volume=session_volume,
            )
            for s in ("AAA", "BBB", "CCC")
        }
        records = build_pit_universe(_SESSION, realism_cfg(), FakeLakeStore(am, daily))
        return eligible_symbols(records), universe_hash(records)

    baseline_syms, baseline_hash = _build(10.0, 500_000)
    # Session bar pushed far out of band / volume — must not move the universe.
    mutated_syms, mutated_hash = _build(0.01, 1.0)
    assert mutated_syms == baseline_syms == ["AAA", "BBB", "CCC"]
    assert mutated_hash == baseline_hash
