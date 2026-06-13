"""Common normalized schema for production-vs-lab parity.

Both backtesters are normalized TO this schema so the parity metrics see a
single shape regardless of side-specific field names / casing / timestamps.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Mapping, Optional


@dataclass(frozen=True)
class NormalizedTrade:
    """One trade in both sides' common shape.

    Join keys: ``(session_date, symbol, entry_ts_minute)`` —
    ``entry_ts_minute`` is the entry timestamp floored DOWN to the minute. The
    two sides may differ by sub-minute sequencing, but a disagreement at the
    minute is a genuinely different trade.
    """

    session_date: date
    symbol: str
    entry_ts_minute: datetime    # tz-aware UTC, floored to minute
    entry_price: float
    qty_filled: int
    exit_ts_minute: Optional[datetime]
    exit_price: Optional[float]
    exit_reason: Optional[str]   # 'stop' | 'target' | 'time_stop' | 'signal_fade_*' | 'eod' | 'manual'
    pnl_dollars: float
    side: str = "long"           # Bowaka v2 is long-only (audit §3)

    def __post_init__(self) -> None:
        if self.side != "long":
            raise ValueError(
                f"NormalizedTrade.side must be 'long' (Bowaka v2 is long-only "
                f"per audit §3); got {self.side!r}"
            )

    @property
    def join_key(self) -> tuple[date, str, datetime]:
        return (self.session_date, self.symbol, self.entry_ts_minute)


@dataclass(frozen=True)
class NormalizedCandidate:
    """One candidate-event in both sides' common shape.

    May be partially populated when one side does not emit candidate-level
    telemetry by default (production writes it; the lab emits it under
    ``debug_first_n_trials`` only).
    """

    session_date: date
    symbol: str
    candidate_ts_minute: datetime
    gate_passed: bool
    gate_rejection_reason: Optional[str]   # None when gate_passed=True

    @property
    def join_key(self) -> tuple[date, str, datetime]:
        return (self.session_date, self.symbol, self.candidate_ts_minute)


@dataclass(frozen=True)
class ParityReport:
    window_start: date
    window_end: date
    universe_size: int
    n_sessions: int            # requested XNYS sessions in the window (when known)
    n_trade_sessions: int      # sessions with >=1 trade on either side
    # Production-side counts
    prod_n_candidates: int
    prod_n_trades: int
    prod_gross_pnl: float
    # Lab-side counts
    lab_n_candidates: int
    lab_n_trades: int
    lab_gross_pnl: float
    # Parity metrics (audit §14.5 adapted to sim-vs-sim)
    # Phase 0 (parity oracle): ``None`` == "not measured" (a side lacks candidate
    # telemetry). ``evaluate_thresholds`` EXCLUDES not-measured metrics from the
    # verdict — a missing data source must never report PASS.
    candidate_recall: Optional[float]
    gate_match_rate: Optional[float]
    # L17: ``None`` == "not measured" (no trades to compare on either side). A
    # both-sides-empty parity run is VACUOUS — these rates are None and
    # build_parity_report's vacuous guard (n_trade_sessions == 0) fails the run, so
    # an empty run can never stamp PASS with zero evidence.
    trade_intersection_rate: Optional[float]    # |prod ∩ lab| / |prod ∪ lab|
    fill_price_mae_bps: float
    exit_reason_match_rate: Optional[float]
    daily_pnl_sign_match_rate: Optional[float]
    # Worst divergences for drill-down
    prod_only_trades: list[NormalizedTrade] = field(default_factory=list)
    lab_only_trades: list[NormalizedTrade] = field(default_factory=list)
    largest_fill_diffs: list[Mapping[str, object]] = field(default_factory=list)
    exit_reason_mismatches: list[Mapping[str, object]] = field(default_factory=list)
    # Per-session daily-PnL sign comparison (for the report's per-day table).
    daily_pnl_per_session: list[Mapping[str, object]] = field(default_factory=list)
    # Threshold-pass booleans (audit §14.5 defaults)
    passes_audit_thresholds: bool = False
    failing_metrics: list[str] = field(default_factory=list)


__all__ = ["NormalizedTrade", "NormalizedCandidate", "ParityReport"]
