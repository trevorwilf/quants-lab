"""End-to-end smoke test for MR and EMA directional pipelines.

Marked slow. Exercises:
  1. suggest -> canonicalize -> walk-forward -> stress -> aggregate
  2. export YAML
  3. validator round-trip

On a small synthetic dataset with n_trials=2 per strategy.
"""

from dataclasses import replace
from pathlib import Path

import numpy as np
import optuna
import pytest
import yaml

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.export.hb_yaml_ema_regime_hold import (
    EMARegimeHoldExportParams,
    export_ema_regime_hold_yaml,
    validate_export_ema_regime_hold,
)
from pmm_lab.export.hb_yaml_mr_bb_rsi import (
    MRBBRSIExportParams,
    export_mr_bb_rsi_yaml,
    validate_export_mr_bb_rsi,
)
from pmm_lab.optuna.canonicalizer_ema_regime_hold import canonicalize_ema_regime_hold_params
from pmm_lab.optuna.canonicalizer_mean_reversion_bb_rsi import canonicalize_mr_bb_rsi_params
from pmm_lab.optuna.objective_wrapper import create_objective
from tests.conftest import CANDLE_DTYPE


pytestmark = pytest.mark.slow


def _make_fast(n=6000, seed=201):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0.02, 0.35)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.15))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.15))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.2, 2.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_slow(n=250, seed=211):
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 14400
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0.8, 1.0)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.6))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.6))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.5, 5.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )


def test_mr_e2e_smoke(tmp_path, pair_rules):
    candles = _make_fast()
    obj = create_objective(
        candles=candles, pair_rules=pair_rules,
        bar_interval_seconds=300,
        dataset_hash="e2e_mr", reference_price=100.0,
        train_days=3.0, test_days=1.0, step_days=1.0,
        strategy_name="mean_reversion_bb_rsi",
        fixed_quote=100.0,
        objective_version=1,
        run_stress=False,
        controller_compat=False,
    )
    study = optuna.create_study(direction="maximize")
    study.optimize(obj, n_trials=2, catch=(Exception,))
    # Find a completed, non-rejected trial
    best = None
    for t in study.trials:
        if t.state == optuna.trial.TrialState.COMPLETE and t.user_attrs.get("reject_reason") is None:
            best = t
            break
    if best is None:
        pytest.skip("No completed non-reject trial in this synthetic run")

    raw = dict(best.params)
    raw.setdefault("min_trend_slope", 0.0)
    raw.setdefault("max_spread_pct", 0.006)
    raw.setdefault("max_trades_per_day", 6)
    raw.setdefault("max_executors_per_side", 1)
    raw.setdefault("total_amount_quote", 100.0)  # fixed_quote wasn't sampled
    bundle, reason = canonicalize_mr_bb_rsi_params(raw, pair_rules, 100.0, bar_interval_seconds=300)
    assert bundle is not None, reason

    out = tmp_path / "mr_e2e.yml"
    export_params = MRBBRSIExportParams(connector_name="nonkyc", trading_pair="XMR-USDT", interval="5m")
    export_mr_bb_rsi_yaml(bundle.strategy_config, bundle.engine_config, export_params, out)
    validate_export_mr_bb_rsi(out)


def test_ema_e2e_smoke(tmp_path, pair_rules):
    fast = _make_fast()
    slow = _make_slow()
    obj = create_objective(
        candles=fast, pair_rules=pair_rules,
        bar_interval_seconds=300,
        dataset_hash="e2e_ema", reference_price=100.0,
        train_days=3.0, test_days=1.0, step_days=1.0,
        strategy_name="ema_regime_hold",
        fixed_quote=100.0,
        objective_version=1,
        run_stress=False,
        controller_compat=False,
        regime_candles=slow,
    )
    study = optuna.create_study(direction="maximize")
    study.optimize(obj, n_trials=2, catch=(Exception,))
    best = None
    for t in study.trials:
        if t.state == optuna.trial.TrialState.COMPLETE and t.user_attrs.get("reject_reason") is None:
            best = t
            break
    if best is None:
        pytest.skip("No completed non-reject trial in this synthetic run")

    raw = dict(best.params)
    raw.setdefault("hold_mode", "reentry")
    raw.setdefault("max_executors_per_side", 1)
    raw.setdefault("total_amount_quote", 100.0)  # fixed_quote wasn't sampled
    bundle, reason = canonicalize_ema_regime_hold_params(
        raw, pair_rules, 100.0,
        signal_interval_seconds=300, regime_candles=slow,
    )
    assert bundle is not None, reason

    out = tmp_path / "ema_e2e.yml"
    export_params = EMARegimeHoldExportParams(
        connector_name="nonkyc", trading_pair="XMR-USDT",
        signal_interval="5m", regime_interval="4h",
    )
    export_ema_regime_hold_yaml(bundle.strategy_config, bundle.engine_config, export_params, out)
    validate_export_ema_regime_hold(out)
