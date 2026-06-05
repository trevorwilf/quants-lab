"""Configurable, incremental backfill of the shared market-data lake.

:func:`run_configured_backfill` is the single orchestration entry point shared by
``scripts/backfill_market_data.py`` (cron automation) and the manual Jupyter
notebook, so the two never drift.

It is **incremental** — `incremental_window` fetches only the missing head/tail
of daily bars, and `fetch_minute_bars` skips already-covered ``(symbol, session)``
pairs — and **feed-aware**: switching ``feed`` between ``iex`` and ``sip`` writes a
separate ``feed=`` partition, so the first SIP run fills that partition and later
runs extend it incrementally. Re-running with the same dates is a near no-op;
advancing ``end_date`` (or using ``end_date: auto``) fetches just the new sessions.
"""
from __future__ import annotations

import datetime as _dt
import logging
import os
from pathlib import Path
from typing import Any, Callable, Iterable

import pandas as pd
import yaml

from . import catalog as _catalog
from .backfill import (
    BackfillConfig,
    RateLimiter,
    _get_xnys_calendar,
    audit_daily_bars,
    compute_dataset_hash,
    fetch_assets,
    fetch_daily_bars,
    fetch_minute_bars,
    fetch_quotes,
    find_and_load_dotenv,
    write_audits,
    write_ingestion_run,
    write_manifest_json,
)
from .store import MarketDataStore, resolve_market_data_root

ALLOWED_FEEDS = ("iex", "sip")
ALLOWED_MINUTE_POLICIES = ("none", "explicit", "all_daily", "adv_gated")


def _log() -> logging.Logger:
    log = logging.getLogger("bowaka_common.marketdata.runner")
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(handler)
        log.setLevel(logging.INFO)
    return log


def _to_date(value: Any) -> _dt.date:
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    return pd.Timestamp(value).date()


def resolve_end_date(value: Any) -> _dt.date:
    """Resolve ``end_date``. ``None`` / ``"auto"`` → yesterday (UTC) so a nightly
    job extends the lake to the most recent complete day without config edits."""
    if value is None or (isinstance(value, str) and value.strip().lower() == "auto"):
        return _dt.datetime.now(_dt.timezone.utc).date() - _dt.timedelta(days=1)
    return _to_date(value)


