"""Replay a paper-trading session against the lab (realism-audit Phase 10).

:func:`replay_paper_session` loads a single paper day's logs (candidates /
decisions / orders / fills / quotes / brackets / exits), runs the v2 lab
backtester over the **same lake / universe / date** in
``simulation.mode == current_code_parity``, and returns a :class:`ReplayResult`
holding side-by-side :class:`~bowaka_v2_lab.reconcile.schemas.ReconcileRow`
records keyed by ``candidate_event_id``.

Scaffolding-only contract (Phase 10)
------------------------------------
No real paper logs are supplied with this phase. The whole path is exercised
end-to-end against a frozen *synthetic* paper-log fixture (see
``tests/fixtures/paper_logs_synthetic/``). When no paper logs exist for the
requested session, :func:`replay_paper_session` still runs (it produces a
``scaffolding_only`` result) so the framework is callable the moment real logs
land — it never fabricates paper data.

current_code_parity
-------------------
The lab is run in ``current_code_parity`` mode — the contract that reproduces
the live code *as written*, the only meaningful basis for a paper-vs-lab
reconciliation. The replay forces ``simulation.mode = current_code_parity`` on
the supplied config (and ``allow_research_relaxed`` so a partial research
config still runs), builds the point-in-time universe from the lake (a
``current_code_parity`` run refuses a synthetic universe), and never touches
``intended_realism`` behaviour.
"""
from __future__ import annotations

import copy
import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from .comparators import (
    compare_decision_reason,
    compare_exit_reason,
    compare_fill,
    compare_order_size,
    compare_pnl,
    diff_candidate_sets,
)
from .importer import _read_jsonl, import_paper_logs
from .schemas import (
    LabCandidate,
    LabDecision,
    LabExit,
    LabFill,
    LabOrder,
    PaperCandidate,
    PaperDecision,
    PaperExit,
    PaperFill,
    PaperOrder,
    ReconcileRow,
)


@dataclass
class ReplayResult:
    """Side-by-side paper-vs-lab records for one replayed session.

    ``rows`` is keyed (1:1) on ``candidate_event_id`` — every paper-only,
    lab-only and both-sides candidate has exactly one row. ``scaffolding_only``
    is True when no paper logs were found for the session: the lab still ran,
    but there is nothing to reconcile against (the Phase-10 operator constraint).
    """

    session_date: str
    rows: list[ReconcileRow] = field(default_factory=list)
    scaffolding_only: bool = False
    note: Optional[str] = None
    lab_run_dir: Optional[str] = None
    lab_run_id: Optional[str] = None
    n_paper_candidates: int = 0
    n_lab_candidates: int = 0


# --------------------------------------------------------------------------
# Session-date helpers.
# --------------------------------------------------------------------------
def _as_date(value: Any) -> _dt.date:
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    return pd.Timestamp(value).date()


def _session_str(value: Any) -> str:
    return _as_date(value).isoformat()


# --------------------------------------------------------------------------
# Paper-log loading (one session).
# --------------------------------------------------------------------------
def _filter_session(records: list[dict], session: str, ts_key: str) -> list[dict]:
    """Keep only records belonging to ``session`` (by ``session_date`` or ts)."""
    out: list[dict] = []
    for rec in records:
        sd = rec.get("session_date")
        if sd is not None:
            if str(sd) == session:
                out.append(rec)
            continue
        ts = rec.get(ts_key)
        if ts is not None:
            try:
                if _session_str(ts) == session:
                    out.append(rec)
            except Exception:  # noqa: BLE001 — un-parseable ts: drop, don't crash
                continue
    return out


def _normalize_candidate_id(rec: dict, *, fallback_prefix: str) -> str:
    """The candidate id a downstream record keys on, with a stable fallback.

    Paper / lab decisions, orders and fills should all carry
    ``candidate_event_id``. When a record lacks one (older paper schema), a
    normalized id is synthesised from ``(symbol, parent_order_id | event_id)``
    so the record can still be slotted into a row deterministically.
    """
    cid = rec.get("candidate_event_id") or rec.get("event_id")
    if cid:
        return str(cid)
    key = rec.get("parent_order_id") or rec.get("symbol") or "unknown"
    return f"{fallback_prefix}:{key}"


@dataclass
class _PaperSession:
    candidates: list[PaperCandidate]
    decisions: list[PaperDecision]
    orders: list[PaperOrder]
    fills: list[PaperFill]
    exits: list[PaperExit]


