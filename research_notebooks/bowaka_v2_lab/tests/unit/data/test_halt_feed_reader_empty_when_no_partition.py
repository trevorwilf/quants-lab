"""Phase 5 (audit 2026-05-29 §9 Phase 7) — halt feed reader empty on no partition."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from bowaka_v2_lab.data.halt_feed import read_halt_events


def test_read_halt_events_empty_when_no_partition(tmp_path: Path) -> None:
    events = read_halt_events(tmp_path, "AAA", dt.date(2024, 9, 3), dt.date(2024, 9, 4))
    assert events == []
