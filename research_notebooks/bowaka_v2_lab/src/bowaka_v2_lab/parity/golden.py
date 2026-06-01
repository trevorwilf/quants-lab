"""Golden-bundle persistence + diff — the parity fidelity gate (Phase 0).

A *golden bundle* is the canonical, diffable snapshot of a parity run: the
:class:`ParityReport` scalar fields + the full prod/lab trade rows + the lab
candidate stream, serialized to JSON. Phase 0 captures it once on the repaired
oracle; every later speedup phase re-runs parity and proves it reproduced the
baseline EXACTLY — identical per-trade rows, identical candidate stream,
identical report fields — within the speedup prompt's tolerances:

    price 1e-12, objective/pnl 1e-9   (rule 5 / scripts/check_worker_count_parity.py)

``diff_parity_bundles(golden_dir, candidate_dir)`` returns ``{"match": bool, ...}``
with the offending rows when they drift, so a phase gate is simply
``assert diff_parity_bundles(GOLDEN, run)["match"]``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

#: Tolerances from the speedup prompt (rule 5).
PRICE_TOL = 1e-12
PNL_TOL = 1e-9

#: Report fields compared by the gate. ``_REPORT_NUMERIC`` are compared within
#: ``PNL_TOL``; the rest are compared exactly.
_REPORT_FIELDS = (
    "window_start", "window_end", "universe_size", "n_sessions", "n_trade_sessions",
    "prod_n_candidates", "prod_n_trades", "prod_gross_pnl",
    "lab_n_candidates", "lab_n_trades", "lab_gross_pnl",
    "candidate_recall", "gate_match_rate", "trade_intersection_rate",
    "fill_price_mae_bps", "exit_reason_match_rate", "daily_pnl_sign_match_rate",
    "passes_audit_thresholds", "failing_metrics",
)
_REPORT_NUMERIC = frozenset({
    "prod_gross_pnl", "lab_gross_pnl", "candidate_recall", "gate_match_rate",
    "trade_intersection_rate", "fill_price_mae_bps", "exit_reason_match_rate",
    "daily_pnl_sign_match_rate",
})


def _iso(x: Any) -> Any:
    return x.isoformat() if x is not None else None


def _trade_row(t: Any) -> dict:
    return {
        "session_date": _iso(t.session_date),
        "symbol": t.symbol,
        "entry_ts_minute": _iso(t.entry_ts_minute),
        "entry_price": t.entry_price,
        "qty_filled": t.qty_filled,
        "exit_ts_minute": _iso(t.exit_ts_minute),
        "exit_price": t.exit_price,
        "exit_reason": t.exit_reason,
        "pnl_dollars": t.pnl_dollars,
    }


def _cand_row(c: Any) -> dict:
    return {
        "session_date": _iso(c.session_date),
        "symbol": c.symbol,
        "candidate_ts_minute": _iso(c.candidate_ts_minute),
        "gate_passed": c.gate_passed,
        "gate_rejection_reason": c.gate_rejection_reason,
    }


def _report_dict(report: Any) -> dict:
    out: dict[str, Any] = {}
    for k in _REPORT_FIELDS:
        v = getattr(report, k)
        if k in ("window_start", "window_end"):
            v = _iso(v)
        elif k == "failing_metrics":
            v = sorted(v)
        out[k] = v
    return out


def _trade_key(r: dict) -> tuple:
    return (r["session_date"], r["symbol"], r["entry_ts_minute"] or "")


def _cand_key(r: dict) -> tuple:
    return (r["session_date"], r["symbol"], r["candidate_ts_minute"] or "")


def persist_parity_bundle(
    out_dir: Path | str,
    *,
    report: Any,
    prod_trades: Sequence[Any],
    lab_trades: Sequence[Any],
    lab_candidates: Sequence[Any],
) -> Path:
    """Write a golden bundle (report.json + prod/lab trades + lab candidates)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(
        json.dumps(_report_dict(report), indent=2, sort_keys=True), encoding="utf-8")
    pt = sorted((_trade_row(t) for t in prod_trades), key=_trade_key)
    lt = sorted((_trade_row(t) for t in lab_trades), key=_trade_key)
    lc = sorted((_cand_row(c) for c in lab_candidates), key=_cand_key)
    (out_dir / "prod_trades.json").write_text(json.dumps(pt, indent=2), encoding="utf-8")
    (out_dir / "lab_trades.json").write_text(json.dumps(lt, indent=2), encoding="utf-8")
    (out_dir / "lab_candidates.json").write_text(json.dumps(lc, indent=2), encoding="utf-8")
    return out_dir


