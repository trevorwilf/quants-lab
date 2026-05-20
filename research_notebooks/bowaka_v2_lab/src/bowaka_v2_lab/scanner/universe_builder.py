"""Universe-builder adapter for v2.

Port of ``bowaka_universe_builder.py`` adapted for historical / point-in-time
backfill (Phase 4 calls per-session). Reads asset metadata from a supplied
asset master and applies v2 universe filters:

- price within ``[min_price, max_price]``
- avg_dollar_volume_20d >= ``min_adv_dollars``
- instrument_class in ``asset_classes`` (default ``["operating_equity"]``)
- ETFs / pattern-class instruments excluded when ``exclude_pattern_class``

Returns a universe snapshot suitable for ``scanner.scan_loop.evaluate_one_scan``.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from ..utils.atomic_io import atomic_write_json


def _hash_universe(symbols: list[dict[str, Any]]) -> str:
    payload = json.dumps(sorted(symbols, key=lambda d: d.get("symbol", "")), sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()[:16]


def build_universe_snapshot(
    *,
    asset_master: pd.DataFrame,
    daily_baselines: pd.DataFrame | None,
    cfg: Mapping[str, Any],
    session_date: _dt.date,
) -> dict[str, Any]:
    """Build a v2 universe snapshot for a given session date.

    ``asset_master`` columns expected: ``symbol``, ``exchange``,
    ``venue_code``, ``instrument_class``, ``eligible_for_bowaka_equity_bucket``.
    ``daily_baselines`` columns expected: ``symbol``, ``prior_close``,
    ``avg_dollar_volume_20d``.
    """
    universe_cfg = cfg.get("universe") or {}
    asset_classes = set(universe_cfg.get("asset_classes", ["operating_equity"]))
    min_price = float(universe_cfg.get("min_price", 1.0))
    max_price = float(universe_cfg.get("max_price", 1000.0))
    min_adv = float(universe_cfg.get("min_adv_dollars", 1_000_000))
    exclude_pattern = bool(universe_cfg.get("exclude_pattern_class", True))
    explicit_symbols = universe_cfg.get("symbols")

    df = asset_master.copy()
    if explicit_symbols:
        df = df[df["symbol"].isin(set(explicit_symbols))]
    if exclude_pattern:
        if "instrument_class" in df.columns:
            df = df[df["instrument_class"].isin(asset_classes)]
    if daily_baselines is not None and not daily_baselines.empty:
        base = daily_baselines.set_index("symbol")
        df = df.set_index("symbol").join(
            base[["prior_close", "avg_dollar_volume_20d"]], how="left"
        ).reset_index()
        df = df[
            (df["prior_close"].fillna(0) >= min_price)
            & (df["prior_close"].fillna(0) <= max_price)
            & (df["avg_dollar_volume_20d"].fillna(0) >= min_adv)
        ]

    symbols: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        symbols.append({
            "symbol": row["symbol"],
            "exchange": row.get("exchange"),
            "venue_code": row.get("venue_code") or "XNAS",
            "instrument_class": row.get("instrument_class", "operating_equity"),
            "eligible_for_bowaka_equity_bucket": bool(
                row.get("eligible_for_bowaka_equity_bucket", True)
            ),
        })
    snapshot = {
        "session_date": session_date.isoformat(),
        "as_of": _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
        "symbols": symbols,
        "universe_hash": _hash_universe(symbols),
        "filters": {
            "asset_classes": sorted(asset_classes),
            "min_price": min_price,
            "max_price": max_price,
            "min_adv_dollars": min_adv,
            "exclude_pattern_class": exclude_pattern,
        },
    }
    return snapshot


def write_universe_snapshot(snapshot: Mapping[str, Any], out_path: Path) -> None:
    atomic_write_json(Path(out_path), dict(snapshot))
