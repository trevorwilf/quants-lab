"""Numba fill kernel for the range_ladder strategy.

Exact port of the validated ladder_lab `_sim_kernel` (Trading Pod oscillator
finder, v3 cooldown-in-bars semantics), extended with a per-bar base-balance
track so the pmm_lab dispatch layer can build a SimResult position history.

Semantics (keep exact — do not "improve" without regenerating fixtures):

- Initial state: quote = fund*quote_frac, base = fund*(1-quote_frac)/c[0].
- Per-rung quantities are STATIC, computed once at t=0:
    buy_qty_i  = (fund*quote_frac * bw_i/Σbw) / buy_price_i
    sell_qty_i = (fund*(1-quote_frac)/c[0]) * sw_i/Σsw
  (Known, accepted Phase A bias: no proceeds recycling — Phase B fixes this.)
- Intrabar path: up bar (c>=o) → o,l,h,c; down bar → o,h,l,c. body_only → o,c.
- On a DOWN leg a..b (b<a): armed buy rung i fills iff b <= P_i <= a AND
  t - last_fill_i > cooldown_bars AND quote covers cost*(1+fee+slip).
  Buy collateral INCLUDES the fee — matches the live NonKYC hold
  (totalWithFee = price*qty*(1+fee)).
- On an UP leg symmetric for sells, gated on base >= sell_qty_i; credits
  proceeds*(1-fee-slip).
- A rung disarms on fill and re-arms when the CLOSE crosses back past it
  (c > buy rung / c < sell rung). The cooldown is enforced at fill time
  (t - last_fill > cooldown_bars), so a re-armed rung still cannot refill
  inside its cooldown window. Initial arm: buy armed iff c[0] > P_i, sell
  armed iff c[0] < P_i.
- max_fills_per_bar caps TOTAL fills per bar (both sides combined).

`executor_refresh_time` is NOT modeled — the bar-path simulator cannot
express it. That is Phase B (event-level sim, separate prompt).

The pure-Python reference `_run_ladder_reference` must match the compiled
kernel bit-for-bit; parity is frozen in fixtures/numba_parity/rl_*.npz
(see scripts/generate_range_ladder_fixtures.py).
"""

from __future__ import annotations

import math

import numpy as np

from pmm_lab.features._numba_availability import _NUMBA_AVAILABLE

if _NUMBA_AVAILABLE:
    from numba import njit  # type: ignore
else:
    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]

        def _wrap(fn):
            return fn
        return _wrap


# Sentinel for "unbounded fills per bar" (mirrors ladder_lab's 2**62).
UNBOUNDED_FILLS = np.int64(2 ** 62)


