"""Optuna study dispatcher.

Persists to PostgreSQL when configured, else SQLite local file. Study-name
format: ``bowaka_v2_{feed}_walkforward_{cost_stress}_{ds_hash8}_{YYYYMMDD}``.

IEX-only studies are blocked from promotion via
``OptunaStudy.mark_promotion_eligible``.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import optuna

from .objective import compute_objective, FoldResult


def build_study_name(*, feed: str, cost_stress: str, dataset_hash: str, on_date: Optional[_dt.date] = None) -> str:
    d = on_date or _dt.date.today()
    return f"bowaka_v2_{feed}_walkforward_{cost_stress}_{dataset_hash[:8]}_{d:%Y%m%d}"


@dataclass
class OptunaStudy:
    feed: str
    cost_stress: str
    dataset_hash: str
    config_hash: str
    storage_uri: Optional[str] = None
    n_trials: int = 20
    n_jobs: int = 1
    study: Optional[optuna.Study] = None
    promotion_eligible: bool = field(default=False)

    def create(self) -> optuna.Study:
        name = build_study_name(feed=self.feed, cost_stress=self.cost_stress, dataset_hash=self.dataset_hash)
        self.study = optuna.create_study(
            direction="maximize",
            study_name=name,
            storage=self.storage_uri,
            load_if_exists=True,
            sampler=optuna.samplers.TPESampler(multivariate=True, seed=1337),
        )
        # Attach run-side metadata.
        self.study.set_user_attr("feed", self.feed)
        self.study.set_user_attr("cost_stress", self.cost_stress)
        self.study.set_user_attr("config_hash", self.config_hash)
        self.study.set_user_attr("dataset_hash", self.dataset_hash)
        return self.study

    def mark_promotion_eligible(self) -> None:
        """IEX-only studies cannot be promoted past research_only.

        Per [Report §11/14]: promotion to paper/live requires SIP-validated
        walk-forward + paper-vs-sim reconciliation; IEX cannot satisfy that.
        """
        if self.feed == "iex":
            raise RuntimeError(
                "IEX-only study cannot be promoted past research_only; "
                "re-run on SIP feed and produce paper-recon evidence first."
            )
        self.promotion_eligible = True

    def optimize(self, objective_fn: Callable[[optuna.Trial], float]) -> None:
        assert self.study is not None, "call create() first"
        self.study.optimize(objective_fn, n_trials=self.n_trials, n_jobs=self.n_jobs)
