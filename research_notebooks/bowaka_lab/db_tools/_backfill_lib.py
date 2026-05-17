"""Standalone Bowaka backfill helper library.

This module is intentionally self-contained: it does NOT import from
``bowaka_lab.*`` modules so the backfill notebook can run before bowaka_lab
Phase 2 ships. Pure-Python helpers; alpaca-py is imported lazily so the unit
tests don't require API credentials.

Section references in this file point to ``bowaka_lab_project_handoff_report.md``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field, fields
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Optional, Sequence

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Substring patterns that identify leveraged / inverse / fund products
#: (per ``[Report §11]`` + §27.1). Used by the default name-pattern filter.
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

#: Set of HTTP-style status codes that should fail fast (no retry).
NON_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({400, 401, 403, 404, 422})


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BackfillConfig:
    """Backfill run configuration. Fields mirror the notebook parameter cell."""

    api_key: str
    api_secret: str
    paper: bool
    feed: str
    start_date: date
    end_date: date
    out_dir: Path
    mongo_uri: str | None
    mongo_database: str = "bowaka_lab"
    write_to_mongo: bool = True
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
    #: Reuse an existing Stage-1 asset snapshot if its embedded timestamp is
    #: within this many days. Defaults to 7 = weekly refresh.
    asset_snapshot_max_age_days: int = 7
    #: ``"latest"`` upserts the daily-bar audit row by ``(symbol, feed,
    #: timeframe)`` so each weekly run overwrites the previous audit;
    #: ``"append"`` inserts one row per ``audit_run_id`` so history accumulates.
    audit_history_mode: Literal["latest", "append"] = "latest"

    @property
    def daily_fetch_start(self) -> date:
        """Start fetching daily bars this many days before ``start_date`` so the
        ADV rolling window has enough warmup data to be non-NaN on ``start_date``.
        """
        pad = int(self.adv_window_days * 1.5) + 7
        return self.start_date - timedelta(days=pad)

    @property
    def feed_enum(self) -> Any:
        """Lazy: returns ``alpaca.data.enums.DataFeed`` member matching ``feed``."""
        from alpaca.data.enums import DataFeed

        return DataFeed[self.feed.upper()]


# ---------------------------------------------------------------------------
# Incremental tail planning
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IncrementalPlan:
    """Per-symbol decision returned by :func:`incremental_window`.

    ``action`` ∈ {``"fetch_full"``, ``"up_to_date"``, ``"fetch_tail"``}.
    ``start`` / ``end`` are populated only for ``"fetch_tail"``.
    """

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
) -> IncrementalPlan:
    """Decide how to update a per-symbol daily-bar Parquet file.

    Reads ``symbol_file`` if present, derives the latest session_date covered
    (interpreting timestamps in America/New_York), and returns one of:

    - ``IncrementalPlan(action="fetch_full")`` — file missing, unreadable,
      empty, or has no ``timestamp`` column.
    - ``IncrementalPlan(action="up_to_date", existing_max_session=D)`` — file's
      max session_date is ≥ ``target_end_date``.
    - ``IncrementalPlan(action="fetch_tail", start=next_xnys_session_after_D,
      end=target_end_date, existing_max_session=D)`` — file's max session_date
      is < ``target_end_date``. ``start`` is the next XNYS trading session
      after the existing max, never a calendar day. ADV warmup padding is the
      caller's responsibility; this helper does not consult ``adv_window_days``.
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
    except Exception:
        return IncrementalPlan(action="fetch_full")

    if existing_max >= target_end_date:
        return IncrementalPlan(action="up_to_date", existing_max_session=existing_max)

    cal = calendar if calendar is not None else _get_xnys_calendar()
    next_session_ts = cal.next_session(pd.Timestamp(existing_max))
    next_session_date = pd.Timestamp(next_session_ts).date()
    return IncrementalPlan(
        action="fetch_tail",
        start=next_session_date,
        end=target_end_date,
        existing_max_session=existing_max,
    )


# ---------------------------------------------------------------------------
# Env / dotenv
# ---------------------------------------------------------------------------


