"""Side-specific output normalizers for production-vs-lab parity.

Discovered output shapes (from reading the source at dev HEAD; update if either
side changes columns).

Production ``trades.parquet`` columns
    (mirror of ``reference/source_strategy/scripts/bowaka_v2_backtest.py:BacktestTrade``):
    ``session_date`` (str ``YYYY-MM-DD``), ``symbol`` (str), ``entry_ts`` (str ISO),
    ``entry_price`` (float), ``qty`` (int), ``notional`` (float),
    ``stop_price`` (float), ``target_price`` (float),
    ``max_hold_session_minutes`` (int), ``exit_ts`` (str|None),
    ``exit_price`` (float|None), ``exit_reason`` (str|None),
    ``pnl_dollars`` (float|None), ``pnl_pct`` (float|None),
    ``adv_at_entry`` (float|None), ``spread_bps_at_entry`` (float|None).

Production ``summary.json`` keys (mirror of ``BacktestSummary``):
    ``trade_count``, ``win_count``, ``win_rate``, ``mean_pnl_pct``,
    ``median_pnl_pct``, ``total_pnl``, ``exits_by_reason``.

Lab ``BacktestResult.trades`` row keys (per
``src/bowaka_v2_lab/sim/backtester.py:BacktestResult``: ``list[dict]``):
    ``session_date`` (date|str), ``symbol`` (str), ``entry_timestamp`` /
    ``entry_ts`` (str|datetime, defensive), ``entry_price`` (float),
    ``qty`` (int|float), ``exit_timestamp`` / ``exit_ts``, ``exit_price``,
    ``exit_reason``, ``pnl`` / ``pnl_dollars``, ``entry_date``.

Lab ``candidate_events`` row keys (best-effort): ``session_date`` (date|str),
``symbol``, ``scan_timestamp`` / ``ts``, ``passed_gates`` / ``gate_passed``,
``gate_rejection_reason``.

Field mapping (canonicalized):
    session_date  -> NormalizedTrade.session_date          (date)
    symbol        -> NormalizedTrade.symbol                (str)
    entry_ts (UTC)-> NormalizedTrade.entry_ts_minute       (floor to minute)
    entry_price   -> NormalizedTrade.entry_price
    qty           -> NormalizedTrade.qty_filled            (int)
    exit_ts (UTC) -> NormalizedTrade.exit_ts_minute        (floor to minute)
    exit_price    -> NormalizedTrade.exit_price
    exit_reason   -> NormalizedTrade.exit_reason           (canonicalized lower)
    pnl_dollars   -> NormalizedTrade.pnl_dollars
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import pandas as pd

from .schemas import NormalizedCandidate, NormalizedTrade


def _parse_date(value: Any) -> _dt.date:
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    if value is None:
        raise ValueError("session_date is None")
    s = str(value)[:10]
    return _dt.date.fromisoformat(s)


def _to_utc_minute(value: Any) -> _dt.datetime:
    """Parse a timestamp-like value to a tz-aware UTC ``datetime`` floored to the minute."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    ts = ts.floor("1min")
    return ts.to_pydatetime()


def _to_utc_minute_or_none(value: Any) -> Optional[_dt.datetime]:
    if value is None or (isinstance(value, float) and value != value):  # NaN
        return None
    try:
        if isinstance(value, str) and not value.strip():
            return None
        return _to_utc_minute(value)
    except Exception:  # noqa: BLE001 — malformed timestamps surface as missing
        return None


