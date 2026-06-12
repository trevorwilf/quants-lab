#!/usr/bin/env python
"""PC.3 — end-to-end exit-fill PnL on the REAL tape (legacy vs tape_replay).

Drives the ACTUAL engine exit path (:func:`sim.exits.walk_lot_exit` — the one the
backtester calls) over real minute bars + the real trade tape, for a set of
synthetic-but-realistic long lots. It walks each lot to exit TWICE — once with
the legacy bracket fill (exact stop/target price, 0 slippage) and once with
``fill_model="tape_replay"`` (the real-tape VWAP) — holding the ENTRY fixed, so
the realized-PnL delta isolates the honest EXIT fill.

This is the PC.3 demonstration that honest fills lower realized PnL (≤ legacy) —
end-to-end through the wired exit engine, not just the oracle (PB.5). It avoids
the scanner/PIT-universe pipeline (which yields an empty universe on a scoped
window — a universe issue orthogonal to the fill model). Read-only on the lake.

Usage (ql-jupyter container)::

    PYTHONPATH=research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src \
      python research_notebooks/bowaka_v2_lab/scripts/_pc3_exit_pnl.py \
      --lake-root /opt/market_data_cache --feed sip --symbols 8 --sessions 3 \
      --notional 8000 --stop-pct 0.02 --target-pct 0.03
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
    repo = Path(__file__).resolve().parents[3]
    for sub in ("research_notebooks/bowaka_v2_lab/src", "research_notebooks/bowaka_common/src"):
        p = str(repo / sub)
        if p not in sys.path:
            sys.path.insert(0, p)


_bootstrap_path()

from bowaka_common.marketdata import MarketDataStore  # noqa: E402
from bowaka_v2_lab.data.suppliers import make_trades_supplier  # noqa: E402
from bowaka_v2_lab.sim.exits import walk_lot_exit  # noqa: E402
from bowaka_v2_lab.sim.portfolio import Position  # noqa: E402


def _discover_symbols(lake_root: Path, feed: str, want: int) -> list[str]:
    base = lake_root / "trades" / "vendor=alpaca" / f"feed={feed}"
    if not base.is_dir():
        return []
    counts = []
    for symdir in base.glob("symbol=*"):
        n = sum(1 for _ in symdir.rglob("*.parquet"))
        if n > 0:
            counts.append((n, symdir.name.split("=", 1)[1]))
    counts.sort(reverse=True)
    return [s for _, s in counts[:want]]


def _sessions_for(store: MarketDataStore, sym: str, feed: str, want: int) -> list[_dt.date]:
    end = _dt.date.today()
    mb = store.minute_bars(sym, end - _dt.timedelta(days=20), end, feed=feed)
    if mb is None or mb.empty:
        return []
    ts = pd.to_datetime(mb["timestamp"], utc=True).dt.tz_convert("America/New_York")
    return sorted(set(ts.dt.date))[-want:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lake-root", default=os.environ.get("MARKET_DATA_ROOT", "/opt/market_data_cache"))
    ap.add_argument("--feed", default="sip")
    ap.add_argument("--symbols", type=int, default=8)
    ap.add_argument("--sessions", type=int, default=3)
    ap.add_argument("--entries-per-session", type=int, default=6)
    ap.add_argument("--notional", type=float, default=8000.0)
    ap.add_argument("--stop-pct", type=float, default=0.02)
    ap.add_argument("--target-pct", type=float, default=0.03)
    ap.add_argument("--window", type=float, default=300.0)
    ap.add_argument("--participation", type=float, default=1.0)
    args = ap.parse_args()

    lake_root = Path(args.lake_root)
    store = MarketDataStore(lake_root, vendor="alpaca")
    trades_supplier = make_trades_supplier(lake_root, feed=args.feed)
    symbols = _discover_symbols(lake_root, args.feed, args.symbols)
    if not symbols:
        print(f"NO trades/ symbols under {lake_root} (feed={args.feed})")
        return 2

    legacy_cfg = {"time_stop": {"enabled": False}, "signal_fade": {"enabled": False},
                  "fill_model": "legacy"}
    tape_cfg = {"time_stop": {"enabled": False}, "signal_fade": {"enabled": False},
                "fill_model": "tape_replay", "tape_window_seconds": args.window,
                "tape_participation": args.participation}

    print(f"lake={lake_root} feed={args.feed} symbols={symbols} sessions={args.sessions} "
          f"notional=${args.notional:.0f} stop={args.stop_pct:.1%} target={args.target_pct:.1%}")

    rows = []
    for sym in symbols:
        for session in _sessions_for(store, sym, args.feed, args.sessions):
            open_et = pd.Timestamp(_dt.datetime.combine(session, _dt.time(9, 35)), tz="America/New_York")
            close_et = pd.Timestamp(_dt.datetime.combine(session, _dt.time(15, 59)), tz="America/New_York")
            mb = store.minute_bars(sym, open_et.tz_convert("UTC"), close_et.tz_convert("UTC"), feed=args.feed)
            if mb is None or mb.empty:
                continue
            mb = mb.sort_values("timestamp").reset_index(drop=True)
            n = len(mb)
            # entry minutes spread across the first ~half of the session (so there
            # is forward path left to hit a bracket).
            ent_idx = np.linspace(5, max(5, n // 2), min(args.entries_per_session, max(1, n // 4))).astype(int)
            for ei in sorted(set(int(x) for x in ent_idx if x < n)):
                ebar = mb.iloc[ei]
                entry = float(ebar.get("close", ebar.get("Close", 0.0)) or 0.0)
                if entry <= 0:
                    continue
                ets = pd.Timestamp(ebar["timestamp"])
                ets = ets.tz_localize("UTC") if ets.tzinfo is None else ets.tz_convert("UTC")
                qty = int(args.notional / entry)
                if qty <= 0:
                    continue
                fwd = mb.iloc[ei + 1:].reset_index(drop=True)
                if fwd.empty:
                    continue

                def _lot():
                    return Position(
                        symbol=sym, entry_date=session, entry_price=entry, qty=qty,
                        stop_pct=args.stop_pct, target_pct=args.target_pct, max_hold_days=1,
                        entry_session=session, entry_timestamp=ets.isoformat(),
                        stop_price=entry * (1 - args.stop_pct),
                        target_price=entry * (1 + args.target_pct),
                    )

                ev_l = walk_lot_exit(_lot(), fwd, exit_cfg=legacy_cfg, cost_stress="base")
                ev_t = walk_lot_exit(_lot(), fwd, exit_cfg=tape_cfg, cost_stress="base",
                                     trades_supplier=trades_supplier)
                if ev_l is None or ev_t is None:
                    continue
                pnl_l = (ev_l.exit_price - entry) * qty
                pnl_t = (ev_t.exit_price - entry) * qty
                rows.append({
                    "symbol": sym, "entry_ts": ets, "entry": entry, "qty": qty,
                    "reason_l": ev_l.exit_reason, "reason_t": ev_t.exit_reason,
                    "px_l": ev_l.exit_price, "px_t": ev_t.exit_price,
                    "pnl_l": pnl_l, "pnl_t": pnl_t, "pnl_delta": pnl_t - pnl_l,
                    "bracket": ev_l.exit_reason in ("stop", "target", "gap_stop", "gap_target"),
                })

    if not rows:
        print("NO lots walked to an exit. Widen --sessions / --entries-per-session.")
        return 2
    df = pd.DataFrame(rows)
    nb = int(df["bracket"].sum())
    tot_l, tot_t = df["pnl_l"].sum(), df["pnl_t"].sum()
    br = df[df["bracket"]]
    print("\n" + "=" * 72)
    print(f"PC.3 EXIT-FILL PnL  (N={len(df)} lots; {nb} hit a stop/target bracket)")
    print("=" * 72)
    print(f"  total realized PnL  legacy = ${tot_l:,.2f}")
    print(f"  total realized PnL  tape   = ${tot_t:,.2f}")
    print(f"  delta (tape - legacy)      = ${tot_t - tot_l:,.2f}  "
          f"({100.0*(tot_t-tot_l)/abs(tot_l) if tot_l else 0:+.2f}% of |legacy|)")
    if not br.empty:
        print("-" * 72)
        print(f"  bracket-only lots (where the fill model bites): N={len(br)}")
        print(f"    legacy PnL = ${br['pnl_l'].sum():,.2f}   tape PnL = ${br['pnl_t'].sum():,.2f}   "
              f"delta = ${br['pnl_delta'].sum():,.2f}")
        print(f"    per-lot exit give-up (tape vs legacy): "
              f"median=${br['pnl_delta'].median():.2f}  mean=${br['pnl_delta'].mean():.2f}")
    print("=" * 72)
    worse = int((df["pnl_t"] < df["pnl_l"] - 1e-9).sum())
    better = int((df["pnl_t"] > df["pnl_l"] + 1e-9).sum())
    print(f"  lots where tape PnL < legacy: {worse}   tape PnL > legacy: {better}   equal: {len(df)-worse-better}")
    print("  Expectation: tape ≤ legacy (honest exits give up the spread/impact; a")
    print("  legacy bracket fill at the exact stop/target is unrealistically generous).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
