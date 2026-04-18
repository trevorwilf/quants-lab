"""Composite EMA dataset identity and cache-key uniqueness tests."""
import numpy as np
import pytest


def _make_candles(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    bars = np.zeros(n, dtype=[
        ("timestamp", "i8"), ("open", "f8"), ("high", "f8"),
        ("low", "f8"), ("close", "f8"), ("volume", "f8"),
        ("is_forward_fill", "bool"),
    ])
    bars["timestamp"] = np.arange(n) * 60
    bars["close"] = 100.0 + np.cumsum(rng.normal(0, 0.3, n))
    bars["open"] = bars["close"]
    bars["high"] = bars["close"] + 0.2
    bars["low"] = bars["close"] - 0.2
    bars["volume"] = 1000.0
    return bars


def test_composite_changes_when_only_regime_changes():
    from pmm_lab.data.ema_identity import compute_ema_dataset_identity
    signal = _make_candles(500, seed=1)
    regime_a = _make_candles(50, seed=2)
    regime_b = _make_candles(50, seed=3)

    id_a = compute_ema_dataset_identity(
        signal_candles=signal, regime_candles=regime_a,
        signal_interval="5m", regime_interval="4h",
    )
    id_b = compute_ema_dataset_identity(
        signal_candles=signal, regime_candles=regime_b,
        signal_interval="5m", regime_interval="4h",
    )
    assert id_a["signal_hash"] == id_b["signal_hash"], "signal hash should match"
    assert id_a["regime_hash"] != id_b["regime_hash"], "regime hash should differ"
    assert id_a["composite_hash"] != id_b["composite_hash"], (
        "composite identity must reflect regime candle difference"
    )


def test_composite_stable_when_nothing_changes():
    from pmm_lab.data.ema_identity import compute_ema_dataset_identity
    signal = _make_candles(500, seed=1)
    regime = _make_candles(50, seed=2)
    id1 = compute_ema_dataset_identity(
        signal_candles=signal, regime_candles=regime,
        signal_interval="5m", regime_interval="4h",
    )
    id2 = compute_ema_dataset_identity(
        signal_candles=signal, regime_candles=regime,
        signal_interval="5m", regime_interval="4h",
    )
    assert id1 == id2, "identity must be deterministic for identical inputs"


def test_composite_hash_is_sha256_hex_64():
    from pmm_lab.data.ema_identity import compute_ema_dataset_identity
    signal = _make_candles(500, seed=1)
    regime = _make_candles(50, seed=2)
    identity = compute_ema_dataset_identity(
        signal_candles=signal, regime_candles=regime,
        signal_interval="5m", regime_interval="4h",
    )
    ch = identity["composite_hash"]
    assert isinstance(ch, str) and len(ch) == 64
    int(ch, 16)  # valid hex


def test_signal_cache_distinguishes_different_regime_candles():
    """SharedSignalCache must not reuse signals across different regime candles."""
    from pmm_lab.objective.signal_cache import SharedSignalCache
    from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
    from pmm_lab.config.params import FeeConfig, PairRules

    cache = SharedSignalCache()
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.0001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )
    signal = _make_candles(500, seed=1)
    regime_a = _make_candles(50, seed=2)
    regime_b = _make_candles(50, seed=3)

    cfg = EMARegimeHoldStrategyConfig(
        regime_ema_fast=10, regime_ema_slow=20,
        regime_adx_length=14, regime_adx_threshold=20.0,
        volume_filter_window=50, min_volume_quantile=0.0,
        hold_mode="reentry", timestamp_mode="open", controller_compat=True,
    )
    from dataclasses import replace
    cfg_a = replace(cfg, _regime_candles=regime_a)
    cfg_b = replace(cfg, _regime_candles=regime_b)

    sig_a = cache.get_or_compute(cfg_a, "dev", signal, pair_rules, regime_candles=regime_a)
    sig_b = cache.get_or_compute(cfg_b, "dev", signal, pair_rules, regime_candles=regime_b)

    assert sig_a is not sig_b, (
        "SharedSignalCache returned the same cached signals for different regime candles"
    )


def test_dataset_key_for_pmm_passes_through():
    from pmm_lab.objective.signal_cache import _dataset_key_for
    from pmm_lab.sim.executor_model import SimConfig
    cfg = SimConfig(
        buy_spreads=[1.0], sell_spreads=[1.0],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
    )
    assert _dataset_key_for(cfg, "dev", None) == "dev"
    assert _dataset_key_for(cfg, "full", _make_candles(10)) == "full"


def test_dataset_key_for_ema_adds_regime_hash():
    from pmm_lab.objective.signal_cache import _dataset_key_for
    from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
    cfg = EMARegimeHoldStrategyConfig()
    regime = _make_candles(50, seed=1)
    key = _dataset_key_for(cfg, "dev", regime)
    assert key.startswith("dev#regime=")
    assert len(key.split("=")[-1]) == 16
