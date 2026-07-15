"""Convert openalgo bowaka_v2 live/paper event logs into the reconciler's
per-session paper-logs layout (Phase-10 reconciliation, audit 2026-05-29 §9).

Why this exists
---------------
The live strategy (``openalgo/strategies/scripts/bowaka_v2_strategy.py``) writes
append-only JSONL logs into ``strategies/scripts/data/bowaka_v2/``. Two of them
are already exactly the shape the reconciler's Phase-7 importer wants:

- ``candidate_events.jsonl`` — one row per emitted candidate (``event_id`` is the
  ``candidate_event_id`` the reconciler keys rows on).
- ``entry_decisions.jsonl`` — one row per accept/reject decision, carrying
  ``candidate_event_id`` / ``decision`` / ``reason`` / ``session_date``.

The third, ``trade_ledger.jsonl``, is a mixed event stream. Its ``closure`` rows
are completed round-trips that carry the WHOLE lifecycle keyed by
``candidate_event_id`` + ``link_id``: the entry fill (``entry_price`` /
``entry_timestamp`` / ``qty``) and the exit (``exit_price`` / ``exit_timestamp`` /
``reason`` / ``realized_pnl``). The reconciler instead wants three separate files
(``orders.jsonl`` / ``fills.jsonl`` / ``exits.jsonl``), so this adapter
synthesises them — one parent order + one entry fill + one exit per closed lot.

What it does
------------
1. Groups ``candidate_events`` + ``entry_decisions`` by their ``session_date``.
2. Synthesises ``orders`` / ``fills`` / ``exits`` from the ``closure`` rows,
   deriving each row's session from its ``candidate_event_id`` (the ENTRY
   session — ``bowaka_v2:{session}:{symbol}:{scan_ts}``).
3. Writes one ``<out_root>/<YYYY-MM-DD>/`` directory per session, holding
   ``candidate_events.jsonl`` / ``entry_decisions.jsonl`` / ``orders.jsonl`` /
   ``fills.jsonl`` / ``exits.jsonl`` — the layout
   :func:`reconcile.importer.discover_sessions` and
   :func:`reconcile.replay.load_paper_session` consume.

Safety / scope
--------------
Read-only against the three JSONL files; it NEVER touches the live bot and
writes only under ``out_root``. Open (not-yet-closed) positions are skipped —
their ``entry_fill`` ledger rows carry no ``candidate_event_id`` and so cannot be
keyed to a candidate for reconciliation; the skipped count is reported.
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

# Source (openalgo) log filenames.
OPENALGO_CANDIDATES = "candidate_events.jsonl"
OPENALGO_DECISIONS = "entry_decisions.jsonl"
OPENALGO_LEDGER = "trade_ledger.jsonl"

# Reconciler (Phase-7) per-session output filenames.
OUT_CANDIDATES = "candidate_events.jsonl"
OUT_DECISIONS = "entry_decisions.jsonl"
OUT_ORDERS = "orders.jsonl"
OUT_FILLS = "fills.jsonl"
OUT_EXITS = "exits.jsonl"


def _read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file into a list of dicts; missing file -> []; bad rows skipped."""
    if not path.is_file():
        return []
    out: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except ValueError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    """Write ``rows`` as JSONL (compact), returning the row count written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":"), default=str))
            fh.write("\n")
            n += 1
    return n


def _is_date(value: Any) -> bool:
    try:
        _dt.datetime.strptime(str(value), "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def session_from_candidate_id(cid: Optional[str]) -> Optional[str]:
    """Return the session date embedded in ``candidate_event_id``.

    The live strategy stamps ``bowaka_v2:{session}:{symbol}:{scan_ts}`` so the
    session date is the second colon-delimited field (robust to the timestamp's
    own colons). Returns ``None`` when ``cid`` is missing / malformed.
    """
    if not cid:
        return None
    parts = str(cid).split(":")
    if len(parts) >= 2 and _is_date(parts[1]):
        return parts[1]
    return None


def _et_date(ts_iso: Optional[str]) -> Optional[str]:
    """America/New_York calendar date of a UTC ISO timestamp (fallback session).

    Uses the stdlib zoneinfo; returns ``None`` if the timestamp can't be parsed
    or the tz database is unavailable.
    """
    if not ts_iso:
        return None
    try:
        from zoneinfo import ZoneInfo

        s = str(ts_iso).replace("Z", "+00:00")
        dt = _dt.datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_dt.timezone.utc)
        return dt.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:  # noqa: BLE001 — best-effort fallback only
        return None


def _parse_ts(value: Any) -> Optional[_dt.datetime]:
    if not value:
        return None
    try:
        s = str(value).replace("Z", "+00:00")
        dt = _dt.datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=_dt.timezone.utc)
    except Exception:  # noqa: BLE001
        return None


def _seconds_between(start_iso: Any, end_iso: Any) -> Optional[float]:
    """Signed seconds from ``start`` to ``end`` (None if either is unparseable)."""
    a, b = _parse_ts(start_iso), _parse_ts(end_iso)
    if a is None or b is None:
        return None
    return (b - a).total_seconds()


def _latency_summary(values: list[float]) -> dict:
    """n / median / p90 / max (seconds) for a latency sample; ``{"n": 0}`` if empty."""
    if not values:
        return {"n": 0}
    import statistics

    v = sorted(values)
    p90_idx = min(len(v) - 1, int(round(0.9 * (len(v) - 1))))
    return {
        "n": len(v),
        "median_s": round(statistics.median(v), 3),
        "p90_s": round(v[p90_idx], 3),
        "max_s": round(v[-1], 3),
    }


def _row_session(rec: dict, ts_key: str) -> Optional[str]:
    """Resolve a record's session date: ``session_date`` field, else ET(ts)."""
    sd = rec.get("session_date")
    if sd is not None and _is_date(sd):
        return str(sd)
    return _et_date(rec.get(ts_key))


