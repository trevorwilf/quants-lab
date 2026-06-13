"""P3 (L3, L5) — scanner-feature parity regression pins.

L5: the production daily-cache builder's ``ema_slope_prior`` is the dimensionless
RATIO (``ema_prior/ema_lag3 - 1``, matching features/forming_bar + the live
contract), not the prior abs/(slope_lookback) form ``(ema_prior - ema_lag3)/3``.

L3: the scan-matrix cumulates the forming session bar from the POLICY window
(09:45 ET for scanner_start_to_scan), not a hardcoded 04:00 premarket start, so
its session open/high/low/volume match the live/legacy scan_loop supplier.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def test_supplier_ema_slope_prior_is_dimensionless_ratio() -> None:
    """L5: the daily-cache helper returns the ratio slope, not abs/3."""
    from bowaka_v2_lab.data.suppliers import _daily_cache_row_from_prior

    n = 60
    close = np.linspace(100.0, 130.0, n)  # rising -> ema_prior != ema_lag3
    prior = pd.DataFrame({
        "close": close, "high": close + 0.5, "low": close - 0.5,
        "volume": np.full(n, 1_000_000.0),
    })
    row = _daily_cache_row_from_prior(
        "AAA", prior, atr_window=14, vol_window=20, ema_span=10,
    )
    ema = pd.Series(close).ewm(span=10, adjust=False).mean()
    ema_prior, ema_lag3 = float(ema.iloc[-1]), float(ema.iloc[-4])
    expected_ratio = ema_prior / ema_lag3 - 1.0
    old_abs3 = (ema_prior - ema_lag3) / 3.0

    assert row["ema_slope_prior"] == pytest.approx(expected_ratio, rel=1e-12)
    # Guard the test isn't vacuous: the two forms must differ materially here.
    assert abs(expected_ratio - old_abs3) > 1e-6
    assert row["ema_slope_prior"] != pytest.approx(old_abs3, rel=1e-9)


def test_matrix_session_window_honors_policy_not_premarket(tmp_path: Path) -> None:
    """L3: the matrix cumulates from the 09:45 policy window, not 04:00.

    build_tiny_lake writes 09:30..09:59 ET bars (30 bars, 5000 vol each). Under
    scanner_start_to_scan the matrix window starts at 09:45 -> a post-close scan's
    cumulative session_volume = 15 bars * 5000 = 75_000, NOT 30 bars * 5000 =
    150_000 (the old 04:00-window bug, which wrongly included 09:30..09:44).
    """
    import yaml

    from bowaka_v2_lab.config import load_config
    from bowaka_v2_lab.devtools.wf_lake import (
        build_tiny_lake,
        write_walkforward_test_config,
    )
    from bowaka_v2_lab.scanner.scan_matrix import build_session_partition

    lab = Path(__file__).resolve().parents[2]
    quarantined = lab / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml"
    if not quarantined.is_file():
        pytest.skip("quarantined walk-forward template not present")

    symbols = ["AAA"]
    start, end, session = _dt.date(2024, 1, 1), _dt.date(2024, 5, 1), _dt.date(2024, 3, 15)
    lake = tmp_path / "lake"
    build_tiny_lake(lake, symbols, start=start, end=end)
    cfg_path = write_walkforward_test_config(
        quarantined, tmp_path / "wf.yml", lake=lake, symbols=symbols,
        start=start, end=end, n_trials=1,
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    raw.setdefault("session", {})["scan_interval_seconds"] = 1800
    raw.setdefault("simulation", {})["intraday_window_policy"] = "scanner_start_to_scan"
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    cfg = load_config(cfg_path)
    feed = (cfg.get("market_data") or {}).get("feed", "iex")
    store_root = tmp_path / "store"
    store_root.mkdir(parents=True, exist_ok=True)
    frag = build_session_partition(
        session, cfg, lake, feed, store_root=store_root, scope="validation",
    )
    part_dir = Path(frag["partition_dir"])
    vol = np.load(str(part_dir / "dyn_f64__session_volume.npy"), allow_pickle=False)
    has_bar = np.load(str(part_dir / "dyn_u8__has_bar.npy"), allow_pickle=False)

    finite = vol[(has_bar.astype(bool)) & np.isfinite(vol)]
    assert finite.size > 0, "no forming-bar scans in the matrix"
    assert float(np.nanmax(finite)) == pytest.approx(75_000.0, rel=1e-9), (
        f"matrix session_volume max={np.nanmax(finite)} != 75_000 (15 bars * 5000) "
        "-> the matrix is cumulating pre-09:45 bars (L3 premarket-window regression)"
    )