def load_paper_session(paper_logs_root: Path | str, session_date: Any) -> _PaperSession:
    """Load + validate one paper session's records from ``paper_logs_root``.

    Reuses the Phase-7 :func:`reconcile.importer.import_paper_logs` reader
    (JSONL ingestion + timestamp normalisation) and then filters to the
    requested session and validates each row into the Phase-10 typed models.
    A missing directory simply yields empty record lists — never an error.
    """
    session = _session_str(session_date)
    root = Path(paper_logs_root)
    if not root.is_dir():
        return _PaperSession([], [], [], [], [])
    imp = import_paper_logs(root)

    candidates = [
        PaperCandidate.model_validate(r)
        for r in _filter_session(imp.candidates, session, "scan_timestamp")
    ]
    decisions = [
        PaperDecision.model_validate(r)
        for r in _filter_session(imp.decisions, session, "decision_timestamp")
    ]
    orders_raw = _filter_session(imp.orders, session, "submit_timestamp")
    fills_raw = _filter_session(imp.fills, session, "fill_timestamp")
    # exits.jsonl is an optional Phase-10 log the Phase-7 importer does not
    # read; reuse the importer's JSONL reader (returns [] when the file is
    # absent) rather than duplicating it.
    exits_raw = _filter_session(
        _read_jsonl(root / "exits.jsonl"), session, "exit_timestamp"
    )

    # Backfill candidate_event_id on orders / fills / exits from the order map
    # when the paper log only links them by parent_order_id.
    order_to_candidate: dict[str, str] = {}
    for r in orders_raw:
        if r.get("parent_order_id") and r.get("candidate_event_id"):
            order_to_candidate[str(r["parent_order_id"])] = str(r["candidate_event_id"])
    for r in (*fills_raw, *exits_raw):
        if not r.get("candidate_event_id") and r.get("parent_order_id"):
            mapped = order_to_candidate.get(str(r["parent_order_id"]))
            if mapped:
                r["candidate_event_id"] = mapped

    orders = [PaperOrder.model_validate(r) for r in orders_raw]
    fills = [PaperFill.model_validate(r) for r in fills_raw]
    exits = [PaperExit.model_validate(r) for r in exits_raw]
    return _PaperSession(candidates, decisions, orders, fills, exits)


# --------------------------------------------------------------------------
# Lab run (current_code_parity) for one session.
# --------------------------------------------------------------------------
def _force_parity_config(lab_cfg: Any) -> dict:
    """Deep-copy the config and force ``current_code_parity`` simulation mode.

    A paper-vs-lab reconciliation only makes sense against the parity contract.
    ``allow_research_relaxed`` is set so a partial research config (one that
    does not pin every live signal gate) still validates and runs.
    """
    from ..config import load_config

    cfg = load_config(lab_cfg) if isinstance(lab_cfg, (str, Path)) else copy.deepcopy(dict(lab_cfg))
    sim = dict(cfg.get("simulation") or {})
    sim["mode"] = "current_code_parity"
    sim.setdefault("allow_research_relaxed", True)
    cfg["simulation"] = sim
    return cfg


def run_lab_parity_session(lab_cfg: Any, session_date: Any, *, run_dir: Path | str | None = None):
    """Run the lab backtester for one session in ``current_code_parity`` mode.

    Returns the :class:`~bowaka_v2_lab.sim.backtester.BacktestResult`. The
    universe is the point-in-time universe built from the lake (a
    ``current_code_parity`` run refuses a synthetic universe); a fixture / smoke
    config without a lake falls back to the synthetic suppliers + universe and
    is run in ``smoke_fixture`` mode so the deterministic plumbing path still
    works for tests.
    """
    from ..backtest_runner import (
        paths_for,
        resolve_daily_cache,
        resolve_suppliers,
        resolve_symbols,
        uses_lake,
    )
    from ..sim.backtester import run_backtest
    from ..sim.replay_fixtures import synthetic_universe
    from ..sim.schedule import scan_times_for_session

    cfg = _force_parity_config(lab_cfg)
    session = _as_date(session_date)
    symbols = resolve_symbols(cfg)
    minute_supplier, daily_supplier = resolve_suppliers(cfg)
    daily_cache = resolve_daily_cache(cfg, symbols, session)

    if uses_lake(cfg):
        # current_code_parity over a lake: build the point-in-time universe so
        # the run is not refused for consuming a synthetic universe.
        from bowaka_common.marketdata import MarketDataStore

        from ..universe.builder import build_pit_universe

        md = cfg.get("market_data") or {}
        from ..data.lineage import _coerce_lake_root, resolve_lake_root
        store = MarketDataStore(
            _coerce_lake_root(resolve_lake_root(cfg)),
            vendor=md.get("vendor", "alpaca"),
        )
        universe = {session: build_pit_universe(session, cfg, store)}
    else:
        # No lake — fixture / smoke path. A synthetic universe is only legal in
        # smoke_fixture mode, so drop the run to that mode for the fixture path.
        cfg["simulation"]["mode"] = "smoke_fixture"
        universe = {session: synthetic_universe(symbols)}

    return run_backtest(
        cfg=cfg,
        sessions=[session],
        scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        universe_snapshot_by_session=universe,
        daily_cache_by_session={session: daily_cache},
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=daily_supplier,
        paths=paths_for(cfg),
        run_dir=Path(run_dir) if run_dir else None,
    )


