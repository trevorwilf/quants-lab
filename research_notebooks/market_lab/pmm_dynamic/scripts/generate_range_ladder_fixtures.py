"""Generate frozen parity fixtures for the range_ladder fill kernel.

Follows the generate_numba_parity_fixtures.py pattern: synthetic OHLC walks
are pure code-equivalence inputs (not market realism); the PURE-PYTHON
reference implementation is the golden path. The parity test asserts both
the reference AND the numba kernel reproduce these outputs bit-for-bit.

Grid: 3 sizes × 4 configs —
  cfg0: symmetric 5×5, k>0 front-loaded tilt, base dials
  cfg1: asymmetric 3 buys / 9 sells, k<0 deep tilt
  cfg2: cash-starved (quote_frac=0.05) 5×5 — exercises skipped buys
  cfg3: stress dials (max_fills_per_bar=1, cooldown, slip, body_only)

Run once and commit fixtures/:
    python scripts/generate_range_ladder_fixtures.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pmm_lab.features._numba_range_ladder import (  # noqa: E402
    UNBOUNDED_FILLS,
    _run_ladder_reference,
)
from pmm_lab.strategies.range_ladder_gen import build_rungs  # noqa: E402

OUT_DIR = ROOT / "fixtures" / "numba_parity"

SIZES = [("small", 400), ("medium", 2000), ("large", 8000)]

CONFIGS = [
    dict(
        name="cfg0",
        gen=dict(n_buy=5, n_sell=5, buy_near_pct=0.02, buy_far_pct=0.20,
                 sell_near_pct=0.02, sell_far_pct=0.20, buy_gamma=1.0,
                 sell_gamma=1.0, k_buy=1.5, k_sell=1.5, min_weight_frac=0.10),
        dials=dict(fund=1000.0, quote_frac=0.5, fee=0.002, slip=0.0,
                   max_fills_per_bar=0, cooldown_bars=1, body_only=False),
    ),
    dict(
        name="cfg1",
        gen=dict(n_buy=3, n_sell=9, buy_near_pct=0.03, buy_far_pct=0.25,
                 sell_near_pct=0.015, sell_far_pct=0.35, buy_gamma=0.7,
                 sell_gamma=1.6, k_buy=-1.5, k_sell=-0.8, min_weight_frac=0.10),
        dials=dict(fund=1000.0, quote_frac=0.5, fee=0.0025, slip=0.0,
                   max_fills_per_bar=0, cooldown_bars=0, body_only=False),
    ),
    dict(
        name="cfg2",
        gen=dict(n_buy=5, n_sell=5, buy_near_pct=0.01, buy_far_pct=0.15,
                 sell_near_pct=0.01, sell_far_pct=0.15, buy_gamma=1.2,
                 sell_gamma=0.8, k_buy=2.5, k_sell=0.5, min_weight_frac=0.10),
        dials=dict(fund=1000.0, quote_frac=0.05, fee=0.002, slip=0.0,
                   max_fills_per_bar=0, cooldown_bars=1, body_only=False),
    ),
    dict(
        name="cfg3",
        gen=dict(n_buy=6, n_sell=4, buy_near_pct=0.02, buy_far_pct=0.18,
                 sell_near_pct=0.025, sell_far_pct=0.22, buy_gamma=1.0,
                 sell_gamma=1.0, k_buy=0.0, k_sell=3.0, min_weight_frac=0.10),
        dials=dict(fund=1000.0, quote_frac=0.5, fee=0.002, slip=0.001,
                   max_fills_per_bar=1, cooldown_bars=2, body_only=True),
    ),
]

PRICE_TICK = 0.0001


def _make_ohlc(n: int, seed: int):
    """Volatile pseudo-random walk (pure code-equivalence input)."""
    rng = np.random.default_rng(seed)
    lc = np.cumsum(rng.normal(0.0, 0.03, n)) + math.log(50.0)
    c = np.exp(lc)
    o = np.roll(c, 1)
    o[0] = c[0]
    spread = np.abs(rng.normal(0.0, 0.02, n))
    h = np.maximum(o, c) * (1.0 + spread)
    l = np.minimum(o, c) * (1.0 - spread)
    return o, h, l, c


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n_written = 0
    for size_name, n_bars in SIZES:
        for cfg_idx, cfg in enumerate(CONFIGS):
            seed = 4200 + 10 * cfg_idx
            o, h, l, c = _make_ohlc(n_bars, seed)
            anchor = float(np.median(c[: max(3, n_bars // 10)]))
            rungs = build_rungs(anchor, cfg["gen"], PRICE_TICK)

            d = cfg["dials"]
            mfpb = UNBOUNDED_FILLS if d["max_fills_per_bar"] == 0 else np.int64(d["max_fills_per_bar"])
            quote, base, fees, bf, sf, cb, cs, eq, pb = _run_ladder_reference(
                o, h, l, c,
                rungs.buys, rungs.sells, rungs.buy_weights, rungs.sell_weights,
                float(d["fund"]), float(d["quote_frac"]), float(d["fee"]),
                float(d["slip"]), mfpb, np.int64(d["cooldown_bars"]),
                bool(d["body_only"]),
            )

            name = f"rl_{size_name}_{cfg['name']}"
            np.savez(
                OUT_DIR / f"{name}.npz",
                o=o, h=h, l=l, c=c,
                buys=rungs.buys, sells=rungs.sells,
                bw=rungs.buy_weights, sw=rungs.sell_weights,
                quote=np.float64(quote), base=np.float64(base),
                fees=np.float64(fees),
                bf=np.asarray(bf, dtype=np.int64),
                sf=np.asarray(sf, dtype=np.int64),
                cb=np.asarray(cb, dtype=np.int64),
                cs=np.asarray(cs, dtype=np.int64),
                eq=np.asarray(eq, dtype=np.float64),
                pb=np.asarray(pb, dtype=np.float64),
            )
            meta = dict(
                type="range_ladder", size=size_name, n_bars=n_bars, seed=seed,
                anchor=anchor, price_tick=PRICE_TICK,
                gen=cfg["gen"], dials=cfg["dials"],
                golden_source="_run_ladder_reference (pure Python)",
            )
            with open(OUT_DIR / f"{name}.json", "w") as f:
                json.dump(meta, f, indent=2)
            total_fills = int(np.sum(bf) + np.sum(sf))
            print(f"{name}: {n_bars} bars, fills={total_fills}, "
                  f"final_eq={eq[-1]:.4f}, fees={fees:.4f}")
            n_written += 1
    print(f"\nWrote {n_written} fixtures to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