def find_and_load_dotenv() -> Path | None:
    """Walk up from CWD until we find an ``.env``. Prefer
    ``research_notebooks/bowaka_lab/.env`` if a sibling exists, otherwise pick
    the first .env on the parent chain. Returns the loaded path or None.
    """
    here = Path.cwd().resolve()
    candidates: list[Path] = []
    for ancestor in [here, *here.parents]:
        bow_env = ancestor / "research_notebooks" / "bowaka_lab" / ".env"
        if bow_env.is_file():
            candidates.append(bow_env)
            break
        if (ancestor / ".env").is_file():
            candidates.append(ancestor / ".env")
    if not candidates:
        return None
    target = candidates[0]
    _load_dotenv_file(target)
    return target


def _load_dotenv_file(path: Path) -> None:
    """Minimal .env parser; does not require python-dotenv at import time."""
    try:
        from dotenv import load_dotenv

        load_dotenv(path, override=False)
        return
    except Exception:
        pass
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("\"").strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def resolve_env() -> dict[str, Any]:
    """Read ``ALPACA_*`` + ``MONGO_*`` from os.environ. Returns a dict.

    Raises ``RuntimeError`` with a clear message if a required value is missing.
    """
    missing: list[str] = []
    out: dict[str, Any] = {}
    for key in ("ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY", "MONGO_URI"):
        v = os.environ.get(key)
        if not v:
            missing.append(key)
        out[key] = v
    if missing:
        raise RuntimeError(f"Missing required env vars: {missing}. Set them in .env or the shell.")
    out["MONGO_DATABASE"] = os.environ.get("MONGO_DATABASE", "bowaka_lab")
    paper_raw = os.environ.get("ALPACA_PAPER", "true").lower()
    out["ALPACA_PAPER"] = paper_raw not in ("false", "0", "no")
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
    """Call ``fn`` with retries on transient errors.

    Does NOT retry on HTTP 400/401/403/404/422 — those fail fast so the caller
    can react (e.g. switch feed from sip → iex on 403).
    """
    attempt = 1
    while True:
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            code = _status_code_of(exc)
            if code in NON_RETRYABLE_STATUS_CODES:
                raise
            if attempt >= max_attempts:
                raise
            sleep_for = base_delay * (2 ** (attempt - 1))
            if log is not None:
                log.warning(
                    "transient error on attempt %d/%d: %s; sleeping %.1fs",
                    attempt,
                    max_attempts,
                    exc,
                    sleep_for,
                )
            time.sleep(sleep_for)
            attempt += 1


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def assets_dir(cfg: BackfillConfig) -> Path:
    return cfg.out_dir / "parquet" / "assets" / "vendor=alpaca"


def assets_file(cfg: BackfillConfig, snapshot_id: str) -> Path:
    return assets_dir(cfg) / f"snapshot_id={snapshot_id}" / "assets.parquet"


def daily_root(cfg: BackfillConfig) -> Path:
    return cfg.out_dir / "parquet" / "bars" / "vendor=alpaca" / f"feed={cfg.feed}" / "timeframe=1d" / f"adjustment={cfg.adjustment}"


def daily_file(cfg: BackfillConfig, symbol: str) -> Path:
    return daily_root(cfg) / f"symbol={symbol}" / "part.parquet"


def minute_root(cfg: BackfillConfig) -> Path:
    return cfg.out_dir / "parquet" / "bars" / "vendor=alpaca" / f"feed={cfg.feed}" / "timeframe=1m" / f"adjustment={cfg.adjustment}"


def minute_file(cfg: BackfillConfig, session_date: date, symbol: str) -> Path:
    return minute_root(cfg) / f"session_date={session_date.isoformat()}" / f"symbol={symbol}.parquet"


def scope_file(cfg: BackfillConfig) -> Path:
    return cfg.out_dir / "scope" / f"feed={cfg.feed}" / f"start={cfg.start_date.isoformat()}_end={cfg.end_date.isoformat()}" / "scope3.parquet"


def manifest_file(cfg: BackfillConfig) -> Path:
    return cfg.out_dir / "manifest.json"


# ---------------------------------------------------------------------------
# Dataset hashing
# ---------------------------------------------------------------------------


def compute_dataset_hash(root: Path) -> str:
    """SHA-256 of a sorted (relative_path, size) list. Cheap stand-in for the
    bowaka_lab.data.dataset_hash that ships in Phase 1 of the main implementation.
    """
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
# Alpaca stages
# ---------------------------------------------------------------------------


