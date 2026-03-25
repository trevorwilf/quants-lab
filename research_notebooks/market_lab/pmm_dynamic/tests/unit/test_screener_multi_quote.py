"""Tests for multi-quote-asset screening support."""

from __future__ import annotations

import pandas as pd
import pytest

from pmm_lab.screener.common import (
    ScreenerConfig,
    build_rejection_reasons,
    select_shortlist,
    compute_coarse_scores,
)
from pmm_lab.screener.nonkyc_public import NonKYCPublicScreener, default_nonkyc_config
from pmm_lab.screener.mexc_public import default_mexc_config


class TestMatchesQuoteAsset:
    """Test the ScreenerConfig.matches_quote_asset() helper."""

    def test_single_asset_match(self):
        cfg = ScreenerConfig(connector="test", quote_asset="USDT")
        assert cfg.matches_quote_asset("USDT") is True
        assert cfg.matches_quote_asset("usdt") is True
        assert cfg.matches_quote_asset("BTC") is False

    def test_wildcard_matches_everything(self):
        cfg = ScreenerConfig(connector="test", quote_asset="*")
        assert cfg.matches_quote_asset("USDT") is True
        assert cfg.matches_quote_asset("XMR") is True
        assert cfg.matches_quote_asset("BTC") is True
        assert cfg.matches_quote_asset("DOGE") is True

    def test_comma_separated_list(self):
        cfg = ScreenerConfig(connector="test", quote_asset="USDT,XMR,BTC")
        assert cfg.matches_quote_asset("USDT") is True
        assert cfg.matches_quote_asset("XMR") is True
        assert cfg.matches_quote_asset("BTC") is True
        assert cfg.matches_quote_asset("USDC") is False

    def test_comma_separated_with_spaces(self):
        cfg = ScreenerConfig(connector="test", quote_asset=" USDT , XMR , BTC ")
        assert cfg.matches_quote_asset("USDT") is True
        assert cfg.matches_quote_asset("XMR") is True

    def test_case_insensitive(self):
        cfg = ScreenerConfig(connector="test", quote_asset="usdt,xmr")
        assert cfg.matches_quote_asset("USDT") is True
        assert cfg.matches_quote_asset("Xmr") is True


class TestNonKYCMultiQuoteUniverse:
    """Verify NonKYC screener returns pairs across multiple quote assets."""

    MARKET_LIST = [
        {
            "symbol": "XMR/USDT",
            "isActive": True,
            "lastPrice": "150.5",
            "volume": "325.0",
            "lastTradeAt": 1712132253536,
            "priceDecimals": 2,
            "quantityDecimals": 3,
        },
        {
            "symbol": "DOGE/BTC",
            "isActive": True,
            "lastPrice": "0.000001",
            "volume": "1000",
            "lastTradeAt": 1712132253536,
            "priceDecimals": 8,
            "quantityDecimals": 0,
        },
        {
            "symbol": "BTC/XMR",
            "isActive": True,
            "lastPrice": "500.0",
            "volume": "10.0",
            "lastTradeAt": 1712132253536,
            "priceDecimals": 4,
            "quantityDecimals": 6,
        },
        {
            "symbol": "ETH/USDC",
            "isActive": True,
            "lastPrice": "2100.0",
            "volume": "50.0",
            "lastTradeAt": 1712132253536,
            "priceDecimals": 2,
            "quantityDecimals": 4,
        },
    ]

    TICKERS = [
        {
            "ticker_id": "XMR_USDT",
            "type": "market",
            "last_price": "150.5",
            "base_volume": "325.0",
            "target_volume": "48912.5",
            "bid": "150.4",
            "ask": "150.6",
        },
    ]

    def test_wildcard_returns_all_quotes(self):
        cfg = default_nonkyc_config()
        assert cfg.quote_asset == "*"
        df = NonKYCPublicScreener._build_universe_frame(
            self.MARKET_LIST, self.TICKERS, cfg
        )
        quote_assets = set(df["quote_asset"].str.upper())
        assert "USDT" in quote_assets
        assert "BTC" in quote_assets
        assert "XMR" in quote_assets
        assert "USDC" in quote_assets
        assert len(df) == 4

    def test_single_quote_filters_correctly(self):
        cfg = default_nonkyc_config()
        cfg.quote_asset = "USDT"
        df = NonKYCPublicScreener._build_universe_frame(
            self.MARKET_LIST, self.TICKERS, cfg
        )
        assert len(df) == 1
        assert df.iloc[0]["quote_asset"] == "USDT"

    def test_multi_quote_list(self):
        cfg = default_nonkyc_config()
        cfg.quote_asset = "USDT,BTC"
        df = NonKYCPublicScreener._build_universe_frame(
            self.MARKET_LIST, self.TICKERS, cfg
        )
        assert len(df) == 2
        quote_assets = set(df["quote_asset"].str.upper())
        assert quote_assets == {"USDT", "BTC"}


