"""Phase 0 (speedup report v2 §1.2) — stop_pct contract reconciliation.

This test pins the contract ``exits.stop_pct``, cross-checks the contract's
``source_sha256`` against the source-strategy mirror, and asserts every
contract-GENERATED config reads the same value.

CHANGELOG:
- 2026-05-26: live tightened stop_pct 0.08 -> 0.025.
- 2026-06-12: prod re-mirror adopting optuna winner #3155 set stop_pct to
  0.10383796823643686. NOTE the per-config check is now scoped to GENERATED
  configs only — the mirror does NOT regenerate hand-tuned .workstation/.matrix
  overlays or the smoke fixture config (they legitimately lag at 0.025 until an
  operator rebuilds them from the refreshed base; see mirror_bowaka_v2_source.ps1).
- 2026-07-06: prod re-mirror adopting paper-deploy trial #3437 (applied live
  2026-06-17) set stop_pct to 0.1896328255554003.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab import reference

_LAB_ROOT = Path(__file__).resolve().parents[2]
_CONFIGS = _LAB_ROOT / "configs"
_MIRROR_SOURCE = (
    _LAB_ROOT
    / "reference"
    / "source_strategy"
    / "scripts"
    / "bowaka_v2_config.yaml"
)

#: The contract value (paper-deploy trial #3437, prod re-mirror 2026-07-06).
_EXPECTED_STOP_PCT = 0.1896328255554003

#: Directories under ``configs/`` to ignore. ``quarantined/`` is the operator-
#: maintained "do not use" lane. ``.ipynb_checkpoints/`` is JupyterLab's local
#: checkpoint cache and is gitignored — its contents are stale by definition.
_EXCLUDE_DIRS = ("quarantined", ".ipynb_checkpoints")


def _is_lab_config(path: Path) -> bool:
    """True for non-quarantined ``configs/*.yml`` files."""
    if not path.suffix == ".yml":
        return False
    for parent in path.parents:
        if parent.name in _EXCLUDE_DIRS:
            return False
        if parent == _LAB_ROOT:
            break
    return True


def _lab_configs() -> list[Path]:
    """Every contract-GENERATED, non-quarantined ``configs/*.yml`` with stop_pct.

    Scoped to GENERATED configs (header marker) because only those are
    regenerated from the contract by mirror_bowaka_v2_source.ps1. Hand-tuned
    .workstation/.matrix overlays + the smoke fixture are operator-managed and
    legitimately lag the contract value, so they are out of scope here.
    """
    out: list[Path] = []
    for path in _CONFIGS.rglob("*.yml"):
        if not _is_lab_config(path):
            continue
        text = path.read_text(encoding="utf-8")
        if "GENERATED" not in text:
            continue
        try:
            cfg = yaml.safe_load(text)
        except Exception:
            continue
        if isinstance(cfg, dict) and "exits" in cfg and "stop_pct" in cfg["exits"]:
            out.append(path)
    return sorted(out)


@pytest.fixture(scope="module")
def contract() -> dict:
    if not reference.contract_available():
        pytest.xfail(
            "frozen contract not generated -- run `python -m bowaka_v2_lab.reference`"
        )
    return reference.load_actual_contract()


def test_contract_stop_pct_is_new_value(contract: dict) -> None:
    """The frozen contract reads stop_pct == 0.025 (post-2026-05-26)."""
    actual = contract.get("exits", {}).get("stop_pct")
    assert actual == _EXPECTED_STOP_PCT, (
        f"contract.exits.stop_pct = {actual!r}; expected {_EXPECTED_STOP_PCT!r}. "
        f"Regenerate with `python -m bowaka_v2_lab.reference`."
    )


def test_contract_source_sha_matches_mirror(contract: dict) -> None:
    """The contract's source_sha256 == sha256 of the source-strategy mirror."""
    if not _MIRROR_SOURCE.is_file():
        pytest.xfail(
            "source_strategy mirror not present in this checkout -- "
            "run mirror_bowaka_v2_source.ps1 to populate"
        )
    mirror_sha = hashlib.sha256(_MIRROR_SOURCE.read_bytes()).hexdigest()
    assert contract.get("source_sha256") == mirror_sha, (
        "contract.source_sha256 disagrees with the source-strategy mirror — "
        "regenerate with `python -m bowaka_v2_lab.reference`."
    )


@pytest.mark.parametrize(
    "config_path", _lab_configs(), ids=lambda p: p.relative_to(_LAB_ROOT).as_posix()
)
def test_every_lab_config_uses_new_stop_pct(config_path: Path) -> None:
    """Every non-quarantined ``configs/*.yml`` has exits.stop_pct == 0.025."""
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    value = cfg["exits"]["stop_pct"]
    assert value == _EXPECTED_STOP_PCT, (
        f"{config_path.relative_to(_LAB_ROOT)} has exits.stop_pct={value!r}; "
        f"expected {_EXPECTED_STOP_PCT!r}. Regenerate the CLI-built configs "
        f"with `python -m bowaka_v2_lab.cli import-actual-config ...` and "
        f"hand-edit the four workstation overlays (Phase 0 §4)."
    )
