"""Enforced real-data test lane (P2 / §6).

A real-lake / real-tape test calls :func:`require_real_lake` /
:func:`require_real_tape`. On a machine that DECLARES the lane active (env
``BOWAKA_REAL_DATA_LANE``) a missing lake/tape **fails** the test rather than
skipping it — so the decisive realism/parity gates can never silently no-op on a
machine that claims to have the data. On an ordinary host (lane not declared) a
missing lake skips, exactly as before.

Run the lane in the ql-jupyter container::

    MARKET_DATA_ROOT=/opt/market_data_cache BOWAKA_REAL_DATA_LANE=1 \
      PYTHONPATH=src:../bowaka_common/src \
      /opt/conda/envs/quants-lab/bin/python -m pytest -m real_data
"""
from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path

import pytest

REAL_DATA_LANE_ENV = "BOWAKA_REAL_DATA_LANE"


def real_data_lane_declared() -> bool:
    """True when the operator declares the real-data lake/tape is present."""
    return os.environ.get(REAL_DATA_LANE_ENV, "").strip().lower() not in ("", "0", "false", "no")


def _miss(reason: str):
    """Fail when the lane is declared (data should be here), else skip."""
    if real_data_lane_declared():
        pytest.fail(
            f"[real-data lane] {reason}. The lane is declared active "
            f"(${REAL_DATA_LANE_ENV}) but the data is absent — provide the "
            f"lake/tape or unset {REAL_DATA_LANE_ENV}."
        )
    pytest.skip(f"{reason} (real-data lane not declared; set ${REAL_DATA_LANE_ENV} to enforce)")


def require_real_lake(probe_symbol: str = "IREN", *, feed: str = "sip") -> Path:
    """Resolve the real market-data lake root or skip/fail per the lane policy.

    Probes a known-present SIP microcap's daily bars (the SIP lake universe
    excludes mega-caps, so AAPL is not a reliable probe).
    """
    try:
        from bowaka_common.marketdata import MarketDataStore
        from bowaka_common.marketdata.store import resolve_market_data_root
    except Exception as exc:  # noqa: BLE001
        _miss(f"bowaka_common not importable: {exc}")
    lake_root = resolve_market_data_root(None, create=False)
    present = False
    try:
        store = MarketDataStore(lake_root, vendor="alpaca")
        db = store.daily_bars(
            probe_symbol, _dt.date(2025, 8, 1), _dt.date(2025, 8, 31),
            feed=feed, adjustment="split_adjusted",
        )
        present = db is not None and len(db) > 0
    except Exception:  # noqa: BLE001
        present = False
    if not present:
        _miss(f"real {feed} lake not present at {lake_root} ({probe_symbol} has no daily bars)")
    return Path(lake_root)


def require_real_tape(probe_symbol: str = "IREN", *, feed: str = "sip") -> Path:
    """Resolve the real lake AND require the trades tape for ``probe_symbol``."""
    lake_root = require_real_lake(probe_symbol, feed=feed)
    tape_dir = (
        lake_root / "trades" / "vendor=alpaca" / f"feed={feed}" / f"symbol={probe_symbol}"
    )
    if not tape_dir.is_dir() or not any(tape_dir.rglob("*.parquet")):
        _miss(f"real trades tape absent for {probe_symbol} under {tape_dir}")
    return lake_root