def run_smoke_test(cfg: BackfillConfig, log: logging.Logger) -> dict:
    """Fetch account info + a tiny SPY bar slice on cfg.feed."""
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
            code = _status_code_of(exc)
            if code == 403:
                out["feed_403"] = True
                out["error"] = (
                    f"403 on feed={cfg.feed}. Most likely SIP requires a subscription. "
                    f'Retry the smoke test with FEED = "iex".'
                )
            else:
                out["error"] = str(exc)
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)
        log.exception("smoke test failed")
    return out


def fetch_assets(cfg: BackfillConfig, log: logging.Logger) -> tuple[str, pd.DataFrame]:
    """Fetch active/tradable Alpaca US equities; filter; write parquet.

    Reuse policy: when ``cfg.resume`` is True and at least one prior snapshot
    exists, the most recent snapshot is reused if its embedded UTC timestamp
    is at most ``cfg.asset_snapshot_max_age_days`` days old. Otherwise the
    Alpaca asset endpoint is hit and a new snapshot is written.
    """
    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import AssetClass, AssetStatus
    from alpaca.trading.requests import GetAssetsRequest

    if cfg.resume:
        existing = sorted(assets_dir(cfg).glob("snapshot_id=*/assets.parquet"))
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
                log.info(
                    "Stage 1: reusing snapshot %s (age %dd <= max_age %dd), %d symbols",
                    snap_str,
                    age_days,
                    cfg.asset_snapshot_max_age_days,
                    len(df),
                )
                return snap_str, df
            log.info(
                "Stage 1: snapshot %s is %dd old (> %dd max_age); refreshing",
                snap_str,
                age_days,
                cfg.asset_snapshot_max_age_days,
            )

    snapshot_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ_alpaca_assets")
    out_path = assets_file(cfg, snapshot_id)
    trading = TradingClient(api_key=cfg.api_key, secret_key=cfg.api_secret, paper=cfg.paper)
    req = GetAssetsRequest(asset_class=AssetClass.US_EQUITY, status=AssetStatus.ACTIVE)
    raw_assets = trading.get_all_assets(req)
    rows: list[dict[str, Any]] = []
    n_raw = 0
    n_tradable = 0
    n_exchange = 0
    n_after_name = 0
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
        n_after_name += 1
        status = getattr(a, "status", "")
        status_str = status.value if hasattr(status, "value") else str(status)
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
                "status": status_str,
            }
        )
    df = pd.DataFrame(rows)
    log.info(
        "asset funnel raw=%d → tradable=%d → exchange=%d → name=%d (kept)",
        n_raw,
        n_tradable,
        n_exchange,
        n_after_name,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), out_path)
    return snapshot_id, df


def _coerce_bar_row(symbol: str, row: Any) -> dict[str, Any]:
    ts = getattr(row, "timestamp", None) or (row.get("t") if isinstance(row, dict) else None)
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
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


