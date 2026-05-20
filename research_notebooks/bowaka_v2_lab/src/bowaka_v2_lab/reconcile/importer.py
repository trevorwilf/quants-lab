"""Read paper logs from a directory; normalise timestamps; flag schema drift."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from .paper_log_schema import validate_paper_record


_FILES = {
    "candidate": "candidate_events.jsonl",
    "decision":  "entry_decisions.jsonl",
    "order":     "orders.jsonl",
    "fill":      "fills.jsonl",
}


@dataclass
class PaperLogImportResult:
    candidates: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    orders: list[dict] = field(default_factory=list)
    fills: list[dict] = field(default_factory=list)
    state: dict = field(default_factory=dict)
    drift_issues: list[str] = field(default_factory=list)


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            out.append(json.loads(raw))
        except ValueError:
            continue
    return out


def _normalise_ts(rec: dict, key: str) -> None:
    v = rec.get(key)
    if v is None:
        return
    try:
        ts = pd.Timestamp(v)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        rec[key] = ts.tz_convert("UTC").isoformat()
    except Exception:
        pass


def import_paper_logs(paper_logs_dir: Path | str) -> PaperLogImportResult:
    base = Path(paper_logs_dir)
    result = PaperLogImportResult()
    result.candidates = _read_jsonl(base / _FILES["candidate"])
    result.decisions = _read_jsonl(base / _FILES["decision"])
    result.orders = _read_jsonl(base / _FILES["order"])
    result.fills = _read_jsonl(base / _FILES["fill"])
    state_path = base / "state.json"
    if state_path.is_file():
        try:
            result.state = json.loads(state_path.read_text(encoding="utf-8"))
        except ValueError:
            result.drift_issues.append("state.json: failed to parse")

    for kind, items in (
        ("candidate", result.candidates),
        ("decision", result.decisions),
        ("order", result.orders),
        ("fill", result.fills),
    ):
        for i, rec in enumerate(items):
            issues = validate_paper_record(kind, rec)
            for iss in issues:
                result.drift_issues.append(f"{kind}[{i}]: {iss}")
            # Normalise the canonical timestamp for the kind.
            if kind == "candidate":
                _normalise_ts(rec, "scan_timestamp")
            elif kind == "decision":
                _normalise_ts(rec, "decision_timestamp")
            elif kind == "order":
                _normalise_ts(rec, "submit_timestamp")
            elif kind == "fill":
                _normalise_ts(rec, "fill_timestamp")
    return result
