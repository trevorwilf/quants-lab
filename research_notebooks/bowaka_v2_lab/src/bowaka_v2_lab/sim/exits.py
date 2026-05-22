"""Exit lifecycle — per-lot minute-path stop / target / time-stop / max-hold /
signal-fade evaluation.

Realism Phase 7 (audit P0-009, §11 Phase 7, Ticket 9). The pre-Phase-7
evaluator looked at a SINGLE DAILY BAR per symbol and could only ever produce
``stop_loss`` / ``take_profit`` / ``time_stop``. A daily bar hides the intraday
*path*: a stop and a target both inside the day's range tells you nothing about
which one the OCO bracket would have hit first.

This module replaces that with :func:`walk_lot_exit` — a per-lot walk over the
**minute bars** from the bar AFTER the fill minute through to the earliest of:

* **stop** — a minute whose ``low <= stop_price``.
* **target** — a minute whose ``high >= target_price``.
* **gap stop / gap target** — a minute whose ``open`` is already through a
  bracket (a gap-through fills at the open, not the bracket price).
* **same-minute ambiguity** — a minute that touches BOTH brackets; resolved by
  ``simulation.same_minute_resolution`` (conservative → stop wins).
* **time stop** — ``exits.time_stop.exit_time`` (default 15:45 ET): exit at the
  next available bid (quote-aware in realism, minute-close in smoke).
* **max hold** — the close of session ``entry_session + (max_hold_days - 1)``
  XNYS trading days (holidays inside the window do not count).
* **signal fade** — at ``exits.signal_fade.eval_time`` (default 15:45 ET) the
  signal score is recomputed on the forming bar; below the configured
  ``exit_on`` threshold the lot is closed (``active`` modes) or only logged
  (``telemetry_only``).
* **halt / LULD stress** — when ``cost_stress == "severe"`` a modeled halt
  blocks bracket fills for 60s and force-exits at the next bid on resume.

The daily-bar evaluator :func:`evaluate_exits` is retained for the
``smoke_fixture`` simulation mode only (the smoke suite stays daily-fast); the
``current_code_parity`` / ``intended_realism`` modes use the minute path.

``trading_days_since`` uses ``exchange-calendars`` XNYS sessions, NOT
``pd.bdate_range`` (§15.2 P1 — bdate_range ignores US market holidays).
"""
from __future__ import annotations

import datetime as _dt
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import pandas as pd

try:
    import exchange_calendars as xcals
except ImportError:  # pragma: no cover
    xcals = None  # type: ignore

from .ambiguity import resolve_same_bar
from .portfolio import Position

#: ET clock time the time-stop / signal-fade evaluation defaults to.
_DEFAULT_EXIT_TIME = "15:45"
#: Live signal-fade score thresholds (frozen contract ``exits.signal_fade``).
_DEFAULT_FADE_THRESHOLDS = {"soft": 0.34, "hard": 0.50, "critical": 0.67}
#: Live signal-fade ``exit_on`` set.
_DEFAULT_FADE_EXIT_ON = ("hard", "critical")
#: Modeled halt duration applied under ``cost_stress == "severe"`` (LULD-style).
_HALT_SECONDS = 60


@dataclass
class ExitEvent:
    """One exit closing exactly one lot.

    ``exit_reason`` is one of the Phase-7 reasons:
    ``stop`` / ``target`` / ``time_stop`` / ``max_hold`` / ``signal_fade_hard``
    / ``signal_fade_critical`` / ``gap_stop`` / ``gap_target``. The legacy
    ``stop_loss`` / ``take_profit`` reasons are still produced by the daily-bar
    :func:`evaluate_exits` (smoke path) for back-compat.
    """

    symbol: str
    exit_date: _dt.date
    exit_price: float
    exit_reason: str
    ambiguous_bar_resolved: bool = False
    # Realism Phase 5 — the specific lot this exit closes. open_positions is
    # keyed by position_id, so a symbol may hold several lots; callers close
    # the exact lot via Portfolio.close_position_by_id(position_id, ...).
    position_id: Optional[str] = None
    # Realism Phase 7 — minute-path forensics. ``exit_timestamp`` is the
    # tz-aware UTC minute the exit fired; ``mfe_pct`` / ``mae_pct`` are the
    # peak favourable / adverse excursion over the held minute path (fraction
    # of entry price); ``exit_slippage_bps`` is the bracket-vs-fill slippage.
    exit_timestamp: Optional[str] = None
    mfe_pct: float = 0.0
    mae_pct: float = 0.0
    exit_slippage_bps: float = 0.0
    halted: bool = False