def load_parity_bundle(bundle_dir: Path | str) -> dict:
    bundle_dir = Path(bundle_dir)
    return {
        "report": json.loads((bundle_dir / "report.json").read_text(encoding="utf-8")),
        "prod_trades": json.loads((bundle_dir / "prod_trades.json").read_text(encoding="utf-8")),
        "lab_trades": json.loads((bundle_dir / "lab_trades.json").read_text(encoding="utf-8")),
        "lab_candidates": json.loads((bundle_dir / "lab_candidates.json").read_text(encoding="utf-8")),
    }


def _close(a: Any, b: Any, tol: float) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= tol


def _diff_trades(golden: list, cand: list, *, price_tol: float, pnl_tol: float, label: str) -> list:
    diffs: list[dict] = []
    g_by = {_trade_key(r): r for r in golden}
    c_by = {_trade_key(r): r for r in cand}
    for k in sorted(set(g_by) | set(c_by)):
        if k not in c_by:
            diffs.append({"label": label, "key": list(k), "kind": "missing_in_candidate"})
            continue
        if k not in g_by:
            diffs.append({"label": label, "key": list(k), "kind": "extra_in_candidate"})
            continue
        g, c = g_by[k], c_by[k]
        for f in ("entry_price", "exit_price"):
            if not _close(g[f], c[f], price_tol):
                diffs.append({"label": label, "key": list(k), "field": f,
                              "golden": g[f], "candidate": c[f]})
        if not _close(g["pnl_dollars"], c["pnl_dollars"], pnl_tol):
            diffs.append({"label": label, "key": list(k), "field": "pnl_dollars",
                          "golden": g["pnl_dollars"], "candidate": c["pnl_dollars"]})
        for f in ("qty_filled", "exit_reason", "exit_ts_minute"):
            if g[f] != c[f]:
                diffs.append({"label": label, "key": list(k), "field": f,
                              "golden": g[f], "candidate": c[f]})
    return diffs


def _diff_cands(golden: list, cand: list) -> list:
    diffs: list[dict] = []
    g_by = {_cand_key(r): r for r in golden}
    c_by = {_cand_key(r): r for r in cand}
    for k in sorted(set(g_by) | set(c_by)):
        if k not in c_by:
            diffs.append({"label": "lab_candidates", "key": list(k), "kind": "missing_in_candidate"})
            continue
        if k not in g_by:
            diffs.append({"label": "lab_candidates", "key": list(k), "kind": "extra_in_candidate"})
            continue
        g, c = g_by[k], c_by[k]
        for f in ("gate_passed", "gate_rejection_reason"):
            if g[f] != c[f]:
                diffs.append({"label": "lab_candidates", "key": list(k), "field": f,
                              "golden": g[f], "candidate": c[f]})
    return diffs


def diff_parity_bundles(
    golden_dir: Path | str,
    candidate_dir: Path | str,
    *,
    price_tol: float = PRICE_TOL,
    pnl_tol: float = PNL_TOL,
) -> dict:
    """Compare a candidate bundle against the golden. ``{"match": bool, ...}``."""
    g = load_parity_bundle(golden_dir)
    c = load_parity_bundle(candidate_dir)
    report_diffs: list[dict] = []
    for k in _REPORT_FIELDS:
        gv, cv = g["report"].get(k), c["report"].get(k)
        ok = _close(gv, cv, pnl_tol) if k in _REPORT_NUMERIC else (gv == cv)
        if not ok:
            report_diffs.append({"field": k, "golden": gv, "candidate": cv})
    trade_diffs = _diff_trades(g["prod_trades"], c["prod_trades"],
                               price_tol=price_tol, pnl_tol=pnl_tol, label="prod_trades")
    trade_diffs += _diff_trades(g["lab_trades"], c["lab_trades"],
                                price_tol=price_tol, pnl_tol=pnl_tol, label="lab_trades")
    cand_diffs = _diff_cands(g["lab_candidates"], c["lab_candidates"])
    return {
        "match": not (report_diffs or trade_diffs or cand_diffs),
        "report_diffs": report_diffs,
        "trade_diffs": trade_diffs,
        "candidate_diffs": cand_diffs,
    }


__all__ = [
    "PRICE_TOL", "PNL_TOL",
    "persist_parity_bundle", "load_parity_bundle", "diff_parity_bundles",
]
