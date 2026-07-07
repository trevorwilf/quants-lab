"""Frozen-fixture parity for the range_ladder fill kernel.

The pure-Python reference is the golden path (fixtures were generated from
it — see scripts/generate_range_ladder_fixtures.py). These tests prove:
1. the reference still reproduces the frozen outputs bit-for-bit, and
2. the numba kernel matches the reference bit-for-bit (when numba is
   available), across all sizes and dial combos (asymmetric ladder, k<0 and
   k>0 tilts, cash-starved run, stress dials).
"""

import json
from pathlib import Path

import numpy as np
import pytest

from pmm_lab.features._numba_availability import _NUMBA_AVAILABLE
from pmm_lab.features._numba_range_ladder import (
    UNBOUNDED_FILLS,
    _run_ladder_kernel,
    _run_ladder_reference,
    run_ladder_sim,
)

FIX_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "numba_parity"

FIXTURES = [
    f"rl_{size}_{cfg}"
    for size in ("small", "medium", "large")
    for cfg in ("cfg0", "cfg1", "cfg2", "cfg3")
]


def _load(name):
    z = np.load(FIX_DIR / f"{name}.npz")
    with open(FIX_DIR / f"{name}.json") as f:
        meta = json.load(f)
    return z, meta


def _kernel_args(z, meta):
    d = meta["dials"]
    mfpb = UNBOUNDED_FILLS if d["max_fills_per_bar"] == 0 else np.int64(d["max_fills_per_bar"])
    return (
        z["o"], z["h"], z["l"], z["c"],
        z["buys"], z["sells"], z["bw"], z["sw"],
        float(d["fund"]), float(d["quote_frac"]), float(d["fee"]),
        float(d["slip"]), mfpb, np.int64(d["cooldown_bars"]),
        bool(d["body_only"]),
    )


def _assert_matches_fixture(out, z, label):
    quote, base, fees, bf, sf, cb, cs, eq, pb = out
    assert quote == float(z["quote"]), f"{label}: quote mismatch"
    assert base == float(z["base"]), f"{label}: base mismatch"
    assert fees == float(z["fees"]), f"{label}: fees mismatch"
    np.testing.assert_array_equal(bf, z["bf"], err_msg=f"{label}: bf")
    np.testing.assert_array_equal(sf, z["sf"], err_msg=f"{label}: sf")
    np.testing.assert_array_equal(cb, z["cb"], err_msg=f"{label}: cb")
    np.testing.assert_array_equal(cs, z["cs"], err_msg=f"{label}: cs")
    np.testing.assert_array_equal(eq, z["eq"], err_msg=f"{label}: eq")
    np.testing.assert_array_equal(pb, z["pb"], err_msg=f"{label}: pb")


@pytest.mark.parametrize("name", FIXTURES)
def test_reference_matches_frozen_fixture(name):
    z, meta = _load(name)
    out = _run_ladder_reference(*_kernel_args(z, meta))
    _assert_matches_fixture(out, z, f"{name} reference")


@pytest.mark.parametrize("name", FIXTURES)
@pytest.mark.skipif(not _NUMBA_AVAILABLE, reason="numba not installed")
def test_numba_kernel_matches_frozen_fixture(name):
    z, meta = _load(name)
    out = _run_ladder_kernel(*_kernel_args(z, meta))
    _assert_matches_fixture(out, z, f"{name} numba")


def test_fixtures_exercise_required_scenarios():
    """The fixture grid must include the spec-mandated dial combos."""
    seen_asymmetric = seen_kneg = seen_kpos = seen_starved = False
    for name in FIXTURES:
        _, meta = _load(name)
        g, d = meta["gen"], meta["dials"]
        if g["n_buy"] == 3 and g["n_sell"] == 9:
            seen_asymmetric = True
        if g["k_buy"] < 0 or g["k_sell"] < 0:
            seen_kneg = True
        if g["k_buy"] > 0 or g["k_sell"] > 0:
            seen_kpos = True
        if d["quote_frac"] == 0.05:
            seen_starved = True
    assert seen_asymmetric and seen_kneg and seen_kpos and seen_starved


def test_run_ladder_sim_fallback_when_numba_missing(monkeypatch):
    """With numba flagged unavailable the wrapper must use the reference."""
    import pmm_lab.features._numba_range_ladder as mod

    z, meta = _load("rl_small_cfg0")
    monkeypatch.setattr(mod, "_NUMBA_AVAILABLE", False)
    d = meta["dials"]
    r = run_ladder_sim(
        z["o"], z["h"], z["l"], z["c"], z["buys"], z["sells"], z["bw"], z["sw"],
        fund=d["fund"], quote_frac=d["quote_frac"], fee=d["fee"], slip=d["slip"],
        cooldown_bars=d["cooldown_bars"], max_fills_per_bar=d["max_fills_per_bar"],
        body_only=d["body_only"],
    )
    np.testing.assert_array_equal(r["equity"], z["eq"])
    assert r["fees"] == float(z["fees"])
