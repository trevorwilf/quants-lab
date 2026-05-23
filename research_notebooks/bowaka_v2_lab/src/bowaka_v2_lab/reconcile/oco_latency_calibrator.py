"""Empirical OCO attach-latency distribution calibrator (Phase 9).

Fits a per-``(symbol_liquidity_tier, time_of_day_bin)`` distribution of the
paper attach latency (parent_fill_ts → oco_attached_ts) so the sim can sample
realistic attach-latency rather than the hard-coded 0.5s default. The artifact
is JSON-shaped to match the slippage calibrator and lives under
``artifacts/calibration/oco_latency_<vintage>.json``.

Liquidity tiers
---------------
- ``micro``   — ADV below the cap that the v2 strategy treats as illiquid.
- ``small``   — small-cap range; harder to attach during volatile open.
- ``mid``     — bulk of names — predictable attach.
- ``large``   — mega-caps; near-instant attach.

The tier mapping is the caller's responsibility (it can be derived from the
strategy's adv breakdown or from a static asset master). The calibrator simply
buckets the inputs it is given.

Time-of-day bins
----------------
- ``open``      — first 30 minutes after open
- ``morning``   — open + 30 min through 12:00 ET
- ``midday``    — 12:00 ET through 14:00 ET
- ``afternoon`` — 14:00 ET through close - 30 min
- ``close``     — last 30 minutes before close
"""
from __future__ import annotations

import datetime as _dt
import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

import pandas as pd


#: Canonical liquidity tier ordering — bin 0 = micro, bin 3 = large.
LIQUIDITY_TIERS: tuple[str, ...] = ("micro", "small", "mid", "large")

#: Time-of-day bins (US/Eastern), tied to the regular NYSE session.
TIME_OF_DAY_BINS: tuple[str, ...] = ("open", "morning", "midday", "afternoon", "close")


def time_of_day_bin(ts: Any) -> str:
    """Bucket an ISO timestamp into one of :data:`TIME_OF_DAY_BINS`.

    The input is treated as UTC and converted to US/Eastern (the v2 strategy's
    canonical clock) before binning. A non-parseable ts falls back to
    ``"midday"`` — we never crash on malformed input.
    """
    try:
        t = pd.Timestamp(ts)
        if t.tzinfo is None:
            t = t.tz_localize("UTC")
        t = t.tz_convert("US/Eastern")
    except Exception:  # noqa: BLE001
        return "midday"
    hour = t.hour
    minute = t.minute
    # Regular session is 09:30 → 16:00 ET.
    if (hour == 9 and minute < 30) or hour < 9:
        return "open"  # pre-open events bucket with open
    if hour == 9 and minute >= 30:
        # First 30 minutes.
        return "open"
    if hour < 12:
        return "morning"
    if hour < 14:
        return "midday"
    if hour < 15 or (hour == 15 and minute < 30):
        return "afternoon"
    return "close"


@dataclass
class OCOLatencyObservation:
    """One paired observation for the OCO attach-latency calibrator."""

    parent_fill_timestamp: str
    attached_timestamp: str
    symbol_liquidity_tier: str
    parent_order_id: Optional[str] = None


@dataclass
class OCOLatencyArtifact:
    """Persisted OCO attach-latency distribution.

    Per-bin entries hold ``n``, ``mean_ms``, ``median_ms``, ``p95_ms``,
    ``min_ms`` and ``max_ms``. ``default_latency_ms`` is the global median —
    used when a (tier, time_of_day) bin is unknown.
    """

    vintage: str
    n_observations: int
    liquidity_tiers: list[str]
    time_of_day_bins: list[str]
    latency_ms_by_bin: dict[str, dict[str, float]]
    default_latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "vintage": self.vintage,
            "n_observations": int(self.n_observations),
            "liquidity_tiers": list(self.liquidity_tiers),
            "time_of_day_bins": list(self.time_of_day_bins),
            "latency_ms_by_bin": {
                k: {kk: float(vv) for kk, vv in v.items()}
                for k, v in self.latency_ms_by_bin.items()
            },
            "default_latency_ms": float(self.default_latency_ms),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OCOLatencyArtifact":
        return cls(
            vintage=str(data.get("vintage") or ""),
            n_observations=int(data.get("n_observations") or 0),
            liquidity_tiers=list(data.get("liquidity_tiers") or LIQUIDITY_TIERS),
            time_of_day_bins=list(data.get("time_of_day_bins") or TIME_OF_DAY_BINS),
            latency_ms_by_bin={
                str(k): {kk: float(vv) for kk, vv in v.items()}
                for k, v in (data.get("latency_ms_by_bin") or {}).items()
            },
            default_latency_ms=float(data.get("default_latency_ms") or 0.0),
        )


