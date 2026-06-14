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

#: Optional microstructure columns the SIP lake already carries on every bar
#: (written by ``_coerce_bar_row`` in ``backfill.py``). Surfaced via the opt-in
#: ``with_microstructure=True`` read flag so the impact model (sell-side size
#: cap, PB.2) gets a *stable, typed* per-minute volume signal regardless of the
#: partition's source. ``vwap`` → ``Float64``, ``trade_count`` → ``Int64``.
MICROSTRUCTURE_COLUMNS = ("vwap", "trade_count")


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
    col = df["timestamp"]
    dt = col.dtype
    # Dtype-aware vectorized timestamp normalisation. ``pd.to_datetime(utc=True)``
    # is ~100x slower on an ALREADY-datetime column (profiled: ~31% of minute-read
    # self-time was ``datetimes.__iter__`` — pd.to_datetime iterating element-wise),
    # yet the lake stores ``datetime64[us, UTC]`` already. The fast paths below are
    # byte-identical (verified ``base.equals(cand)`` on the lake schema) and only
    # fall back to ``pd.to_datetime`` for object/string timestamps.
    if isinstance(dt, pd.DatetimeTZDtype):
        df["timestamp"] = col.dt.tz_convert("UTC")
    elif pd.api.types.is_datetime64_dtype(dt):
        df["timestamp"] = col.dt.tz_localize("UTC")
    else:
        df["timestamp"] = pd.to_datetime(col, utc=True)
    return df


def _empty_bars() -> pd.DataFrame:
    return pd.DataFrame(columns=_BAR_COLUMNS)


