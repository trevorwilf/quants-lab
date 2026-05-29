"""Regression: subprocess env carries PYTHONPATH so prod can import bowaka_common.

The notebook bootstrap inserts the lab's ``src`` and the sibling
``bowaka_common/src`` into ``sys.path`` for the current process, but it does
**not** export them via ``PYTHONPATH``. Subprocess children (the production
backtester) don't inherit ``sys.path`` — they need ``PYTHONPATH`` in their
env. Pre-fix the prod subprocess died with
``ModuleNotFoundError: No module named 'bowaka_common'``.
"""
from __future__ import annotations

import datetime as _dt
import os
import subprocess
from pathlib import Path
from unittest import mock

from bowaka_v2_lab.parity.runner import (
    _BOWAKA_COMMON_SRC,
    _LAB_ROOT,
    _build_subprocess_env,
    run_production_backtester,
)


def _fake_completed(returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout="", stderr="")


def test_build_subprocess_env_contains_lab_src_and_bowaka_common() -> None:
    env = _build_subprocess_env()
    pp = env["PYTHONPATH"]
    chunks = pp.split(os.pathsep)
    assert str((_LAB_ROOT / "src").resolve()) in chunks
    assert str(_BOWAKA_COMMON_SRC) in chunks
    # The lab src comes BEFORE bowaka_common so the lab's own copies of
    # shared modules (if any drift in) win.
    assert chunks.index(str((_LAB_ROOT / "src").resolve())) < chunks.index(str(_BOWAKA_COMMON_SRC))


def test_build_subprocess_env_preserves_existing_pythonpath(monkeypatch) -> None:
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(["/caller/site", "/caller/extra"]))
    env = _build_subprocess_env()
    chunks = env["PYTHONPATH"].split(os.pathsep)
    assert "/caller/site" in chunks
    assert "/caller/extra" in chunks
    # Existing entries appended after the injected ones; caller-set still
    # there for fallback.
    assert chunks.index(str((_LAB_ROOT / "src").resolve())) < chunks.index("/caller/site")


def test_run_production_backtester_passes_env_to_subprocess(tmp_path: Path) -> None:
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
    kwargs = patched.call_args.kwargs
    assert "env" in kwargs, "subprocess.run must be called with env=... to pin PYTHONPATH"
    assert "PYTHONPATH" in kwargs["env"]
    pp = kwargs["env"]["PYTHONPATH"]
    assert str((_LAB_ROOT / "src").resolve()) in pp
    assert str(_BOWAKA_COMMON_SRC) in pp
