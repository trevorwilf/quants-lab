"""Each callable returns (status, evidence) — evidence is a dict (Phase 8 Task 4)."""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.promotion.checklist import (
    QUANT_REVIEWER_CHECKLIST,
    SOFTWARE_ENGINEER_CHECKLIST,
    STRATEGY_OWNER_CHECKLIST,
)


def test_shape_on_empty_run_dir(tmp_path: Path) -> None:
    rd = tmp_path / "empty_run"
    rd.mkdir()
    for d in (QUANT_REVIEWER_CHECKLIST, SOFTWARE_ENGINEER_CHECKLIST, STRATEGY_OWNER_CHECKLIST):
        for name, fn in d.items():
            result = fn(rd)
            assert isinstance(result, tuple) and len(result) == 2, name
            status, evidence = result
            assert status in ("pass", "fail", "unknown"), f"{name}: bad status {status}"
            # Realism Phase 8 Task 4: every check records structured evidence.
            assert isinstance(evidence, dict), f"{name}: evidence must be a dict"
