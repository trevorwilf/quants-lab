"""Phase 9 — slippage calibrator: fit, persist, load, apply to the fill model.

End-to-end proof that:

1. :func:`fit_slippage_calibrator` fits a per-(spread, ADV, vol) bin residual
   from synthetic paper-vs-sim observations.
2. :func:`write_slippage_calibrator` persists it to JSON, and
   :func:`load_slippage_calibrator` reads it back into an equal artifact.
3. The T4 fill tier in :mod:`bowaka_v2_lab.sim.fills` consumes the artifact:
   when ``has_calibration_artifact=True`` and a calibrator is passed in, the
   modelled fill price is shifted by the calibrated bps. With no calibrator
   the fill price comes back unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.reconcile import (
    DEFAULT_ADV_BIN_EDGES_SHARES,
    DEFAULT_SPREAD_BIN_EDGES_BPS,
    DEFAULT_VOL_BIN_EDGES,
    FillFeatureRow,
    SlippageCalibratorArtifact,
    calibrator_lookup_bps,
    fit_slippage_calibrator,
    load_slippage_calibrator,
    write_slippage_calibrator,
)
from bowaka_v2_lab.sim.fills import ExecutionTier, simulate_marketable_limit_fill
from bowaka_v2_lab.sim.quote_model import QuoteSnapshot, SOURCE_HISTORICAL


def _toy_observations() -> list[FillFeatureRow]:
    """5 paper-vs-sim observations across mid spread + mid ADV + low vol."""
    return [
        FillFeatureRow(paper_price=10.05, sim_price=10.00,
                       spread_bps=10.0, adv_shares=500_000.0, volatility=0.4,
                       side="buy"),
        FillFeatureRow(paper_price=10.06, sim_price=10.01,
                       spread_bps=10.0, adv_shares=500_000.0, volatility=0.4,
                       side="buy"),
        FillFeatureRow(paper_price=10.08, sim_price=10.02,
                       spread_bps=10.0, adv_shares=500_000.0, volatility=0.4,
                       side="buy"),
        FillFeatureRow(paper_price=10.07, sim_price=10.01,
                       spread_bps=10.0, adv_shares=500_000.0, volatility=0.4,
                       side="buy"),
        FillFeatureRow(paper_price=10.04, sim_price=10.00,
                       spread_bps=10.0, adv_shares=500_000.0, volatility=0.4,
                       side="buy"),
    ]


def test_slippage_calibrator_fit_then_lookup() -> None:
    """A fitted calibrator returns the mean bps for the bin it saw."""
    artifact = fit_slippage_calibrator(
        _toy_observations(),
        vintage="2024-09-03",
    )
    assert artifact.n_observations == 5
    # All five obs fell in the same (spread=mid, adv=mid, vol=low) bin —
    # the binned mean is well above zero.
    bps = calibrator_lookup_bps(
        artifact,
        spread_bps=10.0, adv_shares=500_000.0, volatility=0.4,
    )
    # Mean residual is ~50 bps (paper ~$0.05 over sim on a $10 base).
    assert bps > 30.0
    assert bps < 70.0


def test_slippage_calibrator_persist_and_load(tmp_path: Path) -> None:
    """Persist → load roundtrips to an equal in-memory artifact."""
    artifact = fit_slippage_calibrator(_toy_observations(), vintage="2024-09-03")
    out = tmp_path / "artifacts" / "calibration" / "slippage_2024-09-03.json"
    written = write_slippage_calibrator(artifact, out)
    assert written.is_file()
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk["vintage"] == "2024-09-03"
    assert on_disk["n_observations"] == 5
    assert "bins" in on_disk
    assert "residual_bps_by_bin" in on_disk
    reloaded = load_slippage_calibrator(out)
    assert isinstance(reloaded, SlippageCalibratorArtifact)
    assert reloaded.vintage == artifact.vintage
    assert reloaded.n_observations == artifact.n_observations
    assert reloaded.residual_bps_by_bin == artifact.residual_bps_by_bin
    assert reloaded.default_residual_bps == artifact.default_residual_bps


def test_slippage_calibrator_unknown_bin_returns_default(tmp_path: Path) -> None:
    """A lookup that misses every bin falls back to the default."""
    artifact = fit_slippage_calibrator(_toy_observations(), vintage="2024-09-03")
    # Pick a (spread, adv, vol) combination far outside the fitted bin.
    bps = calibrator_lookup_bps(
        artifact,
        spread_bps=40.0, adv_shares=10_000_000.0, volatility=1.8,
    )
    # Unknown bin → default_residual_bps (which is the global mean).
    assert bps == artifact.default_residual_bps


def test_calibrator_default_bin_edges_used_when_absent() -> None:
    """A fit with no edges uses the module's default bin edges."""
    artifact = fit_slippage_calibrator(_toy_observations(), vintage="2024-09-03")
    assert artifact.bins["spread"] == list(DEFAULT_SPREAD_BIN_EDGES_BPS)
    assert artifact.bins["adv"] == list(DEFAULT_ADV_BIN_EDGES_SHARES)
    assert artifact.bins["volatility"] == list(DEFAULT_VOL_BIN_EDGES)


