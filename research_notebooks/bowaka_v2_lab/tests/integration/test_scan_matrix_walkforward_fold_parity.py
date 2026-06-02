"""End-to-end walk-forward fold parity: matrix overlay vs legacy scanner.

Walk-forward scan-matrix speedup Phase 2 — the live parity gate. This proves
the WIRING the Phase-2 enablement overlay turns on:

1. Enabling the vectorized runtime (``enabled: true`` / ``runtime_mode:
   vectorized``) + a built+verified matrix makes the matrix path ACTUALLY
   FIRE — the per-scan dispatch serves every scan from the matrix
   (``matrix_scans_evaluated > 0``), not a silent fall-through to the legacy
   scanner (which would leave it at 0).
2. Running the SAME validation fold two ways — ``runtime_mode: disabled``
   (legacy ``evaluate_one_scan``) vs ``runtime_mode: vectorized`` (matrix) —
   reproduces the backtest summary EXACTLY (zero field diffs).

Scope / why synthetic + deterministic (not a real-lake gate): a real
validation-scope build is a multi-hour operator job (≈98 min for 23 sessions ×
3 symbols on the operator's lake — see docs/walkforward_scan_matrix_runbook.md),
so it is NOT a CC/CI step. This test instead builds a *tiny* matrix on a
synthetic intraday lake (cheap reads → seconds) and is therefore reproducible
on any host with no real-lake dependency. The CANDIDATE/trade-level three-way
parity (legacy == compatibility == vectorized) is proven separately and
exhaustively by ``tests/parity/test_scan_matrix_vectorized_*``; this test's job
is the fold-context → backtester WIRING + summary parity, which those scan-level
tests do not cover.

Marked ``slow`` (it builds a small matrix + runs two fold backtests); excluded
from the default ``-m "not slow"`` suite, run under ``-m slow`` and by
``make verify-walkforward-speedup``.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from bowaka_common.marketdata import layout

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.devtools.wf_lake import write_walkforward_test_config
from bowaka_v2_lab.optuna.fold_context import build_fold_contexts
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits
from bowaka_v2_lab.scanner.scan_matrix import build_scan_matrix, verify_scan_matrix
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.utils.profile_counters import profile_counters_context

pytestmark = [pytest.mark.integration, pytest.mark.slow]

_SYMS = ["AAA", "BBB"]
# Window sized so build_walkforward_splits yields >=1 validation split with
# real sessions (train 1mo / val 1mo / holdout 1mo); a tighter window can
# collapse the validation scope to zero sessions -> an empty matrix.
_START = dt.date(2024, 1, 1)
_END = dt.date(2024, 5, 1)
_BASE_CFG = (
    Path(__file__).resolve().parents[2]   # tests/integration/ -> lab root
    / "configs" / "quarantined"
    / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml"
)


def _build_intraday_lake(lake: Path) -> None:
    """Tiny lake with minute bars spanning 09:30->16:00 ET (inside the scan
    window, unlike ``build_tiny_lake`` whose 08:30-09:00 ET bars never reach
    the 09:45 scanner start) plus daily bars for the prior-day baseline."""
    days = [d.date() for d in pd.bdate_range(_START, _END)]
    for sym in _SYMS:
        dpath = layout.daily_bars_path(lake, sym, feed="iex")
        dpath.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({
            "symbol": [sym] * len(days),
            "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
            "open": [10.0] * len(days), "high": [10.5] * len(days),
            "low": [9.5] * len(days), "close": [10.0] * len(days),
            "volume": [2_000_000] * len(days), "session_date": days,
        }).to_parquet(dpath, index=False)
        by_month: dict[tuple[int, int], list] = {}
        for d in days:
            base = pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=14, minutes=30)  # 09:30 ET
            for i in range(390):
                ts = base + pd.Timedelta(minutes=i)
                px = 10.0 + 0.5 * np.sin(i / 30.0)
                by_month.setdefault((d.year, d.month), []).append({
                    "symbol": sym, "timestamp": ts, "open": px,
                    "high": px + 0.2, "low": px - 0.2, "close": px + 0.05,
                    "volume": 8000.0 + i * 10,
                })
        for (year, month), rows in by_month.items():
            mpath = layout.minute_bars_path(lake, sym, year, month, feed="iex")
            mpath.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(rows).to_parquet(mpath, index=False)


def _make_cfg(tmp_path: Path, lake: Path, store: Path) -> Path:
    """Synthetic walk-forward config in current_code_parity mode (runs the
    intraday scanner so the matrix can fire) with the vectorized matrix on."""
    cfg_path = write_walkforward_test_config(
        _BASE_CFG, tmp_path / "wf_matrix.yml", lake=lake, symbols=_SYMS,
        start=_START, end=_END, n_trials=1,
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    # current_code_parity drives the full intraday scanner (smoke_fixture uses
    # the daily driver, which never invokes the scanner -> the matrix can't fire).
    raw["simulation"] = {"mode": "current_code_parity"}
    raw["optuna"]["objective_artifact_mode"] = "objective_minimal"
    raw["optuna"].setdefault("acceleration", {})["scan_matrix"] = {
        "enabled": True, "runtime_mode": "vectorized", "require_parity_manifest": True,
        "store_root": str(store), "scope": "validation", "separate_holdout_matrix": True,
    }
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return cfg_path


def _run_fold(ctx, cfg, run_sessions):
    rd = Path(tempfile.mkdtemp(prefix="fold_parity_"))
    with profile_counters_context() as counters:
        res = run_backtest(
            cfg=cfg, sessions=list(run_sessions),
            scan_times_per_session=lambda d: list(ctx.scan_times_by_session.get(d, ())),
            universe_snapshot_by_session=ctx.universe_by_session,
            daily_cache_by_session=ctx.daily_cache_by_session,
            minute_bars_supplier=ctx.suppliers.minute,
            daily_bars_supplier=ctx.suppliers.daily,
            quote_supplier=ctx.suppliers.quote,
            forward_minute_supplier=ctx.suppliers.forward_minute,
            initial_bankroll=100_000.0, paths=ctx.paths, run_dir=rd,
            artifact_mode="objective_minimal",
            startup_dq_report=ctx.startup_dq_report,
            scan_matrix_store=ctx.scan_matrix_store,
        )
    return res, counters


@pytest.mark.timeout(300)
def test_matrix_overlay_fires_and_reproduces_legacy_fold(tmp_path):
    lake = tmp_path / "lake"
    store = tmp_path / "store" / "validation"  # ends with scope -> resolver no-append
    _build_intraday_lake(lake)
    cfg_path = _make_cfg(tmp_path, lake, store)

    # --- build + verify the tiny matrix (the small-build CC path) ---
    build_scan_matrix(cfg_path, scope="validation", workers=1, reserve_gib=0.5,
                      max_optuna_workers=1, store_root=store)
    assert (store / "manifest.json").is_file()
    rep = verify_scan_matrix(store, cfg_path, sample_count=5, vectorized_check=True)
    assert rep.get("status") in ("ok", "warn"), rep
    assert rep.get("vectorized_checked") is True
    # write the parity proof the runtime opt-in guard reads (verifier_version=2)
    (store / "parity_proof.json").write_text(json.dumps({
        "matrix_id": rep.get("matrix_id"), "verifier_version": 2,
        "config_input_hash": rep.get("config_input_hash"),
        "dataset_hash": rep.get("dataset_hash"),
    }, default=str), encoding="utf-8")

    # --- build fold contexts both ways (same plan, same lake) ---
    cfg_vec = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg_dis = copy.deepcopy(cfg_vec)
    cfg_dis["optuna"]["acceleration"]["scan_matrix"]["enabled"] = False
    cfg_dis["optuna"]["acceleration"]["scan_matrix"]["runtime_mode"] = "disabled"

    wf = cfg_vec["optuna"]["walkforward"]
    plan = build_walkforward_splits(
        full_start=_START, full_end=_END,
        train_months=int(wf["train_months"]), val_months=int(wf["val_months"]),
        final_holdout_months=int(wf["final_holdout_months"]),
    )
    paths = BowakaV2Paths.from_config(cfg_vec, repo_root=Path(__file__).resolve().parents[4])
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    ctxs_vec = build_fold_contexts(cfg_vec, plan, lake_root=lake, feed="iex",
                                   symbols=_SYMS, paths=paths, holdout_guard=guard)
    ctxs_dis = build_fold_contexts(cfg_dis, plan, lake_root=lake, feed="iex",
                                   symbols=_SYMS, paths=paths, holdout_guard=guard)
    ctx_vec = next(c for c in ctxs_vec if c is not None)
    ctx_dis = next(c for c in ctxs_dis if c is not None)

    # the vectorized context opened the store (Phase 1 wiring); legacy did not.
    assert ctx_vec.scan_matrix_store is not None, (
        "the vectorized fold context must open the built matrix store"
    )
    assert ctx_dis.scan_matrix_store is None

    # run the first few val sessions both ways (matrix covers all of them).
    run_sessions = list(ctx_vec.sessions)[:3]
    assert run_sessions, "the validation fold must have sessions"
    res_vec, c_vec = _run_fold(ctx_vec, cfg_vec, run_sessions)
    res_dis, c_dis = _run_fold(ctx_dis, cfg_dis, run_sessions)

    # (a) the matrix actually FIRED on the vectorized run, and NOT on the legacy
    #     run — a silent legacy fall-through would leave the counter at 0.
    assert c_vec.matrix_scans_evaluated > 0, (
        "the vectorized run must serve scans from the matrix "
        f"(matrix_scans_evaluated={c_vec.matrix_scans_evaluated}); a 0 here means "
        "the matrix path silently fell back to the legacy scanner"
    )
    assert c_dis.matrix_scans_evaluated == 0, (
        "the disabled run must NOT touch the matrix "
        f"(got matrix_scans_evaluated={c_dis.matrix_scans_evaluated})"
    )

    # (b) the matrix run reproduces the legacy backtest summary EXACTLY.
    sv = {k: v for k, v in res_vec.summary.items() if not str(k).startswith("_")}
    sd = {k: v for k, v in res_dis.summary.items() if not str(k).startswith("_")}
    diffs = {k: (sv.get(k), sd.get(k)) for k in set(sv) | set(sd) if sv.get(k) != sd.get(k)}
    assert not diffs, f"matrix vs legacy fold summary diverged: {diffs}"
    # explicit checks on the FoldResult-relevant fields the prompt names.
    assert int(sv.get("n_trades", 0)) == int(sd.get("n_trades", 0))
    assert float(sv.get("net_return_pct", 0.0) or 0.0) == pytest.approx(
        float(sd.get("net_return_pct", 0.0) or 0.0), abs=1e-9
    )
    assert int(sv.get("candidate_events_count", 0)) == int(sd.get("candidate_events_count", 0))