@dataclass
class FadeTelemetry:
    """A signal-fade ``would-have-exited`` event recorded under ``telemetry_only``
    (the lot is *not* closed)."""

    symbol: str
    position_id: str
    eval_date: _dt.date
    eval_timestamp: str
    score: float
    threshold_name: str
    threshold_value: float
    would_exit_reason: str


def trading_days_since(start: _dt.date, end: _dt.date, *, calendar: str = "XNYS") -> int:
    """Trading-day count using exchange-calendars XNYS sessions.

    Per [Report §15.2 P1]: replaces ``pd.bdate_range`` which ignored US market
    holidays (Christmas, July 4, MLK Day, etc.) and miscounted ``max_hold_days``.
    """
    if end <= start:
        return 0
    if xcals is None:
        # Conservative fallback: use bdate_range with a warning.
        return len(pd.bdate_range(start=start, end=end)) - (1 if start.weekday() < 5 else 0)
    cal = xcals.get_calendar(calendar)
    sessions = cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end))
    return max(0, len(sessions) - 1)  # exclude the entry day itself


def max_hold_exit_session(
    entry_session: _dt.date, max_hold_days: int, *, calendar: str = "XNYS"
) -> _dt.date:
    """The XNYS session a lot held since ``entry_session`` must exit on.

    Per Phase 7 Task 4: exit at the close of session ``N`` where
    ``N = entry_session + (max_hold_days - 1)`` *trading* days — holidays inside
    the window do not count. ``max_hold_days == 1`` therefore exits at the close
    of the entry session itself.
    """
    steps = max(0, int(max_hold_days) - 1)
    if steps == 0:
        return entry_session
    if xcals is None:  # pragma: no cover - calendar always present in the env
        # bdate_range fallback (Mon-Fri, no holidays).
        rng = pd.bdate_range(start=entry_session, periods=steps + 1)
        return rng[-1].date()
    cal = xcals.get_calendar(calendar)
    # Sessions on/after the entry session; the (steps)-th one is the exit day.
    sessions = cal.sessions_in_range(
        pd.Timestamp(entry_session), pd.Timestamp(entry_session) + pd.Timedelta(days=steps * 4 + 10)
    )
    # Drop sessions strictly before entry (sessions_in_range is inclusive).
    sessions = [s for s in sessions if s.date() >= entry_session]
    if len(sessions) > steps:
        return sessions[steps].date()
    return sessions[-1].date() if sessions else entry_session


# --------------------------------------------------------------------------
# Minute-path helpers
# --------------------------------------------------------------------------


def _bar_field(bar: Any, *names: str) -> Optional[float]:
    """Read the first present numeric field from a minute-bar row (dict / Series)."""
    for n in names:
        if isinstance(bar, dict):
            if n in bar and bar[n] is not None:
                try:
                    return float(bar[n])
                except (TypeError, ValueError):
                    continue
        else:  # pandas Series / namedtuple-ish
            v = getattr(bar, n, None)
            if v is None:
                try:
                    v = bar[n]  # type: ignore[index]
                except Exception:  # noqa: BLE001
                    v = None
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    continue
    return None


def _bar_ts(bar: Any) -> Optional[pd.Timestamp]:
    """Read the tz-aware UTC timestamp of a minute-bar row."""
    raw = None
    if isinstance(bar, dict):
        raw = bar.get("timestamp", bar.get("ts"))
    else:
        raw = getattr(bar, "timestamp", None)
        if raw is None:
            raw = getattr(bar, "ts", None)
        if raw is None:
            try:
                raw = bar["timestamp"]  # type: ignore[index]
            except Exception:  # noqa: BLE001
                raw = None
    if raw is None:
        return None
    ts = pd.Timestamp(raw)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def _et_clock(ts: pd.Timestamp) -> _dt.time:
    """ET wall-clock time of a tz-aware UTC timestamp."""
    return ts.tz_convert("America/New_York").time()


def _parse_hhmm(value: Any, default: str = _DEFAULT_EXIT_TIME) -> _dt.time:
    text = str(value) if value else default
    parts = text.strip().split(":")
    return _dt.time(
        hour=int(parts[0]),
        minute=int(parts[1]) if len(parts) > 1 else 0,
        second=int(parts[2]) if len(parts) > 2 else 0,
    )