def test_t4_fill_applies_calibrator_shift() -> None:
    """The T4 fill tier shifts the fill price by the calibrated bps."""
    # Fit a calibrator with a strong positive residual (paper worse than sim).
    obs = [
        FillFeatureRow(paper_price=10.05, sim_price=10.00,
                       spread_bps=10.0, adv_shares=500_000.0, volatility=0.4,
                       side="buy"),
        FillFeatureRow(paper_price=10.05, sim_price=10.00,
                       spread_bps=10.0, adv_shares=500_000.0, volatility=0.4,
                       side="buy"),
    ]
    artifact = fit_slippage_calibrator(obs, vintage="2024-09-03")
    # The residual for this bin is ~50 bps positive.
    bps_expected = calibrator_lookup_bps(
        artifact, spread_bps=10.0, adv_shares=500_000.0, volatility=0.4,
    )
    assert bps_expected >= 30.0

    quote = QuoteSnapshot(
        bid=9.99, ask=10.00, mid=9.995, spread_pct=0.001,
        quote_timestamp="2024-09-03T13:45:01Z", quote_age_seconds=1.0,
        source=SOURCE_HISTORICAL,
        bid_size=1_000.0, ask_size=1_000.0,
    )
    # Provide a minute bar so T2+ tiers can read minute volume.
    minute_bars = pd.DataFrame({
        "timestamp": [pd.Timestamp("2024-09-03T13:45:00Z")],
        "open": [10.0], "high": [10.05], "low": [9.98], "close": [10.0],
        "volume": [100_000.0],
    })

    # Baseline T1 (no NBBO depth, no calibration) — fill at the quote ask.
    base = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=quote,
        marketable_limit_slippage_pct=0.005, minute_bars=minute_bars,
        scan_ts=pd.Timestamp("2024-09-03T13:45:00Z"),
        liquidity_proxy_shares=500_000.0,
        adv_participation_frac=0.01, min_order_notional=0.0,
        has_calibration_artifact=False, slippage_calibrator=None,
    )
    assert base.filled is True
    # Now T4: same setup but with calibrator → fill price shifts UP by ~bps_expected bps.
    cal = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=quote,
        marketable_limit_slippage_pct=0.005, minute_bars=minute_bars,
        scan_ts=pd.Timestamp("2024-09-03T13:45:00Z"),
        liquidity_proxy_shares=500_000.0,
        adv_participation_frac=0.01, min_order_notional=0.0,
        has_calibration_artifact=True, slippage_calibrator=artifact,
    )
    assert cal.filled is True
    assert cal.execution_tier == ExecutionTier.T4_CALIBRATED.value
    # The T4 price is HIGHER than the T1 baseline (positive residual = paper worse for buy).
    assert cal.avg_fill_price > base.avg_fill_price
    observed_bps = (cal.avg_fill_price - base.avg_fill_price) / base.avg_fill_price * 10_000.0
    # The applied shift is within +/-1 bps of the calibrator's prediction
    # (rounding in the fill price's 4-decimal representation).
    assert abs(observed_bps - bps_expected) < 1.5


def test_t4_without_calibrator_is_no_op() -> None:
    """``has_calibration_artifact=True`` but no calibrator → behaves like T2."""
    quote = QuoteSnapshot(
        bid=9.99, ask=10.00, mid=9.995, spread_pct=0.001,
        quote_timestamp="2024-09-03T13:45:01Z", quote_age_seconds=1.0,
        source=SOURCE_HISTORICAL,
        bid_size=1_000.0, ask_size=1_000.0,
    )
    minute_bars = pd.DataFrame({
        "timestamp": [pd.Timestamp("2024-09-03T13:45:00Z")],
        "open": [10.0], "high": [10.05], "low": [9.98], "close": [10.0],
        "volume": [100_000.0],
    })
    base = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=quote,
        marketable_limit_slippage_pct=0.005, minute_bars=minute_bars,
        scan_ts=pd.Timestamp("2024-09-03T13:45:00Z"),
        liquidity_proxy_shares=500_000.0,
        adv_participation_frac=0.01, min_order_notional=0.0,
        has_calibration_artifact=False,
    )
    no_cal = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=quote,
        marketable_limit_slippage_pct=0.005, minute_bars=minute_bars,
        scan_ts=pd.Timestamp("2024-09-03T13:45:00Z"),
        liquidity_proxy_shares=500_000.0,
        adv_participation_frac=0.01, min_order_notional=0.0,
        has_calibration_artifact=True, slippage_calibrator=None,
    )
    # T4 with no calibrator falls back gracefully — same fill price.
    assert no_cal.avg_fill_price == base.avg_fill_price


def test_load_missing_calibrator_raises(tmp_path: Path) -> None:
    """Loading a non-existent artifact path raises ``FileNotFoundError``."""
    import pytest
    with pytest.raises(FileNotFoundError):
        load_slippage_calibrator(tmp_path / "i-do-not-exist.json")
