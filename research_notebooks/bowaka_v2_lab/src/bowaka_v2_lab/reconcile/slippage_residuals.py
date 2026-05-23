"""Slippage residuals + the realism remediation 2 Phase 9 calibrator.

The Phase-7 ``compute_slippage_residuals`` helper computes per-trade paper-vs-
sim slippage residuals as a DataFrame (unchanged).

The Phase-9 calibrator fits a residual model binned by
``(spread_bin, adv_bin, volatility_bin)`` and persists it as a JSON
calibration artifact loadable by :mod:`bowaka_v2_lab.sim.fills`. When
``execution.calibration_artifact`` is set in a config, the T4 calibrated fill
tier reads the artifact and applies the mean-residual bps shift for the
matching bin to the modelled fill price. T4 is opt-in only — the default
tiers (T0-T3) ignore the calibration artifact and behave exactly as before.

The fitted artifact format is intentionally small and human-readable:

.. code-block:: json

    {
      "vintage": "2024-09-03",
      "n_observations": 5,
      "bins": {
        "spread": [0.0, 5.0, 15.0, 50.0],
        "adv": [0.0, 250000.0, 1000000.0, 5000000.0],
        "volatility": [0.0, 0.5, 1.0, 2.0]
      },
      "residual_bps_by_bin": {
        "0|0|0": {"n": 2, "mean_bps": 2.5, "median_bps": 2.5},
        ...
      },
      "default_residual_bps": 0.0
    }

The mean_bps value is the **paper minus sim** residual: positive means paper
fills WORSE than the sim's model (a real-broker disadvantage); applying the
residual to the sim shifts the lab fill price by that bps amount.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

import pandas as pd


# --------------------------------------------------------------------------
# Phase-7 helper (unchanged).
# --------------------------------------------------------------------------
def compute_slippage_residuals(
    paper_fills: list[dict],
    sim_fills: list[dict],
) -> pd.DataFrame:
    """Join paper fills to sim fills by (symbol, parent_order_id) and compute residuals.

    residual = paper_fill_price - sim_fill_price  (positive = paper worse for buy)
    """
    if not paper_fills or not sim_fills:
        return pd.DataFrame(columns=["symbol", "paper_fill", "sim_fill", "residual"])
    df_p = pd.DataFrame(paper_fills).rename(columns={"avg_fill_price": "paper_fill"})
    df_s = pd.DataFrame(sim_fills).rename(columns={"avg_fill_price": "sim_fill"})
    join_keys: list[str] = []
    if "parent_order_id" in df_p.columns and "parent_order_id" in df_s.columns:
        join_keys.append("parent_order_id")
    if "symbol" in df_p.columns and "symbol" in df_s.columns:
        join_keys.append("symbol")
    if not join_keys:
        return pd.DataFrame(columns=["symbol", "paper_fill", "sim_fill", "residual"])
    merged = df_p.merge(df_s[join_keys + ["sim_fill"]], on=join_keys, how="inner")
    merged["residual"] = merged["paper_fill"] - merged["sim_fill"]
    cols = [c for c in ("symbol", "parent_order_id", "paper_fill", "sim_fill", "residual") if c in merged.columns]
    return merged[cols]


# --------------------------------------------------------------------------
# Realism remediation 2 Phase 9 — binned slippage calibrator.
# --------------------------------------------------------------------------
#: Default bin edges. The right-most edge is the implicit cap; values above it
#: are bucketed into the top bin.
DEFAULT_SPREAD_BIN_EDGES_BPS: tuple[float, ...] = (0.0, 5.0, 15.0, 50.0)
DEFAULT_ADV_BIN_EDGES_SHARES: tuple[float, ...] = (0.0, 250_000.0, 1_000_000.0, 5_000_000.0)
DEFAULT_VOL_BIN_EDGES: tuple[float, ...] = (0.0, 0.5, 1.0, 2.0)


def _bucket(value: Optional[float], edges: Sequence[float]) -> int:
    """Bucket ``value`` into ``edges``; ``None`` / negative → bin 0."""
    if value is None or not isinstance(value, (int, float)) or value != value:
        return 0
    v = float(value)
    if v <= edges[0]:
        return 0
    # Find the largest edge index ``i`` whose edge[i] <= v.
    idx = 0
    for i, e in enumerate(edges):
        if v >= e:
            idx = i
    return idx


@dataclass
class SlippageCalibratorArtifact:
    """In-memory representation of a fitted slippage calibrator."""

    vintage: str
    n_observations: int
    bins: dict[str, list[float]]
    residual_bps_by_bin: dict[str, dict[str, float]]
    default_residual_bps: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "vintage": self.vintage,
            "n_observations": int(self.n_observations),
            "bins": dict(self.bins),
            "residual_bps_by_bin": dict(self.residual_bps_by_bin),
            "default_residual_bps": float(self.default_residual_bps),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SlippageCalibratorArtifact":
        return cls(
            vintage=str(data.get("vintage") or ""),
            n_observations=int(data.get("n_observations") or 0),
            bins={k: [float(x) for x in v] for k, v in (data.get("bins") or {}).items()},
            residual_bps_by_bin={
                str(k): {kk: float(vv) for kk, vv in v.items()}
                for k, v in (data.get("residual_bps_by_bin") or {}).items()
            },
            default_residual_bps=float(data.get("default_residual_bps") or 0.0),
        )


@dataclass
class FillFeatureRow:
    """One paired paper-vs-sim observation for the calibrator.

    ``paper_price`` and ``sim_price`` are the two fill prices (same symbol +
    direction); ``spread_bps`` / ``adv_shares`` / ``volatility`` are the
    binning features captured at order-submit time.
    """

    paper_price: float
    sim_price: float
    spread_bps: Optional[float] = None
    adv_shares: Optional[float] = None
    volatility: Optional[float] = None
    side: str = "buy"  # buy or sell — controls residual sign


def _bin_key(
    spread_bps: Optional[float],
    adv_shares: Optional[float],
    volatility: Optional[float],
    *,
    spread_edges: Sequence[float],
    adv_edges: Sequence[float],
    vol_edges: Sequence[float],
) -> str:
    """Compose the bin key for a single observation."""
    s = _bucket(spread_bps, spread_edges)
    a = _bucket(adv_shares, adv_edges)
    v = _bucket(volatility, vol_edges)
    return f"{s}|{a}|{v}"


def fit_slippage_calibrator(
    observations: Iterable[FillFeatureRow],
    *,
    vintage: str,
    spread_edges: Sequence[float] = DEFAULT_SPREAD_BIN_EDGES_BPS,
    adv_edges: Sequence[float] = DEFAULT_ADV_BIN_EDGES_SHARES,
    vol_edges: Sequence[float] = DEFAULT_VOL_BIN_EDGES,
) -> SlippageCalibratorArtifact:
    """Fit a per-(spread, ADV, volatility)-bin slippage residual artifact.

    For each bin, the artifact stores ``n``, ``mean_bps`` and ``median_bps``
    over the observations that fall in it. The residual is computed signed
    against the trade side so paper-worse-than-sim is always positive::

        for a BUY:  bps = (paper_price - sim_price) / sim_price * 10_000
        for a SELL: bps = (sim_price - paper_price) / sim_price * 10_000

    ``default_residual_bps`` is the global mean across all observations — used
    when a fill at runtime falls in a bin the calibrator never saw.
    """
    obs = list(observations)
    per_bin: dict[str, list[float]] = {}
    all_bps: list[float] = []
    for row in obs:
        if row.sim_price == 0:
            continue
        if str(row.side).lower() == "sell":
            bps = (row.sim_price - row.paper_price) / row.sim_price * 10_000.0
        else:
            bps = (row.paper_price - row.sim_price) / row.sim_price * 10_000.0
        all_bps.append(bps)
        key = _bin_key(
            row.spread_bps, row.adv_shares, row.volatility,
            spread_edges=spread_edges, adv_edges=adv_edges, vol_edges=vol_edges,
        )
        per_bin.setdefault(key, []).append(bps)
    summary: dict[str, dict[str, float]] = {}
    for key, vals in per_bin.items():
        summary[key] = {
            "n": float(len(vals)),
            "mean_bps": round(statistics.fmean(vals), 6),
            "median_bps": round(statistics.median(vals), 6),
        }
    default = round(statistics.fmean(all_bps), 6) if all_bps else 0.0
    return SlippageCalibratorArtifact(
        vintage=str(vintage),
        n_observations=len(obs),
        bins={
            "spread": [float(x) for x in spread_edges],
            "adv": [float(x) for x in adv_edges],
            "volatility": [float(x) for x in vol_edges],
        },
        residual_bps_by_bin=summary,
        default_residual_bps=default,
    )


def write_slippage_calibrator(
    artifact: SlippageCalibratorArtifact,
    out_path: Path | str,
) -> Path:
    """Persist a fitted calibrator artifact to ``out_path``.

    Writes JSON with ``indent=2, sort_keys=True`` so the file is stable across
    runs (suitable for committing to ``artifacts/calibration/``).
    """
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(artifact.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return out


def load_slippage_calibrator(path: Path | str) -> SlippageCalibratorArtifact:
    """Load a calibrator artifact from disk.

    Raises ``FileNotFoundError`` when the file does not exist (the sim's T4
    fill path catches it and falls back to T2 with a warning).
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"slippage calibrator artifact not found: {p}")
    return SlippageCalibratorArtifact.from_dict(
        json.loads(p.read_text(encoding="utf-8"))
    )


