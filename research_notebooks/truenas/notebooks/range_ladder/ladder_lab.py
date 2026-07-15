"""
ladder_lab.py -- shared engine for the crypto oscillator / ladder finder notebooks
==================================================================================
One engine, two notebooks (Kraken v3, NonKYC v4). What this module provides over
the older self-contained-cell notebooks:

  DATA
  - Bars carry timestamps (Nx5 float: [ts_sec, o, h, l, c]); windows are sliced by
    time, not row count, so gappy histories don't shift the analysis window.
  - MEXC-first history proxy for BOTH exchanges (deep, parallel-friendly), with
    native fallback and a price guard: if the proxy's last close disagrees with the
    exchange's own ticker by > proxy_price_tol the proxy is rejected (catches ticker
    collisions, depegs, stale books).
  - On-disk candle cache (.npz per pair+interval, TTL) + parallel prefetch.
    Kraken-native fetches stay serial at ~1 req/s (their public limit).

  SIM
  - One parameterized fill sim used EVERYWHERE (backtest, durability, optimizer,
    weights, walk-forward, conservative stress). Numba-jitted when numba is
    available; the same code runs pure-Python otherwise. parity_check() proves the
    kernel matches a direct port of the original notebook sim.

  METHODOLOGY
  - screen(): original grid metrics + mean-reversion features (Hurst, OU half-life,
    vol-regime ratio) + a cross-sectional composite rank. `qualifies` is an
    annotation, not a filter -- everything gets backtested.
  - walkforward(): multi-fold, and each fold re-runs the FULL deployed pipeline
    (placement -> band optimizer -> weight optimizer) on train data only, freezes
    the result, and scores it out-of-sample. This validates the config you deploy,
    not a proxy of it.
  - finalize(): full-history optimize for survivors, conservative stress with the
    pair's MEASURED spread as slip, per-rung min-order-size gate, hourly-bar fill
    realism check, and (NonKYC) proxy-vs-native price divergence check.

Dependencies: requests, numpy, pandas. Optional: numba (strongly recommended).
"""
from __future__ import annotations

import concurrent.futures as _fut
import json
import math
import os
import re
import threading
import time

import numpy as np
import pandas as pd
import requests

__version__ = "1.0.0"

try:
    from numba import njit as _njit
    HAVE_NUMBA = True
except ImportError:  # same code runs pure-Python, just slower
    HAVE_NUMBA = False

    def _njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        def wrap(f):
            return f
        return wrap

KRAKEN = "https://api.kraken.com/0/public"
NONKYC = "https://api.nonkyc.io/api/v2"
MEXC = "https://api.mexc.com/api/v3"

_print_lock = threading.Lock()


def _log(msg):
    with _print_lock:
        print(msg, flush=True)


# ======================================================================
# Config
# ======================================================================
def default_config(exchange):
    """All pipeline knobs in one dict. exchange in {'kraken','nonkyc'}."""
    exchange = exchange.lower()
    if exchange not in ("kraken", "nonkyc"):
        raise ValueError("exchange must be 'kraken' or 'nonkyc'")
    cfg = dict(
        exchange=exchange,
        # ---------------- universe ----------------
        quotes=None,              # None = every quote; or a set like {"USDT","USD"}
        min_vol_usd=0.0,          # scan-time floor; liquidity is gated at deploy time
        require_usd_rate=True,    # drop pairs whose quote has no USD route
        max_scan=None,            # cap universe to top-N by USD vol (None = all)
        skip_inactive=True,       # (nonkyc) drop paused/inactive markets
        max_stale_days=7,         # last bar older than this => flagged stale, no WF
        # ---------------- history ----------------
        history_source="mexc_first",  # "mexc_first" | "native_only"
        years=2.0,                # analysis window (sliced from whatever is fetched)
        min_days=60,              # need at least this many bars to screen at all
        full_days=300,            # fewer than this => tier "young" (no 12mo claims)
        proxy_price_tol=0.05,     # reject proxy history if last close is off by >5%
        cache_dir="_ladder_cache",
        cache_ttl_hours=12.0,
        mexc_workers=8,
        nonkyc_workers=2,
        kraken_sleep=1.0,         # Kraken public API: ~1 call/sec sustained
        nonkyc_sleep=0.6,
        nonkyc_timeout=35,
        # ---------------- economics ----------------
        fee=0.0025 if exchange == "kraken" else 0.002,   # maker, base tier
        fund_usd=1000.0,
        quote_frac=0.5,
        # ---------------- placement ----------------
        months=6,                 # band-fit window
        n_side=5,                 # 5 buys + 5 sells at placement
        band_pctl=(5, 95),
        outlier_method="mad",     # "mad" | "iqr" | "none"
        outlier_k=3.5,
        cap_to_current=2.0,       # clamp band to [cur/x, cur*x]; None = off
        anchor="median3",         # "current" | "median3" | "median7" | "median" | "midpoint"
        anchor_warn_pct=2.0,
        spacing="arith",          # "arith" | "geom" (equal %-gap rungs)
        # ---------------- durability ----------------
        n_quarters=4,
        min_side=2,
        min_two_sided_q=3,
        # ---------------- band optimizer ----------------
        n_buy=5,
        n_sell=7,
        down_range=(0.03, 0.45),
        up_range=(0.03, 0.45),
        coarse_n=30,
        fine_n=44,
        plateau_frac=0.05,
        end_low=10.0,
        end_high=75.0,
        min_valid_bands=20,       # fewer valid coarse bands than this => fragile optimum

        # ---------------- weight optimizer ----------------
        weight_mode="shape",      # "shape" (robust, default) | "free" | "fill_proportional" | "equal"
        min_weight_frac=0.10,
        k_range=(-2.0, 4.0),
        k_n=17,
        free_passes=5,
        free_factors=(0.5, 0.7, 1.3, 1.8),
        # ---------------- walk-forward (validates the DEPLOYED config) ----------------
        wf_folds=3,
        wf_test_days=91,
        wf_min_train_days=270,
        wf_optimize_band=True,    # per-fold band optimize on train only
        wf_coarse_n=22,           # coarse-only per fold (keeps no-numba runtime sane)
        wf_min_pos_folds=2,       # OOS PnL > 0 in at least this many folds
        wf_min_two_sided_folds=2, # both sides filled OOS in at least this many folds
        wf_min_med_ann=0.0,       # median OOS annualized % must exceed this
        wf_top_n=40,              # WF the top-N by composite (plus all old-style qualifiers)
        wf_max_candidates=60,
        # ---------------- conservative stress ----------------
        max_fills_per_bar=1,
        rearm_cooldown=1,
        slip_floor=0.001,         # per-fill slip = max(slip_floor, measured_spread/2)
        body_only=False,
        cons_min_retained=50.0,
        cons_require_beat_hold=True,
        # ---------------- deploy gates / sizing ----------------
        profit_threshold=15.0,    # in-sample 12mo % (triage only; WF is the real gate)
        max_endinv_pct=70.0,
        accumulate_ok={"XMR", "SAL", "SOL"},
        min_rung_gap_mult=2.0,    # min avg rung gap = mult * round-trip fee
        min_depth_2pct=1000.0,
        vol_fraction=0.02,
        depth_fraction=0.5,
        depth_band=0.02,
        fund_floor=200,
        fund_ceil=10000,
        # ---------------- hourly fill-realism check ----------------
        hourly_days=180,          # MEXC-backed pairs; native-only pairs get less
        hourly_warn_ratio=0.5,    # hourly fills < 50% of daily-sim fills => warn
        # ---------------- nonkyc extras ----------------
        divergence_days=30,
        divergence_warn_pct=1.5,
    )
    return cfg


def _rt_fee_pct(cfg):
    """Round-trip fee in percent (2x maker)."""
    return 2.0 * cfg["fee"] * 100.0


