"""Bowaka paper-trading log importer.

Reads:

- ``in_play_candidates.json`` — daily candidate file (schema v2).
- ``daily_summary.jsonl`` — one record per opened/closed event.
- ``trade_ledger.jsonl`` — broker event ledger (schema v1+).
- ``trades/BOWAKA-*.jsonl`` — per-trade event logs.

Each loader returns a normalized pandas DataFrame. Malformed lines are NOT
silently dropped: they are recorded in an ``error_rows`` table with file path
and line number so audits can flag corruption (see ``[Report §E.1]``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class ImportResult:
    """Wraps successful + error rows produced by a single loader call."""

    df: pd.DataFrame
    errors: pd.DataFrame


def _iter_jsonl(path: Path) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    errors: list[dict] = []
    if not path.exists():
        return rows, errors
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception as exc:
            errors.append({"path": str(path), "lineno": lineno, "raw": line, "error": str(exc)})
    return rows, errors


def load_candidate_file(path: Path | str) -> dict[str, Any]:
    """Load a candidate JSON (schema v2) and return its parsed content."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def load_daily_summary(path: Path | str) -> ImportResult:
    rows, errors = _iter_jsonl(Path(path))
    if not rows:
        return ImportResult(pd.DataFrame(), pd.DataFrame(errors))
    df = pd.json_normalize(rows)
    if "entry_timestamp" in df.columns:
        df["entry_timestamp"] = pd.to_datetime(df["entry_timestamp"], errors="coerce", utc=True)
    if "exit_timestamp" in df.columns:
        df["exit_timestamp"] = pd.to_datetime(df["exit_timestamp"], errors="coerce", utc=True)
    return ImportResult(df, pd.DataFrame(errors))


def load_trade_ledger(path: Path | str) -> ImportResult:
    rows, errors = _iter_jsonl(Path(path))
    if not rows:
        return ImportResult(pd.DataFrame(), pd.DataFrame(errors))
    df = pd.json_normalize(rows, sep=".")
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce", utc=True)
    return ImportResult(df, pd.DataFrame(errors))


def load_per_trade_logs(trades_dir: Path | str) -> ImportResult:
    """Load every ``BOWAKA-*.jsonl`` under ``trades_dir``."""
    trades_dir = Path(trades_dir)
    rows: list[dict] = []
    errors: list[dict] = []
    if not trades_dir.exists():
        return ImportResult(pd.DataFrame(), pd.DataFrame())
    for path in sorted(trades_dir.glob("BOWAKA-*.jsonl")):
        r, e = _iter_jsonl(path)
        for row in r:
            row.setdefault("source_file", path.name)
            rows.append(row)
        errors.extend(e)
    if not rows:
        return ImportResult(pd.DataFrame(), pd.DataFrame(errors))
    df = pd.json_normalize(rows)
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce", utc=True)
    return ImportResult(df, pd.DataFrame(errors))
