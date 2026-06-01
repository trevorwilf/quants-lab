"""Fixed sample + window for the Phase 0 golden parity baseline and the
per-phase golden-diff gate.

Operator-chosen, strategy-relevant symbols: the bowaka equity screen admits
~34-35 of them on each session over the window, so the golden carries real
signals + trades rather than a dead universe. All 40 are present in the IEX
1m + 1d lake. Shared by ``scripts/phase0_capture_golden.py`` (reference) and
``scripts/verify_golden_diff.py`` (verification) so the two never drift.
"""
from __future__ import annotations

import datetime as _dt

GOLDEN_SYMBOLS: tuple[str, ...] = (
    "AGNC", "AIIO", "ALHC", "ALT", "ARVN", "BLMN", "BWIN", "BZ", "CCC", "CERS",
    "DCTH", "EVER", "GDRX", "HOPE", "IFRX", "KPTI", "LFST", "LRMR", "MMED", "MRLN",
    "NTSK", "NUAI", "OFIX", "OPRA", "ORIC", "PACB", "PCT", "PDYN", "PSEC", "PTLO",
    "RMIX", "RUM", "SBGI", "SLDE", "SONO", "TALK", "TWFG", "UPB", "VNDA", "VRDN",
)
GOLDEN_START = _dt.date(2026, 5, 19)
GOLDEN_END = _dt.date(2026, 5, 22)    # 4 XNYS sessions: 05-19..05-22
GOLDEN_COST_STRESS = "base"           # fixed across the golden + all phase gates

__all__ = ["GOLDEN_SYMBOLS", "GOLDEN_START", "GOLDEN_END", "GOLDEN_COST_STRESS"]
