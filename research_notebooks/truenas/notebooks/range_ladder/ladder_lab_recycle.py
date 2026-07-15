"""
ladder_lab_recycle.py -- v10 engine: recycling fill model + hold-relative scoring
==================================================================================

Companion module to `ladder_lab.py` (which it imports for exchange adapters,
candle cache, universe builders, screener, depth checks, and fund sizing
primitives). It REPLACES the simulation, scoring, and validation layers of
`ladder_lab_robust.py`, which are retired for the reasons documented in the
project review:

  1. The old `sim()` kernel had no proceeds recycling: order quantities were
     frozen at t=0, rungs re-armed only on a *daily close* crossing, and the
     stress model capped the ENTIRE ladder at one fill per day. It structurally
     could not see the many-small-trades behaviour of the live
     `range_inventory_ladder` controller (event refresh + 1h cooldowns).
  2. The old score subtracted absolute penalties (inventory-vs-50%, drawdown,
     stress degrade) that systematically exceeded any achievable 15-day return,
     so every market on every run scored negative and the `median score >= 0`
     gate failed everything -- including empirically profitable live ladders.
  3. The old walk-forward validated a per-fold re-optimisation process, never a
     deployable frozen ladder, and never the user's actual controller YAMLs.

What this module provides instead
---------------------------------
* `recycle_sim()` -- a numba-accelerated kernel that models the live controller:
  passive fixed-price rungs, order sizes drawn from the CURRENT ledger, event
  refresh of the opposite side after a fill, per-side cooldown re-placement,
  periodic global refresh, per-rung min-notional, intra-bar [o,l,h,c] paths.
  Designed for HOURLY bars (works on daily too; bar interval is inferred).
* `frozen_ladder_report()` -- run ONE fixed ladder continuously over a window
  and break the equity curve into 15-day blocks vs a same-seed HOLD portfolio.
  This is the primary "consistent 3-4 week profit, many small trades" evidence.
* Hold-relative scoring: `edge = strategy% - hold%` per window/block. No
  inventory-vs-50% penalty; conservative stress = body-only paths + extra slip
  (fair conservatism that does not punish trade frequency).
* Leakage-safe rolling walk-forward (60d train -> 15d unseen, step 15d) kept as
  a SECONDARY process check, gated on hold-relative consistency.
* First-class evaluation of your live `range_inventory_ladder*.yml` files:
  parsed (prices, weights, cooldowns, refresh, min order, seed intent) and run
  through the same frozen-ladder report.
* Safe exports: pdec-aware price formatting with hard validation (positive,
  unique, strictly monotonic) -- fixes the DOGS/ETH zero-price and BELLS/BTC
  duplicate-rung bugs from the 8-decimal rounding in v9.
* Diagnostic-JSONL replay helpers to calibrate the fill model against the real
  fills your controllers log.

The base module's `sim()` is still available (via `ladder_lab`) but is not used
for any decision in this pipeline.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import time
import concurrent.futures as _fut
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

import ladder_lab as _base
from ladder_lab import _log, _njit, HAVE_NUMBA, CandleCache, slice_days

__version__ = "10.2.0-recycle-rollspread-bandgates"

DEFAULT_ALWAYS_REVIEW_MARKETS = ("XMR/USDT", "XMR/USD", "SAL/USDT")

STABLE_SYMBOLS = {"USD", "USDT", "USDC", "DAI", "PYUSD", "USDG", "TUSD", "RLUSD",
                  "BUSD", "USDP", "FUSD", "ZSD", "EURT", "EURC", "USDE"}


# ======================================================================
# Config
# ======================================================================
def recycle_default_config(exchange: str) -> Dict[str, Any]:
    """Base config + v10 (rc_*) knobs. All the old cfg keys used by the base
    adapters/screener remain valid."""
    cfg = _base.default_config(exchange)
    cfg.update(dict(
        # ---------------- history ----------------
        years=0.6,                      # ~220d daily request budget for screening
        min_days=75,
        full_days=150,
        hourly_days=185,                # MEXC-backed hourly depth for the engine
        rc_min_hourly_days=45,          # fewer hourly days than this => fall back to daily bars
        rc_report_interval="5m",        # frozen reports / YAML eval / calibration granularity.
                                        # NonKYC native serves 180d of 5m in ONE call (verified);
                                        # MEXC paginates ~104 pages. "60m" reverts to hourly-only.
        rc_intraday_days=185,
        rc_min_intraday_days=45,
        # ---------------- engine ----------------
        rc_eval_days=180,               # continuous frozen-ladder evaluation window
        rc_block_days=15,               # consistency block length ("3-4 week" granularity ~ 2 blocks)
        rc_cooldown_seconds=3600,       # per-side re-placement cooldown (matches controller default)
        rc_refresh_seconds=43200,       # global refresh (matches executor_refresh_time)
        rc_event_refresh=True,
        rc_min_order_quote=1.0,
        rc_quote_frac=0.5,              # default seed mix; controller YAMLs override per-market
        # ---------------- conservative stress (fair: does NOT scale with churn) ----
        rc_stress_body_only=True,       # only open->close path; wick-only touches don't fill
        rc_stress_extra_slip=0.001,     # added to slip_floor; finalize uses measured spread/2 if larger
        # ---------------- candidate generation ----------------
        rc_seed=20260707,
        rc_n_candidates=240,
        rc_stage2_top_k=12,
        rc_n_buy_range=(4, 10),
        rc_n_sell_range=(4, 10),
        rc_inner_pct_range=(0.6, 4.0),
        rc_outer_pct_range=(4.0, 20.0),
        rc_max_outer_pct=24.0,
        rc_max_inner_pct=6.0,
        rc_min_outer_inner_ratio=2.0,
        rc_vol_inner_mult=(0.4, 1.4),
        rc_vol_outer_mult=(3.0, 9.0),
        rc_vol_floor_pct=0.35,
        rc_vol_cap_pct=28.0,
        rc_quantile_inner=(35.0, 65.0),
        rc_quantile_outer=(78.0, 97.0),
        rc_quantile_jitter=(0.85, 1.20),
        rc_spacing_curves=("linear", "geometric", "front_loaded", "back_loaded"),
        rc_weight_curves=("equal", "near", "mild_near", "slight_deep"),
        rc_max_single_rung_weight_pct=18.0,
        rc_hard_max_active_orders=24,
        # ---------------- scoring (hold-relative; small, few terms) -------------
        # score = edge - dd_w*maxdd + trade_bonus*min(trades/target,1)
        #         - stress_w*max(0, edge - stress_edge) - one_sided_penalty
        rc_target_trades_per_15d=40,    # HOURLY recycling sim fills far more than the old daily sim.
                                        # Calibrate this against your live diagnostic JSONL fills.
        rc_min_train_trades=20,
        rc_score_dd_w=0.35,
        rc_score_trade_bonus=2.0,
        rc_score_stress_w=0.50,
        rc_score_onesided_pen=6.0,
        # ---------------- PRIMARY gates: frozen-ladder 15d block consistency ----
        # v10.2: gates are BAND-AWARE. Blocks where price never visited the
        # ladder band are 'dormant' -- activity gates (trades, two-sided,
        # abs-profit) apply to ACTIVE blocks only; edge gates skip 'neutral'
        # blocks (|edge| < rc_gate_neutral_edge, i.e. ladder not engaged).
        rc_gate_min_blocks=6,
        rc_gate_min_active_blocks=4,      # band must actually get visited
        rc_gate_active_in_band=0.25,      # block is ACTIVE if >=25% of closes in band (or it traded)
        rc_gate_neutral_edge=0.25,        # |edge| below this = neutral block (excluded from edge rate)
        rc_gate_min_edge_pos_rate=0.65,   # of NON-NEUTRAL blocks beating hold
        rc_gate_min_abs_pos_rate=0.50,    # of ACTIVE blocks profitable outright
        rc_gate_worst_block_edge=-12.5,   # worst single block edge (%, vs hold; incl. inventory beta)
        rc_gate_min_trades_per_block=8,   # median fills per ACTIVE 15d block
        rc_gate_min_two_sided_rate=0.50,  # of ACTIVE blocks
        rc_gate_max_cycle_edge_pct=1.5,   # plausibility backstop (per round trip)
        rc_gate_max_cycle_edge_x=3.0,     #   ... or 3x the round-trip cost, whichever is larger
        # ---------------- microstructure realism (v10.2) ----------------
        rc_slip_from_roll=True,           # per-side slip = max(floor, Roll half-spread)
        rc_slip_cap=0.06,                 # 6%/side cap on auto slip
        rc_regularize_bars=True,          # snap candles to a fixed grid, flat-fill gaps
        # ---------------- SECONDARY gates: rolling WF of the fit process --------
        rc_train_days=60,
        rc_test_days=15,
        rc_step_days=15,
        rc_min_train_days=54,
        rc_min_test_days=10,
        rc_min_folds=4,
        rc_wf_min_edge_pos_rate=0.625,
        rc_wf_min_two_sided_rate=0.50,
        rc_wf_min_median_edge=0.0,
        rc_wf_worst_edge=-8.0,
        # ---------------- misc ----------------
        rc_drop_stable_stable=True,     # drop stable/stable pairs (USDC/USDT etc.)
        always_review_markets=DEFAULT_ALWAYS_REVIEW_MARKETS,
        focus_markets=(),
        rc_top_n_from_screen=40,        # markets from the screener that get the full engine
    ))
    return cfg


# ======================================================================
# Small shared helpers
# ======================================================================
def _pair_key(value: Any) -> str:
    s = str(value or "").strip().upper().replace("-", "/").replace("_", "/")
    parts = [p.strip() for p in s.split("/") if p.strip()]
    return "/".join(parts)


def merge_unique_markets(*lists: Optional[Sequence[Any]]) -> List[str]:
    out, seen = [], set()
    for lst in lists:
        for m in lst or []:
            k = _pair_key(m)
            if k and k not in seen:
                seen.add(k)
                out.append(k)
    return out


def resolve_present(uni: Dict[str, Any], requested: Sequence[Any]) -> Tuple[List[str], List[str]]:
    lookup = {_pair_key(pk): str(pk) for pk in uni["df"].pairkey}
    present, missing = [], []
    for k in merge_unique_markets(requested):
        (present if k in lookup else missing).append(lookup.get(k, k))
    return present, missing


def drop_stable_stable(df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """Remove stable/stable pairs (USDC/USDT, FUSD/USDC, ...) from a screen frame."""
    if not cfg.get("rc_drop_stable_stable", True) or df is None or df.empty:
        return df
    def _is_ss(pk: str) -> bool:
        try:
            b, q = str(pk).split("/", 1)
        except ValueError:
            return False
        return b.upper() in STABLE_SYMBOLS and q.upper() in STABLE_SYMBOLS
    col = "base" if "base" in df.columns else "pairkey"
    keep = ~df[col].map(_is_ss)
    dropped = int((~keep).sum())
    if dropped:
        _log(f"  dropped {dropped} stable/stable pairs from consideration")
    return df[keep].reset_index(drop=True)


def bar_seconds_of(bars: np.ndarray) -> float:
    bars = np.asarray(bars, float)
    if bars.shape[1] < 5 or len(bars) < 3:
        return 86400.0
    d = np.diff(bars[:, 0])
    d = d[d > 0]
    return float(np.median(d)) if len(d) else 86400.0


def ensure_ts(bars: np.ndarray, bar_seconds: float = 3600.0) -> np.ndarray:
    """Guarantee Nx5 [ts,o,h,l,c]; synthesize timestamps for Nx4 input."""
    bars = np.asarray(bars, float)
    if bars.shape[1] >= 5:
        return bars[:, :5]
    ts = np.arange(len(bars), dtype=float) * bar_seconds
    return np.column_stack([ts, bars[:, -4:]])


# ======================================================================
# Recycling fill kernel (models the live range_inventory_ladder controller)
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
def _recycle_kernel(o, h, l, c, buys, sells, bwn, swn,
                    fund, qf, fee, slip,
                    cooldown_bars, refresh_bars, min_order,
                    event_refresh, body_only):
    n = c.shape[0]
    nb = buys.shape[0]
    ns = sells.shape[0]
    p0 = o[0]
    quote = fund * qf
    base = fund * (1.0 - qf) / p0
    cm = fee + slip

    bq = np.zeros(nb)                 # open buy order qty (base units); 0 = no order
    sq = np.zeros(ns)                 # open sell order qty
    bf = np.zeros(nb, np.int64)
    sf = np.zeros(ns, np.int64)
    cb = np.zeros(n, np.int64)
    cs = np.zeros(n, np.int64)
    eq = np.zeros(n)
    fees = 0.0
    turnover = 0.0
    nbt = 0
    nst = 0
    last_bfill = -1000000000
    last_sfill = -1000000000
    b_dirty = False                   # side has filled (empty) rungs awaiting re-place
    s_dirty = False

    # initial placement, passive around the first open
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

        bfill_bar = False
        sfill_bar = False
        for s in range(plen - 1):
            a = path[s]
            b = path[s + 1]
            if b < a:
                for i in range(nb):
                    if bq[i] > 0.0 and b <= buys[i] and buys[i] <= a:
                        cost = buys[i] * bq[i]
                        debit = cost * (1.0 + cm)
                        if quote >= debit - 1e-12:
                            quote -= debit
                            base += bq[i]
                            fees += cost * cm
                            turnover += cost
                            bq[i] = 0.0
                            bf[i] += 1
                            nbt += 1
                            bfill_bar = True
            elif b > a:
                for i in range(ns):
                    if sq[i] > 0.0 and a <= sells[i] and sells[i] <= b:
                        if base >= sq[i] - 1e-12:
                            proceeds = sells[i] * sq[i]
                            quote += proceeds * (1.0 - cm)
                            base -= sq[i]
                            fees += proceeds * cm
                            turnover += proceeds
                            sq[i] = 0.0
                            sf[i] += 1
                            nst += 1
                            sfill_bar = True

        # ---- end-of-bar controller events (hourly bars => ~live latency) ----
        ref = c[t]
        if bfill_bar:
            last_bfill = t
            b_dirty = True
        if sfill_bar:
            last_sfill = t
            s_dirty = True

        if event_refresh:
            # A fill on one side immediately refreshes the OPPOSITE ladder,
            # deploying the new proceeds, and resets that side's cooldown.
            if bfill_bar:
                _k_place_sells(sq, sells, swn, base, ref, min_order)
                s_dirty = False
                last_sfill = t
            if sfill_bar:
                _k_place_buys(bq, buys, bwn, quote, ref, cm, min_order)
                b_dirty = False
                last_bfill = t

        # A side with holes re-places itself once its cooldown lapses without a fill.
        if b_dirty and (t - last_bfill) >= cooldown_bars:
            _k_place_buys(bq, buys, bwn, quote, ref, cm, min_order)
            b_dirty = False
        if s_dirty and (t - last_sfill) >= cooldown_bars:
            _k_place_sells(sq, sells, swn, base, ref, min_order)
            s_dirty = False

        # Global periodic refresh of both ladders.
        if refresh_bars > 0 and ((t + 1) % refresh_bars) == 0:
            _k_place_buys(bq, buys, bwn, quote, ref, cm, min_order)
            _k_place_sells(sq, sells, swn, base, ref, min_order)
            b_dirty = False
            s_dirty = False

        cb[t] = nbt
        cs[t] = nst
        eq[t] = quote + base * c[t]

    return quote, base, fees, turnover, bf, sf, cb, cs, eq


def recycle_sim(bars: np.ndarray,
                buys: Sequence[float], sells: Sequence[float],
                bw: Optional[Sequence[float]] = None,
                sw: Optional[Sequence[float]] = None,
                fund: float = 1000.0,
                quote_frac: float = 0.5,
                fee: float = 0.002,
                slip: float = 0.0,
                cooldown_seconds: float = 3600.0,
                refresh_seconds: float = 43200.0,
                min_order_quote: float = 1.0,
                event_refresh: bool = True,
                body_only: bool = False,
                bar_seconds: Optional[float] = None) -> Dict[str, Any]:
    """Recycling ladder sim. bars: Nx5 [ts,o,h,l,c] (Nx4 accepted, hourly assumed).

    Returns the same style dict as the legacy sim() plus:
      hold_eq (same-seed hold portfolio equity), edge_pct, turnover_x, bar_seconds.
    """
    bars = ensure_ts(bars, bar_seconds or 3600.0)
    bsec = float(bar_seconds or bar_seconds_of(bars))
    ohlc = bars[:, 1:5]
    o = np.ascontiguousarray(ohlc[:, 0])
    h = np.ascontiguousarray(ohlc[:, 1])
    l = np.ascontiguousarray(ohlc[:, 2])
    c = np.ascontiguousarray(ohlc[:, 3])
    buys = np.asarray(sorted(set(float(x) for x in buys), reverse=True), float)   # high -> low
    sells = np.asarray(sorted(set(float(x) for x in sells)), float)               # low -> high
    bw = np.ones(len(buys)) if bw is None else np.asarray(bw, float)[:len(buys)]
    sw = np.ones(len(sells)) if sw is None else np.asarray(sw, float)[:len(sells)]
    if len(bw) != len(buys) or len(sw) != len(sells):
        raise ValueError("weights length must match prices length after dedupe")
    bwn = bw / bw.sum()
    swn = sw / sw.sum()
    cooldown_bars = max(1, int(round(float(cooldown_seconds) / bsec)))
    refresh_bars = max(0, int(round(float(refresh_seconds) / bsec))) if refresh_seconds else 0

    quote, base, fees, turnover, bf, sf, cb, cs, eq = _recycle_kernel(
        o, h, l, c, buys, sells, bwn, swn,
        float(fund), float(quote_frac), float(fee), float(slip),
        np.int64(cooldown_bars), np.int64(refresh_bars), float(min_order_quote),
        bool(event_refresh), bool(body_only))

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
    lo_b = float(np.min(buys)) if len(buys) else float("nan")
    hi_s = float(np.max(sells)) if len(sells) else float("nan")
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
                if len(buys) and len(sells) else float("nan"),
                quote=quote, base=base)


def _recycle_reference(bars, buys, sells, bw=None, sw=None, fund=1000.0, quote_frac=0.5,
                       fee=0.002, slip=0.0, cooldown_seconds=3600.0, refresh_seconds=43200.0,
                       min_order_quote=1.0, event_refresh=True, body_only=False,
                       bar_seconds=None):
    """Pure-Python literal port of the kernel. Parity reference only."""
    bars = ensure_ts(bars, bar_seconds or 3600.0)
    bsec = float(bar_seconds or bar_seconds_of(bars))
    ohlc = bars[:, 1:5]
    buys = sorted(set(float(x) for x in buys), reverse=True)
    sells = sorted(set(float(x) for x in sells))
    bw = [1.0] * len(buys) if bw is None else list(bw)[:len(buys)]
    sw = [1.0] * len(sells) if sw is None else list(sw)[:len(sells)]
    bwn = [w / sum(bw) for w in bw]
    swn = [w / sum(sw) for w in sw]
    cooldown = max(1, int(round(cooldown_seconds / bsec)))
    refresh = max(0, int(round(refresh_seconds / bsec))) if refresh_seconds else 0
    p0 = ohlc[0][0]
    quote = fund * quote_frac
    base = fund * (1 - quote_frac) / p0
    cm = fee + slip
    bq = [0.0] * len(buys)
    sq = [0.0] * len(sells)

    def place_buys(ref):
        for i, p in enumerate(buys):
            bq[i] = 0.0
            if p < ref and p > 0:
                alloc = quote * bwn[i]
                if alloc >= min_order_quote:
                    bq[i] = alloc / (p * (1 + cm))

    def place_sells(ref):
        for i, p in enumerate(sells):
            sq[i] = 0.0
            if p > ref:
                qty = base * swn[i]
                if qty * p >= min_order_quote:
                    sq[i] = qty

    place_buys(p0)
    place_sells(p0)
    bf = [0] * len(buys)
    sf = [0] * len(sells)
    fees = 0.0
    nbt = nst = 0
    last_b = last_s = -10 ** 9
    b_dirty = s_dirty = False
    eq = []
    for t, (o, h, l, c) in enumerate(ohlc):
        path = [o, c] if body_only else ([o, l, h, c] if c >= o else [o, h, l, c])
        bfill = sfill = False
        for a, b in zip(path, path[1:]):
            if b < a:
                for i, L in enumerate(buys):
                    if bq[i] > 0 and b <= L <= a:
                        cost = L * bq[i]
                        debit = cost * (1 + cm)
                        if quote >= debit - 1e-12:
                            quote -= debit
                            base += bq[i]
                            fees += cost * cm
                            bq[i] = 0.0
                            bf[i] += 1
                            nbt += 1
                            bfill = True
            elif b > a:
                for i, L in enumerate(sells):
                    if sq[i] > 0 and a <= L <= b and base >= sq[i] - 1e-12:
                        proceeds = L * sq[i]
                        quote += proceeds * (1 - cm)
                        base -= sq[i]
                        fees += proceeds * cm
                        sq[i] = 0.0
                        sf[i] += 1
                        nst += 1
                        sfill = True
        ref = c
        if bfill:
            last_b = t
            b_dirty = True
        if sfill:
            last_s = t
            s_dirty = True
        if event_refresh:
            if bfill:
                place_sells(ref)
                s_dirty = False
                last_s = t
            if sfill:
                place_buys(ref)
                b_dirty = False
                last_b = t
        if b_dirty and (t - last_b) >= cooldown:
            place_buys(ref)
            b_dirty = False
        if s_dirty and (t - last_s) >= cooldown:
            place_sells(ref)
            s_dirty = False
        if refresh > 0 and (t + 1) % refresh == 0:
            place_buys(ref)
            place_sells(ref)
            b_dirty = s_dirty = False
        eq.append(quote + base * c)
    final = quote + base * ohlc[-1][3]
    return dict(pnl=final - fund, trades=nbt + nst, bf=bf, sf=sf, fees=fees, eq=eq)


def recycle_parity_check(verbose: bool = False, n_series: int = 4, n_bars: int = 800,
                         seed: int = 11) -> bool:
    """Fast kernel vs pure-Python reference on random walks + random ladders."""
    rng = np.random.default_rng(seed)
    ok = True
    for k in range(n_series):
        n = n_bars
        ret = rng.normal(0, 0.004, n)
        c = 100.0 * np.exp(np.cumsum(ret))
        o = np.concatenate([[100.0], c[:-1]])
        spread = np.abs(rng.normal(0, 0.003, n)) * c
        h = np.maximum(o, c) + spread
        l = np.minimum(o, c) - spread
        ts = np.arange(n) * 3600.0
        bars = np.column_stack([ts, o, h, l, c])
        anchor = float(np.median(c[: n // 4]))
        nb = int(rng.integers(3, 9))
        ns = int(rng.integers(3, 9))
        buys = [anchor * (1 - 0.004 * (i + 1) - 0.01 * i) for i in range(nb)]
        sells = [anchor * (1 + 0.004 * (i + 1) + 0.01 * i) for i in range(ns)]
        bw = rng.uniform(0.5, 2.0, nb)
        sw = rng.uniform(0.5, 2.0, ns)
        kw = dict(fund=1000.0, quote_frac=float(rng.uniform(0.2, 0.8)), fee=0.002,
                  slip=0.0005, cooldown_seconds=3600.0, refresh_seconds=43200.0,
                  min_order_quote=1.0, event_refresh=bool(k % 2 == 0),
                  body_only=bool(k == 3))
        a = recycle_sim(bars, buys, sells, bw, sw, **kw)
        b = _recycle_reference(bars, buys, sells, bw, sw, **kw)
        good = (abs(a["pnl"] - b["pnl"]) < 1e-6 and a["trades"] == b["trades"]
                and abs(a["fees"] - b["fees"]) < 1e-6)
        ok = ok and good
        if verbose:
            _log(f"  recycle parity {k}: pnl {a['pnl']:.6f} vs {b['pnl']:.6f} | "
                 f"trades {a['trades']} vs {b['trades']} | {'OK' if good else 'MISMATCH'}")
    return ok


# ======================================================================
# Price formatting + ladder validation (fixes the v9 export bugs)
# ======================================================================
def price_str(x: float, pdec: Optional[int] = None) -> str:
    """Exchange-safe price text. Uses pdec when sane, else 10 significant figures.
    Never collapses tiny prices to 0 silently -- validate_ladder() catches that."""
    x = float(x)
    if pdec is not None and pdec == pdec:
        try:
            pdec = int(pdec)
            s = f"{x:.{pdec}f}"
            if float(s) > 0 or x == 0:
                return s
        except Exception:
            pass
    return f"{x:.10g}"


def format_ladder_prices(prices: Sequence[float], pdec: Optional[int] = None) -> List[str]:
    return [price_str(p, pdec) for p in prices]


def validate_ladder(buys: Sequence[float], sells: Sequence[float],
                    pdec: Optional[int] = None) -> List[str]:
    """Return a list of problems ([] = valid). Run on the FORMATTED values so
    what ships in the YAML is what was validated."""
    problems: List[str] = []
    b = [float(price_str(p, pdec)) for p in buys]
    s = [float(price_str(p, pdec)) for p in sells]
    if not b or not s:
        problems.append("empty ladder side")
        return problems
    if any(p <= 0 for p in b) or any(p <= 0 for p in s):
        problems.append(f"price precision collapse to <=0 (pdec={pdec})")
    if len(set(b)) != len(b):
        problems.append(f"duplicate buy rungs after formatting (pdec={pdec})")
    if len(set(s)) != len(s):
        problems.append(f"duplicate sell rungs after formatting (pdec={pdec})")
    if sorted(b, reverse=True) != b:
        problems.append("buy_prices not highest->lowest")
    if sorted(s) != s:
        problems.append("sell_prices not lowest->highest")
    if b and s and max(b) >= min(s):
        problems.append("highest buy >= lowest sell")
    return problems


# ======================================================================
# Frozen-ladder block report -- THE primary validation
# ======================================================================
def block_table(res: Dict[str, Any], block_days: float = 15.0,
                band: Optional[Tuple[float, float]] = None) -> pd.DataFrame:
    """Slice one continuous sim into consecutive `block_days` blocks and report
    strategy vs hold per block (mark-to-market). `band=(lowest_buy, highest_sell)`
    adds in_band_pct + active flags so gates can ignore dormant periods."""
    ts = np.asarray(res["ts"], float)
    eq = np.asarray(res["eq"], float)
    hold = np.asarray(res["hold_eq"], float)
    cb = np.asarray(res["cb"], float)
    cs = np.asarray(res["cs"], float)
    if len(ts) < 3:
        return pd.DataFrame()
    idx = np.floor((ts - ts[0]) / (block_days * 86400.0)).astype(int)
    rows = []
    prev_eq, prev_hold, prev_cb, prev_cs = eq[0], hold[0], 0.0, 0.0
    for b in range(int(idx.max()) + 1):
        mask = idx == b
        if not mask.any():
            continue
        i1 = np.where(mask)[0][-1]
        span_days = (ts[i1] - (ts[np.where(mask)[0][0]])) / 86400.0 + \
                    (bar_seconds_of(np.column_stack([ts, ts, ts, ts, ts])) / 86400.0)
        if span_days < 1.0:      # degenerate tail sliver (e.g. a single bar)
            prev_eq, prev_hold, prev_cb, prev_cs = eq[i1], hold[i1], cb[i1], cs[i1]
            continue
        ret = (eq[i1] - prev_eq) / prev_eq * 100 if prev_eq > 0 else float("nan")
        hret = (hold[i1] - prev_hold) / prev_hold * 100 if prev_hold > 0 else float("nan")
        bfl = cb[i1] - prev_cb
        sfl = cs[i1] - prev_cs
        closes = np.asarray(res["close"], float)[mask]
        in_band = (float(np.mean((closes >= band[0]) & (closes <= band[1])))
                   if band is not None else float("nan"))
        rows.append(dict(
            block=b + 1,
            start=pd.to_datetime(ts[np.where(mask)[0][0]], unit="s").date().isoformat(),
            end=pd.to_datetime(ts[i1], unit="s").date().isoformat(),
            days=round(span_days, 1),
            pnl_pct=round(ret, 3),
            hold_pct=round(hret, 3),
            edge_pct=round(ret - hret, 3),
            buy_fills=int(bfl),
            sell_fills=int(sfl),
            trades=int(bfl + sfl),
            two_sided=bool(bfl > 0 and sfl > 0),
            in_band_pct=round(in_band, 3) if in_band == in_band else float("nan"),
            partial=bool(span_days < 0.6 * block_days),
        ))
        prev_eq, prev_hold, prev_cb, prev_cs = eq[i1], hold[i1], cb[i1], cs[i1]
    return pd.DataFrame(rows)


def block_gates(blocks: pd.DataFrame, cfg: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Band-aware primary consistency gates.

    dormant block  = price never meaningfully visited the band and nothing traded
    active block   = in_band_pct >= rc_gate_active_in_band OR it traded
    neutral block  = |edge| < rc_gate_neutral_edge (ladder not engaged vs hold)

    Activity gates (trades / two-sided / absolute profit) judge ACTIVE blocks;
    edge_pos_rate judges non-neutral blocks; worst_block_edge judges everything
    (dormant inventory beta is real risk you hold)."""
    if blocks is None or blocks.empty:
        return False, ["no blocks"], {}
    full = blocks[~blocks["partial"]] if "partial" in blocks.columns else blocks
    if full.empty:
        full = blocks
    n = len(full)
    ib = full["in_band_pct"] if "in_band_pct" in full.columns else pd.Series([float("nan")] * n)
    active_mask = (ib.fillna(1.0) >= float(cfg["rc_gate_active_in_band"])) | (full.trades > 0)
    act = full[active_mask]
    n_active = len(act)
    neutral_thr = float(cfg["rc_gate_neutral_edge"])
    engaged = full[full.edge_pct.abs() >= neutral_thr]
    edge_pos = float(np.mean(engaged.edge_pct > 0)) if len(engaged) else 0.0
    abs_pos = float(np.mean(act.pnl_pct > 0)) if n_active else 0.0
    worst_edge = float(full.edge_pct.min())
    med_trades = float(act.trades.median()) if n_active else 0.0
    two_rate = float(np.mean(act.two_sided)) if n_active else 0.0
    summary = dict(n_blocks=n, n_active_blocks=n_active,
                   n_engaged_blocks=int(len(engaged)),
                   edge_pos_rate=round(edge_pos, 3),
                   abs_pos_rate=round(abs_pos, 3), worst_block_edge=round(worst_edge, 3),
                   median_trades_per_block=med_trades,
                   two_sided_rate=round(two_rate, 3),
                   total_edge_pct=round(float(full.edge_pct.sum()), 3),
                   total_pnl_pct=round(float(full.pnl_pct.sum()), 3))
    fails: List[str] = []
    if n < int(cfg["rc_gate_min_blocks"]):
        fails.append(f"only {n} full blocks (< {cfg['rc_gate_min_blocks']})")
    if n_active < int(cfg["rc_gate_min_active_blocks"]):
        fails.append(f"only {n_active} ACTIVE blocks (< {cfg['rc_gate_min_active_blocks']}) "
                     f"-- band rarely visited")
    if edge_pos < float(cfg["rc_gate_min_edge_pos_rate"]):
        fails.append(f"edge_pos_rate {edge_pos:.2f} < {cfg['rc_gate_min_edge_pos_rate']} "
                     f"(over {len(engaged)} engaged blocks)")
    if abs_pos < float(cfg["rc_gate_min_abs_pos_rate"]):
        fails.append(f"abs_pos_rate {abs_pos:.2f} < {cfg['rc_gate_min_abs_pos_rate']} (active blocks)")
    if worst_edge < float(cfg["rc_gate_worst_block_edge"]):
        fails.append(f"worst block edge {worst_edge:+.2f}% < {cfg['rc_gate_worst_block_edge']}%")
    if med_trades < float(cfg["rc_gate_min_trades_per_block"]):
        fails.append(f"median {med_trades:.0f} trades/ACTIVE block < {cfg['rc_gate_min_trades_per_block']}")
    if two_rate < float(cfg["rc_gate_min_two_sided_rate"]):
        fails.append(f"two_sided_rate {two_rate:.2f} < {cfg['rc_gate_min_two_sided_rate']} (active blocks)")
    return (not fails), fails, summary