def _resolve_same_minute(
    resolution: str, *, seed_key: str
) -> str:
    """Resolve a same-minute stop+target ambiguity → ``"stop"`` / ``"target"``.

    ``conservative`` (the realism default) → stop wins; ``optimistic`` → target
    wins; ``random_with_seed`` → a deterministic coin flip seeded on
    ``seed_key`` so two runs of the same config + seed always agree.
    """
    if resolution == "optimistic":
        return "target"
    if resolution == "random_with_seed":
        rng = random.Random(seed_key)
        return "stop" if rng.random() < 0.5 else "target"
    # conservative (and any unknown value) — stop wins.
    return "stop"


def _next_bid(
    bar: Any,
    symbol: str,
    *,
    quote_supplier: Optional[Callable[..., Optional[dict]]] = None,
) -> float:
    """Exit price for a time-stop / max-hold / fade / halt exit on ``bar``.

    Quote-aware in realism mode: when a ``quote_supplier`` is wired and returns
    a quote at the bar minute, the bid is used. Otherwise the minute close is
    used (the smoke path, and any minute with no historical quote).
    """
    close = _bar_field(bar, "close", "Close") or 0.0
    if quote_supplier is not None:
        ts = _bar_ts(bar)
        if ts is not None:
            try:
                q = quote_supplier(symbol, ts)
            except Exception:  # noqa: BLE001 - quote lookup is best-effort
                q = None
            if q:
                bid = q.get("bid")
                if bid:
                    try:
                        return float(bid)
                    except (TypeError, ValueError):
                        pass
    return float(close)


@dataclass
class _LotPathState:
    """Mutable running state for one lot's minute-path walk."""

    peak: float = 0.0   # highest high seen
    trough: float = 1e30  # lowest low seen
    halt_until: Optional[pd.Timestamp] = None
    halt_seen: bool = False