def fetch_daily_bars(
    cfg: BackfillConfig,
    assets_df: pd.DataFrame,
    log: logging.Logger,
    limiter: RateLimiter,
) -> dict:
    """Fetch daily bars per-symbol with multi-symbol batching.

    Per-symbol planning via :func:`incremental_window` (see ``[Report §10]`` for
    calendar awareness and ``[Report §11.4]`` for the no-lookahead invariant).
    Three outcomes per symbol:

    - ``fetch_full`` — no existing file; fetch the full window from
      ``cfg.daily_fetch_start`` (ADV warmup-padded) through ``cfg.end_date``.
    - ``fetch_tail`` — partial file on disk; fetch only sessions strictly
      after the existing max session, then concatenate, deduplicate by
      ``timestamp``, sort, and rewrite.
    - ``up_to_date`` — existing file already covers through ``cfg.end_date``.
      No API call.

    Returns a stats dict with ``symbols_requested``, ``symbols_written``
    (new files), ``symbols_extended`` (existing files extended in place),
    ``symbols_up_to_date``, ``symbols_empty``, ``symbols_failed``, and
    ``api_call_count_est``.
    """
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    data_client = StockHistoricalDataClient(api_key=cfg.api_key, secret_key=cfg.api_secret)
    symbols = sorted(assets_df["symbol"].astype(str).tolist())
    stats = {
        "symbols_requested": len(symbols),
        "symbols_written": 0,
        "symbols_extended": 0,
        "symbols_up_to_date": 0,
        "symbols_empty": 0,
        "symbols_failed": 0,
        "api_call_count_est": 0,
    }
    root = daily_root(cfg)
    root.mkdir(parents=True, exist_ok=True)

    log.info(
        "Stage 2: planning daily-bar fetch for %d symbols, target end_date=%s, feed=%s",
        len(symbols),
        cfg.end_date,
        cfg.feed,
    )
    plans: dict[str, IncrementalPlan] = {}
    for sym in symbols:
        plans[sym] = incremental_window(daily_file(cfg, sym), cfg.end_date)
    n_full = sum(1 for p in plans.values() if p.action == "fetch_full")
    n_tail = sum(1 for p in plans.values() if p.action == "fetch_tail")
    n_uptodate = sum(1 for p in plans.values() if p.action == "up_to_date")
    log.info("  Plan: %d full-fetch, %d tail-extend, %d up-to-date", n_full, n_tail, n_uptodate)
    stats["symbols_up_to_date"] = n_uptodate

    # Bucket by (kind, fetch_start, fetch_end). Each bucket maps to one
    # multi-symbol API window so symbols sharing the same gap can be combined.
    buckets: dict[tuple, list[str]] = {}
    for sym, plan in plans.items():
        if plan.action == "up_to_date":
            continue
        if plan.action == "fetch_full":
            key = ("full", cfg.daily_fetch_start, cfg.end_date)
        else:
            key = ("tail", plan.start, plan.end)
        buckets.setdefault(key, []).append(sym)

    batches_done = 0
    failed: list[str] = []
    for (kind, fstart, fend), bucket_syms in buckets.items():
        log.info("  Bucket: kind=%s window=%s->%s symbols=%d", kind, fstart, fend, len(bucket_syms))
        start_dt = datetime.combine(fstart, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(fend, datetime.min.time()).replace(tzinfo=timezone.utc) + timedelta(days=1)

        for batch in _chunks(bucket_syms, cfg.batch_size_symbols):
            limiter.acquire()
            stats["api_call_count_est"] += 1
            try:
                req = StockBarsRequest(
                    symbol_or_symbols=batch,
                    timeframe=TimeFrame.Day,
                    start=start_dt,
                    end=end_dt,
                    feed=cfg.feed_enum,
                )
                resp = with_retries(data_client.get_stock_bars, req, log=log)
            except Exception as exc:  # noqa: BLE001
                log.exception(
                    "daily batch failed (%d symbols starting %s): %s", len(batch), batch[0], exc
                )
                stats["symbols_failed"] += len(batch)
                failed.extend(batch)
                batches_done += 1
                continue

            page_token = getattr(resp, "next_page_token", None)
            bars_by_symbol = resp.data if hasattr(resp, "data") and isinstance(resp.data, dict) else {}
            rows_acc: dict[str, list[dict]] = {sym: [] for sym in batch}
            for sym, bar_list in bars_by_symbol.items():
                for bar in bar_list:
                    rows_acc.setdefault(sym, []).append(_coerce_bar_row(sym, bar))
            while page_token:
                limiter.acquire()
                stats["api_call_count_est"] += 1
                req = StockBarsRequest(
                    symbol_or_symbols=batch,
                    timeframe=TimeFrame.Day,
                    start=start_dt,
                    end=end_dt,
                    feed=cfg.feed_enum,
                    page_token=page_token,
                )
                resp = with_retries(data_client.get_stock_bars, req, log=log)
                page_token = getattr(resp, "next_page_token", None)
                bars_by_symbol = resp.data if hasattr(resp, "data") and isinstance(resp.data, dict) else {}
                for sym, bar_list in bars_by_symbol.items():
                    for bar in bar_list:
                        rows_acc.setdefault(sym, []).append(_coerce_bar_row(sym, bar))

            for sym, sym_rows in rows_acc.items():
                if not sym_rows:
                    stats["symbols_empty"] += 1
                    continue
                new_df = pd.DataFrame(sym_rows).sort_values("timestamp").reset_index(drop=True)
                new_df["session_date"] = new_df["timestamp"].dt.tz_convert("America/New_York").dt.date
                target = daily_file(cfg, sym)
                if kind == "tail" and target.exists():
                    try:
                        existing_df = pd.read_parquet(target)
                    except Exception:
                        existing_df = None
                    if existing_df is not None and not existing_df.empty:
                        combined = pd.concat([existing_df, new_df], ignore_index=True)
                        combined = combined.drop_duplicates(subset=["timestamp"], keep="last")
                        combined = combined.sort_values("timestamp").reset_index(drop=True)
                    else:
                        combined = new_df
                    target.parent.mkdir(parents=True, exist_ok=True)
                    pq.write_table(pa.Table.from_pandas(combined, preserve_index=False), target)
                    stats["symbols_extended"] += 1
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    pq.write_table(pa.Table.from_pandas(new_df, preserve_index=False), target)
                    stats["symbols_written"] += 1

            batches_done += 1
            if batches_done % 5 == 0:
                log.info("  Stage 2 progress: %d batches done", batches_done)

    log.info(
        "Stage 2 done: %d new files, %d extended, %d up-to-date, %d failed",
        stats["symbols_written"],
        stats["symbols_extended"],
        stats["symbols_up_to_date"],
        stats["symbols_failed"],
    )
    return stats


def compute_scope_3(cfg: BackfillConfig, log: logging.Logger) -> pd.DataFrame:
    """Materialize the universe-gate-passers per session with no-lookahead ADV.

    For each session_date D and symbol S:

    - ``close`` on D is within ``[price_min, price_max]``
    - ``ADV(D)`` = mean of dollar_volume over the prior ``adv_window_days``
      sessions, EXCLUDING D itself (``shift(1).rolling(N).mean()``) ≥ ``adv_min``
    - D ∈ [start_date, end_date]

    Writes scope3.parquet under ``cfg.out_dir/scope/...``.
    """
    root = daily_root(cfg)
    if not root.exists():
        log.warning("compute_scope_3: no daily root at %s", root)
        return pd.DataFrame(columns=["session_date", "symbol"])
    paths = list(root.rglob("part.parquet"))
    log.info("compute_scope_3: scanning %d daily files", len(paths))
    rows: list[pd.DataFrame] = []
    for path in paths:
        try:
            df = pq.ParquetFile(str(path)).read().to_pandas()
        except Exception as exc:  # noqa: BLE001
            log.warning("failed to read %s: %s", path, exc)
            continue
        if df.empty:
            continue
        if "symbol" not in df.columns:
            # Fall back: derive symbol from path.
            for part in path.parts:
                if part.startswith("symbol="):
                    df["symbol"] = part.split("=", 1)[1]
                    break
        rows.append(df[["symbol", "timestamp", "close", "volume"]])
    if not rows:
        return pd.DataFrame(columns=["session_date", "symbol"])
    df = pd.concat(rows, ignore_index=True)
    df["session_date"] = pd.to_datetime(df["timestamp"]).dt.tz_convert("America/New_York").dt.date
    df = df.sort_values(["symbol", "session_date"]).reset_index(drop=True)
    df["dollar_volume"] = df["close"] * df["volume"]
    df["adv"] = (
        df.groupby("symbol", sort=False)["dollar_volume"]
        .transform(lambda s: s.shift(1).rolling(cfg.adv_window_days).mean())
    )
    mask = (
        df["adv"].notna()
        & (df["close"].between(cfg.price_min, cfg.price_max, inclusive="both"))
        & (df["adv"] >= cfg.adv_min)
        & (df["session_date"] >= cfg.start_date)
        & (df["session_date"] <= cfg.end_date)
    )
    scope = df.loc[mask, ["session_date", "symbol"]].reset_index(drop=True)
    target = scope_file(cfg)
    target.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(scope, preserve_index=False), target)
    return scope


