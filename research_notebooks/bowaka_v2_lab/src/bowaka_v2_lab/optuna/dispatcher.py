"""Optuna study dispatcher.

Persists to PostgreSQL when configured, else SQLite local file. Study-name
format: ``bowaka_v2_{feed}_walkforward_{cost_stress}_{ds_hash8}_{YYYYMMDD}``.

Realism remediation 2 Phase 10 (audit §P1-010): IEX-feed studies auto-prefix
the study name with ``iex__`` and tag ``partial_tape=true`` in
``study.user_attrs`` so any downstream tool can immediately see the run was
tuned on the partial IEX tape. IEX-only studies are blocked from promotion
via :meth:`OptunaStudy.mark_promotion_eligible`.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import optuna

from ..promotion.suitability import (
    IEXPromotionBlocked,
    assert_not_above_research_only_for_iex,
    feed_caveat_for,
)
from .objective import compute_objective, FoldResult


#: Realism remediation 2 Phase 10 (audit §P1-010): the canonical study-name
#: prefix for IEX-feed studies. Surfaced in every study artifact so the
#: downstream caller can tell at a glance the run was tuned on partial tape.
IEX_STUDY_PREFIX = "iex__"


def build_study_name(*, feed: str, cost_stress: str, dataset_hash: str, on_date: Optional[_dt.date] = None) -> str:
    """Build the canonical Optuna study name.

    Realism remediation 2 Phase 10 — IEX studies are auto-prefixed with
    ``iex__`` (audit §P1-010): the prefix is mechanical so an operator
    inspecting a list of studies can immediately spot which ones are IEX-only.
    The legacy ``bowaka_v2_<feed>_walkforward_...`` body is preserved so the
    embedded ``feed`` field remains queryable.
    """
    d = on_date or _dt.date.today()
    body = f"bowaka_v2_{feed}_walkforward_{cost_stress}_{dataset_hash[:8]}_{d:%Y%m%d}"
    if str(feed or "").lower() == "iex":
        return f"{IEX_STUDY_PREFIX}{body}"
    return body


@dataclass
class OptunaStudy:
    feed: str
    cost_stress: str
    dataset_hash: str
    config_hash: str
    storage_uri: Optional[str] = None
    n_trials: int = 20
    n_jobs: int = 1
    #: Random-sampling trials before TPE-guided search begins (Optuna default 10).
    n_startup_trials: int = 10
    study: Optional[optuna.Study] = None
    promotion_eligible: bool = field(default=False)

    def create(self) -> optuna.Study:
        name = build_study_name(feed=self.feed, cost_stress=self.cost_stress, dataset_hash=self.dataset_hash)
        self.study = optuna.create_study(
            direction="maximize",
            study_name=name,
            storage=self.storage_uri,
            load_if_exists=True,
            sampler=optuna.samplers.TPESampler(
                multivariate=True, seed=1337, n_startup_trials=self.n_startup_trials,
            ),
        )
        # Attach run-side metadata.
        self.study.set_user_attr("feed", self.feed)
        self.study.set_user_attr("cost_stress", self.cost_stress)
        self.study.set_user_attr("config_hash", self.config_hash)
        self.study.set_user_attr("dataset_hash", self.dataset_hash)
        # Realism remediation 2 Phase 10 (audit §P1-010) — IEX is partial-tape;
        # downstream tools key off ``partial_tape`` + ``feed_caveat`` to refuse
        # SIP-portable claims on an IEX study. Both attrs are *always* set so
        # consumers don't have to special-case the IEX path.
        is_iex = str(self.feed or "").lower() == "iex"
        self.study.set_user_attr("partial_tape", bool(is_iex))
        caveat = feed_caveat_for(self.feed)
        if caveat is not None:
            self.study.set_user_attr("feed_caveat", caveat)
        return self.study

    def mark_promotion_eligible(self) -> None:
        """IEX-only studies cannot be promoted past research_only.

        Per [Report §11/14]: promotion to paper/live requires SIP-validated
        walk-forward + paper-vs-sim reconciliation; IEX cannot satisfy that.

        Realism remediation 2 Phase 10 (audit §P1-010): the mechanical refusal
        now raises :class:`IEXPromotionBlocked` (a subclass of ``RuntimeError``
        so the existing test surface still matches ``pytest.raises(RuntimeError)``).
        """
        if self.feed == "iex":
            raise IEXPromotionBlocked(
                "IEX-only study cannot be promoted past research_only; "
                "re-run on SIP feed and produce paper-recon evidence first."
            )
        self.promotion_eligible = True

    def optimize(self, objective_fn: Callable[[optuna.Trial], float]) -> None:
        assert self.study is not None, "call create() first"
        self.study.optimize(objective_fn, n_trials=self.n_trials, n_jobs=self.n_jobs)


__all__ = [
    "OptunaStudy",
    "build_study_name",
    "IEX_STUDY_PREFIX",
]
