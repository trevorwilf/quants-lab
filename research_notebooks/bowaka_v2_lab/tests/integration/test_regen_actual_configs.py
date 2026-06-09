"""regen-actual-configs discovers every generated config and is idempotent.

The mirror script (``mirror_bowaka_v2_source.ps1`` STEP 3) calls this to push a
refreshed contract's live screener / signal values into the shipped configs.
Two guarantees matter:

1. The GENERATED-marked configs (and ONLY those) are regenerated — hand-tuned
   ``.workstation`` / ``.matrix`` overlays carry no marker and must be left alone.
2. Re-running against the contract the configs were built from rewrites them
   byte-identically (the committed configs stay in sync with the committed
   contract), so the mirror produces a clean ``git diff`` when nothing changed.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab import reference
from bowaka_v2_lab.reference.import_config import (
    GENERATED_MARKER,
    recover_generation_args,
    regenerate_generated_configs,
)

LAB_ROOT = Path(__file__).resolve().parents[2]
SHIPPED_CONFIGS = LAB_ROOT / "configs"


def _copy_configs(tmp_path: Path) -> Path:
    dst = tmp_path / "configs"
    dst.mkdir()
    for f in SHIPPED_CONFIGS.glob("*.yml"):
        shutil.copy2(f, dst / f.name)
    return dst


def test_regen_discovers_marked_configs_and_is_byte_identical(tmp_path: Path) -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated")
    dst = _copy_configs(tmp_path)
    marker = GENERATED_MARKER.encode("utf-8")
    marked = {f.name for f in dst.glob("*.yml") if marker in f.read_bytes()}
    unmarked = {f.name for f in dst.glob("*.yml")} - marked
    assert marked, "expected at least one GENERATED-marked config to discover"
    assert unmarked, "expected hand-tuned overlays present as a negative control"
    before = {f.name: f.read_bytes() for f in dst.glob("*.yml")}

    records = regenerate_generated_configs(dst)

    # exactly the marked set was regenerated — overlays were never touched
    assert {Path(r["path"]).name for r in records} == marked
    # committed configs are in sync with the committed contract -> no changes
    changed = [r for r in records if r["changed"]]
    assert not changed, f"configs drifted from the contract — regenerate: {changed}"
    after = {f.name: f.read_bytes() for f in dst.glob("*.yml")}
    assert after == before, "regen must be byte-identical when already in sync"


def test_recover_generation_args_roundtrips(tmp_path: Path) -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated")
    dst = _copy_configs(tmp_path)
    cases = {
        "bowaka_v2_actual_iex_current_code.yml": {
            "feed": "iex", "mode": "current_code_parity",
            "purpose": "backtest", "feed_thresholds": "actual",
        },
        "bowaka_v2_actual_sip_intended_realism_optuna.yml": {
            "feed": "sip", "mode": "intended_realism",
            "purpose": "optuna", "feed_thresholds": "actual",
        },
    }
    for name, expected in cases.items():
        path = dst / name
        if not path.is_file():
            pytest.skip(f"{name} not present in shipped configs")
        doc = yaml.safe_load(path.read_bytes().decode("utf-8"))
        assert recover_generation_args(path, doc) == expected