@njit(cache=True)
def _run_ladder_kernel(
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
    buys: np.ndarray,
    sells: np.ndarray,
    bw: np.ndarray,
    sw: np.ndarray,
    fund: float,
    qf: float,
    fee: float,
    slip: float,
    max_fills_per_bar: np.int64,
    cooldown_bars: np.int64,
    body_only: bool,
):
    """Compiled ladder fill loop.

    Returns (quote, base, fees, bf, sf, cb, cs, eq, pb):
      bf/sf — per-rung fill counts; cb/cs — cumulative buy/sell fills per bar;
      eq — per-bar equity (quote + base*close); pb — per-bar base balance.
    """
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
    pb = np.zeros(n)
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
                    if (b_arm[i] and (t - b_last[i] > cooldown_bars)
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
                    if (s_arm[i] and (t - s_last[i] > cooldown_bars)
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
        pb[t] = base
    return quote, base, fees, bf, sf, cb, cs, eq, pb


def _run_ladder_reference(
    o, h, l, c, buys, sells, bw, sw,
    fund, qf, fee, slip, max_fills_per_bar, cooldown_bars, body_only,
):
    """Pure-Python reference implementation — the parity golden path.

    Direct port of ladder_lab's `_sim_reference` (weights + stress dials),
    extended with the per-bar base track. Must match `_run_ladder_kernel`
    bit-for-bit on the frozen fixtures.
    """
    n = len(c)
    nb = len(buys)
    ns = len(sells)
    p0 = c[0]
    quote = fund * qf
    base = fund * (1.0 - qf) / p0
    sbw = float(sum(bw))
    ssw = float(sum(sw))
    buy_qty = [(fund * qf * bw[i] / sbw) / buys[i] for i in range(nb)]
    sell_qty = [(fund * (1.0 - qf) / p0) * sw[i] / ssw for i in range(ns)]
    b_arm = [p0 > buys[i] for i in range(nb)]
    s_arm = [p0 < sells[i] for i in range(ns)]
    cm = fee + slip
    mfpb = int(max_fills_per_bar)
    bf = np.zeros(nb, np.int64)
    sf = np.zeros(ns, np.int64)
    b_last = [-1000000000] * nb
    s_last = [-1000000000] * ns
    cb = np.zeros(n, np.int64)
    cs = np.zeros(n, np.int64)
    eq = np.zeros(n)
    pb = np.zeros(n)
    fees = 0.0
    nbt = 0
    nst = 0
    for t in range(n):
        if body_only:
            path = [o[t], c[t]]
        else:
            if c[t] >= o[t]:
                path = [o[t], l[t], h[t], c[t]]
            else:
                path = [o[t], h[t], l[t], c[t]]
        fb = 0
        for a, b in zip(path, path[1:]):
            if b < a:
                for i in range(nb):
                    if fb >= mfpb:
                        break
                    if (b_arm[i] and (t - b_last[i] > cooldown_bars)
                            and (b <= buys[i] <= a)):
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
                    if fb >= mfpb:
                        break
                    if (s_arm[i] and (t - s_last[i] > cooldown_bars)
                            and (a <= sells[i] <= b)
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
        pb[t] = base
    return quote, base, fees, bf, sf, cb, cs, eq, pb


def run_ladder_sim(
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
    buys: np.ndarray,
    sells: np.ndarray,
    bw: np.ndarray = None,
    sw: np.ndarray = None,
    *,
    fund: float = 1000.0,
    quote_frac: float = 0.5,
    fee: float = 0.002,
    slip: float = 0.0,
    cooldown_bars: int = 0,
    max_fills_per_bar: int = 0,
    body_only: bool = False,
    bar_interval_seconds: int = 3600,
    use_numba: bool = None,
) -> dict:
    """Run the ladder fill sim and assemble the standard output dict.

    Bar-interval-agnostic: `bar_interval_seconds` only affects the
    time-normalized outputs (trades_per_month), never the fill logic.

    Parameters
    ----------
    max_fills_per_bar : int
        0 = unbounded (default backtest); stress mode uses 1.
    use_numba : bool, optional
        None = use the compiled kernel when numba is available. False forces
        the pure-Python reference (used by parity tests).

    Returns
    -------
    dict with keys: pnl, pnl_pct, hold_pct, maxdd, endinv_pct, fees, trades,
    buy_fills, sell_fills, cum_buy_fills, cum_sell_fills, equity,
    base_history, time_in_band, trades_per_month, final_quote, final_base.
    """
    o = np.ascontiguousarray(np.asarray(o, dtype=np.float64))
    h = np.ascontiguousarray(np.asarray(h, dtype=np.float64))
    l = np.ascontiguousarray(np.asarray(l, dtype=np.float64))
    c = np.ascontiguousarray(np.asarray(c, dtype=np.float64))
    buys = np.asarray(buys, dtype=np.float64)
    sells = np.asarray(sells, dtype=np.float64)
    bw = np.ones(len(buys)) if bw is None else np.asarray(bw, dtype=np.float64)
    sw = np.ones(len(sells)) if sw is None else np.asarray(sw, dtype=np.float64)
    if len(c) == 0:
        raise ValueError("run_ladder_sim: empty candle window")

    mfpb = UNBOUNDED_FILLS if max_fills_per_bar in (0, None) else np.int64(max_fills_per_bar)
    if use_numba is None:
        use_numba = _NUMBA_AVAILABLE
    impl = _run_ladder_kernel if (use_numba and _NUMBA_AVAILABLE) else _run_ladder_reference

    quote, base, fees, bf, sf, cb, cs, eq, pb = impl(
        o, h, l, c, buys, sells, bw, sw,
        float(fund), float(quote_frac), float(fee), float(slip),
        mfpb, np.int64(cooldown_bars), bool(body_only),
    )

    last = float(c[-1])
    final = quote + base * last
    init = float(fund)
    hold = fund * quote_frac + (fund * (1.0 - quote_frac) / c[0]) * last
    peak = np.maximum.accumulate(eq)
    maxdd = float(np.max((peak - eq) / np.where(peak > 0, peak, 1.0))) * 100.0
    lo_b, hi_s = float(np.min(buys)), float(np.max(sells))
    months = len(c) * bar_interval_seconds / 86400.0 / 30.4
    trades = int(np.sum(bf) + np.sum(sf))

    return dict(
        pnl=float(final - init),
        pnl_pct=float((final - init) / init * 100.0),
        hold_pct=float((hold - init) / init * 100.0),
        maxdd=maxdd,
        endinv_pct=float(base * last / final * 100.0) if final else 0.0,
        fees=float(fees),
        trades=trades,
        buy_fills=[int(x) for x in bf],
        sell_fills=[int(x) for x in sf],
        cum_buy_fills=np.asarray(cb),
        cum_sell_fills=np.asarray(cs),
        equity=np.asarray(eq),
        base_history=np.asarray(pb),
        time_in_band=float(np.mean((c >= lo_b) & (c <= hi_s))),
        trades_per_month=float(trades / months) if months > 0 else 0.0,
        final_quote=float(quote),
        final_base=float(base),
    )


def quarter_split(cb, cs, eq, fund, nq: int = 4, min_side: int = 2):
    """Quarter-durability split, ported from ladder_lab.

    Splits the run into `nq` equal spans and counts how many are two-sided
    (both sides with >= min_side fills). Returns
    (two_sided_quarters, recent_activity_pct, per_q_buys, per_q_sells, per_q_pnl).
    """
    n = len(eq)
    eqf = np.concatenate([[fund], np.asarray(eq, dtype=np.float64)])
    cbf = np.concatenate([[0], np.asarray(cb)])
    csf = np.concatenate([[0], np.asarray(cs)])
    bnd = [round(n * k / nq) for k in range(nq + 1)]
    qb, qs, qp = [], [], []
    for q in range(nq):
        s, e = bnd[q], bnd[q + 1]
        qb.append(int(cbf[e] - cbf[s]))
        qs.append(int(csf[e] - csf[s]))
        qp.append(float(eqf[e] - eqf[s]))
    two_sided = sum(1 for i in range(nq) if qb[i] >= min_side and qs[i] >= min_side)
    total = (int(cb[-1]) + int(cs[-1])) or 1
    recent_pct = (qb[-1] + qs[-1]) / total * 100.0
    return two_sided, recent_pct, qb, qs, qp
