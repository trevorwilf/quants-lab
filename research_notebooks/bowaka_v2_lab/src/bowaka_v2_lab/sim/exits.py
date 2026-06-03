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

Realism Remediation 2 Phase 7 (audit P0-008). The legacy code treated
``initial_mode: telemetry_then_active_after_validation`` as immediately active.
That is wrong: the phrase implies the mode STARTS in telemetry and only flips
to active after a validation activation step. Phase 7 introduces the
``activation_state`` field (``telemetry`` | ``active``) which can be set:

* explicitly in config (``exits.signal_fade.activation_state: active``), or
* by dropping a validation activation artifact at
  ``artifacts/promotion/signal_fade_activation_<feed>.json`` containing
  ``{timestamp, dataset_hash, code_hash, operator_signature, ...}``.

Until ONE of those two activations is present, ``telemetry_then_active_after_validation``
behaves as telemetry-only — would-have-exited events are recorded, the lot is
not closed via CHILD_FILL.
"""
from __future__ import annotations

import datetime as _dt
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

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


def _activation_artifact_dir(artifact_root: Optional[Any]) -> Path:
    """The directory the signal-fade activation artifact lives in.

    Default is ``<cwd>/artifacts/promotion``; callers can override by passing
    ``exits.signal_fade.activation_artifact_dir`` (typically wired from
    ``BowakaV2Paths.artifact_root / "promotion"``).
    """
    if artifact_root is None:
        return Path.cwd() / "artifacts" / "promotion"
    return Path(artifact_root)


def _activation_artifact_present(
    feed: str, *, artifact_dir: Path
) -> bool:
    """``True`` iff a validation activation artifact for ``feed`` is on disk.

    Per Phase 7 (audit P0-008) the artifact at
    ``<dir>/signal_fade_activation_<feed>.json`` is the documented activation
    handshake: until it lands, ``telemetry_then_active_after_validation`` MUST
    stay in telemetry mode. The artifact body is required to be a JSON object
    (a bare list / scalar is rejected); the operator-signature / dataset-hash /
    code-hash / timestamp keys are *recorded* for the audit trail but only the
    file's *presence and parseability* drives activation here — the gating on
    field content is a downstream operator-policy concern.
    """
    feed_key = str(feed or "").strip().lower() or "default"
    path = artifact_dir / f"signal_fade_activation_{feed_key}.json"
    if not path.exists():
        return False
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(body, dict)


def resolve_signal_fade_active(
    fade_cfg: Mapping[str, Any] | dict | None,
    *,
    feed: Optional[str] = None,
    artifact_dir: Optional[Path] = None,
) -> tuple[bool, str, str]:
    """Resolve the live ``(fade_active, fade_mode, activation_state)`` triple.

    Phase 7 audit P0-008 — this is the single source of truth for the rule:

    * ``fade_mode == "active"`` → always active.
    * ``fade_mode == "telemetry_then_active_after_validation"`` → active ONLY
      when ``activation_state == "active"`` OR a validation activation artifact
      is present on disk.
    * any other mode (``telemetry_only`` / unknown) → telemetry; never active.
    """
    cfg = dict(fade_cfg or {})
    fade_mode = str(cfg.get("initial_mode", cfg.get("signal_fade_mode", "telemetry_only")))
    raw_state = str(cfg.get("activation_state") or "").strip().lower()
    # Default activation state for the after-validation mode is telemetry.
    if not raw_state:
        activation_state = (
            "telemetry"
            if fade_mode == "telemetry_then_active_after_validation"
            else ""  # not applicable
        )
    else:
        activation_state = raw_state

    if fade_mode == "active":
        return True, fade_mode, activation_state

    if fade_mode == "telemetry_then_active_after_validation":
        if activation_state == "active":
            return True, fade_mode, activation_state
        # Check for a validation activation artifact.
        artifact_root = cfg.get("activation_artifact_dir")
        adir = artifact_dir if artifact_dir is not None else _activation_artifact_dir(artifact_root)
        if _activation_artifact_present(feed or "default", artifact_dir=adir):
            return True, fade_mode, "active"
        return False, fade_mode, activation_state or "telemetry"

    # telemetry_only and any unknown mode → telemetry, never active.
    return False, fade_mode, activation_state or "telemetry"


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


def _walk_lot_exit_pandas(
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
    until_ts: Optional[pd.Timestamp] = None,
    feed: Optional[str] = None,
    activation_artifact_dir: Optional[Path] = None,
    status_supplier: Optional[Callable[..., Optional[dict]]] = None,
) -> Optional[ExitEvent]:
    """Reference (pandas/``iterrows``) per-lot minute-path walk — frozen oracle.

    This is the original, semantically-authoritative implementation. It is kept
    in production as (a) the parity oracle the numpy fast path
    (:func:`_walk_lot_exit_numpy`) is differentially tested against and (b) the
    fallback :func:`walk_lot_exit` dispatches to for any minute frame the fast
    path is not eligible for (non-numeric / missing OHLC columns), so the
    ``_bar_field`` None-vs-NaN semantics are never approximated. Do NOT change
    this function's behaviour — it defines correctness.

    Walk one lot's minute path and return the earliest exit, or ``None``.

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
    until_ts:
        Realism remediation 2 Phase 4: when supplied, walk the path only up to
        and including this UTC timestamp; if no exit fires within the window,
        return ``None`` (NO max-hold fallback). The event-driven dispatcher uses
        this to evaluate intraday exits in chronological windows so a same-day
        stop is realized before the next SCAN runs.
    feed:
        Realism remediation 2 Phase 7 — the data feed (``iex`` / ``sip`` / etc.)
        looked up for the per-feed signal-fade activation artifact at
        ``<activation_artifact_dir>/signal_fade_activation_<feed>.json``.
    activation_artifact_dir:
        Realism remediation 2 Phase 7 — directory the signal-fade activation
        artifact lives in (default ``<cwd>/artifacts/promotion``). Typically
        wired by callers from ``BowakaV2Paths.artifact_root / "promotion"``.
    status_supplier:
        Realism remediation 2 Phase 7 (Task 3 robustness): venue-status supplier
        ``fn(symbol, ts) -> dict | None``. When the supplier reports
        ``status in {halted, pending_review, luld_pause}`` for the bar minute,
        bracket / time-stop / fade exits are DEFERRED to the first non-halted
        minute. If the lot reaches max-hold or the bars run out while still
        halted, a fallback ``halt_max_hold`` / ``halt_resume_exit`` is emitted.
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
    # Realism remediation 2 Phase 7 (audit P0-008): resolve fade_active via the
    # documented activation handshake — NOT a naive ``mode in {active, telemetry_then_active_after_validation}``
    # check. ``telemetry_then_active_after_validation`` stays in telemetry mode
    # until either explicit ``activation_state: active`` config OR a validation
    # activation artifact at ``<activation_artifact_dir>/signal_fade_activation_<feed>.json``.
    fade_active, fade_mode, fade_activation_state = resolve_signal_fade_active(
        fade_cfg, feed=feed, artifact_dir=activation_artifact_dir,
    )
    fade_clock = _parse_hhmm(fade_cfg.get("eval_time"), _DEFAULT_EXIT_TIME)
    fade_thresholds = dict(fade_cfg.get("score_thresholds") or _DEFAULT_FADE_THRESHOLDS)
    fade_exit_on = tuple(fade_cfg.get("exit_on") or _DEFAULT_FADE_EXIT_ON)

    # Realism remediation 2 Phase 7 (Task 3 robustness): per-exit-config
    # ``exits.same_minute_tie`` (``stop_first`` default → stop wins; ``target_first``
    # → target wins). Mapped to the existing ``simulation.same_minute_resolution``
    # values so the engine has a single code path. ``exits.same_minute_tie``
    # OVERRIDES ``same_minute_resolution`` when both are set, because the
    # exit-config-level setting is the more specific lever.
    same_minute_tie = cfg.get("same_minute_tie")
    if same_minute_tie:
        tie = str(same_minute_tie).strip().lower()
        if tie == "stop_first":
            same_minute_resolution = "conservative"
        elif tie == "target_first":
            same_minute_resolution = "optimistic"
        elif tie in ("conservative", "optimistic", "random_with_seed"):
            same_minute_resolution = tie

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

    # Realism remediation 2 Phase 4: when the caller supplies ``until_ts`` the
    # walk is bounded — bars whose ``ts > until_ts`` are skipped entirely so the
    # lot can be re-evaluated in the next time window.
    until_ts_utc: Optional[pd.Timestamp] = None
    if until_ts is not None:
        until_ts_utc = pd.Timestamp(until_ts)
        if until_ts_utc.tzinfo is None:
            until_ts_utc = until_ts_utc.tz_localize("UTC")
        else:
            until_ts_utc = until_ts_utc.tz_convert("UTC")

    for _, bar in df.iterrows():
        ts = _bar_ts(bar)
        if ts is None or ts <= fill_minute:
            continue  # never exit on (or before) the fill minute
        if until_ts_utc is not None and ts > until_ts_utc:
            break  # past the caller's window — leave the lot open
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

        # Realism remediation 2 Phase 7 Task 3: a venue-status halt at this
        # minute defers ALL exit evaluation. The bar is skipped (a bracket
        # cannot fill while halted) so the next non-halted minute drives the
        # exit. ``halted`` / ``pending_review`` / ``luld_pause`` all defer.
        if status_supplier is not None:
            try:
                status = status_supplier(pos.symbol, ts)
            except Exception:  # noqa: BLE001 — supplier failure is "no data"
                status = None
            if isinstance(status, dict):
                status_val = str(status.get("status") or "").strip().lower()
                if status_val in ("halted", "pending_review", "luld_pause"):
                    state.halt_seen = True
                    # mark this minute as halted for forensics + skip the bar
                    continue

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
    # trading-day horizon). Skipped when the caller bounded the walk with
    # ``until_ts`` — there a lot that survived the window stays open for the
    # next dispatch tick.
    if until_ts_utc is not None:
        return None
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