def fetch_minute_bars(
    cfg: BackfillConfig,
    scope_df: pd.DataFrame,
    log: logging.Logger,
    limiter: RateLimiter,
) -> dict:
    """Fetch 1-minute bars for every (session, symbol) pair in scope_df.

    Writes one Parquet per pair under ``minute_root(cfg)/session_date=.../symbol=X.parquet``.
    Resume-aware: existing files are skipped.
    """
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    data_client = StockHistoricalDataClient(api_key=cfg.api_key, secret_key=cfg.api_secret)
    stats = {
        "pairs_requested": int(scope_df.shape[0]),
        "pairs_written": 0,
        "pairs_skipped_resume": 0,
        "pairs_empty": 0,
        "batches_failed": 0,
    }
    if scope_df.empty:
        return stats

    pairs_by_session: dict[date, list[str]] = {}
    for sess, group in scope_df.groupby("session_date"):
        pairs_by_session[sess] = sorted(group["symbol"].astype(str).unique().tolist())

    minute_root_path = minute_root(cfg)
    minute_root_path.mkdir(parents=True, exist_ok=True)

    sessions_done = 0
    for session, symbols in sorted(pairs_by_session.items()):
        pending: list[str] = []
        for sym in symbols:
            tgt = minute_file(cfg, session, sym)
            if cfg.resume and tgt.exists():
                stats["pairs_skipped_resume"] += 1
                continue
            pending.append(sym)

        start_dt = datetime.combine(session, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)
        for batch_start in range(0, len(pending), cfg.batch_size_symbols):
            batch = pending[batch_start : batch_start + cfg.batch_size_symbols]
            limiter.acquire()
            try:
                req = StockBarsRequest(
                    symbol_or_symbols=batch,
                    timeframe=TimeFrame.Minute,
                    start=start_dt,
                    end=end_dt,
                    feed=cfg.feed_enum,
                )
                resp = with_retries(data_client.get_stock_bars, req, log=log)
            except Exception as exc:  # noqa: BLE001
                log.exception("minute batch failed (session %s, %d symbols): %s", session, len(batch), exc)
                stats["batches_failed"] += 1
                continue
            page_token = getattr(resp, "next_page_token", None)
            bars_by_symbol = resp.data if hasattr(resp, "data") and isinstance(resp.data, dict) else {}
            rows_acc: dict[str, list[dict]] = {sym: [] for sym in batch}
            for sym, bar_list in bars_by_symbol.items():
                for bar in bar_list:
                    rows_acc.setdefault(sym, []).append(_coerce_bar_row(sym, bar))
            while page_token:
                limiter.acquire()
                req = StockBarsRequest(
                    symbol_or_symbols=batch,
                    timeframe=TimeFrame.Minute,
                    start=start_dt,
                    end=end_dt,
                    feed=cfg.feed_enum,
                    page_token=page_token,
                )
                resp = with_retries(data_client.get_stock_bars, req, log=log)
                page_token = getattr(resp, "next_page_token", None)
                bars_by_symbol = resp.data if hasattr(resp, "data") and isinstance(resp.data, dict) else {}
                for sym, bar_list in bars_by_symbol.items():
                    for bar in bar_list:
                        rows_acc.setdefault(sym, []).append(_coerce_bar_row(sym, bar))
            for sym, sym_rows in rows_acc.items():
                if not sym_rows:
                    stats["pairs_empty"] += 1
                    continue
                df = pd.DataFrame(sym_rows).sort_values("timestamp").reset_index(drop=True)
                tgt = minute_file(cfg, session, sym)
                tgt.parent.mkdir(parents=True, exist_ok=True)
                pq.write_table(pa.Table.from_pandas(df, preserve_index=False), tgt)
                stats["pairs_written"] += 1
        sessions_done += 1
        if sessions_done % 10 == 0:
            log.info("minute backfill: %d/%d sessions done", sessions_done, len(pairs_by_session))
    return stats


