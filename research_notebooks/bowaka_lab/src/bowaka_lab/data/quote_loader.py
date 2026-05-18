"""Per-session quote loader mirroring MinuteBarLoader.

Reads quotes from a partitioned tree
``<data_root>/parquet/quotes/vendor=<v>/feed=<f>/session_date=YYYY-MM-DD/symbol=X.parquet``.
Each parquet file holds the columns produced by ``fetch_quotes``:
``symbol, timestamp, bid_price, ask_price, bid_size, ask_size, spread, mid, spread_pct``.

The loader is callable so it slots into ``BowakaPortfolioBacktester`` next to
``MinuteBarLoader``. It NEVER raises on a missing partition — it returns an
empty DataFrame so engine wiring can branch on ``quotes.empty``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd


_QUOTE_COLUMNS = (
    "symbol", "timestamp", "bid_price", "ask_price",
    "bid_size", "ask_size", "spread", "mid", "spread_pct",
)


class QuoteLoader:
    """Lazy loader that returns quotes for a (trade_date, symbols) pair.

    Behavior is deliberately matched to ``MinuteBarLoader`` so a notebook can
    drop one in alongside the other with the same call shape.
    """

    def __init__(self, quote_root: Path | str):
        self.quote_root = Path(quote_root)

    def __call__(self, trade_date: date, symbols: Iterable[str]) -> pd.DataFrame:
        return self.quotes_for(trade_date, symbols)

    def _session_dir(self, trade_date: date) -> Path:
        return self.quote_root / f"session_date={trade_date.isoformat()}"

    def has_quotes_for(self, trade_date: date) -> bool:
        """Cheap existence check — only verifies the session directory exists,
        not the per-symbol files (callers can hit ``quotes_for`` for that)."""
        return self._session_dir(trade_date).exists()

    def quotes_for(self, trade_date: date, symbols: Iterable[str]) -> pd.DataFrame:
        session_dir = self._session_dir(trade_date)
        if not session_dir.exists():
            return _empty_quotes()
        frames: list[pd.DataFrame] = []
        for sym in symbols:
            f = session_dir / f"symbol={sym}.parquet"
            if not f.exists():
                continue
            frames.append(pd.read_parquet(f))
        if not frames:
            return _empty_quotes()
        df = pd.concat(frames, ignore_index=True)
        df = df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
        # Backfill derived columns if the partition lacked them.
        if "spread" not in df.columns:
            df["spread"] = df["ask_price"] - df["bid_price"]
        if "mid" not in df.columns:
            df["mid"] = (df["ask_price"] + df["bid_price"]) / 2.0
        if "spread_pct" not in df.columns:
            df["spread_pct"] = (df["spread"] / df["mid"]).where(df["mid"] > 0, 0.0)
        return df


def _empty_quotes() -> pd.DataFrame:
    return pd.DataFrame(columns=list(_QUOTE_COLUMNS))