def _sim_kwargs(cfg: Dict[str, Any], ladder: Dict[str, Any]) -> Dict[str, Any]:
    """Merge engine defaults with per-ladder overrides (controller YAML values win)."""
    return dict(
        fund=float(ladder.get("fund", cfg["fund_usd"])),
        quote_frac=float(ladder.get("quote_frac", cfg.get("rc_quote_frac", 0.5))),
        fee=float(ladder.get("fee", cfg["fee"])),
        cooldown_seconds=float(ladder.get("cooldown_seconds", cfg["rc_cooldown_seconds"])),
        refresh_seconds=float(ladder.get("refresh_seconds", cfg["rc_refresh_seconds"])),
        min_order_quote=float(ladder.get("min_order_quote", cfg["rc_min_order_quote"])),
        event_refresh=bool(ladder.get("event_refresh", cfg["rc_event_refresh"])),
    )


def run_ladder(bars: np.ndarray, ladder: Dict[str, Any], cfg: Dict[str, Any],
               stress: bool = False, slip: Optional[float] = None) -> Dict[str, Any]:
    """One sim of a ladder dict {buy_prices, sell_prices, bw, sw, ...overrides}.
    slip=None -> market-realistic per-side slip from the bars themselves
    (max of slip_floor and the Roll half-spread estimate), so thin-book
    bid/ask-bounce candles cannot be harvested as free oscillation."""
    kw = _sim_kwargs(cfg, ladder)
    base_slip = float(slip) if slip is not None else effective_slip(bars, cfg)
    if stress:
        kw["slip"] = base_slip + float(cfg["rc_stress_extra_slip"])
        kw["body_only"] = bool(cfg.get("rc_stress_body_only", True))
    else:
        kw["slip"] = base_slip
        kw["body_only"] = False
    return recycle_sim(bars, ladder["buy_prices"], ladder["sell_prices"],
                       ladder.get("bw"), ladder.get("sw"), **kw)


