"""``MarketDataStore`` — domain read API over the shared market-data lake.

Strategy-neutral. Both ``bowaka_lab`` and ``bowaka_v2_lab`` read through this
class so neither owns the on-disk layout. All bar/quote frames come back with
tz-aware (UTC) ``timestamp`` columns.
"""
from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from . import layout as _layout

_BAR_COLUMNS = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]


# --------------------------------------------------------------------------
# Quote row
# --------------------------------------------------------------------------
@dataclass
class QuoteRow:
    """A single NBBO quote observation returned by :meth:`MarketDataStore.quotes_at_or_before`.

    ``source`` is ``"historical"`` for a quote read from the lake's ``quotes/``
    partitions. The value ``"synthetic"`` is reserved for callers that construct
    a fabricated quote — the store itself never returns a synthetic ``QuoteRow``.

    ``timestamp`` is the row's actual UTC timestamp from the quote partition, so
    callers can record the true quote time (not the request time). Added for
    realism remediation 2 Phase 5 (audit P1-002).
    """

    bid: float
    ask: float
    bid_size: float
    ask_size: float
    mid: float
    spread_pct: float
    quote_age_seconds: float
    source: str = "historical"
    timestamp: Optional[pd.Timestamp] = None


# --------------------------------------------------------------------------
# Root resolution
# --------------------------------------------------------------------------
def _find_repo_root(start: Path) -> Path | None:
    cur = start.resolve()
    for _ in range(15):
        if (cur / "Makefile").is_file() and (cur / "research_notebooks").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def default_market_data_root() -> Path:
    """The in-repo default lake root: ``<repo_root>/research_notebooks/market_data``."""
    repo = _find_repo_root(Path(__file__))
    if repo is None:
        raise RuntimeError(
            "could not locate the quants-lab repo root (Makefile + research_notebooks/) "
            "to derive the default MARKET_DATA_ROOT; set MARKET_DATA_ROOT explicitly"
        )
    return repo / "research_notebooks" / "market_data"


def resolve_market_data_root(
    explicit: str | Path | None = None, *, create: bool = True
) -> Path:
    """Resolve the shared market-data lake root.

    Precedence: explicit arg > ``MARKET_DATA_ROOT`` env var > in-repo default
    ``<repo_root>/research_notebooks/market_data``. Never raises for an unset
    env var. Creates the directory when ``create`` is True (the default).
    """
    if explicit is not None and str(explicit).strip():
        root = Path(explicit)
    else:
        env = os.environ.get("MARKET_DATA_ROOT")
        if env and env.strip():
            root = Path(env)
        else:
            root = default_market_data_root()
    root = root.expanduser()
    if create:
        root.mkdir(parents=True, exist_ok=True)
    return root


# --------------------------------------------------------------------------
# Conversion helpers
# --------------------------------------------------------------------------
def _to_utc_ts(x: Any) -> pd.Timestamp:
    ts = pd.Timestamp(x)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def _to_date(x: Any) -> _dt.date:
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    return pd.Timestamp(x).date()


