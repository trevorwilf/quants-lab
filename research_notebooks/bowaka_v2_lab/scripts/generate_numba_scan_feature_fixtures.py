"""Generate committed parity fixtures for the Phase 1 numba scan-feature kernels.

Run once and COMMIT the output (market_lab pattern). Each fixture seeds synthetic
daily + minute bars, computes the PURE-PYTHON reference (the same algorithm the
kernels replicate) for both the prior-daily baselines and the per-(scan, symbol)
build columns, and stores inputs + expected outputs in ``.npz`` + a JSON sidecar
at small / medium / large sizes under ``tests/fixtures/numba_scan_features/``.

    cd research_notebooks/bowaka_v2_lab
    PYTHONPATH=src:../bowaka_common/src python scripts/generate_numba_scan_feature_fixtures.py
    git add tests/fixtures/numba_scan_features/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_LAB_ROOT = Path(__file__).resolve().parents[1]
if str(_LAB_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_LAB_ROOT / "src"))

from bowaka_v2_lab.features.forming_bar import (  # noqa: E402
    _et_minute_of_day,
    aggregate_forming_session_bar,
    compute_forming_session_features,
    compute_prior_daily_baselines,
    compute_volume_curve_fraction,
)

FIX_DIR = _LAB_ROOT / "tests" / "fixtures" / "numba_scan_features"
_BASE_KEYS = [
    "prior_close", "prior_atr_14d", "prior_atr_pct", "avg_volume_20d",
    "avg_dollar_volume_20d", "ema_10_prior", "ema_10_lag_3", "ema_slope_prior",
]
SIZES = [
    ("small", 22, 80, 17),
    ("medium", 40, 200, 11),
    ("large", 80, 390, 5),
]
ATR_N, LOOKBACK, EMA_N, EMA_SLOPE = 14, 20, 10, 3
FALLBACK_SHARE = 0.08


def _make_daily(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    price = 100.0
    rows = []
    for _ in range(n):
        o = price
        c = o + rng.normal(0.0, 1.0)
        h = max(o, c) + abs(rng.normal(0.0, 0.5))
        lo = min(o, c) - abs(rng.normal(0.0, 0.5))
        lo = max(lo, 0.01)
        v = float(rng.uniform(1.0e5, 5.0e5))
        rows.append((o, h, lo, c, v))
        price = c
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])


def _make_minute(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2024-05-01 09:30", tz="America/New_York").tz_convert("UTC")
    ts = [start + pd.Timedelta(minutes=i) for i in range(n)]
    price = 100.0
    o_, h_, l_, c_, v_ = [], [], [], [], []
    for _ in range(n):
        o = price
        c = o + rng.normal(0.0, 0.2)
        h = max(o, c) + abs(rng.normal(0.0, 0.1))
        lo = min(o, c) - abs(rng.normal(0.0, 0.1))
        lo = max(lo, 0.01)
        o_.append(o); h_.append(h); l_.append(lo); c_.append(c)
        v_.append(float(rng.uniform(0.5, 3.0)))
        price = c
    return pd.DataFrame({
        "timestamp": ts, "open": o_, "high": h_, "low": l_,
        "close": c_, "volume": v_,
    })


def _pure_build_columns(mdf: pd.DataFrame, scan_times, baselines: dict, fallback_share: float):
    """Replicate build_session_partition's per-scan loop in pure Python."""
    n = len(scan_times)
    cols = {
        "has_bar": np.zeros(n, np.uint8),
        "has_valid_ts": np.zeros(n, np.uint8),
        "has_baseline": np.zeros(n, np.uint8),
        "last_bar_ts_ns": np.full(n, -1, np.int64),
    }
    fkeys = ["s_open", "s_high", "s_low", "s_last", "s_vol", "s_range", "bar_age",
             "vcf", "expv", "rvol", "proj", "rexp", "cloc", "edist", "cret", "gap"]
    for k in fkeys:
        cols[k] = np.full(n, np.nan, np.float64)

    def _nn(v):
        if v is None:
            return float("nan")
        try:
            return float(v)
        except (TypeError, ValueError):
            return float("nan")

    has_bl = bool(baselines)
    for t, s in enumerate(scan_times):
        sc = pd.Timestamp(s).tz_convert("UTC")
        # L1 (PIT look-ahead) fix: mirror the kernel/matrix cutoff — only
        # fully-closed bars (exclude the still-forming minute at sc).
        bt = mdf[mdf["timestamp"] <= sc - pd.Timedelta(seconds=60)]
        sess = aggregate_forming_session_bar(bt)
        if sess.get("last_price") is not None:
            cols["has_bar"][t] = 1
        cols["s_open"][t] = _nn(sess.get("session_open"))
        cols["s_high"][t] = _nn(sess.get("session_high"))
        cols["s_low"][t] = _nn(sess.get("session_low"))
        cols["s_last"][t] = _nn(sess.get("last_price"))
        cols["s_vol"][t] = _nn(sess.get("session_volume"))
        cols["s_range"][t] = _nn(sess.get("session_range"))
        lt = sess.get("last_bar_timestamp")
        if lt is not None:
            to = pd.Timestamp(lt)
            cols["last_bar_ts_ns"][t] = to.value
            cols["has_valid_ts"][t] = 1
            cols["bar_age"][t] = float((sc - to.tz_convert("UTC")).total_seconds())
        if has_bl and sess.get("last_price") is not None:
            cols["has_baseline"][t] = 1
            vcf = compute_volume_curve_fraction(
                None, sc, "x", fallback_opening_15m_share=fallback_share)
            feats = compute_forming_session_features(sess, baselines, vcf)
            cols["vcf"][t] = _nn(vcf)
            cols["expv"][t] = _nn(feats.get("expected_volume_until_scan"))
            cols["rvol"][t] = _nn(feats.get("rvol_so_far"))
            cols["proj"][t] = _nn(feats.get("projected_full_day_rvol"))
            cols["rexp"][t] = _nn(feats.get("range_expansion_so_far"))
            cols["cloc"][t] = _nn(feats.get("close_location_so_far"))
            cols["edist"][t] = _nn(feats.get("ema_distance"))
            cols["cret"][t] = _nn(feats.get("current_return_pct"))
            cols["gap"][t] = _nn(feats.get("gap_pct"))
    return cols