def frozen_ladder_report(bars: np.ndarray, ladder: Dict[str, Any], cfg: Dict[str, Any],
                         label: str = "", slip: Optional[float] = None) -> Dict[str, Any]:
    """Run ONE fixed ladder continuously; return sim + stress + 15d blocks + gates.
    v10.2: Roll-spread slip (computed on the RAW candles), then bars are snapped
    to a regular grid (NonKYC native candles omit trade-less periods), blocks are
    band-aware, and a per-round-trip plausibility gate backstops bad data."""
    bars = ensure_ts(bars)
    slip_used = float(slip) if slip is not None else effective_slip(bars, cfg)
    gap_fill = 0.0
    if cfg.get("rc_regularize_bars", True):
        bars, gap_fill = regularize_bars(bars)
    res = run_ladder(bars, ladder, cfg, stress=False, slip=slip_used)
    stress = run_ladder(bars, ladder, cfg, stress=True, slip=slip_used)
    band = (float(min(ladder["buy_prices"])), float(max(ladder["sell_prices"])))
    blocks = block_table(res, float(cfg["rc_block_days"]), band=band)
    passed, fails, summary = block_gates(blocks, cfg)
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
    ))
    rt_cost_pct = 2.0 * (float(_sim_kwargs(cfg, ladder)["fee"]) + slip_used) * 100.0
    sanity = _cycle_edge_gate(summary, cfg, rt_cost_pct)
    if sanity:
        fails = list(fails) + [sanity]
        passed = False
        summary["data_suspect"] = True
    return dict(result=res, stress=stress, blocks=blocks, summary=summary,
                passed=passed, failed_gates=fails, ladder=ladder)


