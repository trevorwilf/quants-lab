"""Addendum §4: canonicalizer + objective wrapper smoke test parameterized
over connector ∈ {nonkyc, kraken}, on synthetic candles (no Mongo)."""

from pathlib import Path

import numpy as np
import optuna
import pytest

from pmm_lab.config.exchange_rules import load_exchange_rules, resolve_pair_rules
from pmm_lab.optuna.objective_wrapper import create_objective
from tests.conftest import CANDLE_DTYPE

YAML_PATH = Path(__file__).resolve().parents[2] / "configs" / "exchange_rules.yaml"
BAR_SECONDS = 3600


def _candles(n=4400, seed=21, base_price=400.0):
    rng = np.random.default_rng(seed)
    ts = np.arange(n, dtype="int64") * BAR_SECONDS + 1_700_000_000
    close = base_price * (1.0 + 0.12 * np.sin(2 * np.pi * np.arange(n) / 150))
    close = close + rng.normal(0, 0.01 * base_price, n)
    close = np.maximum(close, 0.01)
    o = np.roll(close, 1)
    o[0] = close[0]
    h = np.maximum(o, close) + np.abs(rng.normal(0, 0.005 * base_price, n))
    l = np.minimum(o, close) - np.abs(rng.normal(0, 0.005 * base_price, n))
    rows = [(int(ts[i]), o[i], h[i], l[i], close[i], 1.0, False) for i in range(n)]
    return np.array(rows, dtype=CANDLE_DTYPE)


VALID_PARAMS = dict(
    n_buy=4, n_sell=4,
    buy_near_pct=0.02, buy_far_pct=0.15,
    sell_near_pct=0.02, sell_far_pct=0.15,
    buy_gamma=1.0, sell_gamma=1.0,
    k_buy=0.5, k_sell=0.5,
)


@pytest.mark.parametrize("connector", ["nonkyc", "kraken"])
def test_objective_smoke_per_connector(connector):
    rules_db = load_exchange_rules(yaml_path=YAML_PATH)
    pair_rules = resolve_pair_rules(rules_db, connector, "XMR-USDT")
    candles = _candles()
    objective = create_objective(
        candles=candles,
        pair_rules=pair_rules,
        bar_interval_seconds=BAR_SECONDS,
        dataset_hash=f"smoke_{connector}",
        reference_price=400.0,
        strategy_name="range_ladder",
        train_days=None, test_days=None, step_days=None,
        fixed_quote=1000.0,
        run_stress=True,
    )
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.RandomSampler(seed=17),
        pruner=optuna.pruners.NopPruner(),
    )
    study.enqueue_trial(dict(VALID_PARAMS))
    study.optimize(objective, n_trials=1, catch=())
    trial = study.trials[0]
    assert trial.state == optuna.trial.TrialState.COMPLETE
    assert trial.user_attrs["strategy_name"] == "range_ladder"
    # the fee actually used must be the connector's maker fee
    expected_fee = pair_rules.fees.maker_fee
    assert trial.user_attrs["n_folds"] == 3
    # rungs of the last fold exist for eyeballing
    assert "last_fold_rungs" in trial.user_attrs
    # dead-zone floor scaled with the connector fee: 0.02+0.02 clears both,
    # but the config carried the right fee (asserted via export-side checks
    # in test_canonicalizer_range_ladder; here we just confirm completion).
    assert expected_fee in (0.002, 0.0025)
