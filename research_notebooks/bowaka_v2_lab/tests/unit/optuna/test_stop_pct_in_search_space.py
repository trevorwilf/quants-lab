"""Phase 0 — stop_pct stays tunable across the new contract value.

The contract was tightened to 0.025 on 2026-05-26 but the operator wants
``exits.stop_pct`` to remain a tunable knob in the Optuna search. The shipped
range ``("uniform", 0.01, 0.20)`` brackets 0.025 cleanly; this test pins
both the presence of the parameter and that the contract value is inside the
range.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab import reference
from bowaka_v2_lab.optuna.search_space import resolve_search_space


def test_stop_pct_appears_in_resolved_search_space() -> None:
    spec = resolve_search_space({})
    assert "exits.stop_pct" in spec, (
        "exits.stop_pct must remain in the search space — operator decision "
        "2026-05-26: keep it tunable even after the contract tightened to 0.025."
    )


def test_search_space_range_brackets_new_contract_value() -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated")
    spec = resolve_search_space({})
    kind, lo, hi = spec["exits.stop_pct"]
    assert kind == "uniform", f"expected ('uniform', lo, hi), got {(kind, lo, hi)!r}"
    contract_value = reference.load_actual_contract()["exits"]["stop_pct"]
    assert lo <= contract_value <= hi, (
        f"contract.exits.stop_pct={contract_value!r} is OUTSIDE the Optuna "
        f"search range ({lo!r}, {hi!r}) — Phase 0 §5 requires the range to "
        f"bracket the new live value."
    )
