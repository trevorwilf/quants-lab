"""Realism Phase 4 — ``IntradayWindowPolicy`` forming-session bar window.

``intraday_window_start`` resolves the UTC start of the minute-bar window for a
scan timestamp from the policy:

- ``scanner_start_to_scan`` → 09:45 ET (the live scanner's behaviour)
- ``regular_open_to_scan`` → 09:30 ET (regular open — includes the 09:30-09:44
  opening bars)
- ``extended_hours_to_scan`` → 04:00 ET (premarket)

The lake minute supplier (``make_lake_suppliers``) builds its window from this
start, so a ``regular_open_to_scan`` run sees the opening 15 minutes that a
``scanner_start_to_scan`` run excludes; neither (other than the extended-hours
policy) sees premarket bars.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.data.suppliers import (
    intraday_window_start,
    make_lake_suppliers,
    resolve_intraday_window_policy,
)

# A scan at 11:00 ET (15:00 UTC, EDT) on 2024-09-04.
_SCAN_TS = pd.Timestamp("2024-09-04 15:00:00", tz="UTC")


def test_regular_open_starts_0930_et() -> None:
    start = intraday_window_start(_SCAN_TS, "regular_open_to_scan")
    assert start == pd.Timestamp("2024-09-04 13:30:00", tz="UTC")  # 09:30 ET
    assert start.tz_convert("America/New_York").time() == _dt.time(9, 30)


def test_scanner_start_starts_0945_et() -> None:
    start = intraday_window_start(_SCAN_TS, "scanner_start_to_scan")
    assert start == pd.Timestamp("2024-09-04 13:45:00", tz="UTC")  # 09:45 ET
    assert start.tz_convert("America/New_York").time() == _dt.time(9, 45)


def test_extended_hours_starts_0400_et_premarket() -> None:
    start = intraday_window_start(_SCAN_TS, "extended_hours_to_scan")
    assert start == pd.Timestamp("2024-09-04 08:00:00", tz="UTC")  # 04:00 ET
    assert start.tz_convert("America/New_York").time() == _dt.time(4, 0)


def test_regular_open_includes_opening_bars_scanner_start_excludes() -> None:
    # regular_open_to_scan must include the 09:30-09:44 opening bars; the
    # scanner_start_to_scan window must start at/after 09:45 and exclude them.
    ro = intraday_window_start(_SCAN_TS, "regular_open_to_scan")
    ss = intraday_window_start(_SCAN_TS, "scanner_start_to_scan")
    opening_bar_0935 = pd.Timestamp("2024-09-04 13:35:00", tz="UTC")  # 09:35 ET
    assert ro <= opening_bar_0935  # regular_open window covers a 09:35 bar
    assert ss > opening_bar_0935   # scanner_start window starts after it


def test_non_extended_policies_exclude_premarket() -> None:
    premarket_bar = pd.Timestamp("2024-09-04 12:00:00", tz="UTC")  # 08:00 ET premarket
    for policy in ("regular_open_to_scan", "scanner_start_to_scan"):
        start = intraday_window_start(_SCAN_TS, policy)
        assert start > premarket_bar, f"{policy} must exclude premarket bars"
    # extended_hours, by contrast, reaches back into premarket.
    assert intraday_window_start(_SCAN_TS, "extended_hours_to_scan") < premarket_bar


def test_window_start_uses_et_session_date_not_utc_date() -> None:
    # A scan late in the UTC day still resolves to that day's ET session — the
    # window must not roll into the previous calendar day's premarket.
    late_scan = pd.Timestamp("2024-09-04 19:30:00", tz="UTC")  # 15:30 ET
    start = intraday_window_start(late_scan, "regular_open_to_scan")
    assert start.tz_convert("America/New_York").date() == _dt.date(2024, 9, 4)


def test_resolve_policy_from_simulation_mode() -> None:
    # current_code_parity resolves to scanner_start; intended_realism to
    # regular_open (SimulationConfig fills these from mode).
    from bowaka_v2_lab.config.models import SimulationConfig

    parity = SimulationConfig.model_validate({"mode": "current_code_parity"})
    realism = SimulationConfig.model_validate({"mode": "intended_realism"})
    assert resolve_intraday_window_policy({"simulation": parity.model_dump()}) == (
        "scanner_start_to_scan"
    )
    assert resolve_intraday_window_policy({"simulation": realism.model_dump()}) == (
        "regular_open_to_scan"
    )


def test_lake_supplier_window_honours_policy(tmp_path) -> None:
    # The lake minute supplier's window start must reflect intraday_window_policy.
    # Build a tiny lake with bars from 09:30 ET so a regular_open window catches
    # the 09:30-09:44 bars a scanner_start window drops.
    from bowaka_common.marketdata import layout as _layout

    open_et = pd.Timestamp("2024-09-04 09:30:00", tz="America/New_York")
    rows = []
    for i in range(120):  # 09:30 -> 11:29 ET
        ts = (open_et + pd.Timedelta(minutes=i)).tz_convert("UTC")
        rows.append({"symbol": "AAA", "timestamp": ts, "open": 100.0,
                     "high": 100.5, "low": 99.5, "close": 100.2, "volume": 1000.0})
    df = pd.DataFrame(rows)
    part = _layout.minute_bars_path(tmp_path, "AAA", 2024, 9)
    part.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(part, index=False)

    scan_ts = pd.Timestamp("2024-09-04 15:00:00", tz="UTC")  # 11:00 ET

    ro_supplier, _ = make_lake_suppliers(
        tmp_path, feed="iex", intraday_window_policy="regular_open_to_scan"
    )
    ss_supplier, _ = make_lake_suppliers(
        tmp_path, feed="iex", intraday_window_policy="scanner_start_to_scan"
    )
    ro_bars = ro_supplier("AAA", scan_ts)
    ss_bars = ss_supplier("AAA", scan_ts)
    # regular_open includes 15 more bars (09:30-09:44) than scanner_start.
    assert len(ro_bars) - len(ss_bars) == 15
    ro_first_et = pd.Timestamp(ro_bars["timestamp"].min()).tz_convert("America/New_York")
    ss_first_et = pd.Timestamp(ss_bars["timestamp"].min()).tz_convert("America/New_York")
    assert ro_first_et.time() == _dt.time(9, 30)
    assert ss_first_et.time() == _dt.time(9, 45)
