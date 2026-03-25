"""Tests for quant-expert-recommended screener changes."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from pmm_lab.screener.common import (
    ScreenerConfig,
    ScreeningRun,
    build_rejection_reasons,
    compute_orderbook_metrics,
    apply_screening_logic,
    safe_float,
)
from pmm_lab.screener.nonkyc_public import default_nonkyc_config


class TestWiderDepthBands:
    """Verify compute_orderbook_metrics returns 50bps, 100bps, and spread-relative depth."""

    def test_50bps_and_100bps_bands_present(self):
        bids = [["100.0", "10.0"], ["99.0", "5.0"]]
        asks = [["100.2", "8.0"], ["101.0", "3.0"]]
        m = compute_orderbook_metrics(bids, asks)
        assert "sym_depth_quote_50bps" in m
        assert "sym_depth_quote_100bps" in m
        assert not math.isnan(m["sym_depth_quote_50bps"])
        assert not math.isnan(m["sym_depth_quote_100bps"])

    def test_spread_relative_depth_present(self):
        bids = [["100.0", "10.0"], ["99.0", "5.0"]]
        asks = [["100.2", "8.0"], ["101.0", "3.0"]]
        m = compute_orderbook_metrics(bids, asks)
        assert "sym_depth_quote_1xspread" in m
        assert "sym_depth_quote_2xspread" in m

    def test_1xspread_captures_touch_on_wide_spread(self):
        """On a wide-spread book, 1x-spread depth should include at least the touch."""
        bids = [["100.0", "2.0"]]
        asks = [["101.0", "3.0"]]  # ~100 bps spread
        m = compute_orderbook_metrics(bids, asks)
        # 1x spread band = 100 bps from mid -> should capture the touch
        assert m["sym_depth_quote_1xspread"] > 0
        # 10bps band should be empty because half-spread > 10bps
        assert m["sym_depth_quote_10bps"] == 0

    def test_empty_book_has_nan_for_new_bands(self):
        m = compute_orderbook_metrics(None, None)
        assert math.isnan(m["sym_depth_quote_50bps"])
        assert math.isnan(m["sym_depth_quote_1xspread"])
        assert math.isnan(m["sym_depth_quote_2xspread"])


class TestDepthGateSkippable:
    """Verify min_depth_10bps_quote=0 disables the hard gate."""

    def test_depth_10bps_rejected_when_threshold_positive(self):
        cfg = ScreenerConfig(connector="test", min_depth_10bps_quote=100.0)
        row = {"is_active": True, "quote_asset": "USDT", "quote_volume_24h": 999999,
               "spread_bps": 10, "top_of_book_quote": 500, "sym_depth_quote_10bps": 50,
               "last_trade_age_sec": 10, "recent_trade_count": 200, "n_candles": 288,
               "coverage_ratio": 0.99, "zero_volume_fraction": 0.01, "natr_bps_mean": 30}
        reasons = build_rejection_reasons(row, cfg)
        assert any("depth_10bps" in r for r in reasons)

    def test_depth_10bps_not_rejected_when_threshold_zero(self):
        cfg = ScreenerConfig(connector="test", min_depth_10bps_quote=0.0)
        row = {"is_active": True, "quote_asset": "USDT", "quote_volume_24h": 999999,
               "spread_bps": 10, "top_of_book_quote": 500, "sym_depth_quote_10bps": 0,
               "last_trade_age_sec": 10, "recent_trade_count": 200, "n_candles": 288,
               "coverage_ratio": 0.99, "zero_volume_fraction": 0.01, "natr_bps_mean": 30}
        reasons = build_rejection_reasons(row, cfg)
        assert not any("depth_10bps" in r for r in reasons)


class TestNonKYCConfigPatch:
    """Verify default_nonkyc_config reflects the quant expert's thresholds."""

    def test_depth_10bps_disabled(self):
        cfg = default_nonkyc_config()
        assert cfg.min_depth_10bps_quote == 0.0

    def test_spread_widened(self):
        cfg = default_nonkyc_config()
        assert cfg.max_spread_bps == 120.0

    def test_tob_lowered(self):
        cfg = default_nonkyc_config()
        assert cfg.min_top_of_book_quote == 5.0

    def test_volume_lowered(self):
        cfg = default_nonkyc_config()
        assert cfg.min_quote_volume_24h == 50_000.0

    def test_coverage_loosened(self):
        cfg = default_nonkyc_config()
        assert cfg.min_candle_coverage_ratio == 0.90

    def test_fallback_enabled(self):
        cfg = default_nonkyc_config()
        assert cfg.fallback_if_empty is True

    def test_final_top_n_is_15(self):
        cfg = default_nonkyc_config()
        assert cfg.final_top_n == 15


class TestFallbackRankedSelection:
    """Verify fallback_ranked mode when strict yields zero candidates."""

    def _make_run(self, passed_filters: list[bool], fallback_if_empty: bool = True) -> ScreeningRun:
        n = len(passed_filters)
        cfg = ScreenerConfig(
            connector="test", final_top_n=5,
            fallback_if_empty=fallback_if_empty,
            min_depth_10bps_quote=0.0,
        )
        final = pd.DataFrame({
            "trading_pair": [f"TOK{i}-USDT" for i in range(n)],
            "passed_filters": passed_filters,
            "screen_score": list(range(n, 0, -1)),
            "quote_volume_24h": [1000 * i for i in range(n, 0, -1)],
            "rejection_reason": ["" if p else "some_reason" for p in passed_filters],
            "rejection_reasons": [[] if p else ["some_reason"] for p in passed_filters],
        })
        selected = final[final["passed_filters"]].copy()
        selection_mode = "strict"
        if selected.empty and fallback_if_empty:
            selection_mode = "fallback_ranked"
            selected = final.sort_values("screen_score", ascending=False).head(cfg.final_top_n).copy()
        return ScreeningRun(
            connector="test", config=cfg,
            universe=final, shortlist=final, final=final, selected=selected,
            started_at="t0", finished_at="t1",
            selection_mode=selection_mode,
        )

    def test_strict_mode_when_candidates_exist(self):
        run = self._make_run([True, True, False, False, False])
        assert run.selection_mode == "strict"
        assert len(run.selected) == 2

    def test_fallback_ranked_when_none_pass(self):
        run = self._make_run([False, False, False, False, False])
        assert run.selection_mode == "fallback_ranked"
        assert len(run.selected) == 5  # all 5, capped by final_top_n

    def test_fallback_disabled_returns_empty(self):
        run = self._make_run([False, False, False], fallback_if_empty=False)
        assert run.selection_mode == "strict"
        assert len(run.selected) == 0

    def test_metadata_includes_selection_mode(self):
        run = self._make_run([False, False, False])
        m = run.metadata()
        assert m["selection_mode"] == "fallback_ranked"
