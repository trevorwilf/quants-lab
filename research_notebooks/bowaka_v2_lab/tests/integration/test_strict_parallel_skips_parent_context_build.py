"""Strict-parallel skips the parent-side ``build_fold_contexts`` call.

Speedup report v2 §1.3 / §4 P2 / §5.4 / Phase 2 task 6. Workers rebuild
their own fold contexts via the dotted factory; the parent must not pay
the per-fold context-build cost when it has already decided to dispatch
process-parallel.

The test stubs ``preflight_parallel_dispatch`` to return a
``process_parallel`` decision (so we can exercise the wiring without a
real PostgreSQL server) AND stubs
``run_bowaka_optimization_dispatch`` to a no-op so the dispatcher does
not actually try to spawn workers. The assertion is that
``build_fold_contexts`` was NOT invoked in the parent process.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

import bowaka_v2_lab.optuna.walkforward_runner as runner
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.parallel import ParallelDecision


_LAB_ROOT = Path(__file__).resolve().parents[2]


def _make_parallel_cfg(tmp_path: Path) -> Path:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    raw_cfg = _LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code_optuna.yml"
    cfg_path = write_walkforward_test_config(
        raw_cfg, tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=1,
    )
    return cfg_path


def test_strict_parallel_does_not_build_parent_fold_contexts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg_path = _make_parallel_cfg(tmp_path)

    # Bypass the storage / memory check — return a process_parallel decision.
    def _fake_preflight(study, *, n_jobs, storage_uri, mem_budget, strict_parallel):
        return ParallelDecision(
            mode="process_parallel", n_workers=int(n_jobs), reason="test-stub",
        )

    monkeypatch.setattr(runner, "_preflight_parallel_dispatch", _fake_preflight, raising=False)

    # ``preflight_parallel_dispatch`` is locally imported inside the runner
    # body; patch the source name as well so the local rebind picks it up.
    from bowaka_v2_lab.optuna import parallel as _parallel_mod

    monkeypatch.setattr(_parallel_mod, "preflight_parallel_dispatch", _fake_preflight)

    # Stub the dispatcher so the test does not attempt to spawn workers.
    def _no_op_dispatch(**kwargs):
        return kwargs["study"]

    monkeypatch.setattr(runner, "run_bowaka_optimization_dispatch", _no_op_dispatch)

    # Track whether ``build_fold_contexts`` was called in the parent.
    calls: list = []
    original = runner.build_fold_contexts

    def _tracking_build_fold_contexts(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(runner, "build_fold_contexts", _tracking_build_fold_contexts)

    # Run — opt n_jobs=2 + (test-stub) PostgreSQL URI.
    import yaml

    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    doc["optuna"]["n_jobs"] = 2
    doc["optuna"]["storage"] = "postgresql+psycopg2://stub:stub@localhost/stub"
    cfg_path.write_text(yaml.safe_dump(doc), encoding="utf-8")

    # The post-optimize success path needs a completed trial for the best-trial
    # report and the validation block. The stub dispatcher returns the study
    # untouched so the runner sees zero completed trials — the "zero valid
    # trials" branch will raise. The point of this test is the parent-context
    # build check; allow the post-dispatch raise to propagate but assert the
    # build_fold_contexts call count BEFORE the raise.
    try:
        runner.run_walkforward_study(cfg_path, allow_smoke=True)
    except Exception:  # noqa: BLE001 — expected; the stub returns no trials
        pass

    assert not calls, (
        "parent process must NOT call build_fold_contexts in process_parallel "
        f"mode (got {len(calls)} call(s))"
    )
