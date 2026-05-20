"""All 36 checklist items registered; each is callable."""
from __future__ import annotations

from bowaka_v2_lab.promotion.checklist import (
    QUANT_REVIEWER_CHECKLIST,
    SOFTWARE_ENGINEER_CHECKLIST,
    STRATEGY_OWNER_CHECKLIST,
)


def test_quant_reviewer_has_15_items() -> None:
    assert len(QUANT_REVIEWER_CHECKLIST) == 15


def test_software_engineer_has_15_items() -> None:
    assert len(SOFTWARE_ENGINEER_CHECKLIST) == 15


def test_strategy_owner_has_6_items() -> None:
    assert len(STRATEGY_OWNER_CHECKLIST) == 6


def test_every_item_is_callable() -> None:
    for d in (QUANT_REVIEWER_CHECKLIST, SOFTWARE_ENGINEER_CHECKLIST, STRATEGY_OWNER_CHECKLIST):
        for name, fn in d.items():
            assert callable(fn), f"checklist item {name} is not callable"
