"""Phase 1 (audit 2026-05-29 §9 Phase 7) — synthetic-SIP fixture lake shape.

Validates the committed fixture's directory layout, parquet column schemas, and
manifest so a broken fixture is caught fast (unit). The fixture is materialised
by ``tests/fixtures/build_sip_synthetic_lake.py``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout

_FIX = Path(__file__).resolve().parents[2] / "fixtures" / "sip_synthetic_lake"
_SYMBOLS = ("AAAA", "BBBB", "CCCC", "DDDD", "EEEE")


def test_fixture_lake_exists() -> None:
    assert _FIX.is_dir(), (
        "synthetic SIP fixture missing — run "
        "`py -3.12 tests/fixtures/build_sip_synthetic_lake.py`"
    )


def test_daily_bars_present_with_expected_columns() -> None:
    for sym in _SYMBOLS:
        p = layout.daily_bars_path(_FIX, sym, feed="sip", adjustment="split_adjusted")
        assert p.is_file(), p
    df = pd.read_parquet(layout.daily_bars_path(
        _FIX, "AAAA", feed="sip", adjustment="split_adjusted"))
    for col in ("symbol", "timestamp", "open", "high", "low", "close", "volume"):
        assert col in df.columns, col
    assert len(df) >= 60


def test_minute_and_quotes_present() -> None:
    mp = layout.minute_bars_path(_FIX, "AAAA", 2025, 8, feed="sip", adjustment="raw")
    assert mp.is_file(), mp
    qp = layout.quotes_path(_FIX, "AAAA", 2025, 8, feed="sip")
    assert qp.is_file(), qp
    q = pd.read_parquet(qp)
    for col in ("timestamp", "bid", "ask", "bid_size", "ask_size"):
        assert col in q.columns, col


def test_halt_status_and_manifest() -> None:
    sp = layout.statuses_path(_FIX, "AAAA", "2025-08-26")
    assert sp.is_file(), sp
    status = pd.read_parquet(sp)
    assert (status["reason"] == "LULD").any()

    manifest = json.loads(layout.ingestion_manifest_path(_FIX).read_text(encoding="utf-8"))
    assert manifest["feed"] == "sip"
    assert manifest["adjustment"] == "split_adjusted"
