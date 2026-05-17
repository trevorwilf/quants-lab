"""Signal-fade scoring per ``[Report §13]``.

Buckets:

  0-2 → no fade
  3-5 → soft fade
  6-8 → hard fade
  9+ → critical fade
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Literal

import pandas as pd

from bowaka_lab.config.models import SignalFadeConfig
from bowaka_lab.features.signal_fade_features import IntradayContext


@dataclass
class FadeComponent:
    name: str
    score: int
    triggered: bool
    reason: str = ""


@dataclass
class SignalFadeResult:
    score: int
    bucket: Literal["none", "soft", "hard", "critical"]
    components: list[FadeComponent] = field(default_factory=list)

    def is_hard_or_above(self) -> bool:
        return self.bucket in ("hard", "critical")


def _bucket_for(score: int) -> Literal["none", "soft", "hard", "critical"]:
    if score >= 9:
        return "critical"
    if score >= 6:
        return "hard"
    if score >= 3:
        return "soft"
    return "none"


def compute_signal_fade_score(
    *,
    entry_price: float,
    mfe_pct: float,
    current_return_pct: float,
    minutes_since_entry: int,
    intraday: IntradayContext,
    max_hold_days_remaining: int = 3,
    rvol_hold_threshold: float = 1.0,
    normal_hold_spread_threshold: float = 0.01,
    severe_spread_threshold: float = 0.03,
    normal_quote_age_threshold: float = 5.0,
    severe_quote_age_threshold: float = 15.0,
) -> SignalFadeResult:
    """Compute the per-Report §13.2 fade score from intraday context.

    All thresholds are configurable. Returns the integer score, the bucket
    label, and the list of triggered components (for explainability).
    """
    components: list[FadeComponent] = []

    def add(name: str, score: int, triggered: bool, reason: str = "") -> None:
        components.append(FadeComponent(name=name, score=score, triggered=bool(triggered), reason=reason))

    current_price = intraday.current_price

    add("price_below_entry", 2, current_price < entry_price)
    if intraday.prior_close is not None:
        add("price_below_prior_close", 2, current_price < intraday.prior_close)
    if intraday.vwap_now is not None:
        # parity-note: Report §13.2 specifies "below VWAP alone -> soft fade".
        # Soft bucket requires score >= 3, so this single trigger must contribute
        # at least 3 by itself. All other "below X level" triggers stay at +2
        # because the spec treats VWAP as a stronger fair-price reference than
        # the other levels (entry, prior close, session open, opening range).
        add("price_below_vwap", 3, current_price < intraday.vwap_now)
    if intraday.session_open is not None:
        add("price_below_session_open", 1, current_price < intraday.session_open)
    if intraday.opening_range_low is not None:
        add("price_below_opening_range_low", 2, current_price < intraday.opening_range_low)
    if intraday.running_low is not None and intraday.running_high > intraday.running_low:
        bottom_40_threshold = intraday.running_low + 0.4 * (intraday.running_high - intraday.running_low)
        add("price_in_bottom_40pct_intraday_range", 1, current_price < bottom_40_threshold)

    # MFE giveback rules (§13.2):
    if mfe_pct >= 0.05:
        giveback_ratio = (mfe_pct - current_return_pct) / mfe_pct if mfe_pct > 0 else 0.0
        if mfe_pct >= 0.12:
            add("mfe_giveback_12pct_70pct", 3, giveback_ratio >= 0.70)
        elif mfe_pct >= 0.08:
            add("mfe_giveback_8pct_60pct", 2, giveback_ratio >= 0.60)
        else:
            add("mfe_giveback_5pct_50pct", 1, giveback_ratio >= 0.50)

    if intraday.rvol_now is not None:
        add("rvol_below_hold_threshold", 1, intraday.rvol_now < rvol_hold_threshold)
    if intraday.last_30m_volume is not None and intraday.morning_continuation_volume:
        ratio = intraday.last_30m_volume / max(intraday.morning_continuation_volume, 1.0)
        add("late_day_volume_drop", 1, ratio < 0.30)
    add("no_higher_high_since_entry", 1, not intraday.made_higher_high_since_entry)
    add("price_below_short_ema", 1, intraday.short_ema_distance < 0)

    if intraday.spread_pct is not None:
        add("spread_above_normal", 1, intraday.spread_pct > normal_hold_spread_threshold)
        add("spread_severe", 2, intraday.spread_pct > severe_spread_threshold)
    if intraday.quote_age_seconds is not None:
        add("quote_age_above_normal", 1, intraday.quote_age_seconds > normal_quote_age_threshold)
        add("quote_age_severe", 2, intraday.quote_age_seconds > severe_quote_age_threshold)

    holding_sessions = minutes_since_entry // 390
    add("multi_day_no_profit", 1, holding_sessions >= 2 and current_return_pct <= 0)
    add("near_max_hold_no_continuation", 2, max_hold_days_remaining <= 1 and not intraday.made_higher_high_since_entry)

    triggered = [c for c in components if c.triggered]
    score = sum(c.score for c in triggered)
    bucket = _bucket_for(score)
    return SignalFadeResult(score=score, bucket=bucket, components=triggered)


def evaluate_at_time(
    *,
    cfg: SignalFadeConfig,
    now: pd.Timestamp,
    session_date: date,
) -> Literal["executable", "log_only", "skip"]:
    """Return the action mode for the current time given the config."""
    if not cfg.enabled:
        return "skip"
    ny_now = now.tz_convert("America/New_York") if now.tzinfo else pd.Timestamp(now, tz="America/New_York")
    rth = time.fromisoformat(cfg.rth_eval_time)
    ac = time.fromisoformat(cfg.after_close_eval_time)
    ts_only = ny_now.time()
    if ts_only >= ac:
        return "log_only" if cfg.after_close_action == "log_only" else "executable"
    if ts_only >= rth:
        return "executable"
    return "skip"