def audit_daily_bars(cfg: BackfillConfig, log: logging.Logger) -> pd.DataFrame:
    """Per-symbol daily-bar audit per ``[Report §16.1]``.

    Every row in the returned DataFrame carries an identical ``audit_run_id``
    derived from the current UTC timestamp + feed. The ID propagates through
    :func:`write_daily_audits_to_mongo` so a row's history is recoverable
    when ``cfg.audit_history_mode == "append"``.
    """
    import exchange_calendars as xcals

    cal = xcals.get_calendar("XNYS")
    audit_run_id = f"audit_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}_{cfg.feed}"
    root = daily_root(cfg)
    if not root.exists():
        return pd.DataFrame()
    paths = sorted(root.rglob("part.parquet"))
    rows = []
    for path in paths:
        try:
            df = pq.ParquetFile(str(path)).read().to_pandas()
        except Exception as exc:  # noqa: BLE001
            log.warning("failed to audit %s: %s", path, exc)
            continue
        if df.empty:
            continue
        symbol = path.parent.name.split("=", 1)[1] if "symbol=" in path.parent.name else df["symbol"].iloc[0]
        df["session_date"] = pd.to_datetime(df["timestamp"]).dt.tz_convert("America/New_York").dt.date
        sessions_observed = df["session_date"].drop_duplicates().sort_values().tolist()
        if not sessions_observed:
            continue
        try:
            sessions_expected = cal.sessions_in_range(
                pd.Timestamp(sessions_observed[0]),
                pd.Timestamp(sessions_observed[-1]),
            )
            expected_count = len(sessions_expected)
        except Exception:
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
        passed = duplicate_sessions == 0 and ohlc_violations == 0
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
                "passed_research_audit": bool(passed),
                "warnings": warnings,
                "audit_run_id": audit_run_id,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Mongo