# ======================================================================
# HTTP + cache
# ======================================================================
def _get_json(url, params=None, timeout=25, retries=2, backoff=0.7):
    for a in range(retries + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        if a < retries:
            time.sleep(backoff * (a + 1))
    return None


class CandleCache:
    """One .npz per (source, symbol, interval). Bars are Nx5 [ts_sec,o,h,l,c]."""

    def __init__(self, cache_dir, ttl_hours):
        self.dir = cache_dir
        self.ttl = ttl_hours * 3600.0
        os.makedirs(cache_dir, exist_ok=True)

    def _path(self, key):
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", key)
        return os.path.join(self.dir, safe + ".npz")

    def get(self, key):
        p = self._path(key)
        try:
            if not os.path.exists(p):
                return None
            if time.time() - os.path.getmtime(p) > self.ttl:
                return None
            with np.load(p) as z:
                return z["bars"]
        except Exception:
            return None

    def put(self, key, bars):
        try:
            np.savez_compressed(self._path(key), bars=np.asarray(bars, float))
        except Exception:
            pass


# ======================================================================
# Bars helpers  (bars = Nx5 float [ts_sec, o, h, l, c])
# ======================================================================
def slice_days(bars, days):
    """Last `days` of data, measured from the LAST BAR's timestamp (not wall clock)."""
    if bars is None or len(bars) == 0:
        return bars
    cut = bars[-1, 0] - float(days) * 86400.0
    return bars[bars[:, 0] >= cut]


def closes(bars):
    return bars[:, 4]


def bar_age_days(bars):
    if bars is None or len(bars) == 0:
        return float("inf")
    return (time.time() - float(bars[-1, 0])) / 86400.0


# ======================================================================
# Exchange adapters -- MEXC (history proxy)
# ======================================================================
MEXC_COIN_ALIAS = {"XBT": "BTC", "XDG": "DOGE"}


def mexc_symbol(coin, quote):
    c = MEXC_COIN_ALIAS.get(coin.upper(), coin.upper())
    q = MEXC_COIN_ALIAS.get(quote.upper(), quote.upper())
    return f"{c}{q}"


def mexc_klines(symbol, interval="1d", days=730, limit=1000):
    """Paginated MEXC klines -> Nx5 bars, oldest first. None on failure/empty.
    MEXC serves at most ~500 rows/request regardless of `limit`, so paginate until
    the last bar reaches `end` (a short page does NOT mean the data is exhausted)."""
    end = int(time.time() * 1000)
    start = end - int(days) * 86400 * 1000
    iv_ms = {"1d": 86400000, "60m": 3600000, "4h": 14400000}.get(interval, 86400000)
    seen = {}
    cur = start
    for _ in range(200):  # hard stop
        k = _get_json(f"{MEXC}/klines",
                      params={"symbol": symbol, "interval": interval,
                              "startTime": cur, "endTime": end, "limit": limit},
                      timeout=20)
        if not isinstance(k, list) or not k:
            break
        for x in k:
            seen[int(x[0])] = x
        last_open = int(k[-1][0])
        if last_open >= end - iv_ms or last_open + 1 <= cur:
            break
        cur = last_open + 1
    if not seen:
        return None
    rows = [seen[t] for t in sorted(seen)]
    return np.array([[int(x[0]) / 1000.0, float(x[1]), float(x[2]),
                      float(x[3]), float(x[4])] for x in rows], float)


# ======================================================================
# Exchange adapters -- Kraken
# ======================================================================
_KR_PAIRS = None


def kraken_asset_pairs():
    """AssetPairs keyed by 'BASE/QUOTE' + reverse map for ticker keys (cached)."""
    global _KR_PAIRS
    if _KR_PAIRS is not None:
        return _KR_PAIRS
    pairs, alt2key = {}, {}
    res = (_get_json(f"{KRAKEN}/AssetPairs", timeout=30) or {}).get("result", {})
    for pid, info in res.items():
        ws = info.get("wsname", "")
        if "/" not in ws:
            continue
        coin, quote = ws.split("/")
        alt = info.get("altname", pid)
        key = f"{coin.upper()}/{quote.upper()}"
        try:
            omin = float(info.get("ordermin", "nan"))
        except Exception:
            omin = float("nan")
        try:
            pdec = int(info.get("pair_decimals"))
        except Exception:
            pdec = None
        pairs[key] = dict(altname=alt, coin=coin.upper(), quote=quote.upper(),
                          ordermin=omin, pdec=pdec)
        for k in (pid, alt, ws):
            alt2key[k] = key
    _KR_PAIRS = (pairs, alt2key)
    return _KR_PAIRS


def kraken_ohlc_native(altname, interval=1440, days=730, sleep=1.0):
    """Kraken OHLC -> Nx5 bars. Capped at the 720 most recent candles per interval."""
    since = int(time.time()) - int(days) * 86400
    for _ in range(2):
        r = _get_json(f"{KRAKEN}/OHLC",
                      params={"pair": altname, "interval": interval, "since": since},
                      timeout=30)
        if r is not None and not r.get("error"):
            rows = next((v for k, v in r.get("result", {}).items() if k != "last"), None)
            if not rows:
                return None
            return np.array([[float(x[0]), float(x[1]), float(x[2]),
                              float(x[3]), float(x[4])] for x in rows], float)
        time.sleep(sleep)
    return None


def _build_usd_per_quote_kraken(quotes, last_by_key,
                                stables=("USD", "USDT", "USDC", "DAI", "PYUSD",
                                         "USDG", "TUSD", "USDR", "RLUSD", "ZUSD"),
                                hubs=("XBT", "ETH")):
    rate, route = {}, {}
    stables = set(stables)

    def last(b, q):
        v = last_by_key.get(f"{b}/{q}")
        return v[0] if v else None

    for q in quotes:
        if q in stables:
            rate[q], route[q] = 1.0, "peg"
    for q in quotes:
        if q in rate:
            continue
        for s in ("USD", "USDT", "USDC"):
            v = last(q, s)
            if v:
                rate[q], route[q] = v, f"{q}/{s}"
                break
        else:
            for s in ("USD", "USDT", "USDC"):
                v = last(s, q)
                if v:
                    rate[q], route[q] = 1.0 / v, f"{s}/{q} inv"
                    break
    for q in quotes:
        if q in rate:
            continue
        for hub in hubs:
            hr = rate.get(hub)
            if hr is None or hr != hr:
                continue
            v = last(q, hub)
            if v:
                rate[q], route[q] = v * hr, f"{q}/{hub} via {hub}"
                break
            v = last(hub, q)
            if v:
                rate[q], route[q] = hr / v, f"{hub}/{q} inv via {hub}"
                break
    for q in quotes:
        rate.setdefault(q, float("nan"))
        route.setdefault(q, "none")
    return rate, route


def kraken_universe(cfg):
    pairs, alt2key = kraken_asset_pairs()
    if not pairs:
        raise RuntimeError("Kraken AssetPairs returned nothing -- API down or blocked.")
    alts = sorted({p["altname"] for p in pairs.values()})
    last_by_key = {}
    for i in range(0, len(alts), 100):
        res = (_get_json(f"{KRAKEN}/Ticker",
                         params={"pair": ",".join(alts[i:i + 100])}, timeout=30) or {}).get("result", {})
        for tkey, t in res.items():
            pk = alt2key.get(tkey)
            if not pk:
                continue
            try:
                last_by_key[pk] = (float(t["c"][0]), float(t["v"][1]))
            except Exception:
                continue
        time.sleep(0.3)
    quotes = sorted({p["quote"] for p in pairs.values()})
    usd_per_quote, route = _build_usd_per_quote_kraken(quotes, last_by_key)
    want = None if cfg["quotes"] is None else {q.upper() for q in cfg["quotes"]}
    rows = []
    for pk, info in pairs.items():
        if want is not None and info["quote"] not in want:
            continue
        lv = last_by_key.get(pk)
        if not lv:
            continue
        last, vol24 = lv
        rate = usd_per_quote.get(info["quote"], float("nan"))
        if cfg["require_usd_rate"] and not (rate == rate):
            continue
        rows.append(dict(pairkey=pk, coin=info["coin"], quote=info["quote"], last=last,
                         vol_usd=vol24 * last * (rate if rate == rate else float("nan")),
                         min_qty=info["ordermin"], pdec=info["pdec"], active=True))
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No Kraken pairs survived (check quotes/require_usd_rate).")
    df = df[df.vol_usd.fillna(0) >= cfg["min_vol_usd"]]
    df = df.sort_values("vol_usd", ascending=False).reset_index(drop=True)
    if cfg["max_scan"]:
        df = df.head(int(cfg["max_scan"])).reset_index(drop=True)
    uni = dict(exchange="kraken", df=df, usd_per_quote=usd_per_quote, route=route,
               quote_of=dict(zip(df.pairkey, df.quote)),
               base_of=dict(zip(df.pairkey, df.coin)),
               last_of=dict(zip(df.pairkey, df["last"])),
               min_qty=dict(zip(df.pairkey, df.min_qty)),
               pdec=dict(zip(df.pairkey, df.pdec)),
               pair_alt={pk: pairs[pk]["altname"] for pk in df.pairkey})
    _print_universe(uni, cfg)
    return uni


def kraken_depth(uni, pairkey, band_pct=0.02):
    """(spread_pct, depth_usd within +/-band) on Kraken's book; (nan, nan) on failure."""
    alt = uni["pair_alt"].get(pairkey)
    res = (_get_json(f"{KRAKEN}/Depth", params={"pair": alt, "count": 500}, timeout=20)
           or {}).get("result", {})
    book = next(iter(res.values()), None) if res else None
    return _depth_from_book(uni, pairkey, book, band_pct)


# ======================================================================
# Exchange adapters -- NonKYC
# ======================================================================
def _fnum(x):
    try:
        return float(x)
    except Exception:
        return float("nan")


def nonkyc_universe(cfg):
    ml = _get_json(f"{NONKYC}/market/getlist", timeout=30)
    if isinstance(ml, dict):
        ml = ml.get("data", ml.get("markets", []))
    if not ml:
        raise RuntimeError("NonKYC /market/getlist returned nothing.")
    recs, last_by_pair = [], {}
    for m in ml:
        sym = str(m.get("symbol", ""))
        if "/" not in sym:
            continue
        coin, quote = sym.upper().split("/", 1)
        last = _fnum(m.get("lastPriceNumber", m.get("lastPrice")))
        vbase = _fnum(m.get("volumeNumber", m.get("volume")))
        vusd = _fnum(m.get("volumeUsdNumber", float("nan")))
        active = (bool(m.get("isActive", True)) and not bool(m.get("isPaused", False))
                  and not (bool(m.get("pauseBuys", False)) and bool(m.get("pauseSells", False))))
        try:
            pdec = int(m.get("priceDecimals")) if m.get("priceDecimals") is not None else None
        except Exception:
            pdec = None
        last_by_pair[f"{coin}/{quote}"] = last if last == last else None
        recs.append(dict(pairkey=f"{coin}/{quote}", coin=coin, quote=quote, last=last,
                         vbase=vbase, vusd=vusd, active=active,
                         min_qty=_fnum(m.get("minimumQuantity", "nan")), pdec=pdec))
    quotes = sorted({r["quote"] for r in recs})
    stables = {"USD", "USDT", "USDC", "DAI", "PYUSD", "USDG", "TUSD", "RLUSD",
               "BUSD", "USDP", "FUSD", "ZSD"}
    rate, route = {"USDT": 1.0}, {"USDT": "ref(USD~USDT)"}

    def last(b, q):
        v = last_by_pair.get(f"{b}/{q}")
        return v if (v is not None and v == v) else None

    for q in quotes:
        if q in rate:
            continue
        v = last(q, "USDT")
        if v:
            rate[q], route[q] = v, f"{q}/USDT"
    for q in quotes:
        if q in rate:
            continue
        uc = rate.get("USDC")
        if uc:
            v = last(q, "USDC")
            if v:
                rate[q], route[q] = v * uc, f"{q}/USDC"
    for q in quotes:
        if q in rate:
            continue
        v = last("USDT", q)
        if v:
            rate[q], route[q] = 1.0 / v, f"USDT/{q} inv"
    for q in quotes:
        if q in rate:
            continue
        if q in stables:
            rate[q], route[q] = 1.0, "peg($1)"
    for q in quotes:
        if q in rate:
            continue
        for hub in ("BTC", "ETH"):
            hr = rate.get(hub)
            if not hr or hr != hr:
                continue
            v = last(q, hub)
            if v:
                rate[q], route[q] = v * hr, f"{q}/{hub} via {hub}"
                break
            v = last(hub, q)
            if v:
                rate[q], route[q] = hr / v, f"{hub}/{q} inv via {hub}"
                break
    for q in quotes:
        rate.setdefault(q, float("nan"))
        route.setdefault(q, "none")

    want = None if cfg["quotes"] is None else {q.upper() for q in cfg["quotes"]}
    rows = []
    for r in recs:
        if want is not None and r["quote"] not in want:
            continue
        if cfg["skip_inactive"] and not r["active"]:
            continue
        rr = rate.get(r["quote"], float("nan"))
        if cfg["require_usd_rate"] and not (rr == rr):
            continue
        vol_usd = r["vusd"]
        if not (vol_usd == vol_usd):
            vol_usd = (r["vbase"] * r["last"] * rr
                       if (r["vbase"] == r["vbase"] and r["last"] == r["last"] and rr == rr)
                       else float("nan"))
        rows.append(dict(pairkey=r["pairkey"], coin=r["coin"], quote=r["quote"],
                         last=r["last"], vol_usd=vol_usd, min_qty=r["min_qty"],
                         pdec=r["pdec"], active=r["active"]))
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No NonKYC markets parsed (check quotes/require_usd_rate).")
    df = df[df.vol_usd.fillna(0) >= cfg["min_vol_usd"]]
    df = df.sort_values("vol_usd", ascending=False).reset_index(drop=True)
    if cfg["max_scan"]:
        df = df.head(int(cfg["max_scan"])).reset_index(drop=True)
    uni = dict(exchange="nonkyc", df=df, usd_per_quote=rate, route=route,
               quote_of=dict(zip(df.pairkey, df.quote)),
               base_of=dict(zip(df.pairkey, df.coin)),
               last_of=dict(zip(df.pairkey, df["last"])),
               min_qty=dict(zip(df.pairkey, df.min_qty)),
               pdec=dict(zip(df.pairkey, df.pdec)),
               pair_alt={})
    _print_universe(uni, cfg)
    return uni


def nonkyc_ohlc_native(coin, quote, resolution="1440", days=730,
                       timeout=35, sleep=0.6, retries=3):
    to_ = int(time.time())
    frm = to_ - int(days) * 86400
    for a in range(retries):
        try:
            r = requests.get(f"{NONKYC}/market/candles",
                             params={"symbol": f"{coin}/{quote}", "resolution": resolution,
                                     "from": frm, "to": to_}, timeout=timeout)
            if r.status_code == 200:
                bars = r.json().get("bars", [])
                if not bars:
                    return None
                out = []
                for i, b in enumerate(bars):
                    ts = b.get("time", b.get("timestamp", b.get("t")))
                    ts = float(ts) if ts is not None else float("nan")
                    if ts == ts and ts > 1e12:   # ms -> s
                        ts /= 1000.0
                    out.append([ts, float(b["open"]), float(b["high"]),
                                float(b["low"]), float(b["close"])])
                arr = np.array(out, float)
                if np.isnan(arr[:, 0]).any():   # no timestamps -> synthesize daily grid
                    step = 86400.0 if resolution == "1440" else float(resolution) * 60.0
                    n = len(arr)
                    arr[:, 0] = to_ - step * np.arange(n - 1, -1, -1)
                return arr
        except Exception:
            pass
        time.sleep(sleep * (a + 1))
    return None


def nonkyc_depth(uni, pairkey, band_pct=0.02):
    coin, quote = pairkey.split("/", 1)
    ob = _get_json(f"{NONKYC}/market/orderbook", params={"symbol": f"{coin}/{quote}"},
                   timeout=20)
    return _depth_from_book(uni, pairkey, ob, band_pct)


def _depth_from_book(uni, pairkey, book, band_pct):
    try:
        def lv(x):
            if isinstance(x, dict):
                return (float(x.get("price", x.get("p", 0))),
                        float(x.get("quantity", x.get("q", x.get("amount", 0)))))
            return float(x[0]), float(x[1])

        bids = [lv(x) for x in book.get("bids", [])]
        asks = [lv(x) for x in book.get("asks", [])]
        if not bids or not asks:
            return float("nan"), float("nan")
        bb = max(p for p, _ in bids)
        ba = min(p for p, _ in asks)
        mid = (bb + ba) / 2
        lo, hi = mid * (1 - band_pct), mid * (1 + band_pct)
        rate = usd_rate_of(uni, pairkey)
        depth = (sum(p * q for p, q in bids if p >= lo)
                 + sum(p * q for p, q in asks if p <= hi)) * rate
        return (ba - bb) / mid * 100.0, depth
    except Exception:
        return float("nan"), float("nan")


def depth_info(uni, pairkey, band_pct=0.02):
    if uni["exchange"] == "kraken":
        return kraken_depth(uni, pairkey, band_pct)
    return nonkyc_depth(uni, pairkey, band_pct)


def usd_rate_of(uni, pairkey):
    q = uni["quote_of"].get(pairkey)
    r = uni["usd_per_quote"].get(q, 1.0)
    return r if r == r else 1.0


def _print_universe(uni, cfg):
    df = uni["df"]
    byq = df.quote.value_counts()
    _log(f"{len(df)} {uni['exchange']} markets across {df.quote.nunique()} quote(s)"
         f" >= ${cfg['min_vol_usd']:,.0f} 24h vol (USD-equiv).")
    _log("  by quote: " + ", ".join(f"{q}:{byq[q]}" for q in byq.index))


# ======================================================================
# History layer (MEXC-first + native fallback + price guard + cache)
# ======================================================================
def _native_daily(uni, pairkey, cfg):
    coin, quote = uni["base_of"][pairkey], uni["quote_of"][pairkey]
    if uni["exchange"] == "kraken":
        bars = kraken_ohlc_native(uni["pair_alt"].get(pairkey, pairkey.replace("/", "")),
                                  1440, int(cfg["years"] * 365) + 30, cfg["kraken_sleep"])
        time.sleep(cfg["kraken_sleep"])
        return bars
    return nonkyc_ohlc_native(coin, quote, "1440", int(cfg["years"] * 365) + 30,
                              cfg["nonkyc_timeout"], cfg["nonkyc_sleep"])


def _proxy_ok(uni, pairkey, bars, cfg):
    """Reject proxy history when its last close disagrees with the native ticker."""
    ref = uni["last_of"].get(pairkey)
    if ref is None or not (ref == ref) or ref <= 0 or bars is None or not len(bars):
        return True
    return abs(bars[-1, 4] - ref) / ref <= cfg["proxy_price_tol"]


def fetch_daily(uni, pairkey, cfg, cache):
    """(bars Nx5, src) for a market. MEXC exact-pair proxy first (guarded), then native."""
    coin, quote = uni["base_of"][pairkey], uni["quote_of"][pairkey]
    if cfg["history_source"] == "mexc_first":
        key = f"mexc_{mexc_symbol(coin, quote)}_1d"
        bars = cache.get(key)
        if bars is None:
            bars = mexc_klines(mexc_symbol(coin, quote), "1d",
                               int(cfg["years"] * 365) + 30)
            if bars is not None:
                cache.put(key, bars)
        if bars is not None and len(bars) >= cfg["min_days"] and _proxy_ok(uni, pairkey, bars, cfg):
            return bars, "MEXC"
    key = f"{uni['exchange']}_{pairkey}_1d"
    bars = cache.get(key)
    if bars is None:
        bars = _native_daily(uni, pairkey, cfg)
        if bars is not None:
            cache.put(key, bars)
    if bars is not None and len(bars) >= cfg["min_days"]:
        return bars, uni["exchange"].capitalize() if uni["exchange"] == "kraken" else "NonKYC"
    return None, None


def prefetch_history(uni, cfg, cache=None, pairs=None):
    """Parallel MEXC pass, then native fallback (Kraken serial ~1/s; NonKYC small pool).
    Returns {pairkey: {'bars': Nx5, 'src': str}}; misses are absent."""
    cache = cache or CandleCache(cfg["cache_dir"], cfg["cache_ttl_hours"])
    pairs = list(pairs if pairs is not None else uni["df"].pairkey)
    t0 = time.time()
    hist, need_native = {}, []

    if cfg["history_source"] == "mexc_first":
        def try_mexc(pk):
            coin, quote = uni["base_of"][pk], uni["quote_of"][pk]
            key = f"mexc_{mexc_symbol(coin, quote)}_1d"
            bars = cache.get(key)
            if bars is None:
                bars = mexc_klines(mexc_symbol(coin, quote), "1d",
                                   int(cfg["years"] * 365) + 30)
                if bars is not None:
                    cache.put(key, bars)
            if bars is not None and len(bars) >= cfg["min_days"] and _proxy_ok(uni, pk, bars, cfg):
                return pk, bars
            return pk, None

        with _fut.ThreadPoolExecutor(max_workers=cfg["mexc_workers"]) as ex:
            done = 0
            for pk, bars in ex.map(try_mexc, pairs):
                done += 1
                if bars is not None:
                    hist[pk] = dict(bars=bars, src="MEXC")
                else:
                    need_native.append(pk)
                if done % 50 == 0:
                    _log(f"  ...MEXC pass {done}/{len(pairs)}")
    else:
        need_native = pairs

    if need_native:
        _log(f"  native fallback for {len(need_native)} markets "
             f"({'serial ~1/s' if uni['exchange'] == 'kraken' else 'small pool'}) ...")
        src_name = "Kraken" if uni["exchange"] == "kraken" else "NonKYC"
        if uni["exchange"] == "kraken":
            for j, pk in enumerate(need_native, 1):
                key = f"kraken_{pk}_1d"
                bars = cache.get(key)
                if bars is None:
                    bars = _native_daily(uni, pk, cfg)
                    if bars is not None:
                        cache.put(key, bars)
                if bars is not None and len(bars) >= cfg["min_days"]:
                    hist[pk] = dict(bars=bars, src=src_name)
                if j % 25 == 0:
                    _log(f"  ...native {j}/{len(need_native)}")
        else:
            def try_native(pk):
                key = f"nonkyc_{pk}_1d"
                bars = cache.get(key)
                if bars is None:
                    bars = _native_daily(uni, pk, cfg)
                    if bars is not None:
                        cache.put(key, bars)
                return pk, bars

            with _fut.ThreadPoolExecutor(max_workers=cfg["nonkyc_workers"]) as ex:
                for pk, bars in ex.map(try_native, need_native):
                    if bars is not None and len(bars) >= cfg["min_days"]:
                        hist[pk] = dict(bars=bars, src=src_name)

    n_mexc = sum(1 for v in hist.values() if v["src"] == "MEXC")
    _log(f"history: {len(hist)}/{len(pairs)} markets in {time.time() - t0:.0f}s "
         f"(MEXC {n_mexc}, native {len(hist) - n_mexc}, missing {len(pairs) - len(hist)})")
    return hist


def fetch_hourly(uni, pairkey, cfg, cache=None, src_hint=None):
    """Hourly bars for the fill-realism check. MEXC-backed pairs get cfg['hourly_days'];
    Kraken-native tops out at ~30d (720x1h cap); NonKYC-native is best-effort."""
    cache = cache or CandleCache(cfg["cache_dir"], cfg["cache_ttl_hours"])
    coin, quote = uni["base_of"][pairkey], uni["quote_of"][pairkey]
    if src_hint == "MEXC" or cfg["history_source"] == "mexc_first":
        key = f"mexc_{mexc_symbol(coin, quote)}_60m"
        bars = cache.get(key)
        if bars is None:
            bars = mexc_klines(mexc_symbol(coin, quote), "60m", cfg["hourly_days"])
            if bars is not None:
                cache.put(key, bars)
        if bars is not None and len(bars) >= 24 * 7 and _proxy_ok(uni, pairkey, bars, cfg):
            return bars, "MEXC"
    if uni["exchange"] == "kraken":
        key = f"kraken_{pairkey}_60m"
        bars = cache.get(key)
        if bars is None:
            bars = kraken_ohlc_native(uni["pair_alt"].get(pairkey), 60, 31, cfg["kraken_sleep"])
            time.sleep(cfg["kraken_sleep"])
            if bars is not None:
                cache.put(key, bars)
        if bars is not None and len(bars) >= 24 * 7:
            return bars, "Kraken(30d)"
    else:
        key = f"nonkyc_{pairkey}_60m"
        bars = cache.get(key)
        if bars is None:
            bars = nonkyc_ohlc_native(coin, quote, "60", cfg["hourly_days"],
                                      cfg["nonkyc_timeout"], cfg["nonkyc_sleep"])
            if bars is not None:
                cache.put(key, bars)
        if bars is not None and len(bars) >= 24 * 7:
            return bars, "NonKYC"
    return None, None


# ======================================================================
# Screener metrics
# ======================================================================
def _hurst(logc):
    """Hurst exponent via std-of-differences scaling. ~0.5 random, <0.5 mean-reverting."""
    n = len(logc)
    if n < 100:
        return float("nan")
    lags = np.arange(2, min(21, n // 4))
    tau = np.array([np.std(logc[lag:] - logc[:-lag]) for lag in lags])
    if (tau <= 0).any():
        return float("nan")
    return float(np.polyfit(np.log(lags), np.log(tau), 1)[0])


def _half_life(logc):
    """OU half-life in days from an AR(1) fit on log price. inf if not mean-reverting."""
    if len(logc) < 60:
        return float("nan")
    x = logc[:-1]
    y = np.diff(logc)
    xc = x - x.mean()
    den = float(np.sum(xc * xc))
    if den <= 0:
        return float("nan")
    beta = float(np.sum(xc * (y - y.mean())) / den)
    if beta >= 0:
        return float("inf")
    return float(-math.log(2.0) / beta)


def grid_metrics(c):
    """Original grid metrics + mean-reversion features. c = close array."""
    c = np.asarray(c, float)
    c = c[c > 0]
    n = len(c)
    years = n / 365.0
    lc = np.log(c)
    ann_vol = float(np.std(np.diff(lc)) * math.sqrt(365))
    net_return = float(c[-1] / c[0] - 1)
    path = float(np.sum(np.abs(np.diff(c))))
    net_move = abs(float(c[-1] - c[0]))
    er = float(net_move / path) if path > 0 else 1.0
    med = pd.Series(c).rolling(30, min_periods=10).median().to_numpy()
    s = np.sign((c - med)[~np.isnan(c - med)])
    s = s[s != 0]
    crossings = int(np.sum(s[1:] * s[:-1] < 0)) if len(s) > 1 else 0
    cross_per_yr = crossings / years if years > 0 else 0.0
    p5, p95, p20, p80 = np.percentile(c, [5, 95, 20, 80])
    in_band = float(np.mean((c >= p20) & (c <= p80)))
    cur_vs_high = float(c[-1] / np.max(c))
    survival = float(np.clip(cur_vs_high / 0.15, 0, 1))
    grid_score = cross_per_yr * (min(ann_vol, 2.0) * 100) * (1 - er) * survival
    vol_recent = (float(np.std(np.diff(lc[-31:])) * math.sqrt(365))
                  if n >= 40 else float("nan"))
    return dict(days=n, price=float(c[-1]), low=float(p5), high=float(p95),
                ann_vol=ann_vol, er=er, cross_per_yr=cross_per_yr, in_band=in_band,
                net_return=net_return, cur_vs_high=cur_vs_high, survival=survival,
                grid_score=grid_score,
                hurst=_hurst(lc), halflife_d=_half_life(lc),
                vol_ratio=(vol_recent / ann_vol if ann_vol > 0 else float("nan")))


def screen(uni, hist, cfg):
    """Metrics for EVERY market with history. `qualifies` is an annotation, not a filter."""
    rows = []
    for pk, h in hist.items():
        bars = slice_days(h["bars"], int(cfg["years"] * 365))
        if len(bars) < cfg["min_days"]:
            continue
        m = grid_metrics(closes(bars))
        m.update(base=pk, coin=uni["base_of"][pk], quote=uni["quote_of"][pk],
                 src=h["src"], vol_usd=float(uni["df"].set_index("pairkey").vol_usd.get(pk, float("nan"))),
                 min_qty=uni["min_qty"].get(pk, float("nan")),
                 stale=bar_age_days(bars) > cfg["max_stale_days"],
                 tier="full" if m["days"] >= cfg["full_days"] else "young")
        rows.append(m)
    d = pd.DataFrame(rows)
    if d.empty:
        raise RuntimeError("Screener produced no rows -- no market had enough history.")
    d["range_x"] = (d.high / d.low).round(2)
    d["qualifies"] = ((d.cross_per_yr >= 4) & (d.er <= 0.35)
                      & (d.ann_vol >= 0.5) & (d.survival >= 0.8))
    r_gs = d.grid_score.rank(pct=True)
    r_h = (-d.hurst).rank(pct=True).fillna(0.5)
    hl = d.halflife_d.replace(np.inf, 200).clip(upper=200).fillna(200)
    r_hl = (-hl).rank(pct=True)
    d["composite"] = (0.5 * r_gs + 0.25 * r_h + 0.25 * r_hl).round(3)
    return d.sort_values("composite", ascending=False).reset_index(drop=True)


# ======================================================================
# Ladder construction
# ======================================================================
def rp(x):
    x = float(x)
    if x >= 1000:
        return round(x, 1)
    if x >= 100:
        return round(x, 2)
    if x >= 1:
        return round(x, 4)
    if x >= 0.01:
        return round(x, 6)
    return float(f"{x:.4g}")


def round_price(x, pdec=None):
    if pdec is not None and pdec == pdec:
        try:
            return round(float(x), int(pdec))
        except Exception:
            pass
    return rp(x)


def clean_closes(c, method="mad", k=3.5):
    c = np.asarray(c, float)
    if method == "mad":
        med = np.median(c)
        mad = np.median(np.abs(c - med))
        if mad == 0:
            return c, 0
        keep = np.abs(0.6745 * (c - med) / mad) <= k
    elif method == "iqr":
        q1, q3 = np.percentile(c, [25, 75])
        iqr = q3 - q1
        if iqr == 0:
            return c, 0
        keep = (c >= q1 - k * iqr) & (c <= q3 + k * iqr)
    else:
        return c, 0
    if keep.sum() < 10:
        return c, 0
    return c[keep], int((~keep).sum())


def compute_center(closes_raw, closes_clean, lo, hi, cfg, label="", quiet=False):
    cur = float(closes_raw[-1])
    opts = {"current": cur,
            "median3": float(np.median(closes_raw[-3:])),
            "median7": float(np.median(closes_raw[-7:])),
            "median": float(np.median(closes_clean)),
            "midpoint": float((lo + hi) / 2)}
    anchor = cfg["anchor"]
    if anchor not in opts:
        raise ValueError(f"anchor must be one of {list(opts)}, got {anchor!r}")
    center = opts[anchor]
    if not quiet and anchor in ("median3", "median7") and cur:
        div = abs(center - cur) / cur * 100
        if div > cfg["anchor_warn_pct"]:
            _log(f"  !! {label}: {anchor} anchor {center:,.6g} is {div:.1f}% off last "
                 f"close {cur:,.6g} -> trending, not ranging.")
    return center


def _spaced_levels(center, edge, n, spacing):
    """n levels from center toward edge (exclusive of center), arithmetic or geometric."""
    if spacing == "geom" and center > 0 and edge > 0:
        return [center * (edge / center) ** (k / n) for k in range(1, n + 1)]
    step = (edge - center) / n
    return [center + step * k for k in range(1, n + 1)]


def build_ladder(bars, cfg, pdec=None, label="", quiet=False):
    """Placement-cell ladder: outlier-cleaned percentile band, anchored center,
    n_side rungs each way, arithmetic or geometric spacing."""
    craw = closes(bars)
    cur = float(craw[-1])
    cc, n_removed = clean_closes(craw, cfg["outlier_method"], cfg["outlier_k"])
    lo, hi = np.percentile(cc, cfg["band_pctl"])
    if cfg["cap_to_current"]:
        hi = min(hi, cur * cfg["cap_to_current"])
        lo = max(lo, cur / cfg["cap_to_current"])
    center = compute_center(craw, cc, lo, hi, cfg, label, quiet)
    center = min(max(center, lo + (hi - lo) * 0.1), hi - (hi - lo) * 0.1)
    n = cfg["n_side"]
    buys = _spaced_levels(center, lo, n, cfg["spacing"])
    sells = _spaced_levels(center, hi, n, cfg["spacing"])

    def touches(level):
        return int(np.sum((bars[:, 3] <= level) & (level <= bars[:, 2])))

    return dict(lo=float(lo), hi=float(hi), center=float(center), cur=cur,
                n_removed=n_removed,
                buys=[round_price(p, pdec) for p in buys],
                sells=[round_price(p, pdec) for p in sells],
                buy_touch=[touches(p) for p in buys],
                sell_touch=[touches(p) for p in sells])


def avg_gap_pct(prices):
    p = sorted(float(x) for x in prices)
    gaps = [(p[i + 1] - p[i]) / p[i] * 100 for i in range(len(p) - 1)]
    return float(np.mean(gaps)) if gaps else 0.0


# ======================================================================
# Fill sim -- one kernel for everything
# ======================================================================
@_njit(cache=False)
def _sim_kernel(o, h, l, c, buys, sells, bw, sw, fund, qf, fee, slip,
                max_fills_per_bar, rearm_cooldown, body_only):
    n = c.shape[0]
    nb = buys.shape[0]
    ns = sells.shape[0]
    p0 = c[0]
    quote = fund * qf
    base = fund * (1.0 - qf) / p0
    sbw = 0.0
    for i in range(nb):
        sbw += bw[i]
    ssw = 0.0
    for i in range(ns):
        ssw += sw[i]
    buy_qty = np.empty(nb)
    sell_qty = np.empty(ns)
    for i in range(nb):
        buy_qty[i] = (fund * qf * bw[i] / sbw) / buys[i]
    for i in range(ns):
        sell_qty[i] = (fund * (1.0 - qf) / p0) * sw[i] / ssw
    b_arm = np.empty(nb, np.bool_)
    s_arm = np.empty(ns, np.bool_)
    for i in range(nb):
        b_arm[i] = p0 > buys[i]
    for i in range(ns):
        s_arm[i] = p0 < sells[i]
    cm = fee + slip
    bf = np.zeros(nb, np.int64)
    sf = np.zeros(ns, np.int64)
    b_last = np.full(nb, -1000000000, np.int64)
    s_last = np.full(ns, -1000000000, np.int64)
    cb = np.zeros(n, np.int64)
    cs = np.zeros(n, np.int64)
    eq = np.zeros(n)
    fees = 0.0
    nbt = 0
    nst = 0
    path = np.empty(4)
    for t in range(n):
        if body_only:
            plen = 2
            path[0] = o[t]
            path[1] = c[t]
        else:
            plen = 4
            path[0] = o[t]
            if c[t] >= o[t]:
                path[1] = l[t]
                path[2] = h[t]
            else:
                path[1] = h[t]
                path[2] = l[t]
            path[3] = c[t]
        fb = 0
        for s in range(plen - 1):
            a = path[s]
            b = path[s + 1]
            if b < a:
                for i in range(nb):
                    if fb >= max_fills_per_bar:
                        break
                    if (b_arm[i] and (t - b_last[i] > rearm_cooldown)
                            and (b <= buys[i]) and (buys[i] <= a)):
                        cost = buys[i] * buy_qty[i]
                        f = cost * cm
                        if quote >= cost + f:
                            quote -= cost + f
                            base += buy_qty[i]
                            fees += f
                            b_arm[i] = False
                            bf[i] += 1
                            b_last[i] = t
                            fb += 1
                            nbt += 1
            elif b > a:
                for i in range(ns):
                    if fb >= max_fills_per_bar:
                        break
                    if (s_arm[i] and (t - s_last[i] > rearm_cooldown)
                            and (a <= sells[i]) and (sells[i] <= b)
                            and (base >= sell_qty[i])):
                        proc = sells[i] * sell_qty[i]
                        f = proc * cm
                        quote += proc - f
                        base -= sell_qty[i]
                        fees += f
                        s_arm[i] = False
                        sf[i] += 1
                        s_last[i] = t
                        fb += 1
                        nst += 1
        for i in range(nb):
            if (not b_arm[i]) and c[t] > buys[i]:
                b_arm[i] = True
        for i in range(ns):
            if (not s_arm[i]) and c[t] < sells[i]:
                s_arm[i] = True
        cb[t] = nbt
        cs[t] = nst
        eq[t] = quote + base * c[t]
    return quote, base, fees, bf, sf, cb, cs, eq


def sim(bars, buys, sells, bw=None, sw=None, fund=1000.0, quote_frac=0.5, fee=0.002,
        slip=0.0, max_fills_per_bar=None, rearm_cooldown=0, body_only=False):
    """Passive-aware ladder sim. Defaults = optimistic backtest; dials = stress.
    bars: Nx4 [o,h,l,c] or Nx5 [ts,o,h,l,c]."""
    bars = np.asarray(bars, float)
    ohlc = bars[:, -4:]
    o = np.ascontiguousarray(ohlc[:, 0])
    h = np.ascontiguousarray(ohlc[:, 1])
    l = np.ascontiguousarray(ohlc[:, 2])
    c = np.ascontiguousarray(ohlc[:, 3])
    buys = np.asarray(buys, float)
    sells = np.asarray(sells, float)
    bw = np.ones(len(buys)) if bw is None else np.asarray(bw, float)
    sw = np.ones(len(sells)) if sw is None else np.asarray(sw, float)
    mfpb = np.int64(2 ** 62) if max_fills_per_bar is None else np.int64(max_fills_per_bar)
    quote, base, fees, bf, sf, cb, cs, eq = _sim_kernel(
        o, h, l, c, buys, sells, bw, sw, float(fund), float(quote_frac),
        float(fee), float(slip), mfpb, np.int64(rearm_cooldown), bool(body_only))
    last = c[-1]
    final = quote + base * last
    init = float(fund)
    hold = fund * quote_frac + (fund * (1 - quote_frac) / c[0]) * last
    peak = np.maximum.accumulate(eq)
    mdd = float(np.max((peak - eq) / np.where(peak > 0, peak, 1.0))) * 100
    lo_b, hi_s = float(np.min(buys)), float(np.max(sells))
    months = len(c) / 30.4
    trades = int(bf.sum() + sf.sum())
    return dict(pnl=final - init, pnl_pct=(final - init) / init * 100,
                hold_pct=(hold - init) / init * 100, maxdd=mdd,
                endinv=base * last / final * 100 if final else 0.0, fees=fees,
                trades=trades, bf=bf.tolist(), sf=sf.tolist(),
                cb=cb, cs=cs, eq=eq,
                time_in_band=float(np.mean((c >= lo_b) & (c <= hi_s))),
                trades_per_month=trades / months if months > 0 else 0.0)


def _sim_reference(bars, buys, sells, bw=None, sw=None, fund=1000.0, quote_frac=0.5,
                   fee=0.002, slip=0.0, max_fills_per_bar=None, rearm_cooldown=0,
                   body_only=False):
    """Direct pure-Python port of the original notebook sim (weights + stress dials).
    Kept only as the parity reference for the kernel."""
    bars = np.asarray(bars, float)[:, -4:]
    bw = [1.0] * len(buys) if bw is None else list(bw)
    sw = [1.0] * len(sells) if sw is None else list(sw)
    sbw, ssw = sum(bw), sum(sw)
    p0 = bars[0][3]
    quote = fund * quote_frac
    base = fund * (1 - quote_frac) / p0
    buy_qty = [(fund * quote_frac * bw[i] / sbw) / buys[i] for i in range(len(buys))]
    sell_qty = [(fund * (1 - quote_frac) / p0) * sw[i] / ssw for i in range(len(sells))]
    b_arm = [p0 > L for L in buys]
    s_arm = [p0 < L for L in sells]
    cm = fee + slip
    mfpb = 10 ** 18 if max_fills_per_bar is None else max_fills_per_bar
    bf = [0] * len(buys)
    sf = [0] * len(sells)
    b_last = [-10 ** 9] * len(buys)
    s_last = [-10 ** 9] * len(sells)
    fees = 0.0
    cb, cs, eq = [], [], []
    nbt = nst = 0
    for t, (o, h, l, c) in enumerate(bars):
        path = [o, c] if body_only else ([o, l, h, c] if c >= o else [o, h, l, c])
        fb = 0
        for a, b in zip(path, path[1:]):
            if b < a:
                for i, L in enumerate(buys):
                    if fb >= mfpb:
                        break
                    if b_arm[i] and (t - b_last[i] > rearm_cooldown) and b <= L <= a:
                        cost = L * buy_qty[i]
                        f = cost * cm
                        if quote >= cost + f:
                            quote -= cost + f
                            base += buy_qty[i]
                            fees += f
                            b_arm[i] = False
                            bf[i] += 1
                            b_last[i] = t
                            fb += 1
                            nbt += 1
            elif b > a:
                for i, L in enumerate(sells):
                    if fb >= mfpb:
                        break
                    if s_arm[i] and (t - s_last[i] > rearm_cooldown) and a <= L <= b \
                            and base >= sell_qty[i]:
                        proc = L * sell_qty[i]
                        f = proc * cm
                        quote += proc - f
                        base -= sell_qty[i]
                        fees += f
                        s_arm[i] = False
                        sf[i] += 1
                        s_last[i] = t
                        fb += 1
                        nst += 1
        for i, L in enumerate(buys):
            if not b_arm[i] and c > L:
                b_arm[i] = True
        for i, L in enumerate(sells):
            if not s_arm[i] and c < L:
                s_arm[i] = True
        cb.append(nbt)
        cs.append(nst)
        eq.append(quote + base * c)
    last = bars[-1][3]
    final = quote + base * last
    return dict(pnl=final - fund, bf=bf, sf=sf, cb=cb, cs=cs, eq=eq, fees=fees)


def parity_check(verbose=False, n_series=4, n_bars=400, seed=7):
    """Prove the jitted kernel == the original notebook sim, across dial combos.
    Pseudo-random walks are used purely as a code-equivalence test (pure math),
    not as market realism -- realism checks run on real bars in the notebooks."""
    rng = np.random.default_rng(seed)
    combos = [dict(), dict(max_fills_per_bar=1, rearm_cooldown=1, slip=0.001),
              dict(body_only=True), dict(bw=[3, 1, 1, 1, 2], sw=[1, 1, 4, 1, 1])]
    for si in range(n_series):
        lc = np.cumsum(rng.normal(0, 0.03, n_bars)) + math.log(50 + 100 * si)
        c = np.exp(lc)
        o = np.roll(c, 1)
        o[0] = c[0]
        spread = np.abs(rng.normal(0, 0.02, n_bars))
        h = np.maximum(o, c) * (1 + spread)
        l = np.minimum(o, c) * (1 - spread)
        bars = np.column_stack([np.arange(n_bars) * 86400.0, o, h, l, c])
        center = float(np.median(c))
        buys = [center * (1 - 0.05 * k) for k in range(1, 6)]
        sells = [center * (1 + 0.05 * k) for k in range(1, 6)]
        for combo in combos:
            a = sim(bars, buys, sells, fee=0.0025, **combo)
            b = _sim_reference(bars, buys, sells, fee=0.0025, **combo)
            ok = (abs(a["pnl"] - b["pnl"]) < 1e-6 and a["bf"] == b["bf"]
                  and a["sf"] == b["sf"] and abs(a["fees"] - b["fees"]) < 1e-6
                  and np.allclose(a["eq"], b["eq"]))
            if not ok:
                if verbose:
                    _log(f"parity FAIL series {si} combo {combo}: "
                         f"kernel pnl {a['pnl']:.4f} vs ref {b['pnl']:.4f}")
                return False
    if verbose:
        _log(f"sim parity OK ({n_series} series x {len(combos)} dial combos, "
             f"numba={'on' if HAVE_NUMBA else 'OFF -- pip install numba for speed'})")
    return True


# ======================================================================
# Durability
# ======================================================================
def quarter_split(cb, cs, eq, fund, nq=4, min_side=2):
    n = len(eq)
    eqf = np.concatenate([[fund], eq])
    cbf = np.concatenate([[0], cb])
    csf = np.concatenate([[0], cs])
    bnd = [round(n * k / nq) for k in range(nq + 1)]
    qb, qs, qp = [], [], []
    for q in range(nq):
        s, e = bnd[q], bnd[q + 1]
        qb.append(int(cbf[e] - cbf[s]))
        qs.append(int(csf[e] - csf[s]))
        qp.append(float(eqf[e] - eqf[s]))
    two_sided = sum(1 for i in range(nq) if qb[i] >= min_side and qs[i] >= min_side)
    total = (int(cb[-1]) + int(cs[-1])) or 1
    recent_pct = (qb[-1] + qs[-1]) / total * 100
    return two_sided, recent_pct, qb, qs, qp


# ======================================================================
# Band + weight optimizers
# ======================================================================
def _build_band(P, floor, ceil, n_buy, n_sell, spacing):
    return (_spaced_levels(P, floor, n_buy, spacing),
            _spaced_levels(P, ceil, n_sell, spacing))


def _eval_band(bars, P, floor, ceil, cfg):
    buys, sells = _build_band(P, floor, ceil, cfg["n_buy"], cfg["n_sell"], cfg["spacing"])
    r = sim(bars, buys, sells, fund=cfg["fund_usd"], quote_frac=cfg["quote_frac"],
            fee=cfg["fee"])
    two, _, _, _, qp = quarter_split(r["cb"], r["cs"], r["eq"], cfg["fund_usd"],
                                     cfg["n_quarters"], cfg["min_side"])
    valid = (two >= cfg["min_two_sided_q"]
             and cfg["end_low"] <= r["endinv"] <= cfg["end_high"])
    return dict(f=floor, c=ceil, pnl=r["pnl"], endinv=r["endinv"], two=two,
                qp=qp, valid=valid)


def compute_anchor(bars, cfg, label="", quiet=False):
    cl = closes(bars)
    last = float(cl[-1])
    mode = cfg["anchor"]
    if mode == "current":
        a = last
    elif mode == "median3":
        a = float(np.median(cl[-3:]))
    elif mode == "median7":
        a = float(np.median(cl[-7:]))
    else:
        a = float(np.median(cl[-3:]))
    if not quiet and last:
        div = abs(a - last) / last * 100
        if div > cfg["anchor_warn_pct"]:
            _log(f"  !! {label}: anchor {a:,.6g} is {div:.1f}% off last close "
                 f"{last:,.6g} -> trending, not ranging.")
    return a


def optimize_band(bars, P, cfg, coarse_n=None, fine_n=None, quiet=False):
    """Coarse -> plateau -> fine plateau-centre band search under durability +
    inventory constraints. Returns dict or None if nothing valid."""
    coarse_n = coarse_n or cfg["coarse_n"]
    fine_n = cfg["fine_n"] if fine_n is None else fine_n
    step = P * 0.001

    def grid(flo, fhi, clo, chi, n):
        out = []
        for f in np.linspace(flo, fhi, n):
            for cc in np.linspace(clo, chi, n):
                out.append(_eval_band(bars, P, f, cc, cfg))
        return out

    dr, ur = cfg["down_range"], cfg["up_range"]
    coarse = grid(P * (1 - dr[1]), P * (1 - dr[0]), P * (1 + ur[0]), P * (1 + ur[1]),
                  coarse_n)
    valid = [x for x in coarse if x["valid"]]
    if not valid:
        return None
    valid.sort(key=lambda x: x["pnl"], reverse=True)
    K = max(3, int(len(valid) * cfg["plateau_frac"]))
    plat = valid[:K]
    flo = min(x["f"] for x in plat)
    fhi = max(x["f"] for x in plat)
    clo = min(x["c"] for x in plat)
    chi = max(x["c"] for x in plat)
    if fine_n and fine_n > 0:
        pad_f = (fhi - flo) * 0.25 + step
        pad_c = (chi - clo) * 0.25 + step
        fine = grid(flo - pad_f, fhi + pad_f, clo - pad_c, chi + pad_c, fine_n)
        fvalid = [x for x in fine if x["valid"]] or valid
    else:
        fvalid = valid
    fvalid.sort(key=lambda x: x["pnl"], reverse=True)
    fK = max(3, int(len(fvalid) * cfg["plateau_frac"]))
    fplat = fvalid[:fK]
    rec_f = float(np.median([x["f"] for x in fplat]))
    rec_c = float(np.median([x["c"] for x in fplat]))
    rec = _eval_band(bars, P, rec_f, rec_c, cfg)
    buys, sells = _build_band(P, rec_f, rec_c, cfg["n_buy"], cfg["n_sell"], cfg["spacing"])
    return dict(P=P, rec_f=rec_f, rec_c=rec_c, buys=buys, sells=sells,
                pnl=rec["pnl"], endinv=rec["endinv"], two=rec["two"], qp=rec["qp"],
                peak_pnl=fvalid[0]["pnl"],
                plateau_fw=max(x["f"] for x in fplat) - min(x["f"] for x in fplat),
                plateau_cw=max(x["c"] for x in fplat) - min(x["c"] for x in fplat),
                n_valid=len(valid), n_total=len(coarse))


def _shape_w(n, k, floor):
    d = np.linspace(0, 1, n)
    w = np.exp(-k * d)
    w = w / w.max()
    return np.maximum(w, floor)


def optimize_weights(bars, buys, sells, cfg, mode=None):
    """Per-rung capital weights. Returns (bw, sw, sim_result, meta)."""
    mode = mode or cfg["weight_mode"]
    nb, ns = len(buys), len(sells)
    kw = dict(fund=cfg["fund_usd"], quote_frac=cfg["quote_frac"], fee=cfg["fee"])
    if mode == "equal":
        bw, sw = np.ones(nb), np.ones(ns)
        return bw, sw, sim(bars, buys, sells, bw, sw, **kw), "equal"
    if mode == "shape":
        best = None
        for kb in np.linspace(*cfg["k_range"], cfg["k_n"]):
            for ks in np.linspace(*cfg["k_range"], cfg["k_n"]):
                bw = _shape_w(nb, kb, cfg["min_weight_frac"])
                sw = _shape_w(ns, ks, cfg["min_weight_frac"])
                r = sim(bars, buys, sells, bw, sw, **kw)
                if r["endinv"] <= cfg["end_high"] and (best is None or r["pnl"] > best[0]):
                    best = (r["pnl"], bw, sw, r, (kb, ks))
        if best is None:
            bw, sw = np.ones(nb), np.ones(ns)
            return bw, sw, sim(bars, buys, sells, bw, sw, **kw), "equal(fallback)"
        _, bw, sw, r, kk = best
        return bw, sw, r, f"skew buy={kk[0]:+.2f} sell={kk[1]:+.2f}"
    if mode == "fill_proportional":
        r0 = sim(bars, buys, sells, **kw)
        bw = np.maximum([max(f, 0.5) for f in r0["bf"]], 0.5)
        sw = np.maximum([max(f, 0.5) for f in r0["sf"]], 0.5)
        bw = np.maximum(bw, cfg["min_weight_frac"] * bw.max())
        sw = np.maximum(sw, cfg["min_weight_frac"] * sw.max())
        return bw, sw, sim(bars, buys, sells, bw, sw, **kw), "weight ~ fills"
    # free coordinate ascent
    bw, sw = np.ones(nb), np.ones(ns)
    best_pnl = sim(bars, buys, sells, bw, sw, **kw)["pnl"]
    for _ in range(cfg["free_passes"]):
        for side in ("b", "s"):
            W = bw if side == "b" else sw
            for i in range(len(W)):
                for fac in cfg["free_factors"]:
                    trial = W.copy()
                    trial[i] = max(trial[i] * fac, cfg["min_weight_frac"] * trial.max())
                    tb, ts = (trial, sw) if side == "b" else (bw, trial)
                    r = sim(bars, buys, sells, tb, ts, **kw)
                    if r["pnl"] > best_pnl and r["endinv"] <= cfg["end_high"]:
                        best_pnl = r["pnl"]
                        if side == "b":
                            bw = trial
                        else:
                            sw = trial
    r = sim(bars, buys, sells, bw, sw, **kw)
    return bw, sw, r, "free per-rung"


def weights_pct(w):
    w = np.asarray(w, float)
    return [round(float(x), 1) for x in (w / w.sum() * 100)]


# ======================================================================
# In-sample evaluation (triage over the whole universe)
# ======================================================================
def evaluate_all(scr, hist, uni, cfg):
    """Placement + 12mo/3mo backtest + durability for EVERY screened market.
    In-sample only -- used to pick walk-forward candidates, not to deploy."""
    rows, ladders = [], {}
    kw = dict(fund=cfg["fund_usd"], quote_frac=cfg["quote_frac"], fee=cfg["fee"])
    for rec in scr.itertuples():
        pk = rec.base
        h = hist.get(pk)
        if h is None:
            continue
        bars = slice_days(h["bars"], int(cfg["years"] * 365))
        fit = slice_days(bars, int(cfg["months"] * 30.4))
        if len(fit) < 40:
            continue
        L = build_ladder(fit, cfg, uni["pdec"].get(pk), label=pk, quiet=True)
        ladders[pk] = dict(src=h["src"], coin=rec.coin, quote=rec.quote, **L)
        b12 = slice_days(bars, 365)
        b3 = slice_days(bars, 91)
        r12 = sim(b12, L["buys"], L["sells"], **kw)
        r3 = sim(b3, L["buys"], L["sells"], **kw)
        two, recent, qb, qs, qp = quarter_split(r12["cb"], r12["cs"], r12["eq"],
                                                cfg["fund_usd"], cfg["n_quarters"],
                                                cfg["min_side"])
        rows.append(dict(
            base=pk, coin=rec.coin, quote=rec.quote, src=h["src"], tier=rec.tier,
            stale=rec.stale, composite=rec.composite, qualifies=rec.qualifies,
            days=int(rec.days), p3=round(r3["pnl_pct"], 1),
            p12=round(r12["pnl_pct"], 1), p12_q=round(r12["pnl"], 1),
            hold12=round(r12["hold_pct"], 1), t12=r12["trades"],
            endinv=round(r12["endinv"], 0), two_sided=two,
            recent_pct=round(recent, 0),
            time_in_band=round(r12["time_in_band"], 2),
            trades_mo=round(r12["trades_per_month"], 1),
            gap_pct=round(avg_gap_pct(list(L["buys"]) + list(L["sells"])), 2),
            vol_usd=rec.vol_usd))
    d = pd.DataFrame(rows).sort_values("composite", ascending=False).reset_index(drop=True)
    return d, ladders


def pick_wf_candidates(ev, cfg):
    """Top-N by composite among viable markets, plus every old-style qualifier."""
    viable = ev[(~ev.stale) & (ev.tier == "full") & (ev.p12 > 0)]
    top = viable.head(cfg["wf_top_n"])
    qual = viable[viable.qualifies]
    cands = list(dict.fromkeys(list(top.base) + list(qual.base)))
    return cands[:cfg["wf_max_candidates"]]


# ======================================================================
# Walk-forward -- validates the DEPLOYED config, multi-fold
# ======================================================================
def _fit_deployed(train, cfg, pdec, label=""):
    """The full deploy pipeline on TRAIN ONLY: placement -> band opt -> weights."""
    L = build_ladder(train, cfg, pdec, label=label, quiet=True)
    buys, sells = list(map(float, L["buys"])), list(map(float, L["sells"]))
    note = "placement"
    if cfg["wf_optimize_band"]:
        P = compute_anchor(train, cfg, label, quiet=True)
        ob = optimize_band(train, P, cfg, coarse_n=cfg["wf_coarse_n"], fine_n=0)
        if ob is not None:
            buys, sells = ob["buys"], ob["sells"]
            note = "optimized"
    bw, sw, _, wmeta = optimize_weights(train, buys, sells, cfg)
    return buys, sells, bw, sw, f"{note}, {wmeta}"


def walkforward(bars, cfg, pdec=None, label=""):
    """Expanding-train / rolling-test folds. Each fold re-fits the deployed config
    on train only and scores it on the unseen test slice."""
    kw = dict(fund=cfg["fund_usd"], quote_frac=cfg["quote_frac"], fee=cfg["fee"])
    t_end = bars[-1, 0]
    folds = []
    for i in range(cfg["wf_folds"], 0, -1):
        test_hi = t_end - (i - 1) * cfg["wf_test_days"] * 86400.0
        test_lo = test_hi - cfg["wf_test_days"] * 86400.0
        train = bars[bars[:, 0] < test_lo]
        test = bars[(bars[:, 0] >= test_lo) & (bars[:, 0] < test_hi + 1)]
        if len(train) < cfg["wf_min_train_days"] or len(test) < cfg["wf_test_days"] * 0.6:
            continue
        buys, sells, bw, sw, note = _fit_deployed(train, cfg, pdec, label)
        r_tr = sim(train, buys, sells, bw, sw, **kw)
        r_te = sim(test, buys, sells, bw, sw, **kw)
        r_tc = sim(test, buys, sells, bw, sw,
                   max_fills_per_bar=cfg["max_fills_per_bar"],
                   rearm_cooldown=cfg["rearm_cooldown"], slip=cfg["slip_floor"],
                   body_only=cfg["body_only"], **kw)
        tr_days = max((train[-1, 0] - train[0, 0]) / 86400.0, 1)
        te_days = max((test[-1, 0] - test[0, 0]) / 86400.0, 1)
        tr_ann = r_tr["pnl_pct"] * 365 / tr_days
        te_ann = r_te["pnl_pct"] * 365 / te_days
        folds.append(dict(
            train_days=int(tr_days), test_days=int(te_days), note=note,
            train_ann=round(tr_ann, 1), test_pct=round(r_te["pnl_pct"], 2),
            test_ann=round(te_ann, 1),
            cons_ann=round(r_tc["pnl_pct"] * 365 / te_days, 1),
            test_hold=round(r_te["hold_pct"], 1),
            retained=round(te_ann / tr_ann * 100, 0) if tr_ann > 0 else float("nan"),
            b_fills=int(sum(r_te["bf"])), s_fills=int(sum(r_te["sf"])),
            two_sided=sum(r_te["bf"]) > 0 and sum(r_te["sf"]) > 0,
            endinv=round(r_te["endinv"], 0)))
    if not folds:
        return dict(folds=[], n_folds=0, wf_pass=None, note="insufficient history")
    pos = sum(1 for f in folds if f["test_pct"] > 0)
    two = sum(1 for f in folds if f["two_sided"])
    med_ann = float(np.median([f["test_ann"] for f in folds]))
    med_cons = float(np.median([f["cons_ann"] for f in folds]))
    rets = [f["retained"] for f in folds if f["retained"] == f["retained"]]
    wf_pass = (pos >= cfg["wf_min_pos_folds"] and two >= cfg["wf_min_two_sided_folds"]
               and med_ann > cfg["wf_min_med_ann"])
    return dict(folds=folds, n_folds=len(folds), pos_folds=pos, two_sided_folds=two,
                med_test_ann=round(med_ann, 1), med_cons_ann=round(med_cons, 1),
                med_retained=round(float(np.median(rets)), 0) if rets else float("nan"),
                wf_pass=bool(wf_pass))


def walkforward_all(cands, hist, uni, cfg):
    rows, details = [], {}
    t0 = time.time()
    for j, pk in enumerate(cands, 1):
        h = hist.get(pk)
        if h is None:
            continue
        bars = slice_days(h["bars"], int(cfg["years"] * 365))
        wf = walkforward(bars, cfg, uni["pdec"].get(pk), label=pk)
        details[pk] = wf
        if wf["n_folds"] == 0:
            continue
        rows.append(dict(base=pk, src=h["src"], folds=wf["n_folds"],
                         pos=wf["pos_folds"], two_sided=wf["two_sided_folds"],
                         med_test_ann=wf["med_test_ann"],
                         med_cons_ann=wf["med_cons_ann"],
                         med_retained=wf["med_retained"], wf_pass=wf["wf_pass"]))
        if j % 10 == 0:
            _log(f"  ...walk-forward {j}/{len(cands)} ({time.time() - t0:.0f}s)")
    d = (pd.DataFrame(rows).sort_values(["wf_pass", "med_cons_ann"], ascending=[False, False])
         .reset_index(drop=True)) if rows else pd.DataFrame()
    return d, details


# ======================================================================
# Deploy gates + sizing
# ======================================================================
def round_fund(x, cfg):
    x = max(float(cfg["fund_floor"]), min(float(x), float(cfg["fund_ceil"])))
    step = 100 if x < 1000 else (250 if x < 3000 else 500)
    return int(round(x / step) * step)


def min_qty_check(buys, sells, bw, sw, fund, cfg, min_qty, p0):
    """Does every rung's quantity clear the exchange minimum? Returns
    (ok, min_fund_needed)."""
    if min_qty is None or not (min_qty == min_qty) or min_qty <= 0:
        return True, 0.0
    bw = np.asarray(bw, float)
    sw = np.asarray(sw, float)
    need = 0.0
    for i, p in enumerate(buys):
        qty_per_fund = (cfg["quote_frac"] * bw[i] / bw.sum()) / p
        need = max(need, min_qty / qty_per_fund if qty_per_fund > 0 else float("inf"))
    for i, _ in enumerate(sells):
        qty_per_fund = ((1 - cfg["quote_frac"]) / p0) * sw[i] / sw.sum()
        need = max(need, min_qty / qty_per_fund if qty_per_fund > 0 else float("inf"))
    return fund >= need, need


def hourly_fill_check(uni, pk, buys, sells, bw, sw, cfg, cache, daily_bars,
                      src_hint=None):
    """Same frozen ladder on hourly bars vs DAILY bars over the SAME window.
    fill_ratio << 1 means the daily [o,l,h,c] path overstates fills."""
    hb, hsrc = fetch_hourly(uni, pk, cfg, cache, src_hint)
    if hb is None:
        return dict(hourly="n/a")
    kw = dict(fund=cfg["fund_usd"], quote_frac=cfg["quote_frac"], fee=cfg["fee"])
    rh = sim(hb, buys, sells, bw, sw, **kw)
    days = (hb[-1, 0] - hb[0, 0]) / 86400.0
    db = daily_bars[daily_bars[:, 0] >= hb[0, 0] - 43200.0]
    out = dict(hourly=hsrc, hourly_days=int(days), hr_trades=rh["trades"],
               hr_pnl_pct=round(rh["pnl_pct"], 1), fill_ratio=float("nan"))
    if len(db) >= 5:
        rd = sim(db, buys, sells, bw, sw, **kw)
        out["dly_trades_window"] = rd["trades"]
        if rd["trades"] > 0:
            out["fill_ratio"] = round(rh["trades"] / rd["trades"], 2)
    return out


def proxy_divergence(uni, pk, cfg, cache):
    """Median |native - proxy| close diff over the last divergence_days (percent)."""
    coin, quote = uni["base_of"][pk], uni["quote_of"][pk]
    if uni["exchange"] == "kraken":
        nat = kraken_ohlc_native(uni["pair_alt"].get(pk), 1440,
                                 cfg["divergence_days"] + 3, cfg["kraken_sleep"])
        time.sleep(cfg["kraken_sleep"])
    else:
        nat = nonkyc_ohlc_native(coin, quote, "1440", cfg["divergence_days"] + 3,
                                 cfg["nonkyc_timeout"], cfg["nonkyc_sleep"])
    key = f"mexc_{mexc_symbol(coin, quote)}_1d"
    prox = cache.get(key)
    if nat is None or prox is None or len(nat) < 5:
        return float("nan")
    nmap = {int(round(b[0] / 86400.0)): b[4] for b in nat[-cfg["divergence_days"]:]}
    diffs = []
    for b in prox[-(cfg["divergence_days"] + 3):]:
        d = int(round(b[0] / 86400.0))
        if d in nmap and nmap[d] > 0:
            diffs.append(abs(b[4] - nmap[d]) / nmap[d] * 100)
    return float(np.median(diffs)) if diffs else float("nan")


# ======================================================================
# Finalize (full-history optimize + stress + sizing for WF survivors)
# ======================================================================
def finalize(cands, hist, uni, cfg, cache=None, wf_details=None):
    """For each candidate: optimize rungs+weights on the full 12mo, conservative
    stress with MEASURED spread as slip, sizing + min-qty gate, hourly realism
    check, divergence check (proxy-sourced pairs). Returns (DataFrame, configs)."""
    cache = cache or CandleCache(cfg["cache_dir"], cfg["cache_ttl_hours"])
    kw = dict(fund=cfg["fund_usd"], quote_frac=cfg["quote_frac"], fee=cfg["fee"])
    min_gap = _rt_fee_pct(cfg) * cfg["min_rung_gap_mult"] / 2.0  # avg-gap floor, %
    rows, configs = [], []
    for pk in cands:
        h = hist.get(pk)
        if h is None:
            continue
        bars = slice_days(h["bars"], 365)
        pdec = uni["pdec"].get(pk)
        P = compute_anchor(bars, cfg, label=pk, quiet=True)
        ob = optimize_band(bars, P, cfg)
        if ob is None:
            L = build_ladder(slice_days(bars, int(cfg["months"] * 30.4)), cfg, pdec,
                             label=pk, quiet=True)
            buys, sells = list(map(float, L["buys"])), list(map(float, L["sells"]))
            band_note = "placement (no valid optimized band)"
        else:
            buys, sells = ob["buys"], ob["sells"]
            band_note = (f"plateau centre (peak gives up "
                         f"{ob['peak_pnl'] - ob['pnl']:+.0f}, "
                         f"{ob['n_valid']}/{ob['n_total']} valid)")
        bw, sw, r_w, wmeta = optimize_weights(bars, buys, sells, cfg)
        buys_r = [round_price(p, pdec) for p in buys]
        sells_r = [round_price(p, pdec) for p in sells]

        r12 = sim(bars, buys_r, sells_r, bw, sw, **kw)
        two, recent, qb, qs, qp = quarter_split(r12["cb"], r12["cs"], r12["eq"],
                                                cfg["fund_usd"], cfg["n_quarters"],
                                                cfg["min_side"])
        spread_pct, depth_usd = depth_info(uni, pk, cfg["depth_band"])
        slip = max(cfg["slip_floor"],
                   (spread_pct / 200.0) if spread_pct == spread_pct else 0.0)
        r_cons = sim(bars, buys_r, sells_r, bw, sw,
                     max_fills_per_bar=cfg["max_fills_per_bar"],
                     rearm_cooldown=cfg["rearm_cooldown"], slip=slip,
                     body_only=cfg["body_only"], **kw)
        cons_ret = (r_cons["pnl_pct"] / r12["pnl_pct"] * 100
                    if r12["pnl_pct"] > 0 else float("nan"))
        cons_pass = ((cons_ret == cons_ret and cons_ret >= cfg["cons_min_retained"])
                     and (not cfg["cons_require_beat_hold"]
                          or r_cons["pnl_pct"] > r_cons["hold_pct"]))

        vol_usd = float(uni["df"].set_index("pairkey").vol_usd.get(pk, float("nan")))
        vol_term = cfg["vol_fraction"] * vol_usd if vol_usd == vol_usd else float("inf")
        depth_term = (cfg["depth_fraction"] * depth_usd
                      if depth_usd == depth_usd else float("inf"))
        basis = min(vol_term, depth_term)
        max_fund = round_fund(basis, cfg) if basis != float("inf") else cfg["fund_floor"]

        gap = avg_gap_pct(buys_r + sells_r)
        mq_ok, mq_need = min_qty_check(buys_r, sells_r, bw, sw, max_fund, cfg,
                                       uni["min_qty"].get(pk), bars[0, 4])
        hr = hourly_fill_check(uni, pk, buys_r, sells_r, bw, sw, cfg, cache,
                               bars, h["src"])
        div = (proxy_divergence(uni, pk, cfg, cache)
               if h["src"] == "MEXC" else float("nan"))

        gates = []
        if r12["endinv"] > cfg["max_endinv_pct"] and uni["base_of"][pk] not in cfg["accumulate_ok"]:
            gates.append(f"bagged ({r12['endinv']:.0f}%)")
        if gap < min_gap:
            gates.append(f"rungs too tight ({gap:.2f}% < {min_gap:.2f}%)")
        if depth_usd == depth_usd and depth_usd < cfg["min_depth_2pct"]:
            gates.append(f"thin book (${depth_usd:,.0f})")
        if not mq_ok:
            gates.append(f"min-qty needs fund >= ${mq_need:,.0f}")
        if div == div and div > cfg["divergence_warn_pct"]:
            gates.append(f"proxy diverges {div:.1f}% from native")
        fr = hr.get("fill_ratio", float("nan"))
        if fr == fr and fr < cfg["hourly_warn_ratio"]:
            gates.append(f"hourly fills only {fr:.0%} of daily-sim fills")
        if ob is not None and ob["n_valid"] < cfg["min_valid_bands"]:
            gates.append(f"fragile optimum ({ob['n_valid']}/{ob['n_total']} valid bands)")

        wf = (wf_details or {}).get(pk, {})
        wf_pass = wf.get("wf_pass")
        verdict = ("CONFIRMED" if (wf_pass and cons_pass and not gates) else
                   "GATED" if (wf_pass and cons_pass) else
                   "MIXED" if (wf_pass or cons_pass) else "SUSPECT")

        rows.append(dict(
            base=pk, coin=uni["base_of"][pk], quote=uni["quote_of"][pk], src=h["src"],
            band=f"{rp(min(buys_r)):g}-{rp(max(sells_r)):g}",
            rungs=f"{len(buys_r)}+{len(sells_r)}", wt=wmeta,
            pnl12=round(r12["pnl_pct"], 1),
            pnl12_usd=round(r12["pnl"] * usd_rate_of(uni, pk), 0),
            endinv=round(r12["endinv"], 0), two_sided=f"{two}/{cfg['n_quarters']}",
            wf_med_ann=wf.get("med_test_ann", float("nan")),
            wf_pos=f"{wf.get('pos_folds', '?')}/{wf.get('n_folds', '?')}",
            wf_pass=wf_pass,
            cons_kept=round(cons_ret, 0) if cons_ret == cons_ret else float("nan"),
            cons_pass=cons_pass, slip_bps=round(slip * 1e4, 0),
            spread_pct=round(spread_pct, 3) if spread_pct == spread_pct else float("nan"),
            depth_2pct=round(depth_usd, 0) if depth_usd == depth_usd else float("nan"),
            max_fund=max_fund,
            fill_ratio=hr.get("fill_ratio", float("nan")),
            hourly_src=hr.get("hourly", "n/a"),
            diverge_pct=round(div, 2) if div == div else float("nan"),
            gates="; ".join(gates) if gates else "",
            VERDICT=verdict, band_note=band_note))
        configs.append(dict(
            symbol=pk, exchange=uni["exchange"], passive_order_placement=True,
            max_fund_value_quote=max_fund, total_amount_quote=max_fund,
            buy_prices=[round(float(x), 8) for x in buys_r],
            sell_prices=[round(float(x), 8) for x in sells_r],
            buy_amounts_pct=weights_pct(bw), sell_amounts_pct=weights_pct(sw),
            validation=verdict,
            walkforward=dict(passed=wf_pass, folds=wf.get("folds", []),
                             med_test_ann=wf.get("med_test_ann"),
                             med_cons_ann=wf.get("med_cons_ann")),
            conservative=dict(passed=bool(cons_pass),
                              retained_pct=round(cons_ret, 0) if cons_ret == cons_ret else None,
                              slip_bps=round(slip * 1e4, 0)),
            hourly_check=hr, gates=gates))
    order = {"CONFIRMED": 0, "GATED": 1, "MIXED": 2, "SUSPECT": 3}
    d = pd.DataFrame(rows)
    if not d.empty:
        d["_o"] = d.VERDICT.map(order)
        d = d.sort_values(["_o", "pnl12_usd"], ascending=[True, False]).drop(columns="_o")
        d = d.reset_index(drop=True)
        configs = sorted(configs, key=lambda c: (order.get(c["validation"], 9),
                                                 -(c["max_fund_value_quote"] or 0)))
    return d, configs


def save_outputs(summary_df, configs, csv_path, json_path):
    summary_df.to_csv(csv_path, index=False)
    with open(json_path, "w") as f:
        json.dump(configs, f, indent=2, default=str)
    _log(f"Saved table -> {csv_path}   |   configs -> {json_path}")


if __name__ == "__main__":
    print(f"ladder_lab {__version__} | numba={HAVE_NUMBA}")
    print("parity:", parity_check(verbose=True))
