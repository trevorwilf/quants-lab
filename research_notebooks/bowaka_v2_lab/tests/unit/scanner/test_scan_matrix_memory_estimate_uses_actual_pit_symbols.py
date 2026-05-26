"""Memory estimator uses the actual PIT eligible-symbol count.

Speedup report v2 §4 P6 / Phase 6 task 1. The pre-remediation
estimator hard-coded ``n_symbols=100``, producing a ~7× understatement
on a representative IEX session (~704 eligible on 2025-08-27). Phase 6
swaps in the actual point-in-time eligible-symbol counts.
"""
from __future__ import annotations

import datetime as dt

from bowaka_v2_lab.scanner.scan_matrix import _estimate_matrix_size_gib


def test_estimator_uses_max_eligible_count_when_pit_map_is_supplied() -> None:
    eligible = {
        dt.date(2025, 1, 2): tuple(f"S{i}" for i in range(50)),
        dt.date(2025, 1, 3): tuple(f"S{i}" for i in range(80)),
        dt.date(2025, 1, 4): tuple(f"S{i}" for i in range(200)),
    }
    big = _estimate_matrix_size_gib(
        n_sessions=3, n_scans_per_session=24, n_symbols=100,
        eligible_symbols_by_session=eligible,
    )
    small = _estimate_matrix_size_gib(
        n_sessions=3, n_scans_per_session=24, n_symbols=100,
        eligible_symbols_by_session=None,
    )
    # The PIT-aware estimate must use max(eligible)=200 instead of 100.
    assert big > small, (
        f"PIT-aware estimate {big!r} not greater than legacy {small!r}; "
        "the max-of-eligible-counts override did not kick in"
    )


def test_estimator_legacy_path_unchanged_for_n_symbols_100() -> None:
    """Without ``eligible_symbols_by_session`` the legacy formula holds."""
    legacy = _estimate_matrix_size_gib(
        n_sessions=10, n_scans_per_session=24, n_symbols=100,
    )
    legacy_explicit_none = _estimate_matrix_size_gib(
        n_sessions=10, n_scans_per_session=24, n_symbols=100,
        eligible_symbols_by_session=None,
    )
    assert legacy == legacy_explicit_none


def test_estimator_pit_override_only_increases_size() -> None:
    """When PIT counts are smaller than ``n_symbols`` the estimator keeps
    the conservative legacy fallback."""
    eligible = {
        dt.date(2025, 1, 2): tuple(f"S{i}" for i in range(20)),
    }
    out = _estimate_matrix_size_gib(
        n_sessions=1, n_scans_per_session=24, n_symbols=100,
        eligible_symbols_by_session=eligible,
    )
    legacy = _estimate_matrix_size_gib(
        n_sessions=1, n_scans_per_session=24, n_symbols=100,
    )
    assert out == legacy


def test_estimator_700_symbols_produces_7x_legacy_estimate() -> None:
    """The 7× understatement the prompt calls out."""
    eligible = {
        dt.date(2025, 1, 2): tuple(f"S{i}" for i in range(700)),
    }
    big = _estimate_matrix_size_gib(
        n_sessions=10, n_scans_per_session=24, n_symbols=100,
        eligible_symbols_by_session=eligible,
    )
    legacy = _estimate_matrix_size_gib(
        n_sessions=10, n_scans_per_session=24, n_symbols=100,
    )
    ratio = big / legacy
    assert ratio >= 6.0, (
        f"PIT/legacy ratio {ratio:.2f} below expected 7× for 700 eligible"
    )