def _gen(size: str, n_daily: int, n_min: int, scan_step: int) -> None:
    ddf = _make_daily(n_daily, seed=100 + len(size))
    mdf = _make_minute(n_min, seed=200 + len(size))
    start = mdf["timestamp"].iloc[0]
    scan_times = [start + pd.Timedelta(minutes=m) for m in range(0, n_min + 30, scan_step)]

    base = compute_prior_daily_baselines(
        ddf, atr_n=ATR_N, lookback=LOOKBACK, ema_n=EMA_N,
        ema_slope_lookback=EMA_SLOPE, use_numba=False,
    )
    base_expected = np.array(
        [np.nan if base[k] is None else float(base[k]) for k in _BASE_KEYS],
        dtype=np.float64,
    )
    cols = _pure_build_columns(mdf, scan_times, base, FALLBACK_SHARE)

    scan_ts_ns = np.array([pd.Timestamp(s).tz_convert("UTC").value for s in scan_times], np.int64)
    scan_mod = np.array([_et_minute_of_day(pd.Timestamp(s)) for s in scan_times], np.int64)

    FIX_DIR.mkdir(parents=True, exist_ok=True)
    npz_path = FIX_DIR / f"scan_features_{size}.npz"
    np.savez(
        npz_path,
        daily_close=ddf["close"].to_numpy(np.float64),
        daily_high=ddf["high"].to_numpy(np.float64),
        daily_low=ddf["low"].to_numpy(np.float64),
        daily_volume=ddf["volume"].to_numpy(np.float64),
        base_expected=base_expected,
        bar_ts_ns=mdf["timestamp"].astype("int64").to_numpy(),
        bar_open=mdf["open"].to_numpy(np.float64),
        bar_high=mdf["high"].to_numpy(np.float64),
        bar_low=mdf["low"].to_numpy(np.float64),
        bar_close=mdf["close"].to_numpy(np.float64),
        bar_volume=mdf["volume"].to_numpy(np.float64),
        scan_ts_ns=scan_ts_ns,
        scan_minute_of_day=scan_mod,
        avg_volume_20d=np.float64(base_expected[3]),
        prior_atr_14d=np.float64(base_expected[1]),
        prior_close=np.float64(base_expected[0]),
        ema_10_prior=np.float64(base_expected[5]),
        **cols,
    )
    sidecar = {
        "type": "scan_features", "size": size, "n_daily": n_daily,
        "n_minute": n_min, "n_scans": len(scan_times), "scan_step_min": scan_step,
        "fallback_share": FALLBACK_SHARE, "atr_n": ATR_N, "lookback": LOOKBACK,
        "ema_n": EMA_N, "ema_slope_lookback": EMA_SLOPE,
    }
    npz_path.with_suffix(".json").write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    print(f"wrote {npz_path.name}  (n_daily={n_daily} n_min={n_min} n_scans={len(scan_times)})")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    for size, nd, nm, step in SIZES:
        _gen(size, nd, nm, step)
    print(f"fixtures -> {FIX_DIR}")


if __name__ == "__main__":
    main()
