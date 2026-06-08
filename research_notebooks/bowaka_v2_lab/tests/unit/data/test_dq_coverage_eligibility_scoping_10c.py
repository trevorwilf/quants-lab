"""Audit 2026-06-07 §10c — coverage-eligibility scoping fixes (A / B / C).

Fix A  ``build_coverage_check``: sim-faithful any-regular-session-bar minute
       criterion + flat-session denominator drop (gated only).
Fix B  ``build_backfill_presence_check``: strict structural-absence guardrail
       the tolerant coverage gate must not mask.
Fix C  ``build_audit_checks``: per-session-eligibility scoping of
       ``audit_missing_sessions``.

The locked invariant across all three: with ``eligible_per_session is None``
the behaviour is BYTE-IDENTICAL to the pre-§10c (committed) report. The gated
path implements the new semantics.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.data.data_quality import (
    _DQ_CHECK_INVARIANCE,
    _REQUIRED_CHECK_NAMES,
    build_audit_checks,
    build_backfill_presence_check,
    build_coverage_check,
    dq_check_invariance,
)

_S = dt.date(2024, 9, 4)
_DF1 = pd.DataFrame({"x": [1]})


def _scan_grid(d: dt.date) -> list[pd.Timestamp]:
    """A full 60 s regular-session scan grid 09:45 -> 15:30 ET (346 scans)."""
    first = pd.Timestamp(f"{d}T13:45:00", tz="UTC")
    return [first + pd.Timedelta(minutes=k) for k in range(346)]


# ---------------------------------------------------------------------------
# Fix A — coverage_missing
# ---------------------------------------------------------------------------
def test_fixA_legacy_path_byte_identical_evidence_keys() -> None:
    """Ungated (eligible_per_session=None) evidence carries NO §10c telemetry.

    The Fix-A keys (``dropped_flat_session_pairs`` / ``minute_leg_criterion``)
    are emitted ONLY on the gated path, so the legacy evidence dict is exactly
    the committed surface (``expected_pairs`` / ``missing_*`` / ``eligible_*`` /
    ``gated``).
    """
    cov = build_coverage_check(
        requested_symbols=["AAA", "BBB"],
        sessions=[_S],
        daily_bars_supplier=lambda s, d: _DF1,
        minute_bars_supplier=lambda s, t: None,  # both miss the first-scan probe
        scan_times_per_session=_scan_grid,
    )
    ev = cov["evidence"]
    assert ev["gated"] is False
    assert "dropped_flat_session_pairs" not in ev
    assert "minute_leg_criterion" not in ev
    # Legacy first-scan probe: both symbols miss => eligible mirrors full union.
    assert ev["eligible_expected"] == 2
    assert ev["eligible_missing"] == 2
    assert cov["status"] == "fail"


def test_fixA_gated_drops_genuine_flat_session_from_denominator() -> None:
    """An eligible pair with a daily bar but NO regular-session minute bar is a
    genuine illiquid no-trade session — dropped from the gated denominator."""

    def minute(s, t):
        return _DF1 if s == "BBB" else None  # AAA flat all session

    cov = build_coverage_check(
        requested_symbols=["AAA", "BBB"],
        sessions=[_S],
        daily_bars_supplier=lambda s, d: _DF1,
        minute_bars_supplier=minute,
        scan_times_per_session=_scan_grid,
        eligible_per_session={_S: {"AAA", "BBB"}},
    )
    ev = cov["evidence"]
    assert ev["gated"] is True
    assert ev["minute_leg_criterion"] == "any_regular_session_bar"
    assert ev["dropped_flat_session_pairs"] == 1  # AAA dropped
    assert ev["eligible_expected"] == 1  # only BBB remains in denominator
    assert ev["eligible_missing"] == 0
    assert cov["status"] == "pass"


def test_fixA_gated_daily_gap_still_counts_as_a_miss() -> None:
    """day_ok=False is a real daily-leg gap — it stays in the gated denominator
    and counts as a gated miss (it is NOT a flat-session drop)."""

    def daily(s, d):
        return None if s == "AAA" else _DF1

    cov = build_coverage_check(
        requested_symbols=["AAA", "BBB"],
        sessions=[_S],
        daily_bars_supplier=daily,
        minute_bars_supplier=lambda s, t: None,  # no minute anywhere
        scan_times_per_session=_scan_grid,
        eligible_per_session={_S: {"AAA", "BBB"}},
    )
    ev = cov["evidence"]
    # AAA: daily gap -> counted + missed. BBB: daily ok, no minute -> flat drop.
    assert ev["dropped_flat_session_pairs"] == 1  # BBB dropped
    assert ev["eligible_expected"] == 1  # AAA only
    assert ev["eligible_missing"] == 1
    assert cov["status"] == "fail"  # 1/1 >= 1%


def test_fixA_gated_any_session_bar_passes_when_first_scan_empty_but_later_present() -> None:
    """The any-regular-session-bar criterion: the supplier window
    [09:45, scan_times[-1]] is non-empty even if the 09:45 bar is absent, so the
    pair is simulable and NOT dropped."""

    def minute(s, cutoff):
        # Non-empty for the last-scan window (covers the whole session); the
        # supplier is only ever called at scan_times[-1] on the gated path.
        return _DF1

    cov = build_coverage_check(
        requested_symbols=["AAA"],
        sessions=[_S],
        daily_bars_supplier=lambda s, d: _DF1,
        minute_bars_supplier=minute,
        scan_times_per_session=_scan_grid,
        eligible_per_session={_S: {"AAA"}},
    )
    ev = cov["evidence"]
    assert ev["dropped_flat_session_pairs"] == 0
    assert ev["eligible_expected"] == 1
    assert ev["eligible_missing"] == 0
    assert cov["status"] == "pass"


# ---------------------------------------------------------------------------
# Fix B — coverage_backfill_present
# ---------------------------------------------------------------------------
def test_fixB_registered_required_and_invariant() -> None:
    assert "coverage_backfill_present" in _REQUIRED_CHECK_NAMES
    assert _DQ_CHECK_INVARIANCE["coverage_backfill_present"] == "invariant"
    assert dq_check_invariance("coverage_backfill_present") == "invariant"


def test_fixB_legacy_is_a_noop_pass() -> None:
    chk = build_backfill_presence_check(
        requested_symbols=["AAA"],
        sessions=[_S],
        eligible_per_session=None,
        lake_root=None,
        feed="iex",
        daily_bars_supplier=lambda s, d: None,
    )
    assert chk["name"] == "coverage_backfill_present"
    assert chk["status"] == "pass"
    assert chk["count"] == 0
    assert chk["evidence"]["gated"] is False


def _write(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _minute_month_df(sym: str) -> pd.DataFrame:
    mts = [pd.Timestamp(f"{_S} 13:45", tz="UTC") + pd.Timedelta(minutes=i) for i in range(10)]
    return pd.DataFrame(
        {
            "symbol": [sym] * len(mts),
            "timestamp": mts,
            "open": [1.0] * len(mts),
            "high": [1.0] * len(mts),
            "low": [1.0] * len(mts),
            "close": [1.0] * len(mts),
            "volume": [100.0] * len(mts),
        }
    )


def test_fixB_passes_when_both_legs_present(tmp_path) -> None:
    root = tmp_path / "lake"
    for sym in ("AAA", "BBB"):
        _write(layout.minute_bars_path(root, sym, _S.year, _S.month, feed="iex"),
                _minute_month_df(sym))
    chk = build_backfill_presence_check(
        requested_symbols=["AAA", "BBB"],
        sessions=[_S],
        eligible_per_session={_S: {"AAA", "BBB"}},
        lake_root=root,
        feed="iex",
        daily_bars_supplier=lambda s, d: _DF1,
    )
    assert chk["status"] == "pass"
    assert chk["evidence"]["expected"] == 2
    assert chk["evidence"]["missing"] == 0


def test_fixB_fails_on_missing_minute_month_catastrophe(tmp_path) -> None:
    """A wholesale missing-month backfill (the catastrophe the tolerant gate must
    not mask): no minute month parquet for any eligible symbol -> fail."""
    root = tmp_path / "lake"  # no minute partitions written at all
    chk = build_backfill_presence_check(
        requested_symbols=["AAA", "BBB", "CCC"],
        sessions=[_S],
        eligible_per_session={_S: {"AAA", "BBB", "CCC"}},
        lake_root=root,
        feed="iex",
        daily_bars_supplier=lambda s, d: _DF1,  # daily leg is fine
    )
    assert chk["status"] == "fail"
    assert chk["evidence"]["expected"] == 3
    assert chk["evidence"]["missing"] == 3
    assert len(chk["evidence"]["missing_minute_month"]) == 3
    assert "structural backfill absence" in chk["evidence"]["detail"]


def test_fixB_fails_on_missing_daily_leg(tmp_path) -> None:
    root = tmp_path / "lake"
    for sym in ("AAA", "BBB"):
        _write(layout.minute_bars_path(root, sym, _S.year, _S.month, feed="iex"),
                _minute_month_df(sym))
    chk = build_backfill_presence_check(
        requested_symbols=["AAA", "BBB"],
        sessions=[_S],
        eligible_per_session={_S: {"AAA", "BBB"}},
        lake_root=root,
        feed="iex",
        daily_bars_supplier=lambda s, d: None,  # daily leg absent for all
    )
    assert chk["status"] == "fail"
    assert chk["evidence"]["missing"] == 2
    assert len(chk["evidence"]["missing_daily"]) == 2


# ---------------------------------------------------------------------------
# Fix C — audit_missing_sessions per-session-eligibility scoping
# ---------------------------------------------------------------------------
def _write_audit(root: Path, *, missing_sessions: int) -> Path:
    audit_dir = layout.ingestion_dir(root) / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    p = audit_dir / "audit_2024-09-01T000000Z_iex.parquet"
    pd.DataFrame(
        [{
            "symbol": "REUSED", "feed": "iex", "timeframe": "1d",
            "missing_sessions": missing_sessions, "duplicate_sessions": 0,
            "ohlc_violations": 0, "zero_volume_sessions": 0, "large_gap_flags": 0,
            "passed_research_audit": True,
        }]
    ).to_parquet(p, index=False)
    return p


def test_fixC_legacy_gates_on_parquet_symbol_level_count(tmp_path) -> None:
    """Without eligibility inputs, the symbol-level parquet count gates (legacy,
    byte-identical: a positive missing_sessions count => fail)."""
    p = _write_audit(tmp_path, missing_sessions=1762)
    checks = build_audit_checks(p, feed="iex", requested_symbols=["REUSED"])
    ms = next(c for c in checks if c["name"] == "audit_missing_sessions")
    assert ms["status"] == "fail"
    assert ms["count"] == 1762
    assert "gated" not in ms["evidence"]  # legacy evidence surface unchanged


def test_fixC_gated_recomputes_over_eligible_windows(tmp_path) -> None:
    """With eligibility + a daily supplier, the gate is the count of eligible
    (sym, session) pairs LACKING a daily bar. All parquet misses are
    pre-first-eligible => the recomputed gate is 0 => PASS, while the parquet
    symbol-level total is retained as telemetry."""
    p = _write_audit(tmp_path, missing_sessions=1762)
    checks = build_audit_checks(
        p,
        feed="iex",
        requested_symbols=["REUSED"],
        sessions=[_S],
        eligible_per_session={_S: {"REUSED"}},
        daily_bars_supplier=lambda s, d: _DF1,  # eligible session HAS a daily bar
    )
    ms = next(c for c in checks if c["name"] == "audit_missing_sessions")
    assert ms["status"] == "pass"
    assert ms["count"] == 0
    assert ms["evidence"]["gated"] is True
    assert ms["evidence"]["lake_audit_missing_sessions"] == 1762  # telemetry
    assert ms["evidence"]["eligible_missing_sessions"] == 0


def test_fixC_gated_fails_when_an_eligible_session_lacks_a_daily_bar(tmp_path) -> None:
    p = _write_audit(tmp_path, missing_sessions=0)
    checks = build_audit_checks(
        p,
        feed="iex",
        requested_symbols=["REUSED"],
        sessions=[_S],
        eligible_per_session={_S: {"REUSED"}},
        daily_bars_supplier=lambda s, d: None,  # eligible session LACKS a daily bar
    )
    ms = next(c for c in checks if c["name"] == "audit_missing_sessions")
    assert ms["status"] == "fail"
    assert ms["count"] == 1
    assert ms["evidence"]["eligible_missing_sessions"] == 1
    assert ms["evidence"]["eligible_missing_examples"] == [f"REUSED@{_S.isoformat()}"]
