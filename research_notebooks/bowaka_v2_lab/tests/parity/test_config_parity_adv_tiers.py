"""ADV-tier cap parity: lab adv_tier_cap == live adv_tier_cap.

Realism Phase 1, Task D, audit Ticket 1. The lab's
``sim.risk_gates.adv_tier_cap`` is a byte-identical port of the live
``bowaka_v2_strategy.adv_tier_cap``. This test extracts the live function's
source from the read-only mirror, ``exec``-s it in an isolated namespace, and
asserts both return identical ``(allowed, max_position_dollars)`` across an ADV
matrix using the live ADV-tier policy from the frozen contract.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Callable, Optional

import pytest

from bowaka_v2_lab import reference
from bowaka_v2_lab.sim.risk_gates import adv_tier_cap as lab_adv_tier_cap

#: ADVs straddling every tier edge (250k / 500k / 1M / 5M) + above-top.
_ADV_MATRIX = [200_000, 250_000, 300_000, 600_000, 1_200_000, 6_000_000, 25_000_000]


def _extract_live_adv_tier_cap() -> Optional[Callable]:
    """Pull *only* the ``adv_tier_cap`` function out of the live strategy source.

    The function is self-contained (builtins + ``cfg.get`` only), so it can be
    compiled in isolation without importing the whole live module. Returns
    ``None`` when the mirror source is absent.
    """
    src_path = reference.source_file("bowaka_v2_strategy.py")
    if src_path is None or not src_path.is_file():
        return None
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    func_node = next(
        (
            n
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == "adv_tier_cap"
        ),
        None,
    )
    if func_node is None:
        return None
    module = ast.Module(body=[func_node], type_ignores=[])
    ns: dict = {}
    exec(compile(module, filename=str(src_path), mode="exec"), ns)  # noqa: S102
    return ns.get("adv_tier_cap")


@pytest.fixture(scope="module")
def live_adv_tier_cap() -> Callable:
    fn = _extract_live_adv_tier_cap()
    if fn is None:
        pytest.xfail("live source absent")
    return fn


@pytest.fixture(scope="module")
def contract_risk_cfg() -> dict:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated")
    contract = reference.load_actual_contract()
    return {"risk": contract["risk"]}


@pytest.mark.parametrize("adv", _ADV_MATRIX)
def test_adv_tier_cap_matches_live(
    adv: int, live_adv_tier_cap: Callable, contract_risk_cfg: dict
) -> None:
    lab_result = lab_adv_tier_cap(adv, contract_risk_cfg)
    live_result = live_adv_tier_cap(adv, contract_risk_cfg)
    assert lab_result == live_result, (
        f"adv={adv}: lab adv_tier_cap returned {lab_result}, "
        f"live returned {live_result}"
    )


@pytest.mark.parametrize("adv", _ADV_MATRIX)
def test_adv_tier_cap_shape(adv: int, contract_risk_cfg: dict) -> None:
    """Sanity: lab adv_tier_cap returns ``(bool, float)``."""
    allowed, cap = lab_adv_tier_cap(adv, contract_risk_cfg)
    assert isinstance(allowed, bool)
    assert isinstance(cap, float)


def test_adv_below_reject_tier_is_rejected(contract_risk_cfg: dict) -> None:
    """First contract tier has ``reject_if_below: true`` at <=250k ADV."""
    allowed, cap = lab_adv_tier_cap(200_000, contract_risk_cfg)
    assert allowed is False and cap == 0.0
