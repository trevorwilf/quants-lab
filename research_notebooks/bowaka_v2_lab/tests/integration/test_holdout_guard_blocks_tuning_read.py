"""Phase 3 (audit 2026-05-29 §9 Phase 5) — the tuning-phase lock blocks a
holdout-overlapping MarketDataStore read.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from bowaka_common.marketdata.store import MarketDataStore
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuardError, tuning_phase_lock


def test_lock_blocks_holdout_read_and_releases(tmp_path: Path) -> None:
    store = MarketDataStore(root=str(tmp_path))  # empty lake — lock checks the range first
    hs, he = dt.date(2024, 9, 1), dt.date(2024, 10, 1)

    with tuning_phase_lock(hs, he):
        with pytest.raises(HoldoutGuardError):
            store.daily_bars("AAA", hs, he)        # overlaps the holdout window
        # a pre-holdout read is NOT blocked by the lock (may fail on empty data,
        # but never with HoldoutGuardError).
        try:
            store.daily_bars("AAA", dt.date(2024, 1, 1), dt.date(2024, 2, 1))
        except HoldoutGuardError:
            pytest.fail("a non-overlapping read must not be blocked")
        except Exception:
            pass

    # After exit the wrappers are uninstalled — the holdout read no longer raises
    # HoldoutGuardError (the finalist-evaluation step is then free to read it).
    try:
        store.daily_bars("AAA", hs, he)
    except HoldoutGuardError:
        pytest.fail("tuning_phase_lock did not release on exit")
    except Exception:
        pass