# ======================================================================
# Scoring (hold-relative, few terms) + candidate generation + search
# ======================================================================
def score_v10(res: Dict[str, Any], stress_res: Optional[Dict[str, Any]],
              cfg: Dict[str, Any], days: float) -> float:
    trades = int(res.get("trades", 0))
    if trades <= 0:
        return -100.0
    edge = float(res["pnl_pct"] - res["hold_pct"])
    dd = float(res.get("maxdd", 0.0))
    target = float(cfg["rc_target_trades_per_15d"]) * max(days, 1.0) / 15.0
    trade_factor = min(trades / max(target, 1.0), 1.0)
    one_sided = (sum(res["bf"]) <= 0) or (sum(res["sf"]) <= 0)
    stress_gap = 0.0
    if stress_res is not None:
        s_edge = float(stress_res["pnl_pct"] - stress_res["hold_pct"])
        stress_gap = max(0.0, edge - s_edge)
    score = (edge
             - float(cfg["rc_score_dd_w"]) * dd
             + float(cfg["rc_score_trade_bonus"]) * trade_factor
             - float(cfg["rc_score_stress_w"]) * stress_gap
             - (float(cfg["rc_score_onesided_pen"]) if one_sided else 0.0))
    if trades < int(cfg["rc_min_train_trades"]):
        score -= 3.0
    return float(score)


def _stable_int(*parts: Any) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def _rng_for(cfg: Dict[str, Any], label: str, fold_idx: int = 0, salt: str = "") -> np.random.Generator:
    return np.random.default_rng((int(cfg.get("rc_seed", 0)) + _stable_int(label, salt))
                                 % (2 ** 32 - 1))
    # NOTE: fold_idx intentionally NOT in the seed -- the same market draws the
    # same candidate pool in every fold so fold-to-fold ladder differences
    # reflect the DATA, not the RNG. (v9 salted by fold, guaranteeing churn.)


def _distance_grid(inner: float, outer: float, n: int, curve: str) -> np.ndarray:
    inner = max(float(inner), 1e-9)
    outer = max(float(outer), inner + 1e-9)
    if n <= 0:
        return np.array([])
    if n == 1:
        return np.array([inner])
    x = np.linspace(0.0, 1.0, n)
    if curve == "geometric":
        return inner * (outer / inner) ** x
    if curve == "front_loaded":
        return inner + (outer - inner) * (x ** 1.65)
    if curve == "back_loaded":
        return inner + (outer - inner) * (1.0 - (1.0 - x) ** 1.65)
    return inner + (outer - inner) * x


def _cap_weight_share(w: Sequence[float], max_single_pct: float, passes: int = 20) -> np.ndarray:
    arr = np.maximum(np.asarray(w, float), 1e-12)
    max_share = max(float(max_single_pct) / 100.0, 1.0 / len(arr))
    for _ in range(passes):
        shares = arr / arr.sum()
        if shares.max() <= max_share + 1e-12:
            break
        cap = max_share * arr.sum()
        over = arr > cap
        excess = float(np.sum(arr[over] - cap))
        arr[over] = cap
        if excess <= 0 or (~over).sum() == 0:
            break
        arr[~over] += excess / (~over).sum()
    return arr


def _weights_for_curve(n: int, curve: str, max_single_pct: float) -> np.ndarray:
    if curve == "near":
        w = np.exp(-1.35 * np.linspace(0, 1, n))
    elif curve == "mild_near":
        w = np.exp(-0.65 * np.linspace(0, 1, n))
    elif curve == "slight_deep":
        w = np.exp(0.45 * np.linspace(0, 1, n))
    else:
        w = np.ones(n)
    return _cap_weight_share(w, max_single_pct)


def _daily_view(bars: np.ndarray) -> np.ndarray:
    """Resample intraday Nx5 to daily Nx5 for vol/quantile statistics."""
    bars = ensure_ts(bars)
    day = np.floor(bars[:, 0] / 86400.0).astype(int)
    rows = []
    for d in np.unique(day):
        g = bars[day == d]
        rows.append([g[0, 0], g[0, 1], g[:, 2].max(), g[:, 3].min(), g[-1, 4]])
    return np.asarray(rows, float)


def _train_vol_pct_daily(bars: np.ndarray) -> float:
    db = _daily_view(bars)
    if len(db) < 5:
        return 1.0
    o, h, l, c = db[:, 1], db[:, 2], db[:, 3], db[:, 4]
    prev = np.roll(c, 1); prev[0] = o[0]
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev), np.abs(l - prev)))
    trp = tr / np.where(prev > 0, prev, 1.0) * 100.0
    v = float(np.nanmedian(trp))
    return v if np.isfinite(v) and v > 0 else 1.0


def _anchor_price(bars: np.ndarray) -> float:
    c = ensure_ts(bars)[:, 4]
    return float(np.median(c[-min(len(c), 72):]))   # median of last ~3 days of hourly closes


def _sanitize_distances(bi, bo, si, so, cfg) -> Tuple[float, float, float, float]:
    min_cycle = max(1.0, 2.5 * _base._rt_fee_pct(cfg))
    inner_floor = max(float(cfg["rc_inner_pct_range"][0]), min_cycle / 2.0)
    outer_cap = float(cfg["rc_max_outer_pct"])
    ratio = float(cfg["rc_min_outer_inner_ratio"])
    cap_in = float(cfg["rc_max_inner_pct"])
    bi = min(max(float(bi), inner_floor), cap_in)
    si = min(max(float(si), inner_floor), cap_in)
    if bi + si < min_cycle:
        extra = (min_cycle - bi - si) / 2.0
        bi += extra; si += extra
    bo = min(max(float(bo), bi * ratio, float(cfg["rc_outer_pct_range"][0])), outer_cap)
    so = min(max(float(so), si * ratio, float(cfg["rc_outer_pct_range"][0])), outer_cap)
    if bo <= bi:
        bo = min(outer_cap, bi * ratio + 0.25)
    if so <= si:
        so = min(outer_cap, si * ratio + 0.25)
    return bi, bo, si, so


def _make_candidate(anchor, nb, ns, bi, bo, si, so, spacing, weight_curve, family,
                    cfg, pdec=None, serial=0) -> Optional[Dict[str, Any]]:
    if anchor <= 0 or nb <= 0 or ns <= 0:
        return None
    if nb + ns > int(cfg["rc_hard_max_active_orders"]):
        return None
    bi, bo, si, so = _sanitize_distances(bi, bo, si, so, cfg)
    bd = _distance_grid(bi, bo, nb, spacing)
    sd = _distance_grid(si, so, ns, spacing)
    buys = [float(_base.round_price(anchor * (1 - d / 100.0), pdec)) for d in bd]
    sells = [float(_base.round_price(anchor * (1 + d / 100.0), pdec)) for d in sd]
    n_raw = len(buys) + len(sells)
    buys = list(dict.fromkeys([p for p in buys if 0 < p < anchor]))
    sells = list(dict.fromkeys([p for p in sells if p > anchor]))
    if len(buys) < 2 or len(sells) < 2:
        return None
    if (len(buys) + len(sells)) < 0.7 * n_raw:       # pdec collapsed the grid
        return None
    bw = _weights_for_curve(len(buys), weight_curve, cfg["rc_max_single_rung_weight_pct"])
    sw = _weights_for_curve(len(sells), weight_curve, cfg["rc_max_single_rung_weight_pct"])
    return dict(candidate_id=f"{family}-{serial:04d}-{len(buys)}x{len(sells)}-{spacing}-{weight_curve}",
                family=family, spacing_curve=spacing, weight_curve=weight_curve,
                n_buy=len(buys), n_sell=len(sells), anchor=float(anchor),
                buy_inner_pct=float(bd[0]), buy_outer_pct=float(bd[-1]),
                sell_inner_pct=float(sd[0]), sell_outer_pct=float(sd[-1]),
                buy_prices=buys, sell_prices=sells,
                bw=np.asarray(bw, float), sw=np.asarray(sw, float))


