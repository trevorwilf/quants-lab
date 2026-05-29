"""Regression: the runner must default to the current interpreter.

Pre-hotfix, the default was ``python_exe="py", python_extra=("-3.12",)`` —
the Windows launcher — which fails with ``FileNotFoundError: [Errno 2] No
such file or directory: 'py'`` on the ql-jupyter Linux container (and on
any host without the Windows ``py`` launcher).

The default must be ``sys.executable`` so the subprocess inherits the same
interpreter (and the same site-packages including pyarrow) that's running
the notebook / CLI / test.
"""
from __future__ import annotations

import datetime as _dt
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from bowaka_v2_lab.parity.runner import run_production_backtester


def _fake_completed(returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout="", stderr="",
    )


def test_run_production_backtester_defaults_to_sys_executable(tmp_path: Path) -> None:
    symbols_file = tmp_path / "uni.txt"
    symbols_file.write_text("AAA\n", encoding="utf-8")
    prod_script = tmp_path / "fake_prod.py"
    prod_script.write_text("# placeholder\n", encoding="utf-8")
    with mock.patch("bowaka_v2_lab.parity.runner.subprocess.run",
                    return_value=_fake_completed()) as patched:
        run_production_backtester(
            start_date=_dt.date(2026, 5, 19),
            end_date=_dt.date(2026, 5, 19),
            symbols_file=symbols_file,
            prod_config_path=tmp_path / "prod.yaml",
            lake_root=None,
            output_dir=tmp_path / "out",
            prod_script=prod_script,
        )
    assert patched.called
    cmd = patched.call_args.args[0]
    assert cmd[0] == sys.executable, (
        f"runner did not default to sys.executable; got cmd[0]={cmd[0]!r}"
    )
    # No phantom ``-3.12`` argument from the Windows-launcher era.
    assert "-3.12" not in cmd


def test_explicit_python_exe_overrides_default(tmp_path: Path) -> None:
    symbols_file = tmp_path / "uni.txt"
    symbols_file.write_text("AAA\n", encoding="utf-8")
    prod_script = tmp_path / "fake_prod.py"
    prod_script.write_text("# placeholder\n", encoding="utf-8")
    with mock.patch("bowaka_v2_lab.parity.runner.subprocess.run",
                    return_value=_fake_completed()) as patched:
        run_production_backtester(
            start_date=_dt.date(2026, 5, 19),
            end_date=_dt.date(2026, 5, 19),
            symbols_file=symbols_file,
            prod_config_path=tmp_path / "prod.yaml",
            lake_root=None,
            output_dir=tmp_path / "out",
            prod_script=prod_script,
            python_exe="py",
            python_extra=("-3.12",),
        )
    cmd = patched.call_args.args[0]
    assert cmd[0] == "py"
    assert cmd[1] == "-3.12"


def test_subprocess_failure_surfaces_via_returncode(tmp_path: Path) -> None:
    symbols_file = tmp_path / "uni.txt"
    symbols_file.write_text("AAA\n", encoding="utf-8")
    prod_script = tmp_path / "fake_prod.py"
    prod_script.write_text("# placeholder\n", encoding="utf-8")
    with mock.patch("bowaka_v2_lab.parity.runner.subprocess.run",
                    return_value=_fake_completed(returncode=42)):
        result = run_production_backtester(
            start_date=_dt.date(2026, 5, 19),
            end_date=_dt.date(2026, 5, 19),
            symbols_file=symbols_file,
            prod_config_path=tmp_path / "prod.yaml",
            lake_root=None,
            output_dir=tmp_path / "out",
            prod_script=prod_script,
        )
    assert result.returncode == 42
