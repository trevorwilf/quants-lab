"""Phase fidelity-4: ``SimulatedBroker`` FSM unit tests.

Covers parent fill paths (market, marketable_limit, partial, rejection,
timeout), OCO attach (success, retry, failure → fallback / flatten), bracket
exit (stop, target), and ``order_events.parquet`` schema.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from bowaka_lab.config.models import BrokerSimConfig
from bowaka_lab.sim.broker import (
    EVT_FALLBACK_STOP_SUBMITTED,
    EVT_FLATTEN,
    EVT_OCO_ATTACHED,
    EVT_OCO_ATTACH_FAILED,
    EVT_OCO_ATTACH_PENDING,
    EVT_PARENT_FILLED,
    EVT_PARENT_PARTIALLY_FILLED,
    EVT_PARENT_REJECTED,
    EVT_MARKETABLE_LIMIT_TIMED_OUT,
    EVT_STOP_HIT,
    EVT_TARGET_HIT,
    SimulatedBroker,
)
from bowaka_lab.sim.orders import OrderStatus, ProtectionState


BAR = {"symbol": "AAA", "open": 10.0, "high": 10.1, "low": 9.9, "close": 10.0}
QUOTE = {"timestamp": pd.Timestamp("2026-05-12 14:00:00", tz="UTC"), "bid_price": 9.95, "ask_price": 10.05}
_T0 = pd.Timestamp("2026-05-12 14:00:00", tz="UTC")


def _cfg(**kw):
    base = {"enabled": True, "parent_fill_latency_seconds": 0.0,
            "oco_attach_latency_seconds": 0.0}
    base.update(kw)
    return BrokerSimConfig.model_validate(base)


# ---------- parent fills ----------


def test_broker_parent_fill_market_default():
    cfg = _cfg(parent_fill_latency_seconds=0.0)
    broker = SimulatedBroker(cfg)
    parent = broker.submit_parent(symbol="AAA", side="buy", qty=100, style="market",
                                  limit_price=None, ts=_T0)
    evts = broker.step(now_ts=_T0, bar=BAR, quote=QUOTE)
    types = {e.event_type for e in evts}
    assert EVT_PARENT_FILLED in types
    assert parent.status == OrderStatus.FILLED
    assert parent.filled_qty == 100
    assert parent.avg_fill_price == QUOTE["ask_price"]


def test_broker_parent_fill_marketable_limit_passes_when_ask_within_limit():
    cfg = _cfg(parent_fill_latency_seconds=0.0, marketable_limit_timeout_seconds=30)
    broker = SimulatedBroker(cfg)
    parent = broker.submit_parent(symbol="AAA", side="buy", qty=50, style="marketable_limit",
                                  limit_price=10.10, ts=_T0, timeout_seconds=30)
    evts = broker.step(now_ts=_T0, bar=BAR, quote=QUOTE)
    assert any(e.event_type == EVT_PARENT_FILLED for e in evts)


def test_broker_marketable_limit_timeout_emits_expired_event():
    cfg = _cfg(parent_fill_latency_seconds=0.0, marketable_limit_timeout_seconds=5)
    broker = SimulatedBroker(cfg)
    parent = broker.submit_parent(symbol="AAA", side="buy", qty=50, style="marketable_limit",
                                  limit_price=9.50, ts=_T0, timeout_seconds=5)
    # ask=10.05 > limit=9.50 → no fill. Advance past timeout.
    broker.step(now_ts=_T0, bar=BAR, quote=QUOTE)
    evts = broker.step(now_ts=_T0 + pd.Timedelta(seconds=10), bar=BAR, quote=QUOTE)
    assert any(e.event_type == EVT_MARKETABLE_LIMIT_TIMED_OUT for e in evts)
    assert parent.status == OrderStatus.EXPIRED


def test_broker_parent_partial_fill_then_full():
    cfg = _cfg(parent_fill_latency_seconds=0.0,
               partial_fill_probability=1.0, partial_fill_min_fraction=0.5)
    broker = SimulatedBroker(cfg, rng=np.random.default_rng(7))
    parent = broker.submit_parent(symbol="AAA", side="buy", qty=100, style="market",
                                  limit_price=None, ts=_T0)
    broker.step(now_ts=_T0, bar=BAR, quote=QUOTE)
    assert parent.filled_qty < 100
    assert parent.status == OrderStatus.PARTIALLY_FILLED
    # Next step finishes the remainder.
    broker.step(now_ts=_T0 + pd.Timedelta(seconds=1), bar=BAR, quote=QUOTE)
    assert parent.status == OrderStatus.FILLED
    assert parent.filled_qty == 100
    types = {e.event_type for e in broker.events}
    assert EVT_PARENT_PARTIALLY_FILLED in types
    assert EVT_PARENT_FILLED in types


def test_broker_rejection():
    cfg = _cfg(broker_rejection_probability=1.0)
    broker = SimulatedBroker(cfg)
    parent = broker.submit_parent(symbol="AAA", side="buy", qty=100, style="market",
                                  limit_price=None, ts=_T0)
    broker.step(now_ts=_T0, bar=BAR, quote=QUOTE)
    assert parent.status == OrderStatus.REJECTED
    assert any(e.event_type == EVT_PARENT_REJECTED for e in broker.events)


# ---------- OCO attach ----------


def test_broker_oco_attach_success():
    cfg = _cfg()
    broker = SimulatedBroker(cfg)
    parent = broker.submit_parent(symbol="AAA", side="buy", qty=100, style="market",
                                  limit_price=None, ts=_T0)
    broker.step(now_ts=_T0, bar=BAR, quote=QUOTE)
    bracket = broker.attach_oco(
        parent=parent, stop_price=9.20, target_price=11.50, ts=_T0,
    )
    broker.step(now_ts=_T0 + pd.Timedelta(seconds=1), bar=BAR, quote=QUOTE)
    assert bracket.state == ProtectionState.OCO_ACTIVE
    types = [e.event_type for e in broker.events]
    assert EVT_OCO_ATTACH_PENDING in types
    assert EVT_OCO_ATTACHED in types


def test_broker_oco_attach_failure_retry_then_fallback():
    cfg = _cfg(oco_attach_failure_probability=1.0, max_oco_attach_attempts=2,
               fallback_stop_enabled=True, max_unprotected_seconds=0)
    broker = SimulatedBroker(cfg)
    parent = broker.submit_parent(symbol="AAA", side="buy", qty=100, style="market",
                                  limit_price=None, ts=_T0)
    broker.step(now_ts=_T0, bar=BAR, quote=QUOTE)
    bracket = broker.attach_oco(parent=parent, stop_price=9.20, target_price=11.50, ts=_T0)
    broker.step(now_ts=_T0 + pd.Timedelta(seconds=1), bar=BAR, quote=QUOTE)
    broker.step(now_ts=_T0 + pd.Timedelta(seconds=2), bar=BAR, quote=QUOTE)
    types = [e.event_type for e in broker.events]
    assert types.count(EVT_OCO_ATTACH_FAILED) >= 2
    assert EVT_FALLBACK_STOP_SUBMITTED in types
    assert bracket.state == ProtectionState.FALLBACK_STOP_ACTIVE


def test_broker_oco_attach_failure_then_flatten():
    cfg = _cfg(oco_attach_failure_probability=1.0, max_oco_attach_attempts=1,
               fallback_stop_enabled=False, flatten_if_unprotected=True,
               max_unprotected_seconds=0)
    broker = SimulatedBroker(cfg)
    parent = broker.submit_parent(symbol="AAA", side="buy", qty=100, style="market",
                                  limit_price=None, ts=_T0)
    broker.step(now_ts=_T0, bar=BAR, quote=QUOTE)
    bracket = broker.attach_oco(parent=parent, stop_price=9.20, target_price=11.50, ts=_T0)
    broker.step(now_ts=_T0 + pd.Timedelta(seconds=1), bar=BAR, quote=QUOTE)
    types = [e.event_type for e in broker.events]
    assert EVT_FLATTEN in types
    assert bracket.state == ProtectionState.FLATTENING


# ---------- bracket exits ----------


def test_broker_stop_hit_closes_bracket():
    cfg = _cfg()
    broker = SimulatedBroker(cfg)
    parent = broker.submit_parent(symbol="AAA", side="buy", qty=100, style="market",
                                  limit_price=None, ts=_T0)
    broker.step(now_ts=_T0, bar=BAR, quote=QUOTE)
    bracket = broker.attach_oco(parent=parent, stop_price=9.20, target_price=11.50, ts=_T0)
    broker.step(now_ts=_T0 + pd.Timedelta(seconds=1), bar=BAR, quote=QUOTE)
    # Stop-hit bar.
    bad_bar = {"symbol": "AAA", "open": 9.30, "high": 9.30, "low": 9.10, "close": 9.15}
    evts = broker.step(now_ts=_T0 + pd.Timedelta(seconds=60), bar=bad_bar, quote=None)
    assert any(e.event_type == EVT_STOP_HIT for e in evts)
    assert bracket.state == ProtectionState.CLOSED
    assert bracket.exit_reason == "stop_hit"


def test_broker_target_hit_closes_bracket():
    cfg = _cfg()
    broker = SimulatedBroker(cfg)
    parent = broker.submit_parent(symbol="AAA", side="buy", qty=100, style="market",
                                  limit_price=None, ts=_T0)
    broker.step(now_ts=_T0, bar=BAR, quote=QUOTE)
    bracket = broker.attach_oco(parent=parent, stop_price=9.20, target_price=11.50, ts=_T0)
    broker.step(now_ts=_T0 + pd.Timedelta(seconds=1), bar=BAR, quote=QUOTE)
    good_bar = {"symbol": "AAA", "open": 10.5, "high": 11.6, "low": 10.4, "close": 11.55}
    evts = broker.step(now_ts=_T0 + pd.Timedelta(seconds=60), bar=good_bar, quote=None)
    assert any(e.event_type == EVT_TARGET_HIT for e in evts)
    assert bracket.exit_reason == "target_hit"


# ---------- artifact schema ----------


def test_order_events_artifact_schema():
    cfg = _cfg()
    broker = SimulatedBroker(cfg)
    parent = broker.submit_parent(symbol="AAA", side="buy", qty=100, style="market",
                                  limit_price=None, ts=_T0)
    broker.step(now_ts=_T0, bar=BAR, quote=QUOTE)
    df = broker.events_df()
    expected_cols = {
        "event_id", "ts", "event_type", "parent_order_id", "bracket_id",
        "symbol", "qty", "price", "reason", "attach_attempt", "protection_state",
    }
    assert expected_cols.issubset(set(df.columns))
    assert df.shape[0] >= 1