# ---------------------------------------------------------------------------


def get_mongo_client(mongo_uri: str):
    from pymongo import MongoClient

    return MongoClient(mongo_uri, serverSelectionTimeoutMS=5_000)


SECTION_8_6_INDEXES: dict[str, list[dict]] = {
    "bowaka_asset_snapshots": [{"keys": [("snapshot_id", 1)], "unique": True}],
    "bowaka_assets": [{"keys": [("snapshot_id", 1), ("symbol", 1)], "unique": True}],
    "bowaka_data_ingestion_runs": [{"keys": [("ingestion_run_id", 1)], "unique": True}],
    "bowaka_daily_bar_audits": [
        # Lookup index used by audit_history_mode == "latest". Not unique —
        # the latest-mode writer enforces single-row-per-symbol semantics via
        # ``update_one(..., upsert=True)``. Making this index unique would
        # forbid the append-mode coexistence below.
        {"keys": [("symbol", 1), ("feed", 1), ("timeframe", 1)], "unique": False},
        # Used by audit_history_mode == "append" — one row per (symbol, feed,
        # timeframe, audit_run_id) so historical audits accumulate.
        {
            "keys": [("symbol", 1), ("feed", 1), ("timeframe", 1), ("audit_run_id", 1)],
            "unique": True,
        },
    ],
}


def apply_indexes(db) -> None:
    """Apply ``[Report §8.6]`` indexes idempotently.

    Both audit-history index variants are created so writers in either
    ``audit_history_mode`` can rely on the appropriate uniqueness constraint
    without re-running ``apply_indexes`` after a mode switch.

    Self-healing for upgrades: if the collection already has an index with
    the same key but a *different* options spec (e.g. ``unique`` flipped, as
    happens when a prior schema gets upgraded), the conflicting index is
    dropped by its server-assigned name and recreated with the current
    options. This surfaces as ``OperationFailure(code=86, IndexKeySpecsConflict)``
    from Mongo.
    """
    from pymongo import ASCENDING
    from pymongo.errors import OperationFailure

    for coll_name, idx_specs in SECTION_8_6_INDEXES.items():
        coll = db[coll_name]
        for idx in idx_specs:
            keys = [(field, ASCENDING if v > 0 else -1) for field, v in idx["keys"]]
            unique = idx.get("unique", False)
            try:
                coll.create_index(keys, unique=unique)
            except OperationFailure as exc:
                if getattr(exc, "code", None) != 86:
                    raise
                # IndexKeySpecsConflict: same key, different options. Drop
                # the existing index by name and recreate. Index names are
                # auto-generated as "<field>_<dir>_<field>_<dir>...".
                index_name = "_".join(f"{field}_{direction}" for field, direction in keys)
                coll.drop_index(index_name)
                coll.create_index(keys, unique=unique)


def write_asset_snapshot_to_mongo(db, snapshot_id: str, kept_df: pd.DataFrame, cfg: BackfillConfig) -> None:
    """Insert a ``bowaka_asset_snapshots`` doc + bulk-upsert all kept_df rows."""
    snap = {
        "snapshot_id": snapshot_id,
        "vendor": "alpaca",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "allowed_exchanges": list(cfg.allowed_exchanges),
        "asset_count": int(kept_df.shape[0]),
        "source": "alpaca_trading_assets",
        "notes": "Current asset universe. Survivorship-biased for historical backtests.",
    }
    db["bowaka_asset_snapshots"].update_one({"snapshot_id": snapshot_id}, {"$set": snap}, upsert=True)
    if kept_df.empty:
        return
    asset_coll = db["bowaka_assets"]
    for _, row in kept_df.iterrows():
        doc = row.to_dict()
        doc["snapshot_id"] = snapshot_id
        asset_coll.update_one({"snapshot_id": snapshot_id, "symbol": doc["symbol"]}, {"$set": doc}, upsert=True)