def walk_lot_exit(
    pos: Position,
    minute_bars: Optional[pd.DataFrame],
    *,
    exit_cfg: Optional[dict] = None,
    same_minute_resolution: str = "conservative",
    cost_stress: str = "base",
    quote_supplier: Optional[Callable[..., Optional[dict]]] = None,
    signal_score_fn: Optional[Callable[[Position, pd.Timestamp], Optional[float]]] = None,
    seed: int = 0,
    fade_telemetry_out: Optional[list] = None,
) -> Optional[ExitEvent]:
    """Walk one lot's minute path and return the earliest exit, or ``None``.

    Parameters
    ----------
    pos:
        The open lot (carries ``stop_price`` / ``target_price`` priced off the
        actual fill, ``entry_timestamp``, ``entry_session``, ``max_hold_days``).
    minute_bars:
        Minute bars covering at least ``[fill_minute, exit_horizon]`` for the
        lot's symbol — tz-aware ``timestamp`` plus OHLC columns. Bars at or
        before the fill minute are skipped (a lot never exits on its fill bar).
    exit_cfg:
        The ``exits`` config block (``time_stop`` / ``signal_fade`` substructs).
    same_minute_resolution:
        ``simulation.same_minute_resolution`` — resolves a minute touching both
        brackets.
    cost_stress:
        ``"severe"`` models a 60s LULD-style halt in the minute path.
    quote_supplier:
        Optional historical-quote supplier; makes time-stop / max-hold / fade /
        halt exits quote-aware (exit at the bid).
    signal_score_fn:
        ``fn(pos, bar_ts) -> Optional[float]`` recomputing the signal score on
        the forming bar at ``bar_ts`` — drives the signal-fade exit.
    fade_telemetry_out:
        When supplied, ``telemetry_only`` would-have-exited events are appended
        here as :class:`FadeTelemetry` (the lot is NOT closed in that mode).
    """
    if minute_bars is None or len(minute_bars) == 0:
        return None
    cfg = exit_cfg or {}

    stop_price = pos.stop_price
    target_price = pos.target_price
    if stop_price is None:
        stop_price = pos.entry_price * (1.0 - pos.stop_pct)
    if target_price is None:
        target_price = pos.entry_price * (1.0 + pos.target_pct)

    fill_minute = pos.entry_minute_utc()
    entry_session = pos.entry_session or pos.entry_date
    exit_session = max_hold_exit_session(entry_session, pos.max_hold_days)

    time_stop_cfg = cfg.get("time_stop") or {}
    time_stop_enabled = bool(time_stop_cfg.get("enabled", True)) if time_stop_cfg else False
    time_stop_clock = _parse_hhmm(time_stop_cfg.get("exit_time"), _DEFAULT_EXIT_TIME)

    fade_cfg = cfg.get("signal_fade") or {}
    fade_enabled = bool(fade_cfg.get("enabled", False)) and signal_score_fn is not None
    fade_mode = str(
        fade_cfg.get("initial_mode", cfg.get("signal_fade_mode", "telemetry_only"))
    )
    fade_active = fade_mode in ("active", "telemetry_then_active_after_validation")
    fade_clock = _parse_hhmm(fade_cfg.get("eval_time"), _DEFAULT_EXIT_TIME)
    fade_thresholds = dict(fade_cfg.get("score_thresholds") or _DEFAULT_FADE_THRESHOLDS)
    fade_exit_on = tuple(fade_cfg.get("exit_on") or _DEFAULT_FADE_EXIT_ON)

    is_severe = str(cost_stress) == "severe"
    state = _LotPathState()
    entry_price = pos.entry_price or 0.0
    seed_base = f"{seed}|{pos.position_id}"
    fade_fired_dates: set[_dt.date] = set()

    # Sort bars by timestamp so the walk is path-ordered.
    df = minute_bars
    ts_col = None
    for c in ("timestamp", "ts"):
        if c in df.columns:
            ts_col = c
            break
    if ts_col is not None:
        df = df.sort_values(ts_col)

    for _, bar in df.iterrows():
        ts = _bar_ts(bar)
        if ts is None or ts <= fill_minute:
            continue  # never exit on (or before) the fill minute
        bar_date = ts.tz_convert("America/New_York").date()
        if bar_date > exit_session:
            break  # past the max-hold horizon — handled below as a fallback

        o = _bar_field(bar, "open", "Open")
        h = _bar_field(bar, "high", "High")
        l = _bar_field(bar, "low", "Low")
        c = _bar_field(bar, "close", "Close")
        if h is None or l is None:
            continue
        # Running MFE / MAE excursion.
        state.peak = max(state.peak, h)
        state.trough = min(state.trough, l)
        clock = _et_clock(ts)

        # ---- Halt / LULD stress (Task 7) ---------------------------------
        # A modeled halt: when severe stress and a minute trips a bracket, the
        # bracket cannot fill for _HALT_SECONDS; the first bar after the halt
        # window force-exits at the next bid.
        in_halt = state.halt_until is not None and ts < state.halt_until
        if state.halt_until is not None and ts >= state.halt_until:
            # Halt just resumed — force-exit at the next available bid.
            px = _next_bid(bar, pos.symbol, quote_supplier=quote_supplier)
            return _mk_exit(
                pos, bar_date, px, "halt_resume_exit", ts,
                state, entry_price, halted=True,
            )

        # ---- gap-through (Task 2) ----------------------------------------
        # The minute OPEN is already through a bracket → fill at the open.
        if o is not None and not in_halt:
            if o <= stop_price:
                if is_severe and not state.halt_seen:
                    state.halt_seen = True
                    state.halt_until = ts + pd.Timedelta(seconds=_HALT_SECONDS)
                    continue
                return _mk_exit(
                    pos, bar_date, o, "gap_stop", ts, state, entry_price,
                )
            if o >= target_price:
                if is_severe and not state.halt_seen:
                    state.halt_seen = True
                    state.halt_until = ts + pd.Timedelta(seconds=_HALT_SECONDS)
                    continue
                return _mk_exit(
                    pos, bar_date, o, "gap_target", ts, state, entry_price,
                )

        # ---- stop / target / same-minute (Tasks 1, 7) --------------------
        stop_hit = l <= stop_price
        target_hit = h >= target_price
        if (stop_hit or target_hit) and not in_halt:
            if is_severe and not state.halt_seen:
                # First bracket trip under severe stress triggers a halt.
                state.halt_seen = True
                state.halt_until = ts + pd.Timedelta(seconds=_HALT_SECONDS)
                continue
            if stop_hit and target_hit:
                winner = _resolve_same_minute(
                    same_minute_resolution, seed_key=f"{seed_base}|{ts.isoformat()}"
                )
                if winner == "stop":
                    return _mk_exit(
                        pos, bar_date, float(stop_price), "stop", ts,
                        state, entry_price, ambiguous=True,
                    )
                return _mk_exit(
                    pos, bar_date, float(target_price), "target", ts,
                    state, entry_price, ambiguous=True,
                )
            if stop_hit:
                return _mk_exit(
                    pos, bar_date, float(stop_price), "stop", ts,
                    state, entry_price,
                )
            return _mk_exit(
                pos, bar_date, float(target_price), "target", ts,
                state, entry_price,
            )

        # ---- signal fade (Task 5) ----------------------------------------
        # At eval_time recompute the score on the forming bar. Evaluate once
        # per session date (the first bar at/after the eval clock).
        if (
            fade_enabled
            and bar_date not in fade_fired_dates
            and clock >= fade_clock
        ):
            fade_fired_dates.add(bar_date)
            score = None
            try:
                score = signal_score_fn(pos, ts)  # type: ignore[misc]
            except Exception:  # noqa: BLE001 - re-scoring is best-effort
                score = None
            if score is not None:
                tripped_name, tripped_val, tripped_reason = _fade_trip(
                    float(score), fade_thresholds, fade_exit_on
                )
                if tripped_name is not None:
                    if fade_active:
                        px = _next_bid(bar, pos.symbol, quote_supplier=quote_supplier)
                        return _mk_exit(
                            pos, bar_date, px, tripped_reason, ts,
                            state, entry_price,
                        )
                    # telemetry_only — record the would-have-exited event but
                    # do NOT close the lot.
                    if fade_telemetry_out is not None:
                        fade_telemetry_out.append(FadeTelemetry(
                            symbol=pos.symbol,
                            position_id=pos.position_id,
                            eval_date=bar_date,
                            eval_timestamp=ts.isoformat(),
                            score=float(score),
                            threshold_name=tripped_name,
                            threshold_value=tripped_val,
                            would_exit_reason=tripped_reason,
                        ))

        # ---- time stop (Task 3) ------------------------------------------
        if time_stop_enabled and clock >= time_stop_clock:
            px = _next_bid(bar, pos.symbol, quote_supplier=quote_supplier)
            return _mk_exit(
                pos, bar_date, px, "time_stop", ts, state, entry_price,
            )

        # ---- max hold (Task 4) -------------------------------------------
        # On the exit session, the last regular-session bar closes the lot.
        if bar_date >= exit_session and clock >= _dt.time(15, 59):
            px = c if c is not None else _next_bid(
                bar, pos.symbol, quote_supplier=quote_supplier
            )
            return _mk_exit(
                pos, bar_date, float(px), "max_hold", ts, state, entry_price,
            )

    # Walked the whole supplied path with no exit. Fall back to a max-hold exit
    # on the last bar that is on/before the exit session (the supplier may stop
    # short of 15:59 in a short fixture; the lot must still close by the
    # trading-day horizon).
    last_in_window = None
    for _, bar in df.iterrows():
        ts = _bar_ts(bar)
        if ts is None or ts <= fill_minute:
            continue
        bd = ts.tz_convert("America/New_York").date()
        if bd <= exit_session:
            last_in_window = (ts, bar, bd)
    if last_in_window is not None:
        ts, bar, bd = last_in_window
        c = _bar_field(bar, "close", "Close")
        px = c if c is not None else entry_price
        return _mk_exit(
            pos, bd, float(px), "max_hold", ts, state, entry_price,
        )
    return None


