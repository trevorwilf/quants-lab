"""Bowaka prefilter port.

This module mirrors ``bowaka_prefilter.apply_filters`` but with two big
research-only differences:

1. **Rejected candidates are retained** with explicit rejection reasons.
   The legacy script discards rejections; the research lab needs them for
   counterfactuals on what could-have-been candidates.
2. **Gate evaluation is deterministic and exposed** — each gate produces a
   boolean column so the funnel can be inspected per symbol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd

from bowaka_lab.config.models import PrefilterConfig, UniverseConfig
from bowaka_lab.features.daily_features import (
    compute_daily_features_history,
    compute_signal_strength,
)
from bowaka_lab.features.instrument_classification import (
    classify_instrument,
)


@dataclass
class CandidateSet:
    signal_date: date
    trade_date: date
    candidates: pd.DataFrame
    all_decisions: pd.DataFrame
    metadata: dict[str, Any] = field(default_factory=dict)


_MIN_GATE_SPECS = (
    ("rvol_min", "rvol"),
    ("atr_pct_min", "atr_pct"),
    ("range_expansion_min", "range_expansion"),
    ("close_location_min", "close_location"),
    ("ema_distance_min", "ema_distance"),
    ("ema_slope_min", "ema_slope"),
)
_MAX_GATE_SPECS = (
    ("rvol_max", "rvol"),
    ("range_expansion_max", "range_expansion"),
    ("gap_pct_max", "gap_pct"),
)


def apply_prefilter(
    features: pd.DataFrame,
    cfg: PrefilterConfig,
    *,
    signal_date: date,
    trade_date: date,
    asset_snapshot: pd.DataFrame | None = None,
    universe: UniverseConfig | None = None,
) -> CandidateSet:
    """Apply universe + signal gates; retain all rows with decisions and reasons."""
    if features.empty:
        empty = pd.DataFrame()
        return CandidateSet(
            signal_date=signal_date,
            trade_date=trade_date,
            candidates=empty,
            all_decisions=empty,
            metadata={
                "n_universe_with_features": 0,
                "n_passed_universe_gates": 0,
                "n_candidates": 0,
                "n_rejected_by_signal_gates": 0,
                "n_excluded_by_instrument_class": 0,
            },
        )

    df = features.copy()
    n_total = int(df.shape[0])

    # --- Universe gates ---
    df["gate_price_min"] = df["close"] >= cfg.price_min
    df["gate_price_max"] = df["close"] <= cfg.price_max
    if cfg.avg_dollar_volume_min is not None:
        df["gate_avg_dollar_volume_min"] = df["avg_dollar_volume"] >= cfg.avg_dollar_volume_min
    if cfg.avg_dollar_volume_max is not None:
        df["gate_avg_dollar_volume_max"] = df["avg_dollar_volume"] <= cfg.avg_dollar_volume_max

    universe_gate_cols = [c for c in df.columns if c.startswith("gate_price_") or c.startswith("gate_avg_dollar")]
    passed_universe = df[universe_gate_cols].fillna(False).all(axis=1)
    n_passed_universe = int(passed_universe.sum())

    # --- Signal gates ---
    for key, col in _MIN_GATE_SPECS:
        thr = getattr(cfg, key)
        if thr is not None:
            df[f"gate_{key}"] = df[col] >= thr
    for key, col in _MAX_GATE_SPECS:
        thr = getattr(cfg, key)
        if thr is not None:
            df[f"gate_{key}"] = df[col] <= thr

    signal_gate_cols = [c for c in df.columns if c.startswith("gate_") and c not in universe_gate_cols]
    if signal_gate_cols:
        passed_signal = df[signal_gate_cols].fillna(False).all(axis=1)
    else:
        passed_signal = pd.Series(True, index=df.index)

    # --- Instrument classification ---
    blocklist = list(universe.ticker_blocklist) if universe is not None else None
    name_lookup: dict[str, str] = {}
    asset_class_lookup: dict[str, str] = {}
    if asset_snapshot is not None and not asset_snapshot.empty:
        key_col = "symbol" if "symbol" in asset_snapshot.columns else asset_snapshot.index.name
        if key_col == "symbol":
            for _, row in asset_snapshot.iterrows():
                name_lookup[str(row["symbol"])] = str(row.get("name", "") or "")
                asset_class_lookup[str(row["symbol"])] = str(row.get("asset_class", "") or "")
        else:
            for sym, row in asset_snapshot.iterrows():
                name_lookup[str(sym)] = str(row.get("name", "") or "")
                asset_class_lookup[str(sym)] = str(row.get("asset_class", "") or "")

    cls_rows: list[tuple[str, bool, str]] = []
    for sym in df.index.tolist():
        cls = classify_instrument(
            sym,
            name=name_lookup.get(sym, ""),
            asset_class=asset_class_lookup.get(sym, ""),
            ticker_blocklist=blocklist,
        )
        cls_rows.append((cls.instrument_class, cls.eligible_for_bowaka_equity_bucket, cls.classification_reason))
    df["instrument_class"] = [r[0] for r in cls_rows]
    df["eligible_for_bowaka_equity_bucket"] = [r[1] for r in cls_rows]
    df["classification_reason"] = [r[2] for r in cls_rows]

    excluded_classes: set[str] = set()
    if universe is not None:
        if universe.exclude_leveraged_etp:
            excluded_classes.add("leveraged_etp")
        if universe.exclude_inverse_etp:
            excluded_classes.add("inverse_etp")
        if universe.exclude_etn:
            excluded_classes.add("etn")
    df["gate_instrument_class"] = ~df["instrument_class"].isin(excluded_classes)

    # --- Combine ---
    all_gate_cols = [c for c in df.columns if c.startswith("gate_")]
    df["passed_prefilter"] = df[all_gate_cols].fillna(False).all(axis=1)

    df["rejection_reasons"] = df.apply(
        lambda r: [c.replace("gate_", "") for c in all_gate_cols if not bool(r[c])],
        axis=1,
    )
    df["final_decision"] = df["passed_prefilter"].map({True: "candidate", False: "rejected"})

    df["signal_strength"] = compute_signal_strength(df, cfg)
    df = df.sort_values("signal_strength", ascending=False, kind="mergesort")
    df["rank"] = range(1, len(df) + 1)

    candidates = df[df["passed_prefilter"]].copy()
    n_candidates = int(candidates.shape[0])
    n_rejected_signal = int(((~passed_signal) & passed_universe).sum())
    n_excluded_class = int((~df["gate_instrument_class"]).sum())

    meta = {
        "n_universe_with_features": n_total,
        "n_passed_universe_gates": n_passed_universe,
        "n_candidates": n_candidates,
        "n_rejected_by_signal_gates": n_rejected_signal,
        "n_excluded_by_instrument_class": n_excluded_class,
    }
    return CandidateSet(
        signal_date=signal_date,
        trade_date=trade_date,
        candidates=candidates,
        all_decisions=df,
        metadata=meta,
    )


def replay_prefilter_over_window(
    bars: pd.DataFrame,
    cfg: PrefilterConfig,
    *,
    signal_dates: list[date],
    next_session_fn,
    universe: UniverseConfig | None = None,
    asset_snapshot: pd.DataFrame | None = None,
) -> dict[date, CandidateSet]:
    """Replay the prefilter across many signal_dates in one feature pass.

    Computes daily features once over the full ``bars`` set (see
    :func:`compute_daily_features_history`), then for each ``signal_date`` in
    ``signal_dates`` slices the feature rows whose ``session_date`` equals
    that date and applies the prefilter gates. Equivalent to looping
    :func:`apply_prefilter` per-date, but ~N× faster on long windows where
    N = len(signal_dates).

    Parameters
    ----------
    bars
        Daily OHLCV DataFrame with ``symbol``, ``timestamp`` (or
        ``session_date``), ``open``, ``high``, ``low``, ``close``, ``volume``.
    cfg
        Prefilter configuration.
    signal_dates
        Sessions for which to materialise candidates.
    next_session_fn
        Callable mapping a session_date to the next trading session
        (typically ``USEquityCalendar(...).next_session``). Used to populate
        ``trade_date`` on each ``CandidateSet``.
    universe
        Optional universe config (instrument-class exclusions, blocklist).
    asset_snapshot
        Optional symbol→name/asset_class lookup for instrument classification.

    Returns
    -------
    dict[date, CandidateSet]
        One entry per ``signal_date`` that had at least one feature row.
        Signal dates with no eligible rows are absent from the dict.
    """
    if bars.empty or not signal_dates:
        return {}
    history = compute_daily_features_history(bars, cfg)
    if history.empty:
        return {}
    out: dict[date, CandidateSet] = {}
    grouped = history.groupby("session_date", sort=False)
    have_dates = set(history["session_date"].unique())
    for sd in signal_dates:
        if sd not in have_dates:
            continue
        feats = grouped.get_group(sd).copy()
        feats = feats.set_index("symbol")
        try:
            td = next_session_fn(sd)
        except Exception:
            continue
        cset = apply_prefilter(
            feats,
            cfg,
            signal_date=sd,
            trade_date=td,
            asset_snapshot=asset_snapshot,
            universe=universe,
        )
        out[sd] = cset
    return out