def write_ingestion_run_to_mongo(db, run_record: dict) -> None:
    required = (
        "ingestion_run_id",
        "vendor",
        "feed",
        "timeframe",
        "adjustment",
        "start",
        "end",
        "symbol_count_requested",
        "symbol_count_success",
        "symbol_count_failed",
        "api_call_count",
        "rate_limit_policy",
        "dataset_hash",
        "parquet_root",
        "created_at",
    )
    missing = [k for k in required if k not in run_record]
    if missing:
        raise ValueError(f"ingestion run record missing fields: {missing}")
    db["bowaka_data_ingestion_runs"].update_one(
        {"ingestion_run_id": run_record["ingestion_run_id"]},
        {"$set": run_record},
        upsert=True,
    )


def write_daily_audits_to_mongo(db, audits_df: pd.DataFrame, cfg: BackfillConfig) -> None:
    """Persist daily-bar audit rows to Mongo.

    Branches on ``cfg.audit_history_mode``:

    - ``"latest"`` (default; backward compatible): upsert by
      ``(symbol, feed, timeframe)`` so each weekly run overwrites the prior
      audit row. ``audit_run_id`` is stored as a regular field so callers can
      tell when the row was last refreshed.
    - ``"append"``: upsert by ``(symbol, feed, timeframe, audit_run_id)`` so
      history accumulates — one row per audit run per symbol.

    ``apply_indexes`` creates both unique-index variants; this writer just
    picks the matching one.
    """
    if audits_df.empty:
        return
    coll = db["bowaka_daily_bar_audits"]
    mode = getattr(cfg, "audit_history_mode", "latest")
    for _, row in audits_df.iterrows():
        doc = row.to_dict()
        doc["feed"] = cfg.feed
        if mode == "append":
            audit_run_id = doc.get("audit_run_id") or f"audit_unknown_{cfg.feed}"
            doc["audit_run_id"] = audit_run_id
            coll.update_one(
                {
                    "symbol": doc["symbol"],
                    "feed": doc["feed"],
                    "timeframe": doc["timeframe"],
                    "audit_run_id": audit_run_id,
                },
                {"$set": doc},
                upsert=True,
            )
        else:
            coll.update_one(
                {"symbol": doc["symbol"], "feed": doc["feed"], "timeframe": doc["timeframe"]},
                {"$set": doc},
                upsert=True,
            )


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


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
        "out_dir": str(cfg.out_dir),
        "counts": counts,
        "dataset_hashes": dataset_hashes,
    }
    target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Estimator
# ---------------------------------------------------------------------------


def estimate_storage_and_time(cfg: BackfillConfig) -> dict:
    """Rough projection of disk space + API calls + wall clock."""
    import exchange_calendars as xcals

    cal = xcals.get_calendar("XNYS")
    sessions = cal.sessions_in_range(pd.Timestamp(cfg.daily_fetch_start), pd.Timestamp(cfg.end_date))
    n_sessions_total = len(sessions)
    n_sessions_in_window = len(cal.sessions_in_range(pd.Timestamp(cfg.start_date), pd.Timestamp(cfg.end_date)))

    n_universe_est = 7_500
    daily_files = n_universe_est
    daily_kb_per_file = 6
    daily_gb = daily_files * daily_kb_per_file / 1024 / 1024

    n_scope_per_session_est = 80
    minute_files = n_sessions_in_window * n_scope_per_session_est
    minute_kb_per_file = 50
    minute_gb = minute_files * minute_kb_per_file / 1024 / 1024

    api_calls = (
        (n_universe_est // cfg.batch_size_symbols + 1)
        + n_sessions_in_window * (n_scope_per_session_est // cfg.batch_size_symbols + 1)
    )
    wall_clock_hours = (api_calls / cfg.rate_limit_rpm) / 60.0

    return {
        "n_sessions": int(n_sessions_in_window),
        "n_sessions_with_warmup": int(n_sessions_total),
        "n_universe_est": int(n_universe_est),
        "daily_files": int(daily_files),
        "minute_files": int(minute_files),
        "daily_gb": round(daily_gb, 3),
        "minute_gb": round(minute_gb, 3),
        "total_gb": round(daily_gb + minute_gb, 3),
        "api_calls": int(api_calls),
        "wall_clock_hours": round(wall_clock_hours, 2),
    }
