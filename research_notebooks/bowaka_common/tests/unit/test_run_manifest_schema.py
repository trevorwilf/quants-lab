"""run_manifest builder: required fields, schema_version, strategy_id required."""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_common.artifacts.run_manifest import (
    RUN_MANIFEST_SCHEMA_VERSION,
    build_run_manifest,
    validate_run_manifest,
)


def _ok_kwargs(**overrides):
    base = dict(
        strategy_id="bowaka_v2",
        run_id="20260520_bowaka_v2_backtest_abcdef12_01234567",
        config_hash="cafebabecafebabe",
        dataset_hash="deadbeefdeadbeef",
        code_manifest_hash="01234567890abcde",
    )
    base.update(overrides)
    return base


def test_build_basic() -> None:
    m = build_run_manifest(**_ok_kwargs())
    assert m["schema_version"] == RUN_MANIFEST_SCHEMA_VERSION
    assert m["strategy_id"] == "bowaka_v2"
    assert m["run_id"].startswith("20260520")
    validate_run_manifest(m)


def test_missing_strategy_id_raises() -> None:
    with pytest.raises(ValueError, match="strategy_id"):
        build_run_manifest(**_ok_kwargs(strategy_id=""))


def test_missing_run_id_raises() -> None:
    with pytest.raises(ValueError, match="run_id"):
        build_run_manifest(**_ok_kwargs(run_id=""))


def test_naive_created_at_raises() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        build_run_manifest(**_ok_kwargs(created_at=_dt.datetime(2024, 1, 1, 12, 0, 0)))


def test_extras_merged_but_required_fields_protected() -> None:
    m = build_run_manifest(**_ok_kwargs(extras={"notes": "hello", "strategy_id": "OVERRIDE"}))
    assert m["notes"] == "hello"
    assert m["strategy_id"] == "bowaka_v2"  # not overridden