def _latency_ms(fill_ts: str, attached_ts: str) -> Optional[float]:
    try:
        a = pd.Timestamp(fill_ts)
        b = pd.Timestamp(attached_ts)
        return float((b - a).total_seconds() * 1000.0)
    except Exception:  # noqa: BLE001
        return None


def _bin_key(tier: str, tod_bin: str) -> str:
    """Compose the canonical (tier, time_of_day) bin key."""
    return f"{tier}|{tod_bin}"


def fit_oco_latency_calibrator(
    observations: Iterable[OCOLatencyObservation],
    *,
    vintage: str,
) -> OCOLatencyArtifact:
    """Fit a per-(tier, time_of_day) OCO attach-latency distribution.

    Observations whose latency is negative or unparseable are dropped from
    fitting (but counted in ``n_observations`` for transparency).
    """
    obs = list(observations)
    per_bin: dict[str, list[float]] = {}
    all_ms: list[float] = []
    for o in obs:
        lat = _latency_ms(o.parent_fill_timestamp, o.attached_timestamp)
        if lat is None or lat < 0:
            continue
        all_ms.append(lat)
        tod = time_of_day_bin(o.parent_fill_timestamp)
        per_bin.setdefault(_bin_key(o.symbol_liquidity_tier, tod), []).append(lat)
    summary: dict[str, dict[str, float]] = {}
    for key, vals in per_bin.items():
        sorted_vals = sorted(vals)
        idx95 = min(len(sorted_vals) - 1, int(round(0.95 * (len(sorted_vals) - 1))))
        summary[key] = {
            "n": float(len(vals)),
            "mean_ms": round(statistics.fmean(vals), 4),
            "median_ms": round(statistics.median(vals), 4),
            "p95_ms": round(sorted_vals[idx95], 4),
            "min_ms": round(min(vals), 4),
            "max_ms": round(max(vals), 4),
        }
    default = round(statistics.median(all_ms), 4) if all_ms else 0.0
    return OCOLatencyArtifact(
        vintage=str(vintage),
        n_observations=len(obs),
        liquidity_tiers=list(LIQUIDITY_TIERS),
        time_of_day_bins=list(TIME_OF_DAY_BINS),
        latency_ms_by_bin=summary,
        default_latency_ms=default,
    )


def write_oco_latency_calibrator(
    artifact: OCOLatencyArtifact, out_path: Path | str
) -> Path:
    """Persist a fitted OCO attach-latency calibrator artifact."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(artifact.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return out


def load_oco_latency_calibrator(path: Path | str) -> OCOLatencyArtifact:
    """Load a calibrator artifact from disk."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"OCO latency calibrator not found: {p}")
    return OCOLatencyArtifact.from_dict(
        json.loads(p.read_text(encoding="utf-8"))
    )


def calibrator_lookup_ms(
    artifact: OCOLatencyArtifact,
    *,
    symbol_liquidity_tier: str,
    timestamp: Any,
    statistic: str = "median_ms",
) -> float:
    """Look up the calibrated attach-latency for a ``(tier, time_of_day)`` point.

    ``statistic`` picks which summary statistic to use — ``median_ms`` (the
    default), ``mean_ms`` or ``p95_ms``. Falls back to
    ``default_latency_ms`` when the bin is unknown.
    """
    tod = time_of_day_bin(timestamp)
    key = _bin_key(symbol_liquidity_tier, tod)
    bin_summary = artifact.latency_ms_by_bin.get(key)
    if bin_summary is None or float(bin_summary.get("n", 0.0)) <= 0:
        return float(artifact.default_latency_ms)
    return float(bin_summary.get(statistic, artifact.default_latency_ms))


__all__ = [
    "LIQUIDITY_TIERS",
    "TIME_OF_DAY_BINS",
    "time_of_day_bin",
    "OCOLatencyObservation",
    "OCOLatencyArtifact",
    "fit_oco_latency_calibrator",
    "write_oco_latency_calibrator",
    "load_oco_latency_calibrator",
    "calibrator_lookup_ms",
]