#: Per-trial speedup — use the numpy fast path in :func:`walk_lot_exit` for
#: eligible (numeric-OHLC + timestamp) minute frames. Flip to ``False`` for an
#: instant revert to the pandas reference everywhere; the differential parity
#: test (``tests/parity/test_walk_lot_exit_numpy_parity.py``) pins the two
#: implementations byte-identical so this is purely a kill switch.
_FAST_EXIT_WALK = True

#: The numpy path's fixed setup (DatetimeIndex + 4× ``to_numpy`` + ET date/time
#: arrays) only pays off once the slice is more than a couple of bars — measured
#: break-even is ~3 bars (1 bar is ~0.85× i.e. a slight regression, 3 bars
#: ~1.3×, a full session ~25-36×). The minute event loop walks each lot's NEW
#: bars per poll tick, which is usually a 1-bar slice, so this guard keeps those
#: tiny calls on the pandas path (no regression) and routes only the larger
#: catch-up / full-session walks through numpy. Purely a performance threshold —
#: the two paths are byte-identical at every size (differential parity test).
_FAST_EXIT_WALK_MIN_BARS = 3


def _exit_walk_fast_eligible(minute_bars: Optional[pd.DataFrame]) -> bool:
    """``True`` iff the numpy fast path can reproduce the pandas reference exactly.

    Eligible frames carry a ``timestamp`` (or ``ts``) column and numeric
    ``open/high/low/close`` columns — the universal shape of a real lake minute
    frame and of every test fixture. Object-dtype or missing OHLC columns fall
    back to :func:`_walk_lot_exit_pandas`, whose ``_bar_field`` distinguishes a
    Python ``None`` (absent / un-floatable cell) from a present ``NaN`` — a
    distinction a ``float64`` array cannot preserve. Numeric columns never carry
    ``None`` (only ``NaN``), so the fast path is bit-exact there.
    """
    if minute_bars is None or len(minute_bars) == 0:
        return False
    cols = minute_bars.columns
    if "timestamp" not in cols and "ts" not in cols:
        return False
    for lower, upper in (("open", "Open"), ("high", "High"),
                         ("low", "Low"), ("close", "Close")):
        name = lower if lower in cols else (upper if upper in cols else None)
        if name is None:
            return False
        if not pd.api.types.is_numeric_dtype(minute_bars[name]):
            return False
    return True


