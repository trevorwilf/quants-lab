"""
ladder_lab_recycle_v11.py -- v11 engine: v10 recycle + fill realism + clean OOS
================================================================================

Companion to `ladder_lab.py` (adapters/cache/universe/screener) and
`ladder_lab_recycle.py` (the v10 engine, which stays installed and unchanged --
v11 imports and reuses everything that was already right, including the
copy/paste markdown renderer, byte-for-byte).

What v11 fixes (each maps to a defect found in the v10 review)
--------------------------------------------------------------
 1. FIT-WINDOW CONTAMINATION. v10's frozen 180d block report included the 60d
    the deploy ladder was fitted on -- ~1/3 of blocks, and the most recent
    ones, were in-sample. v11 (a) tags every block `in_fit` and gates the
    CLEAN blocks separately, and (b) adds a TRUE HOLDOUT: the fit never sees
    the last `rc_holdout_days` (default 15); the fitted, train-anchored ladder
    is then scored once on that unseen tail. That holdout edge is the only
    number in the whole pipeline that is fully out-of-sample for the ladder
    you deploy, and it gates deployment.
 2. TOUCH-FILLS. A resting limit at the exact bar extreme rarely fills live
    (queue position; price must trade THROUGH you). v11 fills require the leg
    to penetrate `max(1 tick, price * rc_fill_penetration_pct)` beyond the
    rung. Fills still execute at the rung price (maker).
 3. VOLUME-BLIND FILLS. On thin NonKYC books the sim could "fill" $200 at a
    level where $30 traded. v11 carries QUOTE VOLUME with every bar (Nx6) and
    caps total filled notional per bar at `rc_volume_cap_frac` of the bar's
    quote volume, with realistic PARTIAL fills (remainder stays open). Bars
    with unknown volume are uncapped (flagged via `vol_capped_fills`).
 4. SLIP ASYMMETRY. v10 selected candidates under Roll-slip (which is 0 for
    healthy books) and only compared against the measured book spread at
    finalize -- biasing selection toward tight ladders that only work at the
    floor. v11 threads the measured book half-spread into the SEARCH, the WF,
    and the report alike: slip = max(floor, Roll, book_half_spread), capped.
 5. PAIR SELECTION. New model-free `grid_harvest` screen: zig-zag swing
    counting at gaps = multiples of the round-trip cost, giving
    "harvestable %/month net of costs" per market with zero fit parameters.
    Used to rank the review set; reported in the final summary.
 6. KRAKEN HISTORY. Kraken native OHLC caps at 720 candles (30d of 1h).
    v11's history layer tries the MEXC proxy with a QUOTE ALIAS
    (USD/USDC->USDT), guarded by the existing last-price proxy check, so
    XMR/USD gets real multi-month hourly/5m depth from XMRUSDT.
 7. Small fixes: collision-safe `regularize_bars6` (aggregates o/h/l/c/vol
    when two raw bars snap to one grid slot), clean bar_seconds handling in
    the block table, deterministic overfit indicator (`fit_score_gap`), and a
    v10-EQUIVALENCE regression: with penetration=0 and the volume cap off the
    v11 kernel reproduces the v10 kernel bit-for-bit (tested).

Nothing was removed from the v10 reports: every v10 summary/CSV field is
still emitted; v11 only ADDS fields (holdout_*, clean_*, harvest_*,
vol_capped_fills, penetration/book-spread provenance). The
`*_copy_paste_ladders.md` file is rendered by v10's own renderer, unchanged.
"""
from __future__ import annotations

import copy
import json
import math
import time
import concurrent.futures as _fut
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

import ladder_lab as _base
import ladder_lab_recycle as _v10
from ladder_lab import _log, _njit, HAVE_NUMBA, CandleCache, slice_days
from ladder_lab_recycle import (   # re-used verbatim (single source of truth)
    _pair_key, merge_unique_markets, resolve_present, drop_stable_stable,
    bar_seconds_of, ensure_ts,
    price_str, format_ladder_prices, validate_ladder,
    df_to_markdown, roll_half_spread_pct,
    parse_controller_yaml, discover_controller_yamls, controller_to_ladder,
    generate_candidates, _weights_for_curve, _anchor_price, _rng_for,
    score_v10, mexc_klines_interval, _IV_MS, _NONKYC_RES,
    render_copy_paste_markdown, controller_copy_block,
    summarize_diagnostic_jsonl, extract_fills_from_jsonl, compare_live_vs_sim,
    with_daily_fallback, prefetch_hourly, prefetch_intraday,
)

__version__ = "11.3.1-resilient-universe"

UNSET = float("nan")


def _num(x: Any, ndigits: int = 3) -> float:
    """None/NaN/non-numeric -> NaN; else round(). (None == None is True, so a
    bare `x == x` NaN-guard silently lets None through into round().)"""
    if x is None:
        return UNSET
    try:
        v = float(x)
    except (TypeError, ValueError):
        return UNSET
    return round(v, ndigits) if v == v else UNSET


# ======================================================================
# Config
# ======================================================================
def recycle_default_config(exchange: str) -> Dict[str, Any]:
    """v10 config + the v11 knobs (prefix rc_ kept for notebook familiarity)."""
    cfg = _v10.recycle_default_config(exchange)
    cfg.update(dict(
        # ---- 1. clean out-of-sample -------------------------------------
        rc_holdout_days=15.0,             # fit NEVER sees the last N days
        rc_gate_holdout_min_edge=-2.0,    # deploy gate: holdout edge floor (%)
        rc_gate_holdout_require_active=True,   # dormant holdout != evidence
        rc_gate_min_clean_blocks=4,       # blocks outside the fit window
        # ---- 2. fill realism --------------------------------------------
        rc_fill_penetration_pct=0.0005,   # 5 bps beyond the rung (plus 1 tick)
        rc_fill_penetration_ticks=1.0,    # ticks beyond the rung (pdec-based)
        rc_volume_cap_frac=0.25,          # max share of a bar's quote volume
                                          #   we may fill (0 disables the cap)
        # ---- 4. slip symmetry ---------------------------------------------
        rc_book_spread_in_slip=True,      # measured book half-spread joins
                                          #   Roll + floor in ALL slip calcs
        # ---- 5. pair selection --------------------------------------------
        rc_harvest_gap_mults=(1.5, 2.0, 3.0),  # gaps as multiples of RT cost
        rc_harvest_rank_weight=0.5,       # blend harvest rank into review pick
        # ---- 6. kraken/deep-history proxy ---------------------------------
        rc_quote_alias={"USD": "USDT", "USDC": "USDT"},
        # v11 engine switch (False = byte-identical v10 fills; for A/B only)
        rc_v11_fill_model=True,
        # ---- v11.1 ---------------------------------------------------------
        # Dust filter: markets below this 24h USD volume never enter the
        # universe. The first full run spent ~90% of engine time on books
        # that could not absorb even the $200 fund floor.
        min_vol_usd=10000.0,
        # Two-sided evidence mode:
        #   'blocks'  = v10 behavior (two_sided_rate over active history blocks)
        #   'holdout' = judge two-sidedness on the holdout only
        #   'either'  = block gate is waived when the HOLDOUT was two-sided
        # Rationale: a ladder re-anchored at today's price is structurally
        # one-sided against a trending past (XMR: candidate failed 0.36 while
        # the live YAML passed 0.73 on the same data). The holdout is anchored
        # and evaluated on its own unseen window, so it has no such bias.
        rc_gate_two_sided_mode="either",
        # v11.1.3: median-of-N book sampling (single snapshots of thin books
        # were the main cause of verdicts flipping between back-to-back runs)
        rc_book_samples=3,
        rc_book_sample_pause=1.0,
        # ---- v11.2: depth measured where the RUNGS are -------------------
        # 'ladder' = depth resting inside the deployed ladder's own span
        #            (lowest buy -> highest sell). 'band' = legacy +-2% of mid.
        # A fixed +-2% band reads the hole between dust quotes on exactly the
        # markets a ladder wants (DASH/USDT: +-2%=$2, +-5%=$29,820).
        rc_depth_metric="ladder",
        rc_depth_min_band=0.05,     # never measure a band tighter than this
        rc_depth_profile_bands=(0.02, 0.05, 0.10, 0.25),
        # ---- v11.3: deployable YAML generation -------------------------
        rc_yaml_min_holdout_edge=2.0,   # GATED market qualifies as CANDIDATE
        rc_yaml_min_clean_epr=0.6,      #   only with this holdout + clean bar
        rc_yaml_seed_frac=0.5,          # fresh deploy: seed = frac of cap, in
                                        #   QUOTE (claimed base = 0, buy-first)
        # ---- v11.3: live-strategy health -------------------------------
        rc_health_recent_blocks=3,      # judge the last N complete blocks
        rc_health_loss_floor_pct=-1.0,  # recent pnl below this = losing money
        # ---- v11.3.1: universe resilience -------------------------------
        rc_universe_cache_hours=48.0,   # max age of the disk-cached universe
                                        #   used when the exchange API is down
    ))
    return cfg


# ======================================================================
# Nx6 bars: [ts, o, h, l, c, quote_volume]   (vol NaN = unknown -> uncapped)
# ======================================================================
def ensure6(bars: np.ndarray, bar_seconds: float = 3600.0) -> np.ndarray:
    """Guarantee Nx6 [ts,o,h,l,c,qvol]; NaN qvol when volume is unknown."""
    bars = np.asarray(bars, float)
    if bars.ndim != 2:
        raise ValueError("bars must be 2-D")
    if bars.shape[1] >= 6:
        base = ensure_ts(bars[:, :5], bar_seconds)
        return np.column_stack([base, bars[:, 5]])
    base = ensure_ts(bars, bar_seconds)
    return np.column_stack([base, np.full(len(base), UNSET)])


def regularize_bars6(bars: np.ndarray, bar_seconds: Optional[float] = None
                     ) -> Tuple[np.ndarray, float]:
    """v11 grid snap: like v10's regularize_bars but (a) carries quote volume
    (gap bars get qvol=0 -- flat AND capped, they can never fill), and
    (b) COLLISION-SAFE: when several raw bars snap to one slot they are
    aggregated (first open, max high, min low, last close, summed volume)
    instead of last-write-wins."""
    bars = ensure6(bars, bar_seconds or 3600.0)
    if len(bars) < 3:
        return bars, 0.0
    d = np.diff(bars[:, 0])
    d = d[d > 0]
    step = float(bar_seconds or 0) or float(np.median(d)) if len(d) else 3600.0
    for grid in (60.0, 300.0, 900.0, 1800.0, 3600.0, 14400.0, 86400.0):
        if abs(step - grid) / grid < 0.25:
            step = grid
            break
    t0, t1 = bars[0, 0], bars[-1, 0]
    n = int(round((t1 - t0) / step)) + 1
    if n <= 2 or n > 4 * 10 ** 6:
        return bars, 0.0
    idx = np.clip(np.round((bars[:, 0] - t0) / step).astype(int), 0, n - 1)
    out = np.zeros((n, 6))
    out[:, 0] = t0 + step * np.arange(n)
    out[:, 5] = 0.0
    have = np.zeros(n, bool)
    for j in range(len(bars)):
        i = idx[j]
        ts, o, h, l, c, v = bars[j]
        # CRITICAL (v11.1.3): NaN volume means UNKNOWN -> uncapped. It must
        # stay NaN through the grid snap. Coercing it to 0.0 (the v11.1.2
        # bug) gave every bar a zero taker budget, so the volume cap
        # silently blocked ALL fills on Nx5-sourced (daily-fallback) data.
        if not have[i]:
            out[i, 1:5] = (o, h, l, c)
            out[i, 5] = v                            # may be NaN (unknown)
            have[i] = True
        else:                                   # collision -> aggregate
            out[i, 2] = max(out[i, 2], h)
            out[i, 3] = min(out[i, 3], l)
            out[i, 4] = c
            if v == v:
                out[i, 5] = v if not (out[i, 5] == out[i, 5]) else out[i, 5] + v
    if have.all() and n == len(bars):
        return out, 0.0
    last_c = bars[0, 1]
    any_vol_known = bool(np.isfinite(bars[:, 5]).any())
    for i in range(n):
        if have[i]:
            last_c = out[i, 4]
        else:
            out[i, 1:5] = last_c
            out[i, 5] = 0.0 if any_vol_known else UNSET
    return out, float(1.0 - have.mean())


