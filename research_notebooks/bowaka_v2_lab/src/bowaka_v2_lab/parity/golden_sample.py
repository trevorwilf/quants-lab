"""Fixed sample + window for the Phase 0 golden parity baseline and the
per-phase golden-diff gate.

Operator-chosen, strategy-relevant symbols: real $1-20 microcaps the bowaka
equity screen admits over the window, so the golden carries real signals +
trades rather than a dead universe.

SIP rebase (P0, 2026-06-13): the lake went SIP-only at the 2026-06-04 cutover,
so the prior IEX symbols/window (2026-05-19..22) produced an EMPTY universe
(feed=iex finds no partitions) and a vacuous 0-trade golden. This sample is
chosen on the SIP lake: the 2025-08-20..25 window has full daily history (SIP
daily goes back to 2024-01) and is a verified trade-producing window for the
current-code (#3155) config. The golden's lab side now runs
``configs/bowaka_v2_actual_sip_current_code.yml`` (feed=sip, current_code_parity)
to match the prod config (feed=sip). All symbols are real tickers present in the
SIP 1m + 1d lake. Shared by ``scripts/phase0_capture_golden.py`` (reference) and
``scripts/verify_golden_diff.py`` (verification) so the two never drift.
"""
from __future__ import annotations

import datetime as _dt

GOLDEN_SYMBOLS: tuple[str, ...] = (
    "AMPX", "ARRY", "ATAI", "ATYR", "CIFR", "CLSK", "CRMD", "EOSE", "FLNC",
    "GDRX", "HIVE", "HTZ", "IBRX", "IREN", "JMIA", "KEEL", "KSS", "LAC",
    "ONDS", "OPEN", "OSCR", "PGEN", "PLUG", "QS", "RCAT", "REAL", "RGTI",
    "RIOT", "RR", "RZLV", "SERV", "SGML", "SHLS", "SLDP", "SOUN", "TMC",
)
GOLDEN_START = _dt.date(2025, 8, 20)
GOLDEN_END = _dt.date(2025, 8, 25)    # 4 XNYS sessions: 08-20,21,22,25
GOLDEN_COST_STRESS = "base"           # fixed across the golden + all phase gates

__all__ = ["GOLDEN_SYMBOLS", "GOLDEN_START", "GOLDEN_END", "GOLDEN_COST_STRESS"]
