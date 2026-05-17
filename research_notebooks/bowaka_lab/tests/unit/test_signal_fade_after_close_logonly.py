"""Phase 6: 16:05 ET evaluation is log_only regardless of bucket."""

from __future__ import annotations

import pandas as pd
import pytest

from bowaka_lab.config.models import SignalFadeConfig
from bowaka_lab.sim.signal_fade import evaluate_at_time
from datetime import date


def test_after_close_log_only_default():
    cfg = SignalFadeConfig(after_close_action="log_only")
    now = pd.Timestamp("2026-05-12 16:10", tz="America/New_York")
    assert evaluate_at_time(cfg=cfg, now=now, session_date=date(2026, 5, 12)) == "log_only"


def test_after_close_exit_when_explicitly_configured():
    cfg = SignalFadeConfig(after_close_action="exit")
    now = pd.Timestamp("2026-05-12 16:10", tz="America/New_York")
    assert evaluate_at_time(cfg=cfg, now=now, session_date=date(2026, 5, 12)) == "executable"


def test_before_rth_eval_time_skipped():
    cfg = SignalFadeConfig(rth_eval_time="15:45", after_close_eval_time="16:05")
    now = pd.Timestamp("2026-05-12 14:00", tz="America/New_York")
    assert evaluate_at_time(cfg=cfg, now=now, session_date=date(2026, 5, 12)) == "skip"


def test_rth_eval_time_executable():
    cfg = SignalFadeConfig(rth_eval_time="15:45", after_close_eval_time="16:05")
    now = pd.Timestamp("2026-05-12 15:50", tz="America/New_York")
    assert evaluate_at_time(cfg=cfg, now=now, session_date=date(2026, 5, 12)) == "executable"


def test_disabled_returns_skip():
    cfg = SignalFadeConfig(enabled=False)
    now = pd.Timestamp("2026-05-12 15:50", tz="America/New_York")
    assert evaluate_at_time(cfg=cfg, now=now, session_date=date(2026, 5, 12)) == "skip"