def generate_candidates(train_bars: np.ndarray, cfg: Dict[str, Any],
                        pdec: Optional[int] = None, label: str = "") -> List[Dict[str, Any]]:
    n_target = int(cfg["rc_n_candidates"])
    rng = _rng_for(cfg, label, salt="candidates")
    anchor = _anchor_price(train_bars)
    vol = _train_vol_pct_daily(train_bars)
    db = _daily_view(train_bars)
    highs, lows = db[:, 2], db[:, 3]
    down = np.maximum(0.0, (anchor - lows) / anchor * 100.0)
    up = np.maximum(0.0, (highs - anchor) / anchor * 100.0)
    down = down[down > 0]; up = up[up > 0]
    out, seen = [], set()
    serial = 0
    nb_lo, nb_hi = map(int, cfg["rc_n_buy_range"])
    ns_lo, ns_hi = map(int, cfg["rc_n_sell_range"])
    while len(out) < n_target and serial < n_target * 5:
        serial += 1
        family = str(rng.choice(("pct", "volatility", "quantile")))
        spacing = str(rng.choice(cfg["rc_spacing_curves"]))
        wcurve = str(rng.choice(cfg["rc_weight_curves"]))
        nb = int(rng.integers(nb_lo, nb_hi + 1))
        ns = int(rng.integers(ns_lo, ns_hi + 1))
        if family == "volatility":
            im = cfg["rc_vol_inner_mult"]; om = cfg["rc_vol_outer_mult"]
            bi = np.clip(vol * rng.uniform(*im), cfg["rc_vol_floor_pct"], cfg["rc_vol_cap_pct"])
            si = np.clip(vol * rng.uniform(*im), cfg["rc_vol_floor_pct"], cfg["rc_vol_cap_pct"])
            bo = np.clip(vol * rng.uniform(*om), cfg["rc_vol_floor_pct"] * 2, cfg["rc_vol_cap_pct"])
            so = np.clip(vol * rng.uniform(*om), cfg["rc_vol_floor_pct"] * 2, cfg["rc_vol_cap_pct"])
        elif family == "quantile" and len(down) >= 5 and len(up) >= 5:
            qi = rng.uniform(*cfg["rc_quantile_inner"])
            qo = rng.uniform(max(qi + 5.0, cfg["rc_quantile_outer"][0]), cfg["rc_quantile_outer"][1])
            j = cfg["rc_quantile_jitter"]
            bi = np.percentile(down, qi) * rng.uniform(*j)
            bo = np.percentile(down, qo) * rng.uniform(*j)
            si = np.percentile(up, qi) * rng.uniform(*j)
            so = np.percentile(up, qo) * rng.uniform(*j)
        else:
            il, ih = cfg["rc_inner_pct_range"]; ol, oh = cfg["rc_outer_pct_range"]
            bi = rng.uniform(il, ih); si = rng.uniform(il, ih)
            bo = rng.uniform(max(ol, bi * cfg["rc_min_outer_inner_ratio"]), oh)
            so = rng.uniform(max(ol, si * cfg["rc_min_outer_inner_ratio"]), oh)
        cand = _make_candidate(anchor, nb, ns, bi, bo, si, so, spacing, wcurve,
                               family, cfg, pdec, serial)
        if cand is None:
            continue
        key = (tuple(cand["buy_prices"]), tuple(cand["sell_prices"]), cand["weight_curve"])
        if key in seen:
            continue
        seen.add(key)
        out.append(cand)
    return out


def search_ladder(train_bars: np.ndarray, cfg: Dict[str, Any],
                  pdec: Optional[int] = None, label: str = "",
                  return_table: bool = False) -> Dict[str, Any]:
    """Fit on TRAIN only. Stage 1: score all candidates with their own weights.
    Stage 2: re-evaluate the top K under every weight curve, keep the best.
    (No free per-rung weight optimizer -- that was a proven overfit vector.)"""
    train_bars = ensure_ts(train_bars)
    slip_used = effective_slip(train_bars, cfg)
    if cfg.get("rc_regularize_bars", True):
        train_bars, _ = regularize_bars(train_bars)
    days = max((train_bars[-1, 0] - train_bars[0, 0]) / 86400.0, 1.0)
    cands = generate_candidates(train_bars, cfg, pdec, label)
    if not cands:
        raise RuntimeError(f"{label}: no candidates survived construction")
    rows = []
    scored = []
    for cand in cands:
        r = run_ladder(train_bars, cand, cfg, stress=False, slip=slip_used)
        s = run_ladder(train_bars, cand, cfg, stress=True, slip=slip_used)
        sc = score_v10(r, s, cfg, days)
        scored.append((sc, cand, r, s))
        if return_table:
            rows.append(dict(candidate_id=cand["candidate_id"], stage="stage1",
                             score=round(sc, 3), edge_pct=round(r["edge_pct"], 3),
                             pnl_pct=round(r["pnl_pct"], 3), hold_pct=round(r["hold_pct"], 3),
                             trades=r["trades"], maxdd=round(r["maxdd"], 3),
                             stress_edge=round(s["edge_pct"], 3),
                             n_buy=cand["n_buy"], n_sell=cand["n_sell"],
                             family=cand["family"], spacing=cand["spacing_curve"],
                             weights=cand["weight_curve"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    best = None
    for sc, cand, r, s in scored[:int(cfg["rc_stage2_top_k"])]:
        for wcurve in cfg["rc_weight_curves"]:
            c2 = copy.deepcopy(cand)
            c2["bw"] = _weights_for_curve(c2["n_buy"], wcurve, cfg["rc_max_single_rung_weight_pct"])
            c2["sw"] = _weights_for_curve(c2["n_sell"], wcurve, cfg["rc_max_single_rung_weight_pct"])
            c2["weight_curve"] = wcurve
            r2 = run_ladder(train_bars, c2, cfg, stress=False, slip=slip_used)
            s2 = run_ladder(train_bars, c2, cfg, stress=True, slip=slip_used)
            sc2 = score_v10(r2, s2, cfg, days)
            if return_table:
                rows.append(dict(candidate_id=c2["candidate_id"], stage="stage2",
                                 score=round(sc2, 3), edge_pct=round(r2["edge_pct"], 3),
                                 pnl_pct=round(r2["pnl_pct"], 3), hold_pct=round(r2["hold_pct"], 3),
                                 trades=r2["trades"], maxdd=round(r2["maxdd"], 3),
                                 stress_edge=round(s2["edge_pct"], 3),
                                 n_buy=c2["n_buy"], n_sell=c2["n_sell"],
                                 family=c2["family"], spacing=c2["spacing_curve"],
                                 weights=wcurve))
            if best is None or sc2 > best[0]:
                best = (sc2, c2, r2, s2)
    sc, cand, r, s = best
    return dict(best=cand, train_result=r, train_stress=s, train_score=float(sc),
                n_candidates=len(cands), train_days=int(round(days)),
                slip_used=float(slip_used),
                leaderboard=(pd.DataFrame(rows).sort_values("score", ascending=False)
                             .reset_index(drop=True)) if return_table else None)


# ======================================================================
# Rolling walk-forward (secondary, leakage-safe process check)
# ======================================================================
def make_rolling_windows(bars: np.ndarray, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    bars = ensure_ts(bars)
    if len(bars) == 0:
        return []
    ts = bars[:, 0]
    t0, t1 = ts[0], ts[-1]
    train_s = cfg["rc_train_days"] * 86400.0
    test_s = cfg["rc_test_days"] * 86400.0
    step_s = cfg["rc_step_days"] * 86400.0
    out = []
    fold = 0
    start = t0
    while start + train_s + test_s <= t1 + 1:
        tr_mask = (ts >= start) & (ts < start + train_s)
        te_mask = (ts >= start + train_s) & (ts < start + train_s + test_s)
        tr, te = bars[tr_mask], bars[te_mask]
        tr_days = (tr[-1, 0] - tr[0, 0]) / 86400.0 if len(tr) > 1 else 0
        te_days = (te[-1, 0] - te[0, 0]) / 86400.0 if len(te) > 1 else 0
        if tr_days >= cfg["rc_min_train_days"] and te_days >= cfg["rc_min_test_days"]:
            out.append(dict(fold_idx=fold, train=tr, test=te,
                            train_days=tr_days, test_days=te_days,
                            train_start=tr[0, 0], train_end=tr[-1, 0],
                            test_start=te[0, 0], test_end=te[-1, 0]))
            fold += 1
        start += step_s
    return out


def rolling_walkforward(bars: np.ndarray, cfg: Dict[str, Any],
                        pdec: Optional[int] = None, label: str = "") -> Dict[str, Any]:
    windows = make_rolling_windows(bars, cfg)
    recs = []
    for w in windows:
        fit = search_ladder(w["train"], cfg, pdec, label=f"{label}")
        cand = fit["best"]
        te_slip = max(fit.get("slip_used", 0.0), effective_slip(w["test"], cfg))
        te = regularize_bars(w["test"])[0] if cfg.get("rc_regularize_bars", True) else w["test"]
        r = run_ladder(te, cand, cfg, stress=False, slip=te_slip)
        s = run_ladder(te, cand, cfg, stress=True, slip=te_slip)
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
            trades=r["trades"], buy_fills=int(sum(r["bf"])), sell_fills=int(sum(r["sf"])),
            two_sided=bool(sum(r["bf"]) > 0 and sum(r["sf"]) > 0),
            maxdd=round(r["maxdd"], 3), endinv=round(r["endinv"], 1)))
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
# Controller YAML files as first-class candidates
# ======================================================================
_NUM_LIST_KEYS = ("buy_prices", "buy_amounts_pct", "sell_prices", "sell_amounts_pct")
_SCALAR_KEYS = ("id", "controller_name", "connector_name", "trading_pair",
                "fee_rate", "total_amount_quote", "max_fund_value_quote",
                "claimed_base_value_quote", "claimed_base_amount",
                "event_refresh_enabled", "executor_refresh_time", "cooldown_time",
                "buy_cooldown_time", "sell_cooldown_time", "min_order_quote",
                "state_file_name")


def _strip_comment(v: str) -> str:
    # values in these YAMLs never contain '#'; comments start with optional spaces + '#'
    i = v.find("#")
    return (v[:i] if i >= 0 else v).strip().strip("'\"")


def parse_controller_yaml(path: Any) -> Optional[Dict[str, Any]]:
    """Tolerant top-level key parser for range_inventory_ladder YAMLs
    (comma-scalar ladders, heavy comments). Returns None if unreadable."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    out: Dict[str, Any] = dict(path=str(path))
    for line in text.splitlines():
        if not line or line.lstrip() != line:      # top-level keys only
            continue
        if line.lstrip().startswith("#") or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        if key not in _SCALAR_KEYS and key not in _NUM_LIST_KEYS:
            continue
        val = _strip_comment(val)
        if not val:
            continue
        if key in _NUM_LIST_KEYS:
            try:
                out[key] = [float(x) for x in val.split(",") if x.strip()]
            except ValueError:
                pass
        else:
            out[key] = val
    if "trading_pair" not in out:
        return None
    return out


def controller_to_ladder(parsed: Dict[str, Any], cfg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert a parsed controller YAML into a ladder dict for the engine,
    including its OWN timings, fee, min order, and seed intent."""
    if not parsed:
        return None
    buys = parsed.get("buy_prices") or []
    sells = parsed.get("sell_prices") or []
    if len(buys) < 1 or len(sells) < 1:
        return None
    def f(key, default):
        try:
            return float(parsed.get(key, default))
        except (TypeError, ValueError):
            return float(default)
    total = f("total_amount_quote", cfg["fund_usd"])
    claimed = f("claimed_base_value_quote", total * (1 - cfg.get("rc_quote_frac", 0.5)))
    qf = min(max(1.0 - (claimed / total if total > 0 else 0.5), 0.0), 1.0)
    cooldowns = [f("buy_cooldown_time", float("nan")), f("sell_cooldown_time", float("nan"))]
    cooldowns = [c for c in cooldowns if c == c]
    cooldown = float(np.mean(cooldowns)) if cooldowns else f("cooldown_time", cfg["rc_cooldown_seconds"])
    ev = str(parsed.get("event_refresh_enabled", "true")).lower() in ("true", "1", "yes")
    return dict(
        source="controller_yaml",
        yaml_path=parsed.get("path"),
        controller_id=parsed.get("id", Path(parsed.get("path", "yaml")).stem),
        trading_pair=_pair_key(parsed.get("trading_pair")),
        connector_name=str(parsed.get("connector_name", "")).lower(),
        buy_prices=[float(x) for x in buys],
        sell_prices=[float(x) for x in sells],
        bw=np.asarray(parsed.get("buy_amounts_pct") or np.ones(len(buys)), float),
        sw=np.asarray(parsed.get("sell_amounts_pct") or np.ones(len(sells)), float),
        fund=total,
        quote_frac=qf,
        fee=f("fee_rate", cfg["fee"]),
        cooldown_seconds=cooldown if cooldown == cooldown else cfg["rc_cooldown_seconds"],
        refresh_seconds=f("executor_refresh_time", cfg["rc_refresh_seconds"]),
        min_order_quote=f("min_order_quote", cfg["rc_min_order_quote"]),
        event_refresh=ev,
        n_buy=len(buys), n_sell=len(sells),
        family="live_yaml", spacing_curve="manual", weight_curve="manual",
        candidate_id=f"yaml-{parsed.get('id', 'controller')}",
        buy_inner_pct=float("nan"), buy_outer_pct=float("nan"),
        sell_inner_pct=float("nan"), sell_outer_pct=float("nan"),
        anchor=float("nan"),
    )


def discover_controller_yamls(roots: Optional[Sequence[Any]] = None,
                              pattern: str = "range_inventory_ladder*.y*ml",
                              exchange: Optional[str] = None) -> List[Dict[str, Any]]:
    """Find + parse controller YAMLs under one or more directories (recursive),
    optionally filtered to one connector/exchange."""
    roots = [Path(r) for r in (roots or ["."])]
    found: List[Dict[str, Any]] = []
    seen_paths = set()
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob(pattern)):
            if str(p) in seen_paths:
                continue
            seen_paths.add(str(p))
            parsed = parse_controller_yaml(p)
            if parsed is None:
                continue
            if exchange and str(parsed.get("connector_name", "")).lower() != str(exchange).lower():
                continue
            found.append(parsed)
    return found


def evaluate_controller_yamls(parsed_list: Sequence[Dict[str, Any]],
                              hist_h: Dict[str, Any], uni: Dict[str, Any],
                              cfg: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    """Frozen-ladder block report for each live controller YAML on ITS market's
    hourly history, using ITS cooldowns/fees/seed intent. This is genuinely
    out-of-sample for any ladder written before the evaluation window ends."""
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
                             note="no hourly history loaded for this market"))
            continue
        bars = slice_days(ensure_ts(h["bars"]), int(cfg["rc_eval_days"]))
        rep = frozen_ladder_report(bars, ladder, cfg, label=label)
        details[ladder["controller_id"]] = rep
        s = rep["summary"]
        rows.append(dict(controller=ladder["controller_id"], pair=pk, src=h.get("src"),
                         days=s["days"], blocks=s.get("n_blocks", 0),
                         pnl_pct=s["pnl_pct"], hold_pct=s["hold_pct"], edge_pct=s["edge_pct"],
                         edge_pos_rate=s.get("edge_pos_rate"), abs_pos_rate=s.get("abs_pos_rate"),
                         worst_block_edge=s.get("worst_block_edge"),
                         trades=s["trades"], trades_per_month=s["trades_per_month"],
                         med_trades_per_block=s.get("median_trades_per_block"),
                         maxdd=s["maxdd"], endinv=s["endinv"],
                         stress_edge_pct=s["stress_edge_pct"],
                         passed=rep["passed"],
                         failed_gates="; ".join(rep["failed_gates"])))
    return pd.DataFrame(rows), details


