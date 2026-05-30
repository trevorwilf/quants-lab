"""Regression: timeout + progress-log UX for long-running parity runs.

The user hit ``TimeoutExpired`` at the old 600-second default while running
a 1-year / 833-symbol window (255 sessions * 833 syms = ~212 k symbol-days).
Three things must hold:

  1. ``timeout_sec`` is configurable end-to-end (run_production_backtester +
     run_parity + CLI flag).
  2. Production subprocess stderr is streamed to a log file so long runs
     are observable via ``tail -f`` while still in-flight (the prior
     ``capture_output=True`` buffered everything until exit).
  3. On ``TimeoutExpired``, the runner raises a ``RuntimeError`` with the
     log-file tail and an actionable hint about MAX_UNIVERSE_SIZE.
"""
from __future__ import annotations

import datetime as _dt
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from bowaka_v2_lab.parity.runner import run_production_backtester


def _fake_completed(returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout="prod stdout", stderr=None,
    )


def _make_args(tmp_path: Path) -> dict:
    symbols_file = tmp_path / "uni.txt"
    symbols_file.write_text("AAA\n", encoding="utf-8")
    prod_script = tmp_path / "fake_prod.py"
    prod_script.write_text("# placeholder\n", encoding="utf-8")
    return {
        "start_date": _dt.date(2026, 5, 19),
        "end_date": _dt.date(2026, 5, 19),
        "symbols_file": symbols_file,
        "prod_config_path": tmp_path / "prod.yaml",
        "lake_root": None,
        "output_dir": tmp_path / "out",
        "prod_script": prod_script,
    }


def test_timeout_sec_passed_to_subprocess(tmp_path: Path) -> None:
    args = _make_args(tmp_path)
    with mock.patch("bowaka_v2_lab.parity.runner.subprocess.run",
                    return_value=_fake_completed()) as patched:
        run_production_backtester(**args, timeout_sec=2400)
    kwargs = patched.call_args.kwargs
    assert kwargs.get("timeout") == 2400


def test_progress_log_defaults_inside_output_dir(tmp_path: Path) -> None:
    args = _make_args(tmp_path)
    with mock.patch("bowaka_v2_lab.parity.runner.subprocess.run",
                    return_value=_fake_completed()):
        run_production_backtester(**args)
    # Default log path: <output_dir>/production.stderr.log
    expected = args["output_dir"] / "production.stderr.log"
    assert expected.is_file()


def test_explicit_progress_log_path_is_honored(tmp_path: Path) -> None:
    args = _make_args(tmp_path)
    custom_log = tmp_path / "custom_dir" / "my.log"
    with mock.patch("bowaka_v2_lab.parity.runner.subprocess.run",
                    return_value=_fake_completed()):
        run_production_backtester(**args, progress_log=custom_log)
    assert custom_log.is_file()


def test_subprocess_stderr_redirected_to_file_handle(tmp_path: Path) -> None:
    args = _make_args(tmp_path)
    captured: dict = {}

    def _capture(cmd, **kwargs):
        # The stderr kwarg should be an open file handle (not a PIPE int).
        captured["stderr"] = kwargs.get("stderr")
        captured["stdout"] = kwargs.get("stdout")
        return _fake_completed()

    with mock.patch("bowaka_v2_lab.parity.runner.subprocess.run", side_effect=_capture):
        run_production_backtester(**args)
    # stdout still captured for the summary path; stderr -> file handle.
    assert captured["stdout"] == subprocess.PIPE
    stderr_arg = captured["stderr"]
    # The handle was a writable file object opened in text mode.
    assert hasattr(stderr_arg, "write")
    assert not isinstance(stderr_arg, int)  # not PIPE / STDOUT


def test_timeout_expired_raises_runtime_error_with_log_tail(tmp_path: Path) -> None:
    args = _make_args(tmp_path)
    # Write the log file BEFORE the call so the runtime tail-read finds content.
    def _raise_timeout(cmd, **kwargs):
        # Simulate the subprocess having written progress before the timeout.
        log_handle = kwargs.get("stderr")
        if hasattr(log_handle, "write"):
            log_handle.write("scanning session 2025-05-19...\n")
            log_handle.write("processed 200 symbols / 833\n")
            log_handle.flush()
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout", 0))

    with mock.patch("bowaka_v2_lab.parity.runner.subprocess.run", side_effect=_raise_timeout):
        with pytest.raises(RuntimeError) as exc_info:
            run_production_backtester(**args, timeout_sec=120)

    msg = str(exc_info.value)
    assert "timed out" in msg
    assert "120" in msg
    assert "MAX_UNIVERSE_SIZE" in msg
    # The progress-log tail is included so the user sees what got far.
    assert "processed 200 symbols" in msg
