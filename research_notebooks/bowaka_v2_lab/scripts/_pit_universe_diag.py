#!/usr/bin/env python
"""Diagnostic — why does the PIT universe screen to EMPTY on a scoped window?

Builds the point-in-time universe for one session via the real screening path
(:func:`universe.builder.build_pit_universe`) and prints the rejection-reason
histogram across ALL asset-master symbols, so we can see which of the 7 screens
(exchange / otc / instrument-class / blocklist / price / ADV / delisted) zeroed
it out. Read-only. Runs the same probe under current_code_parity and
intended_realism so the unknown-instrument-class policy effect is visible.

Usage (ql-jupyter container):
  PYTHONPATH=research_notebooks/bowaka_v2_lab/src:research_notebooks/bowaka_common/src \
    python research_notebooks/bowaka_v2_lab/scripts/_pit_universe_diag.py \
    --lake-root /opt/market_data_cache --feed sip --session 2025-09-03 --adv 250000
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
from collections import Counter
from pathlib import Path


def _bootstrap() -> None:
    repo = Path(__file__).resolve().parents[3]
    for sub in ("research_notebooks/bowaka_v2_lab/src", "research_notebooks/bowaka_common/src"):
        p = str(repo / sub)
        if p not in sys.path:
            sys.path.insert(0, p)


_bootstrap()

from bowaka_common.marketdata import MarketDataStore  # noqa: E402
from bowaka_v2_lab.universe.builder import build_pit_universe, eligible_symbols  # noqa: E402


def _cfg(mode: str, feed: str, adv: float, pmin: float, pmax: float) -> dict:
    return {
        "simulation": {"mode": mode},
        "market_data": {"feed": feed, "daily_bar_source": "alpaca", "vendor": "alpaca"},
        "universe": {
            "min_price": pmin, "max_price": pmax,
            "min_adv_dollars": adv, "avg_dollar_volume_min": adv,
            "asset_classes": ["operating_equity"], "exclude_pattern_class": False,
        },
    }


def _probe(store, session, mode, feed, adv, pmin, pmax) -> None:
    cfg = _cfg(mode, feed, adv, pmin, pmax)
    recs = build_pit_universe(session, cfg, store)
    n_total = len(recs)
    elig = eligible_symbols(recs)
    # Histogram of every applied rejection reason (a symbol can have several).
    reason_hist = Counter()
    # How many symbols are rejected ONLY by reason R (R is the sole blocker)?
    sole_blocker = Counter()
    n_no_baseline = 0
    for r in recs.values():
        rs = list(r.rejection_reasons)
        for reason in rs:
            reason_hist[reason] += 1
        if len(rs) == 1:
            sole_blocker[rs[0]] += 1
        if r.prior_close is None:
            n_no_baseline += 1
    print(f"\n=== mode={mode} feed={feed} adv=${adv:,.0f} price=[{pmin},{pmax}] session={session} ===")
    print(f"  asset-master symbols          : {n_total}")
    print(f"  ELIGIBLE (no rejections)      : {len(elig)}")
    print(f"  symbols with NO prior baseline: {n_no_baseline}  (prior_close is None)")
    print(f"  rejection reasons (count of symbols hitting each):")
    for reason, c in reason_hist.most_common():
        print(f"      {reason:32s} {c:6d}   (sole blocker for {sole_blocker.get(reason,0)})")
    if elig:
        print(f"  sample eligible: {elig[:8]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lake-root", default="/opt/market_data_cache")
    ap.add_argument("--feed", default="sip")
    ap.add_argument("--session", default="2025-09-03")
    ap.add_argument("--adv", type=float, default=250000.0)
    ap.add_argument("--price-min", type=float, default=1.0)
    ap.add_argument("--price-max", type=float, default=1000.0)
    args = ap.parse_args()

    store = MarketDataStore(Path(args.lake_root), vendor="alpaca")
    session = _dt.date.fromisoformat(args.session)

    # Probe the two contracts (unknown-instrument-class policy differs) + a
    # no-ADV-floor variant to isolate the ADV/baseline screen.
    _probe(store, session, "current_code_parity", args.feed, args.adv, args.price_min, args.price_max)
    _probe(store, session, "intended_realism", args.feed, args.adv, args.price_min, args.price_max)
    _probe(store, session, "current_code_parity", args.feed, 0.0, args.price_min, args.price_max)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
