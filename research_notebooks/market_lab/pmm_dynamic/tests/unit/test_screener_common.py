"""Unit tests for screener common utilities — supplements test_public_screeners.py."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from pmm_lab.screener.common import (
    ScreenerConfig,
    band_score,
    compute_candle_metrics,
    compute_trade_metrics,
    ensure_timestamp_seconds,
    hb_to_slash_pair,
    hb_to_underscore_pair,
    normalize_orderbook_side,
    percentile_rank,
    safe_float,
    safe_int,
    should_exclude_symbol,
    split_hb_pair,
    to_hb_pair,
)


class TestSafeFloat:
    def test_none_returns_default(self):
        assert math.isnan(safe_float(None))

    def test_string_number(self):
        assert safe_float("3.14") == pytest.approx(3.14)

    def test_empty_string(self):
        assert math.isnan(safe_float(""))

    def test_nan_string(self):
        assert math.isnan(safe_float("nan"))

    def test_int_value(self):
        assert safe_float(42) == 42.0

    def test_custom_default(self):
        assert safe_float(None, default=0.0) == 0.0


class TestSafeInt:
    def test_none_returns_default(self):
        assert safe_int(None) == 0

    def test_float_string(self):
        assert safe_int("3.7") == 3

    def test_custom_default(self):
        assert safe_int("bad", default=-1) == -1


class TestPairConversions:
    def test_to_hb_pair(self):
        assert to_hb_pair("btc", "usdt") == "BTC-USDT"

    def test_split_hb_pair(self):
        assert split_hb_pair("BTC-USDT") == ("BTC", "USDT")

    def test_split_hb_pair_invalid(self):
        with pytest.raises(ValueError):
            split_hb_pair("BTCUSDT")

    def test_hb_to_slash_pair(self):
        assert hb_to_slash_pair("XMR-USDT") == "XMR/USDT"

    def test_hb_to_underscore_pair(self):
        assert hb_to_underscore_pair("XMR-USDT") == "XMR_USDT"


class TestShouldExcludeSymbol:
    def test_leveraged_token_excluded(self):
        cfg = ScreenerConfig(connector="test")
        # Regex matches tokens ending with UP/DOWN/BULL/BEAR
        assert should_exclude_symbol("BTCUP", "BTCUP/USDT", cfg) is True

    def test_normal_pair_included(self):
        cfg = ScreenerConfig(connector="test")
        assert should_exclude_symbol("BTC", "BTC/USDT", cfg) is False

    def test_include_symbols_override(self):
        cfg = ScreenerConfig(connector="test", include_symbols=("BTC/USDT",))
        assert should_exclude_symbol("ETH", "ETH/USDT", cfg) is True
        assert should_exclude_symbol("BTC", "BTC/USDT", cfg) is False

    def test_exclude_symbols(self):
        cfg = ScreenerConfig(connector="test", exclude_symbols=("DOGE/USDT",))
        assert should_exclude_symbol("DOGE", "DOGE/USDT", cfg) is True


class TestEnsureTimestampSeconds:
    def test_milliseconds_converted(self):
        assert ensure_timestamp_seconds(1712132253536) == pytest.approx(1712132253.536)

    def test_seconds_unchanged(self):
        assert ensure_timestamp_seconds(1712132253) == pytest.approx(1712132253.0)

    def test_none_returns_nan(self):
        assert math.isnan(ensure_timestamp_seconds(None))

    def test_iso_string(self):
        result = ensure_timestamp_seconds("2024-04-03T12:00:00Z")
        assert result > 1e9


class TestNormalizeOrderbookSide:
    def test_dict_items(self):
        side = [{"price": "100.0", "quantity": "2.0"}, {"price": "99.0", "quantity": "5.0"}]
        result = normalize_orderbook_side(side, reverse=True)
        assert len(result) == 2
        assert result[0][0] == 100.0  # highest first when reverse=True

    def test_list_items(self):
        side = [["100.0", "2.0"], ["99.0", "5.0"]]
        result = normalize_orderbook_side(side, reverse=False)
        assert len(result) == 2
        assert result[0][0] == 99.0  # lowest first

    def test_none_returns_empty(self):
        assert normalize_orderbook_side(None) == []


class TestBandScore:
    def test_in_target_range(self):
        assert band_score(50, 10, 20, 80, 100) == 1.0

    def test_below_soft_min(self):
        assert band_score(5, 10, 20, 80, 100) == 0.0

    def test_above_soft_max(self):
        assert band_score(110, 10, 20, 80, 100) == 0.0

    def test_ramp_up(self):
        score = band_score(15, 10, 20, 80, 100)
        assert 0.0 < score < 1.0

    def test_nan_returns_zero(self):
        assert band_score(float("nan"), 10, 20, 80, 100) == 0.0


class TestPercentileRank:
    def test_basic_ranking(self):
        s = pd.Series([10, 20, 30, 40, 50])
        ranks = percentile_rank(s)
        assert ranks.iloc[-1] > ranks.iloc[0]

    def test_reverse(self):
        s = pd.Series([10, 20, 30])
        ranks = percentile_rank(s, reverse=True)
        assert ranks.iloc[0] > ranks.iloc[-1]

    def test_single_value(self):
        s = pd.Series([42.0])
        ranks = percentile_rank(s)
        assert ranks.iloc[0] == 1.0


class TestComputeCandleMetrics:
    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = compute_candle_metrics(df, 300)
        assert result["n_candles"] == 0
        assert math.isnan(result["natr_bps_mean"])

    def test_basic_candles(self):
        n = 100
        ts_start = 1700000000
        df = pd.DataFrame({
            "timestamp": [ts_start + i * 300 for i in range(n)],
            "open": [100.0 + i * 0.1 for i in range(n)],
            "high": [101.0 + i * 0.1 for i in range(n)],
            "low": [99.0 + i * 0.1 for i in range(n)],
            "close": [100.5 + i * 0.1 for i in range(n)],
            "volume": [1000.0] * n,
        })
        result = compute_candle_metrics(df, 300)
        assert result["n_candles"] == n
        assert result["coverage_ratio"] > 0.99
        assert result["zero_volume_fraction"] == 0.0
        assert result["natr_bps_mean"] > 0


class TestComputeTradeMetrics:
    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = compute_trade_metrics(df)
        assert result["recent_trade_count"] == 0

    def test_basic_trades(self):
        n = 50
        now = 1700000000.0
        df = pd.DataFrame({
            "timestamp": [now - (n - i) * 10 for i in range(n)],
            "price": [100.0] * n,
            "quantity": [1.0] * n,
            "side": ["buy"] * 25 + ["sell"] * 25,
        })
        result = compute_trade_metrics(df, now_ts=now)
        assert result["recent_trade_count"] == n
        assert result["buy_trade_fraction"] == pytest.approx(0.5)
        assert result["trades_per_minute"] > 0
