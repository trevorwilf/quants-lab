"""Shared utilities for public REST-based pair screeners.

These helpers are intentionally conservative: the goal is to shortlist
markets for *research and data ingestion*, not to certify them as live-ready.
"""

from __future__ import annotations

import json
import logging
import math
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

EXTENDED_INTERVAL_SECONDS: dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "3h": 10800,
    "4h": 14400,
    "8h": 28800,
    "12h": 43200,
    "1d": 86400,
    "1w": 604800,
    "1W": 604800,
    "1M": 2592000,
}

DEFAULT_EXCLUDE_PATTERNS: tuple[str, ...] = (
    r"(?:^|[^A-Z])(3L|3S|5L|5S)$",
    r"(?:UP|DOWN|BULL|BEAR)$",
)

DEFAULT_SCORE_WEIGHTS: dict[str, float] = {
    "volume": 0.24,
    "depth": 0.20,
    "spread": 0.16,
    "top_of_book": 0.08,
    "activity": 0.12,
    "quality": 0.10,
    "alpha": 0.10,
}


@dataclass
class ScreenerConfig:
    """Configuration for a public REST screener."""

    connector: str
    quote_asset: str = "USDT"
    interval: str = "5m"
    universe_top_k: int = 80
    final_top_n: int = 25
    candle_limit: int = 288
    depth_limit: int = 200
    recent_trade_limit: int = 500
    request_pause_sec: float = 0.10
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_backoff: float = 1.8
    user_agent: str = "pmm-lab-screener/0.1"

    min_quote_volume_24h: float = 100_000.0
    max_spread_bps: float = 80.0
    min_top_of_book_quote: float = 100.0
    min_depth_10bps_quote: float = 300.0
    max_last_trade_age_sec: float = 3600.0
    min_recent_trade_count: int = 50
    min_candle_count: int = 200
    min_candle_coverage_ratio: float = 0.95
    max_zero_volume_fraction: float = 0.35
    min_natr_bps: float = 8.0
    max_natr_bps: float = 350.0

    natr_soft_min: float = 5.0
    natr_target_min: float = 15.0
    natr_target_max: float = 150.0
    natr_soft_max: float = 300.0

    efficiency_soft_min: float = 0.00
    efficiency_target_min: float = 0.05
    efficiency_target_max: float = 0.45
    efficiency_soft_max: float = 0.80

    vol_to_spread_soft_min: float = 1.0
    vol_to_spread_target_min: float = 3.0
    vol_to_spread_target_max: float = 25.0
    vol_to_spread_soft_max: float = 60.0

    exclude_regex: tuple[str, ...] = DEFAULT_EXCLUDE_PATTERNS
    include_symbols: tuple[str, ...] = field(default_factory=tuple)
    exclude_symbols: tuple[str, ...] = field(default_factory=tuple)
    score_weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_SCORE_WEIGHTS))

    def interval_seconds(self) -> int:
        try:
            return EXTENDED_INTERVAL_SECONDS[self.interval]
        except KeyError as exc:
            raise ValueError(f"Unsupported interval: {self.interval}") from exc

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["interval_seconds"] = self.interval_seconds()
        return d


@dataclass
class ScreeningRun:
    """Container for the screener pipeline outputs."""

    connector: str
    config: ScreenerConfig
    universe: pd.DataFrame
    shortlist: pd.DataFrame
    final: pd.DataFrame
    selected: pd.DataFrame
    started_at: str
    finished_at: str
    notes: list[str] = field(default_factory=list)

    def metadata(self) -> dict[str, Any]:
        return {
            "connector": self.connector,
            "config": self.config.as_dict(),
            "counts": {
                "universe": int(len(self.universe)),
                "shortlist": int(len(self.shortlist)),
                "final": int(len(self.final)),
                "selected": int(len(self.selected)),
            },
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "notes": list(self.notes),
        }


