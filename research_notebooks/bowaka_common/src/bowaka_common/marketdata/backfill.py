"""Alpaca market-data ingestion for the shared lake.

Migrated from ``bowaka_lab/db_tools/_backfill_lib.py``. Changes vs the original:

- **Parquet only** — every Mongo write path is removed. Audit and
  ingestion-run metadata land under ``_ingestion/`` in the lake instead.
- Writes the **canonical layout** (see :mod:`bowaka_common.marketdata.layout`);
  minute bars are grouped per symbol/month, not per session.
- The strategy-specific **scope-3 / ADV universe** stage is gone — that is
  ``bowaka_lab``'s concern. The minute stage takes an explicit ``targets``
  table of ``(session_date, symbol)`` pairs supplied by the caller.
- Network access is injectable: ``fetch_assets`` / ``fetch_daily_bars`` /
  ``fetch_minute_bars`` accept a fetcher callable, so unit tests run with no
  network and no ``alpaca`` dependency.

``alpaca-py`` is imported lazily — only the default fetchers touch it.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from . import layout as _layout

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_EXCLUDE_NAME_PATTERN: re.Pattern = re.compile(
    r"\b("
    r"iShares|ProShares|Direxion|Invesco|SPDR|Vanguard|"
    r"WisdomTree|VanEck|First\s+Trust|Global\s+X|"
    r"2X|3X|-1X|-2X|-3X|"
    r"Inverse|Leveraged|Ultra|UltraPro|UltraShort|UltraBear|"
    r"Bull\s+\dX|Bear\s+\dX|"
    r"ETF|ETN|Fund|Trust|"
    r"Note(?:\s|$)|"
    r"Preferred(?:\s|,|$)"
    r")\b",
    re.IGNORECASE,
)

EXCHANGES_DEFAULT: tuple[str, ...] = ("NASDAQ", "NYSE", "ARCA", "AMEX", "BATS")
ADJUSTMENT_DEFAULT: str = "raw"
RATE_LIMIT_DEFAULT_RPM: int = 180
SYMBOL_BATCH_SIZE_DEFAULT: int = 200
ADV_WINDOW_DAYS_DEFAULT: int = 20

NON_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({400, 401, 403, 404, 422})

#: Fetcher signature: (batch_symbols, timeframe, start_dt, end_dt) ->
#: {symbol: [coerced bar-row dict, ...]}. ``timeframe`` is "1d" or "1m".
BarsFetcher = Callable[[list, str, datetime, datetime], dict]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class BackfillConfig:
    """Backfill run configuration.

    ``lake_root`` is the shared market-data lake root (resolve it with
    :func:`bowaka_common.marketdata.resolve_market_data_root`). There is no
    Mongo configuration — the lake is the single canonical store.
    """

    api_key: str
    api_secret: str
    paper: bool
    feed: str
    start_date: date
    end_date: date
    lake_root: Path
    price_min: float = 1.0
    price_max: float = 20.0
    adv_min: float = 200_000.0
    adv_window_days: int = ADV_WINDOW_DAYS_DEFAULT
    rate_limit_rpm: int = RATE_LIMIT_DEFAULT_RPM
    allowed_exchanges: tuple[str, ...] = EXCHANGES_DEFAULT
    exclude_name_pattern: re.Pattern = field(default=DEFAULT_EXCLUDE_NAME_PATTERN)
    batch_size_symbols: int = SYMBOL_BATCH_SIZE_DEFAULT
    resume: bool = True
    adjustment: str = ADJUSTMENT_DEFAULT
    asset_snapshot_max_age_days: int = 7

    @property
    def daily_fetch_start(self) -> date:
        """Start daily-bar fetch this far before ``start_date`` so a downstream
        ADV rolling window has warmup data."""
        pad = int(self.adv_window_days * 1.5) + 7
        return self.start_date - timedelta(days=pad)

    @property
    def feed_enum(self) -> Any:
        """Lazy: ``alpaca.data.enums.DataFeed`` member matching ``feed``."""
        from alpaca.data.enums import DataFeed

        return DataFeed[self.feed.upper()]


# ---------------------------------------------------------------------------
# Incremental tail planning
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class IncrementalPlan:
    """Per-symbol update decision. ``action`` ∈
    {``"fetch_full"``, ``"up_to_date"``, ``"fetch_tail"``}."""

    action: Literal["fetch_full", "up_to_date", "fetch_tail"]
    start: Optional[date] = None
    end: Optional[date] = None
    existing_max_session: Optional[date] = None


_XNYS_CALENDAR_CACHE: Any = None


def _get_xnys_calendar():
    global _XNYS_CALENDAR_CACHE
    if _XNYS_CALENDAR_CACHE is None:
        import exchange_calendars as xcals

        _XNYS_CALENDAR_CACHE = xcals.get_calendar("XNYS")
    return _XNYS_CALENDAR_CACHE


def incremental_window(
    symbol_file: Path,
    target_end_date: date,
    calendar: Any = None,
    *,
    target_start_date: date | None = None,
) -> IncrementalPlan:
    """Decide how to update a per-symbol daily-bar Parquet file.

    Forward extension (``target_end_date`` advanced) → ``fetch_tail``. A missing
    head (``target_start_date`` earlier than the file's first session) → a full
    re-fetch, so changing either end of the date range fills what is missing.
    """
    path = Path(symbol_file)
    if not path.exists():
        return IncrementalPlan(action="fetch_full")
    try:
        df = pd.read_parquet(path)
    except Exception:
        return IncrementalPlan(action="fetch_full")
    if df.empty or "timestamp" not in df.columns:
        return IncrementalPlan(action="fetch_full")
    try:
        ts = pd.to_datetime(df["timestamp"])
        if getattr(ts.dt, "tz", None) is not None:
            ts = ts.dt.tz_convert("America/New_York")
        else:
            ts = ts.dt.tz_localize("America/New_York")
        existing_max = ts.dt.date.max()
        existing_min = ts.dt.date.min()
    except Exception:
        return IncrementalPlan(action="fetch_full")

    # Missing head: the file starts materially later than the requested start →
    # full re-fetch. The 7-day tolerance absorbs weekends/holidays so a re-run
    # over the same range is not mistaken for a missing head.
    if target_start_date is not None and existing_min > target_start_date + timedelta(days=7):
        return IncrementalPlan(action="fetch_full")

    if existing_max >= target_end_date:
        return IncrementalPlan(action="up_to_date", existing_max_session=existing_max)

    cal = calendar if calendar is not None else _get_xnys_calendar()
    next_session_ts = cal.next_session(pd.Timestamp(existing_max))
    return IncrementalPlan(
        action="fetch_tail",
        start=pd.Timestamp(next_session_ts).date(),
        end=target_end_date,
        existing_max_session=existing_max,
    )


# ---------------------------------------------------------------------------
# Env / dotenv
# ---------------------------------------------------------------------------
def find_and_load_dotenv() -> Path | None:
    """Walk up from CWD until an ``.env`` is found; load it; return its path."""
    here = Path.cwd().resolve()
    for ancestor in [here, *here.parents]:
        bow_env = ancestor / "research_notebooks" / "bowaka_lab" / ".env"
        if bow_env.is_file():
            _load_dotenv_file(bow_env)
            return bow_env
        if (ancestor / ".env").is_file():
            _load_dotenv_file(ancestor / ".env")
            return ancestor / ".env"
    return None


def _load_dotenv_file(path: Path) -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(path, override=False)
        return
    except Exception:
        pass
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def resolve_env() -> dict[str, Any]:
    """Read ``ALPACA_*`` from os.environ. Mongo is no longer required."""
    missing: list[str] = []
    out: dict[str, Any] = {}
    for key in ("ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY"):
        v = os.environ.get(key)
        if not v:
            missing.append(key)
        out[key] = v
    if missing:
        raise RuntimeError(f"Missing required env vars: {missing}. Set them in .env or the shell.")
    out["ALPACA_PAPER"] = os.environ.get("ALPACA_PAPER", "true").lower() not in ("false", "0", "no")
    return out


# ---------------------------------------------------------------------------
# Rate limiter + retries
# ---------------------------------------------------------------------------
class RateLimiter:
    """Sliding-window rate limiter; one token per call."""

    def __init__(self, rpm: int):
        if rpm <= 0:
            raise ValueError("rpm must be > 0")
        self.rpm = int(rpm)
        self.interval = 60.0 / float(rpm)
        self._lock = threading.Lock()
        self._next_allowed = time.monotonic()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            if now < self._next_allowed:
                time.sleep(self._next_allowed - now)
                now = time.monotonic()
            self._next_allowed = now + self.interval


def _status_code_of(exc: BaseException) -> int | None:
    for attr in ("status_code", "status", "code", "http_status"):
        val = getattr(exc, attr, None)
        if isinstance(val, int):
            return val
    msg = str(exc).lower()
    for code in NON_RETRYABLE_STATUS_CODES:
        if str(code) in msg:
            return code
    return None


def with_retries(
    fn: Callable[..., Any],
    *args: Any,
    max_attempts: int = 3,
    log: logging.Logger | None = None,
    base_delay: float = 1.0,
    **kwargs: Any,
) -> Any:
    """Call ``fn`` with retries on transient errors (not on 400/401/403/404/422)."""
    attempt = 1
    while True:
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            code = _status_code_of(exc)
            if code in NON_RETRYABLE_STATUS_CODES or attempt >= max_attempts:
                raise
            sleep_for = base_delay * (2 ** (attempt - 1))
            if log is not None:
                log.warning("transient error %d/%d: %s; sleeping %.1fs", attempt, max_attempts, exc, sleep_for)
            time.sleep(sleep_for)
            attempt += 1


def _default_logger() -> logging.Logger:
    log = logging.getLogger("bowaka_common.marketdata.backfill")
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(handler)
        log.setLevel(logging.INFO)
    return log


# ---------------------------------------------------------------------------
# Path helpers (delegate to the canonical layout)
# ---------------------------------------------------------------------------
# Minute bars are always stored + read RAW (the actual live-traded intraday
# prices). The whole lab/strategy reads minute bars at adjustment="raw"
# (layout.DEFAULT_ADJUSTMENT, store.minute_bars' default, every supplier, the
# scan matrix, and the per-fold preflight). RAW is required for backtest-to-live
# parity: split-adjusted retroactively rewrites pre-split prices, which would
# skew the $1-20 price gate for any symbol that splits in-window. cfg.adjustment
# (e.g. split_adjusted) governs DAILY bars only (continuous ADV history).
MINUTE_ADJUSTMENT = "raw"


def daily_file(cfg: BackfillConfig, symbol: str) -> Path:
    return _layout.daily_bars_path(cfg.lake_root, symbol, feed=cfg.feed, adjustment=cfg.adjustment)


def daily_root(cfg: BackfillConfig) -> Path:
    return _layout.bars_timeframe_root(cfg.lake_root, "1d", feed=cfg.feed, adjustment=cfg.adjustment)


def minute_file(cfg: BackfillConfig, symbol: str, year: int, month: int) -> Path:
    return _layout.minute_bars_path(
        cfg.lake_root, symbol, year, month, feed=cfg.feed, adjustment=MINUTE_ADJUSTMENT)


def assets_file(cfg: BackfillConfig, snapshot_id: str) -> Path:
    return _layout.assets_path(cfg.lake_root, snapshot_id)


def manifest_file(cfg: BackfillConfig) -> Path:
    return _layout.ingestion_manifest_path(cfg.lake_root)


# ---------------------------------------------------------------------------
# Dataset hashing (cheap path+size stand-in for the manifest)
# ---------------------------------------------------------------------------
def compute_dataset_hash(root: Path) -> str:
    if not Path(root).exists():
        return "sha256:" + hashlib.sha256(b"").hexdigest()
    items: list[tuple[str, int]] = []
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(root)).replace("\\", "/")
            items.append((rel, p.stat().st_size))
    payload = json.dumps(items, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Bar coercion
# ---------------------------------------------------------------------------
def _coerce_bar_row(symbol: str, row: Any) -> dict[str, Any]:
    ts = getattr(row, "timestamp", None) or (row.get("t") if isinstance(row, dict) else None)
    if ts is None and isinstance(row, dict):
        ts = row.get("timestamp")
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")

    def _attr(name: str, alt: str, default: Any = None) -> Any:
        if hasattr(row, name):
            return getattr(row, name)
        if isinstance(row, dict):
            return row.get(name, row.get(alt, default))
        return default

    return {
        "symbol": symbol,
        "timestamp": ts,
        "open": float(_attr("open", "o", 0.0) or 0.0),
        "high": float(_attr("high", "h", 0.0) or 0.0),
        "low": float(_attr("low", "l", 0.0) or 0.0),
        "close": float(_attr("close", "c", 0.0) or 0.0),
        "volume": int(_attr("volume", "v", 0) or 0),
        "vwap": float(_attr("vwap", "vw", 0.0) or 0.0) or None,
        "trade_count": int(_attr("trade_count", "n", 0) or 0) or None,
    }


def _chunks(seq: list, n: int) -> Iterable[list]:
    for i in range(0, len(seq), max(1, n)):
        yield seq[i : i + n]


# ---------------------------------------------------------------------------
# Default Alpaca fetchers (lazy import; the only place that touches the network)
# ---------------------------------------------------------------------------
def make_alpaca_assets_fetcher(cfg: BackfillConfig) -> Callable[[], Iterable[Any]]:
    """Return a no-arg callable yielding raw active US-equity assets."""

    def _fetch() -> Iterable[Any]:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.enums import AssetClass, AssetStatus
        from alpaca.trading.requests import GetAssetsRequest

        trading = TradingClient(api_key=cfg.api_key, secret_key=cfg.api_secret, paper=cfg.paper)
        req = GetAssetsRequest(asset_class=AssetClass.US_EQUITY, status=AssetStatus.ACTIVE)
        return trading.get_all_assets(req)

    return _fetch


def make_alpaca_bars_fetcher(
    cfg: BackfillConfig, limiter: RateLimiter, log: logging.Logger
) -> BarsFetcher:
    """Return a :data:`BarsFetcher` backed by the Alpaca historical data API."""

    def _fetch(batch: list, timeframe: str, start_dt: datetime, end_dt: datetime) -> dict:
        from alpaca.data.enums import Adjustment
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        tf = TimeFrame.Day if timeframe == "1d" else TimeFrame.Minute
        client = StockHistoricalDataClient(api_key=cfg.api_key, secret_key=cfg.api_secret)
        # bowaka_v2 speedup-v2 P0-A follow-up — thread the configured adjustment
        # into the Alpaca SDK request so the actual bar payload matches the
        # ``cfg.adjustment`` partition label. Pre-patch the request omitted
        # ``adjustment`` and Alpaca defaulted to raw, which produced a silent
        # mislabel when ``cfg.adjustment="split_adjusted"`` wrote bars under
        # the ``_adjusted/`` partition path that were actually raw.
        _adjustment_enum_by_cfg: dict[str, Any] = {
            "raw": Adjustment.RAW,
            "split_adjusted": Adjustment.SPLIT,
            "split": Adjustment.SPLIT,
            "dividend_adjusted": Adjustment.DIVIDEND,
            "dividend": Adjustment.DIVIDEND,
            "all": Adjustment.ALL,
            "adjusted": Adjustment.ALL,
        }
        # Minute bars are RAW everywhere in the lab (see MINUTE_ADJUSTMENT) —
        # request raw from Alpaca so the payload matches the raw partition the
        # readers use. Only DAILY uses cfg.adjustment (split_adjusted for ADV).
        if timeframe == "1m":
            _adj = Adjustment.RAW
        else:
            _adj = _adjustment_enum_by_cfg.get(str(cfg.adjustment).lower(), Adjustment.RAW)
        rows: dict[str, list[dict]] = {sym: [] for sym in batch}
        page_token = None
        while True:
            limiter.acquire()
            req = StockBarsRequest(
                symbol_or_symbols=batch,
                timeframe=tf,
                start=start_dt,
                end=end_dt,
                feed=cfg.feed_enum,
                adjustment=_adj,
                page_token=page_token,
            )
            resp = with_retries(client.get_stock_bars, req, log=log)
            data = resp.data if hasattr(resp, "data") and isinstance(resp.data, dict) else {}
            for sym, bar_list in data.items():
                for bar in bar_list or []:
                    rows.setdefault(sym, []).append(_coerce_bar_row(sym, bar))
            page_token = getattr(resp, "next_page_token", None)
            if not page_token:
                break
        return rows

    return _fetch


# ---------------------------------------------------------------------------
# Quotes (SIP NBBO) — fetcher + per-minute sampling
# ---------------------------------------------------------------------------
# (batch_symbols, start_dt, end_dt) -> {symbol: [coerced quote-tick dict, ...]}
QuotesFetcher = Callable[[list, datetime, datetime], dict]


def _coerce_quote_row(symbol: str, q: Any) -> dict[str, Any]:
    """Normalise one Alpaca NBBO quote (SDK object OR raw dict) to the canonical
    lake quote schema: ``symbol, timestamp(UTC), bid, ask, bid_size, ask_size,
    conditions`` — exactly what ``MarketDataStore.quotes_at_or_before`` reads."""
    ts = getattr(q, "timestamp", None)
    if ts is None and isinstance(q, dict):
        ts = q.get("timestamp", q.get("t"))
    ts = pd.Timestamp(ts)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")

    def _a(name: str, alt: str, default: Any = 0.0) -> Any:
        if hasattr(q, name):
            return getattr(q, name)
        if isinstance(q, dict):
            return q.get(name, q.get(alt, default))
        return default

    cond = _a("conditions", "c", None)
    if isinstance(cond, (list, tuple)):
        cond = ",".join(str(x) for x in cond)
    return {
        "symbol": symbol,
        "timestamp": ts,
        "bid": float(_a("bid_price", "bp", 0.0) or 0.0),
        "ask": float(_a("ask_price", "ap", 0.0) or 0.0),
        "bid_size": float(_a("bid_size", "bs", 0.0) or 0.0),
        "ask_size": float(_a("ask_size", "as", 0.0) or 0.0),
        "conditions": "" if cond is None else str(cond),
    }


def make_alpaca_quotes_fetcher(
    cfg: BackfillConfig, limiter: RateLimiter, log: logging.Logger
) -> QuotesFetcher:
    """Return a :data:`QuotesFetcher` backed by the Alpaca historical quotes API.

    Mirrors :func:`make_alpaca_bars_fetcher` but uses ``StockQuotesRequest`` /
    ``get_stock_quotes`` and the configured ``feed`` (SIP for intended_realism).
    Returns the full NBBO tick stream per symbol for the window; the caller
    (:func:`fetch_quotes`) samples it down to one prevailing-NBBO snapshot per
    minute.
    """

    def _fetch(batch: list, start_dt: datetime, end_dt: datetime) -> dict:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockQuotesRequest

        client = StockHistoricalDataClient(api_key=cfg.api_key, secret_key=cfg.api_secret)
        rows: dict[str, list[dict]] = {sym: [] for sym in batch}
        page_token = None
        while True:
            limiter.acquire()
            req = StockQuotesRequest(
                symbol_or_symbols=batch,
                start=start_dt,
                end=end_dt,
                feed=cfg.feed_enum,
                page_token=page_token,
            )
            resp = with_retries(client.get_stock_quotes, req, log=log)
            data = resp.data if hasattr(resp, "data") and isinstance(resp.data, dict) else {}
            for sym, qlist in data.items():
                for q in qlist or []:
                    rows.setdefault(sym, []).append(_coerce_quote_row(sym, q))
            page_token = getattr(resp, "next_page_token", None)
            if not page_token:
                break
        return rows

    return _fetch


def _session_minute_boundaries_utc(session_date: date) -> pd.DatetimeIndex:
    """The regular-session (09:30–16:00 ET, DST-aware) minute boundaries as UTC
    timestamps — 09:30 … 15:59 (390 points), matching the minute-bar grid."""
    open_et = pd.Timestamp(f"{session_date} 09:30", tz="America/New_York")
    close_et = pd.Timestamp(f"{session_date} 16:00", tz="America/New_York")
    return pd.date_range(open_et, close_et, freq="1min", inclusive="left").tz_convert("UTC")


def _sample_session_nbbo(ticks: pd.DataFrame, session_date: date) -> pd.DataFrame:
    """Down-sample a session's NBBO tick stream to one prevailing quote per minute.

    For each regular-session minute boundary, keep the last quote at-or-before it
    (its ACTUAL tick timestamp is preserved so quote-age telemetry is real). This
    is exactly what the consumer's ``quotes_at_or_before(bar_ts)`` looks up and
    the cardinality the synthetic-SIP fixture uses (≤390 rows/symbol/session).
    """
    if ticks is None or ticks.empty:
        return ticks if ticks is not None else pd.DataFrame()
    ticks = ticks.sort_values("timestamp").reset_index(drop=True)
    boundaries = _session_minute_boundaries_utc(session_date)
    merged = pd.merge_asof(
        pd.DataFrame({"_boundary": boundaries}), ticks,
        left_on="_boundary", right_on="timestamp", direction="backward",
    )
    cols = ["symbol", "timestamp", "bid", "ask", "bid_size", "ask_size", "conditions"]
    out = merged.dropna(subset=["timestamp"])[[c for c in cols if c in merged.columns]]
    return out.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)


def _flush_accumulated_months(
    accumulated: dict[tuple, list[pd.DataFrame]],
    keys: Iterable[tuple],
    target_for: Callable[[str, int, int], Path],
    stats: dict,
) -> None:
    """Write + drop the given ``(symbol, year, month)`` keys from ``accumulated``.

    Identical merge/dedup/sort/write semantics to the original end-of-run write
    loop — only the TIMING changes: the minute-bar / quote stages call this to
    flush COMPLETED months as the date-sorted session loop crosses a month
    boundary, instead of buffering the whole range in memory and writing once at
    the end. Output parquet is byte-identical, but peak RAM stays bounded to the
    in-flight month(s) and already-written months survive an interruption (the
    next run's resume scan skips them).
    """
    for key in list(keys):
        frames = accumulated.pop(key, None)
        if not frames:
            continue
        sym, year, month = key
        new_df = pd.concat(frames, ignore_index=True)
        target = target_for(sym, year, month)
        if target.exists():
            try:
                existing = pd.read_parquet(target)
                if not existing.empty:
                    new_df = pd.concat([existing, new_df], ignore_index=True)
            except Exception:  # noqa: BLE001
                pass
        new_df["timestamp"] = pd.to_datetime(new_df["timestamp"], utc=True)
        new_df = (
            new_df.drop_duplicates(subset=["timestamp"], keep="last")
            .sort_values("timestamp").reset_index(drop=True)
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.Table.from_pandas(new_df, preserve_index=False), target)
        stats["months_written"] += 1


def fetch_quotes(
    cfg: BackfillConfig,
    targets: pd.DataFrame,
    log: logging.Logger,
    limiter: RateLimiter,
    *,
    quotes_fetcher: QuotesFetcher | None = None,
    batch_size: int | None = None,
) -> dict:
    """Fetch SIP NBBO quotes for every ``(session_date, symbol)`` in ``targets``,
    down-sampled to one prevailing quote per minute. Writes per-symbol/month
    Parquet at ``layout.quotes_path(feed=cfg.feed)``. Resume-aware: a pair whose
    session is already present in the symbol's month file is skipped.

    The (symbol, session) target set is the SAME as the minute-bar stage (the
    traded universe), so quotes exist exactly where bars do.
    """
    stats = {
        "pairs_requested": int(0 if targets is None else len(targets)),
        "pairs_written": 0, "pairs_skipped_resume": 0, "pairs_empty": 0,
        "batches_failed": 0, "months_written": 0,
    }
    if targets is None or len(targets) == 0:
        return stats
    fetcher = quotes_fetcher or make_alpaca_quotes_fetcher(cfg, limiter, log)
    bsize = int(batch_size or cfg.batch_size_symbols)

    tdf = targets.copy()
    tdf["session_date"] = pd.to_datetime(tdf["session_date"]).dt.date
    tdf["symbol"] = tdf["symbol"].astype(str)

    covered: dict[str, set] = {}
    if cfg.resume:
        for sym in tdf["symbol"].unique():
            sym_dir = _layout.quotes_symbol_dir(cfg.lake_root, sym, feed=cfg.feed)
            dates: set = set()
            if sym_dir.is_dir():
                for f in sym_dir.rglob("part.parquet"):
                    try:
                        ts = pd.to_datetime(
                            pd.read_parquet(f, columns=["timestamp"])["timestamp"], utc=True)
                        dates |= set(ts.dt.date.unique())
                    except Exception:  # noqa: BLE001
                        continue
            covered[sym] = dates

    pairs_by_session: dict[date, list[str]] = {}
    for sess, group in tdf.groupby("session_date"):
        syms = sorted(set(group["symbol"]))
        pending = [s for s in syms if not (cfg.resume and sess in covered.get(s, set()))]
        stats["pairs_skipped_resume"] += len(syms) - len(pending)
        if pending:
            pairs_by_session[sess] = pending

    # Incremental per-month flush (bounded RAM + resumable): sessions are
    # processed in ascending date order and every session's sampled NBBO falls
    # in its own UTC month, so once the loop crosses into a new month all earlier
    # months are complete and are written immediately. Byte-identical to a single
    # end-of-run flush; only the timing differs.
    def _quote_target(sym: str, year: int, month: int) -> Path:
        return _layout.quotes_path(cfg.lake_root, sym, year, month, feed=cfg.feed)

    accumulated: dict[tuple, list[pd.DataFrame]] = {}
    prev_month: tuple | None = None
    for session, symbols in sorted(pairs_by_session.items()):
        sess_month = (session.year, session.month)
        if prev_month is not None and sess_month != prev_month:
            done = [k for k in accumulated if (k[1], k[2]) < sess_month]
            _flush_accumulated_months(accumulated, done, _quote_target, stats)
        prev_month = sess_month
        start_dt = datetime.combine(session, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)
        for batch in _chunks(symbols, bsize):
            try:
                ticks_acc = fetcher(batch, start_dt, end_dt)
            except Exception as exc:  # noqa: BLE001
                log.exception("quote batch failed (session %s, %d symbols): %s",
                              session, len(batch), exc)
                stats["batches_failed"] += 1
                continue
            for sym in batch:
                sym_ticks = ticks_acc.get(sym) or []
                if not sym_ticks:
                    stats["pairs_empty"] += 1
                    continue
                ticks = pd.DataFrame(sym_ticks)
                ticks["timestamp"] = pd.to_datetime(ticks["timestamp"], utc=True)
                sampled = _sample_session_nbbo(ticks, session)
                if sampled is None or sampled.empty:
                    stats["pairs_empty"] += 1
                    continue
                for (year, month), grp in sampled.groupby(
                    [sampled["timestamp"].dt.year, sampled["timestamp"].dt.month]):
                    accumulated.setdefault((sym, int(year), int(month)), []).append(grp)
                stats["pairs_written"] += 1

    _flush_accumulated_months(accumulated, list(accumulated.keys()), _quote_target, stats)

    return stats


# ---------------------------------------------------------------------------
# Stage: assets
# ---------------------------------------------------------------------------
def fetch_assets(
    cfg: BackfillConfig,
    log: logging.Logger,
    *,
    assets_fetcher: Callable[[], Iterable[Any]] | None = None,
) -> tuple[str, pd.DataFrame]:
    """Fetch / filter active US equities and write an asset snapshot.

    Reuse: when ``cfg.resume`` and a recent snapshot exists (within
    ``asset_snapshot_max_age_days``), it is returned without a network call.
    """
    if cfg.resume:
        existing = sorted(_layout.assets_root(cfg.lake_root).glob("snapshot_id=*/assets.parquet"))
        if existing:
            latest = existing[-1]
            snap_str = latest.parent.name.replace("snapshot_id=", "")
            try:
                ts_str = snap_str.split("_", 1)[0]
                snap_ts = datetime.strptime(ts_str, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                age_days = (datetime.now(timezone.utc) - snap_ts).days
            except Exception:
                age_days = 10**9
            if age_days <= cfg.asset_snapshot_max_age_days:
                df = pd.read_parquet(latest)
                log.info("Stage 1: reusing snapshot %s (age %dd), %d symbols", snap_str, age_days, len(df))
                return snap_str, df

    snapshot_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ_alpaca_assets")
    raw_assets = (assets_fetcher or make_alpaca_assets_fetcher(cfg))()
    rows: list[dict[str, Any]] = []
    n_raw = n_tradable = n_exchange = n_kept = 0
    for a in raw_assets:
        n_raw += 1
        if not getattr(a, "tradable", False):
            continue
        n_tradable += 1
        exch = a.exchange.value if hasattr(a.exchange, "value") else str(a.exchange)
        if exch.startswith("AssetExchange."):
            exch = exch.split(".", 1)[1]
        if exch not in cfg.allowed_exchanges:
            continue
        n_exchange += 1
        name = getattr(a, "name", "") or ""
        if cfg.exclude_name_pattern.search(name):
            continue
        n_kept += 1
        status = getattr(a, "status", "")
        rows.append(
            {
                "snapshot_id": snapshot_id,
                "symbol": str(a.symbol),
                "name": name,
                "exchange": exch,
                "asset_class": "us_equity",
                "tradable": bool(getattr(a, "tradable", False)),
                "marginable": bool(getattr(a, "marginable", False)),
                "shortable": bool(getattr(a, "shortable", False)),
                "fractionable": bool(getattr(a, "fractionable", False)),
                "status": status.value if hasattr(status, "value") else str(status),
            }
        )
    df = pd.DataFrame(rows)
    log.info("asset funnel raw=%d → tradable=%d → exchange=%d → kept=%d", n_raw, n_tradable, n_exchange, n_kept)
    out_path = assets_file(cfg, snapshot_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), out_path)
    return snapshot_id, df


# ---------------------------------------------------------------------------
# Stage: daily bars
# ---------------------------------------------------------------------------
def fetch_daily_bars(
    cfg: BackfillConfig,
    assets_df: pd.DataFrame,
    log: logging.Logger,
    limiter: RateLimiter,
    *,
    bars_fetcher: BarsFetcher | None = None,
) -> dict:
    """Fetch daily bars per symbol with incremental tail planning."""
    fetcher = bars_fetcher or make_alpaca_bars_fetcher(cfg, limiter, log)
    symbols = sorted(assets_df["symbol"].astype(str).tolist()) if not assets_df.empty else []
    stats = {
        "symbols_requested": len(symbols),
        "symbols_written": 0,
        "symbols_extended": 0,
        "symbols_up_to_date": 0,
        "symbols_empty": 0,
        "symbols_failed": 0,
        "api_call_count_est": 0,
    }
    daily_root(cfg).mkdir(parents=True, exist_ok=True)

    plans = {
        sym: incremental_window(
            daily_file(cfg, sym), cfg.end_date, target_start_date=cfg.daily_fetch_start
        )
        for sym in symbols
    }
    stats["symbols_up_to_date"] = sum(1 for p in plans.values() if p.action == "up_to_date")

    buckets: dict[tuple, list[str]] = {}
    for sym, plan in plans.items():
        if plan.action == "up_to_date":
            continue
        if plan.action == "fetch_full":
            key = ("full", cfg.daily_fetch_start, cfg.end_date)
        else:
            key = ("tail", plan.start, plan.end)
        buckets.setdefault(key, []).append(sym)

    for (kind, fstart, fend), bucket_syms in buckets.items():
        start_dt = datetime.combine(fstart, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(fend, datetime.min.time()).replace(tzinfo=timezone.utc) + timedelta(days=1)
        for batch in _chunks(bucket_syms, cfg.batch_size_symbols):
            stats["api_call_count_est"] += 1
            try:
                rows_acc = fetcher(batch, "1d", start_dt, end_dt)
            except Exception as exc:  # noqa: BLE001
                log.exception("daily batch failed (%d symbols starting %s): %s", len(batch), batch[0], exc)
                stats["symbols_failed"] += len(batch)
                continue
            for sym in batch:
                sym_rows = rows_acc.get(sym) or []
                if not sym_rows:
                    stats["symbols_empty"] += 1
                    continue
                new_df = pd.DataFrame(sym_rows).sort_values("timestamp").reset_index(drop=True)
                new_df["session_date"] = pd.to_datetime(new_df["timestamp"], utc=True).dt.tz_convert(
                    "America/New_York"
                ).dt.date
                target = daily_file(cfg, sym)
                if kind == "tail" and target.exists():
                    try:
                        existing_df = pd.read_parquet(target)
                    except Exception:
                        existing_df = None
                    if existing_df is not None and not existing_df.empty:
                        combined = pd.concat([existing_df, new_df], ignore_index=True)
                        combined = combined.drop_duplicates(subset=["timestamp"], keep="last")
                        new_df = combined.sort_values("timestamp").reset_index(drop=True)
                    stats["symbols_extended"] += 1
                else:
                    stats["symbols_written"] += 1
                target.parent.mkdir(parents=True, exist_ok=True)
                pq.write_table(pa.Table.from_pandas(new_df, preserve_index=False), target)

    log.info(
        "Stage 2 done: %d new, %d extended, %d up-to-date, %d failed",
        stats["symbols_written"], stats["symbols_extended"], stats["symbols_up_to_date"], stats["symbols_failed"],
    )
    return stats


# ---------------------------------------------------------------------------
# Stage: minute bars (per symbol/month)
# ---------------------------------------------------------------------------
def fetch_minute_bars(
    cfg: BackfillConfig,
    targets: pd.DataFrame,
    log: logging.Logger,
    limiter: RateLimiter,
    *,
    bars_fetcher: BarsFetcher | None = None,
) -> dict:
    """Fetch 1-minute bars for every ``(session_date, symbol)`` pair in ``targets``.

    Writes per-symbol/month Parquet files. Resume-aware: a pair whose session
    is already present in the symbol's month file is skipped.
    """
    stats = {
        "pairs_requested": int(0 if targets is None else len(targets)),
        "pairs_written": 0,
        "pairs_skipped_resume": 0,
        "pairs_empty": 0,
        "batches_failed": 0,
        "months_written": 0,
    }
    if targets is None or len(targets) == 0:
        return stats
    fetcher = bars_fetcher or make_alpaca_bars_fetcher(cfg, limiter, log)

    tdf = targets.copy()
    tdf["session_date"] = pd.to_datetime(tdf["session_date"]).dt.date
    tdf["symbol"] = tdf["symbol"].astype(str)

    covered: dict[str, set] = {}
    if cfg.resume:
        for sym in tdf["symbol"].unique():
            sym_dir = _layout.minute_bars_symbol_dir(cfg.lake_root, sym, feed=cfg.feed, adjustment=MINUTE_ADJUSTMENT)
            dates: set = set()
            if sym_dir.is_dir():
                for f in sym_dir.rglob("part.parquet"):
                    try:
                        ts = pd.to_datetime(pd.read_parquet(f, columns=["timestamp"])["timestamp"], utc=True)
                        dates |= set(ts.dt.date.unique())
                    except Exception:
                        continue
            covered[sym] = dates

    pairs_by_session: dict[date, list[str]] = {}
    for sess, group in tdf.groupby("session_date"):
        syms = sorted(set(group["symbol"]))
        pending = [s for s in syms if not (cfg.resume and sess in covered.get(s, set()))]
        stats["pairs_skipped_resume"] += len(syms) - len(pending)
        if pending:
            pairs_by_session[sess] = pending

    # Incremental per-month flush (bounded RAM + resumable): sessions are
    # processed in ascending date order and every session's bars fall in its own
    # UTC month, so once the loop crosses into a new month all earlier months are
    # complete and written immediately. Byte-identical to a single end-of-run
    # flush; only the timing differs.
    def _minute_target(sym: str, year: int, month: int) -> Path:
        return minute_file(cfg, sym, year, month)

    accumulated: dict[tuple, list[pd.DataFrame]] = {}
    prev_month: tuple | None = None
    for session, symbols in sorted(pairs_by_session.items()):
        sess_month = (session.year, session.month)
        if prev_month is not None and sess_month != prev_month:
            done = [k for k in accumulated if (k[1], k[2]) < sess_month]
            _flush_accumulated_months(accumulated, done, _minute_target, stats)
        prev_month = sess_month
        start_dt = datetime.combine(session, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)
        for batch in _chunks(symbols, cfg.batch_size_symbols):
            try:
                rows_acc = fetcher(batch, "1m", start_dt, end_dt)
            except Exception as exc:  # noqa: BLE001
                log.exception("minute batch failed (session %s, %d symbols): %s", session, len(batch), exc)
                stats["batches_failed"] += 1
                continue
            for sym in batch:
                sym_rows = rows_acc.get(sym) or []
                if not sym_rows:
                    stats["pairs_empty"] += 1
                    continue
                df = pd.DataFrame(sym_rows)
                df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
                for (year, month), grp in df.groupby([df["timestamp"].dt.year, df["timestamp"].dt.month]):
                    accumulated.setdefault((sym, int(year), int(month)), []).append(grp)
                stats["pairs_written"] += 1

    _flush_accumulated_months(accumulated, list(accumulated.keys()), _minute_target, stats)

    return stats


# ---------------------------------------------------------------------------
# Stage: audit
# ---------------------------------------------------------------------------
def audit_daily_bars(cfg: BackfillConfig, log: logging.Logger) -> pd.DataFrame:
    """Per-symbol daily-bar quality audit. Every row shares one ``audit_run_id``."""
    try:
        import exchange_calendars as xcals

        cal = xcals.get_calendar("XNYS")
    except Exception:  # pragma: no cover - calendar optional
        cal = None
    audit_run_id = f"audit_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}_{cfg.feed}"
    root = daily_root(cfg)
    if not root.exists():
        return pd.DataFrame()
    rows = []
    for path in sorted(root.rglob("part.parquet")):
        try:
            df = pq.ParquetFile(str(path)).read().to_pandas()
        except Exception as exc:  # noqa: BLE001
            log.warning("failed to audit %s: %s", path, exc)
            continue
        if df.empty:
            continue
        symbol = path.parent.name.split("=", 1)[1] if "symbol=" in path.parent.name else str(df["symbol"].iloc[0])
        df["session_date"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date
        sessions_observed = df["session_date"].drop_duplicates().sort_values().tolist()
        if not sessions_observed:
            continue
        if cal is not None:
            try:
                expected_count = len(
                    cal.sessions_in_range(pd.Timestamp(sessions_observed[0]), pd.Timestamp(sessions_observed[-1]))
                )
            except Exception:
                expected_count = len(sessions_observed)
        else:
            expected_count = len(sessions_observed)
        duplicate_sessions = int(df["session_date"].duplicated().sum())
        ohlc_violations = int(
            ((df["high"] < df[["open", "close"]].max(axis=1)) | (df["low"] > df[["open", "close"]].min(axis=1))).sum()
        )
        zero_volume_sessions = int((df["volume"] <= 0).sum())
        sorted_df = df.sort_values("session_date")
        gap = sorted_df["open"] / sorted_df["close"].shift(1) - 1.0
        large_gap_flags = int((gap.abs() >= 0.40).fillna(False).sum())
        warnings: list[str] = []
        if duplicate_sessions:
            warnings.append("duplicate_sessions")
        if ohlc_violations:
            warnings.append("ohlc_violations")
        if expected_count and len(sessions_observed) < 0.8 * expected_count:
            warnings.append("low_session_coverage")
        if large_gap_flags:
            warnings.append("large_overnight_gap_suspected_split")
        rows.append(
            {
                "symbol": symbol,
                "feed": cfg.feed,
                "timeframe": "1d",
                "start": str(sessions_observed[0]),
                "end": str(sessions_observed[-1]),
                "expected_sessions": int(expected_count),
                "observed_sessions": int(len(sessions_observed)),
                "missing_sessions": max(0, int(expected_count) - int(len(sessions_observed))),
                "duplicate_sessions": duplicate_sessions,
                "ohlc_violations": ohlc_violations,
                "zero_volume_sessions": zero_volume_sessions,
                "large_gap_flags": large_gap_flags,
                "passed_research_audit": bool(duplicate_sessions == 0 and ohlc_violations == 0),
                "warnings": warnings,
                "audit_run_id": audit_run_id,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Ingestion metadata writers (replace the former Mongo writers)
# ---------------------------------------------------------------------------
def write_audits(cfg: BackfillConfig, audits_df: pd.DataFrame) -> Path | None:
    """Persist a daily-bar audit table under ``_ingestion/audits/``."""
    if audits_df is None or audits_df.empty:
        return None
    audit_run_id = str(audits_df["audit_run_id"].iloc[0]) if "audit_run_id" in audits_df.columns else "audit_unknown"
    target = _layout.ingestion_audit_path(cfg.lake_root, audit_run_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(audits_df, preserve_index=False), target)
    return target


def write_ingestion_run(cfg: BackfillConfig, run_record: dict) -> Path:
    """Persist an ingestion-run record as JSON under ``_ingestion/runs/``."""
    required = ("ingestion_run_id", "vendor", "feed", "created_at")
    missing = [k for k in required if k not in run_record]
    if missing:
        raise ValueError(f"ingestion run record missing fields: {missing}")
    target = _layout.ingestion_run_path(cfg.lake_root, run_record["ingestion_run_id"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(run_record, indent=2, default=str), encoding="utf-8")
    return target


def write_manifest_json(cfg: BackfillConfig, counts: dict, dataset_hashes: dict) -> Path:
    target = manifest_file(cfg)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feed": cfg.feed,
        "adjustment": cfg.adjustment,
        "start_date": cfg.start_date.isoformat(),
        "end_date": cfg.end_date.isoformat(),
        "daily_fetch_start": cfg.daily_fetch_start.isoformat(),
        "lake_root": str(cfg.lake_root),
        "counts": counts,
        "dataset_hashes": dataset_hashes,
    }
    target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Smoke test + estimator
# ---------------------------------------------------------------------------
def run_smoke_test(cfg: BackfillConfig, log: logging.Logger) -> dict:
    """Fetch account info + a tiny SPY slice on ``cfg.feed`` (live; needs creds)."""
    out: dict[str, Any] = {"ok": False, "account_no": None, "bars_returned": 0, "feed_403": False, "error": None}
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        from alpaca.trading.client import TradingClient

        trading = TradingClient(api_key=cfg.api_key, secret_key=cfg.api_secret, paper=cfg.paper)
        acct = trading.get_account()
        out["account_no"] = getattr(acct, "account_number", None) or getattr(acct, "id", None)
        data = StockHistoricalDataClient(api_key=cfg.api_key, secret_key=cfg.api_secret)
        try:
            req = StockBarsRequest(
                symbol_or_symbols=["SPY"],
                timeframe=TimeFrame.Day,
                start=datetime.now(timezone.utc) - timedelta(days=15),
                end=datetime.now(timezone.utc) - timedelta(minutes=20),
                feed=cfg.feed_enum,
                limit=5,
            )
            resp = data.get_stock_bars(req)
            bars = resp.data.get("SPY") if hasattr(resp, "data") and isinstance(resp.data, dict) else []
            out["bars_returned"] = len(bars or [])
            out["ok"] = True
        except Exception as exc:  # noqa: BLE001
            if _status_code_of(exc) == 403:
                out["feed_403"] = True
                out["error"] = f'403 on feed={cfg.feed}; SIP likely needs a subscription. Retry with FEED="iex".'
            else:
                out["error"] = str(exc)
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)
        log.exception("smoke test failed")
    return out


def estimate_storage_and_time(cfg: BackfillConfig) -> dict:
    """Rough projection of disk + API calls + wall clock."""
    import exchange_calendars as xcals

    cal = xcals.get_calendar("XNYS")
    n_warmup = len(cal.sessions_in_range(pd.Timestamp(cfg.daily_fetch_start), pd.Timestamp(cfg.end_date)))
    n_window = len(cal.sessions_in_range(pd.Timestamp(cfg.start_date), pd.Timestamp(cfg.end_date)))
    n_universe = 7_500
    daily_gb = n_universe * 6 / 1024 / 1024
    minute_files = n_window * 80
    minute_gb = minute_files * 50 / 1024 / 1024
    api_calls = (n_universe // cfg.batch_size_symbols + 1) + n_window * (80 // cfg.batch_size_symbols + 1)
    return {
        "n_sessions": int(n_window),
        "n_sessions_with_warmup": int(n_warmup),
        "n_universe_est": int(n_universe),
        "daily_gb": round(daily_gb, 3),
        "minute_gb": round(minute_gb, 3),
        "total_gb": round(daily_gb + minute_gb, 3),
        "api_calls": int(api_calls),
        "wall_clock_hours": round((api_calls / cfg.rate_limit_rpm) / 60.0, 2),
    }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def run_backfill(
    cfg: BackfillConfig,
    log: logging.Logger | None = None,
    *,
    assets_fetcher: Callable[[], Iterable[Any]] | None = None,
    bars_fetcher: BarsFetcher | None = None,
    minute_targets: pd.DataFrame | None = None,
) -> dict:
    """Run the backfill: assets → daily bars → (minute bars) → audit → manifest.

    The minute stage runs only when ``minute_targets`` (a ``session_date`` /
    ``symbol`` table) is supplied — the shared backfill does not compute a
    strategy universe.
    """
    log = log or _default_logger()
    limiter = RateLimiter(cfg.rate_limit_rpm)
    result: dict[str, Any] = {}

    snapshot_id, assets_df = fetch_assets(cfg, log, assets_fetcher=assets_fetcher)
    result["snapshot_id"] = snapshot_id
    result["assets_count"] = int(len(assets_df))

    result["daily"] = fetch_daily_bars(cfg, assets_df, log, limiter, bars_fetcher=bars_fetcher)
    if minute_targets is not None:
        result["minute"] = fetch_minute_bars(cfg, minute_targets, log, limiter, bars_fetcher=bars_fetcher)

    audits = audit_daily_bars(cfg, log)
    if not audits.empty:
        write_audits(cfg, audits)
    result["audit_rows"] = int(len(audits))

    counts = {
        "assets": int(len(assets_df)),
        "daily": result["daily"],
        "minute": result.get("minute", {}),
        "audit_rows": int(len(audits)),
    }
    write_manifest_json(cfg, counts, {"lake": compute_dataset_hash(cfg.lake_root)})

    run_id = f"ingest_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}_{cfg.feed}"
    write_ingestion_run(
        cfg,
        {
            "ingestion_run_id": run_id,
            "vendor": "alpaca",
            "feed": cfg.feed,
            "adjustment": cfg.adjustment,
            "start": cfg.start_date.isoformat(),
            "end": cfg.end_date.isoformat(),
            "counts": counts,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    result["ingestion_run_id"] = run_id
    result["manifest"] = str(manifest_file(cfg))
    return result
