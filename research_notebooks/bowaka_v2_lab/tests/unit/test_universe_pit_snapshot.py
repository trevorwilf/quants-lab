"""PIT universe snapshot excludes ETFs / warrants / etc per [Report §7.4]."""
from __future__ import annotations

import datetime as _dt

import pandas as pd

from bowaka_v2_lab.scanner.universe_builder import build_universe_snapshot


def test_excludes_non_equity_classes() -> None:
    asset_master = pd.DataFrame([
        {"symbol": "AAPL", "exchange": "NASDAQ", "venue_code": "XNAS",
         "instrument_class": "operating_equity",
         "eligible_for_bowaka_equity_bucket": True},
        {"symbol": "SPY", "exchange": "NYSE", "venue_code": "XNYS",
         "instrument_class": "etf",
         "eligible_for_bowaka_equity_bucket": False},
        {"symbol": "WAR", "exchange": "NYSE", "venue_code": "XNYS",
         "instrument_class": "warrant",
         "eligible_for_bowaka_equity_bucket": False},
        {"symbol": "SPAC", "exchange": "NYSE", "venue_code": "XNYS",
         "instrument_class": "spac",
         "eligible_for_bowaka_equity_bucket": False},
    ])
    daily_baselines = pd.DataFrame([
        {"symbol": "AAPL", "prior_close": 150.0, "avg_dollar_volume_20d": 5e9},
        {"symbol": "SPY", "prior_close": 500.0, "avg_dollar_volume_20d": 30e9},
        {"symbol": "WAR", "prior_close": 5.0, "avg_dollar_volume_20d": 1e6},
        {"symbol": "SPAC", "prior_close": 10.0, "avg_dollar_volume_20d": 2e6},
    ])
    snap = build_universe_snapshot(
        asset_master=asset_master, daily_baselines=daily_baselines,
        cfg={"universe": {"asset_classes": ["operating_equity"],
                            "min_price": 1.0, "max_price": 1000.0,
                            "min_adv_dollars": 1_000_000,
                            "exclude_pattern_class": True}},
        session_date=_dt.date(2024, 9, 4),
    )
    syms = {s["symbol"] for s in snap["symbols"]}
    assert syms == {"AAPL"}


def test_universe_hash_stable() -> None:
    asset_master = pd.DataFrame([
        {"symbol": "AAA", "exchange": "NASDAQ", "venue_code": "XNAS",
         "instrument_class": "operating_equity",
         "eligible_for_bowaka_equity_bucket": True},
    ])
    daily_baselines = pd.DataFrame([
        {"symbol": "AAA", "prior_close": 100.0, "avg_dollar_volume_20d": 5_000_000},
    ])
    s1 = build_universe_snapshot(
        asset_master=asset_master, daily_baselines=daily_baselines, cfg={"universe": {}},
        session_date=_dt.date(2024, 9, 4),
    )
    s2 = build_universe_snapshot(
        asset_master=asset_master, daily_baselines=daily_baselines, cfg={"universe": {}},
        session_date=_dt.date(2024, 9, 4),
    )
    assert s1["universe_hash"] == s2["universe_hash"]


def test_price_filter_applied() -> None:
    asset_master = pd.DataFrame([
        {"symbol": "PENNY", "exchange": "OTC", "venue_code": "XOTC",
         "instrument_class": "operating_equity",
         "eligible_for_bowaka_equity_bucket": True},
        {"symbol": "GOOG", "exchange": "NASDAQ", "venue_code": "XNAS",
         "instrument_class": "operating_equity",
         "eligible_for_bowaka_equity_bucket": True},
    ])
    daily_baselines = pd.DataFrame([
        {"symbol": "PENNY", "prior_close": 0.50, "avg_dollar_volume_20d": 5_000_000},
        {"symbol": "GOOG", "prior_close": 150.0, "avg_dollar_volume_20d": 5_000_000_000},
    ])
    snap = build_universe_snapshot(
        asset_master=asset_master, daily_baselines=daily_baselines,
        cfg={"universe": {"min_price": 1.0, "max_price": 1000.0,
                            "min_adv_dollars": 1_000_000,
                            "asset_classes": ["operating_equity"],
                            "exclude_pattern_class": True}},
        session_date=_dt.date(2024, 9, 4),
    )
    syms = {s["symbol"] for s in snap["symbols"]}
    assert syms == {"GOOG"}