# ======================================================================
# Hourly history prefetch
# ======================================================================
def prefetch_hourly(uni: Dict[str, Any], cfg: Dict[str, Any],
                    cache: Optional[CandleCache] = None,
                    pairs: Optional[Sequence[str]] = None,
                    src_hints: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Fetch hourly bars for the candidate set (threaded). Falls back to daily
    (via src_hints/hist) when hourly depth is below rc_min_hourly_days -- the
    engine then just runs at daily granularity for that market (worse, flagged)."""
    cache = cache or CandleCache(cfg["cache_dir"], cfg["cache_ttl_hours"])
    pairs = list(pairs if pairs is not None else uni["df"].pairkey)
    src_hints = src_hints or {}
    t0 = time.time()
    out: Dict[str, Any] = {}

    def one(pk):
        try:
            bars, src = _base.fetch_hourly(uni, pk, cfg, cache, src_hints.get(pk))
        except Exception as e:
            return pk, None, f"error:{e}"
        return pk, bars, src

    workers = max(2, int(cfg.get("mexc_workers", 8)))
    with _fut.ThreadPoolExecutor(max_workers=workers) as ex:
        for j, (pk, bars, src) in enumerate(ex.map(one, pairs), 1):
            if bars is not None:
                days = (bars[-1, 0] - bars[0, 0]) / 86400.0
                if days >= cfg["rc_min_hourly_days"]:
                    out[pk] = dict(bars=np.asarray(bars, float), src=src, days=days,
                                   granularity="1h")
            if j % 20 == 0:
                _log(f"  ...hourly {j}/{len(pairs)}")
    _log(f"hourly history: {len(out)}/{len(pairs)} markets in {time.time() - t0:.0f}s")
    return out


def with_daily_fallback(hist_h: Dict[str, Any], hist_d: Dict[str, Any],
                        cfg: Dict[str, Any], pairs: Sequence[str]) -> Dict[str, Any]:
    """Merge: hourly where available, daily otherwise (flagged)."""
    out = dict(hist_h)
    for pk in pairs:
        if pk in out:
            continue
        h = hist_d.get(pk)
        if h is None:
            continue
        bars = ensure_ts(np.asarray(h["bars"], float), 86400.0)
        out[pk] = dict(bars=bars, src=h.get("src"), granularity="1d",
                       days=(bars[-1, 0] - bars[0, 0]) / 86400.0)
    return out


# ======================================================================
# Per-market pipeline + finalize + exports
# ======================================================================
def evaluate_market(pk: str, hist_h: Dict[str, Any], uni: Dict[str, Any],
                    cfg: Dict[str, Any], run_wf: bool = True,
                    hist_report: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """WF (secondary) + deploy fit on last train window + frozen block report.

    Hybrid granularity: `hist_h` drives the candidate search + walk-forward
    (hourly is plenty for ladder geometry and 12x cheaper); `hist_report`, when
    given, drives the FROZEN block report and stress (use 5m here -- event
    refresh + cooldowns resolve at near-live latency)."""
    h = hist_h.get(pk)
    if h is None:
        return None
    bars = slice_days(ensure_ts(h["bars"]), int(cfg["rc_eval_days"]))
    pdec = uni.get("pdec", {}).get(pk)
    wf = rolling_walkforward(bars, cfg, pdec, label=pk) if run_wf else dict(n_folds=0, wf_pass=None, folds=pd.DataFrame())
    train = slice_days(bars, int(cfg["rc_train_days"]))
    fit = search_ladder(train, cfg, pdec, label=pk)
    hr = (hist_report or {}).get(pk)
    if hr is not None:
        rep_bars = slice_days(ensure_ts(hr["bars"]), int(cfg["rc_eval_days"]))
        rep_src, rep_gran = hr.get("src"), hr.get("granularity", "?")
    else:
        rep_bars, rep_src, rep_gran = bars, h.get("src"), h.get("granularity", "?")
    rep = frozen_ladder_report(rep_bars, fit["best"], cfg, label=f"{pk} deploy")
    return dict(pair=pk, src=rep_src, granularity=rep_gran,
                search_granularity=h.get("granularity", "?"),
                wf=wf, fit=fit, report=rep)


def _fund_sizing(uni, pk, cfg) -> Tuple[int, float, float, float]:
    spread_pct, depth_usd = _base.depth_info(uni, pk, cfg["depth_band"])
    vol_usd = float(uni["df"].set_index("pairkey").vol_usd.get(pk, float("nan")))
    vol_term = cfg["vol_fraction"] * vol_usd if vol_usd == vol_usd else float("inf")
    depth_term = cfg["depth_fraction"] * depth_usd if depth_usd == depth_usd else float("inf")
    basis = min(vol_term, depth_term)
    max_fund = _base.round_fund(basis, cfg) if basis != float("inf") else cfg["fund_floor"]
    return int(max_fund), float(spread_pct), float(depth_usd), float(vol_usd)


def finalize_v10(evals: Dict[str, Dict[str, Any]], uni: Dict[str, Any],
                 cfg: Dict[str, Any],
                 yaml_reports: Optional[Dict[str, Dict[str, Any]]] = None
                 ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Deploy gates + sizing + validated export configs for evaluated markets."""
    rows, configs = [], []
    for pk, ev in evals.items():
        if ev is None:
            continue
        cand = ev["fit"]["best"]
        rep = ev["report"]
        wf = ev["wf"]
        s = rep["summary"]
        pdec = uni.get("pdec", {}).get(pk)
        max_fund, spread_pct, depth_usd, vol_usd = _fund_sizing(uni, pk, cfg)
        gates: List[str] = list(rep["failed_gates"])
        slip_used = float(rep["summary"].get("slip_used_pct", cfg["slip_floor"] * 100)) / 100.0
        meas_slip = (spread_pct / 200.0) if spread_pct == spread_pct else 0.0
        if meas_slip > slip_used + cfg["rc_stress_extra_slip"]:
            gates.append(f"live half-spread {meas_slip*1e4:.0f}bps exceeds the "
                         f"{slip_used*1e4:.0f}bps slip the report already charged")
        if wf.get("wf_pass") is False:
            gates.append("rolling WF (process check) failed")
        p_last = uni.get("last_of", {}).get(pk, float("nan"))
        mq_ok, mq_need = _base.min_qty_check(
            cand["buy_prices"], cand["sell_prices"], cand["bw"], cand["sw"],
            max_fund, cfg, uni.get("min_qty", {}).get(pk),
            p_last if p_last == p_last else float(rep["result"]["close"][-1]))
        if not mq_ok:
            gates.append(f"min-qty needs fund >= ${mq_need:,.0f}")
        if depth_usd == depth_usd and depth_usd < cfg["min_depth_2pct"]:
            gates.append(f"thin book (${depth_usd:,.0f})")
        if ev.get("granularity") == "1d":
            gates.append("evaluated on DAILY bars only (hourly history unavailable)")
        fmt_problems = validate_ladder(cand["buy_prices"], cand["sell_prices"], pdec)
        if fmt_problems:
            gates.extend(fmt_problems)
        validation = ("CONFIRMED" if rep["passed"] and not gates
                      else ("GATED" if rep["passed"] else "SUSPECT"))
        rows.append(dict(
            base=pk, trading_pair=pk.replace("/", "-"), src=ev.get("src"),
            granularity=ev.get("granularity"), validation=validation,
            rungs=f"{cand['n_buy']}+{cand['n_sell']}",
            family=cand["family"], spacing=cand["spacing_curve"], weights=cand["weight_curve"],
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
            max_fund=max_fund, spread_pct=round(spread_pct, 4) if spread_pct == spread_pct else float("nan"),
            depth_2pct=round(depth_usd, 0) if depth_usd == depth_usd else float("nan"),
            gates="; ".join(gates)))
        configs.append(dict(
            symbol=pk, trading_pair=pk.replace("/", "-"), exchange=uni["exchange"],
            validation=validation, gates=gates,
            passive_order_placement=True,
            max_fund_value_quote=max_fund, total_amount_quote=max_fund,
            buy_prices=format_ladder_prices(cand["buy_prices"], pdec),
            sell_prices=format_ladder_prices(cand["sell_prices"], pdec),
            buy_amounts_pct=_base.weights_pct(cand["bw"]),
            sell_amounts_pct=_base.weights_pct(cand["sw"]),
            engine=dict(name="ladder_lab_recycle", version=__version__,
                        granularity=ev.get("granularity"),
                        train_days=ev["fit"]["train_days"],
                        family=cand["family"], spacing=cand["spacing_curve"],
                        weight_curve=cand["weight_curve"]),
            block_consistency=dict(passed=rep["passed"], **{k: v for k, v in s.items()
                                                            if k not in ("label",)}),
            walkforward=dict(passed=wf.get("wf_pass"),
                             edge_pos_rate=wf.get("edge_pos_rate"),
                             median_edge_pct=wf.get("median_edge_pct"),
                             worst_edge_pct=wf.get("worst_edge_pct"),
                             n_folds=wf.get("n_folds"))))
    df = pd.DataFrame(rows)
    if not df.empty:
        order = {"CONFIRMED": 0, "GATED": 1, "SUSPECT": 2}
        df["_o"] = df.validation.map(order).fillna(9) + 10 * df.data_suspect.astype(int)
        df = (df.sort_values(["_o", "edge_pos_rate", "edge_pct"], ascending=[True, False, False])
                .drop(columns="_o").reset_index(drop=True))
    return df, configs


def controller_copy_block(config: Dict[str, Any]) -> str:
    lines = [
        "buy_prices: " + ",".join(str(x) for x in config["buy_prices"]),
        "buy_amounts_pct: " + ",".join(str(x) for x in config["buy_amounts_pct"]),
        "sell_prices: " + ",".join(str(x) for x in config["sell_prices"]),
        "sell_amounts_pct: " + ",".join(str(x) for x in config["sell_amounts_pct"]),
    ]
    return "\n".join(lines)


def render_copy_paste_markdown(configs: Sequence[Dict[str, Any]],
                               yaml_df: Optional[pd.DataFrame] = None,
                               title: str = "Suggested ladder copy/paste values (v10 recycle engine)") -> str:
    from datetime import datetime
    out = [f"# {title}", "", f"Generated: {datetime.now().isoformat(timespec='seconds')}", "",
           "Validation is based on the RECYCLING sim (5m report bars) and 15-day block",
           "consistency vs hold. `CONFIRMED` = consistency gates + deploy gates passed; `GATED` =",
           "consistency passed but a deploy gate (depth/min-qty/precision/WF) flagged;",
           "`SUSPECT` = the block-consistency gates themselves failed.", ""]
    if yaml_df is not None and not yaml_df.empty:
        out += ["## Your live controller YAMLs on the same engine", "",
                df_to_markdown(yaml_df), ""]
    for c in configs:
        out.append(f"## {c['trading_pair']} — **{c['validation']}**")
        out.append("")
        bc = c.get("block_consistency", {})
        out.append(f"- Blocks: {bc.get('n_blocks')} x {int(c.get('engine', {}).get('train_days', 0)) and ''}"
                   f"edge_pos_rate={bc.get('edge_pos_rate')}, abs_pos_rate={bc.get('abs_pos_rate')}, "
                   f"worst_block_edge={bc.get('worst_block_edge')}%, "
                   f"median_trades/block={bc.get('median_trades_per_block')}")
        out.append(f"- Window: pnl={bc.get('pnl_pct')}% vs hold={bc.get('hold_pct')}% "
                   f"(edge {bc.get('edge_pct')}%), maxdd={bc.get('maxdd')}%, trades={bc.get('trades')}")
        out.append(f"- Conservative (body-only + slip): edge={bc.get('stress_edge_pct')}%")
        if c.get("gates"):
            out.append(f"- Gates/warnings: {'; '.join(c['gates'])}")
        out.append("")
        out.append("### Ladder-only copy/paste block")
        out.append("")
        out.append("```yaml")
        out.append(controller_copy_block(c))
        out.append("```")
        out.append("")
        out.append("### Optional sizing/cap block (clean reseed only)")
        out.append("")
        out.append("```yaml")
        out.append(f"max_fund_value_quote: {c['max_fund_value_quote']}")
        out.append(f"# total_amount_quote: {c['total_amount_quote']}  # clean reseed only")
        out.append("```")
        out.append("")
        if c["validation"] != "CONFIRMED":
            out.append("> Not a clean CONFIRMED result. Treat the gates above as real risk flags.")
            out.append("")
    return "\n".join(out)


def save_v10_outputs(prefix: str, final_df: pd.DataFrame, configs: List[Dict[str, Any]],
                     wf_rows: Optional[pd.DataFrame] = None,
                     yaml_df: Optional[pd.DataFrame] = None,
                     block_tables: Optional[Dict[str, pd.DataFrame]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> List[str]:
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
    p = f"{prefix}_deploy_config.json"
    with open(p, "w") as f:
        json.dump(dict(engine="ladder_lab_recycle", version=__version__,
                       metadata=metadata or {}, configs=configs), f, indent=2, default=str)
    written.append(p)
    p = f"{prefix}_copy_paste_ladders.md"
    with open(p, "w") as f:
        f.write(render_copy_paste_markdown(configs, yaml_df))
    written.append(p)
    for w in written:
        _log(f"  wrote {w}")
    return written


# ======================================================================
# Diagnostic JSONL replay -- calibrate the fill model against LIVE fills
# ======================================================================
def summarize_diagnostic_jsonl(path: Any, max_lines: int = 200000) -> pd.DataFrame:
    """Schema sniff: event-type histogram + the keys each type carries."""
    counts: Dict[str, int] = {}
    keys: Dict[str, set] = {}
    with open(path, "r", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ev = str(rec.get("event", rec.get("type", rec.get("event_type", "unknown"))))
            counts[ev] = counts.get(ev, 0) + 1
            keys.setdefault(ev, set()).update(rec.keys())
    return pd.DataFrame([dict(event=k, count=v, keys=", ".join(sorted(keys[k])))
                         for k, v in sorted(counts.items(), key=lambda kv: -kv[1])])


_FILL_EVENT_HINTS = ("fill", "trade", "order_filled", "executed")
_SIDE_KEYS = ("side", "trade_type", "order_side", "is_buy")
_PRICE_KEYS = ("price", "fill_price", "avg_price", "execution_price")
_AMOUNT_KEYS = ("amount", "qty", "quantity", "filled_amount", "base_amount")
_TS_KEYS = ("timestamp", "ts", "time", "created_at", "event_ts")


def extract_fills_from_jsonl(path: Any, max_lines: int = 500000) -> pd.DataFrame:
    """Best-effort fill extraction from a controller diagnostic JSONL.
    Returns DataFrame [ts, side, price, amount]. If empty, run
    summarize_diagnostic_jsonl() and adapt -- schemas vary by controller version."""
    rows = []
    with open(path, "r", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            try:
                rec = json.loads(line.strip() or "{}")
            except json.JSONDecodeError:
                continue
            flat = dict(rec)
            for v in list(rec.values()):
                if isinstance(v, dict):
                    for k2, v2 in v.items():
                        flat.setdefault(k2, v2)
            ev = str(flat.get("event", flat.get("type", flat.get("event_type", "")))).lower()
            if not any(h in ev for h in _FILL_EVENT_HINTS):
                continue
            def first(keys):
                for k in keys:
                    if k in flat and flat[k] is not None:
                        return flat[k]
                return None
            price = first(_PRICE_KEYS)
            amount = first(_AMOUNT_KEYS)
            side = first(_SIDE_KEYS)
            ts = first(_TS_KEYS)
            if price is None or ts is None:
                continue
            try:
                tsv = float(ts)
                if tsv > 1e12:
                    tsv /= 1000.0
            except (TypeError, ValueError):
                try:
                    tsv = pd.Timestamp(str(ts)).timestamp()
                except Exception:
                    continue
            if isinstance(side, bool):
                side = "buy" if side else "sell"
            side = str(side or "?").lower()
            side = "buy" if "buy" in side else ("sell" if "sell" in side else side)
            try:
                rows.append(dict(ts=tsv, side=side, price=float(price),
                                 amount=float(amount) if amount is not None else float("nan")))
            except (TypeError, ValueError):
                continue
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("ts").reset_index(drop=True)
        df["date"] = pd.to_datetime(df.ts, unit="s")
    return df


def compare_live_vs_sim(fills: pd.DataFrame, bars: np.ndarray, ladder: Dict[str, Any],
                        cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Run the recycle sim over the live-fill window and compare fill counts.
    A large mismatch means the fill model (or the candle source) is off and
    rc_target_trades_per_15d should be recalibrated."""
    if fills is None or fills.empty:
        return dict(note="no live fills extracted")
    t0, t1 = float(fills.ts.min()), float(fills.ts.max())
    bars = ensure_ts(bars)
    m = (bars[:, 0] >= t0 - 3600) & (bars[:, 0] <= t1 + 3600)
    window = bars[m]
    if len(window) < 24:
        return dict(note="candle window too short for comparison")
    res = run_ladder(window, ladder, cfg, stress=False)
    days = (t1 - t0) / 86400.0
    live_b = int((fills.side == "buy").sum())
    live_s = int((fills.side == "sell").sum())
    out = dict(window_days=round(days, 1),
               live_buy_fills=live_b, live_sell_fills=live_s,
               live_fills_per_day=round((live_b + live_s) / max(days, 1e-9), 2),
               sim_buy_fills=int(sum(res["bf"])), sim_sell_fills=int(sum(res["sf"])),
               sim_fills_per_day=round(res["trades"] / max(days, 1e-9), 2),
               sim_pnl_pct=round(res["pnl_pct"], 3), sim_edge_pct=round(res["edge_pct"], 3))
    ratio = out["sim_fills_per_day"] / out["live_fills_per_day"] if out["live_fills_per_day"] else float("nan")
    out["sim_over_live_fill_ratio"] = round(ratio, 2) if ratio == ratio else float("nan")
    return out


# ======================================================================
# Intraday (5m) history -- native-first on NonKYC, paginated MEXC proxy
# ======================================================================
_IV_MS = {"1m": 60000, "5m": 300000, "15m": 900000, "30m": 1800000,
          "60m": 3600000, "4h": 14400000, "1d": 86400000}
_NONKYC_RES = {"1m": "1", "5m": "5", "15m": "15", "30m": "30",
               "60m": "60", "1d": "1440"}


def mexc_klines_interval(symbol: str, interval: str, days: float,
                         limit: int = 1000, max_pages: int = 400) -> Optional[np.ndarray]:
    """Paginated MEXC klines with a CORRECT interval->ms map (the base helper's
    map lacks sub-hourly intervals, which breaks its termination check at 5m).
    180d of 5m ~= 104 pages at MEXC's ~500 rows/page. Verified live 2026-07."""
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
    return np.array([[int(x[0]) / 1000.0, float(x[1]), float(x[2]),
                      float(x[3]), float(x[4])] for x in rows], float)


def fetch_intraday(uni: Dict[str, Any], pairkey: str, cfg: Dict[str, Any],
                   cache: Optional[CandleCache] = None, src_hint: Optional[str] = None,
                   interval: Optional[str] = None) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """Intraday bars for the report engine. Order of preference:
      1. NonKYC NATIVE (their /market/candles serves the FULL requested range in
         one call at 5m -- verified live; ts in ms, converted by the base helper).
         Real NonKYC microstructure beats any proxy at fine granularity.
      2. MEXC proxy (paginated, guarded by the base price-proxy check).
      3. Hourly fallback via the base fetcher.
    Returns (bars, src)."""
    cache = cache or CandleCache(cfg["cache_dir"], cfg["cache_ttl_hours"])
    interval = interval or cfg.get("rc_report_interval", "5m")
    if interval in ("60m", "1h"):
        return _base.fetch_hourly(uni, pairkey, cfg, cache, src_hint)
    days = float(cfg.get("rc_intraday_days", cfg.get("hourly_days", 185)))
    bars_per_day = 86400.0 / (_IV_MS.get(interval, 300000) / 1000.0)
    min_bars = int(bars_per_day * 7)
    coin, quote = uni["base_of"][pairkey], uni["quote_of"][pairkey]

    if uni["exchange"] == "nonkyc" and interval in _NONKYC_RES:
        key = f"nonkyc_{pairkey}_{interval}"
        bars = cache.get(key)
        if bars is None:
            bars = _base.nonkyc_ohlc_native(coin, quote, _NONKYC_RES[interval], days,
                                            cfg["nonkyc_timeout"], cfg["nonkyc_sleep"])
            if bars is not None and len(bars) >= min_bars:
                cache.put(key, bars)
        if bars is not None and len(bars) >= min_bars:
            return bars, "NonKYC"

    key = f"mexc_{_base.mexc_symbol(coin, quote)}_{interval}"
    bars = cache.get(key)
    if bars is None:
        bars = mexc_klines_interval(_base.mexc_symbol(coin, quote), interval, days)
        if bars is not None and len(bars) >= min_bars:
            cache.put(key, bars)
    if (bars is not None and len(bars) >= min_bars
            and _base._proxy_ok(uni, pairkey, bars, cfg)):
        return bars, "MEXC"

    return _base.fetch_hourly(uni, pairkey, cfg, cache, src_hint)


def prefetch_intraday(uni: Dict[str, Any], cfg: Dict[str, Any],
                      cache: Optional[CandleCache] = None,
                      pairs: Optional[Sequence[str]] = None,
                      src_hints: Optional[Dict[str, str]] = None,
                      interval: Optional[str] = None) -> Dict[str, Any]:
    """Threaded fetch_intraday over the review set. NonKYC-native 5m is one
    request per market, so keep the pool small and polite for that leg."""
    cache = cache or CandleCache(cfg["cache_dir"], cfg["cache_ttl_hours"])
    pairs = list(pairs if pairs is not None else uni["df"].pairkey)
    src_hints = src_hints or {}
    interval = interval or cfg.get("rc_report_interval", "5m")
    t0 = time.time()
    out: Dict[str, Any] = {}

    def one(pk):
        try:
            bars, src = fetch_intraday(uni, pk, cfg, cache, src_hints.get(pk), interval)
        except Exception as e:
            return pk, None, f"error:{e}"
        return pk, bars, src

    workers = max(2, min(int(cfg.get("nonkyc_workers", 4)), 6)) \
        if uni["exchange"] == "nonkyc" else max(2, int(cfg.get("mexc_workers", 8)))
    with _fut.ThreadPoolExecutor(max_workers=workers) as ex:
        for j, (pk, bars, src) in enumerate(ex.map(one, pairs), 1):
            if bars is not None:
                bars = ensure_ts(np.asarray(bars, float))
                days = (bars[-1, 0] - bars[0, 0]) / 86400.0
                if days >= cfg.get("rc_min_intraday_days", cfg["rc_min_hourly_days"]):
                    bsec = bar_seconds_of(bars)
                    gran = interval if bsec < 3599 else ("1h" if bsec < 86000 else "1d")
                    out[pk] = dict(bars=bars, src=src, days=days, granularity=gran)
            if j % 10 == 0:
                _log(f"  ...intraday {j}/{len(pairs)}")
    _log(f"intraday({interval}) history: {len(out)}/{len(pairs)} markets "
         f"in {time.time() - t0:.0f}s")
    return out


# ======================================================================
# tabulate-free markdown tables (DataFrame.to_markdown needs `tabulate`)
# ======================================================================
def df_to_markdown(df: pd.DataFrame, index: bool = False) -> str:
    """Pipe-table renderer with a graceful fallback when `tabulate` is absent."""
    if df is None or df.empty:
        return "(empty)"
    try:
        return df.to_markdown(index=index)
    except ImportError:
        pass
    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]
    def cell(v):
        if isinstance(v, float):
            return f"{v:.6g}"
        return str(v)
    lines = ["| " + " | ".join(cols) + " |",
             "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in d.iterrows():
        lines.append("| " + " | ".join(cell(v) for v in row) + " |")
    return "\n".join(lines)


# ======================================================================
# v10.2 -- market-microstructure realism + band-aware gates
# (added after the first full live run exposed spread-bounce harvesting on
#  thin NonKYC books and dormant-block gate poisoning; see notes doc)
# ======================================================================
def roll_half_spread_pct(bars: np.ndarray) -> float:
    """Roll (1984) effective HALF-spread estimate from close-to-close returns.
    Bid/ask bounce induces negative lag-1 autocovariance: half = sqrt(-cov).
    Returns percent of price. ~0 for genuine random-walk mids; large for
    illiquid books whose 'candles' are alternating bid/ask prints (the DOGS
    +30M% failure mode). Under near-deterministic print alternation this
    returns up to the FULL spread rather than half -- deliberately accepted:
    it over-charges exactly the markets whose candles are least tradeable.
    Computed on RAW candles -- call before regularizing."""
    c = ensure_ts(bars)[:, 4]
    if len(c) < 50:
        return 0.0
    r = np.diff(np.log(np.maximum(c, 1e-30)))
    r = r[np.isfinite(r)]
    if len(r) < 40:
        return 0.0
    cov1 = float(np.mean((r[1:] - r[1:].mean()) * (r[:-1] - r[:-1].mean())))
    if cov1 >= 0:
        return 0.0
    return float(np.sqrt(-cov1) * 100.0)


def effective_slip(bars: np.ndarray, cfg: Dict[str, Any],
                   extra_half_spread_pct: float = 0.0) -> float:
    """Per-side slippage for THIS market: max(config floor, Roll half-spread,
    any externally measured half-spread), capped at rc_slip_cap. This is what
    stops the sim from harvesting bid/ask bounce as free oscillation."""
    if not cfg.get("rc_slip_from_roll", True):
        return float(cfg.get("slip_floor", 0.001))
    roll = roll_half_spread_pct(bars) / 100.0
    slip = max(float(cfg.get("slip_floor", 0.001)), roll,
               float(extra_half_spread_pct) / 100.0)
    return float(min(slip, float(cfg.get("rc_slip_cap", 0.06))))


def regularize_bars(bars: np.ndarray, bar_seconds: Optional[float] = None
                    ) -> Tuple[np.ndarray, float]:
    """Snap candles onto a fixed time grid; fill gaps (NonKYC native candles
    OMIT trade-less periods) with flat bars at the previous close. Flat bars
    cannot create fills but restore correct cooldown/refresh timing and block
    spans. Returns (bars, fill_fraction_of_grid_that_was_missing)."""
    bars = ensure_ts(bars)
    if len(bars) < 3:
        return bars, 0.0
    d = np.diff(bars[:, 0])
    d = d[d > 0]
    step = float(bar_seconds or 0) or float(np.median(d))
    for grid in (60.0, 300.0, 900.0, 1800.0, 3600.0, 14400.0, 86400.0):
        if abs(step - grid) / grid < 0.25:
            step = grid
            break
    t0, t1 = bars[0, 0], bars[-1, 0]
    n = int(round((t1 - t0) / step)) + 1
    if n <= len(bars) or n > 4 * 10 ** 6:
        return bars, 0.0
    idx = np.clip(np.round((bars[:, 0] - t0) / step).astype(int), 0, n - 1)
    out = np.zeros((n, 5))
    out[:, 0] = t0 + step * np.arange(n)
    have = np.zeros(n, bool)
    out[idx, 1:] = bars[:, 1:]
    have[idx] = True
    last_c = bars[0, 1]
    for i in range(n):
        if have[i]:
            last_c = out[i, 4]
        else:
            out[i, 1:] = last_c
    return out, float(1.0 - have.mean())


def _cycle_edge_gate(summary: Dict[str, Any], cfg: Dict[str, Any],
                     rt_cost_pct: float) -> Optional[str]:
    """Backstop plausibility check: implied per-round-trip edge must not dwarf
    the round-trip cost. Catches residual data pathologies even after Roll slip."""
    trades = int(summary.get("trades", 0))
    cycles = trades / 2.0
    if cycles < 10:
        return None
    pnl = float(summary.get("pnl_pct", 0.0)) / 100.0
    if pnl <= 0:
        return None
    per_cycle = (1.0 + pnl) ** (1.0 / cycles) - 1.0
    limit = max(float(cfg.get("rc_gate_max_cycle_edge_pct", 1.5)) / 100.0,
                float(cfg.get("rc_gate_max_cycle_edge_x", 3.0)) * rt_cost_pct / 100.0)
    if per_cycle > limit:
        return (f"implied {per_cycle*100:.2f}%/round-trip edge exceeds plausible "
                f"{limit*100:.2f}% (bid/ask-bounce candles?) -- treat as INVALID DATA")
    return None
