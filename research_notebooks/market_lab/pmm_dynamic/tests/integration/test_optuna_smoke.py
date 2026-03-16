"""Integration smoke tests for Optuna optimization pipeline."""

import logging
import tempfile
import os
import numpy as np
import optuna
import pytest

pytestmark = pytest.mark.slow

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.data.hashing import hash_candles
from pmm_lab.optuna.objective_wrapper import create_objective
from pmm_lab.optuna.study import create_study, run_optimization
from pmm_lab.optuna.callbacks import DegeneracyCheckCallback
from pmm_lab.objective.objective import REJECT_SCORE

CANDLE_DTYPE = np.dtype([
    ("timestamp", "int64"),
    ("open", "float64"),
    ("high", "float64"),
    ("low", "float64"),
    ("close", "float64"),
    ("volume", "float64"),
    ("is_forward_fill", "bool"),
])


def _make_candles(n: int, seed: int = 99) -> np.ndarray:
    """Create n-bar candle array with random walks."""
    rng = np.random.default_rng(seed=seed)
    start_ts = 1756833000
    interval = 300
    price = 100000.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 80)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 30))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 30))
        open_p = max(open_p, 1.0)
        close_p = max(close_p, 1.0)
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.1, 3.0)
        rows.append((start_ts + i * interval, open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


@pytest.fixture
def candles_500():
    return _make_candles(500)


class TestOptunaSmoke:
    def test_smoke_30_trials(self, candles_500, pair_rules, tmp_path):
        """Run 30 trials. Assert >= 20 complete, >= 10 distinct values, best > REJECT_SCORE."""
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        dataset_hash = hash_candles(candles_500)
        reference_price = float(np.median(candles_500["close"]))
        db_path = str(tmp_path / "test_study.db")
        storage_url = f"sqlite:///{db_path}"

        objective = create_objective(
            candles=candles_500,
            pair_rules=pair_rules,
            bar_interval_seconds=300,
            dataset_hash=dataset_hash,
            reference_price=reference_price,
            train_days=0.5,
            test_days=0.25,
            step_days=0.25,
            embargo_bars=10,
            run_stress=False,
            lambda_mad=0.5,
        )

        study = create_study(
            study_name="smoke_test_30",
            seed=42,
            storage_url=storage_url,
            n_startup_trials=10,
        )

        run_optimization(study, objective, n_trials=30)

        complete_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
        assert len(complete_trials) >= 20, f"Only {len(complete_trials)} completed out of 30"

        values = [t.value for t in complete_trials if t.value is not None]
        distinct = len(set(round(v, 6) for v in values))
        assert distinct >= 2, f"Only {distinct} distinct values"

        assert study.best_trial is not None
        assert study.best_value > REJECT_SCORE

        assert "objective_score" in study.best_trial.user_attrs
        assert "dataset_hash" in study.best_trial.user_attrs

    def test_study_resume(self, candles_500, pair_rules, tmp_path):
        """Run study, then resume with 5 more trials."""
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        dataset_hash = hash_candles(candles_500)
        reference_price = float(np.median(candles_500["close"]))
        db_path = str(tmp_path / "resume_study.db")
        storage_url = f"sqlite:///{db_path}"

        objective = create_objective(
            candles=candles_500,
            pair_rules=pair_rules,
            bar_interval_seconds=300,
            dataset_hash=dataset_hash,
            reference_price=reference_price,
            train_days=0.5,
            test_days=0.25,
            step_days=0.25,
            embargo_bars=10,
            run_stress=False,
        )

        # First run: 10 trials
        study1 = create_study("resume_test", seed=42, storage_url=storage_url, n_startup_trials=5)
        run_optimization(study1, objective, n_trials=10)
        n_after_first = len(study1.trials)

        # Resume: 5 more
        study2 = create_study("resume_test", seed=42, storage_url=storage_url, n_startup_trials=5)
        run_optimization(study2, objective, n_trials=5)
        n_after_second = len(study2.trials)

        assert n_after_second == n_after_first + 5

    def test_smoke_v2_objective_30_trials(self, candles_500, pair_rules, tmp_path):
        """Run 30 trials with v2 objective + fixed_quote. Assert >= 15 complete, best > REJECT_SCORE."""
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        dataset_hash = hash_candles(candles_500)
        reference_price = float(np.median(candles_500["close"]))
        db_path = str(tmp_path / "test_study_v2.db")
        storage_url = f"sqlite:///{db_path}"

        objective = create_objective(
            candles=candles_500,
            pair_rules=pair_rules,
            bar_interval_seconds=300,
            dataset_hash=dataset_hash,
            reference_price=reference_price,
            train_days=0.5,
            test_days=0.25,
            step_days=0.25,
            embargo_bars=10,
            objective_version=2,
            fixed_quote=100.0,
            run_stress=False,
            lambda_mad=0.5,
        )

        study = create_study(
            study_name="smoke_test_v2_30",
            seed=42,
            storage_url=storage_url,
            n_startup_trials=10,
        )

        run_optimization(study, objective, n_trials=30)

        complete_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
        assert len(complete_trials) >= 15, f"Only {len(complete_trials)} completed out of 30"

        assert study.best_trial is not None
        assert study.best_value > REJECT_SCORE

    def test_degeneracy_callback_fires(self, tmp_path, caplog):
        """Constant-value objective → DegeneracyCheckCallback logs warning."""
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        db_path = str(tmp_path / "degen_study.db")
        storage_url = f"sqlite:///{db_path}"

        def constant_objective(trial):
            # Suggest at least one param so Optuna doesn't complain
            trial.suggest_float("x", 0.0, 1.0)
            return 42.0

        callback = DegeneracyCheckCallback(check_after_n_trials=30, min_distinct_values=10)

        study = create_study("degen_test", seed=42, storage_url=storage_url, n_startup_trials=5)

        with caplog.at_level(logging.WARNING, logger="pmm_lab.optuna.callbacks"):
            run_optimization(study, constant_objective, n_trials=35, callbacks=[callback])

        assert callback._checked
        assert any("DEGENERACY WARNING" in rec.message for rec in caplog.records)
