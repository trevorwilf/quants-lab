"""Point-in-time universe snapshot.

Per [Report §7.4]: each session must consume a universe as of that session date,
not the latest known universe. The snapshot is written to
``<data_root>/universe_snapshots/<YYYY-MM-DD>.json`` and is the input to the
scanner's evaluation loop.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from ..config.paths import BowakaV2Paths
from ..scanner.universe_builder import build_universe_snapshot, write_universe_snapshot as _write_snapshot_to_path
from ..utils.atomic_io import atomic_write_json


def build_pit_universe_snapshot(
    *,
    asset_master: pd.DataFrame,
    daily_baselines: pd.DataFrame | None,
    cfg: Mapping[str, Any],
    session_date: _dt.date,
) -> dict[str, Any]:
    """Build a PIT snapshot for ``session_date``.

    Excludes ETFs / warrants / SPACs / preferred per the universe filter
    ``exclude_pattern_class=True`` (default).
    """
    return build_universe_snapshot(
        asset_master=asset_master,
        daily_baselines=daily_baselines,
        cfg=cfg,
        session_date=session_date,
    )


def write_universe_snapshot(
    snapshot: Mapping[str, Any],
    *,
    paths: BowakaV2Paths,
) -> Path:
    paths.assert_strategy_isolation()
    sd = snapshot.get("session_date") or _dt.date.today().isoformat()
    out = Path(paths.data_root) / "universe_snapshots" / f"{sd}.json"
    atomic_write_json(out, dict(snapshot))
    return out
