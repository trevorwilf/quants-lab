"""Dependency direction: marketdata/ imports neither strategy lab."""
from __future__ import annotations

from pathlib import Path

import bowaka_common.marketdata as md


def test_marketdata_imports_no_strategy_lab():
    md_dir = Path(md.__file__).parent
    offenders: list[tuple[str, str]] = []
    for py in sorted(md_dir.rglob("*.py")):
        src = py.read_text(encoding="utf-8")
        for needle in (
            "import bowaka_lab",
            "from bowaka_lab",
            "import bowaka_v2_lab",
            "from bowaka_v2_lab",
        ):
            if needle in src:
                offenders.append((py.name, needle))
    assert not offenders, f"marketdata must not import a strategy lab: {offenders}"
