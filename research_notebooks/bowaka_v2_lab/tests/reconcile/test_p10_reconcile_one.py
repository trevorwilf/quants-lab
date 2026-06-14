"""P10 — the per-session reconciler wiring (_default_reconcile_one), the real lab
fill_timestamp, and the single P9 tolerance set.

The orchestrator's aggregation/status/gate logic was already tested with injected
stubs; these exercise the PRODUCTION reconciler against the frozen synthetic paper
logs (still no real paper data / network — the live run is the operator gate).
"""
from __future__ import annotations

import inspect
import shutil

import pandas as pd

from .conftest import PAPER_LOGS_SYNTHETIC, SYNTHETIC_SESSION


def test_lab_fill_timestamp_comes_from_order_created_at(tmp_path) -> None:
    """P10: LabFill.fill_timestamp is populated from the parent order's created_at
    (was hard-coded None, which made fill-latency reconciliation vacuous)."""
    from bowaka_v2_lab.reconcile.replay import _lab_orders_and_fills

    rd = tmp_path / "run"
    rd.mkdir()
    pd.DataFrame([{
        "parent_order_id": "o1", "candidate_event_id": "c1", "symbol": "AAA",
        "side": "buy", "qty": 100, "limit_price": 10.0,
        "created_at": "2024-09-04T13:45:00Z", "status": "filled",
    }]).to_parquet(rd / "orders.parquet", index=False)
    pd.DataFrame([{
        "parent_order_id": "o1", "symbol": "AAA", "filled": True,
        "filled_qty": 100, "avg_fill_price": 10.01,
    }]).to_parquet(rd / "fills.parquet", index=False)

    class _Result:
        run_dir = rd

    orders, fills = _lab_orders_and_fills(_Result())
    assert len(fills) == 1
    assert fills[0].fill_timestamp == "2024-09-04T13:45:00Z"   # was None
    assert fills[0].candidate_event_id == "c1"


def test_default_reconcile_one_on_synthetic_session(parity_lake_config, tmp_path) -> None:
    """_default_reconcile_one replays the lab + computes the §8.7 metrics for one real
    paper session (no longer NotImplementedError)."""
    from bowaka_v2_lab.reconcile.orchestrator import _default_reconcile_one

    # The orchestrator convention: a YYYY-MM-DD session dir holding the JSONLs.
    session_dir = tmp_path / SYNTHETIC_SESSION.isoformat()
    session_dir.mkdir()
    for f in PAPER_LOGS_SYNTHETIC.glob("*.jsonl"):
        shutil.copy(f, session_dir / f.name)

    res = _default_reconcile_one(session_dir, parity_lake_config, None)
    assert res.session_date == SYNTHETIC_SESSION.isoformat()
    assert res.n_paper_candidates == 3      # the frozen fixture has 3 paper candidates
    # Every gate metric is a well-formed rate (computed, not stubbed).
    for m in ("candidate_recall", "gate_match", "entry_decision_match", "fill_match",
              "exit_reason_match", "bracket_attach_match", "daily_pnl_sign_match"):
        v = getattr(res, m)
        assert 0.0 <= v <= 1.0, (m, v)
    assert res.fill_price_mae_bps >= 0.0
    assert isinstance(res.per_symbol_fill_error_bps, dict)


def test_default_reconcile_one_via_run_reconciliation(parity_lake_config, tmp_path) -> None:
    """End-to-end through the orchestrator: with a real session on disk the default
    reconciler runs (status 'ok'/'BELOW_MIN_SESSIONS', NOT REAL_LOGS_DEFERRED)."""
    from bowaka_v2_lab.reconcile.orchestrator import run_reconciliation

    root = tmp_path / "paper_logs"
    session_dir = root / SYNTHETIC_SESSION.isoformat()
    session_dir.mkdir(parents=True)
    for f in PAPER_LOGS_SYNTHETIC.glob("*.jsonl"):
        shutil.copy(f, session_dir / f.name)

    report = run_reconciliation(paper_logs_root=root, cfg=parity_lake_config)
    assert report.n_sessions == 1
    # 1 < DEFAULT_MIN_SESSIONS(10) -> BELOW_MIN_SESSIONS (real reconcile ran; not deferred).
    assert report.status == "BELOW_MIN_SESSIONS"
    assert report.aggregate  # metrics were aggregated (the reconciler produced them)
    assert "candidate_recall" in report.aggregate


def test_reconcile_uses_single_p9_tolerance_set() -> None:
    """The §3.4 / Phase-7/9/10 'match' tolerances are the SINGLE P9 set
    (comparator.DEFAULT_RECONCILE_TOLERANCES, the source load_reconcile_tolerances
    resolves + _default_reconcile_one consumes); the Phase-10 comparators' defaults
    agree with it (guard against drift)."""
    from bowaka_v2_lab.reconcile import comparators
    from bowaka_v2_lab.reconcile.comparator import (
        DEFAULT_RECONCILE_TOLERANCES,
        load_reconcile_tolerances,
    )

    tol = load_reconcile_tolerances(None)
    for k in ("emission_jaccard_min", "decision_reason_match_min",
              "fill_price_tolerance_bps", "fill_qty_tolerance_shares"):
        assert tol[k] == DEFAULT_RECONCILE_TOLERANCES[k]
    # the Phase-10 emission comparator's hard default == the single P9 set
    assert (inspect.signature(comparators.emission_jaccard).parameters["threshold"].default
            == DEFAULT_RECONCILE_TOLERANCES["emission_jaccard_min"])