def is_closure(row: dict) -> bool:
    """True for a trade_ledger completed round-trip row."""
    return row.get("record_type") == "closure" or row.get("event_type") == "closure"


def synth_from_closure(closure: dict) -> Optional[tuple[str, dict, dict, dict]]:
    """Build ``(session, order, fill, exit)`` dicts from one ``closure`` ledger row.

    Returns ``None`` when the row cannot be keyed to a session (no
    ``candidate_event_id`` and no parseable ``entry_timestamp``). The three
    synthesised records are keyed by ``candidate_event_id`` (row join key) and
    ``parent_order_id`` = the ledger ``link_id``.
    """
    cid = closure.get("candidate_event_id")
    session = session_from_candidate_id(cid) or _et_date(closure.get("entry_timestamp"))
    if session is None:
        return None
    poid = closure.get("link_id")
    sym = closure.get("symbol")
    qty = closure.get("qty")

    order = {
        "parent_order_id": poid,
        "candidate_event_id": cid,
        "symbol": sym,
        "side": "buy",
        "qty": qty,
        "limit_price": closure.get("entry_price"),
        "submit_timestamp": closure.get("entry_timestamp"),
        "status": "filled",
        "session_date": session,
    }
    fill = {
        "parent_order_id": poid,
        "candidate_event_id": cid,
        "symbol": sym,
        "filled_qty": qty,
        "avg_fill_price": closure.get("entry_price"),
        "fill_timestamp": closure.get("entry_timestamp"),
        "session_date": session,
    }
    exit_ = {
        "parent_order_id": poid,
        "candidate_event_id": cid,
        "symbol": sym,
        "exit_reason": closure.get("reason"),
        "exit_price": closure.get("exit_price"),
        "realized_pnl": closure.get("realized_pnl"),
        "exit_timestamp": closure.get("exit_timestamp"),
        "session_date": session,
    }
    return session, order, fill, exit_


def _lift_signal_strength(cand: dict) -> dict:
    """Copy ``features.signal_strength`` up to the top level if not already there."""
    if cand.get("signal_strength") is None:
        feats = cand.get("features")
        if isinstance(feats, dict) and feats.get("signal_strength") is not None:
            cand = dict(cand)
            cand["signal_strength"] = feats.get("signal_strength")
    return cand


@dataclass
class AdaptResult:
    out_root: str
    sessions: list[str] = field(default_factory=list)
    n_candidates: int = 0
    n_decisions: int = 0
    n_closures: int = 0
    n_orders: int = 0
    n_fills: int = 0
    n_exits: int = 0
    n_open_skipped: int = 0
    n_unkeyed_closures: int = 0
    # Latency capture (Tier 0 fill->attach, Tier 1 submit->fill).
    n_parent_submits: int = 0
    n_parent_fills: int = 0
    n_oco_attached: int = 0
    latency_summary: dict = field(default_factory=dict)
    per_session: dict[str, dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "out_root": self.out_root,
            "n_sessions": len(self.sessions),
            "sessions": self.sessions,
            "n_candidates": self.n_candidates,
            "n_decisions": self.n_decisions,
            "n_closures": self.n_closures,
            "n_orders": self.n_orders,
            "n_fills": self.n_fills,
            "n_exits": self.n_exits,
            "n_open_skipped": self.n_open_skipped,
            "n_unkeyed_closures": self.n_unkeyed_closures,
            "n_parent_submits": self.n_parent_submits,
            "n_parent_fills": self.n_parent_fills,
            "n_oco_attached": self.n_oco_attached,
            "latency_summary": self.latency_summary,
            "per_session": self.per_session,
        }


