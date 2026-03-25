"""Unit tests for public screener helpers and payload normalization."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pmm_lab.screener.artifacts import build_candle_ingestor_manifest
from pmm_lab.screener.common import (
    ScreeningRun,
    compute_orderbook_metrics,
)
from pmm_lab.screener.mexc_public import MEXCPublicScreener, default_mexc_config
from pmm_lab.screener.nonkyc_public import NonKYCPublicScreener, default_nonkyc_config



def test_compute_orderbook_metrics_symmetric_depth_and_spread():
    bids = [["100.0", "2.0"], ["99.95", "1.0"], ["99.0", "50"]]
    asks = [["100.1", "3.0"], ["100.15", "1.0"], ["101.0", "50"]]

    metrics = compute_orderbook_metrics(bids, asks)

    assert round(metrics["mid_price"], 4) == 100.05
    assert round(metrics["spread_bps"], 4) == round((0.1 / 100.05) * 10_000.0, 4)
    assert metrics["top_of_book_quote"] == min(100.0 * 2.0, 100.1 * 3.0)
    assert metrics["sym_depth_quote_10bps"] == min(100.0 * 2.0 + 99.95 * 1.0, 100.1 * 3.0 + 100.15 * 1.0)



def test_mexc_universe_normalization_from_public_payloads():
    cfg = default_mexc_config()
    exchange_info = {
        "symbols": [
            {
                "symbol": "ALGOUSDT",
                "status": "1",
                "baseAsset": "ALGO",
                "quoteAsset": "USDT",
                "quotePrecision": 4,
                "baseAssetPrecision": 2,
                "baseSizePrecision": "0.1",
                "quoteAmountPrecision": "5",
                "permissions": ["SPOT"],
                "st": False,
                "makerCommission": "0.0002",
                "takerCommission": "0.0002",
            },
            {
                "symbol": "BTCBTC",
                "status": "1",
                "baseAsset": "BTC",
                "quoteAsset": "BTC",
                "quotePrecision": 8,
                "baseAssetPrecision": 8,
                "baseSizePrecision": "0.000001",
                "quoteAmountPrecision": "0.0001",
                "permissions": ["SPOT"],
                "st": False,
            },
        ]
    }
    tickers = [
        {
            "symbol": "ALGOUSDT",
            "lastPrice": "0.215",
            "volume": "100000",
            "quoteVolume": "21500",
            "bidPrice": "0.2149",
            "askPrice": "0.2151",
        }
    ]
    books = [{"symbol": "ALGOUSDT", "bidPrice": "0.2149", "bidQty": "4000", "askPrice": "0.2151", "askQty": "5000"}]

    df = MEXCPublicScreener._build_universe_frame(exchange_info, tickers, books, cfg)

    assert len(df) == 1
    row = df.iloc[0]
    assert row["trading_pair"] == "ALGO-USDT"
    assert row["exchange_symbol"] == "ALGOUSDT"
    assert row["quote_volume_24h"] == 21500.0
    assert row["price_tick_estimate"] == 0.0001
    assert row["amount_step_estimate"] == 0.1
    assert row["min_notional_quote_estimate"] == 5.0
    assert row["top_of_book_quote"] == min(0.2149 * 4000, 0.2151 * 5000)



def test_nonkyc_universe_normalization_from_public_payloads():
    cfg = default_nonkyc_config()
    market_list = [
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
    ]
    tickers = [
        {
            "ticker_id": "XMR_USDT",
            "type": "market",
            "base_currency": "XMR",
            "target_currency": "USDT",
            "last_price": "150.5",
            "base_volume": "325.0",
            "target_volume": "48912.5",
            "bid": "150.4",
            "ask": "150.6",
        }
    ]

    df = NonKYCPublicScreener._build_universe_frame(market_list, tickers, cfg)

    assert len(df) == 1
    row = df.iloc[0]
    assert row["trading_pair"] == "XMR-USDT"
    assert row["exchange_symbol"] == "XMR/USDT"
    assert row["quote_volume_24h"] == 48912.5
    assert row["price_tick_estimate"] == 0.01
    assert row["amount_step_estimate"] == 0.001
    assert row["spread_bps"] > 0



def test_build_candle_ingestor_manifest_uses_slash_pairs(tmp_path: Path):
    cfg = default_nonkyc_config()
    selected = pd.DataFrame(
        [
            {
                "trading_pair": "BTC-USDT",
                "exchange_symbol": "BTC/USDT",
                "connector": "nonkyc",
            },
            {
                "trading_pair": "XMR-USDT",
                "exchange_symbol": "XMR/USDT",
                "connector": "nonkyc",
            },
        ]
    )
    run = ScreeningRun(
        connector="nonkyc",
        config=cfg,
        universe=selected.copy(),
        shortlist=selected.copy(),
        final=selected.copy(),
        selected=selected.copy(),
        started_at="2026-03-23T00:00:00Z",
        finished_at="2026-03-23T00:05:00Z",
    )

    manifest = build_candle_ingestor_manifest(
        run,
        base_url="https://api.nonkyc.io/api/v2",
        trade_limit=500,
    )

    assert manifest["exchanges"]["nonkyc"]["pairs"] == ["BTC/USDT", "XMR/USDT"]
    assert manifest["exchanges"]["nonkyc"]["intervals"] == [cfg.interval]
    assert manifest["exchanges"]["nonkyc"]["trades"]["limit"] == 500
