"""Per-session universe artifact persistence (realism remediation Phase 3).

Writes, into ``<run_dir>/universe/``:

- ``universe_snapshot_{session_date}.parquet`` — one row per asset-master
  symbol, with ``session_date, symbol, instrument_class, venue_code, eligible,
  rejection_reasons``.
- ``universe_funnel_{session_date}.json`` — the starting count and the per-
  rejection-reason breakdown for that session.

These are the audit trail behind the per-session ``universe_hash`` recorded in
``run_manifest.json`` and every emitted candidate event.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from ..utils.atomic_io import atomic_write_json, write_parquet
from .builder import UniverseRecord, funnel, universe_hash


def _snapshot_rows(
    session_date: _dt.date, records: Mapping[str, UniverseRecord]
) -> list[dict[str, Any]]:
    """Flatten PIT records into snapshot-parquet rows (sorted by symbol)."""
    rows: list[dict[str, Any]] = []
    for symbol in sorted(records):
        r = records[symbol]
        rows.append(
            {
                "session_date": session_date.isoformat(),
                "symbol": r.symbol,
                "instrument_class": r.instrument_class,
                "venue_code": r.venue_code,
                "eligible": bool(r.eligible_for_bowaka_equity_bucket),
                # JSONL-safe scalar; the parquet column is a comma-joined string
                # so it round-trips without an object/list column.
                "rejection_reasons": ",".join(r.rejection_reasons),
            }
        )
    return rows


def write_universe_artifacts(
    run_dir: Path | str,
    universe_by_session: Mapping[_dt.date, Mapping[str, UniverseRecord]],
) -> dict[_dt.date, str]:
    """Write the per-session universe snapshot + funnel artifacts.

    Parameters
    ----------
    run_dir:
        The run directory. Artifacts land under ``run_dir / "universe"``.
    universe_by_session:
        ``{session_date: {symbol: UniverseRecord}}`` from
        :func:`builder.build_pit_universe_for_sessions`.

    Returns
    -------
    dict[date, str]
        ``{session_date: universe_hash}`` — the per-session eligible-set hash,
        for the run manifest's ``universe_hashes_by_session``.
    """
    universe_dir = Path(run_dir) / "universe"
    universe_dir.mkdir(parents=True, exist_ok=True)

    hashes: dict[_dt.date, str] = {}
    for session_date, records in universe_by_session.items():
        sd = (
            session_date
            if isinstance(session_date, _dt.date)
            else pd.Timestamp(session_date).date()
        )
        rows = _snapshot_rows(sd, records)
        snapshot_df = (
            pd.DataFrame(rows)
            if rows
            else pd.DataFrame(
                columns=[
                    "session_date",
                    "symbol",
                    "instrument_class",
                    "venue_code",
                    "eligible",
                    "rejection_reasons",
                ]
            )
        )
        write_parquet(
            universe_dir / f"universe_snapshot_{sd.isoformat()}.parquet", snapshot_df
        )

        funnel_doc = funnel(records)
        funnel_doc["session_date"] = sd.isoformat()
        funnel_doc["universe_hash"] = universe_hash(records)
        atomic_write_json(
            universe_dir / f"universe_funnel_{sd.isoformat()}.json", funnel_doc
        )
        hashes[sd] = funnel_doc["universe_hash"]
    return hashes


def compute_universe_hashes(
    universe_by_session: Mapping[_dt.date, Mapping[str, UniverseRecord]],
) -> dict[_dt.date, str]:
    """Return ``{session_date: universe_hash}`` without writing parquet/json.

    Used by ``run_backtest(artifact_mode="objective_minimal")`` (speedup §5.1
    Phase 1) — the objective needs the per-session hash for the run-manifest
    extras but does not need the snapshot/funnel files. Same hashing as
    :func:`write_universe_artifacts`; only the disk writes are skipped.
    """
    hashes: dict[_dt.date, str] = {}
    for session_date, records in universe_by_session.items():
        sd = (
            session_date
            if isinstance(session_date, _dt.date)
            else pd.Timestamp(session_date).date()
        )
        hashes[sd] = universe_hash(records)
    return hashes


__all__ = ["compute_universe_hashes", "write_universe_artifacts"]