def _walk_lot_exit_numpy(
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
    until_ts: Optional[pd.Timestamp] = None,
    feed: Optional[str] = None,
    activation_artifact_dir: Optional[Path] = None,
    status_supplier: Optional[Callable[..., Optional[dict]]] = None,
) -> Optional[ExitEvent]:
    """Numpy fast path for :func:`_walk_lot_exit_pandas` — byte-identical output.

    The reference walks ``df.iterrows()`` and reads each minute via ``_bar_ts`` /
    ``_bar_field`` (a fresh ``Series`` + per-cell ``__getitem__`` + per-bar
    ``ts.tz_convert`` every bar — the profiled per-trial hot spot). This path
    pre-extracts the sorted path ONCE into numpy arrays — ``ts_ns`` (int64
    ns-since-epoch, UTC), vectorized ET ``date`` / ``time`` object arrays, and
    ``float64`` OHLC — then iterates by integer index with int/float compares,
    materialising a ``pd.Timestamp`` only on the rare bar that actually exits /
    halts / re-scores. The per-bar arithmetic is the SAME IEEE-754 double work,
    so every ``ExitEvent`` field (price, reason, date, timestamp, MFE/MAE,
    slippage, ambiguity) and every ``FadeTelemetry`` row match the reference
    exactly. See ``tests/parity/test_walk_lot_exit_numpy_parity.py``.

    NOTE the ``state.peak``/``state.trough`` updates use ``if h > peak`` /
    ``if l < trough`` rather than ``max``/``min``: this is identical to the
    reference (``max(peak, h)`` returns ``h`` iff ``h > peak``) AND inherits
    Python's ``max`` NaN semantics for free (``NaN > peak`` is ``False`` → no
    update), so a present-NaN bar leaves the excursions unchanged exactly as
    ``max(peak, NaN)`` would.
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
    fade_active, fade_mode, fade_activation_state = resolve_signal_fade_active(
        fade_cfg, feed=feed, artifact_dir=activation_artifact_dir,
    )
    fade_clock = _parse_hhmm(fade_cfg.get("eval_time"), _DEFAULT_EXIT_TIME)
    fade_thresholds = dict(fade_cfg.get("score_thresholds") or _DEFAULT_FADE_THRESHOLDS)
    fade_exit_on = tuple(fade_cfg.get("exit_on") or _DEFAULT_FADE_EXIT_ON)

    same_minute_tie = cfg.get("same_minute_tie")
    if same_minute_tie:
        tie = str(same_minute_tie).strip().lower()
        if tie == "stop_first":
            same_minute_resolution = "conservative"
        elif tie == "target_first":
            same_minute_resolution = "optimistic"
        elif tie in ("conservative", "optimistic", "random_with_seed"):
            same_minute_resolution = tie

    is_severe = str(cost_stress) == "severe"
    state = _LotPathState()
    entry_price = pos.entry_price or 0.0
    seed_base = f"{seed}|{pos.position_id}"
    fade_fired_dates: set[_dt.date] = set()

    # ---- pre-extract the sorted path as numpy arrays (the optimization) ----
    df = minute_bars
    ts_col = "timestamp" if "timestamp" in df.columns else "ts"
    df = df.sort_values(ts_col)  # same sort as the reference (deterministic order)
    idx = pd.DatetimeIndex(df[ts_col])
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    # ns-since-epoch, forcing ns regardless of the source resolution (the µs
    # astype gotcha — see session_minute_window_cache). Matches Timestamp.value.
    ts_ns = idx.tz_localize(None).to_numpy(dtype="datetime64[ns]").view("int64")
    et_idx = idx.tz_convert("America/New_York")
    et_dates = et_idx.date  # object array of datetime.date (== ts.tz_convert(ET).date())
    et_times = et_idx.time  # object array of datetime.time (== _et_clock(ts))

    def _col(*names: str):
        for n in names:
            if n in df.columns:
                return df[n].to_numpy(dtype="float64")
        return None

    o_arr = _col("open", "Open")
    h_arr = _col("high", "High")
    l_arr = _col("low", "Low")
    c_arr = _col("close", "Close")

    fill_minute_ns = int(fill_minute.value)
    until_ns: Optional[int] = None
    if until_ts is not None:
        until_ts_utc = pd.Timestamp(until_ts)
        until_ts_utc = (until_ts_utc.tz_localize("UTC") if until_ts_utc.tzinfo is None
                        else until_ts_utc.tz_convert("UTC"))
        until_ns = int(until_ts_utc.value)

    halt_until_ns: Optional[int] = None  # severe-stress halt window end (ns)
    n = len(df)

    for i in range(n):
        ts_i_ns = int(ts_ns[i])
        if ts_i_ns <= fill_minute_ns:
            continue  # never exit on (or before) the fill minute
        if until_ns is not None and ts_i_ns > until_ns:
            break  # past the caller's window — leave the lot open
        bar_date = et_dates[i]
        if bar_date > exit_session:
            break  # past the max-hold horizon — handled below as a fallback

        o = o_arr[i]
        h = h_arr[i]
        l = l_arr[i]
        c = c_arr[i]
        # Eligible frames carry numeric o/h/l/c, so _bar_field's is-None guard
        # never fires; a present-NaN cell is processed (not skipped) exactly as
        # the reference does. Running MFE / MAE excursion (NaN-safe via >/<):
        if h > state.peak:
            state.peak = h
        if l < state.trough:
            state.trough = l
        clock = et_times[i]

        # ---- Halt / LULD stress (Task 7) ---------------------------------
        in_halt = halt_until_ns is not None and ts_i_ns < halt_until_ns
        if halt_until_ns is not None and ts_i_ns >= halt_until_ns:
            ts = idx[i]
            px = _next_bid({"close": c, "timestamp": ts}, pos.symbol,
                           quote_supplier=quote_supplier)
            return _mk_exit(
                pos, bar_date, px, "halt_resume_exit", ts,
                state, entry_price, halted=True,
            )

        # Realism remediation 2 Phase 7 Task 3: venue-status halt defers exits.
        if status_supplier is not None:
            ts = idx[i]
            try:
                status = status_supplier(pos.symbol, ts)
            except Exception:  # noqa: BLE001 — supplier failure is "no data"
                status = None
            if isinstance(status, dict):
                status_val = str(status.get("status") or "").strip().lower()
                if status_val in ("halted", "pending_review", "luld_pause"):
                    state.halt_seen = True
                    continue

        # ---- gap-through (Task 2) ----------------------------------------
        if not in_halt:
            if o <= stop_price:
                if is_severe and not state.halt_seen:
                    state.halt_seen = True
                    halt_until_ns = ts_i_ns + _HALT_SECONDS * 1_000_000_000
                    continue
                return _mk_exit(
                    pos, bar_date, o, "gap_stop", idx[i], state, entry_price,
                )
            if o >= target_price:
                if is_severe and not state.halt_seen:
                    state.halt_seen = True
                    halt_until_ns = ts_i_ns + _HALT_SECONDS * 1_000_000_000
                    continue
                return _mk_exit(
                    pos, bar_date, o, "gap_target", idx[i], state, entry_price,
                )

        # ---- stop / target / same-minute (Tasks 1, 7) --------------------
        stop_hit = l <= stop_price
        target_hit = h >= target_price
        if (stop_hit or target_hit) and not in_halt:
            if is_severe and not state.halt_seen:
                state.halt_seen = True
                halt_until_ns = ts_i_ns + _HALT_SECONDS * 1_000_000_000
                continue
            ts = idx[i]
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
        if (
            fade_enabled
            and bar_date not in fade_fired_dates
            and clock >= fade_clock
        ):
            fade_fired_dates.add(bar_date)
            ts = idx[i]
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
                        px = _next_bid({"close": c, "timestamp": ts}, pos.symbol,
                                       quote_supplier=quote_supplier)
                        return _mk_exit(
                            pos, bar_date, px, tripped_reason, ts,
                            state, entry_price,
                        )
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
            ts = idx[i]
            px = _next_bid({"close": c, "timestamp": ts}, pos.symbol,
                           quote_supplier=quote_supplier)
            return _mk_exit(
                pos, bar_date, px, "time_stop", ts, state, entry_price,
            )

        # ---- max hold (Task 4) -------------------------------------------
        if bar_date >= exit_session and clock >= _dt.time(15, 59):
            # Reference: ``c if c is not None else _next_bid(...)``. For an
            # eligible (numeric-close) frame ``c`` is never None — it is the
            # float close (possibly NaN) — so the reference always takes ``c``.
            px = c
            return _mk_exit(
                pos, bar_date, float(px), "max_hold", idx[i], state, entry_price,
            )

    # Walked the whole path with no exit — max-hold fallback on the last bar
    # on/before the exit session (skipped when the caller bounded with until_ts).
    if until_ns is not None:
        return None
    last_i = -1
    for i in range(n):
        if int(ts_ns[i]) <= fill_minute_ns:
            continue
        if et_dates[i] <= exit_session:
            last_i = i
    if last_i >= 0:
        # Reference: ``c if c is not None else entry_price``. ``c`` is the
        # eligible-frame float close (never None) → always used (matches ref).
        px = c_arr[last_i]
        return _mk_exit(
            pos, et_dates[last_i], float(px), "max_hold", idx[last_i],
            state, entry_price,
        )
    return None


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
    until_ts: Optional[pd.Timestamp] = None,
    feed: Optional[str] = None,
    activation_artifact_dir: Optional[Path] = None,
    status_supplier: Optional[Callable[..., Optional[dict]]] = None,
) -> Optional[ExitEvent]:
    """Walk one lot's minute path and return the earliest exit, or ``None``.

    Dispatches to the numpy fast path (:func:`_walk_lot_exit_numpy`) for the
    common case of a numeric-OHLC minute frame, falling back to the pandas
    reference (:func:`_walk_lot_exit_pandas`) for non-numeric / missing-column
    frames or when ``_FAST_EXIT_WALK`` is off. The two are byte-identical on
    eligible frames (differential parity test), so this is transparent — the
    fast path only removes per-bar ``Series`` construction + ``tz_convert``,
    not any numeric work. See the two implementations for details.
    """
    if (
        _FAST_EXIT_WALK
        and minute_bars is not None
        and len(minute_bars) >= _FAST_EXIT_WALK_MIN_BARS
        and _exit_walk_fast_eligible(minute_bars)
    ):
        return _walk_lot_exit_numpy(
            pos, minute_bars, exit_cfg=exit_cfg,
            same_minute_resolution=same_minute_resolution, cost_stress=cost_stress,
            quote_supplier=quote_supplier, signal_score_fn=signal_score_fn,
            seed=seed, fade_telemetry_out=fade_telemetry_out, until_ts=until_ts,
            feed=feed, activation_artifact_dir=activation_artifact_dir,
            status_supplier=status_supplier,
        )
    return _walk_lot_exit_pandas(
        pos, minute_bars, exit_cfg=exit_cfg,
        same_minute_resolution=same_minute_resolution, cost_stress=cost_stress,
        quote_supplier=quote_supplier, signal_score_fn=signal_score_fn,
        seed=seed, fade_telemetry_out=fade_telemetry_out, until_ts=until_ts,
        feed=feed, activation_artifact_dir=activation_artifact_dir,
        status_supplier=status_supplier,
    )


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