class JsonRestClient:
    """Small JSON REST client using only the standard library."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 1.8,
        user_agent: str = "pmm-lab-screener/0.1",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = float(timeout_seconds)
        self.max_retries = int(max_retries)
        self.retry_backoff = float(retry_backoff)
        self.user_agent = user_agent

    def get(
        self,
        path: str,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            clean = {
                k: v
                for k, v in params.items()
                if v is not None and v != ""
            }
            if clean:
                url = f"{url}?{urlencode(clean)}"

        req_headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }
        if headers:
            req_headers.update(headers)

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                req = Request(url, headers=req_headers, method="GET")
                with urlopen(req, timeout=self.timeout_seconds) as resp:
                    payload = resp.read().decode("utf-8")
                    if not payload:
                        return None
                    return json.loads(payload)
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                retryable = True
                if isinstance(exc, HTTPError) and exc.code < 500 and exc.code not in (408, 409, 429):
                    retryable = False
                if attempt >= self.max_retries or not retryable:
                    break
                sleep_for = self.retry_backoff ** (attempt - 1)
                log.warning("GET %s failed on attempt %d/%d: %s", url, attempt, self.max_retries, exc)
                time.sleep(sleep_for)
        raise RuntimeError(f"GET {url} failed after {self.max_retries} attempts: {last_error}")


class PublicExchangeScreener:
    """Base class for public REST market screeners."""

    base_url: str = ""

    def __init__(self, config: ScreenerConfig) -> None:
        self.config = config
        if not self.base_url:
            raise ValueError("Subclasses must define base_url")
        self.client = JsonRestClient(
            self.base_url,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
            retry_backoff=config.retry_backoff,
            user_agent=config.user_agent,
        )

    def build_universe(self) -> pd.DataFrame:
        raise NotImplementedError

    def enrich_pair(self, row: Mapping[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def screen_from_universe(self, universe: pd.DataFrame) -> ScreeningRun:
        started = now_utc_iso()
        universe = universe.copy()
        if universe.empty:
            finished = now_utc_iso()
            empty = pd.DataFrame()
            return ScreeningRun(
                connector=self.config.connector,
                config=self.config,
                universe=universe,
                shortlist=empty,
                final=empty,
                selected=empty,
                started_at=started,
                finished_at=finished,
                notes=["Universe build returned zero rows."],
            )

        if "coarse_score" not in universe.columns:
            universe = compute_coarse_scores(universe)
        shortlist = select_shortlist(universe, self.config)

        enriched_rows: list[dict[str, Any]] = []
        for _, row in shortlist.iterrows():
            row_dict = row.to_dict()
            try:
                metrics = self.enrich_pair(row_dict)
            except Exception as exc:  # pragma: no cover - exercised by live notebook usage
                metrics = {
                    "screen_error": str(exc),
                    "passed_filters": False,
                    "rejection_reason": f"enrichment_error:{exc}",
                }
                log.exception("Failed to enrich %s %s", self.config.connector, row_dict.get("trading_pair"))
            enriched_rows.append({**row_dict, **metrics})
            if self.config.request_pause_sec > 0:
                time.sleep(self.config.request_pause_sec)

        final = pd.DataFrame(enriched_rows)
        if not final.empty:
            final = apply_screening_logic(final, self.config)
        selected = final[final["passed_filters"]].copy() if not final.empty else final.copy()
        if not selected.empty:
            selected = selected.sort_values(["screen_score", "quote_volume_24h"], ascending=[False, False]).head(
                self.config.final_top_n
            )
        finished = now_utc_iso()
        notes = [
            "Research/ingestion only. Passing the screener does not imply live readiness.",
            "Rule fields in exports are estimates unless the exchange API exposes exact constraints.",
        ]
        return ScreeningRun(
            connector=self.config.connector,
            config=self.config,
            universe=universe,
            shortlist=shortlist,
            final=final,
            selected=selected,
            started_at=started,
            finished_at=finished,
            notes=notes,
        )

    def screen(self) -> ScreeningRun:
        return self.screen_from_universe(self.build_universe())


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_float(value: Any, default: float = math.nan) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return default
        return float(value)
    try:
        text = str(value).strip()
        if text == "" or text.lower() in {"null", "none", "nan"}:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default



def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default



def to_hb_pair(base_asset: str, quote_asset: str) -> str:
    return f"{str(base_asset).upper()}-{str(quote_asset).upper()}"



def split_hb_pair(trading_pair: str) -> tuple[str, str]:
    if "-" not in trading_pair:
        raise ValueError(f"Expected Hummingbot trading pair like BTC-USDT, got: {trading_pair}")
    base, quote = trading_pair.split("-", 1)
    return base.upper(), quote.upper()



def hb_to_slash_pair(trading_pair: str) -> str:
    base, quote = split_hb_pair(trading_pair)
    return f"{base}/{quote}"



def hb_to_underscore_pair(trading_pair: str) -> str:
    base, quote = split_hb_pair(trading_pair)
    return f"{base}_{quote}"



def should_exclude_symbol(base_asset: str, exchange_symbol: str, config: ScreenerConfig) -> bool:
    base = str(base_asset).upper()
    symbol = str(exchange_symbol).upper()
    if config.include_symbols:
        return symbol not in {s.upper() for s in config.include_symbols}
    if symbol in {s.upper() for s in config.exclude_symbols}:
        return True
    for pattern in config.exclude_regex:
        if re.search(pattern, base, flags=re.IGNORECASE):
            return True
    return False



def normalize_orderbook_side(side: Any, reverse: bool = False) -> list[tuple[float, float]]:
    rows: list[tuple[float, float]] = []
    if side is None:
        return rows
    for item in side:
        price: float
        qty: float
        if isinstance(item, Mapping):
            price = safe_float(item.get("price") or item.get("numberprice"))
            qty = safe_float(item.get("quantity") or item.get("qty"))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            price = safe_float(item[0])
            qty = safe_float(item[1])
        else:
            continue
        if price > 0 and qty > 0:
            rows.append((price, qty))
    rows.sort(key=lambda x: x[0], reverse=reverse)
    return rows



def compute_orderbook_metrics(
    bids: Any,
    asks: Any,
    depth_bps: Sequence[int] = (5, 10, 25),
) -> dict[str, Any]:
    bid_levels = normalize_orderbook_side(bids, reverse=True)
    ask_levels = normalize_orderbook_side(asks, reverse=False)
    metrics: dict[str, Any] = {
        "best_bid": math.nan,
        "best_ask": math.nan,
        "mid_price": math.nan,
        "spread_abs": math.nan,
        "spread_bps": math.nan,
        "top_of_book_quote": math.nan,
        "bid_top_quote": math.nan,
        "ask_top_quote": math.nan,
        "book_crossed": False,
        "orderbook_levels_bid": len(bid_levels),
        "orderbook_levels_ask": len(ask_levels),
    }
    for bps in depth_bps:
        metrics[f"bid_depth_quote_{bps}bps"] = math.nan
        metrics[f"ask_depth_quote_{bps}bps"] = math.nan
        metrics[f"sym_depth_quote_{bps}bps"] = math.nan

    if not bid_levels or not ask_levels:
        return metrics

    best_bid, best_bid_qty = bid_levels[0]
    best_ask, best_ask_qty = ask_levels[0]
    mid = (best_bid + best_ask) / 2.0
    spread_abs = best_ask - best_bid
    spread_bps = (spread_abs / mid) * 10_000.0 if mid > 0 else math.nan

    metrics.update(
        {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid_price": mid,
            "spread_abs": spread_abs,
            "spread_bps": max(spread_bps, 0.0) if not math.isnan(spread_bps) else spread_bps,
            "book_crossed": bool(best_ask <= best_bid),
            "bid_top_quote": best_bid * best_bid_qty,
            "ask_top_quote": best_ask * best_ask_qty,
            "top_of_book_quote": min(best_bid * best_bid_qty, best_ask * best_ask_qty),
        }
    )

    for bps in depth_bps:
        band = bps / 10_000.0
        bid_floor = mid * (1.0 - band)
        ask_ceiling = mid * (1.0 + band)
        bid_depth_quote = sum(price * qty for price, qty in bid_levels if price >= bid_floor)
        ask_depth_quote = sum(price * qty for price, qty in ask_levels if price <= ask_ceiling)
        metrics[f"bid_depth_quote_{bps}bps"] = bid_depth_quote
        metrics[f"ask_depth_quote_{bps}bps"] = ask_depth_quote
        metrics[f"sym_depth_quote_{bps}bps"] = min(bid_depth_quote, ask_depth_quote)

    return metrics



def ensure_timestamp_seconds(ts_like: Any) -> float:
    if ts_like is None:
        return math.nan
    if isinstance(ts_like, (int, float)):
        value = float(ts_like)
        if value > 1e12:
            return value / 1000.0
        if value > 1e10:
            return value / 1000.0
        return value
    text = str(ts_like).strip()
    if not text:
        return math.nan
    try:
        if text.isdigit():
            return ensure_timestamp_seconds(float(text))
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return math.nan



def compute_candle_metrics(candles: pd.DataFrame, interval_seconds: int) -> dict[str, Any]:
    columns = ["timestamp", "open", "high", "low", "close", "volume"]
    if candles is None or candles.empty:
        return {
            "n_candles": 0,
            "candle_first_ts": math.nan,
            "candle_last_ts": math.nan,
            "candle_expected": 0,
            "candle_missing": math.nan,
            "coverage_ratio": math.nan,
            "zero_volume_fraction": math.nan,
            "natr_bps_mean": math.nan,
            "realized_vol_bps": math.nan,
            "efficiency_ratio": math.nan,
            "lag1_return_autocorr": math.nan,
            "median_quote_volume_per_bar": math.nan,
        }

    df = candles.loc[:, columns].copy()
    df["timestamp"] = df["timestamp"].map(ensure_timestamp_seconds)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"])
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")

    if df.empty:
        return {
            "n_candles": 0,
            "candle_first_ts": math.nan,
            "candle_last_ts": math.nan,
            "candle_expected": 0,
            "candle_missing": math.nan,
            "coverage_ratio": math.nan,
            "zero_volume_fraction": math.nan,
            "natr_bps_mean": math.nan,
            "realized_vol_bps": math.nan,
            "efficiency_ratio": math.nan,
            "lag1_return_autocorr": math.nan,
            "median_quote_volume_per_bar": math.nan,
        }

    first_ts = float(df["timestamp"].iloc[0])
    last_ts = float(df["timestamp"].iloc[-1])
    expected = max(int(round((last_ts - first_ts) / interval_seconds)) + 1, len(df))
    missing = max(expected - len(df), 0)
    coverage_ratio = len(df) / expected if expected > 0 else math.nan
    zero_volume_fraction = float((df["volume"] <= 0).mean())

    close = df["close"].replace(0, np.nan)
    ret = close.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    log_ret = np.log(close).diff().replace([np.inf, -np.inf], np.nan).dropna()
    range_bps = ((df["high"] - df["low"]) / close.abs()) * 10_000.0
    range_bps = range_bps.replace([np.inf, -np.inf], np.nan)

    diff_sum = close.diff().abs().sum(skipna=True)
    efficiency = abs(close.iloc[-1] - close.iloc[0]) / diff_sum if diff_sum and diff_sum > 0 else 0.0
    lag1_autocorr = float(ret.autocorr(lag=1)) if len(ret) >= 5 else math.nan

    return {
        "n_candles": int(len(df)),
        "candle_first_ts": first_ts,
        "candle_last_ts": last_ts,
        "candle_expected": int(expected),
        "candle_missing": int(missing),
        "coverage_ratio": float(coverage_ratio),
        "zero_volume_fraction": zero_volume_fraction,
        "natr_bps_mean": float(range_bps.mean(skipna=True)) if not range_bps.empty else math.nan,
        "realized_vol_bps": float(log_ret.std(ddof=0) * 10_000.0) if not log_ret.empty else math.nan,
        "efficiency_ratio": float(efficiency),
        "lag1_return_autocorr": lag1_autocorr,
        "median_quote_volume_per_bar": float((df["close"] * df["volume"]).median()),
    }



def compute_trade_metrics(trades: pd.DataFrame, now_ts: Optional[float] = None) -> dict[str, Any]:
    if trades is None or trades.empty:
        return {
            "recent_trade_count": 0,
            "trades_per_minute": math.nan,
            "trade_quote_volume": math.nan,
            "trade_quote_volume_per_minute": math.nan,
            "last_trade_age_sec": math.nan,
            "median_trade_quote": math.nan,
            "buy_trade_fraction": math.nan,
        }

    df = trades.copy()
    if "timestamp" not in df.columns:
        raise ValueError("Trades DataFrame must include a timestamp column")
    df["timestamp"] = df["timestamp"].map(ensure_timestamp_seconds)
    if "price" not in df.columns or "quantity" not in df.columns:
        raise ValueError("Trades DataFrame must include price and quantity columns")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    if "quote_quantity" not in df.columns:
        df["quote_quantity"] = df["price"] * df["quantity"]
    else:
        df["quote_quantity"] = pd.to_numeric(df["quote_quantity"], errors="coerce")
    df = df.dropna(subset=["timestamp", "price", "quantity", "quote_quantity"]) 
    df = df.sort_values("timestamp")

    if df.empty:
        return {
            "recent_trade_count": 0,
            "trades_per_minute": math.nan,
            "trade_quote_volume": math.nan,
            "trade_quote_volume_per_minute": math.nan,
            "last_trade_age_sec": math.nan,
            "median_trade_quote": math.nan,
            "buy_trade_fraction": math.nan,
        }

    start_ts = float(df["timestamp"].iloc[0])
    end_ts = float(df["timestamp"].iloc[-1])
    window_sec = max(end_ts - start_ts, 60.0)
    now_value = now_ts if now_ts is not None else time.time()
    age_sec = max(now_value - end_ts, 0.0)

    buy_fraction = math.nan
    if "side" in df.columns:
        side = df["side"].astype(str).str.lower()
        buy_fraction = float((side == "buy").mean())

    return {
        "recent_trade_count": int(len(df)),
        "trades_per_minute": float(len(df) / (window_sec / 60.0)),
        "trade_quote_volume": float(df["quote_quantity"].sum()),
        "trade_quote_volume_per_minute": float(df["quote_quantity"].sum() / (window_sec / 60.0)),
        "last_trade_age_sec": float(age_sec),
        "median_trade_quote": float(df["quote_quantity"].median()),
        "buy_trade_fraction": buy_fraction,
    }



def percentile_rank(series: pd.Series, reverse: bool = False) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    if s.notna().sum() <= 1:
        base = pd.Series(np.where(s.notna(), 1.0, 0.0), index=s.index, dtype=float)
        return base
    ranks = s.rank(pct=True, method="average")
    ranks = ranks.fillna(0.0)
    if reverse:
        return (1.0 - ranks).clip(lower=0.0, upper=1.0)
    return ranks.clip(lower=0.0, upper=1.0)



def band_score(value: Any, soft_min: float, target_min: float, target_max: float, soft_max: float) -> float:
    x = safe_float(value)
    if math.isnan(x):
        return 0.0
    if x < soft_min or x > soft_max:
        return 0.0
    if target_min <= x <= target_max:
        return 1.0
    if x < target_min:
        width = max(target_min - soft_min, 1e-9)
        return max(0.0, min(1.0, (x - soft_min) / width))
    width = max(soft_max - target_max, 1e-9)
    return max(0.0, min(1.0, (soft_max - x) / width))



def compute_coarse_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["coarse_volume_rank"] = percentile_rank(np.log1p(pd.to_numeric(out["quote_volume_24h"], errors="coerce")))
    out["coarse_spread_rank"] = percentile_rank(pd.to_numeric(out["spread_bps"], errors="coerce"), reverse=True)
    out["coarse_top_rank"] = percentile_rank(np.log1p(pd.to_numeric(out["top_of_book_quote"], errors="coerce")))
    out["coarse_score"] = 100.0 * (
        0.55 * out["coarse_volume_rank"]
        + 0.25 * out["coarse_spread_rank"]
        + 0.20 * out["coarse_top_rank"]
    )
    return out.sort_values(["coarse_score", "quote_volume_24h"], ascending=[False, False]).reset_index(drop=True)



def select_shortlist(universe: pd.DataFrame, config: ScreenerConfig) -> pd.DataFrame:
    df = universe.copy()
    mask = pd.Series(True, index=df.index)
    if "is_active" in df.columns:
        mask &= df["is_active"].fillna(False).astype(bool)
    if "quote_asset" in df.columns:
        mask &= df["quote_asset"].astype(str).str.upper().eq(config.quote_asset.upper())
    df = df[mask].copy()
    if df.empty:
        return df
    return df.sort_values(["coarse_score", "quote_volume_24h"], ascending=[False, False]).head(config.universe_top_k)



def build_rejection_reasons(row: Mapping[str, Any], config: ScreenerConfig) -> list[str]:
    reasons: list[str] = []

    if not bool(row.get("is_active", False)):
        reasons.append("inactive")
    if str(row.get("quote_asset", "")).upper() != config.quote_asset.upper():
        reasons.append("quote_asset_mismatch")

    qv = safe_float(row.get("quote_volume_24h"))
    if math.isnan(qv):
        reasons.append("missing_quote_volume_24h")
    elif qv < config.min_quote_volume_24h:
        reasons.append(f"quote_volume_24h<{config.min_quote_volume_24h:g}")

    spread = safe_float(row.get("spread_bps"))
    if math.isnan(spread):
        reasons.append("missing_spread_bps")
    elif spread > config.max_spread_bps:
        reasons.append(f"spread_bps>{config.max_spread_bps:g}")

    tob = safe_float(row.get("top_of_book_quote"))
    if math.isnan(tob):
        reasons.append("missing_top_of_book_quote")
    elif tob < config.min_top_of_book_quote:
        reasons.append(f"top_of_book_quote<{config.min_top_of_book_quote:g}")

    depth10 = safe_float(row.get("sym_depth_quote_10bps"))
    if math.isnan(depth10):
        reasons.append("missing_depth_10bps")
    elif depth10 < config.min_depth_10bps_quote:
        reasons.append(f"depth_10bps<{config.min_depth_10bps_quote:g}")

    age = safe_float(row.get("last_trade_age_sec"))
    if math.isnan(age):
        reasons.append("missing_last_trade_age_sec")
    elif age > config.max_last_trade_age_sec:
        reasons.append(f"last_trade_age_sec>{config.max_last_trade_age_sec:g}")

    recent_trades = safe_int(row.get("recent_trade_count"), default=-1)
    if recent_trades < 0:
        reasons.append("missing_recent_trade_count")
    elif recent_trades < config.min_recent_trade_count:
        reasons.append(f"recent_trade_count<{config.min_recent_trade_count}")

    n_candles = safe_int(row.get("n_candles"), default=-1)
    if n_candles < 0:
        reasons.append("missing_n_candles")
    elif n_candles < config.min_candle_count:
        reasons.append(f"n_candles<{config.min_candle_count}")

    coverage = safe_float(row.get("coverage_ratio"))
    if math.isnan(coverage):
        reasons.append("missing_coverage_ratio")
    elif coverage < config.min_candle_coverage_ratio:
        reasons.append(f"coverage_ratio<{config.min_candle_coverage_ratio:.2f}")

    zero_frac = safe_float(row.get("zero_volume_fraction"))
    if math.isnan(zero_frac):
        reasons.append("missing_zero_volume_fraction")
    elif zero_frac > config.max_zero_volume_fraction:
        reasons.append(f"zero_volume_fraction>{config.max_zero_volume_fraction:.2f}")

    natr = safe_float(row.get("natr_bps_mean"))
    if math.isnan(natr):
        reasons.append("missing_natr_bps_mean")
    elif natr < config.min_natr_bps:
        reasons.append(f"natr_bps_mean<{config.min_natr_bps:g}")
    elif natr > config.max_natr_bps:
        reasons.append(f"natr_bps_mean>{config.max_natr_bps:g}")

    if row.get("book_crossed") is True:
        reasons.append("crossed_orderbook")

    if row.get("screen_error"):
        reasons.append("enrichment_error")

    return reasons



def apply_screening_logic(df: pd.DataFrame, config: ScreenerConfig) -> pd.DataFrame:
    out = df.copy()

    out["vol_to_spread_ratio"] = (
        pd.to_numeric(out["natr_bps_mean"], errors="coerce")
        / pd.to_numeric(out["spread_bps"], errors="coerce").replace(0, np.nan)
    )

    out["volume_rank"] = percentile_rank(np.log1p(pd.to_numeric(out["quote_volume_24h"], errors="coerce")))
    out["depth_rank"] = percentile_rank(np.log1p(pd.to_numeric(out["sym_depth_quote_10bps"], errors="coerce")))
    out["spread_rank"] = percentile_rank(pd.to_numeric(out["spread_bps"], errors="coerce"), reverse=True)
    out["top_rank"] = percentile_rank(np.log1p(pd.to_numeric(out["top_of_book_quote"], errors="coerce")))
    out["activity_rank"] = 0.65 * percentile_rank(pd.to_numeric(out["trades_per_minute"], errors="coerce")) + 0.35 * percentile_rank(
        pd.to_numeric(out["last_trade_age_sec"], errors="coerce"), reverse=True
    )
    out["quality_rank"] = 0.55 * pd.to_numeric(out["coverage_ratio"], errors="coerce").clip(lower=0.0, upper=1.0).fillna(0.0) + 0.45 * (
        1.0 - pd.to_numeric(out["zero_volume_fraction"], errors="coerce").clip(lower=0.0, upper=1.0).fillna(1.0)
    )

    out["alpha_natr_score"] = out["natr_bps_mean"].map(
        lambda x: band_score(x, config.natr_soft_min, config.natr_target_min, config.natr_target_max, config.natr_soft_max)
    )
    out["alpha_efficiency_score"] = out["efficiency_ratio"].map(
        lambda x: band_score(
            x,
            config.efficiency_soft_min,
            config.efficiency_target_min,
            config.efficiency_target_max,
            config.efficiency_soft_max,
        )
    )
    out["alpha_edge_score"] = out["vol_to_spread_ratio"].map(
        lambda x: band_score(
            x,
            config.vol_to_spread_soft_min,
            config.vol_to_spread_target_min,
            config.vol_to_spread_target_max,
            config.vol_to_spread_soft_max,
        )
    )
    out["alpha_rank"] = (
        out["alpha_natr_score"] + out["alpha_efficiency_score"] + out["alpha_edge_score"]
    ) / 3.0

    weights = dict(DEFAULT_SCORE_WEIGHTS)
    weights.update(config.score_weights)
    total_weight = sum(weights.values()) or 1.0

    out["screen_score"] = 100.0 * (
        weights["volume"] * out["volume_rank"]
        + weights["depth"] * out["depth_rank"]
        + weights["spread"] * out["spread_rank"]
        + weights["top_of_book"] * out["top_rank"]
        + weights["activity"] * out["activity_rank"]
        + weights["quality"] * out["quality_rank"]
        + weights["alpha"] * out["alpha_rank"]
    ) / total_weight

    reasons = [build_rejection_reasons(row, config) for row in out.to_dict(orient="records")]
    out["rejection_reasons"] = reasons
    out["rejection_reason"] = ["; ".join(r) for r in reasons]
    out["passed_filters"] = [len(r) == 0 for r in reasons]

    return out.sort_values(["passed_filters", "screen_score", "quote_volume_24h"], ascending=[False, False, False]).reset_index(drop=True)



def records_to_frame(records: Iterable[Mapping[str, Any]]) -> pd.DataFrame:
    rows = list(records)
    return pd.DataFrame(rows)



def json_ready_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    frame = df.copy()
    frame = frame.replace({np.nan: None})
    records = frame.to_dict(orient="records")
    return records