def _fade_trip(
    score: float, thresholds: dict, exit_on: tuple
) -> tuple[Optional[str], float, str]:
    """If the re-scored signal trips an ``exit_on`` fade threshold, return the
    threshold name / value / exit-reason — else ``(None, 0.0, "")``.

    Per Phase 7 Task 5 the rule is ``score < threshold`` → exit. The live
    thresholds are ``{soft: 0.34, hard: 0.50, critical: 0.67}`` with
    ``exit_on: ["hard", "critical"]``. A signal can be below several thresholds
    at once; the band reported is the **tightest** (smallest-value) ``exit_on``
    threshold the score is still below — so a score below ``hard`` is a
    ``signal_fade_hard``, and a score that clears ``hard`` but is still below
    ``critical`` is a ``signal_fade_critical``.
    """
    # Candidate (name, value) pairs for the exit_on thresholds, ascending.
    candidates = sorted(
        ((n, float(thresholds[n])) for n in exit_on if n in thresholds),
        key=lambda kv: kv[1],
    )
    for name, value in candidates:
        if score < value:
            return name, value, f"signal_fade_{name}"
    return None, 0.0, ""


def _mk_exit(
    pos: Position,
    bar_date: _dt.date,
    exit_price: float,
    reason: str,
    ts: pd.Timestamp,
    state: _LotPathState,
    entry_price: float,
    *,
    ambiguous: bool = False,
    halted: bool = False,
) -> ExitEvent:
    """Build an :class:`ExitEvent`, filling MFE/MAE + exit-slippage forensics."""
    mfe = (state.peak - entry_price) / entry_price if entry_price > 0 and state.peak > 0 else 0.0
    mae = (
        (state.trough - entry_price) / entry_price
        if entry_price > 0 and state.trough < 1e30
        else 0.0
    )
    # Exit slippage: a bracket exit fills exactly at the bracket price (0 bps);
    # a time-stop / max-hold / fade / gap exit fills away from the bracket — the
    # signed deviation from the nearer bracket reference, in bps.
    slip_bps = 0.0
    if reason in ("time_stop", "max_hold", "signal_fade_hard", "signal_fade_critical",
                  "halt_resume_exit"):
        # measured vs the entry price (a discretionary exit has no bracket).
        if entry_price > 0:
            slip_bps = (exit_price - entry_price) / entry_price * 10_000.0
    elif reason in ("gap_stop", "gap_target"):
        ref = pos.stop_price if reason == "gap_stop" else pos.target_price
        if ref:
            slip_bps = (exit_price - float(ref)) / float(ref) * 10_000.0
    return ExitEvent(
        symbol=pos.symbol,
        exit_date=bar_date,
        exit_price=float(exit_price),
        exit_reason=reason,
        ambiguous_bar_resolved=ambiguous,
        position_id=pos.position_id,
        exit_timestamp=ts.isoformat(),
        mfe_pct=float(mfe),
        mae_pct=float(mae),
        exit_slippage_bps=float(slip_bps),
        halted=halted,
    )


