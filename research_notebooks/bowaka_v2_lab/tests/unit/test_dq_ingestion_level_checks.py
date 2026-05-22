"""Realism remediation 2 Phase 3 — ingestion-level DQ checks (audit §P0-010).

Synthesise a parquet with a deliberate OHLC violation; the ingestion-level
checks must flag it as ``ingestion_ohlc_violation: fail``, leaving every other
ingestion check ``pass``.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.data.dq_levels import build_ingestion_checks


def _bar(o: float, h: float, l: float, c: float, v: float = 1000.0) -> dict:
    return {
        "timestamp": pd.Timestamp("2024-09-04 14:30:00", tz="UTC"),
        "open": o, "high": h, "low": l, "close": c, "volume": v,
    }


def _frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(
        ["2024-09-04 14:30:00", "2024-09-04 14:31:00", "2024-09-04 14:32:00",
         "2024-09-04 14:33:00", "2024-09-04 14:34:00"][: len(rows)], utc=True
    )
    return df


def test_ingestion_ohlc_violation_flagged() -> None:
    # 3 clean bars + 1 with high < low (impossible) + 1 with high < close.
    bad = _frame([
        _bar(10.0, 10.2, 9.9, 10.1),
        _bar(10.1, 10.3, 10.0, 10.2),
        _bar(10.2, 10.4, 10.1, 10.3),
        _bar(10.3, 9.5, 10.2, 10.4),   # high < low/open/close — clear violation
        _bar(10.4, 10.5, 10.3, 10.8),  # close > high — violation
    ])
    checks = build_ingestion_checks(bar_frames={"AAA": bad})
    by_name = {c["name"]: c for c in checks}
    assert by_name["ingestion_ohlc_violation"]["status"] == "fail"
    assert by_name["ingestion_ohlc_violation"]["count"] >= 2
    assert "AAA" in by_name["ingestion_ohlc_violation"]["evidence"]["offending_symbols"]
    # Other ingestion checks remain clean on the same frame.
    for name in (
        "ingestion_schema",
        "ingestion_timestamps_sorted",
        "ingestion_duplicate_timestamps",
        "ingestion_nonpositive_price",
    ):
        assert by_name[name]["status"] == "pass", name


def test_ingestion_clean_frame_all_pass() -> None:
    good = _frame([
        _bar(10.0, 10.2, 9.9, 10.1),
        _bar(10.1, 10.3, 10.0, 10.2),
        _bar(10.2, 10.4, 10.1, 10.3),
    ])
    checks = build_ingestion_checks(bar_frames={"AAA": good})
    by_name = {c["name"]: c for c in checks}
    for name in (
        "ingestion_schema",
        "ingestion_timestamps_sorted",
        "ingestion_duplicate_timestamps",
        "ingestion_ohlc_violation",
        "ingestion_nonpositive_price",
    ):
        assert by_name[name]["status"] == "pass", name


def test_ingestion_duplicate_timestamps_fail() -> None:
    df = _frame([
        _bar(10.0, 10.2, 9.9, 10.1),
        _bar(10.1, 10.3, 10.0, 10.2),
    ])
    df["timestamp"] = pd.to_datetime(["2024-09-04 14:30:00"] * 2, utc=True)
    checks = build_ingestion_checks(bar_frames={"AAA": df})
    by_name = {c["name"]: c for c in checks}
    assert by_name["ingestion_duplicate_timestamps"]["status"] == "fail"


def test_ingestion_nonpositive_price_fail() -> None:
    df = _frame([
        _bar(10.0, 10.2, 9.9, 10.1),
        _bar(0.0, 0.0, 0.0, 0.0),  # zero prices
    ])
    checks = build_ingestion_checks(bar_frames={"AAA": df})
    by_name = {c["name"]: c for c in checks}
    assert by_name["ingestion_nonpositive_price"]["status"] == "fail"
