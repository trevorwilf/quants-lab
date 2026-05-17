"""Synthetic daily-bars fixture generator for prefilter regression tests.

Running this script regenerates:

  tests/fixtures/daily_bars_small.parquet     -- 30 sessions, 6 synthetic symbols
  tests/fixtures/expected_features.json       -- compute_daily_features() golden
  tests/fixtures/expected_candidates.json     -- apply_prefilter() golden

Determinism comes from seeded numpy RNG. Re-run this when feature math changes
intentionally; otherwise leave the fixtures frozen. The frozen JSON files are
committed so test runs do NOT depend on the generator's RNG state.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from bowaka_lab.config.models import (
    PrefilterConfig,
    ScoreConfig,
    UniverseConfig,
)
from bowaka_lab.features.daily_features import compute_daily_features
from bowaka_lab.features.prefilter import apply_prefilter

OUT_DIR = Path(__file__).resolve().parent / "fixtures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _generate_synthetic_bars(*, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
    n_sessions = 30
    start = date(2026, 4, 1)
    rows = []
    for s in symbols:
        base_price = float(rng.uniform(2.0, 15.0))
        for i in range(n_sessions):
            d = start + timedelta(days=i * 1)
            if d.weekday() >= 5:
                continue
            move = rng.normal(0, 0.03)
            base_price = max(0.5, base_price * (1.0 + move))
            high = base_price * (1.0 + abs(rng.normal(0, 0.02)))
            low = base_price * (1.0 - abs(rng.normal(0, 0.02)))
            open_p = base_price * (1.0 + rng.normal(0, 0.01))
            close = base_price
            vol = int(rng.integers(50_000, 5_000_000))
            # Anchor each bar's timestamp at 16:00 ET (market close) so the
            # NY session_date equals the calendar date d; otherwise UTC-midnight
            # would shift the session_date back one day.
            ts = (pd.Timestamp(d).tz_localize("America/New_York") + pd.Timedelta(hours=16)).tz_convert("UTC")
            rows.append(
                {
                    "symbol": s,
                    "timestamp": ts,
                    "open": float(open_p),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                    "volume": int(vol),
                }
            )
    df = pd.DataFrame(rows).sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    df["session_date"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
    return df


def main() -> None:
    bars = _generate_synthetic_bars()
    bars.to_parquet(OUT_DIR / "daily_bars_small.parquet", index=False)

    cfg = PrefilterConfig(
        lookback_days=10,
        atr_days=7,
        ema_days=5,
        ema_slope_lookback=2,
        price_min=1.0,
        price_max=30.0,
        avg_dollar_volume_min=100_000,
        rvol_min=None,
        atr_pct_min=None,
        range_expansion_min=None,
        close_location_min=None,
        ema_distance_min=None,
        ema_slope_min=None,
        score=ScoreConfig(bounded=False),
    )

    signal_date = bars["session_date"].max()
    features = compute_daily_features(bars, cfg, signal_date=signal_date)
    features_records = features.reset_index().to_dict(orient="records")
    (OUT_DIR / "expected_features.json").write_text(
        json.dumps({"signal_date": str(signal_date), "rows": features_records}, default=str, indent=2)
    )

    universe = UniverseConfig(
        exclude_leveraged_etp=True,
        exclude_inverse_etp=True,
        exclude_etn=True,
        ticker_blocklist=[],
    )
    cset = apply_prefilter(
        features,
        cfg,
        signal_date=signal_date,
        trade_date=signal_date + timedelta(days=1),
        universe=universe,
    )
    decisions = cset.all_decisions.reset_index().to_dict(orient="records")
    candidates = cset.candidates.reset_index().to_dict(orient="records")
    (OUT_DIR / "expected_candidates.json").write_text(
        json.dumps(
            {
                "signal_date": str(signal_date),
                "metadata": cset.metadata,
                "candidates": candidates,
                "all_decisions": decisions,
            },
            default=str,
            indent=2,
        )
    )
    print(f"Wrote fixtures to {OUT_DIR}")


if __name__ == "__main__":
    main()