# --------------------------------------------------------------------------
# Legacy daily-bar evaluator — smoke_fixture path only
# --------------------------------------------------------------------------


def evaluate_exits(
    pos: Position,
    *,
    bar: dict,
    bar_date: _dt.date,
    exit_cfg: dict,
    same_bar_policy: str = "stop_first",
) -> Optional[ExitEvent]:
    """Evaluate a single DAILY bar for stop / target / time-stop hits.

    Realism Phase 7: this daily-bar evaluator is retained for the
    ``smoke_fixture`` simulation mode ONLY — it keeps the smoke suite fast by
    avoiding the minute-path walk. The ``current_code_parity`` /
    ``intended_realism`` modes drive exits through :func:`walk_lot_exit`.
    """
    high = float(bar.get("high", bar.get("session_high", 0.0)) or 0.0)
    low = float(bar.get("low", bar.get("session_low", 0.0)) or 0.0)
    close = float(bar.get("close", bar.get("last_price", 0.0)) or 0.0)
    if high == 0 or low == 0:
        return None

    stop_price = pos.entry_price * (1.0 - pos.stop_pct)
    target_price = pos.entry_price * (1.0 + pos.target_pct)

    stop_hit = low <= stop_price
    target_hit = high >= target_price
    ambiguous = stop_hit and target_hit
    pid = pos.position_id
    if ambiguous:
        winner = resolve_same_bar(same_bar_policy)
        if winner == "stop":
            return ExitEvent(pos.symbol, bar_date, stop_price, "stop_loss",
                             ambiguous_bar_resolved=True, position_id=pid)
        else:
            return ExitEvent(pos.symbol, bar_date, target_price, "take_profit",
                             ambiguous_bar_resolved=True, position_id=pid)
    if stop_hit:
        return ExitEvent(pos.symbol, bar_date, stop_price, "stop_loss", position_id=pid)
    if target_hit:
        return ExitEvent(pos.symbol, bar_date, target_price, "take_profit", position_id=pid)

    # Time stop.
    days_held = trading_days_since(pos.entry_date, bar_date)
    if days_held >= pos.max_hold_days:
        return ExitEvent(pos.symbol, bar_date, close, "time_stop", position_id=pid)

    return None