# ======================================================================
# Volume-carrying fetchers (Nx6). Cache keys carry a _v6 suffix.
# ======================================================================
def mexc_klines6(symbol: str, interval: str, days: float,
                 limit: int = 1000, max_pages: int = 400) -> Optional[np.ndarray]:
    """Paginated MEXC klines -> Nx6 with QUOTE volume (kline field 7;
    falls back to base_vol*close). Same pagination as v10's interval fetcher."""
    end = int(time.time() * 1000)
    start = end - int(days * 86400 * 1000)
    iv_ms = _IV_MS.get(interval, 86400000)
    seen: Dict[int, Any] = {}
    cur = start
    for _ in range(max_pages):
        k = _base._get_json(f"{_base.MEXC}/klines",
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
    out = []
    for x in rows:
        c = float(x[4])
        try:
            qv = float(x[7])
        except (IndexError, TypeError, ValueError):
            try:
                qv = float(x[5]) * c
            except (IndexError, TypeError, ValueError):
                qv = UNSET
        out.append([int(x[0]) / 1000.0, float(x[1]), float(x[2]),
                    float(x[3]), c, qv])
    return np.array(out, float)


def nonkyc_ohlc6(coin: str, quote: str, resolution: str = "60", days: float = 185,
                 timeout: int = 35, sleep: float = 0.6, retries: int = 3
                 ) -> Optional[np.ndarray]:
    """NonKYC native candles -> Nx6. Volume: quote-volume field when present,
    else base volume * close, else NaN (uncapped)."""
    import requests
    to_ = int(time.time())
    frm = to_ - int(days) * 86400
    for a in range(retries):
        try:
            r = requests.get(f"{_base.NONKYC}/market/candles",
                             params={"symbol": f"{coin}/{quote}",
                                     "resolution": resolution,
                                     "from": frm, "to": to_}, timeout=timeout)
            if r.status_code == 200:
                bars = r.json().get("bars", [])
                if not bars:
                    return None
                out = []
                for b in bars:
                    ts = b.get("time", b.get("timestamp", b.get("t")))
                    ts = float(ts) if ts is not None else UNSET
                    if ts == ts and ts > 1e12:
                        ts /= 1000.0
                    c = float(b["close"])
                    qv = b.get("volumeQuote", b.get("quoteVolume",
                               b.get("volume_quote")))
                    if qv is not None:
                        try:
                            qv = float(qv)
                        except (TypeError, ValueError):
                            qv = None
                    if qv is None:
                        bv = b.get("volume", b.get("volumeBase", b.get("v")))
                        try:
                            qv = float(bv) * c if bv is not None else UNSET
                        except (TypeError, ValueError):
                            qv = UNSET
                    out.append([ts, float(b["open"]), float(b["high"]),
                                float(b["low"]), c, qv])
                arr = np.array(out, float)
                if np.isnan(arr[:, 0]).any():
                    step = 86400.0 if resolution == "1440" else float(resolution) * 60.0
                    arr[:, 0] = to_ - step * np.arange(len(arr) - 1, -1, -1)
                return arr
        except Exception:
            pass
        time.sleep(sleep * (a + 1))
    return None


def kraken_ohlc6(altname: str, interval: int = 60, days: float = 31,
                 sleep: float = 1.0) -> Optional[np.ndarray]:
    """Kraken OHLC -> Nx6. Row: [t,o,h,l,c,vwap,vol,count]; qvol = vwap*vol.
    Kraken caps this endpoint at the 720 most recent candles per interval."""
    since = int(time.time()) - int(days) * 86400
    for _ in range(2):
        r = _base._get_json(f"{_base.KRAKEN}/OHLC",
                            params={"pair": altname, "interval": interval,
                                    "since": since}, timeout=30)
        if r is not None and not r.get("error"):
            rows = next((v for k, v in r.get("result", {}).items() if k != "last"), None)
            if not rows:
                return None
            out = []
            for x in rows:
                vwap = float(x[5]) if float(x[5]) > 0 else float(x[4])
                out.append([float(x[0]), float(x[1]), float(x[2]),
                            float(x[3]), float(x[4]), vwap * float(x[6])])
            return np.array(out, float)
        time.sleep(sleep)
    return None


def _mexc_symbols_for(uni: Dict[str, Any], pk: str, cfg: Dict[str, Any]) -> List[str]:
    """Exact MEXC symbol first, then quote-aliased (USD/USDC -> USDT etc.),
    all still guarded by the last-price proxy check downstream."""
    coin, quote = uni["base_of"][pk], uni["quote_of"][pk]
    syms = [_base.mexc_symbol(coin, quote)]
    alias = (cfg.get("rc_quote_alias") or {}).get(quote.upper())
    if alias and alias.upper() != quote.upper():
        s2 = _base.mexc_symbol(coin, alias)
        if s2 not in syms:
            syms.append(s2)
    return syms


def fetch_bars6(uni: Dict[str, Any], pk: str, cfg: Dict[str, Any],
                cache: Optional[CandleCache] = None,
                interval: str = "60m", days: Optional[float] = None
                ) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """Unified Nx6 history: NonKYC native (own exchange) -> MEXC proxy
    (exact, then quote-aliased; price-guarded) -> Kraken native (720 cap).
    Returns (bars6, src) or (None, None)."""
    cache = cache or CandleCache(cfg["cache_dir"], cfg["cache_ttl_hours"])
    days = float(days if days is not None
                 else (cfg.get("rc_intraday_days", 185)
                       if interval not in ("60m", "1h", "1d")
                       else (cfg.get("hourly_days", 185) if interval != "1d"
                             else cfg["years"] * 365 + 30)))
    bars_per_day = 86400.0 / (_IV_MS.get(interval, 3600000) / 1000.0)
    min_bars = int(bars_per_day * 7)
    coin, quote = uni["base_of"][pk], uni["quote_of"][pk]

    if uni["exchange"] == "nonkyc" and interval in _NONKYC_RES:
        key = f"nonkyc_{pk}_{interval}_v6"
        bars = cache.get(key)
        if bars is None:
            bars = nonkyc_ohlc6(coin, quote, _NONKYC_RES[interval], days,
                                cfg["nonkyc_timeout"], cfg["nonkyc_sleep"])
            if bars is not None and len(bars) >= min_bars:
                cache.put(key, bars)
        if bars is not None and len(bars) >= min_bars:
            return ensure6(bars), "NonKYC"

    for sym in _mexc_symbols_for(uni, pk, cfg):
        key = f"mexc_{sym}_{interval}_v6"
        bars = cache.get(key)
        if bars is None:
            bars = mexc_klines6(sym, interval, days)
            if bars is not None and len(bars) >= min_bars:
                cache.put(key, bars)
        if (bars is not None and len(bars) >= min_bars
                and _base._proxy_ok(uni, pk, bars, cfg)):
            src = "MEXC" if sym == _base.mexc_symbol(coin, quote) else f"MEXC({sym})"
            return ensure6(bars), src

    if uni["exchange"] == "kraken" and interval in ("60m", "1h", "1d"):
        kiv = 60 if interval in ("60m", "1h") else 1440
        key = f"kraken_{pk}_{interval}_v6"
        bars = cache.get(key)
        if bars is None:
            bars = kraken_ohlc6(uni["pair_alt"].get(pk, pk.replace("/", "")),
                                kiv, min(days, 31 if kiv == 60 else days),
                                cfg["kraken_sleep"])
            time.sleep(cfg["kraken_sleep"])
            if bars is not None and len(bars) >= min(min_bars, 24 * 7):
                cache.put(key, bars)
        if bars is not None and len(bars) >= min(min_bars, 24 * 7):
            return ensure6(bars), "Kraken(720cap)"

    if uni["exchange"] == "nonkyc" and interval not in _NONKYC_RES:
        b, s = _base.fetch_hourly(uni, pk, cfg, cache)
        if b is not None:
            return ensure6(b), s
    return None, None


def prefetch_bars6(uni: Dict[str, Any], cfg: Dict[str, Any],
                   cache: Optional[CandleCache] = None,
                   pairs: Optional[Sequence[str]] = None,
                   interval: str = "60m",
                   min_days_key: str = "rc_min_hourly_days") -> Dict[str, Any]:
    """Threaded fetch_bars6 over a pair list -> {pk: {bars,src,days,granularity,
    vol_known}}. Same result shape as v10's prefetchers (bars are Nx6 now)."""
    cache = cache or CandleCache(cfg["cache_dir"], cfg["cache_ttl_hours"])
    pairs = list(pairs if pairs is not None else uni["df"].pairkey)
    t0 = time.time()
    out: Dict[str, Any] = {}

    def one(pk):
        try:
            bars, src = fetch_bars6(uni, pk, cfg, cache, interval)
        except Exception as e:
            return pk, None, f"error:{e}"
        return pk, bars, src

    workers = (max(2, min(int(cfg.get("nonkyc_workers", 4)), 6))
               if uni["exchange"] == "nonkyc" and interval in _NONKYC_RES
               else max(2, int(cfg.get("mexc_workers", 8))))
    with _fut.ThreadPoolExecutor(max_workers=workers) as ex:
        for j, (pk, bars, src) in enumerate(ex.map(one, pairs), 1):
            if bars is not None:
                days = (bars[-1, 0] - bars[0, 0]) / 86400.0
                if days >= float(cfg.get(min_days_key, 45)):
                    bsec = bar_seconds_of(bars)
                    gran = (interval if bsec < 3599
                            else ("1h" if bsec < 86000 else "1d"))
                    out[pk] = dict(bars=bars, src=src, days=days,
                                   granularity=gran,
                                   vol_known=bool(np.isfinite(bars[:, 5]).mean() > 0.5))
            if j % 10 == 0:
                _log(f"  ...bars6[{interval}] {j}/{len(pairs)}")
    _log(f"bars6({interval}): {len(out)}/{len(pairs)} markets in {time.time() - t0:.0f}s")
    return out


# ======================================================================
# v11 fill kernel: v10 recycle + penetration + volume-capped partial fills
# ======================================================================
@_njit(cache=False)
def _k_place_buys(bq, buys, bwn, quote, ref, cm, min_order):
    for i in range(buys.shape[0]):
        bq[i] = 0.0
        if buys[i] < ref and buys[i] > 0.0:
            alloc = quote * bwn[i]
            if alloc >= min_order:
                bq[i] = alloc / (buys[i] * (1.0 + cm))


@_njit(cache=False)
def _k_place_sells(sq, sells, swn, base, ref, min_order):
    for i in range(sells.shape[0]):
        sq[i] = 0.0
        if sells[i] > ref:
            qty = base * swn[i]
            if qty * sells[i] >= min_order:
                sq[i] = qty


@_njit(cache=False)
def _recycle_kernel_v11(o, h, l, c, qvol, buys, sells, bwn, swn,
                        pen_b, pen_s,
                        fund, qf, fee, slip,
                        cooldown_bars, refresh_bars, min_order,
                        event_refresh, body_only, vol_cap_frac):
    """v10 recycle kernel + (a) penetration: a leg must trade pen beyond the
    rung to fill, (b) per-bar quote-volume budget shared by both sides with
    PARTIAL fills (remainder stays open). pen arrays of zeros + vol_cap_frac
    <= 0 reproduce the v10 kernel bit-for-bit (regression-tested)."""
    n = c.shape[0]
    nb = buys.shape[0]
    ns = sells.shape[0]
    p0 = o[0]
    quote = fund * qf
    base = fund * (1.0 - qf) / p0
    cm = fee + slip

    bq = np.zeros(nb)
    sq = np.zeros(ns)
    bf = np.zeros(nb, np.int64)
    sf = np.zeros(ns, np.int64)
    cb = np.zeros(n, np.int64)
    cs = np.zeros(n, np.int64)
    eq = np.zeros(n)
    fees = 0.0
    turnover = 0.0
    nbt = 0
    nst = 0
    ncapped = 0
    last_bfill = -1000000000
    last_sfill = -1000000000
    b_dirty = False
    s_dirty = False

    _k_place_buys(bq, buys, bwn, quote, p0, cm, min_order)
    _k_place_sells(sq, sells, swn, base, p0, min_order)

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

        # per-bar taker-volume budget shared by both sides (quote units)
        budget = 1e300
        if vol_cap_frac > 0.0 and qvol[t] == qvol[t]:     # NaN = unknown
            budget = qvol[t] * vol_cap_frac

        bfill_bar = False
        sfill_bar = False
        for s in range(plen - 1):
            a = path[s]
            b = path[s + 1]
            if b < a:
                for i in range(nb):
                    if budget <= 0.0:
                        break
                    if bq[i] > 0.0 and b <= buys[i] - pen_b[i] and buys[i] <= a:
                        qty = bq[i]
                        cost = buys[i] * qty
                        capped = False
                        if cost > budget:
                            qty = budget / buys[i]
                            cost = buys[i] * qty
                            capped = True
                        debit = cost * (1.0 + cm)
                        if quote >= debit - 1e-12 and qty > 0.0:
                            quote -= debit
                            base += qty
                            fees += cost * cm
                            turnover += cost
                            budget -= cost
                            bq[i] -= qty
                            if bq[i] * buys[i] < 1e-9:
                                bq[i] = 0.0
                            bf[i] += 1
                            nbt += 1
                            if capped:
                                ncapped += 1
                            bfill_bar = True
            elif b > a:
                for i in range(ns):
                    if budget <= 0.0:
                        break
                    if sq[i] > 0.0 and a <= sells[i] and sells[i] + pen_s[i] <= b:
                        qty = sq[i]
                        capped = False
                        if qty * sells[i] > budget:
                            qty = budget / sells[i]
                            capped = True
                        if base >= qty - 1e-12 and qty > 0.0:
                            proceeds = sells[i] * qty
                            quote += proceeds * (1.0 - cm)
                            base -= qty
                            fees += proceeds * cm
                            turnover += proceeds
                            budget -= proceeds
                            sq[i] -= qty
                            if sq[i] * sells[i] < 1e-9:
                                sq[i] = 0.0
                            sf[i] += 1
                            nst += 1
                            if capped:
                                ncapped += 1
                            sfill_bar = True

        ref = c[t]
        if bfill_bar:
            last_bfill = t
            b_dirty = True
        if sfill_bar:
            last_sfill = t
            s_dirty = True

        if event_refresh:
            if bfill_bar:
                _k_place_sells(sq, sells, swn, base, ref, min_order)
                s_dirty = False
                last_sfill = t
            if sfill_bar:
                _k_place_buys(bq, buys, bwn, quote, ref, cm, min_order)
                b_dirty = False
                last_bfill = t

        if b_dirty and (t - last_bfill) >= cooldown_bars:
            _k_place_buys(bq, buys, bwn, quote, ref, cm, min_order)
            b_dirty = False
        if s_dirty and (t - last_sfill) >= cooldown_bars:
            _k_place_sells(sq, sells, swn, base, ref, min_order)
            s_dirty = False

        if refresh_bars > 0 and ((t + 1) % refresh_bars) == 0:
            _k_place_buys(bq, buys, bwn, quote, ref, cm, min_order)
            _k_place_sells(sq, sells, swn, base, ref, min_order)
            b_dirty = False
            s_dirty = False

        cb[t] = nbt
        cs[t] = nst
        eq[t] = quote + base * c[t]

    return quote, base, fees, turnover, bf, sf, cb, cs, eq, ncapped


def _recycle_reference_v11(o, h, l, c, qvol, buys, sells, bwn, swn, pen_b, pen_s,
                           fund, qf, fee, slip, cooldown_bars, refresh_bars,
                           min_order, event_refresh, body_only, vol_cap_frac):
    """Pure-Python literal port of _recycle_kernel_v11 (parity golden path)."""
    n = len(c)
    nb, ns = len(buys), len(sells)
    p0 = o[0]
    quote = fund * qf
    base = fund * (1.0 - qf) / p0
    cm = fee + slip
    bq = np.zeros(nb)
    sq = np.zeros(ns)
    bf = np.zeros(nb, np.int64)
    sf = np.zeros(ns, np.int64)
    cb = np.zeros(n, np.int64)
    cs = np.zeros(n, np.int64)
    eq = np.zeros(n)
    fees = turnover = 0.0
    nbt = nst = ncapped = 0
    last_bfill = last_sfill = -1000000000
    b_dirty = s_dirty = False

    def place_buys(ref):
        for i in range(nb):
            bq[i] = 0.0
            if 0.0 < buys[i] < ref:
                alloc = quote * bwn[i]
                if alloc >= min_order:
                    bq[i] = alloc / (buys[i] * (1.0 + cm))

    def place_sells(ref):
        for i in range(ns):
            sq[i] = 0.0
            if sells[i] > ref:
                qty = base * swn[i]
                if qty * sells[i] >= min_order:
                    sq[i] = qty

    place_buys(p0)
    place_sells(p0)
    for t in range(n):
        path = ([o[t], c[t]] if body_only else
                ([o[t], l[t], h[t], c[t]] if c[t] >= o[t]
                 else [o[t], h[t], l[t], c[t]]))
        budget = 1e300
        if vol_cap_frac > 0.0 and qvol[t] == qvol[t]:
            budget = qvol[t] * vol_cap_frac
        bfill_bar = sfill_bar = False
        for a, b in zip(path, path[1:]):
            if b < a:
                for i in range(nb):
                    if budget <= 0.0:
                        break
                    if bq[i] > 0.0 and b <= buys[i] - pen_b[i] and buys[i] <= a:
                        qty = bq[i]
                        cost = buys[i] * qty
                        capped = False
                        if cost > budget:
                            qty = budget / buys[i]
                            cost = buys[i] * qty
                            capped = True
                        debit = cost * (1.0 + cm)
                        if quote >= debit - 1e-12 and qty > 0.0:
                            quote -= debit
                            base += qty
                            fees += cost * cm
                            turnover += cost
                            budget -= cost
                            bq[i] -= qty
                            if bq[i] * buys[i] < 1e-9:
                                bq[i] = 0.0
                            bf[i] += 1
                            nbt += 1
                            ncapped += 1 if capped else 0
                            bfill_bar = True
            elif b > a:
                for i in range(ns):
                    if budget <= 0.0:
                        break
                    if sq[i] > 0.0 and a <= sells[i] and sells[i] + pen_s[i] <= b:
                        qty = sq[i]
                        capped = False
                        if qty * sells[i] > budget:
                            qty = budget / sells[i]
                            capped = True
                        if base >= qty - 1e-12 and qty > 0.0:
                            proceeds = sells[i] * qty
                            quote += proceeds * (1.0 - cm)
                            base -= qty
                            fees += proceeds * cm
                            turnover += proceeds
                            budget -= proceeds
                            sq[i] -= qty
                            if sq[i] * sells[i] < 1e-9:
                                sq[i] = 0.0
                            sf[i] += 1
                            nst += 1
                            ncapped += 1 if capped else 0
                            sfill_bar = True
        ref = c[t]
        if bfill_bar:
            last_bfill = t
            b_dirty = True
        if sfill_bar:
            last_sfill = t
            s_dirty = True
        if event_refresh:
            if bfill_bar:
                place_sells(ref)
                s_dirty = False
                last_sfill = t
            if sfill_bar:
                place_buys(ref)
                b_dirty = False
                last_bfill = t
        if b_dirty and (t - last_bfill) >= cooldown_bars:
            place_buys(ref)
            b_dirty = False
        if s_dirty and (t - last_sfill) >= cooldown_bars:
            place_sells(ref)
            s_dirty = False
        if refresh_bars > 0 and ((t + 1) % refresh_bars) == 0:
            place_buys(ref)
            place_sells(ref)
            b_dirty = s_dirty = False
        cb[t] = nbt
        cs[t] = nst
        eq[t] = quote + base * c[t]
    return quote, base, fees, turnover, bf, sf, cb, cs, eq, ncapped


def recycle_sim_v11(bars: np.ndarray,
                    buys: Sequence[float], sells: Sequence[float],
                    bw: Optional[Sequence[float]] = None,
                    sw: Optional[Sequence[float]] = None,
                    fund: float = 1000.0, quote_frac: float = 0.5,
                    fee: float = 0.002, slip: float = 0.0,
                    cooldown_seconds: float = 3600.0,
                    refresh_seconds: float = 43200.0,
                    min_order_quote: float = 1.0,
                    event_refresh: bool = True, body_only: bool = False,
                    bar_seconds: Optional[float] = None,
                    pen_frac: float = 0.0, tick: float = 0.0,
                    vol_cap_frac: float = 0.0,
                    use_numba: Optional[bool] = None) -> Dict[str, Any]:
    """v11 recycling sim on Nx6 bars. Returns the exact v10 result dict PLUS
    vol_capped_fills, pen_frac, tick, vol_cap_frac (provenance)."""
    bars = ensure6(bars, bar_seconds or 3600.0)
    bsec = float(bar_seconds or bar_seconds_of(bars))
    o = np.ascontiguousarray(bars[:, 1])
    h = np.ascontiguousarray(bars[:, 2])
    l = np.ascontiguousarray(bars[:, 3])
    c = np.ascontiguousarray(bars[:, 4])
    qvol = np.ascontiguousarray(bars[:, 5])
    buys = np.asarray(sorted(set(float(x) for x in buys), reverse=True), float)
    sells = np.asarray(sorted(set(float(x) for x in sells)), float)
    bw = np.ones(len(buys)) if bw is None else np.asarray(bw, float)[:len(buys)]
    sw = np.ones(len(sells)) if sw is None else np.asarray(sw, float)[:len(sells)]
    if len(bw) != len(buys) or len(sw) != len(sells):
        raise ValueError("weights length must match prices length after dedupe")
    bwn = bw / bw.sum()
    swn = sw / sw.sum()
    pen_b = np.maximum(float(tick), buys * float(pen_frac))
    pen_s = np.maximum(float(tick), sells * float(pen_frac))
    if pen_frac <= 0.0 and tick <= 0.0:
        pen_b = np.zeros(len(buys))
        pen_s = np.zeros(len(sells))
    cooldown_bars = max(1, int(round(float(cooldown_seconds) / bsec)))
    refresh_bars = max(0, int(round(float(refresh_seconds) / bsec))) if refresh_seconds else 0

    if use_numba is None:
        use_numba = HAVE_NUMBA
    impl = _recycle_kernel_v11 if (use_numba and HAVE_NUMBA) else _recycle_reference_v11
    quote, base, fees, turnover, bf, sf, cb, cs, eq, ncapped = impl(
        o, h, l, c, qvol, buys, sells, bwn, swn, pen_b, pen_s,
        float(fund), float(quote_frac), float(fee), float(slip),
        np.int64(cooldown_bars), np.int64(refresh_bars), float(min_order_quote),
        bool(event_refresh), bool(body_only), float(vol_cap_frac))

    p0 = o[0]
    hold_q = fund * quote_frac
    hold_b = fund * (1.0 - quote_frac) / p0
    hold_eq = hold_q + hold_b * c
    final = quote + base * c[-1]
    peak = np.maximum.accumulate(eq)
    mdd = float(np.max((peak - eq) / np.where(peak > 0, peak, 1.0))) * 100
    days = max((bars[-1, 0] - bars[0, 0]) / 86400.0, 1e-9)
    months = days / 30.4
    trades = int(bf.sum() + sf.sum())
    lo_b = float(np.min(buys)) if len(buys) else UNSET
    hi_s = float(np.max(sells)) if len(sells) else UNSET
    pnl_pct = (final - fund) / fund * 100
    hold_pct = (hold_eq[-1] - fund) / fund * 100
    return dict(pnl=final - fund, pnl_pct=pnl_pct, hold_pct=hold_pct,
                edge_pct=pnl_pct - hold_pct,
                maxdd=mdd, endinv=(base * c[-1] / final * 100) if final else 0.0,
                fees=fees, turnover_x=turnover / fund,
                trades=trades, bf=bf.tolist(), sf=sf.tolist(),
                cb=cb, cs=cs, eq=eq, hold_eq=hold_eq,
                ts=bars[:, 0], close=c,
                days=days, bar_seconds=bsec,
                trades_per_month=trades / months if months > 0 else 0.0,
                time_in_band=float(np.mean((c >= lo_b) & (c <= hi_s)))
                if len(buys) and len(sells) else UNSET,
                quote=quote, base=base,
                vol_capped_fills=int(ncapped),
                pen_frac=float(pen_frac), tick=float(tick),
                vol_cap_frac=float(vol_cap_frac))


def recycle_v11_parity_check(verbose: bool = False, n_series: int = 4,
                             n_bars: int = 800, seed: int = 11) -> bool:
    """(1) numba-vs-python parity of the v11 kernel; (2) v10-EQUIVALENCE:
    with penetration off and no volume cap, v11 must reproduce v10's kernel
    outputs bit-for-bit on random series."""
    rng = np.random.default_rng(seed)
    ok = True
    for k in range(n_series):
        n = n_bars
        rets = rng.normal(0, 0.01, n)
        cser = 100.0 * np.exp(np.cumsum(rets))
        o = np.roll(cser, 1); o[0] = 100.0
        h = np.maximum(o, cser) * (1 + np.abs(rng.normal(0, 0.004, n)))
        l = np.minimum(o, cser) * (1 - np.abs(rng.normal(0, 0.004, n)))
        ts = np.arange(n) * 3600.0
        qv = np.abs(rng.normal(500, 200, n))
        bars6 = np.column_stack([ts, o, h, l, cser, qv])
        buys = [95.0, 92.0, 89.0, 86.0]
        sells = [105.0, 108.0, 111.0, 115.0]
        kw = dict(fund=1000.0, quote_frac=0.5, fee=0.002, slip=0.001,
                  cooldown_seconds=3600, refresh_seconds=43200,
                  min_order_quote=1.0, event_refresh=True, body_only=False)
        # numba vs python parity (only meaningful when numba is present)
        if HAVE_NUMBA:
            a = recycle_sim_v11(bars6, buys, sells, **kw, pen_frac=0.0005,
                                tick=0.01, vol_cap_frac=0.25, use_numba=True)
            b = recycle_sim_v11(bars6, buys, sells, **kw, pen_frac=0.0005,
                                tick=0.01, vol_cap_frac=0.25, use_numba=False)
            same = (a["trades"] == b["trades"]
                    and abs(a["pnl"] - b["pnl"]) < 1e-9
                    and np.allclose(a["eq"], b["eq"], atol=1e-9)
                    and a["vol_capped_fills"] == b["vol_capped_fills"])
            ok &= same
            if verbose and not same:
                _log(f"  v11 parity FAIL on series {k}")
        # v10 equivalence with the new features off
        v10r = _v10.recycle_sim(bars6[:, :5], buys, sells, **kw)
        v11r = recycle_sim_v11(bars6, buys, sells, **kw,
                               pen_frac=0.0, tick=0.0, vol_cap_frac=0.0)
        same10 = (v10r["trades"] == v11r["trades"]
                  and abs(v10r["pnl"] - v11r["pnl"]) < 1e-9
                  and np.allclose(v10r["eq"], v11r["eq"], atol=1e-9)
                  and v10r["bf"] == v11r["bf"] and v10r["sf"] == v11r["sf"])
        ok &= same10
        if verbose:
            _log(f"  series {k}: v10-equiv={'OK' if same10 else 'FAIL'} "
                 f"trades={v11r['trades']}")
    return bool(ok)


# ======================================================================
# Slippage: floor + Roll + measured BOOK half-spread, in EVERY sim
# ======================================================================
def effective_slip_v11(bars: np.ndarray, cfg: Dict[str, Any],
                       book_half_spread_pct: float = 0.0) -> float:
    """max(floor, Roll half-spread, measured book half-spread), capped.
    Unlike v10, the measured book spread participates in the SEARCH and WF,
    not only in a post-hoc finalize gate."""
    extra = (float(book_half_spread_pct)
             if cfg.get("rc_book_spread_in_slip", True)
             and book_half_spread_pct == book_half_spread_pct else 0.0)
    return _v10.effective_slip(bars[:, :5], cfg, extra_half_spread_pct=extra)


def fetch_orderbook(uni: Dict[str, Any], pk: str, cfg: Dict[str, Any]
                    ) -> Optional[Dict[str, Any]]:
    """Raw order book -> {'bids': [(price, qty)...], 'asks': [...]} (one API
    call, both venues). v11.2: the engine now keeps the BOOK, not just a
    scalar depth, so depth can be measured wherever it actually matters."""
    try:
        if uni["exchange"] == "kraken":
            alt = uni["pair_alt"].get(pk, pk.replace("/", ""))
            res = (_base._get_json(f"{_base.KRAKEN}/Depth",
                                   params={"pair": alt, "count": 500},
                                   timeout=20) or {}).get("result", {})
            book = next(iter(res.values()), None) if res else None
        else:
            coin, quote = pk.split("/", 1)
            book = _base._get_json(f"{_base.NONKYC}/market/orderbook",
                                   params={"symbol": f"{coin}/{quote}"}, timeout=20)
        if not book:
            return None

        def lv(x):
            if isinstance(x, dict):
                return (float(x.get("price", x.get("p", 0))),
                        float(x.get("quantity", x.get("q", x.get("amount", 0)))))
            return float(x[0]), float(x[1])

        bids = sorted((lv(x) for x in book.get("bids", [])), reverse=True)
        asks = sorted(lv(x) for x in book.get("asks", []))
        if not bids or not asks:
            return None
        return dict(bids=bids, asks=asks)
    except Exception:
        return None


def depth_in_range(book: Optional[Dict[str, Any]], lo: float, hi: float,
                   rate: float = 1.0) -> float:
    """USD notional resting between lo and hi (inclusive) on both sides."""
    if not book:
        return UNSET
    d = (sum(p * q for p, q in book["bids"] if lo <= p <= hi)
         + sum(p * q for p, q in book["asks"] if lo <= p <= hi))
    return float(d) * float(rate)


def book_profile(book: Optional[Dict[str, Any]], rate: float = 1.0,
                 bands: Sequence[float] = (0.02, 0.05, 0.10, 0.25)
                 ) -> Dict[str, float]:
    """Spread + a DEPTH PROFILE across several bands + whole-book notional.

    Why: a fixed +-2% depth reading misjudges exactly the markets a ladder
    wants. NonKYC DASH/USDT (measured 2026-07-12) quotes dust at the touch
    and parks its real size ~2.6% out: +-2% = $2, +-5% = $29,820, whole book
    = $33,509. The old thin-book gate read the hole between the quotes and
    called a $30k market untradeable."""
    out: Dict[str, float] = {}
    if not book:
        return out
    bids, asks = book["bids"], book["asks"]
    bb, ba = bids[0][0], asks[0][0]
    mid = (bb + ba) / 2.0
    out["mid"] = mid
    out["spread_pct"] = (ba - bb) / mid * 100.0 if mid > 0 else UNSET
    out["book_total_usd"] = float(
        sum(p * q for p, q in bids) + sum(p * q for p, q in asks)) * rate
    out["n_bids"] = float(len(bids))
    out["n_asks"] = float(len(asks))
    for b in bands:
        out[f"depth_{b*100:g}pct"] = depth_in_range(
            book, mid * (1 - b), mid * (1 + b), rate)
    return out


def ladder_band_depth(book: Optional[Dict[str, Any]], ladder: Dict[str, Any],
                      rate: float = 1.0) -> float:
    """Depth resting inside the LADDER'S OWN price span (lowest buy rung ->
    highest sell rung). This is the liquidity that can actually interact with
    the rungs you are about to place; +-2% of mid is irrelevant if your rungs
    live at +-3-10%."""
    if not book or not ladder.get("buy_prices") or not ladder.get("sell_prices"):
        return UNSET
    lo = float(min(ladder["buy_prices"]))
    hi = float(max(ladder["sell_prices"]))
    return depth_in_range(book, lo, hi, rate)


def market_book_snapshot(uni: Dict[str, Any], pk: str, cfg: Dict[str, Any]
                         ) -> Dict[str, Any]:
    """Median-of-N book profiles + the last raw book (kept so depth can be
    re-measured over the deployed ladder's band without another API call).
    Median-of-N (rc_book_samples, default 3) because single snapshots of thin
    books were the main source of verdict flips between back-to-back runs."""
    n = max(1, int(cfg.get("rc_book_samples", 3)))
    profiles, last = [], None
    for i in range(n):
        book = fetch_orderbook(uni, pk, cfg)
        if book:
            last = book
            prof = book_profile(book, quote_usd_rate(uni, pk))
            if prof:
                profiles.append(prof)
        if i < n - 1:
            time.sleep(float(cfg.get("rc_book_sample_pause", 1.0)))
    if not profiles:
        return dict(book=None, samples=0)
    med = {k: float(np.median([p[k] for p in profiles if k in p]))
           for k in profiles[0]}
    med["samples"] = len(profiles)
    med["book"] = last
    return med


def market_depth_snapshot(uni: Dict[str, Any], pk: str, cfg: Dict[str, Any]
                          ) -> Tuple[float, float]:
    """(spread_pct, depth_usd) at the configured band -- back-compat shim."""
    snap = market_book_snapshot(uni, pk, cfg)
    band = float(cfg.get("depth_band", 0.02))
    return (snap.get("spread_pct", UNSET),
            snap.get(f"depth_{band*100:g}pct", UNSET))


def depth_for_sizing(snap: Dict[str, Any], ladder: Dict[str, Any],
                     rate: float, cfg: Dict[str, Any]) -> Tuple[float, str]:
    """The depth number that gates and sizes a market (v11.2).

    rc_depth_metric='ladder' (default): depth inside the ladder's own span,
    floored at rc_depth_min_band around mid so a pathologically narrow ladder
    cannot claim a pathologically small book. Falls back to the legacy band
    reading when there is no book or no ladder."""
    book = snap.get("book")
    band = float(cfg.get("depth_band", 0.02))
    legacy = snap.get(f"depth_{band*100:g}pct", UNSET)
    if str(cfg.get("rc_depth_metric", "ladder")).lower() != "ladder" or not book:
        return legacy, f"band_{band*100:g}pct"
    mid = float(snap.get("mid", UNSET))
    d_lad = ladder_band_depth(book, ladder, rate)
    minb = float(cfg.get("rc_depth_min_band", 0.05))
    d_min = (depth_in_range(book, mid * (1 - minb), mid * (1 + minb), rate)
             if mid == mid else UNSET)
    cands = [(d, n) for d, n in ((d_lad, "ladder_band"),
                                 (d_min, f"min_band_{minb*100:g}pct"))
             if d == d]
    if not cands:
        return legacy, f"band_{band*100:g}pct"
    return max(cands, key=lambda t: t[0])


def market_book_half_spread_pct(uni: Dict[str, Any], pk: str,
                                cfg: Dict[str, Any]) -> float:
    """Live order-book half-spread in percent (one API call, NaN-safe)."""
    spread_pct, _depth = market_depth_snapshot(uni, pk, cfg)
    return float(spread_pct) / 2.0 if spread_pct == spread_pct else 0.0


# ----------------------------------------------------------------------
# v11.1: quote-unit conversion (crypto-quoted pairs)
# ----------------------------------------------------------------------
def quote_usd_rate(uni: Dict[str, Any], pk: str) -> float:
    """USD per 1 unit of the pair's QUOTE currency (1.0 for USD-stables,
    ~1e5 for BTC, NaN-safe fallback 1.0)."""
    try:
        r = float(_base.usd_rate_of(uni, pk))
        return r if r == r and r > 0 else 1.0
    except Exception:
        return 1.0


def quote_scaled_cfg(uni: Dict[str, Any], pk: str, cfg: Dict[str, Any]
                     ) -> Tuple[Dict[str, Any], float]:
    """Per-market cfg whose fund and min-order are converted from USD into
    QUOTE units. v11.0 ran a BTC-quoted market with fund '1000' = 1000 BTC
    against bar volumes of ~0.001 BTC, so the volume cap crushed every fill
    to dust and the row read edge=0.000 -- inert garbage. With the
    conversion, a $1000 fund on a BTC pair is ~0.01 BTC and the sim,
    min-order, and volume cap are all denominated consistently."""
    rate = quote_usd_rate(uni, pk)
    if abs(rate - 1.0) < 1e-9:
        return cfg, rate
    c2 = dict(cfg)
    c2["fund_usd"] = float(cfg["fund_usd"]) / rate
    c2["rc_min_order_quote"] = float(cfg["rc_min_order_quote"]) / rate
    return c2, rate


def fund_quote_str(fund_quote: float, rate: float) -> Any:
    """Human-sane fund formatting: whole numbers for USD-stables, 6
    significant figures for crypto quotes (0.01 BTC, not 0.010000000001)."""
    if abs(rate - 1.0) < 1e-9:
        return int(round(fund_quote))
    return float(f"{fund_quote:.6g}")


# ----------------------------------------------------------------------
# v11.1: two-sided evidence mode ('blocks' | 'holdout' | 'either')
# ----------------------------------------------------------------------
_TS_FAIL_TOKEN = "two_sided_rate"


def apply_two_sided_mode(rep: Dict[str, Any], holdout: Optional[Dict[str, Any]],
                         cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Reconcile block-history two-sidedness with holdout two-sidedness.

    'blocks'  -> v10 behavior, untouched.
    'either'  -> if the HOLDOUT was two-sided, block two-sided failures are
                 waived (recorded in summary as two_sided_waived_by_holdout).
    'holdout' -> block two-sided failures are dropped entirely; an ACTIVE
                 holdout that was NOT two-sided adds its own failure.
    Only the two-sided gates are touched; every other gate stands."""
    mode = str(cfg.get("rc_gate_two_sided_mode", "either")).lower()
    if mode == "blocks" or rep is None:
        return rep
    fails = list(rep.get("failed_gates", []))
    ts_fails = [f for f in fails if _TS_FAIL_TOKEN in f]
    other = [f for f in fails if _TS_FAIL_TOKEN not in f]
    ho_two = bool((holdout or {}).get("two_sided", False))
    ho_active = bool((holdout or {}).get("active", False))
    if mode == "either":
        if ts_fails and ho_two:
            rep["failed_gates"] = other
            rep["summary"]["two_sided_waived_by_holdout"] = True
            rep["passed"] = (len(other) == 0)
        return rep
    if mode == "holdout":
        fails = other
        if holdout is not None and ho_active and not ho_two:
            fails = other + [f"holdout not two-sided "
                             f"({(holdout or {}).get('buy_fills', 0)} buys / "
                             f"{(holdout or {}).get('sell_fills', 0)} sells)"]
        rep["failed_gates"] = fails
        rep["summary"]["two_sided_mode"] = "holdout"
        rep["passed"] = (len(fails) == 0)
    return rep


# ----------------------------------------------------------------------
# v11.1: order-book verification for the shortlist (Cell 10)
# ----------------------------------------------------------------------
def verify_books(uni: Dict[str, Any], pairs: Sequence[str], cfg: Dict[str, Any],
                 samples: int = 5, pause: float = 4.0,
                 ladders: Optional[Dict[str, Dict[str, Any]]] = None) -> pd.DataFrame:
    """Poll each pair's live book `samples` times and report the DEPTH PROFILE
    (+-2/5/10/25% and the whole book), plus the depth inside each market's own
    deployed ladder span when `ladders` is given.

    Read it like this: `depth_2pct` tiny but `depth_5pct` large = the market
    quotes dust at the touch and parks real size further out (NonKYC
    DASH/USDT, 2026-07-12: $2 vs $29,820). That market is NOT thin -- it is
    ladder-shaped, and `depth_ladder_band` is the number that matters.
    `flaky=True` (depth swinging >5x across samples) = don't trust any single
    reading. `size_suggestion` uses depth_fraction x the sizing depth."""
    rows = []
    for pk in pairs:
        profs, books = [], []
        for i in range(int(samples)):
            book = fetch_orderbook(uni, pk, cfg)
            if book:
                books.append(book)
                p = book_profile(book, quote_usd_rate(uni, pk),
                                 cfg.get("rc_depth_profile_bands", (0.02, 0.05, 0.10, 0.25)))
                if p:
                    profs.append(p)
            if i < samples - 1:
                time.sleep(float(pause))
        row: Dict[str, Any] = dict(market=pk, samples_ok=len(profs))
        if not profs:
            row["note"] = "no book samples (endpoint failed)"
            rows.append(row)
            _log(f"  book check {pk}: FAILED")
            continue
        for k in profs[0]:
            if k in ("mid",):
                continue
            vals = [p[k] for p in profs if k in p and p[k] == p[k]]
            if vals:
                row[k if k.startswith(("depth", "spread", "book", "n_")) else k] = \
                    round(float(np.median(vals)), 4 if "spread" in k else 0)
        dcol = f"depth_{float(cfg.get('depth_band', 0.02))*100:g}pct"
        dvals = [p[dcol] for p in profs if p.get(dcol) == p.get(dcol)]
        if dvals:
            dmin, dmax = float(np.min(dvals)), float(np.max(dvals))
            row["flaky"] = bool(dmin > 0 and dmax / max(dmin, 1e-9) > 5.0)
        lad = (ladders or {}).get(pk)
        rate = quote_usd_rate(uni, pk)
        if lad and books:
            dl = float(np.median([ladder_band_depth(b, lad, rate) for b in books]))
            row["depth_ladder_band"] = round(dl, 0)
            size_depth = dl
        else:
            size_depth = row.get("depth_5pct", row.get(dcol, UNSET))
        if size_depth == size_depth:
            row["thin_med"] = bool(size_depth < float(cfg["min_depth_2pct"]))
            row["size_suggestion"] = round(min(float(cfg["depth_fraction"]) * size_depth,
                                               float(cfg["fund_ceil"])), 0)
        rows.append(row)
        _log(f"  book check {pk}: {row}")
    return pd.DataFrame(rows)


# ======================================================================
# Grid-harvest screen (model-free pair selection)
# ======================================================================
def zigzag_swings(closes: np.ndarray, gap_pct: float) -> int:
    """Count direction-alternating swings of at least gap_pct (zig-zag)."""
    c = np.asarray(closes, float)
    c = c[c > 0]
    if len(c) < 3 or gap_pct <= 0:
        return 0
    g = gap_pct / 100.0
    ext = c[0]
    dirn = 0
    swings = 0
    for x in c[1:]:
        if dirn == 0:                      # no direction yet: first +-g move
            if x >= ext * (1.0 + g):       # sets it (not counted as a swing)
                dirn = 1
                ext = x
            elif x <= ext * (1.0 - g):
                dirn = -1
                ext = x
        elif dirn > 0:
            if x > ext:
                ext = x
            elif x <= ext * (1.0 - g):
                swings += 1
                dirn = -1
                ext = x
        else:
            if x < ext:
                ext = x
            elif x >= ext * (1.0 + g):
                swings += 1
                dirn = 1
                ext = x
    return swings


def grid_harvest(bars: np.ndarray, cfg: Dict[str, Any],
                 slip: Optional[float] = None) -> Dict[str, float]:
    """Model-free harvest estimate: at gap = mult x round-trip-cost, count
    zig-zag swings; one round trip per two swings; net edge per round trip =
    gap - rt_cost. harvest_%/mo = round_trips/mo * net_edge_%. No parameters
    are fitted, so this cannot overfit -- it ranks MARKETS, not ladders."""
    bars = ensure6(bars)
    c = bars[:, 4]
    days = max((bars[-1, 0] - bars[0, 0]) / 86400.0, 1e-9)
    months = days / 30.4
    s = float(slip) if slip is not None else effective_slip_v11(bars, cfg)
    rt_cost = 2.0 * (float(cfg["fee"]) + s) * 100.0     # % per round trip
    out: Dict[str, float] = dict(harvest_rt_cost_pct=round(rt_cost, 3))
    best = -1e9
    best_gap = UNSET
    for m in cfg.get("rc_harvest_gap_mults", (1.5, 2.0, 3.0)):
        gap = rt_cost * float(m)
        swings = zigzag_swings(c, gap)
        rtpm = swings / 2.0 / months if months > 0 else 0.0
        hv = rtpm * (gap - rt_cost)
        out[f"harvest_{m:g}x_pct_mo"] = round(hv, 3)
        if hv > best:
            best, best_gap = hv, gap
    out["harvest_best_pct_mo"] = round(best, 3)
    out["harvest_best_gap_pct"] = round(best_gap, 3)
    return out


def rank_review_markets(screen_df: pd.DataFrame, hist: Dict[str, Any],
                        cfg: Dict[str, Any]) -> pd.DataFrame:
    """Blend the base composite rank with the harvest rank; adds harvest
    columns to the screener frame (nothing removed)."""
    col = "base" if "base" in screen_df.columns else "pairkey"
    rows = {}
    for pk in screen_df[col]:
        h = hist.get(pk)
        if h is None:
            continue
        rows[pk] = grid_harvest(h["bars"], cfg)
    hv = pd.DataFrame.from_dict(rows, orient="index")
    d = screen_df.set_index(col).join(hv).reset_index().rename(columns={"index": col})
    if "harvest_best_pct_mo" in d.columns:
        w = float(cfg.get("rc_harvest_rank_weight", 0.5))
        r_h = d["harvest_best_pct_mo"].rank(pct=True).fillna(0.0)
        r_c = d["composite"].rank(pct=True).fillna(0.0) if "composite" in d.columns else 0.5
        d["review_rank"] = (w * r_h + (1.0 - w) * r_c).round(3)
        d = d.sort_values("review_rank", ascending=False).reset_index(drop=True)
    return d


# ======================================================================
# Candidate rebuild (deploy re-anchoring) + v11 run/search/WF
# ======================================================================
def rebuild_candidate_at_anchor(cand: Dict[str, Any], new_anchor: float,
                                pdec: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Rebuild a candidate's ladder at a new anchor, preserving the exact
    RELATIVE offsets of its (possibly pdec-collapsed) rung set."""
    old = float(cand.get("anchor", UNSET))
    if not (old == old) or old <= 0 or new_anchor <= 0:
        return None
    c2 = copy.deepcopy(cand)
    offs_b = [(old - p) / old for p in cand["buy_prices"]]
    offs_s = [(p - old) / old for p in cand["sell_prices"]]
    buys = [float(_base.round_price(new_anchor * (1.0 - d), pdec)) for d in offs_b]
    sells = [float(_base.round_price(new_anchor * (1.0 + d), pdec)) for d in offs_s]
    buys = list(dict.fromkeys([p for p in buys if 0 < p < new_anchor]))
    sells = list(dict.fromkeys([p for p in sells if p > new_anchor]))
    if len(buys) < 2 or len(sells) < 2:
        return None
    c2["buy_prices"], c2["sell_prices"] = buys, sells
    c2["bw"] = np.asarray(cand["bw"], float)[:len(buys)]
    c2["sw"] = np.asarray(cand["sw"], float)[:len(sells)]
    c2["n_buy"], c2["n_sell"] = len(buys), len(sells)
    c2["anchor"] = float(new_anchor)
    c2["reanchored_from"] = old
    return c2


def _pen_kwargs(cfg: Dict[str, Any], pdec: Optional[int]) -> Dict[str, float]:
    if not cfg.get("rc_v11_fill_model", True):
        return dict(pen_frac=0.0, tick=0.0, vol_cap_frac=0.0)
    tick = (float(cfg.get("rc_fill_penetration_ticks", 1.0)) * 10.0 ** (-pdec)
            if pdec is not None else 0.0)
    return dict(pen_frac=float(cfg.get("rc_fill_penetration_pct", 0.0)),
                tick=tick,
                vol_cap_frac=float(cfg.get("rc_volume_cap_frac", 0.0)))


def run_ladder_v11(bars: np.ndarray, ladder: Dict[str, Any], cfg: Dict[str, Any],
                   stress: bool = False, slip: Optional[float] = None,
                   book_half: float = 0.0,
                   pdec: Optional[int] = None) -> Dict[str, Any]:
    """v11 twin of v10.run_ladder: same dials + penetration/volume realism +
    book-spread-aware slip. pdec sets the penetration tick."""
    kw = _v10._sim_kwargs(cfg, ladder)
    base_slip = (float(slip) if slip is not None
                 else effective_slip_v11(bars, cfg, book_half))
    if stress:
        kw["slip"] = base_slip + float(cfg["rc_stress_extra_slip"])
        kw["body_only"] = bool(cfg.get("rc_stress_body_only", True))
    else:
        kw["slip"] = base_slip
        kw["body_only"] = False
    pk = _pen_kwargs(cfg, pdec if pdec is not None else ladder.get("pdec"))
    return recycle_sim_v11(bars, ladder["buy_prices"], ladder["sell_prices"],
                           ladder.get("bw"), ladder.get("sw"), **kw, **pk)


def search_ladder_v11(train_bars: np.ndarray, cfg: Dict[str, Any],
                      pdec: Optional[int] = None, label: str = "",
                      book_half: float = 0.0,
                      return_table: bool = False) -> Dict[str, Any]:
    """v10's two-stage search on the v11 engine + overfit telemetry
    (fit_score_gap = best - median stage-1 score; big gap on 3 noisy folds
    of data = the winner is likelier to be a lucky draw)."""
    train_bars = ensure6(train_bars)
    slip_used = effective_slip_v11(train_bars, cfg, book_half)
    if cfg.get("rc_regularize_bars", True):
        train_bars, _ = regularize_bars6(train_bars)
    days = max((train_bars[-1, 0] - train_bars[0, 0]) / 86400.0, 1.0)
    cands = generate_candidates(train_bars[:, :5], cfg, pdec, label)
    if not cands:
        raise RuntimeError(f"{label}: no candidates survived construction")
    rows = []
    scored = []
    for cand in cands:
        cand["pdec"] = pdec
        r = run_ladder_v11(train_bars, cand, cfg, stress=False,
                           slip=slip_used, pdec=pdec)
        s = run_ladder_v11(train_bars, cand, cfg, stress=True,
                           slip=slip_used, pdec=pdec)
        sc = score_v10(r, s, cfg, days)
        scored.append((sc, cand, r, s))
        if return_table:
            rows.append(dict(candidate_id=cand["candidate_id"], stage="stage1",
                             score=round(sc, 3), edge_pct=round(r["edge_pct"], 3),
                             pnl_pct=round(r["pnl_pct"], 3),
                             hold_pct=round(r["hold_pct"], 3),
                             trades=r["trades"], maxdd=round(r["maxdd"], 3),
                             stress_edge=round(s["edge_pct"], 3),
                             n_buy=cand["n_buy"], n_sell=cand["n_sell"],
                             family=cand["family"], spacing=cand["spacing_curve"],
                             weights=cand["weight_curve"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    stage1_scores = np.array([x[0] for x in scored], float)
    best = None
    for sc, cand, r, s in scored[:int(cfg["rc_stage2_top_k"])]:
        for wcurve in cfg["rc_weight_curves"]:
            c2 = copy.deepcopy(cand)
            c2["bw"] = _weights_for_curve(c2["n_buy"], wcurve,
                                          cfg["rc_max_single_rung_weight_pct"])
            c2["sw"] = _weights_for_curve(c2["n_sell"], wcurve,
                                          cfg["rc_max_single_rung_weight_pct"])
            c2["weight_curve"] = wcurve
            r2 = run_ladder_v11(train_bars, c2, cfg, stress=False,
                                slip=slip_used, pdec=pdec)
            s2 = run_ladder_v11(train_bars, c2, cfg, stress=True,
                                slip=slip_used, pdec=pdec)
            sc2 = score_v10(r2, s2, cfg, days)
            if return_table:
                rows.append(dict(candidate_id=c2["candidate_id"], stage="stage2",
                                 score=round(sc2, 3),
                                 edge_pct=round(r2["edge_pct"], 3),
                                 pnl_pct=round(r2["pnl_pct"], 3),
                                 hold_pct=round(r2["hold_pct"], 3),
                                 trades=r2["trades"], maxdd=round(r2["maxdd"], 3),
                                 stress_edge=round(s2["edge_pct"], 3),
                                 n_buy=c2["n_buy"], n_sell=c2["n_sell"],
                                 family=c2["family"], spacing=c2["spacing_curve"],
                                 weights=wcurve))
            if best is None or sc2 > best[0]:
                best = (sc2, c2, r2, s2)
    sc, cand, r, s = best
    gap = float(sc - np.median(stage1_scores)) if len(stage1_scores) else UNSET
    return dict(best=cand, train_result=r, train_stress=s, train_score=float(sc),
                n_candidates=len(cands), train_days=int(round(days)),
                slip_used=float(slip_used), book_half_spread_pct=float(book_half),
                fit_score_gap=round(gap, 3),
                leaderboard=(pd.DataFrame(rows).sort_values("score", ascending=False)
                             .reset_index(drop=True)) if return_table else None)


def rolling_walkforward_v11(bars: np.ndarray, cfg: Dict[str, Any],
                            pdec: Optional[int] = None, label: str = "",
                            book_half: float = 0.0) -> Dict[str, Any]:
    """v10's leakage-safe rolling WF on the v11 engine (book-spread slip
    included in both the fit and the unseen-test evaluation)."""
    bars = ensure6(bars)
    windows = _v10.make_rolling_windows(bars[:, :5], cfg)
    ts = bars[:, 0]
    recs = []
    for w in windows:
        tr = bars[(ts >= w["train_start"]) & (ts <= w["train_end"])]
        te = bars[(ts >= w["test_start"]) & (ts <= w["test_end"])]
        fit = search_ladder_v11(tr, cfg, pdec, label=label, book_half=book_half)
        cand = fit["best"]
        te_slip = max(fit.get("slip_used", 0.0), effective_slip_v11(te, cfg, book_half))
        te2 = regularize_bars6(te)[0] if cfg.get("rc_regularize_bars", True) else te
        r = run_ladder_v11(te2, cand, cfg, stress=False, slip=te_slip, pdec=pdec)
        s = run_ladder_v11(te2, cand, cfg, stress=True, slip=te_slip, pdec=pdec)
        recs.append(dict(
            fold_idx=w["fold_idx"],
            train_start=pd.to_datetime(w["train_start"], unit="s").date().isoformat(),
            test_start=pd.to_datetime(w["test_start"], unit="s").date().isoformat(),
            test_end=pd.to_datetime(w["test_end"], unit="s").date().isoformat(),
            family=cand["family"], n_buy=cand["n_buy"], n_sell=cand["n_sell"],
            train_edge=round(fit["train_result"]["edge_pct"], 3),
            test_pct=round(r["pnl_pct"], 3), hold_pct=round(r["hold_pct"], 3),
            edge_pct=round(r["edge_pct"], 3),
            stress_edge=round(s["edge_pct"], 3),
            trades=r["trades"], buy_fills=int(sum(r["bf"])),
            sell_fills=int(sum(r["sf"])),
            two_sided=bool(sum(r["bf"]) > 0 and sum(r["sf"]) > 0),
            maxdd=round(r["maxdd"], 3), endinv=round(r["endinv"], 1),
            vol_capped_fills=r.get("vol_capped_fills", 0)))
    folds = pd.DataFrame(recs)
    if folds.empty:
        return dict(folds=folds, n_folds=0, wf_pass=False,
                    note="insufficient history for rolling validation")
    edge = folds.edge_pct.astype(float).to_numpy()
    two = folds.two_sided.astype(bool).to_numpy()
    summary = dict(
        n_folds=len(folds),
        edge_pos_rate=round(float(np.mean(edge > 0)), 3),
        two_sided_rate=round(float(np.mean(two)), 3),
        median_edge_pct=round(float(np.median(edge)), 3),
        median_test_pct=round(float(folds.test_pct.median()), 3),
        median_stress_edge=round(float(folds.stress_edge.median()), 3),
        worst_edge_pct=round(float(edge.min()), 3),
        median_trades=float(folds.trades.median()),
        total_trades=int(folds.trades.sum()))
    summary["wf_pass"] = bool(
        len(folds) >= int(cfg["rc_min_folds"])
        and summary["edge_pos_rate"] >= float(cfg["rc_wf_min_edge_pos_rate"])
        and summary["two_sided_rate"] >= float(cfg["rc_wf_min_two_sided_rate"])
        and summary["median_edge_pct"] >= float(cfg["rc_wf_min_median_edge"])
        and summary["worst_edge_pct"] >= float(cfg["rc_wf_worst_edge"]))
    return dict(folds=folds, **summary)


# ======================================================================
# Blocks + gates: v10 semantics kept, CLEAN-block gating added
# ======================================================================
def block_table_v11(res: Dict[str, Any], block_days: float = 15.0,
                    band: Optional[Tuple[float, float]] = None,
                    fit_span: Optional[Tuple[float, float]] = None) -> pd.DataFrame:
    """v10's block table + a clean `in_fit` flag (block overlaps the fit
    window) and a proper bar_seconds computation."""
    ts = np.asarray(res["ts"], float)
    eq = np.asarray(res["eq"], float)
    hold = np.asarray(res["hold_eq"], float)
    cb = np.asarray(res["cb"], float)
    cs = np.asarray(res["cs"], float)
    if len(ts) < 3:
        return pd.DataFrame()
    bsec = float(res.get("bar_seconds") or np.median(np.diff(ts)))
    idx = np.floor((ts - ts[0]) / (block_days * 86400.0)).astype(int)
    rows = []
    prev_eq, prev_hold, prev_cb, prev_cs = eq[0], hold[0], 0.0, 0.0
    for b in range(int(idx.max()) + 1):
        mask = idx == b
        if not mask.any():
            continue
        i0 = np.where(mask)[0][0]
        i1 = np.where(mask)[0][-1]
        span_days = (ts[i1] - ts[i0] + bsec) / 86400.0
        if span_days < 1.0:
            prev_eq, prev_hold, prev_cb, prev_cs = eq[i1], hold[i1], cb[i1], cs[i1]
            continue
        ret = (eq[i1] - prev_eq) / prev_eq * 100 if prev_eq > 0 else UNSET
        hret = (hold[i1] - prev_hold) / prev_hold * 100 if prev_hold > 0 else UNSET
        bfl = cb[i1] - prev_cb
        sfl = cs[i1] - prev_cs
        closes = np.asarray(res["close"], float)[mask]
        in_band = (float(np.mean((closes >= band[0]) & (closes <= band[1])))
                   if band is not None else UNSET)
        in_fit = bool(fit_span is not None
                      and ts[i1] >= fit_span[0] and ts[i0] <= fit_span[1])
        rows.append(dict(
            block=b + 1,
            start=pd.to_datetime(ts[i0], unit="s").date().isoformat(),
            end=pd.to_datetime(ts[i1], unit="s").date().isoformat(),
            days=round(span_days, 1),
            pnl_pct=round(ret, 3),
            hold_pct=round(hret, 3),
            edge_pct=round(ret - hret, 3),
            buy_fills=int(bfl),
            sell_fills=int(sfl),
            trades=int(bfl + sfl),
            two_sided=bool(bfl > 0 and sfl > 0),
            in_band_pct=round(in_band, 3) if in_band == in_band else UNSET,
            in_fit=in_fit,
            partial=bool(span_days < 0.6 * block_days),
        ))
        prev_eq, prev_hold, prev_cb, prev_cs = eq[i1], hold[i1], cb[i1], cs[i1]
    return pd.DataFrame(rows)


def block_gates_v11(blocks: pd.DataFrame, cfg: Dict[str, Any]
                    ) -> Tuple[bool, List[str], Dict[str, Any]]:
    """v10's band-aware gates over ALL blocks (identical fields), PLUS the
    same gates recomputed over CLEAN (out-of-fit) blocks. Passing requires
    both; clean fails are prefixed 'clean:' so reports show provenance."""
    passed_all, fails_all, summary = _v10.block_gates(blocks, cfg)
    if blocks is None or blocks.empty or "in_fit" not in blocks.columns:
        return passed_all, fails_all, summary
    clean = blocks[~blocks["in_fit"]]
    min_clean = int(cfg.get("rc_gate_min_clean_blocks", 4))
    fails = list(fails_all)
    if len(clean) < min_clean:
        fails.append(f"clean: only {len(clean)} out-of-fit blocks (< {min_clean})")
        summary.update(n_clean_blocks=int(len(clean)))
        return False, fails, summary
    p2, f2, s2 = _v10.block_gates(clean, cfg)
    summary.update({f"clean_{k}": v for k, v in s2.items()})
    summary["n_clean_blocks"] = int(len(clean))
    fails += [f"clean: {f}" for f in f2]
    return (passed_all and p2), fails, summary


def frozen_ladder_report_v11(bars: np.ndarray, ladder: Dict[str, Any],
                             cfg: Dict[str, Any], label: str = "",
                             slip: Optional[float] = None,
                             book_half: float = 0.0,
                             pdec: Optional[int] = None,
                             fit_span: Optional[Tuple[float, float]] = None
                             ) -> Dict[str, Any]:
    """v10's frozen report on the v11 engine, with in-fit block tagging and
    clean-block gating. All v10 summary fields preserved; adds clean_*,
    n_clean_blocks, vol_capped_fills, book_half_spread_pct."""
    bars = ensure6(bars)
    slip_used = (float(slip) if slip is not None
                 else effective_slip_v11(bars, cfg, book_half))
    gap_fill = 0.0
    if cfg.get("rc_regularize_bars", True):
        bars, gap_fill = regularize_bars6(bars)
    res = run_ladder_v11(bars, ladder, cfg, stress=False, slip=slip_used, pdec=pdec)
    stress = run_ladder_v11(bars, ladder, cfg, stress=True, slip=slip_used, pdec=pdec)
    band = (float(min(ladder["buy_prices"])), float(max(ladder["sell_prices"])))
    blocks = block_table_v11(res, float(cfg["rc_block_days"]), band=band,
                             fit_span=fit_span)
    passed, fails, summary = block_gates_v11(blocks, cfg)
    summary.update(dict(
        label=label, days=round(res["days"], 1), bar_seconds=int(res["bar_seconds"]),
        pnl_pct=round(res["pnl_pct"], 3), hold_pct=round(res["hold_pct"], 3),
        edge_pct=round(res["edge_pct"], 3), maxdd=round(res["maxdd"], 3),
        trades=res["trades"], trades_per_month=round(res["trades_per_month"], 1),
        endinv=round(res["endinv"], 1), fees=round(res["fees"], 2),
        stress_pnl_pct=round(stress["pnl_pct"], 3),
        stress_edge_pct=round(stress["edge_pct"], 3),
        stress_trades=stress["trades"],
        slip_used_pct=round(slip_used * 100, 3),
        candle_gap_fill=round(gap_fill, 3),
        vol_capped_fills=int(res.get("vol_capped_fills", 0)),
        book_half_spread_pct=round(float(book_half), 4),
        fill_model="v11" if cfg.get("rc_v11_fill_model", True) else "v10",
    ))
    rt_cost_pct = 2.0 * (float(_v10._sim_kwargs(cfg, ladder)["fee"]) + slip_used) * 100.0
    sanity = _v10._cycle_edge_gate(summary, cfg, rt_cost_pct)
    if sanity:
        fails = list(fails) + [sanity]
        passed = False
        summary["data_suspect"] = True
    return dict(result=res, stress=stress, blocks=blocks, summary=summary,
                passed=passed, failed_gates=fails, ladder=ladder)


# ======================================================================
# TRUE HOLDOUT deploy fit
# ======================================================================
def deploy_fit_with_holdout(bars: np.ndarray, cfg: Dict[str, Any],
                            pdec: Optional[int] = None, label: str = "",
                            book_half: float = 0.0,
                            report_bars: Optional[np.ndarray] = None
                            ) -> Dict[str, Any]:
    """Fit the deploy ladder WITHOUT the last rc_holdout_days, score the
    fitted (train-anchored) ladder ONCE on that unseen tail, then re-anchor
    the same relative geometry at the current price for deployment.

    The returned `holdout` dict is the only fully-clean OOS evidence for the
    deployed geometry: the geometry, the anchor it was priced at, and the
    weights were all frozen before the holdout began."""
    bars = ensure6(bars)
    hd = float(cfg.get("rc_holdout_days", 15.0))
    t_end = bars[-1, 0]
    cut = t_end - hd * 86400.0
    fit_bars = bars[bars[:, 0] < cut]
    min_fit = float(cfg.get("rc_min_train_days", 54))
    holdout = None
    if hd <= 0 or len(fit_bars) < 10 or \
            (fit_bars[-1, 0] - fit_bars[0, 0]) / 86400.0 < min_fit:
        fit_bars = bars
        cut = t_end
    train = slice_days(fit_bars, int(cfg["rc_train_days"]))
    fit = search_ladder_v11(train, cfg, pdec, label=label, book_half=book_half)
    cand = fit["best"]

    if cut < t_end:
        ho_src = ensure6(report_bars) if report_bars is not None else bars
        ho = ho_src[ho_src[:, 0] >= cut]
        if len(ho) >= 3:
            ho_slip = max(fit["slip_used"], effective_slip_v11(ho, cfg, book_half))
            ho2 = regularize_bars6(ho)[0] if cfg.get("rc_regularize_bars", True) else ho
            r = run_ladder_v11(ho2, cand, cfg, stress=False, slip=ho_slip, pdec=pdec)
            s = run_ladder_v11(ho2, cand, cfg, stress=True, slip=ho_slip, pdec=pdec)
            band = (float(min(cand["buy_prices"])), float(max(cand["sell_prices"])))
            in_band = float(np.mean((ho2[:, 4] >= band[0]) & (ho2[:, 4] <= band[1])))
            holdout = dict(
                days=round(r["days"], 1),
                start=pd.to_datetime(cut, unit="s").date().isoformat(),
                pnl_pct=round(r["pnl_pct"], 3), hold_pct=round(r["hold_pct"], 3),
                edge_pct=round(r["edge_pct"], 3),
                stress_edge_pct=round(s["edge_pct"], 3),
                trades=r["trades"], buy_fills=int(sum(r["bf"])),
                sell_fills=int(sum(r["sf"])),
                two_sided=bool(sum(r["bf"]) > 0 and sum(r["sf"]) > 0),
                maxdd=round(r["maxdd"], 3),
                in_band_pct=round(in_band, 3),
                active=bool(r["trades"] > 0
                            or in_band >= float(cfg["rc_gate_active_in_band"])),
                vol_capped_fills=r.get("vol_capped_fills", 0),
                anchor=float(cand.get("anchor", UNSET)),
            )

    deploy_anchor = _anchor_price(bars[:, :5])
    deployed = rebuild_candidate_at_anchor(cand, deploy_anchor, pdec) or cand
    deployed["pdec"] = pdec
    fit_span = (float(train[0, 0]), float(cut))
    return dict(fit=fit, holdout=holdout, deployed=deployed,
                fit_span=fit_span, holdout_days=hd if holdout else 0.0,
                deploy_anchor=float(deploy_anchor))


def holdout_gate(holdout: Optional[Dict[str, Any]], cfg: Dict[str, Any]
                 ) -> Optional[str]:
    """Deploy-gate string (None = pass). Dormant holdouts are not evidence."""
    if holdout is None:
        return "no holdout evaluated (history too short for a clean tail)"
    if not holdout.get("active", False):
        if cfg.get("rc_gate_holdout_require_active", True):
            return (f"holdout dormant (in_band {holdout.get('in_band_pct')}, "
                    f"{holdout.get('trades', 0)} trades) -- no OOS evidence")
        return None
    floor = float(cfg.get("rc_gate_holdout_min_edge", -2.0))
    if float(holdout["edge_pct"]) < floor:
        return (f"holdout {holdout['days']:g}d edge {holdout['edge_pct']:+.2f}% "
                f"< {floor:g}% floor (train-anchored ladder, unseen tail)")
    return None


# ======================================================================
# Per-market pipeline, YAML eval, finalize, save
# ======================================================================
def evaluate_market(pk: str, hist_h: Dict[str, Any], uni: Dict[str, Any],
                    cfg: Dict[str, Any], run_wf: bool = True,
                    hist_report: Optional[Dict[str, Any]] = None
                    ) -> Optional[Dict[str, Any]]:
    """v11 twin of v10.evaluate_market: WF (secondary) + HOLDOUT deploy fit +
    frozen block report of the DEPLOYED (re-anchored) ladder with in-fit
    tagging + harvest metrics. Same return shape as v10 plus
    holdout/deployed/harvest keys.

    v11.1: the order book is sampled ONCE here and the snapshot (spread,
    depth) rides along for finalize; fund/min-order are converted into the
    pair's QUOTE units; the two-sided evidence mode reconciles block history
    with the holdout."""
    h = hist_h.get(pk)
    if h is None:
        return None
    bars = slice_days(ensure6(h["bars"]), int(cfg["rc_eval_days"]))
    pdec = uni.get("pdec", {}).get(pk)
    snap = market_book_snapshot(uni, pk, cfg)                 # v11.2: one pull
    spread_pct = snap.get("spread_pct", UNSET)
    depth_usd = snap.get(f"depth_{float(cfg.get('depth_band', 0.02))*100:g}pct", UNSET)
    book_half = float(spread_pct) / 2.0 if spread_pct == spread_pct else 0.0
    cfg_m, q_rate = quote_scaled_cfg(uni, pk, cfg)
    wf = (rolling_walkforward_v11(bars, cfg_m, pdec, label=pk, book_half=book_half)
          if run_wf else dict(n_folds=0, wf_pass=None, folds=pd.DataFrame()))
    hr = (hist_report or {}).get(pk)
    if hr is not None:
        rep_bars = slice_days(ensure6(hr["bars"]), int(cfg["rc_eval_days"]))
        rep_src, rep_gran = hr.get("src"), hr.get("granularity", "?")
    else:
        rep_bars, rep_src, rep_gran = bars, h.get("src"), h.get("granularity", "?")

    dep = deploy_fit_with_holdout(bars, cfg_m, pdec, label=pk,
                                  book_half=book_half, report_bars=rep_bars)
    rep = frozen_ladder_report_v11(rep_bars, dep["deployed"], cfg_m,
                                   label=f"{pk} deploy", book_half=book_half,
                                   pdec=pdec, fit_span=dep["fit_span"])
    rep = apply_two_sided_mode(rep, dep["holdout"], cfg_m)
    harvest = grid_harvest(bars, cfg_m)
    # v11.2: depth that can actually interact with the rungs we will place
    book = snap.get("book")
    depth_ladder = ladder_band_depth(book, dep["deployed"], q_rate)
    depth_used, depth_basis = depth_for_sizing(snap, dep["deployed"], q_rate, cfg)
    return dict(pair=pk, src=rep_src, granularity=rep_gran,
                search_granularity=h.get("granularity", "?"),
                wf=wf, fit=dep["fit"], report=rep,
                holdout=dep["holdout"], deployed=dep["deployed"],
                deploy_anchor=dep["deploy_anchor"],
                book_half_spread_pct=book_half,
                spread_pct_sampled=spread_pct, depth_usd_sampled=depth_usd,
                depth_ladder_band=depth_ladder, depth_used=depth_used,
                depth_basis=depth_basis, book_snapshot=snap,
                quote_usd_rate=q_rate, harvest=harvest)


def evaluate_controller_yamls(parsed_list: Sequence[Dict[str, Any]],
                              hist_h: Dict[str, Any], uni: Dict[str, Any],
                              cfg: Dict[str, Any]
                              ) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    """v10's YAML benchmark on the v11 engine (live ladders have no fit
    window on this data, so every block is clean). Same columns as v10 plus
    vol_capped_fills."""
    rows, details = [], {}
    for parsed in parsed_list:
        ladder = controller_to_ladder(parsed, cfg)
        if ladder is None:
            continue
        pk = ladder["trading_pair"]
        h = hist_h.get(pk)
        label = f"{ladder['controller_id']} ({pk})"
        if h is None:
            rows.append(dict(controller=ladder["controller_id"], pair=pk, src="n/a",
                             note="no history loaded for this market"))
            continue
        bars = slice_days(ensure6(h["bars"]), int(cfg["rc_eval_days"]))
        pdec = uni.get("pdec", {}).get(pk)
        cfg_m, _q = quote_scaled_cfg(uni, pk, cfg)   # YAML carries its own fund
        book_half = market_book_half_spread_pct(uni, pk, cfg)
        rep = frozen_ladder_report_v11(bars, ladder, cfg_m, label=label,
                                       book_half=book_half, pdec=pdec)
        details[ladder["controller_id"]] = rep
        s = rep["summary"]
        rows.append(dict(controller=ladder["controller_id"], pair=pk, src=h.get("src"),
                         days=s["days"], blocks=s.get("n_blocks", 0),
                         pnl_pct=s["pnl_pct"], hold_pct=s["hold_pct"],
                         edge_pct=s["edge_pct"],
                         edge_pos_rate=s.get("edge_pos_rate"),
                         abs_pos_rate=s.get("abs_pos_rate"),
                         worst_block_edge=s.get("worst_block_edge"),
                         trades=s["trades"], trades_per_month=s["trades_per_month"],
                         med_trades_per_block=s.get("median_trades_per_block"),
                         maxdd=s["maxdd"], endinv=s["endinv"],
                         stress_edge_pct=s["stress_edge_pct"],
                         vol_capped_fills=s.get("vol_capped_fills", 0),
                         passed=rep["passed"],
                         failed_gates="; ".join(rep["failed_gates"])))
    return pd.DataFrame(rows), details


def finalize_v11(evals: Dict[str, Dict[str, Any]], uni: Dict[str, Any],
                 cfg: Dict[str, Any],
                 yaml_reports: Optional[Dict[str, Dict[str, Any]]] = None
                 ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """v10's finalize + the v11 gates (holdout, clean blocks come in via the
    report's failed_gates) + harvest/overfit telemetry. Every v10 column is
    preserved; configs keep every v10 key so v10's copy/paste renderer works
    byte-identically."""
    rows, configs = [], []
    for pk, ev in evals.items():
        if ev is None:
            continue
        cand = ev["deployed"]
        rep = ev["report"]
        wf = ev["wf"]
        ho = ev.get("holdout")
        s = rep["summary"]
        pdec = uni.get("pdec", {}).get(pk)
        # ---- v11.1: sizing from the SNAPSHOT taken in evaluate_market ----
        spread_pct = ev.get("spread_pct_sampled", UNSET)
        depth_usd = ev.get("depth_usd_sampled", UNSET)          # legacy +-2%
        # v11.2: gate and size on the depth that can reach the RUNGS
        depth_used = ev.get("depth_used", UNSET)
        depth_basis = ev.get("depth_basis", "band")
        if not (depth_used == depth_used):
            depth_used, depth_basis = depth_usd, "band_legacy"
        if not (spread_pct == spread_pct) and not (depth_used == depth_used):
            max_fund, spread_pct, depth_usd, vol_usd = _v10._fund_sizing(uni, pk, cfg)
            depth_used, depth_basis = depth_usd, "band_legacy"
        else:
            vol_usd = float(uni["df"].set_index("pairkey").vol_usd.get(pk, UNSET))
            vol_term = cfg["vol_fraction"] * vol_usd if vol_usd == vol_usd else float("inf")
            depth_term = (cfg["depth_fraction"] * depth_used
                          if depth_used == depth_used else float("inf"))
            basis = min(vol_term, depth_term)
            max_fund = (_base.round_fund(basis, cfg) if basis != float("inf")
                        else cfg["fund_floor"])
        max_fund = int(max_fund)
        q_rate = float(ev.get("quote_usd_rate", quote_usd_rate(uni, pk)))
        max_fund_quote = max_fund / q_rate            # what the controller takes
        quote_ccy = uni.get("quote_of", {}).get(pk, "quote")
        gates: List[str] = list(rep["failed_gates"])
        hg = holdout_gate(ho, cfg)
        if hg:
            gates.append(hg)
        slip_used = float(s.get("slip_used_pct", cfg["slip_floor"] * 100)) / 100.0
        meas_slip = (spread_pct / 200.0) if spread_pct == spread_pct else 0.0
        if meas_slip > slip_used + cfg["rc_stress_extra_slip"]:
            gates.append(f"live half-spread {meas_slip*1e4:.0f}bps exceeds the "
                         f"{slip_used*1e4:.0f}bps slip the report already charged")
        if wf.get("wf_pass") is False:
            gates.append("rolling WF (process check) failed")
        p_last = uni.get("last_of", {}).get(pk, UNSET)
        mq_ok, mq_need = _base.min_qty_check(
            cand["buy_prices"], cand["sell_prices"], cand["bw"], cand["sw"],
            max_fund_quote, cfg, uni.get("min_qty", {}).get(pk),
            p_last if p_last == p_last else float(rep["result"]["close"][-1]))
        if not mq_ok:
            gates.append(f"min-qty needs fund >= {mq_need:,.6g} {quote_ccy}"
                         + (f" (~${mq_need * q_rate:,.0f})" if q_rate != 1.0 else ""))
        if depth_used == depth_used and depth_used < cfg["min_depth_2pct"]:
            gates.append(f"thin book (${depth_used:,.0f} in the {depth_basis})")
        if ev.get("granularity") == "1d":
            gates.append("evaluated on DAILY bars only (intraday unavailable)")
        fmt_problems = validate_ladder(cand["buy_prices"], cand["sell_prices"], pdec)
        if fmt_problems:
            gates.extend(fmt_problems)
        validation = ("CONFIRMED" if rep["passed"] and not gates
                      else ("GATED" if rep["passed"] else "SUSPECT"))
        hv = ev.get("harvest", {})
        rows.append(dict(
            base=pk, trading_pair=pk.replace("/", "-"), src=ev.get("src"),
            granularity=ev.get("granularity"), validation=validation,
            rungs=f"{cand['n_buy']}+{cand['n_sell']}",
            family=cand["family"], spacing=cand["spacing_curve"],
            weights=cand["weight_curve"],
            pnl_pct=s["pnl_pct"], hold_pct=s["hold_pct"], edge_pct=s["edge_pct"],
            edge_pos_rate=s.get("edge_pos_rate"), abs_pos_rate=s.get("abs_pos_rate"),
            worst_block_edge=s.get("worst_block_edge"),
            med_trades_per_block=s.get("median_trades_per_block"),
            trades=s["trades"], maxdd=s["maxdd"], endinv=s["endinv"],
            n_active_blocks=s.get("n_active_blocks"),
            slip_used_pct=s.get("slip_used_pct"),
            data_suspect=bool(s.get("data_suspect", False)),
            stress_edge_pct=s["stress_edge_pct"],
            wf_pass=wf.get("wf_pass"), wf_edge_pos_rate=wf.get("edge_pos_rate"),
            wf_median_edge=wf.get("median_edge_pct"),
            # ---- v11 additions (nothing above was removed) ----
            holdout_edge_pct=(ho or {}).get("edge_pct"),
            holdout_trades=(ho or {}).get("trades"),
            holdout_two_sided=(ho or {}).get("two_sided"),
            holdout_active=(ho or {}).get("active"),
            n_clean_blocks=s.get("n_clean_blocks"),
            clean_edge_pos_rate=s.get("clean_edge_pos_rate"),
            clean_worst_block_edge=s.get("clean_worst_block_edge"),
            vol_capped_fills=s.get("vol_capped_fills"),
            book_half_spread_pct=s.get("book_half_spread_pct"),
            fit_score_gap=ev["fit"].get("fit_score_gap"),
            harvest_best_pct_mo=hv.get("harvest_best_pct_mo"),
            harvest_best_gap_pct=hv.get("harvest_best_gap_pct"),
            fill_model=s.get("fill_model", "v11"),
            two_sided_waived_by_holdout=bool(s.get("two_sided_waived_by_holdout", False)),
            quote_usd_rate=q_rate,
            max_fund_quote=fund_quote_str(max_fund_quote, q_rate),
            max_fund=max_fund,
            spread_pct=round(spread_pct, 4) if spread_pct == spread_pct else UNSET,
            depth_2pct=round(depth_usd, 0) if depth_usd == depth_usd else UNSET,
            depth_used=_num(depth_used, 0),
            depth_basis=depth_basis,
            depth_ladder_band=_num(ev.get("depth_ladder_band"), 0),
            book_total_usd=_num((ev.get("book_snapshot") or {}).get("book_total_usd"), 0),
            gates="; ".join(gates)))
        configs.append(dict(
            symbol=pk, trading_pair=pk.replace("/", "-"), exchange=uni["exchange"],
            validation=validation, gates=gates,
            passive_order_placement=True,
            # v11.1: QUOTE units (the controller's own denomination). For
            # USD-stables this is the same dollar figure as before; for
            # crypto quotes it is now e.g. 0.01 BTC instead of a wrong 1000.
            max_fund_value_quote=fund_quote_str(max_fund_quote, q_rate),
            total_amount_quote=fund_quote_str(max_fund_quote, q_rate),
            max_fund_value_usd=max_fund,
            quote_usd_rate=q_rate,
            buy_prices=format_ladder_prices(cand["buy_prices"], pdec),
            sell_prices=format_ladder_prices(cand["sell_prices"], pdec),
            buy_amounts_pct=_base.weights_pct(cand["bw"]),
            sell_amounts_pct=_base.weights_pct(cand["sw"]),
            engine=dict(name="ladder_lab_recycle_v11", version=__version__,
                        granularity=ev.get("granularity"),
                        train_days=ev["fit"]["train_days"],
                        family=cand["family"], spacing=cand["spacing_curve"],
                        weight_curve=cand["weight_curve"],
                        deploy_anchor=ev.get("deploy_anchor"),
                        fill_model=s.get("fill_model", "v11"),
                        penetration_pct=cfg.get("rc_fill_penetration_pct"),
                        volume_cap_frac=cfg.get("rc_volume_cap_frac"),
                        book_half_spread_pct=ev.get("book_half_spread_pct")),
            block_consistency=dict(passed=rep["passed"],
                                   **{k: v for k, v in s.items() if k != "label"}),
            holdout=ho,
            harvest=hv,
            walkforward=dict(passed=wf.get("wf_pass"),
                             edge_pos_rate=wf.get("edge_pos_rate"),
                             median_edge_pct=wf.get("median_edge_pct"),
                             worst_edge_pct=wf.get("worst_edge_pct"),
                             n_folds=wf.get("n_folds"))))
    df = pd.DataFrame(rows)
    if not df.empty:
        order = {"CONFIRMED": 0, "GATED": 1, "SUSPECT": 2}
        df["_o"] = df.validation.map(order).fillna(9) + 10 * df.data_suspect.astype(int)
        df = (df.sort_values(["_o", "edge_pos_rate", "edge_pct"],
                             ascending=[True, False, False])
                .drop(columns="_o").reset_index(drop=True))
    return df, configs


# ======================================================================
# v11.1: multi-file JSONL calibration
# ======================================================================
def extract_fills_range_ladder(path: Any, max_lines: int = 500000) -> pd.DataFrame:
    """Schema-exact fill extractor for the range_inventory_ladder controller's
    diagnostic JSONL (schema_version 10): `range_ladder_fill_booked` events.
      ts     <- ts_ms / 1000
      side   <- side ('BUY'/'SELL' -> lower)
      amount <- d_base
      price  <- d_quote / d_base   (falls back to the level_id price)
      fees   <- d_fees; plus level_id / executor_id for provenance.
    The v10 generic extractor does not recognize this schema (returns 0 rows),
    which is why collect_jsonl_fills tries this one FIRST."""
    rows = []
    try:
        f = open(path, "r", errors="replace")
    except OSError:
        return pd.DataFrame()
    with f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line or '"range_ladder_fill_booked"' not in line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("event_type") != "range_ladder_fill_booked":
                continue
            try:
                ts = float(rec["ts_ms"]) / 1000.0
                amt = abs(float(rec.get("d_base", "nan")))
                dq = abs(float(rec.get("d_quote", "nan")))
                price = dq / amt if amt > 0 and dq == dq else UNSET
                if not (price == price):                    # level_id fallback
                    lid = str(rec.get("level_id", ""))
                    price = float(lid.split("_", 1)[1]) if "_" in lid else UNSET
                side = str(rec.get("side", "")).lower()
                if side not in ("buy", "sell") or not (price == price) or amt <= 0:
                    continue
                rows.append(dict(ts=ts, side=side, price=price, amount=amt,
                                 fees=float(rec.get("d_fees", 0) or 0),
                                 level_id=rec.get("level_id"),
                                 executor_id=rec.get("executor_id"),
                                 trading_pair=rec.get("trading_pair")))
            except (KeyError, TypeError, ValueError):
                continue
    return pd.DataFrame(rows)


def first_existing(paths: Any) -> Optional[str]:
    """First real file behind a path / list / glob pattern (None if nothing
    matches) -- for schema sniffing without FileNotFoundError on raw globs."""
    import glob as _glob
    if isinstance(paths, (str, Path)):
        paths = [paths]
    for p in paths:
        hits = sorted(_glob.glob(str(p)))
        for h in hits:
            if Path(h).is_file():
                return h
        if not hits and Path(str(p)).is_file():
            return str(p)
    return None


def collect_jsonl_fills(paths: Any) -> pd.DataFrame:
    """Extract fills from ONE OR MANY diagnostic JSONL files. `paths` may be
    a single path, a list/tuple of paths, and any entry may be a glob
    pattern ('logs/xmr_*.jsonl'). Per file, the schema-exact range_ladder
    extractor is tried first, then v10's generic one -- whichever finds more
    fills wins. Files are merged chronologically and deduplicated on
    (ts, side, price, amount), so overlapping log rotations are safe.
    Adds a source_file column for provenance."""
    import glob as _glob
    if isinstance(paths, (str, Path)):
        paths = [paths]
    files: List[str] = []
    for p in paths:
        hits = sorted(_glob.glob(str(p)))
        files.extend(hits if hits else [str(p)])
    frames = []
    for fp in dict.fromkeys(files):           # de-dupe file list, keep order
        try:
            df = extract_fills_range_ladder(fp)
            if df.empty:
                df = extract_fills_from_jsonl(fp)
        except FileNotFoundError:
            _log(f"  collect_jsonl_fills: missing {fp}")
            continue
        except Exception as e:
            _log(f"  collect_jsonl_fills: {fp}: {e}")
            continue
        if df is not None and not df.empty:
            df = df.copy()
            df["source_file"] = fp
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    subset = [c for c in ("ts", "side", "price", "amount") if c in out.columns]
    out = (out.drop_duplicates(subset=subset or None)
              .sort_values("ts").reset_index(drop=True))
    return out


def fills_sufficiency(fills: pd.DataFrame) -> str:
    """Plain-language verdict on whether a fill set can calibrate anything.
    Rule of thumb: relative error of a fills-per-window estimate ~ 1/sqrt(N)."""
    if fills is None or fills.empty:
        return "no fills -- nothing to calibrate"
    n = len(fills)
    days = (float(fills.ts.max()) - float(fills.ts.min())) / 86400.0
    if n < 2 or days < 0.05:                       # v11.1.3: no rate from a point
        return (f"{n} fill(s), window ~{days*24:.1f}h -> TOO THIN: a rate needs "
                "at least a few fills spread over time; keep logging")
    two = (fills.side == "buy").any() and (fills.side == "sell").any()
    err = 100.0 / math.sqrt(n)
    msg = (f"{n} fills over {days:.1f}d "
           f"(~{n / max(days, 1e-9) * 15:.0f}/15d, +-{err:.0f}% count error)")
    if n < 15 or days < 10:
        return msg + " -> TOO THIN: directional hint only, do not tune knobs on this"
    if n < 30 or days < 15 or not two:
        return msg + (" -> marginal: fine for a first sanity ratio, keep logging"
                      + ("" if two else " [one-sided -- sell/buy balance unverifiable]"))
    if n < 60 or days < 30:
        return msg + " -> usable: calibrate the volume-cap/penetration direction"
    return msg + " -> solid: trust the ratio, tune knobs to bring it to ~1.0"


def compare_live_vs_sim_v11(fills: pd.DataFrame, bars: np.ndarray,
                            ladder: Dict[str, Any], cfg: Dict[str, Any],
                            pdec: Optional[int] = None,
                            book_half: float = 0.0) -> Dict[str, Any]:
    """v10's live-vs-sim comparison, run under the v11 FILL MODEL (penetration
    + volume cap + book-spread slip) on Nx6 bars -- this is the number that
    calibrates rc_volume_cap_frac / rc_fill_penetration_pct:
      ratio >> 1  -> sim over-fills  -> raise penetration / lower volume cap
      ratio << 1  -> sim under-fills -> your live edge is BETTER than reported
                     (or the candle source misses your venue's ping-pong)."""
    if fills is None or fills.empty:
        return dict(note="no live fills extracted")
    t0, t1 = float(fills.ts.min()), float(fills.ts.max())
    if len(fills) < 2 or (t1 - t0) < 0.05 * 86400.0:   # v11.1.3
        return dict(note=f"only {len(fills)} fill(s) over {(t1-t0)/3600:.1f}h -- "
                         "no meaningful rate; keep logging",
                    fills_sufficiency=fills_sufficiency(fills))
    bars = ensure6(bars)
    m = (bars[:, 0] >= t0 - 3600) & (bars[:, 0] <= t1 + 3600)
    window = bars[m]
    if len(window) < 24:
        return dict(note="candle window too short for comparison")
    res = run_ladder_v11(window, ladder, cfg, stress=False,
                         book_half=book_half, pdec=pdec)
    days = (t1 - t0) / 86400.0
    live_b = int((fills.side == "buy").sum())
    live_s = int((fills.side == "sell").sum())
    out = dict(window_days=round(days, 1),
               live_buy_fills=live_b, live_sell_fills=live_s,
               live_fills_per_day=round((live_b + live_s) / max(days, 1e-9), 2),
               sim_buy_fills=int(sum(res["bf"])), sim_sell_fills=int(sum(res["sf"])),
               sim_fills_per_day=round(res["trades"] / max(days, 1e-9), 2),
               sim_pnl_pct=round(res["pnl_pct"], 3),
               sim_edge_pct=round(res["edge_pct"], 3),
               vol_capped_fills=int(res.get("vol_capped_fills", 0)),
               fill_model="v11" if cfg.get("rc_v11_fill_model", True) else "v10",
               fills_sufficiency=fills_sufficiency(fills))
    ratio = (out["sim_fills_per_day"] / out["live_fills_per_day"]
             if out["live_fills_per_day"] else float("nan"))
    out["sim_over_live_fill_ratio"] = round(ratio, 2) if ratio == ratio else float("nan")
    return out


# ======================================================================
# v11.3: fully deployable controller YAMLs
# ======================================================================
_YAML_TIER_DOC = {
    "CONFIRMED": "passed every block-consistency and deploy gate",
    "CANDIDATE": "GATED on the WF process check only, but holdout + clean "
                 "blocks are strong -- paper it for one 15d block first",
    "REFRESH": "this pair is ALREADY LIVE; this file is a re-fit of the same "
               "market at today's anchor. Do NOT drop it over the running "
               "config blindly -- compare rungs first, and if you adopt it, "
               "bump the id and start a clean state file",
}


def yaml_deploy_selection(final_df: pd.DataFrame, cfg: Dict[str, Any],
                          deployed_pairs: Optional[Sequence[str]] = None
                          ) -> Dict[str, str]:
    """{pair: tier} for every market that deserves a generated YAML.
    CONFIRMED always; GATED qualifies as CANDIDATE only when its sole gate is
    the WF process check and the clean OOS evidence is strong; anything
    already live gets a REFRESH file regardless of verdict."""
    tiers: Dict[str, str] = {}
    dep = {str(p) for p in (deployed_pairs or [])}
    if final_df is None or final_df.empty:
        return {p: "REFRESH" for p in dep}
    for _, r in final_df.iterrows():
        pk = r["base"]
        if r["validation"] == "CONFIRMED":
            tiers[pk] = "CONFIRMED"
            continue
        if r["validation"] == "GATED":
            gates = str(r.get("gates", "") or "")
            only_wf = (gates.strip() != "" and
                       all("rolling WF" in g for g in gates.split(";") if g.strip()))
            ho = float(r.get("holdout_edge_pct") or UNSET)
            cepr = float(r.get("clean_edge_pos_rate") or UNSET)
            if (only_wf and ho == ho and cepr == cepr
                    and ho >= float(cfg.get("rc_yaml_min_holdout_edge", 2.0))
                    and bool(r.get("holdout_two_sided"))
                    and cepr >= float(cfg.get("rc_yaml_min_clean_epr", 0.6))):
                tiers[pk] = "CANDIDATE"
    for p in dep:
        tiers.setdefault(p, "REFRESH")
        if p in tiers and tiers[p] in ("CONFIRMED", "CANDIDATE"):
            tiers[p] = tiers[p] + "+REFRESH"
    return tiers


def render_deploy_yaml(config: Dict[str, Any], cfg: Dict[str, Any],
                       tier: str = "CONFIRMED",
                       run_id: str = "", extra_note: str = "") -> Tuple[str, str]:
    """Render one fully deployable range_inventory_ladder YAML (returns
    (controller_id, yaml_text)). Field set and conventions mirror the user's
    live configs (verified round-trippable through parse_controller_yaml /
    controller_to_ladder in the test suite).

    Seeding: a FRESH deployment claims 0 base and seeds rc_yaml_seed_frac of
    the cap in QUOTE (buy-first, accumulates base). If you already hold the
    base asset, set claimed_base_value_quote to its value before starting."""
    exch = config["exchange"]
    base, quote = config["symbol"].split("/", 1)
    prefix = "k_" if exch == "kraken" else ""
    stamp = run_id or time.strftime("%Y%m%d")
    cid = f"{prefix}range_inventory_ladder_{base.lower()}_{quote.lower()}_auto_{stamp}"
    cap = config["max_fund_value_quote"]
    seed = cap * float(cfg.get("rc_yaml_seed_frac", 0.5))
    seed = fund_quote_str(seed, float(config.get("quote_usd_rate", 1.0)))
    fee = float(config.get("fee", cfg.get("fee", 0.002)))
    eng = config.get("engine", {})
    ho = config.get("holdout") or {}
    bc = config.get("block_consistency") or {}
    q_rate = float(config.get("quote_usd_rate", 1.0))
    min_order = fund_quote_str(float(cfg.get("rc_min_order_quote", 1.0)) / q_rate, q_rate)

    def csv_(xs):
        return ",".join(str(x) for x in xs)

    tier_base = tier.split("+")[0]
    lines = [
        "# " + "=" * 76,
        f"#  range_inventory_ladder -- {exch.upper()} {config['symbol']} (AUTO-GENERATED)",
        f"#  Generated by ladder_lab_recycle_v11 {__version__} on {time.strftime('%Y-%m-%d %H:%M')}",
        f"#  TIER: {tier} -- {_YAML_TIER_DOC.get(tier_base, '')}",
        f"#  Evidence: validation={config.get('validation')}"
        f" | holdout_edge={ho.get('edge_pct', 'n/a')}% ({ho.get('trades', 0)} fills,"
        f" two_sided={ho.get('two_sided', 'n/a')})"
        f" | 180d edge={bc.get('edge_pct', 'n/a')}% | maxdd={bc.get('maxdd', 'n/a')}%",
        f"#  Fill model: {eng.get('fill_model', 'v11')} (penetration"
        f" {eng.get('penetration_pct')}, vol-cap {eng.get('volume_cap_frac')},"
        f" book half-spread {_num(eng.get('book_half_spread_pct'), 4)}%)",
    ]
    if config.get("gates"):
        lines.append(f"#  Open gates: {'; '.join(config['gates'])}")
    if extra_note:
        lines.append(f"#  {extra_note}")
    lines += [
        "#  DISCIPLINE: deploy at or below the cap; treat the FIRST live 15-day",
        "#  block as the final gate (holdout above is the expectation to beat).",
        "# " + "=" * 76,
        "",
        "# --- Identity ---",
        f"id: {cid}",
        "controller_name: range_inventory_ladder",
        "controller_type: market_making",
        "",
        "# --- Market ---",
        f"connector_name: {exch}",
        f"trading_pair: {config['trading_pair']}",
        f"fee_rate: {fee}",
        "",
        "# --- Managed fund ---",
        "ledger_funded_budgets: true",
        f"total_amount_quote: {seed}          # seed = {float(cfg.get('rc_yaml_seed_frac', 0.5))*100:g}% of cap, in QUOTE",
        "allow_initialize_with_unavailable_wallet_funds: true",
        f"max_fund_value_quote: {config['max_fund_value_quote']}       # engine-sized hard cap",
        "use_wallet_balance: true",
        "claimed_base_value_quote: 0         # FRESH deploy: buy-first. If you already",
        f"                                    #   hold {base}, set this to its quote value.",
        "",
        "# --- The ladder (fixed rungs + welded relative weights) ---",
        f"buy_prices: {csv_(config['buy_prices'])}",
        f"buy_amounts_pct: {csv_(config['buy_amounts_pct'])}",
        f"sell_prices: {csv_(config['sell_prices'])}",
        f"sell_amounts_pct: {csv_(config['sell_amounts_pct'])}",
        "",
        "# --- Refresh / re-center (matches the simulated event model) ---",
        "event_refresh_enabled: true",
        f"executor_refresh_time: {int(cfg.get('rc_refresh_seconds', 43200))}",
        f"buy_cooldown_time: {int(cfg.get('rc_cooldown_seconds', 3600))}",
        f"sell_cooldown_time: {int(cfg.get('rc_cooldown_seconds', 3600))}",
        "",
        "# --- Order placement ---",
        f"min_order_quote: {min_order}",
        "allow_partial_levels: true",
        "passive_order_placement: true",
        "",
        "# --- Unattended-run safety ---",
        "max_session_duration_hours: 66000",
        "cancel_orders_on_session_end: true",
        "max_market_data_unavailable_seconds: 900",
        "cancel_orders_on_market_data_hard_pause: true",
        "",
        "# --- Diagnostics (Cell 11 calibration reads these) ---",
        "diagnostic_log_enabled: true",
        f"diagnostic_log_file_name: {cid}_diagnostic.jsonl",
        "diagnostic_heartbeat_interval_seconds: 300",
        "",
        "# --- State / control ---",
        f"state_file_name: {cid}.json",
        "manual_kill_switch: false",
        "",
    ]
    return cid, "\n".join(lines)


# ======================================================================
# v11.3.1: resilient universe construction
# ======================================================================
def build_universe(exchange: str, cfg: Dict[str, Any],
                   retries: int = 4, base_sleep: float = 15.0
                   ) -> Dict[str, Any]:
    """Universe builder that survives a flaky exchange API.

    The base builders give up after ~2s of quick retries, so a transient
    NonKYC hiccup / rate-limit window / VPN-exit-IP challenge kills the run
    on its very first call. This wrapper (a) retries PATIENTLY -- sleeps of
    base_sleep * attempt (15s, 30s, 45s, 60s: long enough to outlast a
    typical rate-limit window), and (b) falls back LOUDLY to the last good
    universe cached on disk (rc_universe_cache_hours, default 48) so one
    dead endpoint costs you freshness, not the whole 40-minute run.
    Note: the universe is always built with min_vol_usd=0 (the dust filter
    belongs to review selection, not to universe membership -- live-YAML
    markets must always be resolvable)."""
    import pickle
    exchange = str(exchange).lower()
    cfg0 = {**cfg, "min_vol_usd": 0.0}
    cache_dir = Path(cfg.get("cache_dir", "_ladder_cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    pkl = cache_dir / f"universe_{exchange}.pkl"
    builder = _base.kraken_universe if exchange == "kraken" else _base.nonkyc_universe
    last_err: Optional[Exception] = None
    for a in range(int(retries) + 1):
        try:
            uni = builder(cfg0)
            try:
                with open(pkl, "wb") as f:
                    pickle.dump(dict(saved_at=time.time(), uni=uni), f)
            except Exception:
                pass
            return uni
        except Exception as e:
            last_err = e
            if a < retries:
                wait = base_sleep * (a + 1)
                _log(f"universe({exchange}) attempt {a+1}/{retries+1} failed "
                     f"({e}); retrying in {wait:.0f}s -- if this persists, the "
                     f"exchange may be rate-limiting or challenging your "
                     f"VPN exit IP (rotate the Gluetun server)")
                time.sleep(wait)
    max_age_h = float(cfg.get("rc_universe_cache_hours", 48.0))
    if pkl.exists():
        try:
            with open(pkl, "rb") as f:
                blob = pickle.load(f)
            age_h = (time.time() - float(blob.get("saved_at", 0))) / 3600.0
            if age_h <= max_age_h:
                _log("=" * 72)
                _log(f"WARNING: {exchange} universe endpoint is DOWN after "
                     f"{retries+1} patient attempts. Falling back to the "
                     f"cached universe from {age_h:.1f}h ago. Volumes / last "
                     f"prices / listings are {age_h:.1f}h STALE -- fine for "
                     f"screening; re-verify books (Cell 10) before deploying.")
                _log("=" * 72)
                return blob["uni"]
            _log(f"cached {exchange} universe is {age_h:.0f}h old "
                 f"(> {max_age_h:.0f}h limit) -- not using it")
        except Exception as e:
            _log(f"universe cache unreadable: {e}")
    raise last_err if last_err else RuntimeError(f"{exchange} universe failed")


def save_deploy_yamls(out_dir: Any, configs: List[Dict[str, Any]],
                      final_df: pd.DataFrame, cfg: Dict[str, Any],
                      deployed_pairs: Optional[Sequence[str]] = None,
                      run_id: str = "") -> List[str]:
    """Write one deployable YAML per qualifying market into out_dir, plus an
    INDEX.md explaining each file's tier and evidence. Returns paths."""
    tiers = yaml_deploy_selection(final_df, cfg, deployed_pairs)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_pair = {c["symbol"]: c for c in configs}
    written: List[str] = []
    index = ["# Generated deployable ladders", "",
             f"Engine ladder_lab_recycle_v11 {__version__} | {time.strftime('%Y-%m-%d %H:%M')}",
             "", "| file | pair | tier | validation | holdout edge | cap |",
             "|---|---|---|---|---|---|"]
    for pk, tier in sorted(tiers.items()):
        c = by_pair.get(pk)
        if c is None:
            index.append(f"| (not in this run) | {pk} | {tier} | — | — | — |")
            continue
        note = ("REPLACES a live config for this pair -- compare rungs before adopting"
                if "REFRESH" in tier else "")
        cid, text = render_deploy_yaml(c, cfg, tier=tier, run_id=run_id,
                                       extra_note=note)
        p = out_dir / f"{cid}.yml"
        p.write_text(text)
        written.append(str(p))
        ho = (c.get("holdout") or {}).get("edge_pct", "n/a")
        index.append(f"| {p.name} | {pk} | {tier} | {c.get('validation')} "
                     f"| {ho}% | {c.get('max_fund_value_quote')} |")
        _log(f"  wrote deployable YAML {p}")
    idx = out_dir / "INDEX.md"
    idx.write_text("\n".join(index) + "\n\nTiers: " + "; ".join(
        f"**{k}** = {v}" for k, v in _YAML_TIER_DOC.items()) + "\n")
    written.append(str(idx))
    return written


# ======================================================================
# v11.3: live-strategy health -- make "no longer profitable" impossible to miss
# ======================================================================
_HEALTH_ORDER = ["NOT PROFITABLE", "DORMANT", "BLEEDING VS HOLD",
                 "DEFENSIVE (beating hold, losing money)", "HEALTHY"]


def live_strategy_health(yaml_df: pd.DataFrame,
                         yaml_reports: Dict[str, Dict[str, Any]],
                         cfg: Dict[str, Any],
                         fills_by_pair: Optional[Dict[str, pd.DataFrame]] = None
                         ) -> pd.DataFrame:
    """Recent-form triage of every evaluated controller YAML: the last
    `rc_health_recent_blocks` COMPLETE 15d blocks, judged on two independent
    axes -- absolute money (pnl) and edge vs hold:

      HEALTHY          recent pnl > 0 and recent edge > 0
      DEFENSIVE        beating hold but LOSING MONEY (bear-market ladder:
                       working as designed, still costing you)
      BLEEDING VS HOLD making money but LESS than doing nothing
      NOT PROFITABLE   losing money AND losing to hold -> retire / re-anchor
      DORMANT          price hasn't meaningfully visited the band recently

    A 180-day headline can hide a strategy that died a month ago; this is
    the table that makes it obvious."""
    n_rec = int(cfg.get("rc_health_recent_blocks", 3))
    loss_floor = float(cfg.get("rc_health_loss_floor_pct", -1.0))
    rows = []
    for cid, rep in (yaml_reports or {}).items():
        blocks = rep.get("blocks")
        s = rep.get("summary", {})
        pk = rep.get("ladder", {}).get("trading_pair", "?")
        if blocks is None or blocks.empty:
            rows.append(dict(controller=cid, pair=pk, status="NO DATA"))
            continue
        full = blocks[~blocks.get("partial", False)]
        rec = full.tail(n_rec)
        if rec.empty:
            rows.append(dict(controller=cid, pair=pk, status="NO DATA"))
            continue
        pnl = (np.prod(1.0 + rec.pnl_pct.astype(float) / 100.0) - 1.0) * 100.0
        hold = (np.prod(1.0 + rec.hold_pct.astype(float) / 100.0) - 1.0) * 100.0
        edge = pnl - hold
        trades = int(rec.trades.sum())
        in_band = float(rec.in_band_pct.astype(float).mean())
        active = trades > 0 or in_band >= float(cfg.get("rc_gate_active_in_band", 0.05))
        if not active:
            status = "DORMANT"
        elif pnl <= loss_floor and edge <= 0:
            status = "NOT PROFITABLE"
        elif pnl <= loss_floor:
            status = "DEFENSIVE (beating hold, losing money)"
        elif edge <= 0:
            status = "BLEEDING VS HOLD"
        else:
            status = "HEALTHY"
        row = dict(controller=cid, pair=pk, status=status,
                   recent_blocks=len(rec),
                   recent_days=float(rec.days.sum()),
                   recent_pnl_pct=round(float(pnl), 2),
                   recent_hold_pct=round(float(hold), 2),
                   recent_edge_pct=round(float(edge), 2),
                   recent_trades=trades,
                   recent_two_sided_blocks=int(rec.two_sided.sum()),
                   last_block_pnl_pct=float(rec.pnl_pct.iloc[-1]),
                   full_pnl_pct=s.get("pnl_pct"),
                   full_edge_pct=s.get("edge_pct"))
        fills = (fills_by_pair or {}).get(pk)
        if fills is not None and not fills.empty:
            row["days_since_live_fill"] = round(
                (time.time() - float(fills.ts.max())) / 86400.0, 1)
        rows.append(row)
    df = pd.DataFrame(rows)
    if not df.empty and "status" in df:
        order = {s: i for i, s in enumerate(_HEALTH_ORDER)}
        df["_o"] = df.status.map(order).fillna(9)
        df = df.sort_values(["_o", "recent_pnl_pct"]).drop(columns="_o") \
               .reset_index(drop=True)
    return df


def print_health_banners(health: pd.DataFrame) -> None:
    """Loud, unmissable console verdicts for anything not HEALTHY."""
    if health is None or health.empty:
        return
    for _, r in health.iterrows():
        st = str(r.get("status", ""))
        if st == "HEALTHY":
            continue
        if st == "NOT PROFITABLE":
            mark, advice = "[!!] STOP", ("losing money AND losing to hold over its "
                                         "recent blocks -- retire it or re-anchor it")
        elif st == "DEFENSIVE (beating hold, losing money)":
            mark, advice = "[! ] CHECK", ("the ladder is beating hold but the market "
                                          "is dragging it down -- decide if you want "
                                          "this exposure at all")
        elif st == "BLEEDING VS HOLD":
            mark, advice = "[! ] CHECK", ("it is making money but LESS than doing "
                                          "nothing -- the churn is not paying for itself")
        elif st == "DORMANT":
            mark, advice = "[ ?] IDLE", ("price has left the band -- capital is parked; "
                                         "consider re-anchoring")
        else:
            continue
        print(f"{mark}  {r.get('controller')} ({r.get('pair')}): {st} -- "
              f"recent {r.get('recent_days', 0):.0f}d pnl "
              f"{r.get('recent_pnl_pct', float('nan')):+.2f}% vs hold "
              f"{r.get('recent_hold_pct', float('nan')):+.2f}% "
              f"({r.get('recent_trades', 0)} fills). {advice}.")


def save_v11_outputs(prefix: str, final_df: pd.DataFrame,
                     configs: List[Dict[str, Any]],
                     wf_rows: Optional[pd.DataFrame] = None,
                     yaml_df: Optional[pd.DataFrame] = None,
                     block_tables: Optional[Dict[str, pd.DataFrame]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> List[str]:
    """Same artifact set + filenames as v10's saver; the copy/paste markdown
    is rendered by v10's renderer UNCHANGED (format promise). The deploy
    JSON records v11 engine provenance. Adds one file: *_holdout_summary.csv."""
    prefix = str(prefix)
    Path(prefix).parent.mkdir(parents=True, exist_ok=True)
    written: List[str] = []

    def _csv(df, name):
        if df is None or (hasattr(df, "empty") and df.empty):
            return
        p = f"{prefix}_{name}.csv"
        df.to_csv(p, index=False)
        written.append(p)

    _csv(final_df, "final_summary")
    _csv(wf_rows, "walkforward_summary")
    _csv(yaml_df, "live_yaml_summary")
    if block_tables:
        frames = []
        for pk, bt in block_tables.items():
            if bt is None or bt.empty:
                continue
            bt = bt.copy()
            bt.insert(0, "market", pk)
            frames.append(bt)
        if frames:
            _csv(pd.concat(frames, ignore_index=True), "block_details")
    ho_rows = [dict(market=c["symbol"], validation=c["validation"],
                    **{f"holdout_{k}": v for k, v in (c.get("holdout") or {}).items()})
               for c in configs if c.get("holdout")]
    _csv(pd.DataFrame(ho_rows), "holdout_summary")
    p = f"{prefix}_deploy_config.json"
    with open(p, "w") as f:
        json.dump(dict(engine="ladder_lab_recycle_v11", version=__version__,
                       metadata=metadata or {}, configs=configs), f,
                  indent=2, default=str)
    written.append(p)
    p = f"{prefix}_copy_paste_ladders.md"
    with open(p, "w") as f:
        f.write(render_copy_paste_markdown(configs, yaml_df))
    written.append(p)
    for w in written:
        _log(f"  wrote {w}")
    return written
