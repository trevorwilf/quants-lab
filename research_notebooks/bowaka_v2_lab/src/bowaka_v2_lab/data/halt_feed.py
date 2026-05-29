"""LULD / trading-halt feed reader (audit 2026-05-29 §9 Phase 7 — scaffolding).

The schema + reader exist now so that when SIP-era halt data lands under the
lake's ``halt_events`` partition the simulator can consume it without a code
change. On today's IEX-only lake the partition is absent and
:func:`read_halt_events` returns ``[]`` (the no-data case).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd


@dataclass(frozen=True)
class HaltEvent:
    symbol: str
    ts_start: pd.Timestamp
    ts_end: Optional[pd.Timestamp]   # None = still halted at last observation
    reason: str                      # "LULD" | "T1" | "T2" | "T5" | ...


def halt_events_symbol_dir(lake_root: Path | str, symbol: str, *, vendor: str = "alpaca") -> Path:
    """``halt_events/vendor=<vendor>/symbol=<symbol>`` under the lake root."""
    return Path(lake_root) / "halt_events" / f"vendor={vendor}" / f"symbol={symbol}"


def read_halt_events(
    lake_root: Path | str,
    symbol: str,
    start: Any,
    end: Any,
    *,
    vendor: str = "alpaca",
) -> list[HaltEvent]:
    """Read halt events for ``symbol`` in ``[start, end]`` from the lake.

    Reads every ``year=*/month=*/part.parquet`` under the symbol's halt-events
    directory and returns the events overlapping the window. Returns ``[]`` when
    no halt-event partition exists (the IEX-only case today).
    """
    sym_dir = halt_events_symbol_dir(lake_root, symbol, vendor=vendor)
    if not sym_dir.is_dir():
        return []
    parts = sorted(sym_dir.glob("year=*/month=*/part.parquet"))
    if not parts:
        return []
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if start_ts.tzinfo is None:
        start_ts = start_ts.tz_localize("UTC")
    if end_ts.tzinfo is None:
        end_ts = end_ts.tz_localize("UTC")
    out: list[HaltEvent] = []
    for part in parts:
        try:
            df = pd.read_parquet(part)
        except Exception:  # noqa: BLE001 — a corrupt partition is no-data
            continue
        for _, row in df.iterrows():
            ts_start = pd.Timestamp(row.get("ts_start"))
            if ts_start.tzinfo is None:
                ts_start = ts_start.tz_localize("UTC")
            raw_end = row.get("ts_end")
            ts_end = None
            if raw_end is not None and not pd.isna(raw_end):
                ts_end = pd.Timestamp(raw_end)
                if ts_end.tzinfo is None:
                    ts_end = ts_end.tz_localize("UTC")
            window_end = ts_end if ts_end is not None else ts_start
            if window_end < start_ts or ts_start > end_ts:
                continue
            out.append(HaltEvent(
                symbol=str(row.get("symbol", symbol)),
                ts_start=ts_start, ts_end=ts_end,
                reason=str(row.get("reason", "UNKNOWN")),
            ))
    out.sort(key=lambda e: e.ts_start)
    return out


__all__ = ["HaltEvent", "read_halt_events", "halt_events_symbol_dir"]