def load_backfill_config(path: str | Path) -> dict:
    """Load and lightly validate a backfill YAML config."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"backfill config at {path} did not parse to a mapping")
    if "start_date" not in raw:
        raise ValueError(f"backfill config at {path} is missing required key 'start_date'")
    feed = str(raw.get("feed", "iex"))
    if feed not in ALLOWED_FEEDS:
        raise ValueError(f"feed must be one of {ALLOWED_FEEDS}, got {feed!r}")
    policy = str((raw.get("minute_bars") or {}).get("policy", "none"))
    if policy not in ALLOWED_MINUTE_POLICIES:
        raise ValueError(f"minute_bars.policy must be one of {ALLOWED_MINUTE_POLICIES}, got {policy!r}")
    return raw


def _xnys_sessions(start: _dt.date, end: _dt.date) -> list[_dt.date]:
    cal = _get_xnys_calendar()
    return [pd.Timestamp(s).date() for s in cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end))]


def _adv_gated_targets(
    minute_cfg: dict, bcfg: BackfillConfig, lake: Path, symbols: Iterable[str],
    sessions: list[_dt.date], log: logging.Logger,
) -> pd.DataFrame:
    """Price-band + rolling-ADV gate over lake daily bars (no-lookahead)."""
    store = MarketDataStore(lake)
    price_min = float(minute_cfg.get("price_min", 1.0))
    price_max = float(minute_cfg.get("price_max", 20.0))
    adv_min = float(minute_cfg.get("adv_min", 200_000.0))
    adv_window = int(minute_cfg.get("adv_window_days", 20))
    session_set = set(sessions)
    pad = _dt.timedelta(days=int(adv_window * 1.6) + 10)
    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        df = store.daily_bars(symbol, min(sessions) - pad, max(sessions), feed=bcfg.feed, adjustment=bcfg.adjustment)
        if df.empty:
            continue
        if "session_date" in df.columns:
            sd = pd.to_datetime(df["session_date"]).dt.date
        else:
            sd = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date
        df = df.assign(_sd=sd).sort_values("_sd")
        dollar_vol = df["close"].astype(float) * df["volume"].astype(float)
        adv = dollar_vol.shift(1).rolling(adv_window).mean()
        mask = (
            adv.notna()
            & df["close"].between(price_min, price_max, inclusive="both")
            & (adv >= adv_min)
            & df["_sd"].isin(session_set)
        )
        selected = df.loc[mask, ["_sd"]].rename(columns={"_sd": "session_date"})
        if not selected.empty:
            selected["symbol"] = symbol
            frames.append(selected[["session_date", "symbol"]])
    if not frames:
        return pd.DataFrame(columns=["session_date", "symbol"])
    return pd.concat(frames, ignore_index=True)


def _minute_targets(
    minute_cfg: dict, bcfg: BackfillConfig, lake: Path, assets_df: pd.DataFrame, log: logging.Logger,
) -> pd.DataFrame | None:
    """Resolve the ``(session_date, symbol)`` table for the minute-bar stage."""
    policy = str(minute_cfg.get("policy", "none"))
    if policy == "none":
        return None
    sessions = _xnys_sessions(bcfg.start_date, bcfg.end_date)
    if not sessions:
        return None
    if policy == "adv_gated":
        candidates = list(assets_df["symbol"].astype(str)) if not assets_df.empty else []
        return _adv_gated_targets(minute_cfg, bcfg, lake, candidates, sessions, log)
    if policy == "explicit":
        symbols = sorted({str(s) for s in (minute_cfg.get("symbols") or [])})
    else:  # all_daily
        symbols = _catalog.available_symbols(
            lake, timeframe="1d", feed=bcfg.feed, adjustment=bcfg.adjustment
        )
    if not symbols:
        return None
    return pd.DataFrame(
        [{"session_date": s, "symbol": sym} for s in sessions for sym in symbols]
    )


def run_configured_backfill(
    config: dict,
    *,
    lake_root: str | Path | None = None,
    log: logging.Logger | None = None,
    assets_fetcher: Callable[[], Iterable[Any]] | None = None,
    bars_fetcher: Any | None = None,
    quotes_fetcher: Any | None = None,
) -> dict:
    """Run the configurable, incremental backfill described by ``config``.

    ``assets_fetcher`` / ``bars_fetcher`` are injection points for tests; in
    production they default to the live Alpaca fetchers.
    """
    log = log or _log()
    # Best-effort: load ALPACA_* (etc.) from a repo .env so cron and notebook
    # runs work without the caller exporting credentials first.
    try:
        find_and_load_dotenv()
    except Exception:  # noqa: BLE001
        pass
    lake = resolve_market_data_root(lake_root if lake_root is not None else config.get("lake_root"))
    start = _to_date(config["start_date"])
    end = resolve_end_date(config.get("end_date", "auto"))
    if end < start:
        raise ValueError(f"end_date {end} is before start_date {start}")
    feed = str(config.get("feed", "iex"))
    if feed not in ALLOWED_FEEDS:
        raise ValueError(f"feed must be one of {ALLOWED_FEEDS}, got {feed!r}")

    bcfg = BackfillConfig(
        api_key=os.environ.get("ALPACA_API_KEY_ID", ""),
        api_secret=os.environ.get("ALPACA_API_SECRET_KEY", ""),
        paper=bool(config.get("paper", True)),
        feed=feed,
        start_date=start,
        end_date=end,
        lake_root=lake,
        adjustment=str(config.get("adjustment", "raw")),
        rate_limit_rpm=int(config.get("rate_limit_rpm", 180)),
        batch_size_symbols=int(config.get("batch_size_symbols", 200)),
        resume=True,
    )
    log.info("backfill start: feed=%s range=%s..%s lake=%s", feed, start, end, lake)
    limiter = RateLimiter(bcfg.rate_limit_rpm)

    # -- assets ----------------------------------------------------------
    daily_universe = config.get("daily_universe", {}) or {}
    if str(daily_universe.get("source", "alpaca_assets")) == "explicit":
        explicit_syms = sorted({str(s) for s in (daily_universe.get("symbols") or [])})
        assets_df = pd.DataFrame({"symbol": explicit_syms})
        snapshot_id: str | None = None
    else:
        snapshot_id, assets_df = fetch_assets(bcfg, log, assets_fetcher=assets_fetcher)

    # -- daily bars (incremental: head + tail) ---------------------------
    daily_stats = fetch_daily_bars(bcfg, assets_df, log, limiter, bars_fetcher=bars_fetcher)

    # -- minute bars + quotes (incremental: resume skips covered sessions) --
    # Quotes share the minute-bar (symbol, session) universe, so they exist
    # exactly where bars do. Compute the target set once for both stages.
    minute_cfg = config.get("minute_bars", {}) or {}
    quotes_cfg = config.get("quotes", {}) or {}
    minute_stats: dict = {}
    quote_stats: dict = {}
    targets = None
    if minute_cfg.get("enabled", False) or quotes_cfg.get("enabled", False):
        targets = _minute_targets(minute_cfg, bcfg, lake, assets_df, log)
    if minute_cfg.get("enabled", False) and targets is not None and len(targets) > 0:
        minute_stats = fetch_minute_bars(bcfg, targets, log, limiter, bars_fetcher=bars_fetcher)
    # SIP NBBO quotes — required for intended_realism (quote-aware fills/exits +
    # the quote-coverage gate). IEX quotes are partial-tape and unused by realism.
    if quotes_cfg.get("enabled", False):
        if feed != "sip":
            log.warning("quotes.enabled with feed=%s — IEX quotes are partial-tape and are "
                        "NOT used by intended_realism; SIP is the intended feed.", feed)
        if targets is not None and len(targets) > 0:
            quote_stats = fetch_quotes(
                bcfg, targets, log, limiter, quotes_fetcher=quotes_fetcher,
                batch_size=int(quotes_cfg.get("batch_size_symbols", 25)),
            )
        else:
            log.warning("quotes.enabled but no (symbol, session) targets — enable "
                        "minute_bars (quotes use its universe).")

    # -- audit + manifest + ingestion-run record -------------------------
    audits = audit_daily_bars(bcfg, log)
    if not audits.empty:
        write_audits(bcfg, audits)
    counts = {
        "assets": int(len(assets_df)),
        "daily": daily_stats,
        "minute": minute_stats,
        "quotes": quote_stats,
        "audit_rows": int(len(audits)),
    }
    write_manifest_json(bcfg, counts, {"lake": compute_dataset_hash(lake)})
    run_id = f"ingest_{_dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}_{feed}"
    write_ingestion_run(
        bcfg,
        {
            "ingestion_run_id": run_id,
            "vendor": "alpaca",
            "feed": feed,
            "adjustment": bcfg.adjustment,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "counts": counts,
            "created_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        },
    )
    result = {
        "run_id": run_id,
        "feed": feed,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "lake_root": str(lake),
        "snapshot_id": snapshot_id,
        "counts": counts,
    }
    log.info("backfill done: run_id=%s daily=%s minute=%s quotes=%s",
             run_id, daily_stats, minute_stats, quote_stats)
    return result
