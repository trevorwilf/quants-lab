"""Phase 1 (audit 2026-05-29 §5.3 / §13.1) — daily-adjustment resolver."""
from __future__ import annotations

from bowaka_v2_lab.data.adjustment import daily_adjustment_for_config


def test_require_split_adjustment_maps_to_split_adjusted() -> None:
    assert daily_adjustment_for_config(
        {"market_data": {"require_split_adjustment": True}}
    ) == "split_adjusted"


def test_require_adjusted_daily_bars_maps_to_split_adjusted() -> None:
    assert daily_adjustment_for_config(
        {"market_data": {"require_adjusted_daily_bars": True}}
    ) == "split_adjusted"


def test_explicit_daily_adjustment_passed_through() -> None:
    assert daily_adjustment_for_config(
        {"market_data": {"daily_adjustment": "split_adjusted"}}
    ) == "split_adjusted"


def test_empty_config_defaults_to_raw() -> None:
    assert daily_adjustment_for_config({}) == "raw"
    assert daily_adjustment_for_config({"market_data": {}}) == "raw"


def test_explicit_raw_with_flags_false() -> None:
    assert daily_adjustment_for_config(
        {"market_data": {"require_split_adjustment": False, "daily_adjustment": "raw"}}
    ) == "raw"
