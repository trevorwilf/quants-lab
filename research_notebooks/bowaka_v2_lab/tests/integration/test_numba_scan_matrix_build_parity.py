"""Phase 1 (walk-forward numba) — LOAD-BEARING build-parity guard.

Builds one scan-matrix session partition on a tiny synthetic lake with
``optuna.acceleration.numba.enabled`` False and True and asserts EVERY stored
column is byte-equal for ints/bools and ``atol<=1e-10`` for floats. This proves
that enabling the compiled feature kernels does not perturb the matrix the
per-trial runtime reads — so the existing scan-matrix parity proof (which is run
numba-OFF as the canonical, kernel-independent proof) transfers unchanged.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pytest
import yaml

pytestmark = pytest.mark.slow

_LAB = Path(__file__).resolve().parents[2]
_QUARANTINED = (
    _LAB / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml"
)
_SYMBOLS = ["AAA", "BBB"]
_START = dt.date(2024, 1, 1)
_END = dt.date(2024, 5, 1)
_SESSION = dt.date(2024, 3, 15)


def _build(tmp_path: Path, *, numba: bool) -> Path:
    from bowaka_v2_lab.config import load_config
    from bowaka_v2_lab.devtools.wf_lake import (
        build_tiny_lake,
        write_walkforward_test_config,
    )
    from bowaka_v2_lab.scanner.scan_matrix import build_session_partition

    lake = tmp_path / "lake"
    build_tiny_lake(lake, _SYMBOLS, start=_START, end=_END)
    cfg_path = write_walkforward_test_config(
        _QUARANTINED, tmp_path / f"wf_{numba}.yml",
        lake=lake, symbols=_SYMBOLS, start=_START, end=_END, n_trials=1,
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    raw.setdefault("session", {})["scan_interval_seconds"] = 1800
    raw.setdefault("simulation", {})["intraday_window_policy"] = "extended_hours_to_scan"
    raw.setdefault("optuna", {}).setdefault("acceleration", {})["numba"] = {"enabled": numba}
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    cfg = load_config(cfg_path)
    feed = (cfg.get("market_data") or {}).get("feed", "iex")
    store_root = tmp_path / ("store_on" if numba else "store_off")
    store_root.mkdir(parents=True, exist_ok=True)
    frag = build_session_partition(
        _SESSION, cfg, lake, feed, store_root=store_root, scope="validation",
    )
    return Path(frag["partition_dir"])


def _load_cols(part_dir: Path) -> dict[str, np.ndarray]:
    return {p.name: np.load(str(p), allow_pickle=False) for p in sorted(part_dir.glob("*.npy"))}


def test_numba_build_matches_pure_python_build(tmp_path: Path) -> None:
    if not _QUARANTINED.is_file():
        pytest.skip("quarantined walk-forward template not present")

    off = _load_cols(_build(tmp_path / "off", numba=False))
    on = _load_cols(_build(tmp_path / "on", numba=True))

    assert set(off) == set(on), f"column file sets differ: {set(off) ^ set(on)}"
    # Sanity: the kernel path must actually have fired (the matrix has feature
    # cells), else this would be a vacuous comparison of all-default arrays.
    assert "dyn_u8__has_baseline.npy" in off
    assert int(off["dyn_u8__has_baseline.npy"].sum()) > 0, (
        "no baseline cells — pick a session with >=20 prior daily bars"
    )

    worst_float = 0.0
    for name in sorted(off):
        a, b = off[name], on[name]
        assert a.shape == b.shape, f"{name}: shape {a.shape} vs {b.shape}"
        if np.issubdtype(a.dtype, np.floating):
            nan_a, nan_b = np.isnan(a), np.isnan(b)
            assert np.array_equal(nan_a, nan_b), f"{name}: NaN positions differ"
            m = ~nan_a
            if m.any():
                d = float(np.max(np.abs(a[m] - b[m])))
                worst_float = max(worst_float, d)
                np.testing.assert_allclose(a[m], b[m], atol=1e-10, rtol=1e-10)
        else:
            np.testing.assert_array_equal(a, b, err_msg=f"{name}: int/bool mismatch")
    assert worst_float <= 1e-10, f"worst float diff {worst_float:.2e} exceeds 1e-10"
