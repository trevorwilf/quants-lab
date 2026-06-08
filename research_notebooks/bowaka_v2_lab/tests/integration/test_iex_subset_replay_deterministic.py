"""Realism remediation 2 Phase 3 — deterministic IEX-subset replay (§P0-003).

Replays the committed real-IEX subset against the multi-level DQ stack and
byte-compares the normalised result against an ``approved/`` baseline. The
committed parquet payloads + the fixed run config + the normalisation
(:func:`tests.fixtures.iex_subset_replay_snapshot.normalise_report`) together
guarantee determinism — two CI runs against the same committed subset produce
the same snapshot. A future phase that legitimately changes the DQ surface
must re-approve the baseline via the snapshot script.

GOLDEN CHANGELOG — ``approved/dq_report_snapshot.json`` re-approval:
  * §6.6 denominator fix (commit f160ee2) added the ``eligible_expected`` /
    ``eligible_missing`` / ``eligible_fraction`` / ``gated`` evidence keys to
    ``coverage_missing`` (and ``eligible_probes`` / ``eligible_*`` / ``gated`` to
    the two replay coverage checks) but the snapshot was never re-approved — the
    baseline byte-comparison had been silently red.
  * Audit 2026-06-07 §10c (Fix A/B/C) is byte-identical on this ungated
    (``eligible_per_session is None``) replay: the Fix-A telemetry keys
    (``dropped_flat_session_pairs`` / ``minute_leg_criterion``) and the Fix-B
    ``coverage_backfill_present`` check are emitted ONLY on the gated path, so the
    legacy snapshot surface is unchanged by §10c. The re-approval here merely
    captures the long-standing §6.6 ``eligible_*`` keys.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.fixtures.iex_subset_replay_snapshot import build_snapshot
from tests.fixtures.loader import committed_subset_available, load_iex_subset

_LAB_ROOT = Path(__file__).resolve().parents[2]
_APPROVED = _LAB_ROOT / "tests" / "fixtures" / "iex_subset_replay" / "approved" / "dq_report_snapshot.json"


def test_approved_baseline_is_committed() -> None:
    """The approved baseline must be committed in-repo."""
    assert _APPROVED.is_file(), (
        f"approved baseline not committed at {_APPROVED}; regenerate with "
        "tests/fixtures/iex_subset_replay_snapshot.py"
    )


@pytest.mark.skipif(
    not committed_subset_available(),
    reason="committed IEX subset absent — run tests/fixtures/build_iex_subset.py",
)
def test_iex_subset_replay_matches_approved_snapshot() -> None:
    """A fresh DQ replay of the committed subset matches the approved baseline byte-for-byte."""
    subset = load_iex_subset(lake_source="committed")
    if subset.synthetic_fallback:
        pytest.skip(
            "real-IEX subset unavailable; deterministic replay requires the real "
            "committed subset (not the synthetic fallback)"
        )
    fresh = build_snapshot()
    approved = json.loads(_APPROVED.read_text(encoding="utf-8"))
    # Compare the JSON-canonical forms (sorted keys + no incidental whitespace)
    # so a key-order difference can never mask a real diff.
    fresh_canonical = json.dumps(fresh, indent=2, sort_keys=True, default=str)
    approved_canonical = json.dumps(approved, indent=2, sort_keys=True, default=str)
    if fresh_canonical != approved_canonical:
        # Make the diff trivially readable.
        import difflib

        diff = "\n".join(
            difflib.unified_diff(
                approved_canonical.splitlines(),
                fresh_canonical.splitlines(),
                fromfile="approved/dq_report_snapshot.json",
                tofile="fresh_snapshot",
                lineterm="",
            )
        )
        raise AssertionError(
            "IEX subset replay snapshot differs from the approved baseline.\n"
            "If this change is intentional, re-approve by running:\n"
            "  python tests/fixtures/iex_subset_replay_snapshot.py\n\n"
            f"Diff:\n{diff}"
        )


def test_replay_snapshot_check_set_is_complete() -> None:
    """The committed snapshot must carry every multi-level DQ check name.

    A regression that drops a level (e.g. an exception swallowed silently)
    would shrink the check set; pinning the expected name set catches it.
    """
    approved = json.loads(_APPROVED.read_text(encoding="utf-8"))
    names = {c["name"] for c in approved["checks"]}
    must_have = {
        # Ingestion level.
        "ingestion_schema",
        "ingestion_timestamps_sorted",
        "ingestion_duplicate_timestamps",
        "ingestion_ohlc_violation",
        "ingestion_nonpositive_price",
        "ingestion_volume_anomaly",
        # Session level.
        "session_minute_count_violation",
        "intraday_gap",
        "session_stale_segment",
        # Replay level.
        "coverage_missing_late_session",
        "coverage_missing_exit_path",
        "replay_quote_age_violation",
        # Feature level.
        "feature_leakage",
        "feature_split_unaware",
        # Quote/status level.
        "quote_age_distribution",
        "quote_spread_distribution",
        "halt_data_unavailable_when_required",
        # Pre-existing checks (must still be present).
        "coverage_missing",
        "adjustment_mismatch",
        "split_adjustment_mismatch",
        "quotes_partitions_available",
    }
    missing = must_have - names
    assert not missing, f"approved snapshot is missing checks: {sorted(missing)}"