def _canonical_exit_reason(value: Any) -> Optional[str]:
    """Lowercase + collapse signal-fade tier names to a canonical form.

    Examples
    --------
    ``"STOP"`` -> ``"stop"``,
    ``"SignalFadeSoft"`` -> ``"signal_fade_soft"``,
    ``"signal_fade"`` with tier hint left to the caller -> ``"signal_fade"``.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.lower()
    # Canonicalize CamelCase / dash / space variants to snake_case.
    out: list[str] = []
    for i, ch in enumerate(s):
        if ch in (" ", "-"):
            out.append("_")
            continue
        out.append(ch)
    s = "".join(out)
    # Collapse runs of "__".
    while "__" in s:
        s = s.replace("__", "_")
    return s


def _get(row: Any, *names: str, default: Any = None) -> Any:
    """Defensive accessor — dicts via ``.get``, dataclasses / pandas Series via ``getattr`` /
    item lookup. Returns the first present, non-NaN value among ``names``."""
    for name in names:
        try:
            v = row[name] if isinstance(row, Mapping) else getattr(row, name)
        except (KeyError, AttributeError):
            continue
        if v is None:
            continue
        if isinstance(v, float) and v != v:
            continue
        return v
    return default


# --------------------------------------------------------------------------
# Production side
# --------------------------------------------------------------------------
def _normalize_production_trades_df(df: pd.DataFrame) -> list[NormalizedTrade]:
    out: list[NormalizedTrade] = []
    for _, row in df.iterrows():
        try:
            sd = _parse_date(_get(row, "session_date"))
            sym = str(_get(row, "symbol"))
            entry_min = _to_utc_minute(_get(row, "entry_ts"))
        except Exception:  # noqa: BLE001 — malformed row drops out
            continue
        out.append(NormalizedTrade(
            session_date=sd, symbol=sym, entry_ts_minute=entry_min,
            entry_price=float(_get(row, "entry_price", default=0.0) or 0.0),
            qty_filled=int(_get(row, "qty", default=0) or 0),
            exit_ts_minute=_to_utc_minute_or_none(_get(row, "exit_ts")),
            exit_price=(float(v) if (v := _get(row, "exit_price")) is not None else None),
            exit_reason=_canonical_exit_reason(_get(row, "exit_reason")),
            pnl_dollars=float(_get(row, "pnl_dollars", default=0.0) or 0.0),
        ))
    return out


def normalize_production_output(
    prod_result: Any,
) -> tuple[list[NormalizedTrade], list[NormalizedCandidate]]:
    """Read the production backtester's outputs (``trades.parquet`` +
    ``summary.json``) and normalize to the common schema.

    ``prod_result`` is either a ``ProductionRunResult`` (with ``trades_path``
    attribute) or a path-like to a directory holding ``trades.parquet``.
    Production does not emit candidate-level telemetry by default, so the
    candidate list is empty.
    """
    if hasattr(prod_result, "trades_path"):
        trades_path = Path(prod_result.trades_path)
    else:
        d = Path(prod_result)
        trades_path = d / "trades.parquet"
    if trades_path.suffix == ".json" or not trades_path.is_file():
        # Fallback to trades.parquet in the same directory.
        candidate = trades_path.parent / "trades.parquet"
        if candidate.is_file():
            trades_path = candidate
    if not trades_path.is_file():
        return [], []
    df = pd.read_parquet(trades_path)
    if df.empty:
        return [], []
    return _normalize_production_trades_df(df), []


# --------------------------------------------------------------------------
# Lab side
# --------------------------------------------------------------------------
def _normalize_lab_trades(rows: Iterable[Mapping[str, Any]]) -> list[NormalizedTrade]:
    out: list[NormalizedTrade] = []
    for row in rows:
        try:
            sd = _parse_date(_get(row, "session_date", "entry_date"))
            sym = str(_get(row, "symbol"))
        except Exception:  # noqa: BLE001
            continue
        # Phase 0 (parity oracle): a missing/NaT entry timestamp used to fall
        # through to ``pd.Timestamp(None) -> NaT`` SILENTLY, so every lab trade
        # got a NaT join key and ``trade_intersection_rate`` was structurally ~0
        # regardless of real behavior. Fail loud — never let NaT become a key.
        entry_min = _to_utc_minute_or_none(
            _get(row, "entry_timestamp", "entry_ts", "scan_timestamp")
        )
        if entry_min is None:
            raise ValueError(
                "lab trade is missing a parseable entry timestamp "
                "(entry_timestamp|entry_ts|scan_timestamp); a NaT join key would "
                f"silently zero trade_intersection_rate. Offending row: {row!r}"
            )
        out.append(NormalizedTrade(
            session_date=sd, symbol=sym, entry_ts_minute=entry_min,
            entry_price=float(_get(row, "entry_price", default=0.0) or 0.0),
            qty_filled=int(_get(row, "qty", "qty_filled", "filled_qty", default=0) or 0),
            exit_ts_minute=_to_utc_minute_or_none(
                _get(row, "exit_timestamp", "exit_ts")
            ),
            exit_price=(float(v) if (v := _get(row, "exit_price")) is not None else None),
            exit_reason=_canonical_exit_reason(_get(row, "exit_reason")),
            pnl_dollars=float(_get(row, "pnl_dollars", "pnl", default=0.0) or 0.0),
        ))
    return out


def _normalize_lab_candidates(
    rows: Iterable[Mapping[str, Any]],
) -> list[NormalizedCandidate]:
    out: list[NormalizedCandidate] = []
    for row in rows:
        try:
            sd = _parse_date(_get(row, "session_date", "scan_date"))
            sym = str(_get(row, "symbol"))
            cand_min = _to_utc_minute(_get(row, "scan_timestamp", "ts", "timestamp"))
        except Exception:  # noqa: BLE001
            continue
        passed = _get(row, "passed_gates", "gate_passed", "passed")
        gate_passed = bool(passed) if passed is not None else False
        rej = _get(row, "gate_rejection_reason", "rejection_reason", "reason")
        out.append(NormalizedCandidate(
            session_date=sd, symbol=sym, candidate_ts_minute=cand_min,
            gate_passed=gate_passed,
            gate_rejection_reason=(None if gate_passed else (str(rej) if rej else None)),
        ))
    return out


def normalize_lab_output(
    lab_result: Any,
) -> tuple[list[NormalizedTrade], list[NormalizedCandidate]]:
    """Normalize a ``BacktestResult`` (or any object with ``trades`` /
    ``candidate_events`` attributes / keys) to the common schema."""
    trades_rows = _get(lab_result, "trades", default=None) or []
    candidate_rows = _get(lab_result, "candidate_events", default=None) or []
    return _normalize_lab_trades(trades_rows), _normalize_lab_candidates(candidate_rows)


__all__ = [
    "normalize_production_output",
    "normalize_lab_output",
    "_normalize_production_trades_df",
    "_normalize_lab_trades",
    "_normalize_lab_candidates",
    "_canonical_exit_reason",
    "_to_utc_minute",
    "_parse_date",
]