# --------------------------------------------------------------------------
# Lab-record extraction from a BacktestResult.
# --------------------------------------------------------------------------
def _lab_candidates(result: Any) -> list[LabCandidate]:
    out: list[LabCandidate] = []
    for ev in getattr(result, "candidate_events", []) or []:
        feats = ev.get("features") or {}
        out.append(
            LabCandidate(
                event_id=str(ev.get("event_id")),
                session_date=ev.get("session_date"),
                symbol=str(ev.get("symbol")),
                scan_timestamp=ev.get("scan_timestamp"),
                signal_strength=feats.get("signal_strength"),
            )
        )
    return out


def _lab_decisions(result: Any) -> list[LabDecision]:
    out: list[LabDecision] = []
    for d in getattr(result, "decisions", []) or []:
        out.append(
            LabDecision(
                event_id=d.get("event_id"),
                candidate_event_id=d.get("candidate_event_id"),
                session_date=d.get("session_date"),
                symbol=str(d.get("symbol")),
                decision=d.get("decision"),
                reason=d.get("reason"),
                decision_timestamp=d.get("decision_timestamp"),
            )
        )
    return out


def _lab_orders_and_fills(result: Any) -> tuple[list[LabOrder], list[LabFill]]:
    """Extract lab orders + fills from the run-dir parquet artifacts.

    ``BacktestResult`` does not carry orders / fills in memory, but the
    backtester writes ``orders.parquet`` / ``fills.parquet`` (both stamped with
    ``candidate_event_id`` for orders). Fills are linked back to a candidate via
    the order map.
    """
    run_dir = Path(getattr(result, "run_dir"))
    orders: list[LabOrder] = []
    order_to_candidate: dict[str, str] = {}
    order_to_created_at: dict[str, str] = {}
    op = run_dir / "orders.parquet"
    if op.is_file():
        odf = pd.read_parquet(op)
        for _, r in odf.iterrows():
            poid = r.get("parent_order_id")
            if poid is None or (isinstance(poid, float) and pd.isna(poid)):
                continue
            cid = r.get("candidate_event_id")
            cid = None if (cid is None or (isinstance(cid, float) and pd.isna(cid))) else str(cid)
            if cid:
                order_to_candidate[str(poid)] = cid
            created = _opt_str(r.get("created_at"))
            if created:
                order_to_created_at[str(poid)] = created
            orders.append(
                LabOrder(
                    parent_order_id=str(poid),
                    candidate_event_id=cid,
                    symbol=str(r.get("symbol")),
                    side=_opt_str(r.get("side")),
                    qty=_opt_float(r.get("qty")),
                    limit_price=_opt_float(r.get("limit_price")),
                    submit_timestamp=_opt_str(r.get("created_at")),
                    status=_opt_str(r.get("status")),
                )
            )
    fills: list[LabFill] = []
    fp = run_dir / "fills.parquet"
    if fp.is_file():
        fdf = pd.read_parquet(fp)
        for _, r in fdf.iterrows():
            poid = r.get("parent_order_id")
            if poid is None or (isinstance(poid, float) and pd.isna(poid)):
                continue
            if not bool(r.get("filled", False)):
                continue  # only landed fills are comparable on price
            fills.append(
                LabFill(
                    parent_order_id=str(poid),
                    candidate_event_id=order_to_candidate.get(str(poid)),
                    symbol=str(r.get("symbol")),
                    filled_qty=_opt_float(r.get("filled_qty")),
                    avg_fill_price=_opt_float(r.get("avg_fill_price")),
                    # P10: the sim fills synchronously at order submit; the parent
                    # order's created_at is the real fill time available in the
                    # artifacts (fills.parquet carries no separate fill-time column).
                    # Non-None so fill-latency reconciliation is no longer vacuous.
                    fill_timestamp=order_to_created_at.get(str(poid)),
                )
            )
    return orders, fills


