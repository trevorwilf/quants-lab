"""Phase 3 — parallel parity helpers: block split, PG-absence, memory guard."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest

import bowaka_v2_lab.parity.runner as R


def _days(*d):
    return [_dt.date(2026, 5, x) for x in d]


def test_contiguous_blocks_split_is_ordered_and_complete() -> None:
    s = _days(18, 19, 20, 21, 22)  # 5 sessions
    assert R._contiguous_blocks(s, 2) == [s[:3], s[3:]]   # 3+2, earlier absorbs rem
    assert R._contiguous_blocks(s, 1) == [s]
    assert R._contiguous_blocks(s, 10) == [[x] for x in s]  # k capped at n
    # 3 workers: contiguous, no overlap, covers everything exactly once.
    blocks = R._contiguous_blocks(s, 3)
    assert [x for b in blocks for x in b] == s
    assert sum(len(b) for b in blocks) == len(s)


def test_parity_path_opens_no_postgres() -> None:
    # The parity package + cli_runners must not reference PostgreSQL (the worker
    # cap is 12 only because the parity path opens no PG connection).
    assert R._parity_path_touches_postgres() is False


def test_memory_guard_refuses_before_spawning(monkeypatch, tmp_path) -> None:
    """A breached RAM reserve aborts the launch BEFORE any worker spawns."""
    from bowaka_v2_lab.utils.memory_guard import MemoryReserveViolation

    class _RefusingBudget:
        def assert_launch_safe(self, *a, **k):
            raise MemoryReserveViolation("refused for test")

    monkeypatch.setattr(
        "bowaka_v2_lab.utils.memory_guard.MemoryBudget.from_system",
        classmethod(lambda cls, **kw: _RefusingBudget()),
    )
    # Sentinel: no worker subprocess may launch if the guard fires first.
    monkeypatch.setattr(
        "subprocess.Popen",
        lambda *_a, **_k: pytest.fail("launched workers despite memory refusal"),
    )
    with pytest.raises(MemoryReserveViolation):
        R._run_parity_parallel(
            start_date=_dt.date(2026, 5, 19), end_date=_dt.date(2026, 5, 19),
            sessions=_days(19), symbols=["AAA"],
            prod_config_path=Path("prod.yaml"), lab_config_path=Path("lab.yml"),
            lake_root=None, cost_stress="base", run_root=tmp_path,
            symbols_file=tmp_path / "u.txt", python_exe=None, python_extra=(),
            prod_script=None, timeout_sec=60, per_session_universe=False,
            requested_sessions=_days(19), bundle_out=None, n_workers=12,
            print_progress=False,
        )