def _apply_microstructure(df: pd.DataFrame, enabled: bool) -> pd.DataFrame:
    """Guarantee :data:`MICROSTRUCTURE_COLUMNS` exist with stable nullable dtypes.

    Purely additive: passes real values through when the partition already
    carries them (the SIP lake does), fills ``pd.NA`` with the right dtype when a
    source lacks them (synthetic minute fixtures / IEX / older partitions). Never
    drops or reorders existing columns, and is a no-op when ``enabled`` is False —
    so the default read path is byte-identical to before this flag existed.
    """
    if not enabled:
        return df
    df = df.copy()
    if "vwap" in df.columns:
        df["vwap"] = pd.to_numeric(df["vwap"], errors="coerce").astype("Float64")
    else:
        df["vwap"] = pd.Series(pd.NA, index=df.index, dtype="Float64")
    if "trade_count" in df.columns:
        df["trade_count"] = pd.to_numeric(df["trade_count"], errors="coerce").astype("Int64")
    else:
        df["trade_count"] = pd.Series(pd.NA, index=df.index, dtype="Int64")
    return df


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
        with_microstructure: bool = False,
    ) -> pd.DataFrame:
        """Daily bars for ``symbol`` over the inclusive date range ``[start, end]``.

        With ``with_microstructure=True`` the returned frame is guaranteed to
        carry the :data:`MICROSTRUCTURE_COLUMNS` (``vwap``/``trade_count``) with
        stable nullable dtypes — opt-in and purely additive; the default call is
        byte-identical to before the flag existed.
        """
        path = _layout.daily_bars_path(
            self.root, symbol, vendor=self.vendor, feed=feed, adjustment=adjustment
        )
        if not path.is_file():
            return _apply_microstructure(_empty_bars(), with_microstructure)
        df = _normalise_bars(pd.read_parquet(path))
        if df.empty:
            return _apply_microstructure(df, with_microstructure)
        start_d, end_d = _to_date(start), _to_date(end)
        if "session_date" in df.columns:
            sd = pd.to_datetime(df["session_date"]).dt.date
            df = df[(sd >= start_d) & (sd <= end_d)]
        else:
            lo = _to_utc_ts(start_d)
            hi = _to_utc_ts(end_d) + pd.Timedelta(days=1)
            df = df[(df["timestamp"] >= lo) & (df["timestamp"] < hi)]
        return _apply_microstructure(
            df.sort_values("timestamp").reset_index(drop=True), with_microstructure
        )

    def minute_bars(
        self,
        symbol: str,
        start: Any,
        end: Any,
        *,
        feed: str = "iex",
        adjustment: str = "raw",
        with_microstructure: bool = False,
    ) -> pd.DataFrame:
        """Minute bars for ``symbol`` in the inclusive range ``[start, end]``.

        Reads only the per-symbol/month partitions that overlap the range. With
        ``with_microstructure=True`` the frame is guaranteed to carry the
        :data:`MICROSTRUCTURE_COLUMNS` (opt-in, additive; default unchanged).
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
            return _apply_microstructure(_empty_bars(), with_microstructure)
        df = _normalise_bars(pd.concat(frames, ignore_index=True))
        df = df[(df["timestamp"] >= start_ts) & (df["timestamp"] <= end_ts)]
        return _apply_microstructure(
            df.sort_values("timestamp")
            .drop_duplicates(subset=["timestamp"], keep="last")
            .reset_index(drop=True),
            with_microstructure,
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

    # -- trades (raw tape) — PA.2 -----------------------------------------
    def trades_between(
        self, symbol: str, start: Any, end: Any, *, feed: str = "iex"
    ) -> pd.DataFrame:
        """Raw trade prints for ``symbol`` in ``[start, end]`` (inclusive).

        May return empty — the trade-tape stage is opt-in (PA.2); the layout
        reserves the slot. Stored RAW (multiple prints share a timestamp), so
        unlike :meth:`quotes` the result is NOT deduped on timestamp; it is
        stable-sorted by timestamp so the tape sequence is preserved.
        """
        start_ts, end_ts = _to_utc_ts(start), _to_utc_ts(end)
        frames: list[pd.DataFrame] = []
        for year, month in _months_between(start_ts, end_ts):
            path = _layout.trades_path(self.root, symbol, year, month, vendor=self.vendor, feed=feed)
            if path.is_file():
                frames.append(pd.read_parquet(path))
        if not frames:
            return pd.DataFrame()
        df = _normalise_bars(pd.concat(frames, ignore_index=True))
        if "timestamp" not in df.columns:
            return df
        df = df[(df["timestamp"] >= start_ts) & (df["timestamp"] <= end_ts)]
        return df.sort_values("timestamp", kind="stable").reset_index(drop=True)

    def auctions_between(
        self, symbol: str, start: Any, end: Any, *, feed: str = "iex"
    ) -> pd.DataFrame:
        """Official open/close auction prints for ``symbol`` in ``[start, end]`` (§5.1).

        One row per session carrying the official opening + closing auction price
        (Alpaca ``GET /v2/stocks/auctions``). May be empty — the auctions stage is
        opt-in (the layout reserves the slot); the EOD-mark consumer falls back to
        the daily-bar close when a session is absent. Stable-sorted by timestamp.
        """
        start_ts, end_ts = _to_utc_ts(start), _to_utc_ts(end)
        frames: list[pd.DataFrame] = []
        for year, month in _months_between(start_ts, end_ts):
            path = _layout.auctions_path(self.root, symbol, year, month, vendor=self.vendor, feed=feed)
            if path.is_file():
                frames.append(pd.read_parquet(path))
        if not frames:
            return pd.DataFrame()
        df = _normalise_bars(pd.concat(frames, ignore_index=True))
        if "timestamp" not in df.columns:
            return df
        df = df[(df["timestamp"] >= start_ts) & (df["timestamp"] <= end_ts)]
        return df.sort_values("timestamp", kind="stable").reset_index(drop=True)

    def quotes_fine_between(
        self, symbol: str, start: Any, end: Any, *, feed: str = "iex"
    ) -> pd.DataFrame:
        """Fine NBBO (sub-minute + bid/ask exchange + tape) for ``symbol`` in
        ``[start, end]``.

        May return empty — the fine-quote stage is opt-in (PA.3), a SIBLING of the
        canonical ``quotes/`` tree (so it never drifts ``quote_partitions_hash``).
        Stable-sorted by timestamp; NOT deduped on timestamp (sub-minute ticks may
        share a minute).
        """
        start_ts, end_ts = _to_utc_ts(start), _to_utc_ts(end)
        frames: list[pd.DataFrame] = []
        for year, month in _months_between(start_ts, end_ts):
            path = _layout.quotes_fine_path(self.root, symbol, year, month, vendor=self.vendor, feed=feed)
            if path.is_file():
                frames.append(pd.read_parquet(path))
        if not frames:
            return pd.DataFrame()
        df = _normalise_bars(pd.concat(frames, ignore_index=True))
        if "timestamp" not in df.columns:
            return df
        df = df[(df["timestamp"] >= start_ts) & (df["timestamp"] <= end_ts)]
        return df.sort_values("timestamp", kind="stable").reset_index(drop=True)

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

    # -- SIP-aware reads (realism remediation 2 Phase 10, audit §11 Phase 9) ---
    #
    # Thin wrappers that pre-bind ``feed="sip"`` (and the SIP default
    # adjustment for daily bars) on top of the generic read methods above. The
    # store still works exactly the same way for the IEX feed — these helpers
    # exist so SIP-aware callers can spell the read explicitly, and so any
    # SIP-payload existence probe goes through one canonical entry point. The
    # lake has no SIP data today; a call on a SIP-less lake returns empty
    # frames / ``None`` the same way the IEX path does when its partitions
    # are absent.
    # ----------------------------------------------------------------------
    def sip_daily_bars(
        self,
        symbol: str,
        start: Any,
        end: Any,
        *,
        adjustment: str = _layout.SIP_DAILY_ADJUSTMENT,
        with_microstructure: bool = False,
    ) -> pd.DataFrame:
        """SIP daily bars for ``symbol`` over the inclusive date range.

        Convenience wrapper over :meth:`daily_bars` that pins ``feed="sip"``
        and defaults ``adjustment`` to ``split_adjusted`` (the SIP convention).
        """
        return self.daily_bars(
            symbol, start, end, feed=_layout.FEED_SIP, adjustment=adjustment,
            with_microstructure=with_microstructure,
        )

    def sip_minute_bars(
        self,
        symbol: str,
        start: Any,
        end: Any,
        *,
        adjustment: str = "raw",
        with_microstructure: bool = False,
    ) -> pd.DataFrame:
        """SIP minute bars for ``symbol`` over the inclusive range.

        Convenience wrapper over :meth:`minute_bars` that pins ``feed="sip"``.
        SIP minute bars are raw by convention (same as IEX).
        """
        return self.minute_bars(
            symbol, start, end, feed=_layout.FEED_SIP, adjustment=adjustment,
            with_microstructure=with_microstructure,
        )

    def sip_quotes(self, symbol: str, start: Any, end: Any) -> pd.DataFrame:
        """SIP quotes for ``symbol`` over the inclusive range."""
        return self.quotes(symbol, start, end, feed=_layout.FEED_SIP)

    def sip_quotes_at_or_before(
        self,
        symbol: str,
        ts: Any,
        *,
        max_age_seconds: float = 60.0,
    ) -> Optional[QuoteRow]:
        """Latest SIP quote for ``symbol`` at-or-before ``ts``, within
        ``max_age_seconds``.

        Convenience wrapper over :meth:`quotes_at_or_before` that pins
        ``feed="sip"``. Returns ``None`` on a SIP-less lake (the normal case).
        """
        return self.quotes_at_or_before(
            symbol, ts, max_age_seconds=max_age_seconds, feed=_layout.FEED_SIP,
        )

    def sip_trades_between(self, symbol: str, start: Any, end: Any) -> pd.DataFrame:
        """SIP raw trade prints for ``symbol`` over ``[start, end]``.

        Convenience wrapper over :meth:`trades_between` pinning ``feed="sip"``.
        """
        return self.trades_between(symbol, start, end, feed=_layout.FEED_SIP)

    def sip_quotes_fine_between(self, symbol: str, start: Any, end: Any) -> pd.DataFrame:
        """SIP fine NBBO for ``symbol`` over ``[start, end]`` (feed pinned to sip).

        Convenience wrapper over :meth:`quotes_fine_between`.
        """
        return self.quotes_fine_between(symbol, start, end, feed=_layout.FEED_SIP)

    def has_sip_partitions(self) -> bool:
        """Return ``True`` when the lake has any SIP partition (bars / quotes).

        Delegates to :func:`bowaka_common.marketdata.layout.sip_partitions_available`.
        """
        return _layout.sip_partitions_available(self.root, vendor=self.vendor)
