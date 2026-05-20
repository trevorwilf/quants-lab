"""Same inputs fed to the v2 archive's build_candidate_event produce the SAME dict
(modulo schema-fix gate keys added in §8.3) as ours.

The test dynamically imports the archive function from BOWAKA_V2_SOURCE_ROOT.
Skipped when that env var is unset.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pandas as pd
import pytest

from bowaka_v2_lab.scanner.event_builder import build_candidate_event as ported_builder


_ARCHIVE_GATES = {
    "price_gate", "avg_dollar_volume_gate", "rvol_gate", "prior_atr_pct_gate",
    "range_expansion_gate", "close_location_gate", "ema_distance_gate",
    "ema_slope_gate", "max_gap_gate", "instrument_gate",
}


def _load_archive_builder():
    root = os.environ.get("BOWAKA_V2_SOURCE_ROOT")
    if not root:
        pytest.skip("BOWAKA_V2_SOURCE_ROOT not set")
    # Support both layouts:
    #   BOWAKA_V2_SOURCE_ROOT pointing at the archive parent (contains scripts/)
    #   BOWAKA_V2_SOURCE_ROOT pointing directly at the scripts/ directory
    candidates = [
        Path(root) / "scripts" / "bowaka_intraday_scanner.py",
        Path(root) / "bowaka_intraday_scanner.py",
    ]
    scanner_path = next((c for c in candidates if c.is_file()), None)
    if scanner_path is None:
        pytest.skip(f"archive scanner not at any of: {candidates}")
    spec = importlib.util.spec_from_file_location("v2_archive_scanner", scanner_path)
    if spec is None or spec.loader is None:
        pytest.skip("could not build importlib spec")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"archive import failed: {e}")
    if not hasattr(mod, "build_candidate_event"):
        pytest.skip("archive lacks build_candidate_event")
    return mod.build_candidate_event


def _common_inputs():
    return dict(
        symbol="AAA",
        universe_meta={
            "symbol": "AAA", "exchange": "NASDAQ", "venue_code": "XNAS",
            "instrument_class": "operating_equity",
            "eligible_for_bowaka_equity_bucket": True,
        },
        cfg={
            "data": {"provider": "alpaca", "feed": "iex", "intraday_timeframe": "1m"},
            "scanner": {"signal_expiry_seconds": 600},
        },
        universe_hash="sha256:abc",
        config_hash_v="sha256:def",
        session_bar={
            "session_open": 100.0, "session_high": 102.0, "session_low": 99.0,
            "last_price": 101.0, "session_volume": 12345.0,
            "session_range": 3.0, "last_bar_timestamp": "2024-09-04T14:30:00+00:00",
        },
        prior_baselines={
            "prior_close": 99.0, "avg_volume_20d": 100_000,
            "avg_dollar_volume_20d": 10_000_000, "prior_atr_14d": 1.5,
            "prior_atr_pct": 0.015, "ema_10_prior": 98.5, "ema_10_lag_3": 98.0,
            "ema_slope_prior": 0.005,
        },
        forming_feats={
            "rvol_so_far": 2.5, "projected_full_day_rvol": 3.0,
            "range_expansion_so_far": 2.0, "close_location_so_far": 0.8,
            "ema_distance": 0.025, "current_return_pct": 0.02, "gap_pct": 0.01,
            "expected_volume_until_scan": 5000.0,
        },
        volume_curve_fraction=0.20,
        candidate_rank=1,
        signal_strength=4.5,
    )


def test_parity_with_archive_event_modulo_added_gate_keys() -> None:
    archive_build = _load_archive_builder()
    gates = {
        "price_gate": True, "avg_dollar_volume_gate": True, "rvol_gate": True,
        "prior_atr_pct_gate": True, "range_expansion_gate": True,
        "close_location_gate": True, "ema_distance_gate": True,
        "ema_slope_gate": True, "max_gap_gate": True, "instrument_gate": True,
    }
    ports_gates = dict(gates)
    # The §8.3 fix adds three keys to the ported gate set.
    ports_gates.update({
        "projected_rvol_gate": True, "max_rvol_gate": True,
        "max_range_expansion_gate": True,
    })

    common = _common_inputs()
    scan_ts = pd.Timestamp("2024-09-04 14:30:00", tz="UTC")

    archive_ev = archive_build(
        gate_results=gates, scan_ts=scan_ts.to_pydatetime(),
        **common,
    )
    ported_ev = ported_builder(
        gate_results=ports_gates, scan_ts=scan_ts,
        generated_at=archive_ev.get("generated_at"),  # match archive's ts
        **common,
    )

    # Compare every field except gate_results (where we expect the §8.3 superset)
    # and signal_expiry_timestamp / generated_at (we already align generated_at).
    for k in archive_ev.keys():
        if k in ("gate_results",):
            continue
        assert ported_ev.get(k) == archive_ev.get(k), (
            f"parity mismatch on field {k!r}: archive={archive_ev.get(k)!r} "
            f"vs ported={ported_ev.get(k)!r}"
        )
    # gate_results: archive subset must be present in ported with identical values.
    for k, v in archive_ev["gate_results"].items():
        assert ported_ev["gate_results"].get(k) == v
