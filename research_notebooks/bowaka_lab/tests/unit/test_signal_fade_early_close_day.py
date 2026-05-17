"""Phase 6: 15:45 ET still applies on early-close days; later 16:05 falls after close."""

from __future__ import annotations

from datetime import date

import pandas as pd

from bowaka_lab.config.models import SignalFadeConfig
from bowaka_lab.data.calendar import USEquityCalendar
from bowaka_lab.sim.signal_fade import evaluate_at_time


def test_early_close_still_uses_1545_rule():
    # Thanksgiving Friday 2025 closes at 13:00 ET.
    cfg = SignalFadeConfig(rth_eval_time="15:45", after_close_eval_time="16:05", after_close_action="log_only")
    sd = date(2025, 11, 28)
    now = pd.Timestamp("2025-11-28 12:30", tz="America/New_York")
    # 12:30 ET < 15:45 → skip (config time-of-day semantics, calendar-aware
    # is the backtester's job).
    assert evaluate_at_time(cfg=cfg, now=now, session_date=sd) == "skip"


def test_early_close_after_close_eval_remains_log_only():
    cfg = SignalFadeConfig(rth_eval_time="15:45", after_close_eval_time="16:05", after_close_action="log_only")
    sd = date(2025, 11, 28)
    now = pd.Timestamp("2025-11-28 16:10", tz="America/New_York")
    assert evaluate_at_time(cfg=cfg, now=now, session_date=sd) == "log_only"


def test_calendar_is_early_close_marker():
    cal = USEquityCalendar()
    assert cal.is_early_close(date(2025, 11, 28))