class TestRejectionReasonMultiQuote:
    """Verify rejection reasons handle multi-quote configs."""

    def test_wildcard_no_quote_mismatch(self):
        cfg = ScreenerConfig(connector="test", quote_asset="*",
                             min_depth_10bps_quote=0.0)
        row = {
            "is_active": True, "quote_asset": "XMR",
            "quote_volume_24h": 999999, "spread_bps": 10,
            "top_of_book_quote": 500, "sym_depth_quote_10bps": 0,
            "last_trade_age_sec": 10, "recent_trade_count": 200,
            "n_candles": 288, "coverage_ratio": 0.99,
            "zero_volume_fraction": 0.01, "natr_bps_mean": 30,
        }
        reasons = build_rejection_reasons(row, cfg)
        assert "quote_asset_mismatch" not in reasons

    def test_single_quote_rejects_mismatch(self):
        cfg = ScreenerConfig(connector="test", quote_asset="USDT",
                             min_depth_10bps_quote=0.0)
        row = {
            "is_active": True, "quote_asset": "XMR",
            "quote_volume_24h": 999999, "spread_bps": 10,
            "top_of_book_quote": 500, "sym_depth_quote_10bps": 0,
            "last_trade_age_sec": 10, "recent_trade_count": 200,
            "n_candles": 288, "coverage_ratio": 0.99,
            "zero_volume_fraction": 0.01, "natr_bps_mean": 30,
        }
        reasons = build_rejection_reasons(row, cfg)
        assert "quote_asset_mismatch" in reasons


class TestSelectShortlistMultiQuote:
    """Verify shortlist respects multi-quote filtering."""

    def test_wildcard_keeps_all_quotes(self):
        cfg = ScreenerConfig(connector="test", quote_asset="*",
                             universe_top_k=100)
        df = pd.DataFrame({
            "trading_pair": ["BTC-USDT", "DOGE-BTC", "ETH-XMR"],
            "quote_asset": ["USDT", "BTC", "XMR"],
            "is_active": [True, True, True],
            "quote_volume_24h": [100000, 50000, 30000],
            "spread_bps": [10, 20, 30],
            "top_of_book_quote": [500, 100, 50],
        })
        df = compute_coarse_scores(df)
        result = select_shortlist(df, cfg)
        assert len(result) == 3

    def test_single_quote_filters_shortlist(self):
        cfg = ScreenerConfig(connector="test", quote_asset="USDT",
                             universe_top_k=100)
        df = pd.DataFrame({
            "trading_pair": ["BTC-USDT", "DOGE-BTC", "ETH-XMR"],
            "quote_asset": ["USDT", "BTC", "XMR"],
            "is_active": [True, True, True],
            "quote_volume_24h": [100000, 50000, 30000],
            "spread_bps": [10, 20, 30],
            "top_of_book_quote": [500, 100, 50],
        })
        df = compute_coarse_scores(df)
        result = select_shortlist(df, cfg)
        assert len(result) == 1
        assert result.iloc[0]["quote_asset"] == "USDT"


class TestMEXCDefaultUnchanged:
    """Verify MEXC default config is still USDT-only."""

    def test_mexc_default_is_usdt(self):
        cfg = default_mexc_config()
        assert cfg.quote_asset == "USDT"
        assert cfg.matches_quote_asset("USDT") is True
        assert cfg.matches_quote_asset("BTC") is False