def adapt_openalgo_logs(
    src_dir: Path | str,
    out_root: Path | str,
    *,
    sessions: Optional[Iterable[str]] = None,
    lift_signal_strength: bool = True,
) -> AdaptResult:
    """Convert openalgo bowaka_v2 logs under ``src_dir`` into ``out_root``.

    Parameters
    ----------
    src_dir:
        The openalgo ``strategies/scripts/data/bowaka_v2`` directory (holding
        ``candidate_events.jsonl`` / ``entry_decisions.jsonl`` /
        ``trade_ledger.jsonl``).
    out_root:
        Output paper-logs root; one ``<YYYY-MM-DD>/`` dir is written per session.
    sessions:
        Optional whitelist of ``YYYY-MM-DD`` sessions to emit (default: all).
    lift_signal_strength:
        Copy ``features.signal_strength`` to the top level of candidate rows so
        the reconciler's ``PaperCandidate`` sees it directly.
    """
    src = Path(src_dir)
    out = Path(out_root)
    want = set(sessions) if sessions is not None else None

    candidates = _read_jsonl(src / OPENALGO_CANDIDATES)
    decisions = _read_jsonl(src / OPENALGO_DECISIONS)
    ledger = _read_jsonl(src / OPENALGO_LEDGER)

    # Group candidates + decisions by session.
    cand_by_session: dict[str, list[dict]] = {}
    for c in candidates:
        s = _row_session(c, "scan_timestamp") or session_from_candidate_id(c.get("event_id"))
        if s is None:
            continue
        cand_by_session.setdefault(s, []).append(_lift_signal_strength(c) if lift_signal_strength else c)

    dec_by_session: dict[str, list[dict]] = {}
    for d in decisions:
        s = _row_session(d, "decision_timestamp") or session_from_candidate_id(d.get("candidate_event_id"))
        if s is None:
            continue
        dec_by_session.setdefault(s, []).append(d)

    # Synthesise orders/fills/exits from closure rows.
    ord_by_session: dict[str, list[dict]] = {}
    fill_by_session: dict[str, list[dict]] = {}
    exit_by_session: dict[str, list[dict]] = {}
    n_closures = n_unkeyed = 0
    closure_link_ids: set[str] = set()
    entry_link_ids: set[str] = set()
    for row in ledger:
        if is_closure(row):
            n_closures += 1
            if row.get("link_id"):
                closure_link_ids.add(str(row.get("link_id")))
            built = synth_from_closure(row)
            if built is None:
                n_unkeyed += 1
                continue
            s, order, fill, exit_ = built
            ord_by_session.setdefault(s, []).append(order)
            fill_by_session.setdefault(s, []).append(fill)
            exit_by_session.setdefault(s, []).append(exit_)
        elif row.get("event_type") == "entry_fill" and row.get("link_id"):
            entry_link_ids.add(str(row.get("link_id")))

    # Truly-open = an entry whose link_id never produced a closure row. These are
    # skipped (their entry_fill rows carry no candidate_event_id to key on).
    n_open_skipped = len(entry_link_ids - closure_link_ids)

    # --- Latency capture: join ledger events by link_id, build the Phase-9 latency
    # event rows (paper_parent_submits / paper_parent_fills / paper_oco_attached).
    #   Tier 1 submit->fill  = entry_fill.ts        - parent_submitted_at
    #   Tier 0 fill->attach  = bracket_attached.ts  - entry_fill.ts
    # The `ts` on each ledger event is its emission time; parent_submitted_at is
    # carried on entry_fill (new logs) or falls back to closure.entry_timestamp.
    timing: dict[str, dict] = {}
    for row in ledger:
        lk = row.get("link_id")
        if not lk:
            continue
        lk = str(lk)
        et = row.get("event_type")
        t = timing.setdefault(lk, {})
        if row.get("symbol") and not t.get("symbol"):
            t["symbol"] = row.get("symbol")
        if et == "entry_fill":
            t["fill_ts"] = row.get("ts")
            if row.get("filled_qty") is not None:
                t["qty"] = row.get("filled_qty")
            if row.get("filled_avg_price") is not None:
                t["price"] = row.get("filled_avg_price")
            if row.get("candidate_event_id"):
                t["cid"] = row.get("candidate_event_id")
            if row.get("parent_submitted_at"):
                t["submit_ts"] = row.get("parent_submitted_at")
        elif et == "bracket_attached":
            t["attach_ts"] = row.get("ts")
            t["stop_price"] = row.get("stop_price")
            t["target_price"] = row.get("target_price")
        elif is_closure(row):
            if row.get("candidate_event_id"):
                t["cid"] = row.get("candidate_event_id")
            if not t.get("submit_ts"):
                t["submit_ts"] = row.get("entry_timestamp")  # submit-time fallback
            if t.get("qty") is None:
                t["qty"] = row.get("qty")
            if t.get("price") is None:
                t["price"] = row.get("entry_price")

    submit_by_session: dict[str, list[dict]] = {}
    pfill_by_session: dict[str, list[dict]] = {}
    attach_by_session: dict[str, list[dict]] = {}
    s2f_list: list[float] = []
    f2a_list: list[float] = []
    for lk, t in timing.items():
        cid = t.get("cid")
        submit_ts, fill_ts, attach_ts = t.get("submit_ts"), t.get("fill_ts"), t.get("attach_ts")
        session = session_from_candidate_id(cid) or _et_date(submit_ts) or _et_date(fill_ts)
        if session is None:
            continue
        sym = t.get("symbol")
        if submit_ts:
            submit_by_session.setdefault(session, []).append({
                "timestamp": submit_ts, "symbol": sym, "parent_order_id": lk,
                "candidate_event_id": cid, "submit_timestamp": submit_ts,
                "session_date": session,
            })
        if fill_ts:
            pfill_by_session.setdefault(session, []).append({
                "timestamp": fill_ts, "symbol": sym, "parent_order_id": lk,
                "candidate_event_id": cid, "fill_timestamp": fill_ts,
                "filled_qty": t.get("qty"), "avg_fill_price": t.get("price"),
                "session_date": session,
            })
        if attach_ts:
            attach_by_session.setdefault(session, []).append({
                "timestamp": attach_ts, "symbol": sym, "parent_order_id": lk,
                "candidate_event_id": cid, "attached_timestamp": attach_ts,
                "stop_price": t.get("stop_price"), "target_price": t.get("target_price"),
                "session_date": session,
            })
        s2f = _seconds_between(submit_ts, fill_ts)
        if s2f is not None and s2f >= 0:
            s2f_list.append(s2f)
        f2a = _seconds_between(fill_ts, attach_ts)
        if f2a is not None and f2a >= 0:
            f2a_list.append(f2a)

    all_sessions = sorted(
        set(cand_by_session) | set(dec_by_session) | set(ord_by_session)
        | set(pfill_by_session) | set(submit_by_session) | set(attach_by_session)
    )
    if want is not None:
        all_sessions = [s for s in all_sessions if s in want]

    res = AdaptResult(out_root=str(out))
    res.n_closures = n_closures
    res.n_open_skipped = n_open_skipped
    res.n_unkeyed_closures = n_unkeyed

    for s in all_sessions:
        sdir = out / s
        c_rows = cand_by_session.get(s, [])
        d_rows = dec_by_session.get(s, [])
        o_rows = ord_by_session.get(s, [])
        f_rows = fill_by_session.get(s, [])
        e_rows = exit_by_session.get(s, [])
        nc = _write_jsonl(sdir / OUT_CANDIDATES, c_rows)
        nd = _write_jsonl(sdir / OUT_DECISIONS, d_rows)
        no = _write_jsonl(sdir / OUT_ORDERS, o_rows)
        nf = _write_jsonl(sdir / OUT_FILLS, f_rows)
        ne = _write_jsonl(sdir / OUT_EXITS, e_rows)
        # Phase-9 latency event files (consumed by the reconciler's fill-latency /
        # OCO-attach calibrators). Absent files are tolerated downstream.
        ns = _write_jsonl(sdir / "paper_parent_submits.jsonl", submit_by_session.get(s, []))
        npf = _write_jsonl(sdir / "paper_parent_fills.jsonl", pfill_by_session.get(s, []))
        na = _write_jsonl(sdir / "paper_oco_attached.jsonl", attach_by_session.get(s, []))
        res.sessions.append(s)
        res.n_candidates += nc
        res.n_decisions += nd
        res.n_orders += no
        res.n_fills += nf
        res.n_exits += ne
        res.n_parent_submits += ns
        res.n_parent_fills += npf
        res.n_oco_attached += na
        res.per_session[s] = {
            "candidates": nc, "decisions": nd, "orders": no, "fills": nf, "exits": ne,
            "parent_submits": ns, "parent_fills": npf, "oco_attached": na,
        }
    res.latency_summary = {
        "submit_to_fill_seconds": _latency_summary(s2f_list),
        "fill_to_attach_seconds": _latency_summary(f2a_list),
    }
    return res


__all__ = [
    "AdaptResult",
    "adapt_openalgo_logs",
    "synth_from_closure",
    "session_from_candidate_id",
    "is_closure",
    "OPENALGO_CANDIDATES",
    "OPENALGO_DECISIONS",
    "OPENALGO_LEDGER",
]
