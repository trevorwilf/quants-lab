"""Read paper logs from a directory; normalise timestamps; flag schema drift.

Two readers live here:

- :func:`import_paper_logs` — the **Phase-7** dict reader for the original
  ``candidate_events.jsonl`` / ``entry_decisions.jsonl`` / ``orders.jsonl`` /
  ``fills.jsonl`` file set. Unchanged.
- :func:`import_paper_event_logs` — the **realism remediation 2 Phase 9**
  typed reader. Reads the expanded event taxonomy from one paper-session
  directory (``paper_candidates.jsonl``, ``paper_decisions.jsonl``,
  ``paper_parent_submits.jsonl``, ``paper_parent_acks.jsonl``,
  ``paper_parent_fills.jsonl``, ``paper_oco_attempts.jsonl``,
  ``paper_oco_attached.jsonl``, ``paper_child_fills.jsonl``,
  ``paper_position_closes.jsonl``, ``paper_daily_summary.jsonl``), validates
  each row against the matching Pydantic model, sorts by timestamp and stamps
  ``source_log_file`` on every record.

When :func:`import_paper_event_logs` is called with ``paper_logs_root=None``,
the reader falls back to ``$BOWAKA_V2_PAPER_LOGS_ROOT`` so the CLI / tests do
not have to thread the path explicitly. The Phase-9 reader never fabricates
paper data — a missing directory raises ``PaperLogsNotFoundError``.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Optional

import pandas as pd
from pydantic import ValidationError

from .paper_log_schema import (
    PAPER_EVENT_MODELS,
    _PaperEventBase,
    validate_paper_record,
)


# --------------------------------------------------------------------------
# Phase-7 dict-based reader (unchanged).
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# Realism remediation 2 Phase 9 — typed event reader.
# --------------------------------------------------------------------------
class PaperLogsNotFoundError(FileNotFoundError):
    """Raised when no paper-logs directory can be resolved by the Phase-9 reader."""


#: Mapping from Phase-9 event ``kind`` to the JSONL file it lives in.
PAPER_EVENT_FILES: dict[str, str] = {
    "paper_candidate": "paper_candidates.jsonl",
    "paper_decision": "paper_decisions.jsonl",
    "paper_parent_submit": "paper_parent_submits.jsonl",
    "paper_parent_ack": "paper_parent_acks.jsonl",
    "paper_parent_fill": "paper_parent_fills.jsonl",
    "paper_oco_attempt": "paper_oco_attempts.jsonl",
    "paper_oco_attached": "paper_oco_attached.jsonl",
    "paper_child_fill": "paper_child_fills.jsonl",
    "paper_position_close": "paper_position_closes.jsonl",
    "paper_daily_summary": "paper_daily_summary.jsonl",
}


@dataclass
class PaperEventImportResult:
    """All Phase-9 paper events for one session directory.

    ``events_by_kind`` maps ``kind`` → list of validated typed events sorted by
    timestamp. ``all_events`` is the flat globally-sorted list (used by the
    replay / calibration utilities). ``drift_issues`` records every malformed
    row so the caller can surface them (the reader never crashes on one bad row,
    unless ``strict=True`` is passed).
    """

    paper_logs_root: Path
    events_by_kind: dict[str, list[_PaperEventBase]] = field(default_factory=dict)
    all_events: list[_PaperEventBase] = field(default_factory=list)
    drift_issues: list[str] = field(default_factory=list)
    n_events: int = 0

    def by_kind(self, kind: str) -> list[_PaperEventBase]:
        return self.events_by_kind.get(kind, [])


def _ts_sort_key(ev: _PaperEventBase) -> str:
    """Sort key for an event — falls back to an empty string when the ts is missing."""
    return str(ev.timestamp or "")


def resolve_paper_logs_root(paper_logs_root: Path | str | None) -> Path:
    """Resolve the paper-logs root from a path, the env var, or raise.

    Precedence: explicit ``paper_logs_root`` > ``$BOWAKA_V2_PAPER_LOGS_ROOT``.
    A missing or non-directory path raises :class:`PaperLogsNotFoundError` —
    the Phase-9 reader never fabricates paper data (operator constraint).
    """
    candidate = paper_logs_root or os.environ.get("BOWAKA_V2_PAPER_LOGS_ROOT")
    if not candidate:
        raise PaperLogsNotFoundError(
            "no paper-logs root supplied and $BOWAKA_V2_PAPER_LOGS_ROOT is unset"
        )
    root = Path(candidate)
    if not root.is_dir():
        raise PaperLogsNotFoundError(f"paper-logs root not a directory: {root}")
    return root


def import_paper_event_logs(
    paper_logs_root: Path | str | None = None,
    *,
    session_date: Optional[str] = None,
    strict: bool = False,
) -> PaperEventImportResult:
    """Read + validate the Phase-9 paper event logs from one session directory.

    Parameters
    ----------
    paper_logs_root:
        Directory holding the per-event JSONL files. ``None`` falls back to
        ``$BOWAKA_V2_PAPER_LOGS_ROOT``; both absent / not-a-directory raises
        :class:`PaperLogsNotFoundError` (the reader never fabricates paper data).
    session_date:
        Optional ISO date — when given, every record whose ``session_date`` or
        ``timestamp`` resolves to a different date is filtered out.
    strict:
        When True, the first malformed row raises
        :class:`pydantic.ValidationError`. When False (the default), malformed
        rows are dropped and recorded on ``drift_issues`` so the caller can
        surface them.

    Returns
    -------
    PaperEventImportResult
        Per-kind validated events sorted by ``timestamp`` plus a flat globally-
        sorted ``all_events`` list. ``source_log_file`` is stamped on every
        record.
    """
    root = resolve_paper_logs_root(paper_logs_root)

    out = PaperEventImportResult(paper_logs_root=root)
    for kind, filename in PAPER_EVENT_FILES.items():
        path = root / filename
        rows = _read_jsonl(path) if path.is_file() else []
        validated: list[_PaperEventBase] = []
        model = PAPER_EVENT_MODELS[kind]
        for i, raw in enumerate(rows):
            if not isinstance(raw, dict):
                out.drift_issues.append(f"{filename}[{i}]: row is not a JSON object")
                if strict:
                    raise ValidationError.from_exception_data(
                        title=kind, line_errors=[{
                            "type": "value_error", "loc": (filename, i),
                            "msg": "row is not a JSON object", "input": raw,
                        }],
                    )
                continue
            # Stamp source_log_file BEFORE validation so it survives even if
            # the row carries its own (we trust the importer over the producer).
            raw = dict(raw)
            raw["source_log_file"] = filename
            # Normalise the common timestamp keys to UTC ISO strings.
            for ts_key in (
                "timestamp", "scan_timestamp", "decision_timestamp",
                "submit_timestamp", "ack_timestamp", "fill_timestamp",
                "attempt_timestamp", "attached_timestamp", "exit_timestamp",
                "end_of_day_timestamp",
            ):
                _normalise_ts(raw, ts_key)
            try:
                event = model.model_validate(raw)
            except ValidationError as e:
                out.drift_issues.append(f"{filename}[{i}]: {e.errors()[0]['msg']}")
                if strict:
                    raise
                continue
            # Apply the session-date filter, if any.
            if session_date is not None and not _event_in_session(event, session_date):
                continue
            validated.append(event)
        validated.sort(key=_ts_sort_key)
        out.events_by_kind[kind] = validated
    out.all_events = sorted(
        (ev for evs in out.events_by_kind.values() for ev in evs),
        key=_ts_sort_key,
    )
    out.n_events = len(out.all_events)
    return out


def _event_in_session(event: _PaperEventBase, session_date: str) -> bool:
    """True iff ``event`` belongs to ``session_date`` (by session_date or ts day)."""
    sd = getattr(event, "session_date", None)
    if sd is not None:
        return str(sd) == session_date
    ts = event.timestamp
    if ts is None:
        return True  # no way to filter — keep it
    try:
        return pd.Timestamp(ts).date().isoformat() == session_date
    except Exception:  # noqa: BLE001
        return True


__all__ = [
    # Phase-7 reader.
    "import_paper_logs",
    "PaperLogImportResult",
    # Phase-9 typed reader.
    "PaperEventImportResult",
    "PaperLogsNotFoundError",
    "PAPER_EVENT_FILES",
    "import_paper_event_logs",
    "resolve_paper_logs_root",
]
