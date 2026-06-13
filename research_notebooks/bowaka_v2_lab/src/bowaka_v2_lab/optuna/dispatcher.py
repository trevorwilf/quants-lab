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
from ..utils.memory_guard import MemoryBudget, MemoryReserveViolation
from .errors import OptunaStudyInvalidError
from .objective import compute_objective, FoldResult
from .parallel import (
    WorkerResult,
    pin_blas_threads_to_one,
    run_parallel_bowaka_optimization,
)


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
    #: L16 — TPE sampler seed. Was hard-coded 1337 (reproducible but not
    #: configurable); now a field so the caller can thread ``run.seed`` for
    #: reproducibility while still defaulting to 1337 when unset.
    sampler_seed: int = 1337
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
                multivariate=True, seed=self.sampler_seed, n_startup_trials=self.n_startup_trials,
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


def _is_postgres_url(uri: Optional[str]) -> bool:
    return bool(uri) and "postgresql" in uri.lower()


def run_bowaka_optimization_dispatch(
    *,
    study: optuna.Study,
    study_name: str,
    objective: Callable[[Any], float],
    objective_factory_dotted: Optional[str] = None,
    factory_kwargs: Optional[dict[str, Any]] = None,
    n_trials: int,
    n_jobs: int = 1,
    storage_url: Optional[str] = None,
    memory_budget: Optional[MemoryBudget] = None,
    sampler_seed: int = 1337,
    n_startup_trials: int = 25,
    strict_parallel: bool = False,
    feature_store_gib_estimate: float = 0.0,
    callbacks: Optional[list] = None,
) -> optuna.Study:
    """Run ``n_trials`` against ``study`` either serially or in parallel.

    Speedup report §6.1 / §11.3 Phase 5. When ``n_jobs <= 1`` the dispatcher
    runs ``study.optimize`` in-process (legacy behaviour). When ``n_jobs > 1``:

    * Storage MUST be PostgreSQL — concurrent SQLite writers corrupt the
      study database. With ``strict_parallel=True`` a non-PostgreSQL URI
      raises :class:`OptunaStudyInvalidError`; without it, the dispatcher
      logs a warning and falls back to serial.
    * Worker count is capped at ``memory_budget.max_optuna_workers``
      (default 8).
    * ``memory_budget.assert_launch_safe(feature_store_gib_estimate,
      n_workers=...)`` is asserted before spawn.
    * Workers are spawned subprocesses; each pins BLAS to 1 thread BEFORE
      importing NumPy. The objective is reconstructed inside the worker
      via ``objective_factory_dotted(**factory_kwargs)`` so the parent
      process's objective closure (which captures large fold contexts)
      does NOT have to be pickled.
    * On success the study is reloaded from storage so subsequent
      ``study.best_trial`` / neighbor reruns see every worker's trials.
    """
    import logging

    log = logging.getLogger("bowaka_v2_lab.optuna.dispatcher")
    if n_jobs <= 1:
        study.optimize(objective, n_trials=n_trials, n_jobs=1,
                        callbacks=list(callbacks or []))
        return study

    if not _is_postgres_url(storage_url):
        if strict_parallel:
            raise OptunaStudyInvalidError(
                "Bowaka process-parallel Optuna requires PostgreSQL storage; "
                f"got storage_url={storage_url!r}. Set "
                "OPTUNA_STORAGE=postgresql+psycopg2://... or pass "
                "strict_parallel=False for an automatic serial fallback."
            )
        log.warning(
            "n_jobs=%d but storage=%r is not PostgreSQL; falling back to serial "
            "(set strict_parallel=True to refuse instead).",
            n_jobs, storage_url,
        )
        study.optimize(objective, n_trials=n_trials, n_jobs=1,
                        callbacks=list(callbacks or []))
        return study

    if objective_factory_dotted is None:
        raise OptunaStudyInvalidError(
            "Bowaka process-parallel Optuna requires "
            "objective_factory_dotted='module:attr' so each worker can rebuild "
            "the objective without pickling the parent's closure."
        )

    budget = memory_budget or MemoryBudget.from_system()
    effective_n_jobs = min(int(n_jobs), int(budget.max_optuna_workers))
    if effective_n_jobs != n_jobs:
        log.info(
            "capping n_jobs from %d to %d (memory_budget.max_optuna_workers)",
            n_jobs, effective_n_jobs,
        )
    try:
        budget.assert_launch_safe(
            feature_store_gib_estimate=float(feature_store_gib_estimate),
            n_workers=effective_n_jobs,
        )
    except MemoryReserveViolation as e:
        if strict_parallel:
            raise
        log.warning("memory budget refused parallel launch: %s; serial fallback", e)
        study.optimize(objective, n_trials=n_trials, n_jobs=1,
                        callbacks=list(callbacks or []))
        return study

    log.info(
        "launching %d workers against %s study=%r for %d trials "
        "(speedup report §6.1 / §11.3 Phase 5)",
        effective_n_jobs, storage_url, study_name, n_trials,
    )
    results = run_parallel_bowaka_optimization(
        study_name=study_name,
        storage_url=storage_url,
        n_total_trials=int(n_trials),
        n_workers=effective_n_jobs,
        objective_factory_dotted=objective_factory_dotted,
        factory_kwargs=dict(factory_kwargs or {}),
        sampler_seed=sampler_seed,
        n_startup_trials=n_startup_trials,
        memory_budget=budget,
    )
    n_complete = sum(r.n_completed for r in results)
    n_failed = sum(r.n_failed for r in results)
    log.info(
        "parallel optimize done: %d completed, %d failed across %d workers",
        n_complete, n_failed, len(results),
    )
    if all(r.error for r in results):
        raise OptunaStudyInvalidError(
            "every parallel worker errored before any trial completed: "
            + "; ".join(f"w{r.worker_id}: {r.error}" for r in results)
        )
    # Reload the study so the parent process sees the union of all worker
    # trials (best_trial / neighbour reruns / artifact writers all need this).
    refreshed = optuna.load_study(study_name=study_name, storage=storage_url)
    return refreshed


__all__ = [
    "OptunaStudy",
    "build_study_name",
    "IEX_STUDY_PREFIX",
    "run_bowaka_optimization_dispatch",
]
