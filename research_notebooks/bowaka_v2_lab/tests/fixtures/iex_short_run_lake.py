"""Phase 3 (audit 2026-05-29 §10.1 / §A.9 / §11 / Appendix D.2) — IEX short-run lake.

A small but real IEX-shaped lake for the Notebook 10 short-run papermill test:
split-adjusted daily bars for >= 25 symbols (so the full-fold preflight's PIT
floor is satisfied) across the audit's 2024-11 / 2025-08 windows, minute bars
covering the validation sessions, an asset master, and a split_adjusted
ingestion manifest. No quotes (the current-code-parity warn-only path).
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

from tests.fixtures.adjustment_lake import build_lake

#: 30 synthetic symbols — comfortably above DEFAULT_MIN_PIT_UNIVERSE_PER_FOLD (25).
SHORT_RUN_SYMBOLS: tuple[str, ...] = tuple(f"SR{i:02d}" for i in range(30))


def build_iex_short_run_lake(root: Path) -> Path:
    """Build the IEX short-run lake under ``root`` and return ``root``."""
    build_lake(
        root, SHORT_RUN_SYMBOLS,
        daily_start=_dt.date(2024, 9, 1), daily_end=_dt.date(2025, 9, 30),
        # minute coverage for the validation + holdout months the short run probes
        minute_months=[(2024, 11), (2024, 12), (2025, 8), (2025, 9)],
        feed="iex", adjustment="split_adjusted", close=10.0,
        manifest_adjustment="split_adjusted",
    )
    return root