def _lab_exits(result: Any) -> list[LabExit]:
    """Extract lab lot exits from the in-memory trade records."""
    out: list[LabExit] = []
    for t in getattr(result, "trades", []) or []:
        out.append(
            LabExit(
                parent_order_id=t.get("parent_order_id"),
                position_id=t.get("position_id"),
                candidate_event_id=t.get("candidate_event_id"),
                symbol=str(t.get("symbol")),
                exit_reason=t.get("exit_reason"),
                exit_price=_opt_float(t.get("exit_price")),
                realized_pnl=_opt_float(t.get("pnl")),
                exit_timestamp=_opt_str(t.get("exit_timestamp")),
            )
        )
    return out


def _opt_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        if isinstance(v, float) and pd.isna(v):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _opt_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    return str(v)


# --------------------------------------------------------------------------
# Side-by-side row assembly.
# --------------------------------------------------------------------------
def _first_by_candidate(records: list[Any], *, prefix: str) -> dict[str, Any]:
    """Index records by candidate id, keeping the first per id."""
    out: dict[str, Any] = {}
    for rec in records:
        cid = getattr(rec, "candidate_event_id", None) or getattr(rec, "event_id", None)
        if not cid:
            data = rec.model_dump() if hasattr(rec, "model_dump") else dict(rec)
            cid = _normalize_candidate_id(data, fallback_prefix=prefix)
        out.setdefault(str(cid), rec)
    return out


def build_reconcile_rows(
    paper: _PaperSession,
    lab_candidates: list[LabCandidate],
    lab_decisions: list[LabDecision],
    lab_orders: list[LabOrder],
    lab_fills: list[LabFill],
    lab_exits: list[LabExit],
) -> list[ReconcileRow]:
    """Join paper + lab record sets into one :class:`ReconcileRow` per candidate.

    Every candidate id (paper-only, lab-only, both) gets exactly one row. The
    per-stage comparator outcomes are computed and stamped on the row.
    """
    diff = diff_candidate_sets(paper.candidates, lab_candidates)

    paper_cand = {c.event_id: c for c in paper.candidates}
    lab_cand = {c.event_id: c for c in lab_candidates}
    paper_dec = _first_by_candidate(paper.decisions, prefix="paper-dec")
    lab_dec = _first_by_candidate(lab_decisions, prefix="lab-dec")
    paper_ord = _first_by_candidate(paper.orders, prefix="paper-ord")
    lab_ord = _first_by_candidate(lab_orders, prefix="lab-ord")
    paper_fill = _first_by_candidate(paper.fills, prefix="paper-fill")
    lab_fill = _first_by_candidate(lab_fills, prefix="lab-fill")
    paper_exit = _first_by_candidate(paper.exits, prefix="paper-exit")
    lab_exit = _first_by_candidate(lab_exits, prefix="lab-exit")

    presence_by_id: dict[str, str] = {}
    for cid in diff.both:
        presence_by_id[cid] = "both"
    for cid in diff.paper_only:
        presence_by_id[cid] = "paper_only"
    for cid in diff.lab_only:
        presence_by_id[cid] = "lab_only"
    # A candidate that appears only on a downstream record (no candidate event
    # on either side) still gets a row so nothing is silently dropped.
    for extra in (
        set(paper_dec) | set(lab_dec) | set(paper_ord) | set(lab_ord)
        | set(paper_fill) | set(lab_fill) | set(paper_exit) | set(lab_exit)
    ):
        if extra not in presence_by_id:
            in_paper = extra in paper_dec or extra in paper_ord or extra in paper_fill or extra in paper_exit
            in_lab = extra in lab_dec or extra in lab_ord or extra in lab_fill or extra in lab_exit
            presence_by_id[extra] = (
                "both" if (in_paper and in_lab)
                else ("paper_only" if in_paper else "lab_only")
            )

    rows: list[ReconcileRow] = []
    for cid in sorted(presence_by_id):
        p_dec = paper_dec.get(cid)
        l_dec = lab_dec.get(cid)
        p_ord = paper_ord.get(cid)
        l_ord = lab_ord.get(cid)
        p_fill = paper_fill.get(cid)
        l_fill = lab_fill.get(cid)
        p_exit = paper_exit.get(cid)
        l_exit = lab_exit.get(cid)

        symbol = None
        for rec in (
            paper_cand.get(cid), lab_cand.get(cid), p_dec, l_dec,
            p_ord, l_ord, p_fill, l_fill, p_exit, l_exit,
        ):
            if rec is not None and getattr(rec, "symbol", None):
                symbol = rec.symbol
                break

        dec_cmp = compare_decision_reason(cid, p_dec, l_dec)
        fill_cmp = compare_fill(p_fill, l_fill)
        rows.append(
            ReconcileRow(
                candidate_event_id=cid,
                symbol=symbol,
                presence=presence_by_id[cid],
                paper_candidate=paper_cand.get(cid),
                lab_candidate=lab_cand.get(cid),
                paper_decision=p_dec,
                lab_decision=l_dec,
                paper_order=p_ord,
                lab_order=l_ord,
                paper_fill=p_fill,
                lab_fill=l_fill,
                paper_exit=p_exit,
                lab_exit=l_exit,
                decision_reason_match=dec_cmp.match,
                order_size_delta=compare_order_size(p_ord, l_ord),
                fill_price_delta_bps=fill_cmp.price_delta_bps,
                fill_qty_delta=fill_cmp.qty_delta,
                exit_reason_match=compare_exit_reason(p_exit, l_exit),
                pnl_delta=compare_pnl(p_exit, l_exit),
            )
        )
    return rows


