"""Per-session ``run_parity`` chunked mode — progress prints + callback shape.

The operator's ask: see current date + average time per day during a long
parity run so it's obvious the runner isn't hung. ``chunk_per_session=True``
iterates the window day-by-day, times each side independently, and emits a
single status line per session plus an optional structured callback.
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from bowaka_v2_lab.parity.runner import _fmt_eta, _xnys_sessions, run_parity


def test_xnys_sessions_returns_trading_days_inclusive() -> None:
    sessions = _xnys_sessions(_dt.date(2026, 5, 18), _dt.date(2026, 5, 22))
    # Mon-Fri inclusive: 5 trading days.
    assert sessions == [
        _dt.date(2026, 5, 18),
        _dt.date(2026, 5, 19),
        _dt.date(2026, 5, 20),
        _dt.date(2026, 5, 21),
        _dt.date(2026, 5, 22),
    ]


def test_fmt_eta_picks_compact_units() -> None:
    assert _fmt_eta(0) == "0s"
    assert _fmt_eta(45) == "45s"
    assert _fmt_eta(65) == "1m05s"
    assert _fmt_eta(605) == "10m05s"
    assert _fmt_eta(3660) == "1h01m"
    assert _fmt_eta(7325) == "2h02m"


@dataclass
class _StubProdResult:
    output_dir: Path
    summary: dict = field(default_factory=dict)
    trades_path: Path = Path("dummy.parquet")
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


def test_chunked_mode_prints_one_line_per_session_and_fires_callback(
    tmp_path: Path, capsys: pytest.CaptureFixture,
) -> None:
    callback_calls: list[dict] = []

    def _cb(payload: dict) -> None:
        callback_calls.append(payload)

    sessions = [_dt.date(2026, 5, 18), _dt.date(2026, 5, 19), _dt.date(2026, 5, 20)]
    fake_lab_result = mock.MagicMock(trades=[], candidate_events=[])

    with (
        mock.patch("bowaka_v2_lab.parity.runner._xnys_sessions", return_value=sessions),
        mock.patch(
            "bowaka_v2_lab.parity.runner.run_production_backtester",
            side_effect=[_StubProdResult(output_dir=tmp_path / f"prod_{i}")
                         for i in range(len(sessions))],
        ),
        mock.patch(
            "bowaka_v2_lab.parity.runner.run_lab_backtester",
            return_value=fake_lab_result,
        ),
        mock.patch(
            "bowaka_v2_lab.parity.runner.normalize_production_output",
            return_value=([], []),
        ) if False else mock.patch(
            "bowaka_v2_lab.parity.normalizers.normalize_production_output",
            return_value=([], []),
        ),
        mock.patch(
            "bowaka_v2_lab.parity.normalizers.normalize_lab_output",
            return_value=([], []),
        ),
    ):
        report = run_parity(
            start_date=_dt.date(2026, 5, 18),
            end_date=_dt.date(2026, 5, 20),
            symbols=["AAA", "BBB"],
            prod_config_path=tmp_path / "prod.yaml",
            lab_config_path=tmp_path / "lab.yml",
            lake_root=tmp_path / "lake",
            cost_stress="base",
            run_root=tmp_path / "run",
            chunk_per_session=True,
            print_progress=True,
            progress_callback=_cb,
        )

    captured = capsys.readouterr().out
    # Each session emits 3 status lines: start-prod, prod-done/start-lab, done.
    start_lines = [
        ln for ln in captured.splitlines()
        if re.search(r"\[\s*\d+/\s*\d+\] 20\d\d-\d\d-\d\d  prod: starting", ln)
    ]
    done_lines = [
        ln for ln in captured.splitlines()
        if re.search(r"\[\s*\d+/\s*\d+\] 20\d\d-\d\d-\d\d  done: prod=.*lab=.*eta=", ln)
    ]
    assert len(start_lines) == 3, (
        f"expected 3 'prod: starting' lines, got {len(start_lines)}:\n{captured}"
    )
    assert len(done_lines) == 3, (
        f"expected 3 'done:' status lines, got {len(done_lines)}:\n{captured}"
    )
    # Callback fired once per session with the right structure.
    assert len(callback_calls) == 3
    for idx, payload in enumerate(callback_calls, start=1):
        assert payload["session_idx"] == idx
        assert payload["total_sessions"] == 3
        assert payload["session_date"] == sessions[idx - 1]
        assert payload["prod_seconds"] >= 0
        assert payload["lab_seconds"] >= 0
        assert "avg_prod_seconds" in payload
        assert "avg_lab_seconds" in payload
        assert "est_remaining_seconds" in payload
    # The final ETA is zero (last session).
    assert callback_calls[-1]["est_remaining_seconds"] == pytest.approx(0.0, abs=1e-6)
    # The report has the right window even though we ran in chunks.
    assert report.window_start == _dt.date(2026, 5, 18)
    assert report.window_end == _dt.date(2026, 5, 20)


def test_chunked_mode_raises_with_session_context_on_prod_failure(tmp_path: Path) -> None:
    sessions = [_dt.date(2026, 5, 18), _dt.date(2026, 5, 19)]
    fail = _StubProdResult(
        output_dir=tmp_path / "prod_1", returncode=2,
        stdout="ok-line\n", stderr="boom at parser line 7\n",
    )
    with (
        mock.patch("bowaka_v2_lab.parity.runner._xnys_sessions", return_value=sessions),
        mock.patch(
            "bowaka_v2_lab.parity.runner.run_production_backtester",
            side_effect=[_StubProdResult(output_dir=tmp_path / "prod_0"), fail],
        ),
        mock.patch(
            "bowaka_v2_lab.parity.runner.run_lab_backtester",
            return_value=mock.MagicMock(trades=[], candidate_events=[]),
        ),
        mock.patch(
            "bowaka_v2_lab.parity.normalizers.normalize_production_output",
            return_value=([], []),
        ),
        mock.patch(
            "bowaka_v2_lab.parity.normalizers.normalize_lab_output",
            return_value=([], []),
        ),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            run_parity(
                start_date=_dt.date(2026, 5, 18),
                end_date=_dt.date(2026, 5, 19),
                symbols=["AAA"],
                prod_config_path=tmp_path / "prod.yaml",
                lab_config_path=tmp_path / "lab.yml",
                lake_root=tmp_path / "lake",
                cost_stress="base",
                run_root=tmp_path / "run",
                chunk_per_session=True,
                print_progress=False,
            )
    msg = str(exc_info.value)
    assert "session 2026-05-19" in msg
    assert "exit 2" in msg
    assert "boom at parser line 7" in msg


def test_non_chunked_mode_preserves_old_signature_path(tmp_path: Path) -> None:
    """When chunk_per_session=False, run_production_backtester is called ONCE
    with the full window (not per session). Guards against accidental loop in
    the default path."""
    full_window_prod = _StubProdResult(output_dir=tmp_path / "prod_full")
    with (
        mock.patch(
            "bowaka_v2_lab.parity.runner.run_production_backtester",
            return_value=full_window_prod,
        ) as patched_prod,
        mock.patch(
            "bowaka_v2_lab.parity.runner.run_lab_backtester",
            return_value=mock.MagicMock(trades=[], candidate_events=[]),
        ),
        mock.patch(
            "bowaka_v2_lab.parity.normalizers.normalize_production_output",
            return_value=([], []),
        ),
        mock.patch(
            "bowaka_v2_lab.parity.normalizers.normalize_lab_output",
            return_value=([], []),
        ),
    ):
        run_parity(
            start_date=_dt.date(2026, 5, 18),
            end_date=_dt.date(2026, 5, 22),
            symbols=["AAA"],
            prod_config_path=tmp_path / "prod.yaml",
            lab_config_path=tmp_path / "lab.yml",
            lake_root=tmp_path / "lake",
            cost_stress="base",
            run_root=tmp_path / "run",
            chunk_per_session=False,
        )
    assert patched_prod.call_count == 1
    call_kwargs = patched_prod.call_args.kwargs
    assert call_kwargs["start_date"] == _dt.date(2026, 5, 18)
    assert call_kwargs["end_date"] == _dt.date(2026, 5, 22)
