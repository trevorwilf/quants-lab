"""Historical scanner replay.

Iterates over ``(session, scan_ts)`` pairs, calls ``evaluate_one_scan`` for
each, and writes the run-dir artifacts:

- ``candidate_events.jsonl``
- ``candidate_events.parquet``
- ``gate_dump.parquet``
- ``scanner_summary.json``
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import pandas as pd

from ..utils.atomic_io import append_jsonl, atomic_write_json, write_parquet
from .scan_loop import ScanResult, evaluate_one_scan


def replay_scanner(
    *,
    cfg: Mapping[str, Any],
    universe_snapshot: Mapping[str, Any],
    daily_cache: pd.DataFrame | None,
    volume_curve: pd.DataFrame | None,
    scan_timestamps: Sequence[Any],
    bars_supplier: Callable[[str, Any], pd.DataFrame | None],
    run_dir: Path,
) -> dict[str, Any]:
    """Replay the scanner across a list of scan timestamps.

    Returns a summary dict with totals; per-event artifacts are written to ``run_dir``.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    events_jsonl = run_dir / "candidate_events.jsonl"
    events_parquet = run_dir / "candidate_events.parquet"
    gate_parquet = run_dir / "gate_dump.parquet"
    summary_json = run_dir / "scanner_summary.json"

    # Wipe prior events file (atomic): we overwrite per replay.
    if events_jsonl.exists():
        events_jsonl.unlink()

    # Realism Phase 4: scanner dedup memory (cooldown, per-day entry count,
    # in-play pool) is per session. Replay is a single-session call, so one
    # state dict spanning the supplied scan timestamps is correct.
    state: dict[str, Any] = {
        "entered_symbols_today": [],
        "in_play_pool": {},
        "symbol_last_emit_ts": {},
        "entries_per_symbol_today": {},
    }
    all_events: list[dict[str, Any]] = []
    all_dump: list[dict[str, Any]] = []
    scan_count = 0
    for ts in scan_timestamps:
        result = evaluate_one_scan(
            cfg=cfg,
            universe_snapshot=universe_snapshot,
            daily_cache=daily_cache,
            volume_curve=volume_curve,
            state=state,
            scan_ts=ts,
            bars_supplier=bars_supplier,
        )
        if result.emitted:
            append_jsonl(events_jsonl, result.emitted)
            all_events.extend(result.emitted)
        all_dump.extend(result.gate_dump)
        scan_count += 1

    if all_events:
        # Flatten nested dicts for parquet via pd.json_normalize.
        df_ev = pd.json_normalize(all_events, sep=".")
        write_parquet(events_parquet, df_ev)
    if all_dump:
        df_dump = pd.json_normalize(all_dump, sep=".")
        write_parquet(gate_parquet, df_dump)

    summary = {
        "scan_count": scan_count,
        "emitted_count": len(all_events),
        "gate_dump_rows": len(all_dump),
        "events_jsonl_path": str(events_jsonl),
        "events_parquet_path": str(events_parquet) if all_events else None,
        "gate_dump_parquet_path": str(gate_parquet) if all_dump else None,
    }
    atomic_write_json(summary_json, summary)
    return summary
