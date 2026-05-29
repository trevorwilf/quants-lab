"""Phase 1 (audit 2026-05-29 §A.1) — structured lake-capability probe.

``probe_lake_capability`` replaces the bare ``lake_has_bars`` bool so a caller
can see whether the daily partition for the adjustment the config REQUIRES
exists — not just whether any bars exist.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from bowaka_v2_lab.optuna.autoconfig import lake_has_bars, probe_lake_capability
from tests.fixtures.adjustment_lake import build_lake


def test_probe_reports_missing_required_adjustment(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    # raw daily only; no split_adjusted partition.
    build_lake(
        lake, ["AAAA"],
        daily_start=dt.date(2024, 6, 1), daily_end=dt.date(2024, 9, 1),
        minute_months=[], adjustment="raw",
    )
    cap = probe_lake_capability(lake, "iex", required_adjustment="split_adjusted")
    assert cap.has_bars is True            # raw partition exists
    assert cap.has_required_daily_adjustment is False  # split_adjusted absent
    assert bool(cap) is True               # __bool__ mirrors has_bars
    # back-compat bool helper still works
    assert lake_has_bars(lake, "iex") is True


def test_probe_reports_present_required_adjustment(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    build_lake(
        lake, ["AAAA"],
        daily_start=dt.date(2024, 6, 1), daily_end=dt.date(2024, 9, 1),
        minute_months=[], adjustment="split_adjusted",
    )
    cap = probe_lake_capability(lake, "iex", required_adjustment="split_adjusted")
    assert cap.has_bars is True
    assert cap.has_required_daily_adjustment is True


def test_probe_no_bars_at_all(tmp_path: Path) -> None:
    cap = probe_lake_capability(tmp_path / "empty", "iex",
                                required_adjustment="split_adjusted")
    assert cap.has_bars is False
    assert cap.has_required_daily_adjustment is False
    assert bool(cap) is False