# --------------------------------------------------------------------------
# Public entry point.
# --------------------------------------------------------------------------
def replay_paper_session(
    session_date: Any,
    paper_logs_root: Path | str | None,
    lab_cfg: Any,
    *,
    run_dir: Path | str | None = None,
) -> ReplayResult:
    """Replay one paper session against the lab and return a :class:`ReplayResult`.

    Parameters
    ----------
    session_date:
        The paper trading session to replay (``date`` / ``datetime`` / ISO str).
    paper_logs_root:
        Directory holding the paper-log JSONL files for the session. When
        ``None`` or non-existent the result is ``scaffolding_only`` — the lab
        still runs so the path is exercised, but no paper data is reconciled
        (the Phase-10 operator constraint: no real paper logs are supplied).
    lab_cfg:
        A v2 lab config (path or dict). The replay forces
        ``simulation.mode = current_code_parity`` — the only contract a
        paper-vs-lab reconciliation is meaningful against.
    run_dir:
        Optional override for the lab backtest run directory.

    Returns
    -------
    ReplayResult
        Side-by-side records keyed by ``candidate_event_id``.
    """
    session = _session_str(session_date)
    paper = (
        load_paper_session(paper_logs_root, session)
        if paper_logs_root is not None
        else _PaperSession([], [], [], [], [])
    )

    result = run_lab_parity_session(lab_cfg, session, run_dir=run_dir)
    lab_candidates = _lab_candidates(result)
    lab_decisions = _lab_decisions(result)
    lab_orders, lab_fills = _lab_orders_and_fills(result)
    lab_exits = _lab_exits(result)

    rows = build_reconcile_rows(
        paper, lab_candidates, lab_decisions, lab_orders, lab_fills, lab_exits
    )

    has_paper = bool(
        paper.candidates or paper.decisions or paper.orders or paper.fills or paper.exits
    )
    return ReplayResult(
        session_date=session,
        rows=rows,
        scaffolding_only=not has_paper,
        note=(
            None if has_paper
            else f"no paper logs found for session {session}; "
                 "lab ran but there is nothing to reconcile (scaffolding only)"
        ),
        lab_run_dir=str(getattr(result, "run_dir", "")) or None,
        lab_run_id=getattr(result, "run_id", None),
        n_paper_candidates=len(paper.candidates),
        n_lab_candidates=len(lab_candidates),
    )


__all__ = [
    "ReplayResult",
    "replay_paper_session",
    "load_paper_session",
    "run_lab_parity_session",
    "build_reconcile_rows",
]