def calibrator_lookup_bps(
    artifact: SlippageCalibratorArtifact,
    *,
    spread_bps: Optional[float],
    adv_shares: Optional[float],
    volatility: Optional[float],
) -> float:
    """Look up the calibrated residual bps for one ``(spread, adv, vol)`` point.

    Falls back to the calibrator's ``default_residual_bps`` when the (s, a, v)
    bin is unknown.
    """
    spread_edges = artifact.bins.get("spread") or list(DEFAULT_SPREAD_BIN_EDGES_BPS)
    adv_edges = artifact.bins.get("adv") or list(DEFAULT_ADV_BIN_EDGES_SHARES)
    vol_edges = artifact.bins.get("volatility") or list(DEFAULT_VOL_BIN_EDGES)
    key = _bin_key(
        spread_bps, adv_shares, volatility,
        spread_edges=spread_edges, adv_edges=adv_edges, vol_edges=vol_edges,
    )
    bin_summary = artifact.residual_bps_by_bin.get(key)
    if bin_summary is None or float(bin_summary.get("n", 0.0)) <= 0:
        return float(artifact.default_residual_bps)
    return float(bin_summary.get("mean_bps", artifact.default_residual_bps))


__all__ = [
    # Phase-7 helper.
    "compute_slippage_residuals",
    # Phase-9 calibrator.
    "FillFeatureRow",
    "SlippageCalibratorArtifact",
    "fit_slippage_calibrator",
    "write_slippage_calibrator",
    "load_slippage_calibrator",
    "calibrator_lookup_bps",
    "DEFAULT_SPREAD_BIN_EDGES_BPS",
    "DEFAULT_ADV_BIN_EDGES_SHARES",
    "DEFAULT_VOL_BIN_EDGES",
]
