"""The pytest config must define a non-None default timeout.

Realism remediation 2 Phase 2 (audit §P1-007): the integration / reconciliation
suite must fail deterministically on a hang instead of stalling the CI window.
A default ``timeout`` in ``[tool.pytest.ini_options]`` (pyproject.toml) guarantees
that. The lab is configured via pyproject — there must be no competing pytest.ini.
"""
from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - py310 fallback
    import tomli as tomllib  # type: ignore

_LAB_ROOT = Path(__file__).resolve().parents[2]


def _pytest_ini_options() -> dict:
    pyproject = _LAB_ROOT / "pyproject.toml"
    assert pyproject.is_file(), f"pyproject.toml not found at {pyproject}"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return data.get("tool", {}).get("pytest", {}).get("ini_options", {})


def test_pytest_config_lives_in_pyproject_not_pytest_ini() -> None:
    # A separate pytest.ini would override pyproject and silently win — the lab
    # keeps a single source of truth.
    assert not (_LAB_ROOT / "pytest.ini").exists(), (
        "pytest.ini must not exist — pytest config lives in pyproject.toml"
    )


def test_pytest_config_defines_non_none_default_timeout() -> None:
    opts = _pytest_ini_options()
    assert "timeout" in opts, "[tool.pytest.ini_options] must define `timeout`"
    timeout = opts["timeout"]
    assert timeout is not None, "default `timeout` must not be None"
    assert isinstance(timeout, int), f"`timeout` must be an int, got {type(timeout)!r}"
    assert timeout > 0, f"default `timeout` must be positive, got {timeout}"


def test_pytest_config_uses_thread_timeout_method() -> None:
    # The thread method prints a stack trace on timeout (debuggable hangs).
    opts = _pytest_ini_options()
    assert opts.get("timeout_method") == "thread", (
        "`timeout_method` must be 'thread' so hangs produce a stack trace"
    )


def test_pytest_config_registers_phase2_markers() -> None:
    opts = _pytest_ini_options()
    raw_markers = opts.get("markers", [])
    names = {str(m).split(":", 1)[0].strip() for m in raw_markers}
    required = {"live_alpaca", "slow", "live_paper", "integration",
                "reconcile", "parity", "unit", "notebook"}
    missing = required - names
    assert not missing, f"pytest config is missing markers: {sorted(missing)}"
