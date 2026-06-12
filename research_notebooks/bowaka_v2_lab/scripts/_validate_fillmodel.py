#!/usr/bin/env python
"""PB.5 — fill-fidelity validation against the REAL trade tape.

Quantifies how optimistic the legacy fill model is. For a sample of real
``(symbol, minute)`` points drawn from the lake it compares:

* the **legacy** fill — fills the WHOLE order at the bar price with ZERO
  slippage (the pre-PB.1 sell/exit behaviour: an exit at exactly the bracket
  price, always 100% filled); against
* the **tape_replay** fill — :func:`replay_tape_fill` over the ACTUAL prints in
  ``[t, t + window]`` (the size-weighted VWAP a marketable order would really
  achieve, honouring the stop/target trigger + a participation cap).

It reports the slippage distribution and the fill-fraction so the realism gap
the legacy model hides (give-up vs the touch + partial fills) is measured on the
real tape — not asserted. Read-only: it touches only ``bars/`` and ``trades/``
and writes nothing to the lake.

Usage (in the ql-jupyter container)::

    PYTHONPATH=research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src \
      python research_notebooks/bowaka_v2_lab/scripts/_validate_fillmodel.py \
      --lake-root /opt/market_data_cache --feed sip \
      --symbols 8 --sessions 3 --notional 4000 --window 300 --participation 1.0
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _bootstrap_path() -> None:
    here = Path(__file__).resolve()
    # .../research_notebooks/bowaka_v2_lab/scripts/_validate_fillmodel.py
    repo = here.parents[3]
    for sub in ("research_notebooks/bowaka_v2_lab/src", "research_notebooks/bowaka_common/src"):
        p = str(repo / sub)
        if p not in sys.path:
            sys.path.insert(0, p)


_bootstrap_path()

from bowaka_common.marketdata import MarketDataStore  # noqa: E402
from bowaka_v2_lab.data.suppliers import make_trades_supplier  # noqa: E402
from bowaka_v2_lab.sim.tape_fill import replay_tape_fill  # noqa: E402


def _discover_symbols(lake_root: Path, feed: str, want: int) -> list[str]:
    """Pick the ``want`` symbols with the most trade-month partitions (a coverage
    proxy → the most-liquid names that actually have a usable tape)."""
    base = lake_root / "trades" / "vendor=alpaca" / f"feed={feed}"
    if not base.is_dir():
        return []
    counts: list[tuple[int, str]] = []
    for symdir in base.glob("symbol=*"):
        sym = symdir.name.split("=", 1)[1]
        n = sum(1 for _ in symdir.rglob("*.parquet"))
        if n > 0:
            counts.append((n, sym))
    counts.sort(reverse=True)
    return [s for _, s in counts[:want]]


def _sessions_from_bars(store: MarketDataStore, symbol: str, feed: str, want: int) -> list[_dt.date]:
    """The ``want`` most-recent ET session dates that ``symbol`` has minute bars for."""
    end = _dt.date.today()
    start = end - _dt.timedelta(days=20)
    mb = store.minute_bars(symbol, start, end, feed=feed)
    if mb is None or mb.empty or "timestamp" not in mb.columns:
        return []
    ts = pd.to_datetime(mb["timestamp"], utc=True).dt.tz_convert("America/New_York")
    days = sorted(set(ts.dt.date))
    return days[-want:]


def _session_window(session: _dt.date) -> tuple[pd.Timestamp, pd.Timestamp]:
    open_et = pd.Timestamp(_dt.datetime.combine(session, _dt.time(9, 35)), tz="America/New_York")
    close_et = pd.Timestamp(_dt.datetime.combine(session, _dt.time(15, 55)), tz="America/New_York")
    return open_et.tz_convert("UTC"), close_et.tz_convert("UTC")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lake-root", default=os.environ.get("MARKET_DATA_ROOT", "/opt/market_data_cache"))
    ap.add_argument("--feed", default="sip")
    ap.add_argument("--symbols", type=int, default=8)
    ap.add_argument("--sessions", type=int, default=3)
    ap.add_argument("--minutes-per-session", type=int, default=24, help="evenly-spaced sampled minutes")
    ap.add_argument("--notional", type=float, default=4000.0, help="order $ notional per sampled fill")
    ap.add_argument("--window", type=float, default=300.0, help="tape window seconds")
    ap.add_argument("--participation", type=float, default=1.0)
    args = ap.parse_args()

    lake_root = Path(args.lake_root)
    store = MarketDataStore(lake_root, vendor="alpaca")
    trades_supplier = make_trades_supplier(lake_root, feed=args.feed)

    symbols = _discover_symbols(lake_root, args.feed, args.symbols)
    if not symbols:
        print(f"NO trades/ symbols found under {lake_root} (feed={args.feed}) — run the PA.2 backfill first.")
        return 2
    print(f"lake={lake_root} feed={args.feed} symbols={symbols} "
          f"sessions={args.sessions} notional=${args.notional:.0f} window={args.window:.0f}s "
          f"participation={args.participation}")

    rows: list[dict] = []
    for sym in symbols:
        sessions = _sessions_from_bars(store, sym, args.feed, args.sessions)
        for session in sessions:
            w0, w1 = _session_window(session)
            mb = store.minute_bars(sym, w0, w1, feed=args.feed)
            if mb is None or mb.empty:
                continue
            mb = mb.sort_values("timestamp").reset_index(drop=True)
            n = len(mb)
            if n == 0:
                continue
            idxs = np.linspace(0, n - 1, min(args.minutes_per_session, n)).astype(int)
            for i in set(idxs.tolist()):
                bar = mb.iloc[i]
                t = pd.Timestamp(bar["timestamp"])
                t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
                px = float(bar.get("close", bar.get("Close", 0.0)) or 0.0)
                if px <= 0:
                    continue
                qty = int(args.notional / px)
                if qty <= 0:
                    continue
                tr = trades_supplier(sym, t, t + pd.Timedelta(seconds=args.window))
                # SELL-stop fidelity: marketable sell, prints at/below the bar px.
                sell = replay_tape_fill(
                    tr, qty=qty, start_ts=t, window_seconds=args.window,
                    participation=args.participation, max_price=px,
                )
                # BUY fidelity: marketable buy, prints at/above the bar px.
                buy = replay_tape_fill(
                    tr, qty=qty, start_ts=t, window_seconds=args.window,
                    participation=args.participation, min_price=px,
                )
                rows.append({
                    "symbol": sym, "ts": t, "bar_px": px, "qty": qty,
                    "sell_filled_frac": sell.fill_fraction if sell.filled_qty > 0 else 0.0,
                    "sell_slip_bps": ((sell.avg_fill_price - px) / px * 1e4) if sell.filled_qty > 0 else np.nan,
                    "sell_any": sell.filled_qty > 0,
                    "sell_full": sell.filled,
                    "buy_filled_frac": buy.fill_fraction if buy.filled_qty > 0 else 0.0,
                    "buy_slip_bps": ((buy.avg_fill_price - px) / px * 1e4) if buy.filled_qty > 0 else np.nan,
                    "buy_any": buy.filled_qty > 0,
                    "buy_full": buy.filled,
                })

    if not rows:
        print("NO samples produced (no overlapping bars+trades). Widen --sessions / check the lake.")
        return 2
    df = pd.DataFrame(rows)
    n = len(df)

    def _pct(x: pd.Series) -> str:
        return f"{100.0 * float(x.mean()):.1f}%"

    def _stat(col: str) -> str:
        s = df[col].dropna()
        if s.empty:
            return "n/a (no fills)"
        return (f"median={s.median():+.1f}  mean={s.mean():+.1f}  "
                f"p10={s.quantile(0.10):+.1f}  p90={s.quantile(0.90):+.1f}")

    print("\n" + "=" * 72)
    print(f"FILL-FIDELITY vs REAL TAPE  (N={n} sampled exits/entries)")
    print("=" * 72)
    print("Legacy model (baseline): fills 100% at the bar price, 0 bps slippage.")
    print("-" * 72)
    print(f"SELL/exit  any-fill={_pct(df['sell_any'])}  full-fill={_pct(df['sell_full'])}  "
          f"median fill-frac={df.loc[df['sell_any'],'sell_filled_frac'].median():.2f}")
    print(f"  slippage bps vs bar px:  {_stat('sell_slip_bps')}")
    print(f"BUY/entry  any-fill={_pct(df['buy_any'])}  full-fill={_pct(df['buy_full'])}  "
          f"median fill-frac={df.loc[df['buy_any'],'buy_filled_frac'].median():.2f}")
    print(f"  slippage bps vs bar px:  {_stat('buy_slip_bps')}")
    print("=" * 72)
    print("Interpretation: legacy assumes 100% fill at 0 slippage; the tape shows")
    print("the real fill fraction (< 100% ⇒ legacy over-fills) and the real give-up")
    print("(non-zero bps ⇒ legacy was optimistic). This is the gap PB.1-4 close.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
