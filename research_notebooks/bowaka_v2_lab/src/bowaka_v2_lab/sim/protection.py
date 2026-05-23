"""OCO / protected-position lifecycle state machine (Realism rem-2 Phase 6).

Audit finding **P0-007** documents that the lab's pre-Phase-6 strategy consumer
created a ``Position`` with ``bracket_attached=True`` the moment the simulated
fill landed. The live strategy is materially more nuanced (see
``bowaka_v2_strategy.py`` lines 848-1239 and the ``protected_position`` block
in ``bowaka_v2_config.yaml`` lines 248-254):

1. Submit a parent order.
2. Record a ``pending_fill`` position only after the broker accepts the submit.
3. Poll for the parent fill.
4. Only AFTER the actual fill, attach OCO children
   (``submit_oco_children_v2()`` / ``submit_pending_oco_children_v2()``).
5. Enforce the protected-position invariant:

   - ``max_unprotected_seconds: 10`` — max time the lot may sit unprotected.
   - ``oco_attach_attempts: 2`` — number of OCO attach attempts before fallback.
   - ``fallback_stop_enabled: true`` — submit a manual stop on final failure.
   - ``flatten_if_unprotected: true`` — flatten the lot on terminal failure.
   - ``block_entries_on_violation: true`` — refuse new SCANs until reattach /
     flat.

The unprotected interval is one of the most important live risks. The Phase-4
event loop already reserved ``OCO_ATTACH_ATTEMPT`` / ``PROTECTION_CHECK`` /
``CHILD_FILL`` events; Phase 6 wires the lifecycle to those.

This module is the orchestrator. The :class:`ProtectionStateMachine` owns the
per-lot state transitions; the backtester invokes it on each lifecycle event:

* ``on_parent_fill(pos, fill_ts, *, queue)`` — record the fill ts and schedule
  the first ``OCO_ATTACH_ATTEMPT`` at ``fill_ts + oco_attach_latency_seconds``.
* ``on_oco_attach_attempt(pos, ts, *, queue, attach_succeeds)`` — try the
  attach. On success → :attr:`ProtectionState.PROTECTED`. On failure →
  retry (up to ``oco_attach_attempts``) or terminal-fail to
  :attr:`ProtectionState.OCO_ATTACH_FAILED` and trigger the violation flow.
* ``on_protection_check(pos, ts, *, queue)`` — if ``now - parent_fill_ts >
  max_unprotected_seconds`` and the lot is still in
  :attr:`ProtectionState.OCO_ATTACH_PENDING`, escalate to
  :attr:`ProtectionState.UNPROTECTED_VIOLATION` and trigger the violation flow.

The violation flow:

* ``fallback_stop_enabled=True`` → record a fallback-stop submission marker
  (the synthetic stop fires when the price path next breaches ``stop_price``).
* ``flatten_if_unprotected=True`` → schedule an immediate market flatten at
  the next event tick (we model this as setting ``protection_state =
  ProtectionState.FLATTEN_SUBMITTED`` so the next exit walk closes the lot at
  the prevailing minute close).
* ``block_entries_on_violation=True`` → set ``Portfolio.state.entries_blocked
  = True`` until the lot reaches PROTECTED again or closes flat.

The state machine is deliberately *separate* from the event loop. Its callers
synthesize :class:`sim.event_loop.Event`'s; the machine mutates ``Position``
and ``Portfolio`` and returns a small ``ProtectionStepResult`` describing what
the loop should do next (push another event, log a metric, etc.). This keeps
the test surface narrow — every transition can be unit-tested by calling the
machine directly.

Phase 8 will wire the per-violation optuna objective penalty using the
``Portfolio.protection_metrics.unprotected_violation_count`` counter. For
Phase 6 the metric is exposed (and the hook left in
:func:`compute_protection_penalty`) — the actual objective change is deferred.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import pandas as pd

from .event_loop import Event, EventQueue, EventType
from .portfolio import (
    Portfolio,
    Position,
    ProtectionMetrics,
    ProtectionState,
)


# ---- public config / metric API ------------------------------------------


@dataclass(frozen=True)
class ProtectionConfig:
    """Resolved ``protected_position`` config (Phase 6 task 2).

    The contract values come from ``bowaka_v2_config.yaml`` lines 248-254. A
    runtime config inherits these defaults unless ``protected_position`` is
    explicitly overridden; the canonicalizer pins them so the optuna search
    space does not perturb them.

    ``oco_attach_latency_seconds`` is the modeling delay between PARENT_FILL
    and the first OCO_ATTACH_ATTEMPT; defaults to 0.5s (a live API round-trip).
    ``protection_stress`` injects deterministic failure scenarios — used by
    the audit-acceptance tests. Valid values:

    * ``"none"`` (default) — every attach attempt succeeds.
    * ``"oco_attach_fail_once"`` — the first attempt fails; later attempts
      succeed.
    * ``"oco_attach_fail_always"`` — every attempt fails (final state =
      OCO_ATTACH_FAILED, fallback / flatten triggered).
    * ``"delayed_attach"`` — the first attempt fires later than the configured
      latency (modeling a network-stall) so the lot is in
      OCO_ATTACH_PENDING > ``max_unprotected_seconds`` → UNPROTECTED_VIOLATION.
    * ``"halt_during_unprotected"`` — same as ``"delayed_attach"`` plus a
      halted-status flag, so the violation flow's halt path is exercised.

    Failure rates from a probabilistic stress are RNG-seeded on
    ``(run_seed, position_id)`` so two runs of the same config agree.
    """

    enabled: bool = True
    max_unprotected_seconds: float = 10.0
    oco_attach_attempts: int = 2
    fallback_stop_enabled: bool = True
    flatten_if_unprotected: bool = True
    block_entries_on_violation: bool = True
    oco_attach_latency_seconds: float = 0.5
    delayed_attach_extra_seconds: float = 5.0
    protection_stress: str = "none"
    #: Per-violation penalty used by the Phase-8 optuna objective (Phase 6
    #: task 5). Exposed here so a config can carry it; the hook
    #: :func:`compute_protection_penalty` uses it.
    unprotected_violation_penalty: float = -1.0

    @classmethod
    def from_cfg(cls, cfg: Mapping[str, Any]) -> "ProtectionConfig":
        """Resolve a :class:`ProtectionConfig` from the run cfg dict.

        Reads the ``protected_position`` block plus a few ``simulation`` /
        ``execution`` overrides. Unspecified fields fall back to the contract
        defaults declared on this dataclass.
        """
        pp = (cfg.get("protected_position") or {}) if cfg else {}
        sim = (cfg.get("simulation") or {}) if cfg else {}
        execution = (cfg.get("execution") or {}) if cfg else {}
        return cls(
            enabled=bool(pp.get("enabled", True)),
            max_unprotected_seconds=float(
                pp.get("max_unprotected_seconds", 10.0)
            ),
            oco_attach_attempts=int(
                pp.get("oco_attach_attempts", pp.get("max_oco_attach_attempts", 2))
            ),
            fallback_stop_enabled=bool(pp.get("fallback_stop_enabled", True)),
            flatten_if_unprotected=bool(pp.get("flatten_if_unprotected", True)),
            block_entries_on_violation=bool(
                pp.get("block_entries_on_violation", True)
            ),
            oco_attach_latency_seconds=float(
                execution.get(
                    "oco_attach_latency_seconds",
                    pp.get("oco_attach_latency_seconds", 0.5),
                )
            ),
            delayed_attach_extra_seconds=float(
                pp.get("delayed_attach_extra_seconds", 5.0)
            ),
            protection_stress=str(
                sim.get(
                    "protection_stress",
                    pp.get("protection_stress", "none"),
                )
            ),
            unprotected_violation_penalty=float(
                pp.get("unprotected_violation_penalty", -1.0)
            ),
        )


@dataclass
class ProtectionStepResult:
    """Outcome of one :class:`ProtectionStateMachine` step.

    The state machine itself never pushes events; it returns a small bundle so
    the dispatch caller in the backtester can:

    * Schedule the follow-up events (``follow_up_events``).
    * Decide whether to log an extra event row (``log_extras``).

    The state-machine call site emits an event-log row even when no follow-up
    is scheduled, so ``log_extras`` is purely additional context.
    """

    follow_up_events: list[Event] = field(default_factory=list)
    log_extras: dict[str, Any] = field(default_factory=dict)


def _to_utc(ts: Any) -> pd.Timestamp:
    """Coerce ``ts`` to a tz-aware UTC :class:`pd.Timestamp`."""
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


# ---- state-machine orchestrator ------------------------------------------


class ProtectionStateMachine:
    """Per-run protection lifecycle driver (Phase 6 tasks 1-4).

    A single instance is constructed by the backtester and reused across
    sessions. State lives on the ``Position`` (the per-lot transitions, the
    ``parent_fill_ts``, the attempt count) and the ``Portfolio``
    (``protection_metrics``, ``state.entries_blocked``). The machine itself is
    stateless apart from the resolved :class:`ProtectionConfig` and a run-seed
    for deterministic stress injection.
    """

    def __init__(
        self,
        *,
        cfg: ProtectionConfig,
        run_seed: int = 0,
    ) -> None:
        self._cfg = cfg
        self._run_seed = int(run_seed)

    @property
    def cfg(self) -> ProtectionConfig:
        return self._cfg

    # ---- transitions ----------------------------------------------------

    def initial_state_for_parent(
        self, *, accepted_event_sequencing: str = "pre_submit"
    ) -> ProtectionState:
        """Return the initial protection state a new ``Position`` should be in
        right after the broker accepts the parent submission.

        ``pre_submit`` (parity / smoke) and ``post_submit`` (realism) both
        start at :attr:`ProtectionState.PARENT_ACKNOWLEDGED` — the broker has
        confirmed the submission but the parent has not filled yet. The
        consumer transitions to :attr:`ProtectionState.PARENT_FILLED` via
        :meth:`on_parent_fill` once the synchronous fill model lands.
        """
        return ProtectionState.PARENT_ACKNOWLEDGED

    def on_parent_fill(
        self,
        pos: Position,
        fill_ts: Any,
        *,
        portfolio: Portfolio,
        queue: Optional[EventQueue] = None,
        session_date: Optional[_dt.date] = None,
    ) -> ProtectionStepResult:
        """Transition a lot to PARENT_FILLED → OCO_ATTACH_PENDING and schedule
        the first OCO_ATTACH_ATTEMPT.

        Records ``pos.parent_fill_ts`` (the start of the unprotected interval)
        and pushes the first OCO_ATTACH_ATTEMPT at
        ``fill_ts + oco_attach_latency_seconds`` (or
        ``+ delayed_attach_extra_seconds`` under the ``delayed_attach`` /
        ``halt_during_unprotected`` stresses).
        """
        result = ProtectionStepResult()
        fill_ts_utc = _to_utc(fill_ts)
        pos.parent_fill_ts = fill_ts_utc.isoformat()
        # PARENT_FILLED is the terminal post-fill state; we immediately enter
        # the OCO attach loop.
        pos.set_protection_state(ProtectionState.PARENT_FILLED)
        # If protection is disabled (e.g. an old config without the block),
        # skip straight to PROTECTED so the lot is treated as live-attached.
        if not self._cfg.enabled:
            pos.set_protection_state(ProtectionState.PROTECTED)
            pos.protected_ts = fill_ts_utc.isoformat()
            return result
        pos.set_protection_state(ProtectionState.OCO_ATTACH_PENDING)
        # Schedule the first attach attempt.
        latency = self._cfg.oco_attach_latency_seconds
        if self._cfg.protection_stress in (
            "delayed_attach",
            "halt_during_unprotected",
        ):
            latency = latency + self._cfg.delayed_attach_extra_seconds
        attempt_ts = fill_ts_utc + pd.Timedelta(seconds=latency)
        first_attempt = Event(
            timestamp=attempt_ts,
            type=EventType.OCO_ATTACH_ATTEMPT,
            payload={
                "session_date": session_date,
                "position_id": pos.position_id,
                "symbol": pos.symbol,
                "attempt_index": 0,
            },
        )
        if queue is not None:
            queue.push(first_attempt)
        result.follow_up_events.append(first_attempt)
        return result

    def on_oco_attach_attempt(
        self,
        pos: Position,
        ts: Any,
        *,
        portfolio: Portfolio,
        queue: Optional[EventQueue] = None,
        session_date: Optional[_dt.date] = None,
        attempt_index: int = 0,
    ) -> ProtectionStepResult:
        """Simulate one OCO attach attempt.

        On success the lot transitions to :attr:`ProtectionState.PROTECTED`;
        the unprotected interval is closed at ``ts`` and the per-lot
        ``total_unprotected_seconds`` is updated.

        On failure the attempt counter increments; if there are retries left
        a fresh OCO_ATTACH_ATTEMPT is scheduled at
        ``ts + oco_attach_latency_seconds``. On final failure the lot
        transitions to :attr:`ProtectionState.OCO_ATTACH_FAILED` and the
        violation flow runs (fallback stop / flatten / entries-blocked).
        """
        result = ProtectionStepResult()
        ts_utc = _to_utc(ts)
        # Don't act on a lot that already reached a terminal protection state
        # (e.g. a stale event for a closed lot).
        if pos.protection_state not in (
            ProtectionState.OCO_ATTACH_PENDING,
            ProtectionState.UNPROTECTED_VIOLATION,
        ):
            result.log_extras["stale_attempt"] = True
            return result
        pos.oco_attach_attempt_count = max(
            pos.oco_attach_attempt_count, int(attempt_index) + 1
        )
        portfolio.protection_metrics.oco_attach_attempts_count += 1
        # Decide success / failure (stress-injected).
        attach_succeeds = self._attach_succeeds(
            pos=pos, attempt_index=int(attempt_index)
        )
        if attach_succeeds:
            pos.set_protection_state(ProtectionState.OCO_ATTACHED)
            pos.set_protection_state(ProtectionState.PROTECTED)
            pos.protected_ts = ts_utc.isoformat()
            unprotected_seconds = self._elapsed_seconds(pos, until=ts_utc)
            pos.total_unprotected_seconds += unprotected_seconds
            if portfolio.protection_metrics.max_unprotected_seconds_observed < unprotected_seconds:
                portfolio.protection_metrics.max_unprotected_seconds_observed = unprotected_seconds
            # Release entries_blocked if no other lot is still in violation.
            portfolio._refresh_entries_blocked()
            result.log_extras["attach_succeeded"] = True
            result.log_extras["attempt_index"] = int(attempt_index)
            return result
        # Attach failed.
        portfolio.protection_metrics.oco_attach_failure_count += 1
        result.log_extras["attach_succeeded"] = False
        result.log_extras["attempt_index"] = int(attempt_index)
        attempts_made = int(attempt_index) + 1
        if attempts_made < self._cfg.oco_attach_attempts:
            # Retry — push the next attempt; lot stays in OCO_ATTACH_PENDING.
            retry_ts = ts_utc + pd.Timedelta(
                seconds=self._cfg.oco_attach_latency_seconds
            )
            retry_event = Event(
                timestamp=retry_ts,
                type=EventType.OCO_ATTACH_ATTEMPT,
                payload={
                    "session_date": session_date,
                    "position_id": pos.position_id,
                    "symbol": pos.symbol,
                    "attempt_index": attempts_made,
                },
            )
            if queue is not None:
                queue.push(retry_event)
            result.follow_up_events.append(retry_event)
            return result
        # Final attempt failed → terminal OCO_ATTACH_FAILED → violation flow.
        pos.set_protection_state(ProtectionState.OCO_ATTACH_FAILED)
        return self._trigger_violation(
            pos, ts_utc, portfolio=portfolio, queue=queue,
            session_date=session_date, accumulated=result,
        )

    def on_protection_check(
        self,
        ts: Any,
        *,
        portfolio: Portfolio,
        queue: Optional[EventQueue] = None,
        session_date: Optional[_dt.date] = None,
    ) -> ProtectionStepResult:
        """Sweep every open lot — escalate any that has been OCO_ATTACH_PENDING
        beyond ``max_unprotected_seconds``.

        The Phase-4 event loop ticks PROTECTION_CHECK at
        ``protection_poll_interval_seconds`` (5s by default), so a single lot
        in OCO_ATTACH_PENDING is swept once per tick.
        """
        result = ProtectionStepResult()
        ts_utc = _to_utc(ts)
        for pos in list(portfolio.open_positions.values()):
            if pos.protection_state != ProtectionState.OCO_ATTACH_PENDING:
                continue
            elapsed = self._elapsed_seconds(pos, until=ts_utc)
            if elapsed > self._cfg.max_unprotected_seconds:
                # Escalate to violation. ``pos.total_unprotected_seconds``
                # accumulates the full window so the metric stays accurate
                # even if the lot later flattens.
                pos.total_unprotected_seconds += elapsed
                if portfolio.protection_metrics.max_unprotected_seconds_observed < elapsed:
                    portfolio.protection_metrics.max_unprotected_seconds_observed = elapsed
                pos.set_protection_state(ProtectionState.UNPROTECTED_VIOLATION)
                step = self._trigger_violation(
                    pos, ts_utc, portfolio=portfolio, queue=queue,
                    session_date=session_date,
                )
                result.follow_up_events.extend(step.follow_up_events)
                # Roll the per-lot extras into the result so the caller can
                # log them on the PROTECTION_CHECK row.
                for k, v in step.log_extras.items():
                    result.log_extras.setdefault(k, v)
        return result

    def on_child_fill(
        self,
        pos: Position,
        ts: Any,
        *,
        portfolio: Portfolio,
        exit_reason: str = "child_exit",
    ) -> ProtectionStepResult:
        """Transition a lot to a terminal exit state on CHILD_FILL.

        Called by the backtester when ``walk_lot_exit`` returns an exit.
        Distinguishes a normal child exit (``child_exit_filled``) from a
        manual flatten (``manual_exit_filled``) using the exit reason.
        """
        result = ProtectionStepResult()
        terminal = (
            ProtectionState.MANUAL_EXIT_FILLED
            if str(exit_reason) in ("manual_flatten", "fallback_stop")
            else ProtectionState.CHILD_EXIT_FILLED
        )
        pos.set_protection_state(terminal)
        # ``Portfolio.close_position_by_id`` is the one that pops the lot off
        # ``open_positions``; this method only does the state transition so
        # the dispatch path can log the CHILD_FILL row coherently.
        return result

    # ---- violation flow -------------------------------------------------

    def _trigger_violation(
        self,
        pos: Position,
        ts: pd.Timestamp,
        *,
        portfolio: Portfolio,
        queue: Optional[EventQueue],
        session_date: Optional[_dt.date],
        accumulated: Optional[ProtectionStepResult] = None,
    ) -> ProtectionStepResult:
        """Apply the violation remediation policy.

        Order of operations matches the live strategy contract:

        1. Block entries (sets ``Portfolio.state.entries_blocked``).
        2. If ``fallback_stop_enabled`` — record a fallback-stop marker. The
           marker is the per-lot ``fallback_stop_ts``; the exit walker reads
           it via the normal stop path (so a price breach below stop_price
           still closes the lot with exit_reason ``fallback_stop`` /
           ``stop_loss``).
        3. If ``flatten_if_unprotected`` — set state to
           :attr:`ProtectionState.FLATTEN_SUBMITTED` and (if a queue is
           supplied) push a PROTECTION_CHECK at ``ts`` so the loop runs the
           dispatch's manual-flatten on the next tick. The actual flatten is
           done by the backtester (closing the lot at the prevailing price).

        The ``UNPROTECTED_VIOLATION`` and `FALLBACK_STOP_SUBMITTED` /
        `FLATTEN_SUBMITTED` states co-exist; the FALLBACK / FLATTEN flag is
        the "what remediation we picked"; the violation marker drives the
        run-report and Phase-8 penalty.
        """
        result = accumulated or ProtectionStepResult()
        portfolio.protection_metrics.unprotected_violation_count += 1
        if self._cfg.block_entries_on_violation:
            if portfolio.state is not None:
                portfolio.state.entries_blocked = True
        # Ensure the lot is in the violation state (the caller may have only
        # just set OCO_ATTACH_FAILED on us; promote to UNPROTECTED_VIOLATION
        # so the next protection-check sweep / risk-gate sees the canonical
        # marker — but only if we haven't already moved past it).
        if pos.protection_state in (
            ProtectionState.OCO_ATTACH_FAILED,
            ProtectionState.OCO_ATTACH_PENDING,
        ):
            pos.set_protection_state(ProtectionState.UNPROTECTED_VIOLATION)
        # Fallback-stop marker.
        if self._cfg.fallback_stop_enabled and pos.fallback_stop_ts is None:
            pos.fallback_stop_ts = ts.isoformat()
            portfolio.protection_metrics.fallback_stop_count += 1
            pos.set_protection_state(ProtectionState.FALLBACK_STOP_SUBMITTED)
            result.log_extras["fallback_stop_submitted"] = True
        # Flatten policy.
        if self._cfg.flatten_if_unprotected:
            # We schedule the flatten as a marker; the backtester's event
            # dispatcher (see backtester.py) closes the lot at the next
            # PROTECTION_CHECK tick. To minimize the close latency we push an
            # additional PROTECTION_CHECK at ``ts + 1ms`` so the close lands
            # within the same event boundary the violation fired on.
            pos.flatten_ts = ts.isoformat()
            portfolio.protection_metrics.flatten_unprotected_count += 1
            pos.set_protection_state(ProtectionState.FLATTEN_SUBMITTED)
            result.log_extras["flatten_submitted"] = True
            if queue is not None:
                imminent = ts + pd.Timedelta(milliseconds=1)
                followup = Event(
                    timestamp=imminent,
                    type=EventType.PROTECTION_CHECK,
                    payload={
                        "session_date": session_date,
                        "flatten_trigger": True,
                    },
                )
                queue.push(followup)
                result.follow_up_events.append(followup)
        return result

    # ---- stress / determinism helpers -----------------------------------

    def _attach_succeeds(self, *, pos: Position, attempt_index: int) -> bool:
        """Stress-injected success decision.

        ``protection_stress`` values (see :class:`ProtectionConfig`):

        * ``"none"`` — always succeed.
        * ``"oco_attach_fail_once"`` — fail on attempt 0; succeed thereafter.
        * ``"oco_attach_fail_always"`` — always fail.
        * ``"delayed_attach"`` — eventually succeeds, but slowly (latency is
          increased in :meth:`on_parent_fill`). Attempts still succeed.
        * ``"halt_during_unprotected"`` — same as ``delayed_attach``; the
          violation flow handles the halt context elsewhere.
        """
        stress = self._cfg.protection_stress
        if stress == "oco_attach_fail_always":
            return False
        if stress == "oco_attach_fail_once":
            return attempt_index >= 1
        # default: success
        return True

    def _elapsed_seconds(self, pos: Position, *, until: pd.Timestamp) -> float:
        """Seconds between ``pos.parent_fill_ts`` and ``until`` (UTC).

        Returns 0.0 if the lot has no recorded parent_fill_ts (a degenerate
        case the state machine should never reach, but guarded for safety).
        """
        if pos.parent_fill_ts is None:
            return 0.0
        try:
            start = pd.Timestamp(pos.parent_fill_ts)
            if start.tzinfo is None:
                start = start.tz_localize("UTC")
            delta = until - start
            return float(delta.total_seconds())
        except Exception:  # noqa: BLE001 — parent_fill_ts is best-effort
            return 0.0


# ---- Optuna objective penalty hook (Phase 6 task 5; wired Phase 8) -------


def compute_protection_penalty(
    metrics: ProtectionMetrics, *, per_violation_penalty: float = -1.0
) -> float:
    """Return the run-level penalty an Optuna objective should apply.

    Phase 6 task 5 — expose the hook here so the Phase-8 objective change
    can call it without restructuring the run-report layer. Each
    ``unprotected_violation`` adds ``per_violation_penalty`` (default ``-1.0``,
    a config-tunable knob on :class:`ProtectionConfig`).

    This function is intentionally a thin sum so a Phase-8 reviewer can audit
    the math at a glance; the substantive Optuna wiring belongs in
    ``optuna/objective.py``.
    """
    n_violations = int(metrics.unprotected_violation_count)
    return float(per_violation_penalty) * n_violations