def _months_between(start_ts: pd.Timestamp, end_ts: pd.Timestamp) -> list[tuple[int, int]]:
    """Inclusive list of (year, month) pairs spanned by ``[start_ts, end_ts]``."""
    y, m = start_ts.year, start_ts.month
    ey, em = end_ts.year, end_ts.month
    out: list[tuple[int, int]] = []
    while (y, m) <= (ey, em):
        out.append((y, m))
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def _normalise_bars(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "timestamp" not in df.columns:
        return df
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def _empty_bars() -> pd.DataFrame:
    return pd.DataFrame(columns=_BAR_COLUMNS)


# --------------------------------------------------------------------------
# Store
# --------------------------------------------------------------------------
class MarketDataStore:
    """Read API for the shared market-data lake.

    Parameters
    ----------
    root:
        Lake root. ``None`` resolves via :func:`resolve_market_data_root`.
    vendor:
        Vendor partition (default ``"alpaca"``).
    """

    def __init__(self, root: str | Path | None = None, *, vendor: str = "alpaca"):
        self.root: Path = resolve_market_data_root(root)
        self.vendor = vendor

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"MarketDataStore(root={self.root!s}, vendor={self.vendor!r})"

    # -- bars --------------------------------------------------------------
    def daily_bars(
        self,
        symbol: str,
        start: Any,
        end: Any,
        *,
        feed: str = "iex",
        adjustment: str = "raw",
    ) -> pd.DataFrame:
        """Daily bars for ``symbol`` over the inclusive date range ``[start, end]``."""
        path = _layout.daily_bars_path(
            self.root, symbol, vendor=self.vendor, feed=feed, adjustment=adjustment
        )
        if not path.is_file():
            return _empty_bars()
        df = _normalise_bars(pd.read_parquet(path))
        if df.empty:
            return df
        start_d, end_d = _to_date(start), _to_date(end)
        if "session_date" in df.columns:
            sd = pd.to_datetime(df["session_date"]).dt.date
            df = df[(sd >= start_d) & (sd <= end_d)]
        else:
            lo = _to_utc_ts(start_d)
            hi = _to_utc_ts(end_d) + pd.Timedelta(days=1)
            df = df[(df["timestamp"] >= lo) & (df["timestamp"] < hi)]
        return df.sort_values("timestamp").reset_index(drop=True)

    def minute_bars(
        self,
        symbol: str,
        start: Any,
        end: Any,
        *,
        feed: str = "iex",
        adjustment: str = "raw",
    ) -> pd.DataFrame:
        """Minute bars for ``symbol`` in the inclusive range ``[start, end]``.

        Reads only the per-symbol/month partitions that overlap the range.
        """
        start_ts, end_ts = _to_utc_ts(start), _to_utc_ts(end)
        frames: list[pd.DataFrame] = []
        for year, month in _months_between(start_ts, end_ts):
            path = _layout.minute_bars_path(
                self.root, symbol, year, month,
                vendor=self.vendor, feed=feed, adjustment=adjustment,
            )
            if path.is_file():
                frames.append(pd.read_parquet(path))
        if not frames:
            return _empty_bars()
        df = _normalise_bars(pd.concat(frames, ignore_index=True))
        df = df[(df["timestamp"] >= start_ts) & (df["timestamp"] <= end_ts)]
        return (
            df.sort_values("timestamp")
            .drop_duplicates(subset=["timestamp"], keep="last")
            .reset_index(drop=True)
        )

    # -- quotes ------------------------------------------------------------
    def quotes(
        self, symbol: str, start: Any, end: Any, *, feed: str = "iex"
    ) -> pd.DataFrame:
        """Quotes for ``symbol`` in ``[start, end]``.

        May return empty — the current backfill has no quote stage; the layout
        reserves the slot for a future one.
        """
        start_ts, end_ts = _to_utc_ts(start), _to_utc_ts(end)
        frames: list[pd.DataFrame] = []
        for year, month in _months_between(start_ts, end_ts):
            path = _layout.quotes_path(self.root, symbol, year, month, vendor=self.vendor, feed=feed)
            if path.is_file():
                frames.append(pd.read_parquet(path))
        if not frames:
            return pd.DataFrame()
        df = _normalise_bars(pd.concat(frames, ignore_index=True))
        if "timestamp" in df.columns:
            df = df[(df["timestamp"] >= start_ts) & (df["timestamp"] <= end_ts)]
        return df.sort_values("timestamp").reset_index(drop=True) if "timestamp" in df.columns else df

    def quotes_at_or_before(
        self,
        symbol: str,
        ts: Any,
        *,
        max_age_seconds: float = 60.0,
        feed: str = "iex",
    ) -> Optional[QuoteRow]:
        """The latest historical quote for ``symbol`` at or before ``ts``.

        Reads the lake's ``quotes/`` partition for the (symbol, month) covering
        ``ts``. Returns the most recent quote whose timestamp is ``<= ts`` and no
        older than ``max_age_seconds``, as a :class:`QuoteRow` with
        ``source="historical"``.

        Returns ``None`` when:

        - the quote partition is absent (the normal case on the current lake,
          which has no quote-ingestion stage), or
        - no quote in the partition is at-or-before ``ts``, or
        - the newest at-or-before quote is older than ``max_age_seconds``.
        """
        target = _to_utc_ts(ts)
        path = _layout.quotes_path(
            self.root, symbol, target.year, target.month, vendor=self.vendor, feed=feed
        )
        if not path.is_file():
            return None
        try:
            df = pd.read_parquet(path)
        except Exception:  # noqa: BLE001 — an unreadable partition is "no quote"
            return None
        if df.empty or "timestamp" not in df.columns:
            return None
        df = _normalise_bars(df)
        df = df[df["timestamp"] <= target]
        if df.empty:
            return None
        row = df.sort_values("timestamp").iloc[-1]
        age = (target - row["timestamp"]).total_seconds()
        if age > float(max_age_seconds):
            return None
        bid = float(row.get("bid", 0.0) or 0.0)
        ask = float(row.get("ask", 0.0) or 0.0)
        bid_size = float(row.get("bid_size", 0.0) or 0.0)
        ask_size = float(row.get("ask_size", 0.0) or 0.0)
        mid = float(row["mid"]) if "mid" in row and pd.notna(row["mid"]) else (bid + ask) / 2.0
        if "spread_pct" in row and pd.notna(row["spread_pct"]):
            spread_pct = float(row["spread_pct"])
        else:
            spread_pct = ((ask - bid) / mid) if mid > 0 else 0.0
        # The row's actual UTC timestamp (audit P1-002). Consumers record this
        # so quote-age telemetry reflects the real quote time, not the request.
        row_ts = pd.Timestamp(row["timestamp"])
        if row_ts.tzinfo is None:
            row_ts = row_ts.tz_localize("UTC")
        else:
            row_ts = row_ts.tz_convert("UTC")
        return QuoteRow(
            bid=bid,
            ask=ask,
            bid_size=bid_size,
            ask_size=ask_size,
            mid=mid,
            spread_pct=spread_pct,
            quote_age_seconds=max(0.0, age),
            source="historical",
            timestamp=row_ts,
        )

    # -- corporate actions -------------------------------------------------
    def corporate_actions(self, symbol: str, start: Any, end: Any) -> pd.DataFrame:
        """Corporate actions for ``symbol`` with ``ex_date`` in ``[start, end]``."""
        path = _layout.corporate_actions_path(self.root, symbol, vendor=self.vendor)
        if not path.is_file():
            return pd.DataFrame()
        df = pd.read_parquet(path)
        if df.empty or "ex_date" not in df.columns:
            return df
        ex = pd.to_datetime(df["ex_date"]).dt.date
        start_d, end_d = _to_date(start), _to_date(end)
        return df[(ex >= start_d) & (ex <= end_d)].reset_index(drop=True)

    # -- assets ------------------------------------------------------------
    def assets(self, snapshot_id: str | None = None) -> pd.DataFrame:
        """Asset snapshot. ``None`` returns the most recent snapshot, or empty."""
        if snapshot_id is not None:
            path = _layout.assets_path(self.root, snapshot_id, vendor=self.vendor)
            return pd.read_parquet(path) if path.is_file() else pd.DataFrame()
        root = _layout.assets_root(self.root, vendor=self.vendor)
        if not root.is_dir():
            return pd.DataFrame()
        snaps = sorted(root.glob("snapshot_id=*/assets.parquet"))
        return pd.read_parquet(snaps[-1]) if snaps else pd.DataFrame()

    def latest_snapshot_id(self) -> str | None:
        """Return the most recent asset ``snapshot_id`` present, or ``None``."""
        root = _layout.assets_root(self.root, vendor=self.vendor)
        if not root.is_dir():
            return None
        snaps = sorted(root.glob("snapshot_id=*/assets.parquet"))
        if not snaps:
            return None
        return snaps[-1].parent.name.split("=", 1)[1]
