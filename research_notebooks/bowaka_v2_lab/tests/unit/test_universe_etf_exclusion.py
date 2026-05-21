"""Phase 3 — ETF / pattern-class instrument exclusion.

The lake asset master has no instrument-class field, so the builder classifies
ETF / leveraged-ETP / inverse-ETP / ETN / warrant / unit / right / preferred via
a name + symbol-suffix heuristic. Heuristically-recognised excluded-class
symbols must be dropped with ``excluded_instrument_class``; operating equities
must pass. Symbol-suffix-only matches are ``heuristic`` (unknown) and honour the
Phase-0 ``unknown_instrument_class_policy``.

The symbols here are chosen so the heuristic actually classifies them — see
``universe.builder.classify_instrument``.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.universe.builder import build_pit_universe, classify_instrument
from tests.fixtures.universe_fixture import (
    FakeLakeStore,
    asset_master_frame,
    daily_bars_frame,
    realism_cfg,
)

_SESSION = _dt.date(2024, 9, 4)

# (symbol, name, expected_class) — names the heuristic positively classifies.
_EXCLUDED_INSTRUMENTS = [
    ("SPY", "SPDR S&P 500 ETF Trust", "etf"),
    ("QQQ", "Invesco QQQ Trust", "etf"),
    ("TQQQ", "ProShares UltraPro QQQ", "leveraged_etp"),
    ("SOXL", "Direxion Daily Semiconductor Bull 3X Shares", "leveraged_etp"),
    ("SQQQ", "ProShares UltraShort QQQ", "inverse_etp"),
    ("AACBW", "Artius II Acquisition Inc. Warrants", "warrant"),
    ("AACBU", "Artius II Acquisition Inc. Units", "unit"),
    ("AACBR", "Artius II Acquisition Inc. Rights", "right"),
    ("BMLpL", "Bank of America Corp Depositary Shares Preferred", "preferred"),
]

# Operating equities — must classify as operating_equity and pass.
_OPERATING_EQUITIES = [
    ("AAPL", "Apple Inc."),
    ("MSFT", "Microsoft Corporation"),
    ("MUR", "Murphy Oil Corp."),
    ("F", "Ford Motor Company"),
    ("BAC", "Bank of America Corporation"),
]


def test_heuristic_classifies_excluded_instruments() -> None:
    """Each excluded-instrument fixture classifies to its expected class."""
    for symbol, name, expected in _EXCLUDED_INSTRUMENTS:
        cls, _basis = classify_instrument(symbol, name)
        assert cls == expected, f"{symbol} ({name}) -> {cls}, expected {expected}"


def test_heuristic_classifies_operating_equities() -> None:
    for symbol, name in _OPERATING_EQUITIES:
        cls, _basis = classify_instrument(symbol, name)
        assert cls == "operating_equity", f"{symbol} ({name}) -> {cls}"


def test_etf_and_pattern_class_excluded_from_universe() -> None:
    rows = [{"symbol": s, "name": n} for s, n, _c in _EXCLUDED_INSTRUMENTS]
    rows += [{"symbol": s, "name": n} for s, n in _OPERATING_EQUITIES]
    am = asset_master_frame(rows)
    all_syms = [r["symbol"] for r in rows]
    daily = {s: daily_bars_frame(s, end_before=_SESSION) for s in all_syms}
    records = build_pit_universe(_SESSION, realism_cfg(), FakeLakeStore(am, daily))

    for symbol, _name, _cls in _EXCLUDED_INSTRUMENTS:
        rec = records[symbol]
        assert "excluded_instrument_class" in rec.rejection_reasons, symbol
        assert not rec.eligible_for_bowaka_equity_bucket, symbol

    for symbol, _name in _OPERATING_EQUITIES:
        rec = records[symbol]
        assert rec.instrument_class == "operating_equity", symbol
        assert rec.eligible_for_bowaka_equity_bucket, symbol
        assert rec.rejection_reasons == [], symbol


def test_symbol_suffix_only_is_heuristic_unknown_and_policy_driven() -> None:
    """A >=5-char symbol ending W/U/R whose name does NOT read as a fund and has
    no warrant/unit/right keyword is ``heuristic`` (unknown) — kept under
    ``fail_open`` (parity/smoke), dropped under ``fail_closed`` (realism)."""
    # Ambiguous: 5-char ticker ending 'W', name has no class keyword.
    symbol, name = "ABCDW", "Generic Issuer SA"
    cls, basis = classify_instrument(symbol, name)
    assert cls == "heuristic"
    assert basis == "symbol_suffix"

    am = asset_master_frame([{"symbol": symbol, "name": name}])
    daily = {symbol: daily_bars_frame(symbol, end_before=_SESSION)}

    # fail_closed (intended_realism) — excluded with unknown_instrument_class.
    rec_closed = build_pit_universe(_SESSION, realism_cfg(), FakeLakeStore(am, daily))[symbol]
    assert "unknown_instrument_class" in rec_closed.rejection_reasons
    assert not rec_closed.eligible_for_bowaka_equity_bucket

    # fail_open (current_code_parity) — kept; instrument_class stays "heuristic".
    cfg_open = realism_cfg()
    cfg_open["simulation"]["mode"] = "current_code_parity"
    rec_open = build_pit_universe(_SESSION, cfg_open, FakeLakeStore(am, daily))[symbol]
    assert "unknown_instrument_class" not in rec_open.rejection_reasons
    assert rec_open.instrument_class == "heuristic"
    assert rec_open.eligible_for_bowaka_equity_bucket
