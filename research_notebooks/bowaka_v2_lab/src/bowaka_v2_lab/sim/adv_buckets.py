"""ADV (average daily volume) buckets for partial-fill modelling.

Audit 2026-05-29 §8.5 — partial fills are far more aggressive in low-ADV
microcaps than in large caps. The Bowaka strategy already filters to an
``adv_dollar_min`` floor; the buckets below sit on top of that floor and let
the stress matrix apply tighter caps to the bottom bucket without penalising
the more-liquid bucket.

PARITY ANCHOR — the ``base`` cap is ``1.0`` for EVERY bucket so that an
unstressed backtest (``cost_stress="base"``) is byte-identical whether or not
the ADV-bucket path is engaged. This is required by the Phase 1 base-point
parity test: the matrix's ``(slippage_bps_offset=0, spread_multiplier=1.0,
cost_stress="base")`` point must reproduce the unstressed fold metrics within
``1e-12``. Stress tightening therefore lives entirely in the ``conservative``
and ``severe`` tiers, where the bottom (``micro``) bucket is squeezed hardest.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdvBucket:
    name: str
    adv_dollar_min: float
    adv_dollar_max: float
    partial_fill_cap_base: float          # fraction of bucket-level liquidity
    partial_fill_cap_conservative: float
    partial_fill_cap_severe: float


#: base == 1.0 for every bucket (parity anchor); conservative/severe tighten,
#: most aggressively for the least-liquid (``micro``) bucket.
ADV_BUCKETS: tuple[AdvBucket, ...] = (
    AdvBucket("micro",  2.5e5, 1.0e6,        1.00, 0.25, 0.10),
    AdvBucket("small",  1.0e6, 5.0e6,        1.00, 0.50, 0.25),
    AdvBucket("mid",    5.0e6, 5.0e7,        1.00, 0.75, 0.50),
    AdvBucket("large",  5.0e7, float("inf"), 1.00, 0.90, 0.75),
)


def bucket_for_adv(adv_dollar: float) -> AdvBucket:
    """Return the bucket containing ``adv_dollar``.

    Below-floor ADV defaults to the most-liquid bucket: sizing has already
    filtered out below-floor names, so a stray below-floor value should not be
    penalised here.
    """
    adv = float(adv_dollar)
    for b in ADV_BUCKETS:
        if b.adv_dollar_min <= adv < b.adv_dollar_max:
            return b
    return ADV_BUCKETS[-1]


def fill_cap_for(adv_dollar: float, cost_stress: str) -> float:
    """ADV-bucket partial-fill cap for ``(adv_dollar, cost_stress)``."""
    b = bucket_for_adv(adv_dollar)
    return {
        "base":         b.partial_fill_cap_base,
        "conservative": b.partial_fill_cap_conservative,
        "severe":       b.partial_fill_cap_severe,
    }.get(str(cost_stress), b.partial_fill_cap_conservative)
