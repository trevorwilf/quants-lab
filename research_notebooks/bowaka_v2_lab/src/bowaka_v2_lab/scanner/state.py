"""Scanner state I/O via ``BowakaV2Paths``.

Replaces the v2 archive's module-global state path (lines 140-170 of
``bowaka_intraday_scanner.py``) with a small store keyed on ``BowakaV2Paths``
so v2-lab callers cannot accidentally write to v1 paths or the source
archive's ``scripts/data/bowaka_v2`` tree ([Report §15.1 P0]).
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from ..config.paths import BowakaV2Paths


_STATE_BASENAME = "scanner_state.json"


def _empty_state(today_iso: str) -> dict[str, Any]:
    return {
        "session_date": today_iso,
        "entered_symbols_today": [],
        "in_play_pool": {},
        "scanner_last_run_ts": None,
    }


class ScannerStateStore:
    """File-backed scanner state, parameterised on ``BowakaV2Paths``."""

    def __init__(self, paths: BowakaV2Paths) -> None:
        paths.assert_strategy_isolation()
        self._paths = paths
        self._state_path = paths.artifact_root / "scanner" / _STATE_BASENAME

    @property
    def state_path(self) -> Path:
        return self._state_path

    def load_or_init(self, today_iso: str) -> dict[str, Any]:
        if not self._state_path.exists():
            return _empty_state(today_iso)
        try:
            s = json.loads(self._state_path.read_text(encoding="utf-8"))
        except Exception:
            return _empty_state(today_iso)
        if s.get("session_date") != today_iso:
            return _empty_state(today_iso)
        return s

    def save(self, state: dict[str, Any]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            prefix=_STATE_BASENAME + ".", dir=str(self._state_path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(state, fh, default=str, indent=2, sort_keys=True)
            os.replace(tmp, self._state_path)
        except Exception:
            try:
                os.unlink(tmp)
            finally:
                raise

    def hydrate_entered_symbols_from_decisions(
        self, state: dict[str, Any], today_iso: str
    ) -> None:
        """Read accepted entry decisions for today and mark their symbols in state."""
        decisions_path = self._paths.artifact_root / "scanner" / "entry_decisions.jsonl"
        if not decisions_path.exists():
            return
        entered = set(state.get("entered_symbols_today") or [])
        for raw in decisions_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                ev = json.loads(raw)
            except ValueError:
                continue
            if ev.get("session_date") != today_iso:
                continue
            if ev.get("decision") != "accepted":
                continue
            sym = ev.get("symbol")
            if sym:
                entered.add(sym)
        state["entered_symbols_today"] = sorted(entered)
